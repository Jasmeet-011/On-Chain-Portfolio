# backend/app/services/history_service.py - FIXED: Better Error Handling
import httpx
import time
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta


class HistoryService:
    """
    Service for fetching historical cryptocurrency prices.
    
    ✅ FIXED:
    - Better error handling for missing token histories
    - Filters out $0 values
    - Continues even if some tokens fail
    - More detailed logging
    """
    
    def __init__(self, cache_ttl_seconds: int = 3600):
        """
        Initialize history service.
        
        Args:
            cache_ttl_seconds: Cache TTL (default 1 hour = 3600 seconds)
        """
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Tuple[List[Dict], float]] = {}
        
        # CoinGecko API
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
        # Map symbols to CoinGecko IDs
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
            "AVAX": "avalanche-2",
            "ATOM": "cosmos",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "LTC": "litecoin",
            
            # Stablecoins
            "USDC": "usd-coin",
            "USDT": "tether",
            "DAI": "dai",
            "BUSD": "binance-usd",
            "TUSD": "true-usd",
            "USDD": "usdd",
        }
    
    def get_price_history(
        self, 
        symbol: str, 
        days: int = 7,
        chain: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get historical prices for a token.
        
        Args:
            symbol: Token symbol (e.g., "SOL", "APT")
            days: Number of days to fetch (1, 7, 30, 90, 365)
            chain: Optional chain hint
        
        Returns:
            Price history data or None if unavailable
        """
        symbol = symbol.upper()
        
        # Check cache
        cache_key = f"{symbol}:{days}:{chain or 'any'}"
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                print(f"[HISTORY] ✓ Cache hit for {symbol} ({days}d)")
                return self._format_response(symbol, data)
        
        # Fetch from CoinGecko
        coin_id = self.coingecko_ids.get(symbol)
        if not coin_id:
            print(f"[WARNING] No CoinGecko ID for {symbol} - token not supported")
            return None
        
        try:
            print(f"[HISTORY] Fetching {symbol} history ({days}d) from CoinGecko...")
            
            url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days
            }
            
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=params)
                
                if response.status_code == 429:
                    print(f"[ERROR] Rate limited by CoinGecko! Try again later.")
                    return None
                
                if response.status_code == 401:
                    print(f"[ERROR] CoinGecko API authentication error")
                    return None
                
                if response.status_code != 200:
                    print(f"[ERROR] CoinGecko returned status {response.status_code}")
                    return None
                
                data = response.json()
            
            prices = data.get("prices", [])
            
            if not prices:
                print(f"[WARNING] No price data returned for {symbol}")
                return None
            
            print(f"[SUCCESS] ✓ Got {len(prices)} data points for {symbol}")
            
            # Cache the raw data
            self._cache[cache_key] = (prices, time.time())
            
            return self._format_response(symbol, prices)
            
        except httpx.TimeoutException:
            print(f"[ERROR] Timeout fetching history for {symbol}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to fetch history for {symbol}: {e}")
            return None
    
    def _format_response(self, symbol: str, prices: List) -> Dict:
        """Format CoinGecko response into our API format."""
        if not prices or len(prices) == 0:
            return None
        
        # Convert to our format
        formatted_prices = [
            {
                "timestamp": int(ts / 1000),  # Convert ms to seconds
                "price": float(price)
            }
            for ts, price in prices
        ]
        
        # Calculate metrics
        current_price = formatted_prices[-1]["price"]
        first_price = formatted_prices[0]["price"]
        
        # 24h change (use data from ~24h ago if available)
        if len(formatted_prices) > 24:
            price_24h_ago = formatted_prices[-25]["price"]
        else:
            price_24h_ago = first_price
        
        change_24h = current_price - price_24h_ago
        change_percent = (change_24h / price_24h_ago * 100) if price_24h_ago > 0 else 0
        
        # Total period change
        total_change = current_price - first_price
        total_change_percent = (total_change / first_price * 100) if first_price > 0 else 0
        
        return {
            "symbol": symbol,
            "prices": formatted_prices,
            "current_price": round(current_price, 2),
            "change_24h": round(change_24h, 2),
            "change_percent": round(change_percent, 2),
            "period_change": round(total_change, 2),
            "period_change_percent": round(total_change_percent, 2),
            "data_points": len(formatted_prices)
        }
    
    def get_portfolio_history(
        self,
        balances: List[Dict],
        days: int = 7
    ) -> Optional[Dict]:
        """
        Calculate historical portfolio value based on current holdings.
        
        ✅ FIXED: Now handles missing token histories gracefully!
        
        Args:
            balances: List of current token balances
                [{"symbol": "SOL", "amount": 2.5}, ...]
            days: Number of days to calculate
        
        Returns:
            Portfolio value history
        """
        if not balances or len(balances) == 0:
            print("[WARNING] No balances provided")
            return None
        
        print(f"[HISTORY] Calculating portfolio history for {len(balances)} tokens over {days} days")
        
        # Get price history for each token
        token_histories = {}
        tokens_succeeded = 0
        tokens_failed = 0
        
        for balance in balances:
            symbol = balance.get("symbol")
            amount = balance.get("amount", 0)
            
            if not symbol or amount == 0:
                continue
            
            print(f"[HISTORY] Fetching history for {symbol} (balance: {amount})...")
            history = self.get_price_history(symbol, days=days)
            
            if history and history.get("prices"):
                token_histories[symbol] = {
                    "amount": amount,
                    "prices": history["prices"]
                }
                tokens_succeeded += 1
                print(f"[HISTORY]   ✓ {symbol}: {len(history['prices'])} price points")
            else:
                tokens_failed += 1
                print(f"[HISTORY]   ✗ {symbol}: No price history available")
        
        print(f"[HISTORY] Token history fetch complete: {tokens_succeeded} succeeded, {tokens_failed} failed")
        
        if not token_histories:
            print("[ERROR] No price history available for any tokens")
            return None
        
        # ✅ FIXED: Use the token with most data points as reference
        reference_token = max(
            token_histories.values(),
            key=lambda x: len(x["prices"])
        )
        timestamps = [p["timestamp"] for p in reference_token["prices"]]
        
        print(f"[HISTORY] Using {len(timestamps)} timestamps for portfolio calculation")
        
        # Calculate portfolio value at each timestamp
        portfolio_values = []
        valid_points = 0
        zero_value_points = 0
        
        for i, ts in enumerate(timestamps):
            total_value = 0.0
            tokens_processed = 0
            
            # ✅ FIXED: Better error handling
            for symbol, data in token_histories.items():
                try:
                    # Check if this token has data for this timestamp
                    if i < len(data["prices"]):
                        price = data["prices"][i]["price"]
                        
                        # ✅ FIXED: Skip if price is 0 (bad data)
                        if price > 0:
                            value = data["amount"] * price
                            total_value += value
                            tokens_processed += 1
                        else:
                            print(f"[WARNING] {symbol} has $0 price at index {i}")
                    
                except (KeyError, IndexError, TypeError) as e:
                    print(f"[WARNING] Failed to calculate value for {symbol} at index {i}: {e}")
                    continue
            
            # ✅ FIXED: Only add point if we have valid data
            if tokens_processed > 0 and total_value > 0:
                portfolio_values.append({
                    "timestamp": ts,
                    "value": round(total_value, 2)
                })
                valid_points += 1
            else:
                zero_value_points += 1
        
        print(f"[HISTORY] Portfolio calculation complete:")
        print(f"  Valid points: {valid_points}")
        print(f"  Zero/invalid points: {zero_value_points}")
        
        if not portfolio_values:
            print("[ERROR] No valid portfolio values calculated")
            return None
        
        # Calculate metrics
        current_value = portfolio_values[-1]["value"]
        first_value = portfolio_values[0]["value"]
        total_change = current_value - first_value
        total_change_percent = (total_change / first_value * 100) if first_value > 0 else 0
        
        print(f"[HISTORY] Final portfolio stats:")
        print(f"  Current value: ${current_value:.2f}")
        print(f"  First value: ${first_value:.2f}")
        print(f"  Change: ${total_change:.2f} ({total_change_percent:.2f}%)")
        
        return {
            "values": portfolio_values,
            "current_value": current_value,
            "period_change": round(total_change, 2),
            "period_change_percent": round(total_change_percent, 2),
            "data_points": len(portfolio_values)
        }
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        print("[HISTORY] Cache cleared")