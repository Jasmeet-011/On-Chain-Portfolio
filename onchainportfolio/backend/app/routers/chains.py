# backend/app/routers/chains.py
"""
Chains Router - Supported Blockchain Networks

Provides endpoints for:
- Listing supported chains
- Getting chain info
- Chain status checks
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.schemas.wallet import ChainInfoResponse, SupportedChainsResponse
from app.services.adapters import (
    list_supported_chains,
    get_chain_info,
    get_adapter_for_chain,
    SUPPORTED_CHAINS
)

router = APIRouter(prefix="/chains", tags=["chains"])


# ============================================================
# Chain Listing Endpoints
# ============================================================

@router.get("", response_model=SupportedChainsResponse)
def get_supported_chains(
    include_testnets: bool = Query(True, description="Include testnet chains"),
    available_only: bool = Query(True, description="Only show available chains")
):
    """
    Get list of all supported blockchain networks.
    
    Returns chains grouped by type (EVM, Move, SVM) with availability status.
    """
    chains = list_supported_chains(include_testnets=include_testnets)
    
    if available_only:
        chains = [c for c in chains if c.get("available", False)]
    
    # Convert to response model
    chain_responses = [
        ChainInfoResponse(
            id=c["id"],
            name=c["name"],
            type=c["type"],
            native_token=c["native_token"],
            chain_id=c.get("chain_id"),
            is_testnet=c.get("is_testnet", False),
            available=c.get("available", False)
        )
        for c in chains
    ]
    
    # Count by type
    evm_count = sum(1 for c in chain_responses if c.type == "evm")
    non_evm_count = len(chain_responses) - evm_count
    
    return SupportedChainsResponse(
        chains=chain_responses,
        total=len(chain_responses),
        evm_chains=evm_count,
        non_evm_chains=non_evm_count
    )


@router.get("/{chain_id}", response_model=ChainInfoResponse)
def get_chain_details(chain_id: str):
    """
    Get detailed information about a specific chain.
    
    Args:
        chain_id: Chain identifier (e.g., "ethereum_sepolia", "polygon")
    """
    info = get_chain_info(chain_id)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Chain '{chain_id}' not found. Use /chains to see supported chains."
        )
    
    return ChainInfoResponse(
        id=chain_id,
        name=info["name"],
        type=info["type"],
        native_token=info["native_token"],
        chain_id=info.get("chain_id"),
        is_testnet=info.get("is_testnet", False),
        available=info.get("available", False)
    )


@router.get("/{chain_id}/status")
def get_chain_status(chain_id: str):
    """
    Check the status of a specific chain (RPC connectivity, block height).
    
    Args:
        chain_id: Chain identifier
    """
    info = get_chain_info(chain_id)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Chain '{chain_id}' not found"
        )
    
    if not info.get("available"):
        return {
            "chain": chain_id,
            "status": "unavailable",
            "message": "Required dependencies not installed"
        }
    
    try:
        adapter = get_adapter_for_chain(chain_id)
        chain_info = adapter.get_chain_info()
        
        return {
            "chain": chain_id,
            "status": "connected" if chain_info.get("connected") else "disconnected",
            "block_number": chain_info.get("block_number"),
            "chain_id": chain_info.get("chain_id"),
            "native_token": info["native_token"],
            "rpc_url": chain_info.get("rpc_url"),
            "gas_price_gwei": chain_info.get("gas_price_gwei")
        }
        
    except Exception as e:
        return {
            "chain": chain_id,
            "status": "error",
            "error": str(e)
        }


# ============================================================
# Token Registry Endpoints
# ============================================================

@router.get("/{chain_id}/tokens")
def get_chain_tokens(chain_id: str):
    """
    Get list of supported tokens for a specific chain.
    
    Returns token symbols, addresses, and decimals.
    """
    info = get_chain_info(chain_id)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Chain '{chain_id}' not found"
        )
    
    if not info.get("available"):
        raise HTTPException(
            status_code=503,
            detail=f"Chain '{chain_id}' is not available"
        )
    
    try:
        adapter = get_adapter_for_chain(chain_id)
        
        # Get token registry from adapter
        tokens = []
        if hasattr(adapter, 'TOKEN_REGISTRY'):
            for symbol, token_info in adapter.TOKEN_REGISTRY.items():
                tokens.append({
                    "symbol": symbol,
                    "address": token_info.get("address"),
                    "decimals": token_info.get("decimals", 18),
                    "coingecko_id": token_info.get("coingecko_id")
                })
        
        # Add native token
        tokens.insert(0, {
            "symbol": adapter.NATIVE_TOKEN,
            "address": "native",
            "decimals": adapter.NATIVE_DECIMALS,
            "is_native": True
        })
        
        return {
            "chain": chain_id,
            "native_token": adapter.NATIVE_TOKEN,
            "tokens": tokens,
            "total": len(tokens)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tokens: {str(e)}"
        )


# ============================================================
# Utility Endpoints
# ============================================================

@router.get("/evm/all")
def get_all_evm_chains():
    """Get all EVM-compatible chains."""
    chains = list_supported_chains(include_testnets=True)
    evm_chains = [c for c in chains if c["type"] == "evm"]
    
    return {
        "chains": evm_chains,
        "total": len(evm_chains)
    }


@router.get("/testnets/all")
def get_all_testnets():
    """Get all testnet chains (recommended for development)."""
    chains = list_supported_chains(include_testnets=True)
    testnets = [c for c in chains if c.get("is_testnet")]
    
    return {
        "chains": testnets,
        "total": len(testnets),
        "note": "Testnets are recommended for development and testing"
    }


@router.post("/{chain_id}/validate-address")
def validate_address(
    chain_id: str,
    address: str = Query(..., description="Wallet address to validate")
):
    """
    Validate a wallet address for a specific chain.
    
    Returns validation result without checking on-chain existence.
    """
    info = get_chain_info(chain_id)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Chain '{chain_id}' not found"
        )
    
    if not info.get("available"):
        raise HTTPException(
            status_code=503,
            detail=f"Chain '{chain_id}' is not available"
        )
    
    try:
        adapter = get_adapter_for_chain(chain_id)
        is_valid, error = adapter.validate_address(address)
        
        result = {
            "chain": chain_id,
            "address": address,
            "valid": is_valid
        }
        
        if is_valid:
            result["normalized"] = adapter.normalize_address(address)
        else:
            result["error"] = error
        
        return result
        
    except Exception as e:
        return {
            "chain": chain_id,
            "address": address,
            "valid": False,
            "error": str(e)
        }