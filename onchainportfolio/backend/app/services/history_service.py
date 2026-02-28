# backend/app/services/history_service.py
import httpx
import time
from typing import Optional, Dict, List, Tuple


class HistoryService:
    """
    Service for fetching historical cryptocurrency prices.

    Data sources (priority order):
    1. Binance Klines API (free, no key, covers 200+ tokens, fast)
    2. CoinGecko market_chart (fallback for tokens not on Binance)

    Stablecoins return a flat $1.00 line (no API needed).
    """

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Tuple[List[Dict], float]] = {}

        # Binance Klines API (primary — free, fast, no rate limit issues)
        self.binance_base = "https://api.binance.com/api/v3"

        # CoinGecko API (fallback)
        self.coingecko_base = "https://api.coingecko.com/api/v3"

        # Stablecoins: always $1.00, no API call needed
        self.stablecoins = {
            "USDC", "USDT", "DAI", "BUSD", "TUSD", "FRAX",
            "LUSD", "SUSD", "USDD", "GUSD", "USDBC", "USDC.E",
        }

        # Binance trading pairs for historical klines
        self.binance_symbols = {
            "BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT",
            "SOL": "SOLUSDT", "APT": "APTUSDT", "ADA": "ADAUSDT",
            "XRP": "XRPUSDT", "DOGE": "DOGEUSDT", "LTC": "LTCUSDT",
            "DOT": "DOTUSDT", "AVAX": "AVAXUSDT", "MATIC": "MATICUSDT",
            "ATOM": "ATOMUSDT", "FIL": "FILUSDT", "GRT": "GRTUSDT",
            "WETH": "ETHUSDT", "WBTC": "BTCUSDT", "WMATIC": "MATICUSDT",
            "UNI": "UNIUSDT", "AAVE": "AAVEUSDT", "LINK": "LINKUSDT",
            "MKR": "MKRUSDT", "CRV": "CRVUSDT", "COMP": "COMPUSDT",
            "LDO": "LDOUSDT", "SNX": "SNXUSDT", "SUSHI": "SUSHIUSDT",
            "ARB": "ARBUSDT", "OP": "OPUSDT",
            "SHIB": "SHIBUSDT", "PEPE": "PEPEUSDT",
            "BONK": "BONKUSDT", "JUP": "JUPUSDT", "RAY": "RAYUSDT",
            "ORCA": "ORCAUSDT",
        }

        # CoinGecko ID map (fallback only)
        self.coingecko_ids = {
            "APT": "aptos", "SOL": "solana", "BTC": "bitcoin",
            "ETH": "ethereum", "BNB": "binancecoin", "ADA": "cardano",
            "DOT": "polkadot", "MATIC": "matic-network", "AVAX": "avalanche-2",
            "ATOM": "cosmos", "LINK": "chainlink", "UNI": "uniswap",
            "XRP": "ripple", "DOGE": "dogecoin", "LTC": "litecoin",
            "USDC": "usd-coin", "USDT": "tether", "DAI": "dai",
            "BUSD": "binance-usd", "BONK": "bonk", "JUP": "jupiter-exchange-solana",
        }
    
    def _get_binance_interval(self, days: int) -> Tuple[str, int]:
        """Return (interval, limit) for Binance klines based on requested days."""
        if days <= 1:
            return "1h", 24
        elif days <= 7:
            return "4h", 42       # 42 × 4h = 168h = 7 days
        elif days <= 30:
            return "1d", 30
        elif days <= 90:
            return "1d", 90
        else:
            return "1d", min(days, 365)

    def _get_price_history_from_binance(self, symbol: str, days: int) -> Optional[List]:
        """
        Fetch historical prices from Binance Klines API.
        Returns list of [timestamp_seconds, price] pairs, or None on failure.
        """
        pair = self.binance_symbols.get(symbol)
        if not pair:
            return None

        interval, limit = self._get_binance_interval(days)

        try:
            url = f"{self.binance_base}/klines"
            params = {"symbol": pair, "interval": interval, "limit": limit}

            with httpx.Client(timeout=12.0) as client:
                response = client.get(url, params=params)
                if response.status_code != 200:
                    return None
                klines = response.json()

            if not klines:
                return None

            # kline format: [openTime, open, high, low, CLOSE, volume, closeTime, ...]
            # closeTime (index 6) in ms, close price (index 4)
            prices = []
            for k in klines:
                ts = int(k[6]) // 1000   # closeTime ms → seconds
                price = float(k[4])       # close price
                prices.append([ts * 1000, price])  # keep ms format for _format_response

            print(f"[HISTORY] ✓ Binance {symbol} ({days}d): {len(prices)} points via {pair}")
            return prices

        except Exception as e:
            print(f"[HISTORY] Binance error for {symbol}: {e}")
            return None

    def _get_stablecoin_history(self, symbol: str, days: int) -> List:
        """Generate a flat $1.00 price history for stablecoins."""
        interval, limit = self._get_binance_interval(days)
        now_ms = int(time.time() * 1000)
        # interval in milliseconds
        interval_ms = {"1h": 3600_000, "4h": 14400_000, "1d": 86400_000}.get(interval, 3600_000)
        prices = []
        for i in range(limit, 0, -1):
            ts = now_ms - i * interval_ms
            prices.append([ts, 1.0])
        return prices

    def get_price_history(
        self,
        symbol: str,
        days: int = 7,
        chain: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get historical prices for a token.
        Priority: Cache → Stablecoin flat line → Binance Klines → CoinGecko
        """
        symbol = symbol.upper()

        # Check cache
        cache_key = f"{symbol}:{days}:{chain or 'any'}"
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                print(f"[HISTORY] ✓ Cache hit for {symbol} ({days}d)")
                return self._format_response(symbol, data)

        # Stablecoins: return flat $1.00 line (no API needed)
        if symbol in self.stablecoins:
            prices = self._get_stablecoin_history(symbol, days)
            self._cache[cache_key] = (prices, time.time())
            return self._format_response(symbol, prices)

        # Try Binance Klines first (free, fast, no rate limits)
        binance_prices = self._get_price_history_from_binance(symbol, days)
        if binance_prices:
            self._cache[cache_key] = (binance_prices, time.time())
            return self._format_response(symbol, binance_prices)

        # Fallback: CoinGecko market_chart
        coin_id = self.coingecko_ids.get(symbol)
        if not coin_id:
            print(f"[HISTORY] No price source for {symbol}")
            return None

        try:
            print(f"[HISTORY] Falling back to CoinGecko for {symbol} ({days}d)...")
            url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
            params = {"vs_currency": "usd", "days": days}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=params)

                if response.status_code == 429:
                    print(f"[HISTORY] CoinGecko rate limited for {symbol}")
                    return None
                if response.status_code != 200:
                    print(f"[HISTORY] CoinGecko error {response.status_code} for {symbol}")
                    return None

                data = response.json()

            prices = data.get("prices", [])
            if not prices:
                return None

            print(f"[HISTORY] ✓ CoinGecko {symbol}: {len(prices)} points")
            self._cache[cache_key] = (prices, time.time())
            return self._format_response(symbol, prices)

        except Exception as e:
            print(f"[HISTORY] CoinGecko error for {symbol}: {e}")
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