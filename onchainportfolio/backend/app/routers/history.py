# backend/app/routers/history.py - CORRECTED: Snapshot Integration
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta
from dateutil import parser
from bson import ObjectId

from app.services.history_service import HistoryService
from app.services.snapshot_service import SnapshotService
from app.services.cache import cache
from app.deps import get_current_user, price_service
from app.config import settings

router = APIRouter()

# Initialize history service
history_service = HistoryService(cache_ttl_seconds=3600)


# ============================================================
# Response Models
# ============================================================

class PricePoint(BaseModel):
    """Single price data point."""
    timestamp: int
    price: float


class PriceHistoryResponse(BaseModel):
    """Historical price data for a token."""
    symbol: str
    prices: list[PricePoint]
    current_price: float
    change_24h: float
    change_percent: float
    period_change: float
    period_change_percent: float
    data_points: int


class PortfolioValuePoint(BaseModel):
    """Single portfolio value data point."""
    timestamp: int
    value: float


class PortfolioHistoryMetadata(BaseModel):
    """Metadata about portfolio history calculation."""
    earliest_wallet_date: str
    wallet_age_days: int
    requested_days: int
    actual_days_shown: int
    scope: str  # "all_wallets" or wallet_id
    scope_label: str  # "Complete Portfolio" or wallet label
    disclaimer: str
    data_source: Optional[str] = "approximation"  # ✨ NEW: "snapshots" or "approximation"
    coverage_percent: Optional[float] = 0.0  # ✨ NEW: Snapshot coverage


class PortfolioHistoryResponse(BaseModel):
    """Historical portfolio value."""
    values: list[PortfolioValuePoint]
    current_value: float
    period_change: float
    period_change_percent: float
    data_points: int
    metadata: PortfolioHistoryMetadata


class WalletEvent(BaseModel):
    """Represents a wallet addition event."""
    date: str
    timestamp: int
    type: str
    wallet_id: str
    wallet_label: str
    wallet_chain: str
    value_before: float
    value_after: float
    impact: float


class WalletBreakdown(BaseModel):
    """Current wallet contribution breakdown."""
    wallet_id: str
    label: str
    chain: str
    current_value: float
    percentage: float
    created_at: str
    age_days: int


class DetailedPortfolioHistoryResponse(BaseModel):
    """Enhanced portfolio history with events and breakdown."""
    values: list[PortfolioValuePoint]
    current_value: float
    period_change: float
    period_change_percent: float
    data_points: int
    wallet_events: list[WalletEvent]
    wallet_breakdown: list[WalletBreakdown]
    metadata: PortfolioHistoryMetadata


# ============================================================
# Helper Functions
# ============================================================

def parse_wallet_date(date_value) -> datetime:
    """Parse wallet creation date from various formats."""
    if date_value is None:
        return datetime.utcnow() - timedelta(days=7)
    
    if isinstance(date_value, datetime):
        if date_value.tzinfo is not None:
            return date_value.replace(tzinfo=None)
        return date_value
    
    if isinstance(date_value, str):
        try:
            parsed = parser.parse(date_value)
            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)
            return parsed
        except Exception as e:
            print(f"[WARNING] Failed to parse date '{date_value}': {e}")
            return datetime.utcnow() - timedelta(days=7)
    
    print(f"[WARNING] Unknown date type: {type(date_value)}")
    return datetime.utcnow() - timedelta(days=7)


# ============================================================
# Endpoints
# ============================================================

@router.get("/prices/history/{symbol}", response_model=PriceHistoryResponse)
def get_price_history(
    symbol: str,
    days: int = Query(7, ge=1, le=365, description="Number of days (1-365)"),
    chain: Optional[str] = Query(None, description="Optional chain hint: aptos or solana")
):
    """Get historical price data for a token."""
    symbol = symbol.upper()
    
    if days not in [1, 7, 30, 90, 365]:
        valid_days = [1, 7, 30, 90, 365]
        days = min(valid_days, key=lambda x: abs(x - days))
    
    history = history_service.get_price_history(symbol, days=days, chain=chain)
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"Price history not available for {symbol}"
        )
    
    return history


@router.post("/portfolio/detailed", response_model=DetailedPortfolioHistoryResponse)
async def get_detailed_portfolio_history(
    days: int = Query(7, ge=1, le=365, description="Number of days (1-365)"),
    wallet_id: Optional[str] = Query(None, description="Optional: Filter to specific wallet ID"),
    use_snapshots: bool = Query(True, description="Use snapshots if available"),  # ✨ NEW
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed portfolio history with wallet events and breakdown.
    
    ✅ Uses database snapshots for accurate historical data (when available)
    ✅ Falls back to approximation if insufficient snapshots
    ✅ Supports filtering to specific wallet
    
    Parameters:
    - days: Number of days to show (1-365)
    - wallet_id: Optional wallet ID to filter to specific wallet
    - use_snapshots: Whether to use snapshots (default: true)
    
    Returns:
    - Portfolio value over time
    - Wallet events (additions)
    - Current breakdown
    - Metadata about calculation and data source
    """
    from app.services.db import wallets_collection, snapshots_collection
    from app.services.adapters.aptos_adapter import AptosAdapter
    from app.services.adapters.solana_adapter import SolanaAdapter
    from app.services.adapters import get_adapter_for_chain, is_evm_chain
    import os
    
    user_id = str(current_user["_id"])
    all_user_wallets = list(wallets_collection.find({"user_id": user_id}))
    
    if not all_user_wallets:
        raise HTTPException(status_code=404, detail="No wallets found")
    
    # Filter to specific wallet if requested
    if wallet_id:
        print(f"[HISTORY] 🎯 Filtering to specific wallet: {wallet_id}")
        filtered_wallets = [w for w in all_user_wallets if str(w["_id"]) == wallet_id]
        
        if not filtered_wallets:
            raise HTTPException(
                status_code=404,
                detail=f"Wallet {wallet_id} not found or doesn't belong to user"
            )
        
        wallets = filtered_wallets
        scope = wallet_id
        scope_label = wallets[0].get("label", "Wallet")
        print(f"[HISTORY] 📊 Scope: Single wallet '{scope_label}'")
    else:
        print(f"[HISTORY] 📊 Scope: Complete portfolio (all {len(all_user_wallets)} wallets)")
        wallets = all_user_wallets
        scope = "all_wallets"
        scope_label = "Complete Portfolio"
    
    # ============================================================
    # ✨ NEW: TRY SNAPSHOTS FIRST
    # ============================================================
    
    if use_snapshots:
        print(f"[HISTORY] 📸 Attempting to use snapshots for {days} days")
        
        snapshot_service = SnapshotService(
            snapshots_collection=snapshots_collection,
            wallets_collection=wallets_collection,
            price_service=price_service
        )
        
        snapshot_history = snapshot_service.get_snapshot_history(
            user_id=user_id,
            days=days,
            wallet_id=wallet_id
        )
        
        # Check if we have sufficient snapshot coverage (>= 70%)
        if snapshot_history and snapshot_history.coverage_percent >= 70:
            print(f"[HISTORY] ✅ Using snapshots ({snapshot_history.coverage_percent:.1f}% coverage)")
            
            # Get wallet info for metadata
            wallet_dates = [(w, parse_wallet_date(w.get("created_at"))) for w in wallets]
            wallets_sorted = sorted(wallet_dates, key=lambda x: x[1])
            earliest_wallet, earliest_date = wallets_sorted[0]
            
            wallet_age = datetime.utcnow() - earliest_date
            wallet_age_days = max(wallet_age.days, 1)
            
            # Convert snapshot history to detailed response
            # Note: We skip wallet_events and wallet_breakdown for snapshot-based history
            # to avoid recalculating current balances (they can be added if needed)
            
            # ✅ FIX: Convert SnapshotHistoryPoint to PortfolioValuePoint
            portfolio_values = [
                PortfolioValuePoint(
                    timestamp=point.timestamp,
                    value=point.value
                )
                for point in snapshot_history.values
            ]
            
            return DetailedPortfolioHistoryResponse(
                values=portfolio_values,
                current_value=snapshot_history.current_value,
                period_change=snapshot_history.period_change,
                period_change_percent=snapshot_history.period_change_percent,
                data_points=snapshot_history.data_points,
                wallet_events=[],  # TODO: Can calculate from current wallet data if needed
                wallet_breakdown=[],  # TODO: Can calculate from current wallet data if needed
                metadata=PortfolioHistoryMetadata(
                    earliest_wallet_date=earliest_date.strftime("%Y-%m-%d"),
                    wallet_age_days=wallet_age_days,
                    requested_days=days,
                    actual_days_shown=days,
                    scope=scope,
                    scope_label=scope_label,
                    data_source="snapshots",  # ✨ NEW
                    coverage_percent=snapshot_history.coverage_percent,  # ✨ NEW
                    disclaimer=(
                        f"📸 Portfolio values from accurate database snapshots ({snapshot_history.coverage_percent:.1f}% coverage). "
                        f"Data represents {scope_label}. "
                        f"Snapshots capture real portfolio state daily."
                    )
                )
            )
        else:
            coverage = snapshot_history.coverage_percent if snapshot_history else 0
            print(f"[HISTORY] ⚠️  Insufficient snapshots ({coverage:.1f}% coverage), falling back to approximation")
    
    # ============================================================
    # FALLBACK: USE APPROXIMATION METHOD
    # ============================================================
    
    print(f"[HISTORY] 🔄 Using approximation method")
    
    # Parse wallet dates and sort by creation
    wallet_dates = [(w, parse_wallet_date(w.get("created_at"))) for w in wallets]
    wallets_sorted = sorted(wallet_dates, key=lambda x: x[1])
    
    earliest_wallet, earliest_date = wallets_sorted[0]
    
    wallet_age = datetime.utcnow() - earliest_date
    wallet_age_days = max(wallet_age.days, 1)
    actual_days = min(days, wallet_age_days)
    
    print(f"[HISTORY] Detailed history for user {user_id}:")
    print(f"[HISTORY]   Scope: {scope_label}")
    print(f"[HISTORY]   Wallets in scope: {len(wallets)}")
    print(f"[HISTORY]   Earliest wallet: {earliest_date.strftime('%Y-%m-%d')}")
    print(f"[HISTORY]   Requested: {days} days, showing: {actual_days} days")
    
    # Initialize adapters — use mainnet by default (testnet wallets have no real value)
    aptos_rpc = os.getenv("APTOS_RPC_URL", "https://fullnode.mainnet.aptoslabs.com/v1")
    solana_rpc = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

    aptos_client = AptosAdapter(rpc_url=aptos_rpc)
    solana_client = SolanaAdapter(rpc_url=solana_rpc)

    # EVM chains to expand "evm" into
    EVM_TESTNET_CHAINS = ["ethereum_sepolia", "polygon_amoy", "base_sepolia"]

    # Calculate portfolio value for EACH wallet
    wallet_values: Dict[str, float] = {}
    all_balances = []

    for wallet_doc in wallets:
        wallet_id_str = str(wallet_doc["_id"])
        address = wallet_doc.get("address")
        chain = wallet_doc.get("chain", "aptos")

        print(f"[HISTORY] Processing wallet: {wallet_doc.get('label')} ({chain})")

        # Check shared cache for recently fetched balances (e.g., from multi-wallet endpoint)
        balance_cache_key = f"balances:{chain}:{address}"
        cached_balances = cache.get(balance_cache_key)

        try:
            if cached_balances is not None:
                print(f"[HISTORY]   ✓ Using cached balances for {chain}:{address[:10]}...")
                balances = cached_balances if isinstance(cached_balances, list) else []
            elif chain == "aptos":
                balances = aptos_client.get_token_balances(address)
            elif chain == "solana":
                balances = solana_client.get_token_balances(address)
            elif chain == "evm" or is_evm_chain(chain):
                # For "evm" wallets, query all EVM testnet chains
                # For specific EVM chains (e.g., "ethereum_sepolia"), query just that one
                evm_chains = EVM_TESTNET_CHAINS if chain == "evm" else [chain]
                balances = []
                for evm_chain in evm_chains:
                    try:
                        evm_cache_key = f"balances:{evm_chain}:{address}"
                        evm_cached = cache.get(evm_cache_key)
                        if evm_cached is not None:
                            print(f"[HISTORY]   ✓ Using cached balances for {evm_chain}")
                            chain_balances = evm_cached if isinstance(evm_cached, list) else []
                        else:
                            adapter = get_adapter_for_chain(evm_chain)
                            chain_balances = adapter.get_token_balances(address)
                        for bal in chain_balances:
                            bal["chain"] = evm_chain
                        balances.extend(chain_balances)
                    except Exception as evm_err:
                        print(f"[HISTORY]   ⚠ Failed to fetch from {evm_chain}: {evm_err}")
            else:
                print(f"[WARNING] Unknown chain: {chain}")
                continue
            
            wallet_value = 0.0
            tokens_processed = 0
            tokens_failed = 0
            
            print(f"[HISTORY]   Found {len(balances)} token balances")
            
            for balance in balances:
                symbol = balance.get("symbol")
                amount = balance.get("amount", 0)
                
                if not symbol or amount <= 0:
                    continue
                
                try:
                    usd_price = price_service.get_price(symbol, chain=chain)
                    
                    if usd_price and usd_price > 0:
                        usd_value = float(amount) * float(usd_price)
                        wallet_value += usd_value
                        tokens_processed += 1
                        
                        print(f"[HISTORY]     ✓ {symbol}: {amount} × ${usd_price} = ${usd_value:.2f}")
                        
                        # Add to all_balances for history calculation
                        existing = next((b for b in all_balances if b["symbol"] == symbol), None)
                        if existing:
                            existing["amount"] += amount
                        else:
                            all_balances.append({"symbol": symbol, "amount": amount})
                    else:
                        tokens_failed += 1
                        print(f"[WARNING]     ✗ {symbol}: No price found (amount: {amount})")
                        
                except Exception as price_error:
                    tokens_failed += 1
                    print(f"[WARNING]     ✗ {symbol}: Price fetch failed - {price_error}")
            
            wallet_values[wallet_id_str] = wallet_value
            print(f"[HISTORY]   Wallet total: ${wallet_value:.2f} ({tokens_processed} tokens, {tokens_failed} failed)")
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch balances for {address}: {e}")
            wallet_values[wallet_id_str] = 0.0
            continue
    
    if not all_balances:
        print("[ERROR] No token balances found with valid prices")
        raise HTTPException(status_code=404, detail="No token balances found with valid prices")
    
    print(f"[HISTORY] Total unique tokens: {len(all_balances)}")
    
    # Get portfolio history
    history = history_service.get_portfolio_history(all_balances, days=actual_days)
    
    if not history:
        raise HTTPException(status_code=500, detail="Failed to calculate portfolio history")
    
    print(f"[HISTORY] Generated {history['data_points']} historical data points")
    
    # Generate wallet events
    wallet_events: List[WalletEvent] = []
    cumulative_value = 0.0
    
    for wallet_doc, created_at in wallets_sorted:
        wallet_id_str = str(wallet_doc["_id"])
        label = wallet_doc.get("label", "Wallet")
        chain = wallet_doc.get("chain", "aptos")
        wallet_value = wallet_values.get(wallet_id_str, 0.0)
        
        value_before = cumulative_value
        value_after = cumulative_value + wallet_value
        cumulative_value = value_after
        
        # Only include events within the requested time range
        event_age = (datetime.utcnow() - created_at).days
        if event_age <= actual_days:
            wallet_events.append(WalletEvent(
                date=created_at.strftime("%Y-%m-%d"),
                timestamp=int(created_at.timestamp()),
                type="wallet_added",
                wallet_id=wallet_id_str,
                wallet_label=label,
                wallet_chain=chain,
                value_before=round(value_before, 2),
                value_after=round(value_after, 2),
                impact=round(wallet_value, 2)
            ))
    
    print(f"[HISTORY] Generated {len(wallet_events)} wallet events")
    
    # Generate wallet breakdown
    wallet_breakdown: List[WalletBreakdown] = []
    total_value = sum(wallet_values.values())
    
    print(f"[HISTORY] Total portfolio value: ${total_value:.2f}")
    
    for wallet_doc, created_at in wallets_sorted:
        wallet_id_str = str(wallet_doc["_id"])
        label = wallet_doc.get("label", "Wallet")
        chain = wallet_doc.get("chain", "aptos")
        wallet_value = wallet_values.get(wallet_id_str, 0.0)
        
        percentage = (wallet_value / total_value * 100) if total_value > 0 else 0
        age_days = (datetime.utcnow() - created_at).days
        
        wallet_breakdown.append(WalletBreakdown(
            wallet_id=wallet_id_str,
            label=label,
            chain=chain,
            current_value=round(wallet_value, 2),
            percentage=round(percentage, 2),
            created_at=created_at.strftime("%Y-%m-%d"),
            age_days=age_days
        ))
    
    print(f"[HISTORY] Wallet breakdown:")
    for wb in wallet_breakdown:
        print(f"  - {wb.label} ({wb.chain}): ${wb.current_value:.2f} ({wb.percentage:.1f}%)")
    
    # Return enhanced response with approximation metadata
    return DetailedPortfolioHistoryResponse(
        values=history["values"],
        current_value=history["current_value"],
        period_change=history["period_change"],
        period_change_percent=history["period_change_percent"],
        data_points=history["data_points"],
        wallet_events=wallet_events,
        wallet_breakdown=wallet_breakdown,
        metadata=PortfolioHistoryMetadata(
            earliest_wallet_date=earliest_date.strftime("%Y-%m-%d"),
            wallet_age_days=wallet_age_days,
            requested_days=days,
            actual_days_shown=actual_days,
            scope=scope,
            scope_label=scope_label,
            data_source="approximation",  # ✨ NEW
            coverage_percent=0.0,  # ✨ NEW
            disclaimer=(
                f"Portfolio values based on {scope_label}. "
                f"Historical data limited to {actual_days} days (wallet age). "
                f"⚠️ Values calculated using approximation (current balances × historical prices). "
                f"For accurate data, wait for snapshots to accumulate (5-7 days)."
            )
        )
    )


@router.delete("/cache/clear")
async def clear_cache(current_user: dict = Depends(get_current_user)):
    """Clear price history cache."""
    history_service.clear_cache()
    
    return {
        "message": "History cache cleared",
        "user_id": str(current_user["_id"])
    }