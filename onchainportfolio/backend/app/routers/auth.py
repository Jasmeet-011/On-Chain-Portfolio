# app/routers/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from app.schemas.auth import (
    SignUpRequest, 
    SignInRequest, 
    UserResponse,
    AuthResponse,
    UpdateWalletRequest,
    AddWalletRequest,
    UpdateWalletNameRequest,
    SetPrimaryWalletRequest,
)
from app.schemas.wallet import WalletResponse
from app.services.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_email,
    get_user_by_id,
    create_access_token,
    update_user_wallet,
    get_user_wallet,
    remove_user_wallet,
)
from app.services.wallet_service import (
    list_user_wallets,
    create_wallet,
    delete_wallet,
    update_wallet_label,
    set_primary_wallet,
)
from app.deps import get_current_user, get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])

# ============================================================
# Helper Function
# ============================================================

def user_to_response(user: dict, user_id: str) -> UserResponse:
    """
    Convert user document to UserResponse.
    
    Now fetches wallets from separate wallets collection
    and returns WalletResponse objects (with 'chain' field).
    """
    # Fetch wallets from wallets collection
    wallets = list_user_wallets(user_id)
    
    # Convert to WalletResponse format
    wallet_responses = [
        WalletResponse(
            id=w["id"],
            user_id=w["user_id"],
            address=w["address"],
            chain=w.get("chain", "aptos"),  # ← Include chain field
            type=w.get("type", "manual"),
            label=w.get("label", "Wallet"),
            is_primary=w.get("is_primary", False),
            created_at=w.get("created_at", "")
        )
        for w in wallets
    ]
    
    return UserResponse(
        id=user_id,
        name=user["name"],
        email=user["email"],
        wallet_address=user.get("wallet_address"),  # DEPRECATED but kept
        wallets=wallet_responses
    )

# ============================================================
# Authentication Endpoints
# ============================================================

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest):
    """
    Create a new user account.
    Returns user info and JWT access token.
    """
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    user = create_user(payload.name, payload.email, payload.password)
    user_id = str(user["_id"])
    access_token = create_access_token(user_id=user_id)

    return AuthResponse(
        user=user_to_response(user, user_id),
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: SignInRequest):
    """
    Authenticate user and return user info with JWT access token.
    """
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = str(user["_id"])
    access_token = create_access_token(user_id=user_id)

    return AuthResponse(
        user=user_to_response(user, user_id),
        access_token=access_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires: Bearer token in Authorization header.
    """
    user_id = str(current_user["_id"])
    return user_to_response(current_user, user_id)


# ============================================================
# LEGACY: Single Wallet Endpoints (backward compatibility)
# These endpoints default to Aptos for backward compatibility
# ============================================================

@router.put("/wallet", response_model=UserResponse)
def update_wallet_legacy(
    payload: UpdateWalletRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    LEGACY: Update user's wallet address.
    Use POST /v1/wallets instead for multi-wallet support.
    
    This endpoint now creates a wallet in the wallets collection.
    Defaults to Aptos chain for backward compatibility.
    """
    user_id = str(current_user["_id"])
    
    success = update_user_wallet(user_id, payload.wallet_address)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update wallet address"
        )
    
    updated_user = get_user_by_id(user_id)
    return user_to_response(updated_user, user_id)


@router.get("/wallet")
def get_wallet_legacy(current_user: dict = Depends(get_current_user)):
    """
    LEGACY: Get user's stored wallet address (returns primary).
    Use GET /v1/wallets for all wallets.
    """
    user_id = str(current_user["_id"])
    wallet = get_user_wallet(user_id)
    return {"wallet_address": wallet}


@router.delete("/wallet")
def disconnect_wallet_legacy(current_user: dict = Depends(get_current_user)):
    """
    LEGACY: Remove ALL wallets.
    Use DELETE /v1/wallets/{address} to remove specific wallet.
    """
    user_id = str(current_user["_id"])
    
    success = remove_user_wallet(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect wallet"
        )
    
    return {"message": "All wallets disconnected successfully"}


# ============================================================
# LEGACY: Multiple Wallets Endpoints (DEPRECATED)
# These endpoints still work but are DEPRECATED.
# Use /v1/wallets endpoints instead.
# Defaults to Aptos for backward compatibility.
# ============================================================

@router.get("/wallets", response_model=List[WalletResponse])
def get_wallets_legacy(current_user: dict = Depends(get_current_user)):
    """
    DEPRECATED: Use GET /v1/wallets instead.
    
    Get all wallets for the authenticated user.
    Returns list of wallet objects with address, chain, label, and is_primary flag.
    """
    user_id = str(current_user["_id"])
    wallets = list_user_wallets(user_id)
    
    return [
        WalletResponse(
            id=w["id"],
            user_id=w["user_id"],
            address=w["address"],
            chain=w.get("chain", "aptos"),  # ← Include chain
            type=w.get("type", "manual"),
            label=w.get("label", "Wallet"),
            is_primary=w.get("is_primary", False),
            created_at=w.get("created_at", "")
        )
        for w in wallets
    ]


@router.post("/wallets", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def add_wallet_legacy(
    payload: AddWalletRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    DEPRECATED: Use POST /v1/wallets instead.
    
    Add a new wallet to authenticated user's account.
    Defaults to Aptos chain for backward compatibility.
    """
    user_id = str(current_user["_id"])
    
    # Convert old "name" field to new "label" field
    # Default to Aptos for backward compatibility
    wallet = create_wallet(
        user_id=user_id,
        address=payload.address,
        chain="aptos",  # ← Default to Aptos for legacy endpoint
        wallet_type="manual",
        label=payload.name,  # ← Convert name to label
        is_primary=payload.is_primary
    )
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add wallet. Wallet may already exist."
        )
    
    updated_user = get_user_by_id(user_id)
    return user_to_response(updated_user, user_id)


@router.delete("/wallets/{address}")
def remove_wallet_legacy(
    address: str,
    current_user: dict = Depends(get_current_user)
):
    """
    DEPRECATED: Use DELETE /v1/wallets/{address} instead.
    
    Remove a specific wallet from authenticated user's account.
    """
    user_id = str(current_user["_id"])
    
    success = delete_wallet(user_id, address)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove wallet. Wallet may not exist."
        )
    
    return {"message": "Wallet removed successfully", "address": address}


@router.patch("/wallets/name", response_model=UserResponse)
def update_wallet_name_endpoint_legacy(
    payload: UpdateWalletNameRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    DEPRECATED: Use PATCH /v1/wallets/{address}/label instead.
    
    Update the name of a specific wallet.
    """
    user_id = str(current_user["_id"])
    
    # Convert old "name" to new "label"
    success = update_wallet_label(user_id, payload.address, payload.name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update wallet name. Wallet may not exist."
        )
    
    updated_user = get_user_by_id(user_id)
    return user_to_response(updated_user, user_id)


@router.patch("/wallets/primary", response_model=UserResponse)
def set_primary_wallet_endpoint_legacy(
    payload: SetPrimaryWalletRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    DEPRECATED: Use POST /v1/wallets/primary instead.
    
    Set a specific wallet as the primary wallet.
    """
    user_id = str(current_user["_id"])
    
    success = set_primary_wallet(user_id, payload.address)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set primary wallet. Wallet may not exist."
        )
    
    updated_user = get_user_by_id(user_id)
    return user_to_response(updated_user, user_id)