# app/schemas/wallet.py
from pydantic import BaseModel, Field
from typing import Optional, Literal

# ============================================================
# Wallet Request Models
# ============================================================

class WalletCreateRequest(BaseModel):
    """Request to add a new wallet."""
    address: str = Field(min_length=10, max_length=200)
    type: Literal["petra", "manual"] = "manual"
    label: str = Field(default="Main Wallet", min_length=1, max_length=100)
    is_primary: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x06c5252a6b7e37cdf543cd3ac0d5699c52b6dd7bb3d82fea8acefa8f6f607094",
                "type": "manual",
                "label": "Trading Wallet",
                "is_primary": True
            }
        }

class WalletUpdateLabelRequest(BaseModel):
    """Request to update wallet label."""
    label: str = Field(min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "Cold Storage Wallet"
            }
        }

class WalletSetPrimaryRequest(BaseModel):
    """Request to set a wallet as primary (by address)."""
    address: str = Field(min_length=10, max_length=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x06c5252a6b7e37cdf543cd3ac0d5699c52b6dd7bb3d82fea8acefa8f6f607094"
            }
        }

# ============================================================
# Wallet Response Models
# ============================================================

class WalletResponse(BaseModel):
    """Wallet information returned to client."""
    id: str
    user_id: str
    address: str
    type: Literal["petra", "manual"]
    label: str
    is_primary: bool
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "user_id": "507f191e810c19729de860ea",
                "address": "0x06c5252a6b7e37cdf543cd3ac0d5699c52b6dd7bb3d82fea8acefa8f6f607094",
                "type": "petra",
                "label": "Main Wallet",
                "is_primary": True,
                "created_at": "2025-01-15T10:30:00.000Z"
            }
        }

class WalletListResponse(BaseModel):
    """List of wallets with metadata."""
    wallets: list[WalletResponse]
    total: int
    primary: Optional[WalletResponse] = None