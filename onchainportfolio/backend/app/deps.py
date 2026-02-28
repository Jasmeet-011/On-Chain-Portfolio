# app/deps.py - COMPLETE VERSION with Alert System
"""
FastAPI Dependencies
Authentication, services, and dependency injection.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime

from app.services.auth_service import verify_token, get_user_by_id
from app.services.price_service import PriceService
from app.config import settings

# Import adapters instead of old aptos_client
from app.services.adapters import get_adapter_for_chain, AptosAdapter, SolanaAdapter


# ============================================================
# SERVICE INSTANCES (Singleton-like)
# ============================================================

# Create default Aptos adapter (for backward compatibility)
aptos_client = get_adapter_for_chain("aptos", rpc_url=settings.aptos_node_url)

# Price service (now supports both chains + CoinGecko API key for higher rate limits)
price_service = PriceService(
    ttl_seconds=settings.prices_ttl_seconds,
    coingecko_api_key=settings.coingecko_api_key,
)

# AI service (uncomment if using)
# from app.services.ai_service import AIService
# ai_service = AIService(api_key=settings.gemini_api_key)


# ============================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================

# HTTP Bearer token extractor
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency that extracts and validates JWT token from Authorization header.
    Returns the full user document if valid.
    Raises 401 if token is invalid or user not found.
    
    Usage in routes:
        @router.get("/protected")
        def protected_route(current_user: dict = Depends(get_current_user)):
            return {"user_id": str(current_user["_id"])}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    # Verify token and extract user_id
    user_id = verify_token(token)
    if user_id is None:
        raise credentials_exception
    
    # Fetch user from database
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Optional authentication dependency.
    Returns user if valid token provided, None otherwise.
    Does not raise exceptions for missing/invalid tokens.
    
    Usage in routes:
        @router.get("/public-or-private")
        def flexible_route(current_user: Optional[dict] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": "Hello, authenticated user!"}
            return {"message": "Hello, guest!"}
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    user_id = verify_token(token)
    
    if user_id is None:
        return None
    
    return get_user_by_id(user_id)


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """
    Convenience dependency that returns just the user_id string.
    
    Usage in routes:
        @router.get("/my-data")
        def get_my_data(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    return str(current_user["_id"])


# ============================================================
# ALERT SYSTEM DEPENDENCIES
# ============================================================

def get_alert_service():
    """
    Get alert service instance with all required dependencies.
    
    Usage in routes:
        @router.get("/alerts")
        def get_alerts(alert_service = Depends(get_alert_service)):
            return alert_service.get_user_alerts(user_id)
    """
    from app.services.db import (
        alerts_collection,
        email_preferences_collection,
        wallets_collection
    )
    from app.services.alert_service import AlertService
    from app.services.email_service import EmailService
    
    # Create email service instance
    email_service = EmailService()
    
    # Create and return alert service with all dependencies
    return AlertService(
        alerts_collection=alerts_collection,
        preferences_collection=email_preferences_collection,
        wallets_collection=wallets_collection,
        price_service=price_service,
        email_service=email_service
    )


def get_email_preferences_service():
    """
    Get email preferences service instance.
    
    Usage in routes:
        @router.get("/preferences/email")
        def get_prefs(prefs_service = Depends(get_email_preferences_service)):
            return prefs_service.get_preferences(user_id)
    """
    from app.services.db import email_preferences_collection
    from app.services.email_service import EmailPreferencesService
    
    return EmailPreferencesService(email_preferences_collection)


# ============================================================
# PORTFOLIO SERVICE DEPENDENCIES
# ============================================================

def get_snapshot_service():
    """
    Get snapshot service for portfolio history.
    
    Usage in routes:
        @router.get("/portfolio/history")
        def get_history(snapshot_service = Depends(get_snapshot_service)):
            return snapshot_service.get_snapshots(user_id)
    """
    from app.services.db import snapshots_collection, wallets_collection
    
    class SnapshotService:
        """Service for managing portfolio snapshots"""
        
        def __init__(self, snapshots_col, wallets_col):
            self.snapshots = snapshots_col
            self.wallets = wallets_col
        
        def get_snapshots(self, user_id: str, days: int = 30) -> list:
            """Get portfolio snapshots for the last N days"""
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            snapshots = list(self.snapshots.find({
                "user_id": user_id,
                "snapshot_date": {"$gte": cutoff_date}
            }).sort("snapshot_date", -1))
            
            # Convert ObjectId to string
            for s in snapshots:
                s["id"] = str(s.pop("_id"))
            
            return snapshots
        
        def create_snapshot(self, user_id: str, wallet_id: str, data: dict) -> dict:
            """Create a new portfolio snapshot"""
            snapshot_doc = {
                "user_id": user_id,
                "wallet_id": wallet_id,
                "snapshot_date": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                "total_value": data.get("total_value", 0),
                "balances": data.get("balances", []),
                "created_at": datetime.utcnow()
            }
            
            # Upsert (one snapshot per user/wallet/date)
            result = self.snapshots.update_one(
                {
                    "user_id": user_id,
                    "wallet_id": wallet_id,
                    "snapshot_date": snapshot_doc["snapshot_date"]
                },
                {"$set": snapshot_doc},
                upsert=True
            )
            
            return snapshot_doc
    
    return SnapshotService(snapshots_collection, wallets_collection)


# ============================================================
# ADAPTER DEPENDENCIES
# ============================================================

def get_aptos_adapter():
    """Get Aptos blockchain adapter"""
    return get_adapter_for_chain("aptos", rpc_url=settings.aptos_node_url)


def get_solana_adapter():
    """Get Solana blockchain adapter"""
    solana_rpc = getattr(settings, 'solana_rpc_url', 'https://api.mainnet-beta.solana.com')
    return get_adapter_for_chain("solana", rpc_url=solana_rpc)


def get_adapter_for_wallet(chain: str):
    """
    Get appropriate adapter based on wallet chain.
    
    Usage in routes:
        adapter = get_adapter_for_wallet(wallet.chain)
        balance = adapter.get_balance(wallet.address)
    """
    if chain.lower() == "aptos":
        return get_aptos_adapter()
    elif chain.lower() == "solana":
        return get_solana_adapter()
    else:
        raise ValueError(f"Unsupported chain: {chain}")


# ============================================================
# PRICE SERVICE DEPENDENCY
# ============================================================

def get_price_service() -> PriceService:
    """
    Get price service instance.
    
    Usage in routes:
        @router.get("/price/{symbol}")
        def get_price(symbol: str, price_svc = Depends(get_price_service)):
            return price_svc.get_price(symbol)
    """
    return price_service