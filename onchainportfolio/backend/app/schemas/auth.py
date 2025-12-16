# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

# Import WalletResponse from wallet schema (single source of truth)
from app.schemas.wallet import WalletResponse

# ============================================================
# Auth Request/Response Models
# ============================================================

class SignUpRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)

class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

# JWT Token Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

# ============================================================
# User Response Models
# ============================================================

class UserResponse(BaseModel):
    """
    User response model.
    
    NOTE: wallets field now returns WalletResponse objects (with 'label' field)
    instead of old WalletInfo (with 'name' field).
    
    wallet_address is DEPRECATED but kept for backward compatibility.
    """
    id: str
    name: str
    email: str
    wallet_address: Optional[str] = None  # DEPRECATED: Use wallets list instead
    wallets: List[WalletResponse] = Field(default_factory=list)

# Auth response that includes both user info and token
class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

# ============================================================
# DEPRECATED: Legacy Wallet Request Models
# These are kept ONLY for backward compatibility with old API endpoints
# New code should use schemas from app.schemas.wallet instead
# ============================================================

class UpdateWalletRequest(BaseModel):
    """DEPRECATED: Use POST /v1/wallets instead"""
    wallet_address: str = Field(..., min_length=10, max_length=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "wallet_address": "0xe037e246dfd66661c6162e0dff968d64753eea38af08b1da2695e8464dbfce6a"
            }
        }

class AddWalletRequest(BaseModel):
    """DEPRECATED: Use POST /v1/wallets with WalletCreateRequest instead"""
    address: str = Field(..., min_length=10, max_length=200)
    name: str = Field(default="Wallet", min_length=1, max_length=50)
    is_primary: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "0x06c5252a6b7e37cdf543cd3ac0d5699c52b6dd7bb3d82fea8acefa8f6f607094",
                "name": "Main Wallet",
                "is_primary": True
            }
        }

class RemoveWalletRequest(BaseModel):
    """DEPRECATED: Use DELETE /v1/wallets/{address} instead"""
    address: str = Field(..., min_length=10, max_length=200)

class UpdateWalletNameRequest(BaseModel):
    """DEPRECATED: Use PATCH /v1/wallets/{address}/label instead"""
    address: str = Field(..., min_length=10, max_length=200)
    name: str = Field(..., min_length=1, max_length=50)

class SetPrimaryWalletRequest(BaseModel):
    """DEPRECATED: Use POST /v1/wallets/primary instead"""
    address: str = Field(..., min_length=10, max_length=200)