# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from app.schemas.wallet import WalletResponse

class SignUpRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)

class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserResponse(BaseModel):
    """
    User response model.

    wallet_address is DEPRECATED but kept for backward compatibility.
    """
    id: str
    name: str
    email: str
    wallet_address: Optional[str] = None
    wallets: List[WalletResponse] = Field(default_factory=list)

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

# ---- Deprecated request models (ok to keep) ----

class UpdateWalletRequest(BaseModel):
    wallet_address: str = Field(min_length=10, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "wallet_address": "0xe037e246dfd66661c6162e0dff968d64753eea38af08b1da2695e8464dbfce6a"
            }
        }

class AddWalletRequest(BaseModel):
    address: str = Field(min_length=10, max_length=200)
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
    address: str = Field(min_length=10, max_length=200)

class UpdateWalletNameRequest(BaseModel):
    address: str = Field(min_length=10, max_length=200)
    name: str = Field(min_length=1, max_length=50)

class SetPrimaryWalletRequest(BaseModel):
    address: str = Field(min_length=10, max_length=200)
