# backend/app/routers/wallets.py
"""
Wallets Router - Multi-Chain Wallet Management

Supports: Aptos, Solana, Ethereum, Polygon, Base (and testnets)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Path, Query
from typing import Optional

from app.schemas.wallet import (
    WalletCreateRequest,
    WalletUpdateLabelRequest,
    WalletSetPrimaryRequest,
    WalletResponse,
    WalletListResponse,
    ChainType,
    AddressType,
    detect_address_type,
    get_chains_for_address,
    EVM_TESTNET_CHAINS,
    EVM_MAINNET_CHAINS,
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
    get_wallet_stats_by_chain,
    get_wallets_by_chain,
)
from app.services.adapters import get_adapter_for_chain, list_supported_chains
from app.deps import get_current_user, get_current_user_id

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
        chain=wallet.get("chain", "aptos"),  # Default for old wallets
        type=wallet.get("type", "manual"),
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

    **Chain Auto-Detection:**
    - If chain is not specified or set to "evm", the address type is auto-detected
    - EVM addresses (0x + 40 hex chars) are stored as "evm" and query all EVM chains
    - Aptos addresses (0x + 64 hex chars) are stored as "aptos"
    - Solana addresses (Base58) are stored as "solana"

    **Supported Chains:**
    - **Multi-chain:** evm (queries all EVM chains)
    - **EVM Testnets:** ethereum_sepolia, polygon_amoy, base_sepolia
    - **EVM Mainnets:** ethereum, polygon, base
    - **Non-EVM:** aptos, solana

    **Example Request:**
    ```json
    {
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21",
        "type": "metamask",
        "label": "My EVM Wallet",
        "is_primary": true
    }
    ```
    """
    # Auto-detect chain if not specified or set to EVM
    chain_value = payload.chain.value if payload.chain else None

    if not chain_value or chain_value == "evm":
        try:
            addr_type = detect_address_type(payload.address)
            if addr_type == AddressType.EVM:
                chain_value = "evm"  # Multi-chain EVM
            elif addr_type == AddressType.SOLANA:
                chain_value = "solana"
            elif addr_type == AddressType.APTOS:
                chain_value = "aptos"
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid address format: {str(e)}"
            )

    wallet = create_wallet(
        user_id=user_id,
        address=payload.address,
        chain=chain_value,
        wallet_type=payload.type.value,
        label=payload.label,
        is_primary=payload.is_primary
    )

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add wallet. Address may be invalid or wallet already exists."
        )

    return wallet_to_response(wallet)


@router.get("", response_model=WalletListResponse)
def get_wallets(
    chain: Optional[str] = Query(None, description="Filter by chain (e.g., ethereum_sepolia)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all wallets for the authenticated user.
    
    Optionally filter by chain. Returns list with primary wallet highlighted.
    """
    wallets = list_user_wallets(user_id, chain=chain)
    
    wallet_responses = [wallet_to_response(w) for w in wallets]
    primary = next((w for w in wallet_responses if w.is_primary), None)
    
    # Get stats by chain
    by_chain = get_wallet_stats_by_chain(user_id)
    
    return WalletListResponse(
        wallets=wallet_responses,
        total=len(wallet_responses),
        primary=primary,
        by_chain=by_chain
    )


@router.get("/by-chain")
def get_wallets_grouped_by_chain(user_id: str = Depends(get_current_user_id)):
    """
    Get all wallets grouped by blockchain network.
    
    Useful for displaying wallets organized by chain in the UI.
    """
    wallets_by_chain = get_wallets_by_chain(user_id)
    
    result = {}
    for chain, wallets in wallets_by_chain.items():
        result[chain] = {
            "wallets": [wallet_to_response(w) for w in wallets],
            "count": len(wallets)
        }
    
    return {
        "by_chain": result,
        "total_chains": len(result),
        "total_wallets": sum(len(w) for w in wallets_by_chain.values())
    }


@router.get("/primary", response_model=WalletResponse)
def get_primary_wallet_endpoint(user_id: str = Depends(get_current_user_id)):
    """Get the primary wallet for the authenticated user (any chain)."""
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
    chain: Optional[str] = Query(None, description="Chain (optional, for disambiguation)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a specific wallet by address.
    
    If the same address exists on multiple chains, use the chain parameter
    to specify which one to retrieve.
    """
    wallet = get_wallet_by_address(user_id, address, chain=chain)
    
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
    chain: Optional[str] = Query(None, description="Chain (optional)"),
    user_id: str = Depends(get_current_user_id)
):
    """Update the label/name of a specific wallet."""
    success = update_wallet_label(user_id, address, payload.label, chain=chain)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update wallet label. Wallet may not exist."
        )
    
    # Return updated wallet
    wallet = get_wallet_by_address(user_id, address, chain=chain)
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
    success = set_primary_wallet(
        user_id, 
        payload.address, 
        chain=payload.chain.value if payload.chain else None
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set primary wallet. Wallet may not exist."
        )
    
    # Return updated wallet
    wallet = get_wallet_by_address(
        user_id, 
        payload.address,
        chain=payload.chain.value if payload.chain else None
    )
    return wallet_to_response(wallet)


@router.delete("/{address}", status_code=status.HTTP_204_NO_CONTENT)
def remove_wallet(
    address: str,
    chain: Optional[str] = Query(None, description="Chain (optional)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Remove a specific wallet from the user's account.
    
    If removing the primary wallet, another wallet will automatically become primary.
    """
    success = delete_wallet(user_id, address, chain=chain)
    
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
    
    ⚠️ Use with caution! This action cannot be undone.
    """
    success = delete_all_user_wallets(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove wallets"
        )
    
    return None


# ============================================================
# Portfolio Endpoints (per wallet)
# ============================================================

@router.get("/{address}/portfolio")
def get_wallet_portfolio(
    address: str = Path(..., description="Wallet address"),
    chain: Optional[str] = Query(None, description="Chain (required if ambiguous)"),
    testnet: bool = Query(True, description="Use testnet chains for EVM (default: True)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get complete portfolio for a specific wallet.

    Returns token balances with USD values.

    For EVM wallets (chain="evm"), this aggregates balances from all EVM chains.
    """
    # Find the wallet
    wallet = get_wallet_by_address(user_id, address, chain=chain)

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    wallet_chain = wallet.get("chain", "aptos")

    # If wallet is multi-chain EVM, use the multi-chain endpoint logic
    if wallet_chain == "evm":
        try:
            chains = EVM_TESTNET_CHAINS if testnet else EVM_MAINNET_CHAINS

            from app.services.price_service import get_price_service
            price_service = get_price_service()

            all_balances = []
            total_usd = 0.0

            for evm_chain in chains:
                try:
                    adapter = get_adapter_for_chain(evm_chain)
                    chain_balances = adapter.get_token_balances(address)

                    if not chain_balances:
                        continue

                    symbols = [b["symbol"] for b in chain_balances if b.get("symbol")]
                    prices = price_service.get_prices(symbols, chain=evm_chain)

                    for balance in chain_balances:
                        symbol = balance.get("symbol", "UNKNOWN")
                        price = prices.get(symbol)

                        balance["chain"] = evm_chain
                        if price:
                            balance["usd_price"] = price
                            balance["usd_value"] = balance["amount"] * price
                            total_usd += balance["usd_value"]
                        else:
                            balance["usd_price"] = None
                            balance["usd_value"] = None

                        all_balances.append(balance)

                except Exception as e:
                    print(f"[WALLET] Error fetching from {evm_chain}: {e}")

            return {
                "wallet_address": address,
                "chain": "evm",
                "chains_queried": chains,
                "label": wallet.get("label", "Wallet"),
                "balances": all_balances,
                "total_usd_value": round(total_usd, 2),
                "token_count": len(all_balances)
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch EVM portfolio: {str(e)}"
            )

    # Single chain wallet
    try:
        adapter = get_adapter_for_chain(wallet_chain)
        balances = adapter.get_token_balances(address)

        total_usd = 0.0

        from app.services.price_service import get_price_service
        price_service = get_price_service()

        symbols = [b["symbol"] for b in balances]
        prices = price_service.get_prices(symbols, chain=wallet_chain)

        for balance in balances:
            symbol = balance["symbol"]
            price = prices.get(symbol)
            balance["chain"] = wallet_chain

            if price:
                balance["usd_price"] = price
                balance["usd_value"] = balance["amount"] * price
                total_usd += balance["usd_value"]
            else:
                balance["usd_price"] = None
                balance["usd_value"] = None

        return {
            "wallet_address": address,
            "chain": wallet_chain,
            "label": wallet.get("label", "Wallet"),
            "balances": balances,
            "total_usd_value": round(total_usd, 2),
            "token_count": len(balances)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch portfolio: {str(e)}"
        )


@router.get("/{address}/balances")
def get_wallet_balances(
    address: str = Path(..., description="Wallet address"),
    chain: Optional[str] = Query(None, description="Chain (required if ambiguous)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get token balances for a specific wallet (without USD values).

    Faster than /portfolio as it skips price fetching.
    """
    # Find the wallet
    wallet = get_wallet_by_address(user_id, address, chain=chain)

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    wallet_chain = wallet.get("chain", "aptos")

    try:
        adapter = get_adapter_for_chain(wallet_chain)
        balances = adapter.get_token_balances(address)

        return {
            "wallet_address": address,
            "chain": wallet_chain,
            "balances": balances,
            "token_count": len(balances)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch balances: {str(e)}"
        )


# ============================================================
# Multi-Chain Portfolio Endpoint
# ============================================================

@router.get("/{address}/multi-chain-portfolio")
def get_multi_chain_portfolio(
    address: str = Path(..., description="Wallet address"),
    testnet: bool = Query(True, description="Use testnet chains (default: True)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get aggregated portfolio across all applicable chains for a wallet address.

    For EVM addresses (0x...): Queries Ethereum, Polygon, and Base (or their testnets)
    For Solana addresses: Queries Solana only
    For Aptos addresses: Queries Aptos only

    This endpoint auto-detects the address type and fetches balances from all
    chains that support that address format.
    """
    try:
        # Detect address type
        addr_type = detect_address_type(address)

        # Get chains to query
        chains = get_chains_for_address(address, testnet=testnet)

        if not chains:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not determine chains for address: {address}"
            )

        # Import price service
        from app.services.price_service import get_price_service
        price_service = get_price_service()

        # Fetch balances from all chains
        balances_by_chain = {}
        all_balances = []
        chain_totals = {}
        total_usd = 0.0
        total_tokens = 0

        for chain in chains:
            try:
                adapter = get_adapter_for_chain(chain)
                chain_balances = adapter.get_token_balances(address)

                if not chain_balances:
                    balances_by_chain[chain] = []
                    chain_totals[chain] = 0.0
                    continue

                # Get prices for tokens on this chain
                symbols = [b["symbol"] for b in chain_balances if b.get("symbol")]
                prices = price_service.get_prices(symbols, chain=chain)

                chain_total = 0.0
                processed_balances = []

                for balance in chain_balances:
                    symbol = balance.get("symbol", "UNKNOWN")
                    price = prices.get(symbol)

                    bal_entry = {
                        "symbol": symbol,
                        "address": balance.get("address", ""),
                        "decimals": balance.get("decimals", 0),
                        "raw": balance.get("raw", "0"),
                        "amount": balance.get("amount", 0),
                        "usd_price": price,
                        "usd_value": None,
                        "chain": chain
                    }

                    if price and balance.get("amount", 0) > 0:
                        usd_value = balance["amount"] * price
                        bal_entry["usd_value"] = usd_value
                        chain_total += usd_value

                    processed_balances.append(bal_entry)
                    all_balances.append(bal_entry)

                balances_by_chain[chain] = processed_balances
                chain_totals[chain] = round(chain_total, 2)
                total_usd += chain_total
                total_tokens += len(chain_balances)

            except Exception as e:
                print(f"[WALLET] Error fetching balances from {chain}: {e}")
                balances_by_chain[chain] = []
                chain_totals[chain] = 0.0

        return {
            "wallet_address": address,
            "address_type": addr_type.value,
            "chains_queried": chains,
            "balances_by_chain": balances_by_chain,
            "all_balances": all_balances,
            "total_usd_value": round(total_usd, 2),
            "total_token_count": total_tokens,
            "chain_totals": chain_totals
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch multi-chain portfolio: {str(e)}"
        )