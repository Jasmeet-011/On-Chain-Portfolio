# backend/app/services/nft_service.py
"""
NFT Service - IMPROVED VERSION

Fetches NFTs from Solana (Helius DAS API) and Aptos (Indexer).
Includes fallbacks and better error handling.
"""
import httpx
import os
import asyncio
from typing import List, Dict, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from app.models.nft_models import NFT, CollectionSummary, NFTResponse


class NFTService:
    """Service for fetching NFTs from different chains"""
    
    def __init__(self):
        # API Keys and endpoints
        self.helius_api_key = os.getenv("HELIUS_API_KEY", "")
        self.simplehash_api_key = os.getenv("SIMPLEHASH_API_KEY", "")
        
        self.aptos_indexer_url = os.getenv(
            "APTOS_INDEXER_URL",
            "https://indexer.mainnet.aptoslabs.com/v1/graphql"
        )
        
        # Helius DAS API endpoint (newer, more reliable)
        self.helius_rpc_url = f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}" if self.helius_api_key else None
        
        # SimpleHash fallback (free tier: 1000 requests/day)
        self.simplehash_url = "https://api.simplehash.com/api/v0"
        
        print("[NFT] NFT service initialized")
        if self.helius_api_key:
            print("[NFT] ✅ Helius API key configured")
        else:
            print("[NFT] ⚠️  No Helius API key - Solana NFTs may fail")
        
        if self.simplehash_api_key:
            print("[NFT] ✅ SimpleHash API key configured (fallback)")
    
    # ============================================================
    # SOLANA NFTs - HELIUS DAS API (Primary)
    # ============================================================
    
    def get_solana_nfts_helius(self, wallet_address: str) -> List[NFT]:
        """
        Fetch Solana NFTs using Helius DAS (Digital Asset Standard) API.
        This is the newer, more reliable method.
        
        Args:
            wallet_address: Solana wallet address
            
        Returns:
            List of NFTs
        """
        if not self.helius_api_key:
            print("[NFT] ⚠️  No Helius API key - trying alternative methods")
            return self.get_solana_nfts_simplehash(wallet_address)
        
        print(f"[NFT] Fetching Solana NFTs via Helius DAS for {wallet_address[:8]}...")
        
        try:
            # DAS API - getAssetsByOwner
            payload = {
                "jsonrpc": "2.0",
                "id": "nft-fetch",
                "method": "getAssetsByOwner",
                "params": {
                    "ownerAddress": wallet_address,
                    "page": 1,
                    "limit": 100,
                    "displayOptions": {
                        "showFungible": False,
                        "showNativeBalance": False,
                        "showInscription": False,
                        "showCollectionMetadata": True
                    }
                }
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.helius_rpc_url, json=payload)
                
                print(f"[NFT] Helius response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"[NFT] ❌ Helius DAS error: {response.status_code}")
                    print(f"[NFT] Response: {response.text[:500]}")
                    return self.get_solana_nfts_simplehash(wallet_address)
                
                data = response.json()
            
            # Debug: Print raw response structure
            print(f"[NFT] Helius raw response keys: {data.keys()}")
            
            if "error" in data:
                print(f"[NFT] ❌ Helius DAS error: {data['error']}")
                return self.get_solana_nfts_simplehash(wallet_address)
            
            # Debug: Print result structure
            result = data.get("result", {})
            print(f"[NFT] Helius result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            print(f"[NFT] Helius total items: {result.get('total', 0)}")
            print(f"[NFT] Helius items count: {len(result.get('items', []))}")
            
            items = data.get("result", {}).get("items", [])
            nfts = []
            
            print(f"[NFT] Processing {len(items)} items from Helius...")
            
            for idx, item in enumerate(items):
                # Debug first few items
                if idx < 3:
                    print(f"[NFT] Item {idx}: interface={item.get('interface')}, id={item.get('id', '')[:20]}...")
                
                # Skip fungible tokens
                if item.get("interface") == "FungibleToken":
                    continue
                
                # Get content/metadata
                content = item.get("content", {})
                metadata = content.get("metadata", {})
                
                name = metadata.get("name", "Unknown NFT")
                
                # Get collection name
                collection_name = "Unknown Collection"
                grouping = item.get("grouping", [])
                for group in grouping:
                    if group.get("group_key") == "collection":
                        collection_name = group.get("group_value", "Unknown Collection")
                        # Try to get collection name from collection metadata
                        collection_meta = group.get("collection_metadata", {})
                        if collection_meta.get("name"):
                            collection_name = collection_meta["name"]
                        break
                
                # Get image URL
                image_url = None
                links = content.get("links", {})
                if links.get("image"):
                    image_url = links["image"]
                elif content.get("files"):
                    for f in content["files"]:
                        if f.get("mime", "").startswith("image"):
                            image_url = f.get("uri")
                            break
                
                # Convert IPFS to HTTP
                if image_url and image_url.startswith("ipfs://"):
                    image_url = f"https://ipfs.io/ipfs/{image_url[7:]}"
                
                # Use Cloudflare IPFS gateway (faster)
                if image_url and "ipfs.io" in image_url:
                    image_url = image_url.replace("ipfs.io", "cloudflare-ipfs.com")
                
                nfts.append(NFT(
                    name=name,
                    collection=collection_name,
                    image_url=image_url,
                    token_id=item.get("id"),
                    chain="solana"
                ))
            
            print(f"[NFT] ✅ Found {len(nfts)} Solana NFTs via Helius DAS")
            return nfts
        
        except httpx.TimeoutException:
            print("[NFT] ❌ Helius DAS timeout - trying fallback")
            return self.get_solana_nfts_simplehash(wallet_address)
        except Exception as e:
            print(f"[NFT] ❌ Error fetching Solana NFTs via Helius: {e}")
            return self.get_solana_nfts_simplehash(wallet_address)
    
    # ============================================================
    # SOLANA NFTs - SIMPLEHASH (Fallback)
    # ============================================================
    
    def get_solana_nfts_simplehash(self, wallet_address: str) -> List[NFT]:
        """
        Fallback: Fetch Solana NFTs using SimpleHash API.
        Free tier: 1000 requests/day
        
        Args:
            wallet_address: Solana wallet address
            
        Returns:
            List of NFTs
        """
        if not self.simplehash_api_key:
            print("[NFT] ⚠️  No SimpleHash API key - returning empty")
            return []
        
        print(f"[NFT] Fetching Solana NFTs via SimpleHash for {wallet_address[:8]}...")
        
        try:
            url = f"{self.simplehash_url}/nfts/owners"
            params = {
                "chains": "solana",
                "wallet_addresses": wallet_address,
                "limit": 50
            }
            headers = {
                "X-API-KEY": self.simplehash_api_key,
                "Accept": "application/json"
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params, headers=headers)
                
                if response.status_code != 200:
                    print(f"[NFT] ❌ SimpleHash error: {response.status_code}")
                    return []
                
                data = response.json()
            
            nfts = []
            
            for item in data.get("nfts", []):
                name = item.get("name", "Unknown NFT")
                collection_name = item.get("collection", {}).get("name", "Unknown Collection")
                
                # Get best image
                image_url = None
                previews = item.get("previews", {})
                image_url = (
                    previews.get("image_medium_url") or
                    previews.get("image_small_url") or
                    item.get("image_url")
                )
                
                nfts.append(NFT(
                    name=name,
                    collection=collection_name,
                    image_url=image_url,
                    token_id=item.get("nft_id"),
                    chain="solana"
                ))
            
            print(f"[NFT] ✅ Found {len(nfts)} Solana NFTs via SimpleHash")
            return nfts
        
        except Exception as e:
            print(f"[NFT] ❌ Error fetching Solana NFTs via SimpleHash: {e}")
            return []
    
    # ============================================================
    # SOLANA NFTs - Public Endpoint (No API Key)
    # ============================================================
    
    def get_solana_nfts_public(self, wallet_address: str) -> List[NFT]:
        """
        Fallback: Try to fetch using public Solana RPC.
        Very limited but works without API key.
        
        This is a placeholder - real implementation would need
        to parse token accounts manually.
        """
        print(f"[NFT] ⚠️  No API keys available for Solana NFTs")
        return []
    
    # ============================================================
    # APTOS NFTs (Indexer API)
    # ============================================================
    
    def get_aptos_nfts(self, wallet_address: str) -> List[NFT]:
        """
        Fetch Aptos NFTs using Indexer GraphQL API.
        
        Args:
            wallet_address: Aptos wallet address
            
        Returns:
            List of NFTs
        """
        print(f"[NFT] Fetching Aptos NFTs for {wallet_address[:8]}...")
        
        try:
            # GraphQL query for current token ownerships v2
            query = """
            query GetNFTs($owner_address: String!) {
              current_token_ownerships_v2(
                where: {
                  owner_address: {_eq: $owner_address},
                  amount: {_gt: "0"}
                }
                limit: 100
                order_by: {last_transaction_timestamp: desc}
              ) {
                current_token_data {
                  token_name
                  token_uri
                  token_data_id
                  description
                  current_collection {
                    collection_name
                    uri
                    description
                  }
                }
                token_data_id
                amount
              }
            }
            """
            
            variables = {"owner_address": wallet_address}
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.aptos_indexer_url,
                    json={"query": query, "variables": variables},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    print(f"[NFT] ❌ Aptos Indexer error: {response.status_code}")
                    print(f"[NFT] Response: {response.text[:200]}")
                    return []
                
                data = response.json()
            
            if "errors" in data:
                print(f"[NFT] ❌ Aptos GraphQL errors: {data['errors']}")
                return []
            
            nfts = []
            ownerships = data.get("data", {}).get("current_token_ownerships_v2", [])
            
            for item in ownerships:
                token_data = item.get("current_token_data", {})
                if not token_data:
                    continue
                
                name = token_data.get("token_name", "Unknown NFT")
                
                # Get collection name
                collection_name = "Unknown Collection"
                if token_data.get("current_collection"):
                    collection_name = token_data["current_collection"].get(
                        "collection_name", "Unknown Collection"
                    )
                
                # Try to get image from token_uri
                image_url = None
                token_uri = token_data.get("token_uri", "")
                
                # If token_uri is a direct image URL
                if token_uri and any(token_uri.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']):
                    image_url = token_uri
                # If it's IPFS
                elif token_uri and token_uri.startswith("ipfs://"):
                    # This might be metadata JSON, but let's try
                    image_url = f"https://cloudflare-ipfs.com/ipfs/{token_uri[7:]}"
                elif token_uri and "ipfs" in token_uri:
                    image_url = token_uri.replace("ipfs.io", "cloudflare-ipfs.com")
                
                # Try to fetch metadata if token_uri looks like JSON
                if token_uri and not image_url and (token_uri.startswith("http") or token_uri.startswith("ipfs")):
                    image_url = self._try_fetch_aptos_image(token_uri)
                
                nfts.append(NFT(
                    name=name,
                    collection=collection_name,
                    image_url=image_url,
                    token_id=item.get("token_data_id"),
                    chain="aptos"
                ))
            
            print(f"[NFT] ✅ Found {len(nfts)} Aptos NFTs")
            return nfts
        
        except httpx.TimeoutException:
            print("[NFT] ❌ Aptos Indexer timeout")
            return []
        except Exception as e:
            print(f"[NFT] ❌ Error fetching Aptos NFTs: {e}")
            return []
    
    def _try_fetch_aptos_image(self, uri: str) -> Optional[str]:
        """
        Try to fetch image URL from Aptos token metadata.
        
        Args:
            uri: Token URI (might be JSON metadata)
            
        Returns:
            Image URL or None
        """
        try:
            # Convert IPFS URI
            if uri.startswith("ipfs://"):
                uri = f"https://cloudflare-ipfs.com/ipfs/{uri[7:]}"
            
            # Skip if it's clearly an image
            if any(uri.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                return uri
            
            # Try to fetch metadata (with short timeout)
            with httpx.Client(timeout=5.0) as client:
                response = client.get(uri)
                
                if response.status_code != 200:
                    return None
                
                # Try to parse as JSON
                try:
                    metadata = response.json()
                    
                    # Look for image field
                    image = (
                        metadata.get("image") or
                        metadata.get("image_url") or
                        metadata.get("animation_url") or
                        metadata.get("uri")
                    )
                    
                    if image:
                        # Convert IPFS
                        if image.startswith("ipfs://"):
                            image = f"https://cloudflare-ipfs.com/ipfs/{image[7:]}"
                        return image
                    
                except:
                    # Not JSON, might be the image itself
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type:
                        return uri
            
            return None
        except:
            return None
    
    # ============================================================
    # MAIN INTERFACE
    # ============================================================
    
    def get_solana_nfts(self, wallet_address: str) -> List[NFT]:
        """
        Get Solana NFTs using best available method.
        
        Priority:
        1. Helius DAS API (if key available)
        2. SimpleHash API (if key available)
        3. Empty list
        """
        return self.get_solana_nfts_helius(wallet_address)
    
    def get_nfts_for_wallet(
        self,
        wallet_address: str,
        chain: str
    ) -> NFTResponse:
        """
        Get all NFTs for a single wallet.
        
        Args:
            wallet_address: Wallet address
            chain: "aptos" or "solana"
            
        Returns:
            NFTResponse with NFTs and collection summary
        """
        print(f"[NFT] Getting NFTs for {wallet_address[:8]}... (chain: {chain})")
        
        # Fetch NFTs
        if chain == "solana":
            nfts = self.get_solana_nfts(wallet_address)
        elif chain == "aptos":
            nfts = self.get_aptos_nfts(wallet_address)
        else:
            print(f"[NFT] ❌ Unknown chain: {chain}")
            nfts = []
        
        # Group by collection
        collections_map: Dict[str, List[NFT]] = defaultdict(list)
        for nft in nfts:
            collections_map[nft.collection].append(nft)
        
        # Create collection summaries
        collections = [
            CollectionSummary(
                collection_name=collection_name,
                count=len(collection_nfts),
                chain=chain,
                sample_nfts=collection_nfts[:5]  # First 5 NFTs
            )
            for collection_name, collection_nfts in collections_map.items()
        ]
        
        # Sort by count
        collections.sort(key=lambda c: c.count, reverse=True)
        
        return NFTResponse(
            wallet_address=wallet_address,
            chain=chain,
            nfts=nfts,
            total_nfts=len(nfts),
            collections=collections
        )
    
    def aggregate_nfts(
        self,
        wallet_nfts: List[NFTResponse]
    ) -> Dict:
        """
        Aggregate NFTs across multiple wallets.
        
        Args:
            wallet_nfts: List of NFTResponse for each wallet
            
        Returns:
            Aggregated NFT data
        """
        all_nfts = []
        collections_map: Dict[str, List[NFT]] = defaultdict(list)
        by_chain: Dict[str, int] = defaultdict(int)
        
        for wallet_response in wallet_nfts:
            all_nfts.extend(wallet_response.nfts)
            by_chain[wallet_response.chain] += wallet_response.total_nfts
            
            # Group by collection (use collection + chain as key to separate same-named collections)
            for nft in wallet_response.nfts:
                key = f"{nft.collection}_{nft.chain}"
                collections_map[key].append(nft)
        
        # Create collection summaries
        collections = []
        for key, nfts in collections_map.items():
            if not nfts:
                continue
            
            collection_name = nfts[0].collection
            chain = nfts[0].chain
            
            collections.append(CollectionSummary(
                collection_name=collection_name,
                count=len(nfts),
                chain=chain,
                sample_nfts=nfts[:5]
            ))
        
        # Sort by count
        collections.sort(key=lambda c: c.count, reverse=True)
        
        return {
            "total_nfts": len(all_nfts),
            "total_collections": len(collections),
            "by_chain": dict(by_chain),
            "collections": collections,
            "all_nfts": all_nfts
        }


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_nft_service: Optional[NFTService] = None

def get_nft_service() -> NFTService:
    """Get or create NFT service singleton."""
    global _nft_service
    if _nft_service is None:
        _nft_service = NFTService()
    return _nft_service