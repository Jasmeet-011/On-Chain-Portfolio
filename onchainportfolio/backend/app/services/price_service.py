# app/services/price_service.py
import httpx
from typing import Optional, Dict
import time


class PriceService:
    def __init__(self, ttl_seconds: int = 60):
        """
        Service to fetch cryptocurrency prices from CoinGecko.
        
        Args:
            ttl_seconds: Cache TTL in seconds
        """
        self.base_url = "https://api.coingecko.com/api/v3"
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[float, float]] = {}  # symbol -> (price, timestamp)
        
        # Map token symbols to CoinGecko IDs
        self.coin_ids = {
            "APT": "aptos",
            "USDC": "usd-coin",
            "USDT": "tether",
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "BNB": "binancecoin",
            "ADA": "cardano",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            # Add more as needed
        }
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get USD price for a token symbol.
        
        Args:
            symbol: Token symbol (e.g., "APT")
            
        Returns:
            USD price as float, or None if not found
        """
        symbol = symbol.upper()
        
        # Check cache first
        if symbol in self._cache:
            price, timestamp = self._cache[symbol]
            if time.time() - timestamp < self.ttl_seconds:
                print(f"[DEBUG] Using cached price for {symbol}: ${price}")
                return price
        
        # Get CoinGecko ID
        coin_id = self.coin_ids.get(symbol)
        if not coin_id:
            print(f"[WARNING] No CoinGecko ID mapped for {symbol}")
            return None
        
        # Fetch from CoinGecko
        try:
            url = f"{self.base_url}/simple/price"
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
                    
                    # Cache it
                    self._cache[symbol] = (price, time.time())
                    
                    print(f"[DEBUG] Fetched price for {symbol}: ${price}")
                    return price
                else:
                    print(f"[WARNING] Price not found in response for {symbol}")
                    return None
                    
        except Exception as e:
            print(f"[ERROR] Failed to fetch price for {symbol}: {e}")
            return None
    
    def get_prices(self, symbols: list[str]) -> Dict[str, Optional[float]]:
        """
        Get USD prices for multiple tokens at once (more efficient).
        
        Args:
            symbols: List of token symbols (e.g., ["APT", "USDC"])
            
        Returns:
            Dict mapping symbol to price
        """
        results = {}
        
        # Separate cached and non-cached
        to_fetch = []
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in self._cache:
                price, timestamp = self._cache[symbol]
                if time.time() - timestamp < self.ttl_seconds:
                    results[symbol] = price
                    continue
            to_fetch.append(symbol)
        
        if not to_fetch:
            return results
        
        # Get CoinGecko IDs for symbols we need to fetch
        coin_ids_to_fetch = []
        symbol_to_id = {}
        
        for symbol in to_fetch:
            coin_id = self.coin_ids.get(symbol)
            if coin_id:
                coin_ids_to_fetch.append(coin_id)
                symbol_to_id[coin_id] = symbol
            else:
                results[symbol] = None
        
        if not coin_ids_to_fetch:
            return results
        
        # Fetch all at once
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": ",".join(coin_ids_to_fetch),
                "vs_currencies": "usd"
            }
            
            print(f"[DEBUG] Fetching prices for {len(coin_ids_to_fetch)} tokens...")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                for coin_id, symbol in symbol_to_id.items():
                    if coin_id in data and "usd" in data[coin_id]:
                        price = float(data[coin_id]["usd"])
                        results[symbol] = price
                        self._cache[symbol] = (price, time.time())
                    else:
                        results[symbol] = None
                        
        except Exception as e:
            print(f"[ERROR] Failed to fetch prices: {e}")
            for symbol in to_fetch:
                if symbol not in results:
                    results[symbol] = None
        
        return results