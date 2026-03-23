# backend/app/routers/nfts.py
"""
NFT Router

Endpoints for fetching NFTs from user wallets.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.nft_models import NFTResponse, AggregatedNFTResponse
from app.services.nft_service import get_nft_service
from app.services.db import wallets_collection
from app.deps import get_current_user

logger = logging.getLogger("chainlens.routers.nfts")
router = APIRouter()


# ============================================================
# NFT Endpoints
# ============================================================

@router.get("/wallet/{wallet_address}", response_model=NFTResponse)
async def get_wallet_nfts(
    wallet_address: str,
    chain: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get NFTs for a specific wallet.
    
    Args:
        wallet_address: Wallet address
        chain: "aptos" or "solana"
    
    Returns:
        NFTResponse with NFTs and collection summary
    """
    user_id = str(current_user["_id"])
    
    # Verify wallet belongs to user
    wallet = wallets_collection.find_one({
        "user_id": user_id,
        "address": wallet_address,
        "is_active": True
    })
    
    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found or doesn't belong to user"
        )
    
    logger.info("Fetching NFTs for wallet %s... (%s)", wallet_address[:8], chain)

    try:
        nft_service = get_nft_service()
        nft_response = nft_service.get_nfts_for_wallet(wallet_address, chain)
        return nft_response

    except (ValueError, RuntimeError, ConnectionError) as e:
        logger.error("Error fetching NFTs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=AggregatedNFTResponse)
async def get_all_nfts(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all NFTs across all user wallets.
    
    Returns:
        AggregatedNFTResponse with all NFTs grouped by collection
    """
    user_id = str(current_user["_id"])
    
    # Get all user wallets
    wallets = list(wallets_collection.find({"user_id": user_id, "is_active": True}))

    if not wallets:
        # Return empty response instead of error
        return AggregatedNFTResponse(
            total_nfts=0,
            total_collections=0,
            by_chain={},
            collections=[],
            all_nfts=[]
        )
    
    logger.info("Fetching NFTs for %d wallets", len(wallets))

    nft_service = get_nft_service()

    # Fetch NFTs for each wallet
    wallet_nfts: List[NFTResponse] = []

    for wallet in wallets:
        address = wallet.get("address")
        chain = wallet.get("chain", "aptos")

        try:
            nft_response = nft_service.get_nfts_for_wallet(address, chain)
            wallet_nfts.append(nft_response)

        except (ValueError, RuntimeError, ConnectionError) as e:
            logger.warning("Failed to fetch NFTs for %s: %s", address[:8], e)
            continue

    # Aggregate all NFTs
    aggregated = nft_service.aggregate_nfts(wallet_nfts)

    logger.info("Total NFTs: %d", aggregated['total_nfts'])
    logger.info("Total collections: %d", aggregated['total_collections'])
    
    return AggregatedNFTResponse(**aggregated)


@router.get("/collections", response_model=dict)
async def get_collections_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get collection summary (count per collection).
    
    Returns:
        Collection summary data
    """
    user_id = str(current_user["_id"])
    
    # Get all user wallets
    wallets = list(wallets_collection.find({"user_id": user_id, "is_active": True}))

    if not wallets:
        return {
            "total_collections": 0,
            "collections": []
        }
    
    nft_service = get_nft_service()
    
    # Fetch NFTs for each wallet
    wallet_nfts: List[NFTResponse] = []
    
    for wallet in wallets:
        address = wallet.get("address")
        chain = wallet.get("chain", "aptos")
        
        try:
            nft_response = nft_service.get_nfts_for_wallet(address, chain)
            wallet_nfts.append(nft_response)
        except (ValueError, RuntimeError, ConnectionError) as e:
            logger.warning("Failed to fetch NFTs for collection summary: %s", e)
            continue
    
    # Aggregate
    aggregated = nft_service.aggregate_nfts(wallet_nfts)
    
    return {
        "total_collections": aggregated["total_collections"],
        "total_nfts": aggregated["total_nfts"],
        "by_chain": aggregated["by_chain"],
        "collections": [
            {
                "name": c.collection_name,
                "count": c.count,
                "chain": c.chain,
                "sample_image": c.sample_nfts[0].image_url if c.sample_nfts else None
            }
            for c in aggregated["collections"]
        ]
    }


@router.get("/debug/status")
async def get_nft_service_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Debug endpoint to check NFT service configuration.
    """
    import os
    
    helius_key = os.getenv("HELIUS_API_KEY", "")
    simplehash_key = os.getenv("SIMPLEHASH_API_KEY", "")
    
    return {
        "helius_configured": bool(helius_key),
        "helius_key_prefix": helius_key[:8] + "..." if helius_key else None,
        "simplehash_configured": bool(simplehash_key),
        "simplehash_key_prefix": simplehash_key[:8] + "..." if simplehash_key else None,
        "aptos_indexer_url": os.getenv("APTOS_INDEXER_URL", "https://indexer.mainnet.aptoslabs.com/v1/graphql"),
        "note": "If no API keys configured, Solana NFTs will return empty. Aptos NFTs use public indexer."
    }


@router.get("/debug/test-solana/{wallet_address}")
async def test_solana_nfts(
    wallet_address: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Debug endpoint to test Solana NFT fetching directly.
    Shows raw API response for debugging.
    """
    import os
    import httpx
    
    helius_key = os.getenv("HELIUS_API_KEY", "")
    
    if not helius_key:
        return {
            "error": "No Helius API key configured",
            "solution": "Add HELIUS_API_KEY to your .env file"
        }
    
    helius_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key}"
    
    # Test with getAssetsByOwner
    payload = {
        "jsonrpc": "2.0",
        "id": "test",
        "method": "getAssetsByOwner",
        "params": {
            "ownerAddress": wallet_address,
            "page": 1,
            "limit": 10,
            "displayOptions": {
                "showFungible": False,
                "showNativeBalance": False,
                "showCollectionMetadata": True
            }
        }
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(helius_url, json=payload)
            
            if response.status_code != 200:
                return {
                    "status": response.status_code,
                    "error": response.text[:500]
                }
            
            data = response.json()
            
            if "error" in data:
                return {
                    "error": data["error"],
                    "suggestion": "Check if wallet address is valid Solana address"
                }
            
            result = data.get("result", {})
            items = result.get("items", [])
            
            # Return summary + first few items for debugging
            return {
                "wallet": wallet_address,
                "total": result.get("total", 0),
                "items_returned": len(items),
                "sample_items": [
                    {
                        "id": item.get("id", "")[:30] + "...",
                        "interface": item.get("interface"),
                        "name": item.get("content", {}).get("metadata", {}).get("name", "Unknown"),
                        "collection": next(
                            (g.get("group_value") for g in item.get("grouping", []) if g.get("group_key") == "collection"),
                            "No collection"
                        )
                    }
                    for item in items[:5]
                ]
            }
    
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }


@router.get("/debug/test-helius-alt/{wallet_address}")
async def test_helius_alternative(
    wallet_address: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Test alternative Helius endpoint (old API format).
    """
    import os
    import httpx
    
    helius_key = os.getenv("HELIUS_API_KEY", "")
    
    if not helius_key:
        return {"error": "No Helius API key"}
    
    # Try the old endpoint format
    url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/nfts"
    params = {"api-key": helius_key}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            
            if response.status_code != 200:
                return {
                    "endpoint": "v0/addresses/nfts",
                    "status": response.status_code,
                    "error": response.text[:300]
                }
            
            data = response.json()
            
            return {
                "endpoint": "v0/addresses/nfts",
                "total_nfts": len(data) if isinstance(data, list) else 0,
                "sample": data[:3] if isinstance(data, list) else data
            }
    
    except Exception as e:
        return {"error": str(e)}