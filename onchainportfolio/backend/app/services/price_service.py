# app/services/price_service.py
import httpx
from typing import Optional, Dict
import time


class PriceService:
    def __init__(self, ttl_seconds: int = 60):
        """
        Service to fetch cryptocurrency prices from multiple sources.
        
        - CoinGecko: For major tokens (APT, SOL, BTC, ETH, etc.)
        - Jupiter: For Solana SPL tokens (better coverage)
        
        Args:
            ttl_seconds: Cache TTL in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[float, float]] = {}  # symbol -> (price, timestamp)
        
        # CoinGecko API
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
        # Jupiter Price API (Solana-specific)
        self.jupiter_base_url = "https://price.jup.ag/v4"
        
        # Map token symbols to CoinGecko IDs
        self.coingecko_ids = {
            # Major coins
            "APT": "aptos",
            "SOL": "solana",
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "ADA": "cardano",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            
            # Stablecoins
            "USDC": "usd-coin",
            "USDT": "tether",
            "DAI": "dai",
            "BUSD": "binance-usd",
        }
        
        # Map Solana token symbols to mint addresses (for Jupiter)
        self.solana_mints = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            # Add more Solana tokens as needed
        }
    
    def get_price(self, symbol: str, chain: Optional[str] = None) -> Optional[float]:
        """
        Get USD price for a token symbol.
        
        Args:
            symbol: Token symbol (e.g., "APT", "SOL", "BONK")
            chain: Optional chain hint ("aptos", "solana")
                   If provided, uses chain-specific price source
        
        Returns:
            USD price as float, or None if not found
        """
        symbol = symbol.upper()
        
        # Check cache first
        cache_key = f"{symbol}:{chain}" if chain else symbol
        if cache_key in self._cache:
            price, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.ttl_seconds:
                print(f"[DEBUG] Using cached price for {symbol}: ${price}")
                return price
        
        # Determine which API to use
        if chain == "solana" or symbol in self.solana_mints:
            # Use Jupiter for Solana tokens (better coverage)
            price = self._get_price_from_jupiter(symbol)
        else:
            # Use CoinGecko for Aptos and major tokens
            price = self._get_price_from_coingecko(symbol)
        
        # Cache the result
        if price is not None:
            self._cache[cache_key] = (price, time.time())
        
        return price
    
    def _get_price_from_coingecko(self, symbol: str) -> Optional[float]:
        """
        Get price from CoinGecko API.
        
        Good for: APT, major chains, well-known tokens
        """
        coin_id = self.coingecko_ids.get(symbol)
        if not coin_id:
            print(f"[WARNING] No CoinGecko ID mapped for {symbol}")
            return None
        
        try:
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd"
            }
            
            print(f"[DEBUG] Fetching price for {symbol} from CoinGecko...")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if coin_id in data and "usd" in data[coin_id]:
                    price = float(data[coin_id]["usd"])
                    print(f"[DEBUG] CoinGecko price for {symbol}: ${price}")
                    return price
                else:
                    print(f"[WARNING] Price not found in CoinGecko response for {symbol}")
                    return None
                    
        except Exception as e:
            print(f"[ERROR] Failed to fetch price from CoinGecko for {symbol}: {e}")
            return None
    
    def _get_price_from_jupiter(self, symbol: str) -> Optional[float]:
        """
        Get price from Jupiter Price API (Solana-specific).
        
        Good for: All SPL tokens, including new/small cap tokens
        Free, no API key required
        """
        # Get mint address for this symbol
        mint_address = self.solana_mints.get(symbol)
        
        if not mint_address:
            print(f"[WARNING] No Solana mint address mapped for {symbol}")
            # Could try CoinGecko as fallback
            return self._get_price_from_coingecko(symbol)
        
        try:
            url = f"{self.jupiter_base_url}/price"
            params = {"ids": mint_address}
            
            print(f"[DEBUG] Fetching price for {symbol} from Jupiter...")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if "data" in data and mint_address in data["data"]:
                    token_data = data["data"][mint_address]
                    price = float(token_data.get("price", 0))
                    
                    print(f"[DEBUG] Jupiter price for {symbol}: ${price}")
                    return price
                else:
                    print(f"[WARNING] Price not found in Jupiter response for {symbol}")
                    return None
                    
        except Exception as e:
            print(f"[ERROR] Failed to fetch price from Jupiter for {symbol}: {e}")
            # Try CoinGecko as fallback
            return self._get_price_from_coingecko(symbol)
    
    def get_prices(
        self, 
        symbols: list[str],
        chain: Optional[str] = None
    ) -> Dict[str, Optional[float]]:
        """
        Get USD prices for multiple tokens at once.
        
        Args:
            symbols: List of token symbols
            chain: Optional chain hint for all symbols
        
        Returns:
            Dict mapping symbol to price
        """
        results = {}
        
        # Check cache first
        to_fetch = []
        for symbol in symbols:
            symbol = symbol.upper()
            cache_key = f"{symbol}:{chain}" if chain else symbol
            
            if cache_key in self._cache:
                price, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self.ttl_seconds:
                    results[symbol] = price
                    continue
            
            to_fetch.append(symbol)
        
        if not to_fetch:
            return results
        
        # Fetch prices for remaining symbols
        if chain == "solana":
            # Use Jupiter batch API for Solana tokens
            batch_results = self._get_prices_batch_jupiter(to_fetch)
            results.update(batch_results)
        else:
            # Use CoinGecko batch API for Aptos/major tokens
            batch_results = self._get_prices_batch_coingecko(to_fetch)
            results.update(batch_results)
        
        return results
    
    def _get_prices_batch_coingecko(self, symbols: list[str]) -> Dict[str, Optional[float]]:
        """Get prices for multiple tokens from CoinGecko at once."""
        results = {}
        
        # Get CoinGecko IDs
        coin_ids = []
        symbol_to_id = {}
        
        for symbol in symbols:
            coin_id = self.coingecko_ids.get(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                symbol_to_id[coin_id] = symbol
            else:
                results[symbol] = None
        
        if not coin_ids:
            return results
        
        try:
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd"
            }
            
            print(f"[DEBUG] Batch fetching {len(coin_ids)} prices from CoinGecko...")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                for coin_id, symbol in symbol_to_id.items():
                    if coin_id in data and "usd" in data[coin_id]:
                        price = float(data[coin_id]["usd"])
                        results[symbol] = price
                        # Cache it
                        self._cache[symbol] = (price, time.time())
                    else:
                        results[symbol] = None
                        
        except Exception as e:
            print(f"[ERROR] Failed to batch fetch prices from CoinGecko: {e}")
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None
        
        return results
    
    def _get_prices_batch_jupiter(self, symbols: list[str]) -> Dict[str, Optional[float]]:
        """Get prices for multiple Solana tokens from Jupiter at once."""
        results = {}
        
        # Get mint addresses
        mint_addresses = []
        mint_to_symbol = {}
        
        for symbol in symbols:
            mint = self.solana_mints.get(symbol)
            if mint:
                mint_addresses.append(mint)
                mint_to_symbol[mint] = symbol
            else:
                # Try CoinGecko as fallback
                results[symbol] = self._get_price_from_coingecko(symbol)
        
        if not mint_addresses:
            return results
        
        try:
            url = f"{self.jupiter_base_url}/price"
            params = {"ids": ",".join(mint_addresses)}
            
            print(f"[DEBUG] Batch fetching {len(mint_addresses)} prices from Jupiter...")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if "data" in data:
                    for mint, symbol in mint_to_symbol.items():
                        if mint in data["data"]:
                            price = float(data["data"][mint].get("price", 0))
                            results[symbol] = price
                            # Cache it
                            cache_key = f"{symbol}:solana"
                            self._cache[cache_key] = (price, time.time())
                        else:
                            results[symbol] = None
                            
        except Exception as e:
            print(f"[ERROR] Failed to batch fetch prices from Jupiter: {e}")
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None
        
        return results
    
# ============================================================
# SERVICE INSTANCE (for dependency injection)
# ============================================================

price_service = PriceService()