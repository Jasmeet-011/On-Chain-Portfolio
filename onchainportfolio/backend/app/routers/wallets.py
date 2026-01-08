# app/routers/wallets.py
from fastapi import APIRouter, HTTPException, status, Depends, Path
from typing import List

from app.schemas.wallet import (
    WalletCreateRequest,
    WalletUpdateLabelRequest,
    WalletSetPrimaryRequest,
    WalletResponse,
    WalletListResponse
)
from app.services.wallet_service import (
    create_wallet,
    list_user_wallets,
    get_wallet_by_address,
    get_primary_wallet,
    update_wallet_label,
    set_primary_wallet,
    delete_wallet,
    delete_all_user_wallets,
    validate_wallet_address,  # ← UPDATED: Was validate_aptos_address
    get_wallet_stats_by_chain,  # ← NEW: Multi-chain stats
)
from app.deps import get_current_user, get_current_user_id
from app.config import settings

router = APIRouter(prefix="/wallets", tags=["wallets"])

# ============================================================
# Helper Functions
# ============================================================

def wallet_to_response(wallet: dict) -> WalletResponse:
    """Convert wallet document to response model."""
    return WalletResponse(
        id=wallet["id"],
        user_id=wallet["user_id"],
        address=wallet["address"],
        chain=wallet.get("chain", "aptos"),  # ← NEW: Include chain
        type=wallet["type"],
        label=wallet["label"],
        is_primary=wallet["is_primary"],
        created_at=wallet["created_at"]
    )

# ============================================================
# Wallet CRUD Endpoints
# ============================================================

@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def add_wallet(
    payload: WalletCreateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Add a new wallet to the authenticated user's account.
    
    - **address**: Wallet address
    - **chain**: Blockchain (aptos or solana)  ← NEW
    - **type**: "petra", "phantom", or "manual"
    - **label**: Custom name for the wallet
    - **is_primary**: Whether this should be the primary wallet
    """
    wallet = create_wallet(
        user_id=user_id,
        address=payload.address,
        chain=payload.chain,  # ← NEW: Multi-chain support
        wallet_type=payload.type,
        label=payload.label,
        is_primary=payload.is_primary
    )
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add wallet. Wallet may already exist or address is invalid."
        )
    
    return wallet_to_response(wallet)


@router.get("", response_model=WalletListResponse)
def get_wallets(user_id: str = Depends(get_current_user_id)):
    """
    Get all wallets for the authenticated user.
    Returns list with primary wallet highlighted and stats by chain.
    """
    wallets = list_user_wallets(user_id)
    
    wallet_responses = [wallet_to_response(w) for w in wallets]
    primary = next((w for w in wallet_responses if w.is_primary), None)
    
    # Get stats by chain
    by_chain = get_wallet_stats_by_chain(user_id)  # ← NEW
    
    return WalletListResponse(
        wallets=wallet_responses,
        total=len(wallet_responses),
        primary=primary,
        by_chain=by_chain  # ← NEW: {"aptos": 3, "solana": 2}
    )


@router.get("/primary", response_model=WalletResponse)
def get_primary_wallet_endpoint(user_id: str = Depends(get_current_user_id)):
    """Get the primary wallet for the authenticated user."""
    wallet = get_primary_wallet(user_id)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No primary wallet found. Please add a wallet first."
        )
    
    return wallet_to_response(wallet)


@router.get("/{address}", response_model=WalletResponse)
def get_wallet(
    address: str = Path(..., description="Wallet address"),
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific wallet by address."""
    wallet = get_wallet_by_address(user_id, address)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return wallet_to_response(wallet)


@router.patch("/{address}/label", response_model=WalletResponse)
def update_label(
    address: str,
    payload: WalletUpdateLabelRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Update the label/name of a specific wallet."""
    success = update_wallet_label(user_id, address, payload.label)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update wallet label. Wallet may not exist."
        )
    
    # Return updated wallet
    wallet = get_wallet_by_address(user_id, address)
    return wallet_to_response(wallet)


@router.post("/primary", response_model=WalletResponse)
def set_primary(
    payload: WalletSetPrimaryRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Set a specific wallet as the primary wallet.
    All other wallets will have is_primary=False.
    """
    success = set_primary_wallet(user_id, payload.address)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set primary wallet. Wallet may not exist."
        )
    
    # Return updated wallet
    wallet = get_wallet_by_address(user_id, payload.address)
    return wallet_to_response(wallet)


@router.delete("/{address}", status_code=status.HTTP_204_NO_CONTENT)
def remove_wallet(
    address: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Remove a specific wallet from the user's account.
    If removing the primary wallet, another wallet will automatically become primary.
    """
    success = delete_wallet(user_id, address)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove wallet. Wallet may not exist."
        )
    
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def remove_all_wallets(user_id: str = Depends(get_current_user_id)):
    """
    Remove ALL wallets from the user's account.
    Use with caution!
    """
    success = delete_all_user_wallets(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove wallets"
        )
    
    return None