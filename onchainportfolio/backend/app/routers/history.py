# backend/app/routers/history.py - CORRECTED: Snapshot Integration
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from dateutil import parser

from app.services.history_service import HistoryService
from app.services.snapshot_service import SnapshotService
from app.deps import get_current_user, price_service

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
    use_snapshots: bool = Query(True, description="Reserved for backward compat — always True"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed portfolio history backed exclusively by real database snapshots.

    - Returns only real data; never approximates or fabricates values.
    - If no snapshots exist yet (new user), returns 404 with a clear message.
    - coverage_percent in metadata indicates how many of the requested days
      have at least one snapshot (0-100).
    - wallet_events are sourced from the portfolio_events collection.
    """
    from app.services.db import wallets_collection, snapshots_collection, portfolio_events_collection

    user_id = str(current_user["_id"])

    # Only consider active wallets
    all_user_wallets = list(wallets_collection.find({"user_id": user_id, "is_active": True}))

    if not all_user_wallets:
        raise HTTPException(status_code=404, detail="No wallets found")

    # ── Scope resolution ────────────────────────────────────────────────────
    if wallet_id:
        wallets = [w for w in all_user_wallets if str(w["_id"]) == wallet_id]
        if not wallets:
            raise HTTPException(
                status_code=404,
                detail=f"Wallet {wallet_id} not found or does not belong to this user"
            )
        scope = wallet_id
        scope_label = wallets[0].get("label", "Wallet")
    else:
        wallets = all_user_wallets
        scope = "all_wallets"
        scope_label = "Complete Portfolio"

    print(f"[HISTORY] Scope: {scope_label} | Requested: {days} days")

    # ── Snapshot retrieval ──────────────────────────────────────────────────
    snapshot_service = SnapshotService(
        snapshots_collection=snapshots_collection,
        wallets_collection=wallets_collection,
        price_service=price_service
    )

    # When filtering by wallet_id, snapshots are stored with wallet_id=None
    # (all-wallet aggregate). Fall back to user-level snapshot for all scopes.
    snapshot_history = snapshot_service.get_snapshot_history(
        user_id=user_id,
        days=days,
        wallet_id=None  # always use the user-level aggregate snapshot
    )

    if not snapshot_history:
        raise HTTPException(
            status_code=404,
            detail=(
                "No snapshot data available yet. "
                "Snapshots are captured every 6 hours — check back later."
            )
        )

    print(f"[HISTORY] Snapshots found: {snapshot_history.data_points} points, "
          f"{snapshot_history.coverage_percent:.1f}% day coverage")

    # ── Wallet metadata ─────────────────────────────────────────────────────
    wallet_dates = [(w, parse_wallet_date(w.get("created_at"))) for w in wallets]
    wallets_sorted = sorted(wallet_dates, key=lambda x: x[1])
    _, earliest_date = wallets_sorted[0]
    wallet_age_days = max((datetime.utcnow() - earliest_date).days, 1)

    # ── Wallet events from portfolio_events collection ──────────────────────
    cutoff = datetime.utcnow() - timedelta(days=days)
    raw_events = list(portfolio_events_collection.find(
        {
            "user_id": user_id,
            "timestamp": {"$gte": cutoff}
        },
        sort=[("timestamp", 1)]
    ))

    wallet_events: List[WalletEvent] = []
    for ev in raw_events:
        ts: datetime = ev.get("timestamp", datetime.utcnow())
        wallet_events.append(WalletEvent(
            date=ts.strftime("%Y-%m-%d"),
            timestamp=int(ts.timestamp()),
            type=ev.get("event_type", "wallet_added"),
            wallet_id=ev.get("wallet_address", ""),   # address used as id here
            wallet_label=ev.get("wallet_address", "")[:10] + "...",
            wallet_chain=ev.get("chain", "unknown"),
            # Dollar values are not stored at event time — set to 0.
            # The chart (snapshot data) provides accurate dollar history.
            value_before=0.0,
            value_after=0.0,
            impact=0.0
        ))

    # ── Build response ──────────────────────────────────────────────────────
    portfolio_values = [
        PortfolioValuePoint(timestamp=pt.timestamp, value=pt.value)
        for pt in snapshot_history.values
    ]

    return DetailedPortfolioHistoryResponse(
        values=portfolio_values,
        current_value=snapshot_history.current_value,
        period_change=snapshot_history.period_change,
        period_change_percent=snapshot_history.period_change_percent,
        data_points=snapshot_history.data_points,
        wallet_events=wallet_events,
        wallet_breakdown=[],   # requires live balance fetch — available via /v1/wallets
        metadata=PortfolioHistoryMetadata(
            earliest_wallet_date=earliest_date.strftime("%Y-%m-%d"),
            wallet_age_days=wallet_age_days,
            requested_days=days,
            actual_days_shown=days,
            scope=scope,
            scope_label=scope_label,
            data_source="snapshots",
            coverage_percent=snapshot_history.coverage_percent,
            disclaimer=(
                f"Portfolio values from real database snapshots "
                f"({snapshot_history.coverage_percent:.1f}% day coverage over {days} days). "
                f"Snapshots are captured every 6 hours."
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