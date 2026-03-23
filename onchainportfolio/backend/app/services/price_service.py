# backend/app/services/price_service.py
"""
Price Service - Multi-Chain Token Pricing

Supports:
- CoinGecko: Major tokens across all chains
- Jupiter: Solana SPL tokens
- DefiLlama: Additional token coverage

All testnet tokens use mainnet prices (testnets have no real value)

Includes both sync and async methods for flexibility:
- Sync: get_price(), get_prices()
- Async: get_price_async(), get_prices_async()
"""
import httpx
import asyncio
from typing import Optional, Dict, List
import time
import logging

logger = logging.getLogger("chainlens.services.price")


class PriceService:
    def __init__(self, ttl_seconds: int = 300, coingecko_api_key: str = ""):
        """
        Service to fetch cryptocurrency prices from multiple sources.

        Priority order (most reliable first):
        1. Cache (5 min TTL)
        2. Stablecoins hardcoded to $1.00 (USDC, USDT, DAI, etc.)
        3. Binance Public API (free, no key, covers 200+ major tokens)
        4. Jupiter (Solana tokens via mint address)
        5. CoinGecko (last resort — rate limited on free tier)
        6. DefiLlama (chain-specific token fallback)

        Args:
            ttl_seconds: Cache TTL in seconds (default 5 min to reduce API calls)
            coingecko_api_key: Optional CoinGecko API key for higher rate limits
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[float, float]] = {}  # key -> (price, timestamp)

        # Rate limit cooldown: after a 429, pause all CoinGecko calls for this many seconds
        self._coingecko_cooldown_until = 0.0  # timestamp when cooldown expires
        self._coingecko_cooldown_seconds = 60  # wait 60s after a 429

        # CoinGecko API key setup
        self._coingecko_api_key = coingecko_api_key
        if coingecko_api_key:
            self.coingecko_base_url = "https://api.coingecko.com/api/v3"
            self._coingecko_headers = {"x_cg_demo_api_key": coingecko_api_key}
            print(f"[PRICE] CoinGecko API key configured (higher rate limits)")
        else:
            self.coingecko_base_url = "https://api.coingecko.com/api/v3"
            self._coingecko_headers = {}
            print(f"[PRICE] CoinGecko using free tier (Binance+Jupiter used as primary)")

        # API endpoints
        self.binance_base_url = "https://api.binance.com/api/v3"
        self.jupiter_base_url = "https://api.jup.ag/price/v2"
        self.defillama_base_url = "https://coins.llama.fi"

        # ============================================================
        # Stablecoins — hardcoded to $1.00 (no API needed, saves quota)
        # ============================================================
        self.stablecoin_prices = {
            "USDC": 1.0, "USDT": 1.0, "DAI": 1.0, "BUSD": 1.0,
            "TUSD": 1.0, "USDP": 1.0, "FRAX": 1.0, "LUSD": 1.0,
            "SUSD": 1.0, "USDD": 1.0, "GUSD": 1.0, "USDK": 1.0,
            "HUSD": 1.0, "USDBC": 1.0, "USDC.E": 1.0,
        }

        # ============================================================
        # Binance symbol mappings (symbol → Binance trading pair)
        # Binance is free, no API key, 1200 req/min rate limit
        # ============================================================
        self.binance_symbols = {
            # Layer 1 / Major tokens
            "BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT",
            "SOL": "SOLUSDT", "APT": "APTUSDT", "ADA": "ADAUSDT",
            "XRP": "XRPUSDT", "DOGE": "DOGEUSDT", "LTC": "LTCUSDT",
            "DOT": "DOTUSDT", "AVAX": "AVAXUSDT", "MATIC": "MATICUSDT",
            "ATOM": "ATOMUSDT", "FIL": "FILUSDT", "GRT": "GRTUSDT",
            # Wrapped tokens (use underlying)
            "WETH": "ETHUSDT", "WBTC": "BTCUSDT", "WMATIC": "MATICUSDT",
            "STETH": "ETHUSDT", "CBETH": "ETHUSDT", "RETH": "ETHUSDT",
            # DeFi tokens
            "UNI": "UNIUSDT", "AAVE": "AAVEUSDT", "LINK": "LINKUSDT",
            "MKR": "MKRUSDT", "CRV": "CRVUSDT", "COMP": "COMPUSDT",
            "LDO": "LDOUSDT", "SNX": "SNXUSDT", "SUSHI": "SUSHIUSDT",
            "1INCH": "1INCHUSDT",
            # Layer 2 / Ecosystem
            "ARB": "ARBUSDT", "OP": "OPUSDT",
            # Meme / Popular
            "SHIB": "SHIBUSDT", "PEPE": "PEPEUSDT",
            # Solana ecosystem
            "BONK": "BONKUSDT", "JUP": "JUPUSDT", "RAY": "RAYUSDT",
            "ORCA": "ORCAUSDT",
        }
        
        # ============================================================
        # CoinGecko ID Mappings
        # ============================================================
        
        self.coingecko_ids = {
            # Native Tokens
            "ETH": "ethereum",
            "MATIC": "matic-network",
            "SOL": "solana",
            "APT": "aptos",
            "BTC": "bitcoin",
            "BNB": "binancecoin",
            
            # Stablecoins
            "USDC": "usd-coin",
            "USDT": "tether",
            "DAI": "dai",
            "BUSD": "binance-usd",
            "FRAX": "frax",
            "LUSD": "liquity-usd",
            "USDC.e": "usd-coin",  # Bridged USDC
            "USDbC": "bridged-usdc-base",
            
            # Wrapped Tokens
            "WETH": "weth",
            "WBTC": "wrapped-bitcoin",
            "WMATIC": "wmatic",
            "stETH": "staked-ether",
            "cbETH": "coinbase-wrapped-staked-eth",
            "rETH": "rocket-pool-eth",
            
            # DeFi Tokens
            "UNI": "uniswap",
            "AAVE": "aave",
            "LINK": "chainlink",
            "MKR": "maker",
            "CRV": "curve-dao-token",
            "COMP": "compound-governance-token",
            "LDO": "lido-dao",
            "SNX": "havven",
            "SUSHI": "sushi",
            "1INCH": "1inch",
            
            # Layer 2 / Ecosystem Tokens
            "ARB": "arbitrum",
            "OP": "optimism",
            "AERO": "aerodrome-finance",
            "VELO": "velodrome-finance",
            
            # Other Popular Tokens
            "PEPE": "pepe",
            "SHIB": "shiba-inu",
            "DOGE": "dogecoin",
            "GRT": "the-graph",
            "FIL": "filecoin",
            "ATOM": "cosmos",
            "DOT": "polkadot",
            "AVAX": "avalanche-2",
            
            # Base Ecosystem
            "BRETT": "brett",
            "DEGEN": "degen-base",
            "TOSHI": "toshi",
            
            # Solana Ecosystem
            "BONK": "bonk",
            "JUP": "jupiter-exchange-solana",
            "RAY": "raydium",
            "ORCA": "orca",
            "MNGO": "mango-markets",
        }
        
        # ============================================================
        # Solana Token Mint Addresses (for Jupiter API)
        # ============================================================
        
        self.solana_mints = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
            "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
            "MNGO": "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac",
        }
        
        # ============================================================
        # Chain-specific token address to symbol mapping
        # Used for DefiLlama API
        # ============================================================
        
        self.chain_tokens = {
            "ethereum": {
                "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC",
                "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
                "0x6B175474E89094C44Da98b954EesdeC16B7B1365CA": "DAI",
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
            },
            "polygon": {
                "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174": "USDC",
                "0xc2132D05D31c914a87C6611C10748AEb04B58e8F": "USDT",
                "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270": "WMATIC",
            },
            "base": {
                "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": "USDC",
                "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA": "USDbC",
                "0x4200000000000000000000000000000000000006": "WETH",
            },
        }
    
    # ============================================================
    # Main Price Fetching Methods
    # ============================================================
    
    def get_price(
        self,
        symbol: str,
        chain: Optional[str] = None
    ) -> Optional[float]:
        """
        Get USD price for a token symbol.

        Priority: Cache → Stablecoin hardcode → Binance → Jupiter (Solana) → CoinGecko → DefiLlama
        """
        symbol = symbol.upper()

        # Normalize testnet chains to mainnet (same prices)
        if chain:
            chain = self._normalize_chain(chain)

        # Check cache first
        cache_key = f"{symbol}:{chain}" if chain else symbol
        cached_price = self._get_from_cache(cache_key)
        if cached_price is not None:
            return cached_price

        price = None

        # 1. Stablecoins: hardcoded $1.00 (no API call needed)
        if symbol in self.stablecoin_prices:
            price = self.stablecoin_prices[symbol]

        # 2. Binance (free, no key, covers major tokens)
        if price is None and symbol in self.binance_symbols:
            price = self._get_price_from_binance(symbol)

        # 3. Jupiter for Solana tokens (mint-address based)
        if price is None and (chain == "solana" or symbol in self.solana_mints):
            price = self._get_price_from_jupiter(symbol)

        # 4. CoinGecko as fallback (rate-limited on free tier)
        if price is None:
            price = self._get_price_from_coingecko(symbol)

        # 5. DefiLlama for chain-specific tokens
        if price is None and chain:
            price = self._get_price_from_defillama(symbol, chain)

        # Cache the result
        if price is not None:
            self._set_cache(cache_key, price)

        return price
    
    def get_prices(
        self,
        symbols: List[str],
        chain: Optional[str] = None
    ) -> Dict[str, Optional[float]]:
        """
        Get USD prices for multiple tokens at once.
        Priority: Cache → Stablecoins → Binance (batch) → Jupiter (Solana) → CoinGecko
        """
        results = {}

        if chain:
            chain = self._normalize_chain(chain)

        to_fetch_binance = []
        to_fetch_jupiter = []
        to_fetch_coingecko = []

        for symbol in symbols:
            symbol = symbol.upper()
            cache_key = f"{symbol}:{chain}" if chain else symbol

            cached = self._get_from_cache(cache_key)
            if cached is not None:
                results[symbol] = cached
                continue

            # Stablecoins: hardcoded
            if symbol in self.stablecoin_prices:
                results[symbol] = self.stablecoin_prices[symbol]
                self._set_cache(cache_key, self.stablecoin_prices[symbol])
                continue

            # Categorize by source
            if chain == "solana" or symbol in self.solana_mints:
                to_fetch_jupiter.append(symbol)
            elif symbol in self.binance_symbols:
                to_fetch_binance.append(symbol)
            else:
                to_fetch_coingecko.append(symbol)

        # Batch fetch from Binance
        if to_fetch_binance:
            binance_results = self._get_prices_batch_binance(to_fetch_binance)
            for symbol, price in binance_results.items():
                results[symbol] = price
                cache_key = f"{symbol}:{chain}" if chain else symbol
                if price is not None:
                    self._set_cache(cache_key, price)
                elif symbol not in results:
                    to_fetch_coingecko.append(symbol)  # fallback

        # Batch fetch from Jupiter (Solana)
        if to_fetch_jupiter:
            jupiter_results = self._get_prices_batch_jupiter(to_fetch_jupiter)
            for symbol, price in jupiter_results.items():
                results[symbol] = price
                cache_key = f"{symbol}:solana"
                if price is not None:
                    self._set_cache(cache_key, price)

        # CoinGecko only for unknowns
        if to_fetch_coingecko:
            coingecko_results = self._get_prices_batch_coingecko(to_fetch_coingecko)
            for symbol, price in coingecko_results.items():
                if symbol not in results or results[symbol] is None:
                    results[symbol] = price
                    cache_key = f"{symbol}:{chain}" if chain else symbol
                    if price is not None:
                        self._set_cache(cache_key, price)

        return results
    
    # ============================================================
    # CoinGecko Methods
    # ============================================================
    
    def _is_coingecko_cooled_down(self) -> bool:
        """Check if CoinGecko is in rate-limit cooldown."""
        if time.time() < self._coingecko_cooldown_until:
            return True
        return False

    def _trigger_coingecko_cooldown(self):
        """Activate cooldown after a 429 response."""
        self._coingecko_cooldown_until = time.time() + self._coingecko_cooldown_seconds
        print(f"[PRICE] CoinGecko rate limited - cooling down for {self._coingecko_cooldown_seconds}s")

    def _get_price_from_coingecko(self, symbol: str) -> Optional[float]:
        """Get price from CoinGecko API."""
        if self._is_coingecko_cooled_down():
            return None

        coin_id = self.coingecko_ids.get(symbol)
        if not coin_id:
            return None

        try:
            url = f"{self.coingecko_base_url}/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params, headers=self._coingecko_headers)
                response.raise_for_status()

                data = response.json()
                if coin_id in data and "usd" in data[coin_id]:
                    price = float(data[coin_id]["usd"])
                    return price

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self._trigger_coingecko_cooldown()
            else:
                print(f"[PRICE] CoinGecko error for {symbol}: {e}")
        except Exception as e:
            print(f"[PRICE] CoinGecko error for {symbol}: {e}")

        return None
    
    def _get_prices_batch_coingecko(
        self,
        symbols: List[str]
    ) -> Dict[str, Optional[float]]:
        """Get multiple prices from CoinGecko at once."""
        results = {}

        if self._is_coingecko_cooled_down():
            for symbol in symbols:
                results[symbol] = None
            return results

        # Map symbols to CoinGecko IDs
        coin_ids = []
        id_to_symbol = {}

        for symbol in symbols:
            coin_id = self.coingecko_ids.get(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                id_to_symbol[coin_id] = symbol
            else:
                results[symbol] = None

        if not coin_ids:
            return results

        try:
            url = f"{self.coingecko_base_url}/simple/price"
            params = {"ids": ",".join(coin_ids), "vs_currencies": "usd"}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=params, headers=self._coingecko_headers)
                response.raise_for_status()

                data = response.json()

                for coin_id, symbol in id_to_symbol.items():
                    if coin_id in data and "usd" in data[coin_id]:
                        results[symbol] = float(data[coin_id]["usd"])
                    else:
                        results[symbol] = None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self._trigger_coingecko_cooldown()
            else:
                print(f"[PRICE] CoinGecko batch error: {e}")
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None
        except Exception as e:
            print(f"[PRICE] CoinGecko batch error: {e}")
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None

        return results

    def get_prices_with_changes(
        self,
        symbols: List[str]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Get current prices AND 24h percentage change for multiple tokens.
        Uses CoinGecko /simple/price with include_24hr_change=true.

        Returns:
            Dict mapping symbol -> {"price": float|None, "change_24h": float|None}
        """
        results: Dict[str, Dict[str, Optional[float]]] = {
            s.upper(): {"price": None, "change_24h": None} for s in symbols
        }

        if self._is_coingecko_cooled_down():
            return results

        # Map symbols to CoinGecko IDs (only symbols we know about)
        coin_ids = []
        id_to_symbol: Dict[str, str] = {}
        for symbol in symbols:
            sym_upper = symbol.upper()
            coin_id = self.coingecko_ids.get(sym_upper)
            if coin_id:
                coin_ids.append(coin_id)
                id_to_symbol[coin_id] = sym_upper

        if not coin_ids:
            return results

        try:
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            }

            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=params, headers=self._coingecko_headers)
                response.raise_for_status()

                data = response.json()
                for coin_id, sym in id_to_symbol.items():
                    entry = data.get(coin_id, {})
                    results[sym]["price"] = float(entry["usd"]) if "usd" in entry else None
                    results[sym]["change_24h"] = float(entry["usd_24h_change"]) if "usd_24h_change" in entry else None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self._trigger_coingecko_cooldown()
            else:
                print(f"[PRICE] CoinGecko prices_with_changes error: {e}")
        except Exception as e:
            print(f"[PRICE] prices_with_changes error: {e}")

        return results

    # ============================================================
    # Binance Methods (free, no API key, 1200 req/min)
    # ============================================================

    def _get_price_from_binance(self, symbol: str) -> Optional[float]:
        """Get price from Binance ticker API. Free, no key required."""
        pair = self.binance_symbols.get(symbol)
        if not pair:
            return None
        try:
            url = f"{self.binance_base_url}/ticker/price"
            with httpx.Client(timeout=8.0) as client:
                response = client.get(url, params={"symbol": pair})
                if response.status_code == 200:
                    data = response.json()
                    return float(data["price"])
        except Exception as e:
            logger.debug(f"[PRICE] Binance error for {symbol}: {e}")
        return None

    def _get_prices_batch_binance(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Batch-fetch prices from Binance (single API call for all symbols)."""
        results: Dict[str, Optional[float]] = {s: None for s in symbols}

        # Build pair → symbol reverse map
        pair_to_symbol: Dict[str, str] = {}
        for symbol in symbols:
            pair = self.binance_symbols.get(symbol)
            if pair:
                pair_to_symbol[pair] = symbol

        if not pair_to_symbol:
            return results

        try:
            url = f"{self.binance_base_url}/ticker/price"
            with httpx.Client(timeout=10.0) as client:
                # Fetch all at once — Binance returns all pairs in one call
                response = client.get(url)
                if response.status_code == 200:
                    all_prices = response.json()  # list of {symbol, price}
                    price_map = {item["symbol"]: float(item["price"]) for item in all_prices}
                    for pair, symbol in pair_to_symbol.items():
                        if pair in price_map:
                            results[symbol] = price_map[pair]
        except Exception as e:
            logger.debug(f"[PRICE] Binance batch error: {e}")
            # Fallback: individual requests
            for symbol in symbols:
                if results[symbol] is None:
                    results[symbol] = self._get_price_from_binance(symbol)

        return results

    async def _get_price_from_binance_async(self, symbol: str) -> Optional[float]:
        """Async: Get price from Binance ticker API."""
        pair = self.binance_symbols.get(symbol)
        if not pair:
            return None
        try:
            url = f"{self.binance_base_url}/ticker/price"
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params={"symbol": pair})
                if response.status_code == 200:
                    data = response.json()
                    return float(data["price"])
        except Exception as e:
            logger.debug(f"[PRICE] Binance async error for {symbol}: {e}")
        return None

    async def _get_prices_batch_binance_async(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Async batch-fetch prices from Binance."""
        results: Dict[str, Optional[float]] = {s: None for s in symbols}

        pair_to_symbol: Dict[str, str] = {}
        for symbol in symbols:
            pair = self.binance_symbols.get(symbol)
            if pair:
                pair_to_symbol[pair] = symbol

        if not pair_to_symbol:
            return results

        try:
            url = f"{self.binance_base_url}/ticker/price"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    all_prices = response.json()
                    price_map = {item["symbol"]: float(item["price"]) for item in all_prices}
                    for pair, symbol in pair_to_symbol.items():
                        if pair in price_map:
                            results[symbol] = price_map[pair]
        except Exception as e:
            logger.debug(f"[PRICE] Binance async batch error: {e}")

        return results

    # ============================================================
    # Jupiter Methods (Solana) - Using Jupiter v2 API
    # ============================================================

    def _get_price_from_jupiter(self, symbol: str) -> Optional[float]:
        """Get price from Jupiter Price API v2 (Solana)."""
        mint = self.solana_mints.get(symbol)
        if not mint:
            return None

        try:
            url = self.jupiter_base_url
            params = {"ids": mint}

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                if "data" in data and mint in data["data"]:
                    price_str = data["data"][mint].get("price")
                    if price_str:
                        price = float(price_str)
                        return price

        except Exception as e:
            print(f"[PRICE] Jupiter error for {symbol}: {e}")

        return None

    def _get_prices_batch_jupiter(
        self,
        symbols: List[str]
    ) -> Dict[str, Optional[float]]:
        """Get multiple prices from Jupiter v2 at once."""
        results = {}

        # Map symbols to mint addresses
        mints = []
        mint_to_symbol = {}

        for symbol in symbols:
            mint = self.solana_mints.get(symbol)
            if mint:
                mints.append(mint)
                mint_to_symbol[mint] = symbol
            else:
                # Fallback to CoinGecko
                results[symbol] = self._get_price_from_coingecko(symbol)

        if not mints:
            return results

        try:
            url = self.jupiter_base_url
            params = {"ids": ",".join(mints)}

            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                if "data" in data:
                    for mint, symbol in mint_to_symbol.items():
                        if mint in data["data"] and data["data"][mint].get("price"):
                            results[symbol] = float(data["data"][mint]["price"])
                        else:
                            results[symbol] = None

        except Exception as e:
            print(f"[PRICE] Jupiter batch error: {e}")
            print(f"[PRICE] Falling back to CoinGecko for {len(mint_to_symbol)} Solana tokens")
            for mint, symbol in mint_to_symbol.items():
                if symbol not in results:
                    results[symbol] = self._get_price_from_coingecko(symbol)

        return results

    # ============================================================
    # DefiLlama Methods (Chain-specific)
    # ============================================================
    
    def _get_price_from_defillama(
        self, 
        symbol: str, 
        chain: str
    ) -> Optional[float]:
        """
        Get price from DefiLlama API.
        
        DefiLlama uses format: {chain}:{address}
        """
        # Find token address for this chain
        chain_tokens = self.chain_tokens.get(chain, {})
        token_address = None
        
        for addr, sym in chain_tokens.items():
            if sym == symbol:
                token_address = addr
                break
        
        if not token_address:
            return None
        
        try:
            # DefiLlama format: chain:address
            token_id = f"{chain}:{token_address}"
            url = f"{self.defillama_base_url}/prices/current/{token_id}"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                
                data = response.json()
                coins = data.get("coins", {})
                
                if token_id in coins:
                    price = float(coins[token_id].get("price", 0))
                    print(f"[PRICE] DefiLlama {symbol} on {chain}: ${price}")
                    return price
                    
        except Exception as e:
            print(f"[PRICE] DefiLlama error for {symbol}: {e}")
        
        return None
    
    # ============================================================
    # Cache Methods (uses shared CacheService if available)
    # ============================================================

    def _get_from_cache(self, key: str) -> Optional[float]:
        """Get price from cache if not expired."""
        prefixed = f"prices:{key}"

        # Try shared cache first
        try:
            from app.services.cache import cache as shared_cache
            val = shared_cache.get(prefixed)
            if val is not None:
                return val
        except Exception:
            pass

        # Fallback to local cache
        if key in self._cache:
            price, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return price
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, price: float):
        """Set price in both shared and local cache."""
        prefixed = f"prices:{key}"

        # Write to shared cache
        try:
            from app.services.cache import cache as shared_cache
            shared_cache.set(prefixed, price, self.ttl_seconds)
        except Exception:
            pass

        # Also write to local cache
        self._cache[key] = (price, time.time())

    def clear_cache(self):
        """Clear all cached prices."""
        self._cache.clear()
        try:
            from app.services.cache import cache as shared_cache
            shared_cache.clear_prices()
        except Exception:
            pass
    
    # ============================================================
    # Utility Methods
    # ============================================================
    
    def _normalize_chain(self, chain: str) -> str:
        """Normalize chain name (testnet -> mainnet for pricing)."""
        chain = chain.lower()

        # Map testnets to mainnets (same prices)
        testnet_map = {
            "ethereum_sepolia": "ethereum",
            "polygon_amoy": "polygon",
            "polygon_mumbai": "polygon",
            "base_sepolia": "base",
            "aptos_testnet": "aptos",
            "solana_devnet": "solana",
            "evm": "ethereum",  # Generic "evm" treated as ethereum for pricing
        }

        return testnet_map.get(chain, chain)
    
    def add_coingecko_mapping(self, symbol: str, coingecko_id: str):
        """Add custom CoinGecko ID mapping."""
        self.coingecko_ids[symbol.upper()] = coingecko_id
    
    def add_solana_mint(self, symbol: str, mint_address: str):
        """Add custom Solana token mint mapping."""
        self.solana_mints[symbol.upper()] = mint_address

    # ============================================================
    # Async Price Fetching Methods
    # ============================================================

    async def get_price_async(
        self,
        symbol: str,
        chain: Optional[str] = None
    ) -> Optional[float]:
        """
        Async: Get USD price. Priority: Cache → Stablecoin → Binance → Jupiter → CoinGecko → DefiLlama
        """
        symbol = symbol.upper()

        if chain:
            chain = self._normalize_chain(chain)

        cache_key = f"{symbol}:{chain}" if chain else symbol
        cached_price = self._get_from_cache(cache_key)
        if cached_price is not None:
            return cached_price

        price = None

        # 1. Stablecoins hardcoded
        if symbol in self.stablecoin_prices:
            price = self.stablecoin_prices[symbol]

        # 2. Binance (free)
        if price is None and symbol in self.binance_symbols:
            price = await self._get_price_from_binance_async(symbol)

        # 3. Jupiter for Solana
        if price is None and (chain == "solana" or symbol in self.solana_mints):
            price = await self._get_price_from_jupiter_async(symbol)

        # 4. CoinGecko fallback
        if price is None:
            price = await self._get_price_from_coingecko_async(symbol)

        # 5. DefiLlama chain-specific
        if price is None and chain:
            price = await self._get_price_from_defillama_async(symbol, chain)

        if price is not None:
            self._set_cache(cache_key, price)

        return price

    async def get_prices_async(
        self,
        symbols: List[str],
        chain: Optional[str] = None
    ) -> Dict[str, Optional[float]]:
        """
        Async batch prices. Priority: Cache → Stablecoins → Binance → Jupiter → CoinGecko
        Runs Binance + Jupiter + CoinGecko in parallel for max speed.
        """
        results = {}

        if chain:
            chain = self._normalize_chain(chain)

        to_fetch_binance = []
        to_fetch_jupiter = []
        to_fetch_coingecko = []

        for symbol in symbols:
            symbol = symbol.upper()
            cache_key = f"{symbol}:{chain}" if chain else symbol

            cached = self._get_from_cache(cache_key)
            if cached is not None:
                results[symbol] = cached
                continue

            # Stablecoins hardcoded
            if symbol in self.stablecoin_prices:
                results[symbol] = self.stablecoin_prices[symbol]
                self._set_cache(cache_key, self.stablecoin_prices[symbol])
                continue

            if chain == "solana" or symbol in self.solana_mints:
                to_fetch_jupiter.append(symbol)
            elif symbol in self.binance_symbols:
                to_fetch_binance.append(symbol)
            else:
                to_fetch_coingecko.append(symbol)

        # Run all three sources in parallel
        tasks = []
        task_labels = []
        if to_fetch_binance:
            tasks.append(self._get_prices_batch_binance_async(to_fetch_binance))
            task_labels.append("binance")
        if to_fetch_jupiter:
            tasks.append(self._get_prices_batch_jupiter_async(to_fetch_jupiter))
            task_labels.append("jupiter")
        if to_fetch_coingecko:
            tasks.append(self._get_prices_batch_coingecko_async(to_fetch_coingecko))
            task_labels.append("coingecko")

        if tasks:
            batch_results = await asyncio.gather(*tasks)

            for label, batch in zip(task_labels, batch_results):
                for symbol, price in batch.items():
                    if symbol not in results or results[symbol] is None:
                        results[symbol] = price
                    cache_key = f"{symbol}:{chain}" if chain else symbol
                    if price is not None:
                        self._set_cache(cache_key, price)
                    elif label == "binance" and symbol not in results:
                        # Binance failed for this symbol → try CoinGecko
                        if symbol not in to_fetch_coingecko:
                            to_fetch_coingecko.append(symbol)

        return results

    # ============================================================
    # Async CoinGecko Methods
    # ============================================================

    async def _get_price_from_coingecko_async(self, symbol: str) -> Optional[float]:
        """Async: Get price from CoinGecko API."""
        if self._is_coingecko_cooled_down():
            return None

        coin_id = self.coingecko_ids.get(symbol)
        if not coin_id:
            return None

        try:
            url = f"{self.coingecko_base_url}/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=self._coingecko_headers)
                response.raise_for_status()

                data = response.json()
                if coin_id in data and "usd" in data[coin_id]:
                    price = float(data[coin_id]["usd"])
                    return price

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self._trigger_coingecko_cooldown()
            else:
                print(f"[PRICE] CoinGecko error for {symbol}: {e}")
        except Exception as e:
            print(f"[PRICE] CoinGecko error for {symbol}: {e}")

        return None

    async def _get_prices_batch_coingecko_async(
        self,
        symbols: List[str]
    ) -> Dict[str, Optional[float]]:
        """Async: Get multiple prices from CoinGecko at once."""
        results = {}

        if self._is_coingecko_cooled_down():
            for symbol in symbols:
                results[symbol] = None
            return results

        # Map symbols to CoinGecko IDs
        coin_ids = []
        id_to_symbol = {}

        for symbol in symbols:
            coin_id = self.coingecko_ids.get(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                id_to_symbol[coin_id] = symbol
            else:
                results[symbol] = None

        if not coin_ids:
            return results

        try:
            url = f"{self.coingecko_base_url}/simple/price"
            params = {"ids": ",".join(coin_ids), "vs_currencies": "usd"}

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers=self._coingecko_headers)
                response.raise_for_status()

                data = response.json()

                for coin_id, symbol in id_to_symbol.items():
                    if coin_id in data and "usd" in data[coin_id]:
                        results[symbol] = float(data[coin_id]["usd"])
                    else:
                        results[symbol] = None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self._trigger_coingecko_cooldown()
            else:
                print(f"[PRICE] CoinGecko batch error: {e}")
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None
        except Exception as e:
            print(f"[PRICE] CoinGecko batch error: {e}")
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None

        return results

    # ============================================================
    # Async Jupiter Methods (Solana) - Using Jupiter v2 API
    # ============================================================

    async def _get_price_from_jupiter_async(self, symbol: str) -> Optional[float]:
        """Async: Get price from Jupiter Price API v2 (Solana)."""
        mint = self.solana_mints.get(symbol)
        if not mint:
            return None

        try:
            url = self.jupiter_base_url
            params = {"ids": mint}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                if "data" in data and mint in data["data"]:
                    price_str = data["data"][mint].get("price")
                    if price_str:
                        price = float(price_str)
                        return price

        except Exception as e:
            print(f"[PRICE] Jupiter error for {symbol}: {e}")

        return None

    async def _get_prices_batch_jupiter_async(
        self,
        symbols: List[str]
    ) -> Dict[str, Optional[float]]:
        """Async: Get multiple prices from Jupiter v2 at once."""
        results = {}

        # Map symbols to mint addresses
        mints = []
        mint_to_symbol = {}

        for symbol in symbols:
            mint = self.solana_mints.get(symbol)
            if mint:
                mints.append(mint)
                mint_to_symbol[mint] = symbol
            else:
                # Fallback to CoinGecko
                results[symbol] = await self._get_price_from_coingecko_async(symbol)

        if not mints:
            return results

        try:
            url = self.jupiter_base_url
            params = {"ids": ",".join(mints)}

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                if "data" in data:
                    for mint, symbol in mint_to_symbol.items():
                        if mint in data["data"] and data["data"][mint].get("price"):
                            results[symbol] = float(data["data"][mint]["price"])
                        else:
                            results[symbol] = None

        except Exception as e:
            print(f"[PRICE] Jupiter batch error: {e}")
            print(f"[PRICE] Falling back to CoinGecko for {len(mint_to_symbol)} Solana tokens")
            for mint, symbol in mint_to_symbol.items():
                if symbol not in results:
                    results[symbol] = await self._get_price_from_coingecko_async(symbol)

        return results

    # ============================================================
    # Async DefiLlama Methods
    # ============================================================

    async def _get_price_from_defillama_async(
        self,
        symbol: str,
        chain: str
    ) -> Optional[float]:
        """
        Async: Get price from DefiLlama API.

        DefiLlama uses format: {chain}:{address}
        """
        # Find token address for this chain
        chain_tokens = self.chain_tokens.get(chain, {})
        token_address = None

        for addr, sym in chain_tokens.items():
            if sym == symbol:
                token_address = addr
                break

        if not token_address:
            return None

        try:
            # DefiLlama format: chain:address
            token_id = f"{chain}:{token_address}"
            url = f"{self.defillama_base_url}/prices/current/{token_id}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                coins = data.get("coins", {})

                if token_id in coins:
                    price = float(coins[token_id].get("price", 0))
                    print(f"[PRICE] DefiLlama {symbol} on {chain}: ${price}")
                    return price

        except Exception as e:
            print(f"[PRICE] DefiLlama error for {symbol}: {e}")

        return None

    async def get_prices_with_changes_async(
        self,
        symbols: List[str]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Async wrapper around get_prices_with_changes().
        Returns: {symbol: {"price": float|None, "change_24h": float|None}}
        Runs the sync CoinGecko call in a thread to avoid blocking the event loop.
        """
        import asyncio
        return await asyncio.to_thread(self.get_prices_with_changes, symbols)


# ============================================================
# Singleton Instance
# ============================================================
# NOTE: The primary price_service instance is created in app/deps.py
# with proper config (TTL from settings, CoinGecko API key).
# This factory is only used if someone imports directly from this module.

_price_service: Optional[PriceService] = None

def get_price_service() -> PriceService:
    """Get or create price service singleton."""
    global _price_service
    if _price_service is None:
        try:
            from app.config import settings
            _price_service = PriceService(
                ttl_seconds=settings.prices_ttl_seconds,
                coingecko_api_key=settings.coingecko_api_key,
            )
        except Exception:
            _price_service = PriceService()
    return _price_service