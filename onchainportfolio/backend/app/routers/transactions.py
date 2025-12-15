# app/routers/transactions.py
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import httpx
import io
import csv
from datetime import datetime

from app.services.cache import cache
from app.services.transaction_parser import TransactionParser
from app.deps import get_current_user, get_current_user_optional
from app.services.wallet_service import list_user_wallets

router = APIRouter()


@router.get("/wallets/{address}/transactions")
def get_transactions(
    address: str = Path(..., min_length=3, max_length=200),
    limit: int = Query(20, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    type_filter: Optional[str] = Query(None, description="Filter by type: transfer, swap, stake, etc."),
    status_filter: Optional[str] = Query(None, description="Filter by status: success, failed"),
    search: Optional[str] = Query(None, description="Search by hash or function"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
) -> Dict[str, Any]:
    """
    Get transaction history for a wallet with filters, search, and pagination.
    
    Returns:
        {
            "transactions": [...],
            "total": 100,
            "offset": 0,
            "limit": 20,
            "has_more": true
        }
    """
    # Normalize address
    addr = address.lower()
    if not addr.startswith("0x"):
        addr = "0x" + addr
    
    # Build cache key with filters
    cache_key = f"transactions:{addr}:{limit}:{offset}:{type_filter}:{status_filter}:{search}:{date_from}:{date_to}"
    cached = cache.get(cache_key)
    if cached:
        print(f"[CACHE] Returning cached transactions for {addr}")
        return cached
    
    try:
        # Fetch more transactions for filtering (we'll filter client-side for now)
        fetch_limit = min(100, limit * 3)  # Fetch extra for filtering
        url = f"https://fullnode.testnet.aptoslabs.com/v1/accounts/{addr}/transactions"
        params = {"limit": fetch_limit, "start": offset}
        
        print(f"[INFO] Fetching transactions for {addr}...")
        
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, params=params)
            
            if response.status_code == 404:
                return {
                    "transactions": [],
                    "total": 0,
                    "offset": offset,
                    "limit": limit,
                    "has_more": False
                }
            
            response.raise_for_status()
            raw_txns = response.json()
        
        print(f"[INFO] Received {len(raw_txns)} raw transactions")
        
        # Parse transactions
        parser = TransactionParser()
        transactions = []
        
        for txn in raw_txns:
            if txn.get("type") != "user_transaction":
                continue
            
            parsed = parser.parse_transaction(txn)
            transactions.append(parsed)
        
        print(f"[INFO] Parsed {len(transactions)} user transactions")
        
        # Apply filters
        filtered_txns = transactions
        
        # Type filter
        if type_filter:
            type_lower = type_filter.lower()
            filtered_txns = [
                t for t in filtered_txns 
                if type_lower in t["type"].lower() or type_lower in t["category"].lower()
            ]
        
        # Status filter
        if status_filter:
            if status_filter.lower() == "success":
                filtered_txns = [t for t in filtered_txns if t["success"]]
            elif status_filter.lower() == "failed":
                filtered_txns = [t for t in filtered_txns if not t["success"]]
        
        # Search filter
        if search:
            search_lower = search.lower()
            filtered_txns = [
                t for t in filtered_txns
                if search_lower in t["hash"].lower() 
                or search_lower in t.get("function", "").lower()
                or search_lower in t.get("details", {}).get("recipient", "").lower()
            ]
        
        # Date filters
        if date_from or date_to:
            filtered_txns = apply_date_filters(filtered_txns, date_from, date_to)
        
        # Pagination
        total = len(filtered_txns)
        start = 0  # Already offset by API call
        end = min(limit, len(filtered_txns))
        paginated_txns = filtered_txns[start:end]
        
        result = {
            "transactions": paginated_txns,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": len(filtered_txns) >= limit
        }
        
        # Cache for 30 seconds
        cache.set(cache_key, result, 30)
        
        return result
        
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
        if e.response.status_code == 404:
            return {
                "transactions": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False
            }
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch transactions: HTTP {e.response.status_code}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to fetch transactions: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch transactions: {str(e)}"
        )


@router.get("/wallets/{address}/transactions/{hash}")
def get_transaction_detail(
    address: str = Path(..., min_length=3, max_length=200),
    hash: str = Path(..., description="Transaction hash")
) -> Dict[str, Any]:
    """
    Get detailed information for a specific transaction.
    """
    addr = address.lower()
    if not addr.startswith("0x"):
        addr = "0x" + addr
    
    try:
        url = f"https://fullnode.testnet.aptoslabs.com/v1/transactions/by_hash/{hash}"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            response.raise_for_status()
            raw_txn = response.json()
        
        # Parse transaction
        parser = TransactionParser()
        parsed = parser.parse_transaction(raw_txn)
        
        # Add raw data for debugging
        parsed["raw"] = raw_txn
        
        return parsed
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Transaction not found")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch transaction: HTTP {e.response.status_code}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to fetch transaction detail: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch transaction: {str(e)}"
        )


@router.get("/wallets/{address}/transactions/export/csv")
def export_transactions_csv(
    address: str = Path(..., min_length=3, max_length=200),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Export transactions as CSV file.
    """
    addr = address.lower()
    if not addr.startswith("0x"):
        addr = "0x" + addr
    
    # Get transactions (without pagination for export)
    txn_data = get_transactions(address=addr, limit=limit, offset=0)
    transactions = txn_data["transactions"]
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Hash",
        "Type",
        "Status",
        "Timestamp",
        "Sender",
        "Recipient",
        "Amount",
        "Symbol",
        "Gas Used",
        "Function"
    ])
    
    # Write transactions
    for txn in transactions:
        details = txn.get("details", {})
        
        # Format timestamp
        try:
            ts_micro = int(txn["timestamp"])
            ts_sec = ts_micro / 1_000_000
            dt = datetime.fromtimestamp(ts_sec)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            timestamp_str = txn["timestamp"]
        
        writer.writerow([
            txn["hash"],
            txn["type"],
            "Success" if txn["success"] else "Failed",
            timestamp_str,
            txn["sender"],
            details.get("recipient", "N/A"),
            details.get("amount", "N/A"),
            details.get("symbol", "N/A"),
            txn["gas_used"],
            txn.get("function", "N/A")
        ])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{addr[:10]}.csv"
        }
    )


@router.get("/transactions/summary")
def get_transaction_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get transaction summary across all user's wallets.
    Used for AI insights and dashboard stats.
    """
    user_id = str(current_user["_id"])
    wallets = list_user_wallets(user_id)
    
    summary = {
        "total_transactions": 0,
        "by_type": {},
        "by_wallet": [],
        "total_gas_spent": 0,
        "success_rate": 0.0
    }
    
    total_success = 0
    total_count = 0
    
    for wallet in wallets:
        addr = wallet["address"]
        
        try:
            # Get transactions for this wallet
            txn_data = get_transactions(address=addr, limit=50, offset=0)
            txns = txn_data["transactions"]
            
            wallet_summary = {
                "address": addr,
                "label": wallet["label"],
                "transaction_count": len(txns),
                "by_type": {}
            }
            
            for txn in txns:
                total_count += 1
                if txn["success"]:
                    total_success += 1
                
                # Count by type
                txn_type = txn["type"]
                summary["by_type"][txn_type] = summary["by_type"].get(txn_type, 0) + 1
                wallet_summary["by_type"][txn_type] = wallet_summary["by_type"].get(txn_type, 0) + 1
                
                # Sum gas
                summary["total_gas_spent"] += txn["gas_used"]
            
            summary["by_wallet"].append(wallet_summary)
            summary["total_transactions"] += len(txns)
            
        except Exception as e:
            print(f"[ERROR] Failed to get transactions for {addr}: {e}")
            continue
    
    # Calculate success rate
    if total_count > 0:
        summary["success_rate"] = round((total_success / total_count) * 100, 2)
    
    return summary


def apply_date_filters(transactions: List[Dict[str, Any]], date_from: Optional[str], date_to: Optional[str]) -> List[Dict[str, Any]]:
    """Apply date range filters to transactions."""
    if not date_from and not date_to:
        return transactions
    
    filtered = []
    
    for txn in transactions:
        try:
            # Parse transaction timestamp (microseconds)
            ts_micro = int(txn["timestamp"])
            ts_sec = ts_micro / 1_000_000
            txn_date = datetime.fromtimestamp(ts_sec)
            
            # Check date_from
            if date_from:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                if txn_date < from_date:
                    continue
            
            # Check date_to
            if date_to:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                if txn_date > to_date:
                    continue
            
            filtered.append(txn)
            
        except Exception as e:
            print(f"[WARN] Failed to parse date for txn: {e}")
            filtered.append(txn)  # Include if date parsing fails
    
    return filtered