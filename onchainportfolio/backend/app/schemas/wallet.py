# app/schemas/wallet.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal

# Supported chains
ChainType = Literal["aptos", "solana"]
WalletType = Literal["petra", "phantom", "solflare", "manual"]

# ============================================================
# Wallet Request Models
# ============================================================

class WalletCreateRequest(BaseModel):
    """Request to add a new wallet."""
    address: str = Field(min_length=1, max_length=200)
    chain: ChainType = "aptos"  # ← NEW: Chain identifier
    type: WalletType = "manual"
    label: str = Field(default="Main Wallet", min_length=1, max_length=100)
    is_primary: bool = False
    
    @validator('chain')
    def validate_chain(cls, v):
        """Ensure chain is lowercase."""
        return v.lower()
    
    @validator('type')
    def validate_type_matches_chain(cls, v, values):
        """Validate wallet type matches chain."""
        chain = values.get('chain', 'aptos')
        
        # Petra is Aptos-only
        if v == 'petra' and chain != 'aptos':
            raise ValueError("Petra wallet type is only valid for Aptos chain")
        
        # Phantom/Solflare are Solana-only
        if v in ['phantom', 'solflare'] and chain != 'solana':
            raise ValueError(f"{v.title()} wallet type is only valid for Solana chain")
        
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "address": "0x06c5252a6b7e37cdf543cd3ac0d5699c52b6dd7bb3d82fea8acefa8f6f607094",
                    "chain": "aptos",
                    "type": "petra",
                    "label": "Main Aptos Wallet",
                    "is_primary": True
                },
                {
                    "address": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
                    "chain": "solana",
                    "type": "phantom",
                    "label": "Phantom Wallet",
                    "is_primary": False
                }
            ]
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
    chain: ChainType  # ← NEW: Chain identifier
    type: WalletType
    label: str
    is_primary: bool
    created_at: str
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "507f1f77bcf86cd799439011",
                    "user_id": "507f191e810c19729de860ea",
                    "address": "0x06c5252a6b7e37cdf543cd3ac0d5699c52b6dd7bb3d82fea8acefa8f6f607094",
                    "chain": "aptos",
                    "type": "petra",
                    "label": "Main Wallet",
                    "is_primary": True,
                    "created_at": "2025-01-15T10:30:00.000Z"
                },
                {
                    "id": "507f1f77bcf86cd799439012",
                    "user_id": "507f191e810c19729de860ea",
                    "address": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
                    "chain": "solana",
                    "type": "phantom",
                    "label": "Phantom Wallet",
                    "is_primary": False,
                    "created_at": "2025-01-15T11:00:00.000Z"
                }
            ]
        }

class WalletListResponse(BaseModel):
    """List of wallets with metadata."""
    wallets: list[WalletResponse]
    total: int
    primary: Optional[WalletResponse] = None
    by_chain: Optional[dict[str, int]] = None  # ← NEW: Count by chain
    
    class Config:
        json_schema_extra = {
            "example": {
                "wallets": [],
                "total": 5,
                "primary": None,
                "by_chain": {
                    "aptos": 3,
                    "solana": 2
                }
            }
        }