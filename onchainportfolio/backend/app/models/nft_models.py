# backend/app/models/nft_models.py
"""
NFT Data Models

Simple models for NFT display - collection name, image, count only.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


# ============================================================
# NFT DATA MODELS
# ============================================================

class NFT(BaseModel):
    """Individual NFT."""
    name: str
    collection: str
    image_url: Optional[str] = None
    token_id: Optional[str] = None
    chain: str  # "aptos" or "solana"
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Bored Ape #1234",
                "collection": "Bored Ape Yacht Club",
                "image_url": "https://example.com/nft.png",
                "token_id": "1234",
                "chain": "solana"
            }
        }


class CollectionSummary(BaseModel):
    """NFT collection summary."""
    collection_name: str
    count: int
    chain: str
    sample_nfts: List[NFT] = Field(default_factory=list)  # First 3-5 NFTs
    
    class Config:
        json_schema_extra = {
            "example": {
                "collection_name": "Bored Ape Yacht Club",
                "count": 5,
                "chain": "solana",
                "sample_nfts": []
            }
        }


class NFTResponse(BaseModel):
    """NFT response for a wallet."""
    wallet_address: str
    chain: str
    nfts: List[NFT]
    total_nfts: int
    collections: List[CollectionSummary]
    
    class Config:
        json_schema_extra = {
            "example": {
                "wallet_address": "0x123...",
                "chain": "solana",
                "nfts": [],
                "total_nfts": 14,
                "collections": [
                    {
                        "collection_name": "Bored Ape Yacht Club",
                        "count": 5,
                        "chain": "solana",
                        "sample_nfts": []
                    }
                ]
            }
        }


class AggregatedNFTResponse(BaseModel):
    """Aggregated NFTs across all wallets."""
    total_nfts: int
    total_collections: int
    by_chain: Dict[str, int]  # {"aptos": 5, "solana": 9}
    collections: List[CollectionSummary]
    all_nfts: List[NFT]  # All NFTs for grid view
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_nfts": 14,
                "total_collections": 3,
                "by_chain": {
                    "aptos": 5,
                    "solana": 9
                },
                "collections": [],
                "all_nfts": []
            }
        }