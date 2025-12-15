# app/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.services.auth_service import verify_token, get_user_by_id
from app.services.aptos_client import AptosClient
from app.services.price_service import PriceService
from app.services.ai_service import AIService
from app.config import settings

# ============================================================
# Service Instances (Singleton-like)
# ============================================================

aptos_client = AptosClient(base_url=settings.aptos_node_url)
price_service = PriceService(ttl_seconds=settings.prices_ttl_seconds)
ai_service = AIService(api_key=settings.gemini_api_key)

# ============================================================
# Authentication Dependencies
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