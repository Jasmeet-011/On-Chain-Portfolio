# backend/app/models/alert_models.py - COMPLETE VERSION
"""
Alert Data Models - Complete 3-Tier System + Token Alerts
This file supports both simple token alerts AND the full 3-tier system
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, List
from datetime import datetime


# ============================================================
# ALERT TYPE DEFINITIONS
# ============================================================

AlertType = Literal["portfolio", "token", "wallet"]
AlertCondition = Literal["above", "below", "equals"]
PortfolioMetric = Literal["value", "change_percent", "risk_level", "concentration"]
AlertStatus = Literal["active", "paused", "triggered", "expired"]


# ============================================================
# TIER 1: PORTFOLIO ALERTS
# ============================================================

class PortfolioAlertCreate(BaseModel):
    """Create a portfolio-level alert"""
    alert_type: Literal["portfolio"] = "portfolio"
    portfolio_metric: PortfolioMetric
    condition: AlertCondition
    target_value: float = Field(gt=0, description="Target value for the metric")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_type": "portfolio",
                "portfolio_metric": "value",
                "condition": "below",
                "target_value": 10000
            }
        }


# ============================================================
# TIER 2: TOKEN ALERTS
# ============================================================

class TokenAlertCreate(BaseModel):
    """Create a token price alert"""
    alert_type: Literal["token"] = "token"
    token_symbol: str = Field(min_length=1, description="Token symbol (e.g., SOL, APT)")
    condition: AlertCondition
    target_price: float = Field(gt=0, description="Target price in USD")
    wallet_address: Optional[str] = Field(
        default=None,
        description="Specific wallet to track, null = all wallets"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_type": "token",
                "token_symbol": "SOL",
                "condition": "above",
                "target_price": 150.0,
                "wallet_address": None
            }
        }


# ============================================================
# TIER 3: WALLET ALERTS
# ============================================================

class WalletAlertCreate(BaseModel):
    """Create a wallet-specific alert"""
    alert_type: Literal["wallet"] = "wallet"
    wallet_address: str = Field(min_length=1, description="Wallet address to track")
    condition: AlertCondition
    target_value: float = Field(gt=0, description="Target wallet value in USD")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_type": "wallet",
                "wallet_address": "0x123...",
                "condition": "above",
                "target_value": 5000.0
            }
        }


# ============================================================
# UNIFIED ALERT MODEL
# ============================================================

class AlertCreate(BaseModel):
    """Create any type of alert (unified)"""
    alert_type: AlertType

    # TIER 1: Portfolio fields
    portfolio_metric: Optional[PortfolioMetric] = None

    # TIER 2: Token fields
    token_symbol: Optional[str] = None
    target_price: Optional[float] = None

    # TIER 3: Wallet fields
    wallet_address: Optional[str] = None
    target_value: Optional[float] = None

    # Common fields
    condition: AlertCondition

    @model_validator(mode='after')
    def validate_fields(self):
        """Validate that required fields are present for alert type"""
        if self.alert_type == "portfolio":
            if not self.portfolio_metric or not self.target_value:
                raise ValueError("Portfolio alerts require portfolio_metric and target_value")

        elif self.alert_type == "token":
            if not self.token_symbol or not self.target_price:
                raise ValueError("Token alerts require token_symbol and target_price")

        elif self.alert_type == "wallet":
            if not self.wallet_address or not self.target_value:
                raise ValueError("Wallet alerts require wallet_address and target_value")

        return self


# ============================================================
# SIMPLE TOKEN ALERT (For Current Router)
# ============================================================

class CreateAlertRequest(BaseModel):
    """
    Simple token price alert request.
    This is what the current router uses.
    """
    token_symbol: str = Field(min_length=1, description="Token symbol")
    target_price: float = Field(gt=0, description="Target price in USD")
    condition: Literal["above", "below"] = Field(description="Price condition")
    wallet_address: Optional[str] = Field(default=None, description="Optional specific wallet")
    chain: Optional[str] = Field(default="solana", description="Blockchain chain for the token")
    is_recurring: bool = Field(default=False, description="Re-trigger alert each time condition is met (every 1h)")

    class Config:
        json_schema_extra = {
            "example": {
                "token_symbol": "SOL",
                "target_price": 150.0,
                "condition": "above",
                "wallet_address": None,
                "chain": "solana",
                "is_recurring": False
            }
        }
    
    def to_alert_create(self) -> AlertCreate:
        """Convert to AlertCreate model"""
        return AlertCreate(
            alert_type="token",
            token_symbol=self.token_symbol,
            target_price=self.target_price,
            condition=self.condition,
            wallet_address=self.wallet_address
        )


class UpdateAlertRequest(BaseModel):
    """Request model for updating alerts"""
    is_active: Optional[bool] = Field(default=None, description="Enable/disable alert")
    target_price: Optional[float] = Field(default=None, gt=0, description="Update target price")
    condition: Optional[Literal["above", "below"]] = Field(default=None, description="Update condition")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_active": False,
                "target_price": 160.0,
                "condition": "above"
            }
        }


# ============================================================
# RESPONSE MODELS
# ============================================================

class AlertResponse(BaseModel):
    """Alert response model - supports all 3 tiers"""
    id: str
    user_id: str
    alert_type: AlertType = "token"
    
    # TIER 1: Portfolio fields
    portfolio_metric: Optional[PortfolioMetric] = None
    
    # TIER 2: Token fields
    token_symbol: Optional[str] = None
    target_price: Optional[float] = None
    chain: Optional[str] = "aptos"
    
    # TIER 3: Wallet fields
    wallet_address: Optional[str] = None
    target_value: Optional[float] = None
    
    # Common fields
    condition: AlertCondition
    is_active: bool = True
    is_recurring: Optional[bool] = False
    status: Optional[str] = "active"
    current_price: Optional[float] = None
    last_triggered: Optional[datetime] = None
    trigger_count: Optional[int] = 0
    last_checked: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    alert_summary: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "alert_123",
                    "user_id": "user_456",
                    "alert_type": "token",
                    "token_symbol": "SOL",
                    "chain": "aptos",
                    "condition": "above",
                    "target_price": 150.0,
                    "wallet_address": None,
                    "is_active": True,
                    "is_recurring": False,
                    "status": "active",
                    "created_at": "2025-01-01T00:00:00Z"
                }
            ]
        }


class AlertUpdate(BaseModel):
    """Update alert fields"""
    is_active: Optional[bool] = None
    target_value: Optional[float] = None
    target_price: Optional[float] = None
    condition: Optional[AlertCondition] = None


class AlertListResponse(BaseModel):
    """List of alerts response"""
    alerts: List[AlertResponse]
    total: int
    portfolio_alerts: int = 0
    token_alerts: int = 0
    wallet_alerts: int = 0


class AlertStatsResponse(BaseModel):
    """Statistics about user's alerts"""
    total_alerts: int
    active_alerts: int
    triggered_today: int
    triggered_this_week: int
    triggered_total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_alerts": 8,
                "active_alerts": 5,
                "triggered_today": 1,
                "triggered_this_week": 2,
                "triggered_total": 10
            }
        }


# ============================================================
# ALERT TRIGGER EVENTS
# ============================================================

class AlertTriggerEvent(BaseModel):
    """Event data when alert is triggered"""
    alert_id: str
    user_id: str
    alert_type: AlertType
    triggered_at: datetime
    
    # Current values
    current_value: float
    target_value: float
    condition_met: str
    
    # Additional context
    portfolio_snapshot: Optional[dict] = None
    token_holdings: Optional[dict] = None
    wallet_snapshot: Optional[dict] = None


# ============================================================
# ALERT CHECKING RESPONSES
# ============================================================

class AlertCheckResult(BaseModel):
    """Result of checking an alert"""
    alert_id: str
    checked_at: datetime
    was_triggered: bool
    current_value: Optional[float] = None
    message: Optional[str] = None


# ============================================================
# DATABASE MODELS
# ============================================================

class AlertDocument(BaseModel):
    """Alert document for database storage"""
    _id: Optional[str] = None
    user_id: str
    user_email: Optional[str] = None
    alert_type: AlertType = "token"
    
    # TIER 1
    portfolio_metric: Optional[str] = None
    
    # TIER 2
    token_symbol: Optional[str] = None
    target_price: Optional[float] = None
    chain: Optional[str] = "aptos"
    
    # TIER 3
    wallet_address: Optional[str] = None
    target_value: Optional[float] = None
    
    # Common
    condition: str
    is_active: bool = True
    is_recurring: bool = False
    status: str = "active"
    current_price: Optional[float] = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    last_checked: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Notification settings
    notification_sent: bool = False
    notification_sent_at: Optional[datetime] = None


# ============================================================
# EMAIL NOTIFICATION DATA MODELS
# ============================================================

class PriceAlertEmailData(BaseModel):
    """Data for price alert email notifications"""
    user_email: str
    user_name: str
    token_symbol: str
    chain: str
    alert_type: str  # "above" or "below"
    target_price: float
    current_price: float
    change_24h: float
    change_percent: float
    is_recurring: bool
    wallet_address: Optional[str] = None
    alert_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "user_name": "John",
                "token_symbol": "SOL",
                "chain": "aptos",
                "alert_type": "above",
                "target_price": 150.0,
                "current_price": 152.34,
                "change_24h": 5.2,
                "change_percent": 3.5,
                "is_recurring": False,
                "wallet_address": None,
                "alert_id": "alert_123"
            }
        }


class DailyDigestEmailData(BaseModel):
    """Data for daily digest email"""
    user_email: str
    user_name: str
    portfolio_value: float
    change_24h: float
    change_percent: float
    top_gainer: Optional[dict] = None
    top_loser: Optional[dict] = None
    total_tokens: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "user_name": "John",
                "portfolio_value": 10000.0,
                "change_24h": 250.0,
                "change_percent": 2.5,
                "top_gainer": {"symbol": "SOL", "change_percent": 5.2},
                "top_loser": {"symbol": "APT", "change_percent": -2.1},
                "total_tokens": 12
            }
        }


class WeeklySummaryEmailData(BaseModel):
    """Data for weekly summary email"""
    user_email: str
    user_name: str
    portfolio_value_start: float
    portfolio_value_end: float
    change_week: float
    change_percent: float
    best_performer: Optional[dict] = None
    worst_performer: Optional[dict] = None
    alerts_triggered: int
    total_tokens: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "user_name": "John",
                "portfolio_value_start": 9500.0,
                "portfolio_value_end": 10000.0,
                "change_week": 500.0,
                "change_percent": 5.26,
                "best_performer": {"symbol": "SOL", "change_percent": 15.0},
                "worst_performer": {"symbol": "APT", "change_percent": -5.0},
                "alerts_triggered": 3,
                "total_tokens": 12
            }
        }


class MilestoneEmailData(BaseModel):
    """Data for milestone notifications"""
    user_email: str
    user_name: str
    token_symbol: str
    message: str
    current_price: float
    previous_record: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "user_name": "John",
                "token_symbol": "SOL",
                "message": "SOL just hit a new all-time high!",
                "current_price": 200.0,
                "previous_record": 180.0
            }
        }


# ============================================================
# EMAIL PREFERENCES
# ============================================================

class EmailPreferencesRequest(BaseModel):
    """Request model for updating email preferences"""
    price_alerts_enabled: Optional[bool] = Field(default=None, description="Enable price alert emails")
    daily_digest_enabled: Optional[bool] = Field(default=None, description="Enable daily digest emails")
    weekly_summary_enabled: Optional[bool] = Field(default=None, description="Enable weekly summary emails")
    
    class Config:
        json_schema_extra = {
            "example": {
                "price_alerts_enabled": True,
                "daily_digest_enabled": True,
                "weekly_summary_enabled": False
            }
        }


class EmailPreferencesResponse(BaseModel):
    """Response model for email preferences"""
    user_id: str
    price_alerts_enabled: bool = True
    daily_digest_enabled: bool = True
    weekly_summary_enabled: bool = True
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "price_alerts_enabled": True,
                "daily_digest_enabled": True,
                "weekly_summary_enabled": False,
                "updated_at": "2025-01-01T00:00:00Z"
            }
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_alert_summary(alert: AlertResponse) -> str:
    """Generate human-readable alert summary"""
    
    if alert.alert_type == "portfolio":
        metric_labels = {
            "value": "portfolio value",
            "change_percent": "portfolio change",
            "risk_level": "risk level",
            "concentration": "token concentration"
        }
        metric = metric_labels.get(alert.portfolio_metric, alert.portfolio_metric)
        
        if alert.portfolio_metric == "change_percent":
            return f"Alert when {metric} changes by {alert.condition} {alert.target_value}%"
        else:
            return f"Alert when {metric} {alert.condition} ${alert.target_value:,.2f}"
    
    elif alert.alert_type == "token":
        scope = "all wallets" if not alert.wallet_address else "specific wallet"
        return f"Alert when {alert.token_symbol} goes {alert.condition} ${alert.target_price:.2f} ({scope})"
    
    elif alert.alert_type == "wallet":
        addr_short = f"{alert.wallet_address[:6]}...{alert.wallet_address[-4:]}" if alert.wallet_address else "unknown"
        return f"Alert when wallet {addr_short} value {alert.condition} ${alert.target_value:,.2f}"
    
    return "Alert"