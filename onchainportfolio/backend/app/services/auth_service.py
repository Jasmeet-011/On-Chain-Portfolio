# app/services/auth_service.py
from typing import Optional
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

from .db import users_collection
from app.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ============================================================
# Password Utilities
# ============================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ============================================================
# JWT Token Functions
# ============================================================

def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for the user."""
    to_encode = {"sub": user_id}
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and return the user_id if valid.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None

# ============================================================
# User CRUD Functions
# ============================================================

def get_user_by_email(email: str) -> Optional[dict]:
    return users_collection.find_one({"email": email})

def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    try:
        return users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None

def generate_verification_token() -> str:
    """Generate a secure URL-safe random verification token."""
    return secrets.token_urlsafe(32)


def create_user(name: str, email: str, password: str) -> dict:
    """
    Create a user document in MongoDB.

    NOTE: No longer stores wallets as embedded array.
    Wallets are managed separately via wallet_service.
    """
    password_hash = hash_password(password)
    verification_token = generate_verification_token()
    user_doc = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "wallet_address": None,  # DEPRECATED: Kept for backward compatibility
        "is_email_verified": False,
        "email_verification_token": verification_token,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = users_collection.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc


def get_user_by_verification_token(token: str) -> Optional[dict]:
    """Find a user by their email verification token."""
    return users_collection.find_one({"email_verification_token": token})


def verify_user_email(user_id: str) -> bool:
    """Mark a user's email as verified and clear the verification token."""
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "is_email_verified": True,
                "email_verified_at": datetime.now(timezone.utc).isoformat(),
            },
            "$unset": {"email_verification_token": ""},
        }
    )
    return result.modified_count > 0


def refresh_verification_token(user_id: str) -> Optional[str]:
    """Generate a new verification token for a user (for resend)."""
    token = generate_verification_token()
    result = users_collection.update_one(
        {"_id": ObjectId(user_id), "is_email_verified": False},
        {"$set": {"email_verification_token": token}}
    )
    return token if result.modified_count > 0 else None

def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Return user if email/password are valid, else None."""
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user

# ============================================================
# LEGACY: Single Wallet Functions (DEPRECATED)
# These functions are kept ONLY for backward compatibility.
# They now delegate to wallet_service behind the scenes.
# ============================================================

def update_user_wallet(user_id: str, wallet_address: str) -> bool:
    """
    LEGACY: Update user's single wallet address.
    
    This now:
    1. Adds wallet to wallets collection (if not exists)
    2. Sets it as primary
    3. Updates legacy wallet_address field
    """
    try:
        # Import here to avoid circular dependency
        from .wallet_service import create_wallet, get_wallet_by_address, set_primary_wallet
        
        normalized = wallet_address.lower()
        if not normalized.startswith("0x"):
            normalized = "0x" + normalized
        
        # Check if wallet already exists
        existing = get_wallet_by_address(user_id, normalized)
        
        if not existing:
            # Create new wallet
            wallet = create_wallet(
                user_id=user_id,
                address=normalized,
                wallet_type="manual",
                label="Main Wallet",
                is_primary=True
            )
            return wallet is not None
        else:
            # Set existing wallet as primary
            return set_primary_wallet(user_id, normalized)
            
    except Exception as e:
        print(f"[ERROR] Failed to update wallet: {e}")
        return False

def get_user_wallet(user_id: str) -> Optional[str]:
    """
    LEGACY: Get user's primary wallet address.
    Now fetches from wallets collection.
    """
    try:
        from .wallet_service import get_primary_wallet
        
        primary = get_primary_wallet(user_id)
        if primary:
            return primary.get("address")
        
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get user wallet: {e}")
        return None

def remove_user_wallet(user_id: str) -> bool:
    """
    LEGACY: Remove ALL wallets.
    Now delegates to wallet_service.
    """
    try:
        from .wallet_service import delete_all_user_wallets
        return delete_all_user_wallets(user_id)
    except Exception as e:
        print(f"[ERROR] Failed to remove wallet: {e}")
        return False

# ============================================================
# REMOVED: Embedded Wallet Functions
# The following functions have been REMOVED because wallets are now
# managed in a separate collection via wallet_service:
# 
# - add_user_wallet() → Use wallet_service.create_wallet()
# - get_user_wallets() → Use wallet_service.list_user_wallets()
# - remove_user_wallet_by_address() → Use wallet_service.delete_wallet()
# - update_wallet_name() → Use wallet_service.update_wallet_label()
# - set_primary_wallet() → Use wallet_service.set_primary_wallet()
# 
# All wallet operations should now go through wallet_service.
# ============================================================