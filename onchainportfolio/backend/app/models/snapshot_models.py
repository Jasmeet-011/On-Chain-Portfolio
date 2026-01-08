# backend/app/models/snapshot_models.py
"""
Portfolio Snapshot Models

Snapshots store historical portfolio state for accurate charts.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ============================================================
# SNAPSHOT DATA MODELS
# ============================================================

class SnapshotBalance(BaseModel):
    """Individual token balance in a snapshot."""
    symbol: str
    amount: float
    price_usd: float
    value_usd: float
    chain: str  # "aptos" or "solana"


class PortfolioSnapshot(BaseModel):
    """Complete portfolio snapshot at a point in time."""
    user_id: str
    wallet_id: Optional[str] = None  # None = all wallets, or specific wallet ID
    snapshot_date: datetime  # Date portion (midnight UTC)
    timestamp: datetime  # Actual capture time
    
    # Portfolio data
    total_value_usd: float
    total_tokens: int
    wallet_count: int
    
    # Individual balances
    balances: List[SnapshotBalance]
    
    # Chain breakdown
    chain_breakdown: Dict[str, float] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "wallet_id": None,
                "snapshot_date": "2025-01-03T00:00:00Z",
                "timestamp": "2025-01-03T00:05:23Z",
                "total_value_usd": 1250.50,
                "total_tokens": 5,
                "wallet_count": 2,
                "balances": [
                    {
                        "symbol": "SOL",
                        "amount": 10.5,
                        "price_usd": 100.0,
                        "value_usd": 1050.0,
                        "chain": "solana"
                    }
                ],
                "chain_breakdown": {
                    "aptos": 200.0,
                    "solana": 1050.0
                }
            }
        }


class SnapshotHistoryPoint(BaseModel):
    """Single point in snapshot history for charts."""
    timestamp: int  # Unix timestamp
    value: float  # Total USD value
    token_count: int
    wallet_count: int


class SnapshotHistoryResponse(BaseModel):
    """Response for snapshot-based history query."""
    values: List[SnapshotHistoryPoint]
    current_value: float
    period_change: float
    period_change_percent: float
    data_points: int
    data_source: str = "snapshots"  # "snapshots" or "approximation"
    coverage_percent: float  # Percentage of requested days with snapshots
    
    class Config:
        json_schema_extra = {
            "example": {
                "values": [
                    {
                        "timestamp": 1704067200,
                        "value": 1000.0,
                        "token_count": 5,
                        "wallet_count": 2
                    }
                ],
                "current_value": 1250.50,
                "period_change": 250.50,
                "period_change_percent": 25.05,
                "data_points": 7,
                "data_source": "snapshots",
                "coverage_percent": 100.0
            }
        }


# ============================================================
# SNAPSHOT MANAGEMENT MODELS
# ============================================================

class CreateSnapshotRequest(BaseModel):
    """Request to create a snapshot."""
    user_id: Optional[str] = None  # None = all users
    wallet_id: Optional[str] = None  # None = all wallets
    force: bool = False  # Force creation even if exists today


class SnapshotStatsResponse(BaseModel):
    """Statistics about snapshots."""
    total_snapshots: int
    oldest_snapshot: Optional[datetime] = None
    newest_snapshot: Optional[datetime] = None
    users_with_snapshots: int
    average_value_usd: float
    total_storage_mb: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_snapshots": 150,
                "oldest_snapshot": "2024-12-01T00:00:00Z",
                "newest_snapshot": "2025-01-03T00:00:00Z",
                "users_with_snapshots": 10,
                "average_value_usd": 2500.0,
                "total_storage_mb": 2.5
            }
        }