# app/routers/transactions.py
import logging
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
from app.services.adapters import get_adapter_for_chain

logger = logging.getLogger("chainlens.routers.transactions")
router = APIRouter()


@router.get("/wallets/{address}/transactions")
def get_transactions(
    address: str = Path(..., min_length=3, max_length=200),
    chain: str = Query("aptos", description="Blockchain: aptos or solana"),  # ← NEW
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
    
    Now supports multiple chains!
    
    Returns:
        {
            "transactions": [...],
            "total": 100,
            "offset": 0,
            "limit": 20,
            "has_more": true
        }
    """
    try:
        # Get adapter for this chain
        adapter = get_adapter_for_chain(chain)
        normalized_addr = adapter.normalize_address(address)
    except ValueError as e:
        logger.warning("Unsupported chain '%s' for transactions: %s", chain, e)
        return {
            "transactions": [],
            "total": 0,
            "offset": offset,
            "limit": limit,
            "has_more": False,
            "chain": chain,
            "message": f"Transaction history is not yet supported for chain '{chain}'."
        }
    
    # Build cache key with filters
    cache_key = f"transactions:{chain}:{normalized_addr}:{limit}:{offset}:{type_filter}:{status_filter}:{search}:{date_from}:{date_to}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug("Returning cached transactions for %s on %s", normalized_addr, chain)
        return cached

    try:
        logger.info("Fetching transactions for %s on %s...", normalized_addr, chain)
        
        # Use adapter to get transactions
        raw_txns = adapter.get_transactions(normalized_addr, limit=min(100, limit * 3), offset=offset)
        
        # For Aptos, we have a parser; for Solana, return simplified format
        if chain == "aptos":
            parser = TransactionParser()
            transactions = []
            
            for txn in raw_txns:
                if txn.get("type") != "user_transaction":
                    continue
                
                parsed = parser.parse_transaction(txn)
                transactions.append(parsed)
            
            logger.info("Parsed %d Aptos user transactions", len(transactions))

        else:  # Solana
            # Solana transactions from adapter are already simplified
            transactions = raw_txns
            logger.info("Received %d Solana transactions", len(transactions))
        
        # Apply filters
        filtered_txns = transactions
        
        # Type filter
        if type_filter:
            type_lower = type_filter.lower()
            filtered_txns = [
                t for t in filtered_txns 
                if type_lower in t.get("type", "").lower() or type_lower in t.get("category", "").lower()
            ]
        
        # Status filter
        if status_filter:
            if status_filter.lower() == "success":
                filtered_txns = [t for t in filtered_txns if t.get("success", True)]
            elif status_filter.lower() == "failed":
                filtered_txns = [t for t in filtered_txns if not t.get("success", True)]
        
        # Search filter
        if search:
            search_lower = search.lower()
            filtered_txns = [
                t for t in filtered_txns
                if search_lower in t.get("hash", "").lower() 
                or search_lower in t.get("signature", "").lower()
                or search_lower in t.get("function", "").lower()
                or search_lower in t.get("details", {}).get("recipient", "").lower()
            ]
        
        # Date filters
        if date_from or date_to:
            filtered_txns = apply_date_filters(filtered_txns, date_from, date_to)
        
        # Pagination
        total = len(filtered_txns)
        start = 0
        end = min(limit, len(filtered_txns))
        paginated_txns = filtered_txns[start:end]
        
        result = {
            "transactions": paginated_txns,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": len(filtered_txns) >= limit,
            "chain": chain  # ← Include chain in response
        }
        
        # Cache for 30 seconds
        cache.set(cache_key, result, 30)
        
        return result

    except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as e:
        logger.error("Failed to fetch transactions: %s", e)
        
        # Return empty result instead of error for 404
        if "404" in str(e):
            return {
                "transactions": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False,
                "chain": chain
            }
        
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch transactions: {str(e)}"
        )


@router.get("/wallets/{address}/transactions/{hash}")
def get_transaction_detail(
    address: str = Path(..., min_length=3, max_length=200),
    hash: str = Path(..., description="Transaction hash or signature"),
    chain: str = Query("aptos", description="Blockchain: aptos or solana")  # ← NEW
) -> Dict[str, Any]:
    """
    Get detailed information for a specific transaction.
    
    Now supports multiple chains!
    """
    try:
        adapter = get_adapter_for_chain(chain)
        normalized_addr = adapter.normalize_address(address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # For now, this endpoint only works well with Aptos
    # Solana would need additional implementation
    if chain != "aptos":
        raise HTTPException(
            status_code=501,
            detail=f"Transaction details not yet implemented for {chain}"
        )
    
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
        parsed["chain"] = chain
        
        return parsed
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Transaction not found")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch transaction: HTTP {e.response.status_code}"
        )
    except (httpx.HTTPError, httpx.TimeoutException, ValueError) as e:
        logger.error("Failed to fetch transaction detail: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch transaction: {str(e)}"
        )


@router.get("/wallets/{address}/transactions/export/csv")
def export_transactions_csv(
    address: str = Path(..., min_length=3, max_length=200),
    chain: str = Query("aptos", description="Blockchain: aptos or solana"),  # ← NEW
    limit: int = Query(100, ge=1, le=1000),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Export transactions as CSV file.
    
    Now supports multiple chains!
    """
    # Get transactions
    txn_data = get_transactions(address=address, chain=chain, limit=limit, offset=0)
    transactions = txn_data["transactions"]
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Hash/Signature",
        "Type",
        "Status",
        "Timestamp",
        "Sender",
        "Recipient",
        "Amount",
        "Symbol",
        "Gas Used",
        "Function",
        "Chain"
    ])
    
    # Write transactions
    for txn in transactions:
        details = txn.get("details", {})
        
        # Format timestamp
        try:
            timestamp_val = txn.get("timestamp") or txn.get("blockTime")
            if timestamp_val:
                ts_micro = int(timestamp_val)
                # Aptos uses microseconds, Solana uses seconds
                ts_sec = ts_micro / 1_000_000 if chain == "aptos" else ts_micro
                dt = datetime.fromtimestamp(ts_sec)
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = "N/A"
        except (ValueError, TypeError, OSError) as e:
            logger.debug("Failed to parse timestamp: %s", e)
            timestamp_str = str(timestamp_val) if timestamp_val else "N/A"
        
        writer.writerow([
            txn.get("hash") or txn.get("signature", "N/A"),
            txn.get("type", "N/A"),
            "Success" if txn.get("success") else "Failed",
            timestamp_str,
            txn.get("sender", "N/A"),
            details.get("recipient", "N/A"),
            details.get("amount", "N/A"),
            details.get("symbol", "N/A"),
            txn.get("gas_used", "N/A"),
            txn.get("function", "N/A"),
            chain
        ])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{chain}_{address[:10]}.csv"
        }
    )


@router.get("/transactions/summary")
def get_transaction_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get transaction summary across all user's wallets (multi-chain).
    Used for AI insights and dashboard stats.
    """
    user_id = str(current_user["_id"])
    wallets = list_user_wallets(user_id)
    
    summary = {
        "total_transactions": 0,
        "by_type": {},
        "by_chain": {},  # ← NEW
        "by_wallet": [],
        "total_gas_spent": 0,
        "success_rate": 0.0
    }
    
    total_success = 0
    total_count = 0
    
    for wallet in wallets:
        addr = wallet["address"]
        chain = wallet.get("chain", "aptos")
        
        try:
            # Get transactions for this wallet
            txn_data = get_transactions(address=addr, chain=chain, limit=50, offset=0)
            txns = txn_data["transactions"]
            
            wallet_summary = {
                "address": addr,
                "chain": chain,  # ← NEW
                "label": wallet["label"],
                "transaction_count": len(txns),
                "by_type": {}
            }
            
            # Count by chain
            summary["by_chain"][chain] = summary["by_chain"].get(chain, 0) + len(txns)
            
            for txn in txns:
                total_count += 1
                if txn.get("success", True):
                    total_success += 1
                
                # Count by type
                txn_type = txn.get("type", "Unknown")
                summary["by_type"][txn_type] = summary["by_type"].get(txn_type, 0) + 1
                wallet_summary["by_type"][txn_type] = wallet_summary["by_type"].get(txn_type, 0) + 1
                
                # Sum gas
                summary["total_gas_spent"] += txn.get("gas_used", 0)
            
            summary["by_wallet"].append(wallet_summary)
            summary["total_transactions"] += len(txns)
            
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, RuntimeError) as e:
            logger.error("Failed to get transactions for %s on %s: %s", addr, chain, e)
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
            # Get timestamp (different field names for different chains)
            timestamp_val = txn.get("timestamp") or txn.get("blockTime")
            if not timestamp_val:
                filtered.append(txn)
                continue
            
            # Parse timestamp
            ts_micro = int(timestamp_val)
            # Aptos uses microseconds, Solana uses seconds
            ts_sec = ts_micro / 1_000_000 if "timestamp" in txn else ts_micro
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
            
        except (ValueError, TypeError, OSError) as e:
            logger.warning("Failed to parse date for txn: %s", e)
            filtered.append(txn)  # Include if date parsing fails
    
    return filtered