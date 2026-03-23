# app/routers/balances.py
"""
Balances Router - Optimized with:
- Batch price fetching
- Async price fetching
- Async balance fetching via thread pool
"""
from fastapi import APIRouter, HTTPException, Path, Query
from decimal import Decimal, getcontext
from typing import List, Dict, Set
import logging
import asyncio

from ..models.dto import TokenBalance
from ..services.cache import cache
from ..services.adapters import get_adapter_for_chain
from ..deps import price_service
from ..config import settings
from ..schemas.wallet import detect_address_type, get_chains_for_address, AddressType

logger = logging.getLogger("chainlens.routers.balances")

router = APIRouter()


def _normalize_amount(raw: str, decimals: int) -> Decimal:
    """Convert raw amount string to decimal with proper precision"""
    getcontext().prec = 50
    return Decimal(raw) / (Decimal(10) ** decimals)


@router.get("/wallets/{address}/balances", response_model=List[TokenBalance])
async def get_balances(
    address: str = Path(..., min_length=3, max_length=200),
    chain: str = Query("aptos", description="Blockchain: aptos, solana, ethereum, etc."),
    testnet: bool = Query(True, description="Use testnet (True) or mainnet (False)")
):
    """
    Get token balances for a wallet with USD prices.

    Optimized with:
    - Batch price fetching
    - Async price fetching
    - Async balance fetching via thread pool

    Supports multiple chains!
    """
    network = "testnet" if testnet else "mainnet"

    try:
        # Get the appropriate adapter for this chain
        adapter = get_adapter_for_chain(chain, network=network)
        normalized_addr = adapter.normalize_address(address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check cache (include chain + network in cache key)
    cache_key = f"balances:{chain}:{network}:{normalized_addr}"
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Returning cached balances for {normalized_addr} on {chain}")
        return cached

    balances: List[TokenBalance] = []

    try:
        # ============================================================
        # PHASE 1: Fetch all raw balances (ASYNC via thread pool)
        # ============================================================
        raw_balances = await asyncio.to_thread(
            adapter.get_token_balances, normalized_addr
        )

        if not raw_balances:
            return balances

        # ============================================================
        # PHASE 2: Collect unique symbols and batch fetch prices (ASYNC!)
        # ============================================================
        symbols_to_fetch: Set[str] = set()

        for bal in raw_balances:
            symbol = bal.get("symbol")
            if symbol and bal.get("amount", 0) > 0:
                symbols_to_fetch.add(symbol)

        # Batch fetch prices + 24h changes in parallel (ASYNC!)
        prices: Dict[str, float] = {}
        changes_data: Dict[str, Dict] = {}
        if symbols_to_fetch:
            syms_list = list(symbols_to_fetch)
            logger.info(f"Batch fetching prices+changes for {len(syms_list)} tokens")
            prices, changes_data = await asyncio.gather(
                price_service.get_prices_async(syms_list, chain=chain),
                price_service.get_prices_with_changes_async(syms_list),
            )

        # ============================================================
        # PHASE 3: Build response with prices + 24h change
        # ============================================================
        for bal in raw_balances:
            symbol = bal.get("symbol")
            amount_float = bal.get("amount", 0)
            decimals = bal.get("decimals", 0)
            raw_str = bal.get("raw", "0")
            token_address = bal.get("address", "")

            amount = Decimal(str(amount_float))
            # Best price from Binance / Jupiter / CoinGecko fallback chain
            usd_price = prices.get(symbol) if symbol else None
            # 24h % change from CoinGecko (None if symbol not indexed)
            change_24h = changes_data.get(symbol, {}).get("change_24h") if symbol else None
            usd_value = None

            if usd_price and amount_float > 0:
                usd_value = float(amount) * usd_price

            balances.append(
                TokenBalance(
                    symbol=symbol,
                    address=token_address,
                    decimals=decimals,
                    raw=raw_str,
                    amount=amount,
                    usd_price=usd_price,
                    usd_value=usd_value,
                    change_24h=change_24h,
                )
            )

    except Exception as e:
        logger.error(f"Failed to fetch balances for {chain}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch balances: {str(e)}"
        )

    # Cache and return
    cache.set(cache_key, balances, int(settings.balances_ttl_seconds))
    return balances


@router.get("/wallets/{address}/multi-chain-balances")
async def get_multi_chain_balances(
    address: str = Path(..., min_length=3, max_length=200),
    testnet: bool = Query(True, description="Use testnet chains (default: True)")
):
    """
    Get token balances across all applicable chains for a wallet address.

    Auto-detects address type:
    - EVM addresses (0x + 40 hex): Queries all EVM chains
    - Solana addresses (Base58): Queries Solana only
    - Aptos addresses (0x + 64 hex): Queries Aptos only

    Returns balances grouped by chain with USD values.
    """
    try:
        addr_type = detect_address_type(address)
        chains = get_chains_for_address(address, testnet=testnet)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not chains:
        raise HTTPException(
            status_code=400,
            detail=f"Could not determine chains for address: {address}"
        )

    # Check cache
    cache_key = f"multi_balances:{addr_type.value}:{testnet}:{address}"
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Returning cached multi-chain balances for {address}")
        return cached

    result = {
        "wallet_address": address,
        "address_type": addr_type.value,
        "chains_queried": chains,
        "balances_by_chain": {},
        "all_balances": [],
        "total_usd_value": 0.0,
        "total_token_count": 0,
        "chain_totals": {}
    }

    async def fetch_chain_balances(chain: str):
        """Fetch balances for a single chain."""
        try:
            adapter = get_adapter_for_chain(chain)
            normalized = adapter.normalize_address(address)

            raw_balances = await asyncio.to_thread(
                adapter.get_token_balances, normalized
            )

            if not raw_balances:
                return chain, [], 0.0

            # Fetch prices + 24h changes in parallel
            symbols = [b.get("symbol") for b in raw_balances if b.get("symbol")]
            if symbols:
                prices, changes_data = await asyncio.gather(
                    price_service.get_prices_async(symbols, chain=chain),
                    price_service.get_prices_with_changes_async(symbols),
                )
            else:
                prices, changes_data = {}, {}

            chain_total = 0.0
            processed = []

            for bal in raw_balances:
                symbol = bal.get("symbol", "UNKNOWN")
                amount = bal.get("amount", 0)
                price = prices.get(symbol)
                change_24h = changes_data.get(symbol, {}).get("change_24h")

                entry = {
                    "symbol": symbol,
                    "address": bal.get("address", ""),
                    "decimals": bal.get("decimals", 0),
                    "raw": bal.get("raw", "0"),
                    "amount": amount,
                    "usd_price": price,
                    "usd_value": None,
                    "change_24h": change_24h,
                    "chain": chain,
                }

                if price and amount > 0:
                    usd_value = amount * price
                    entry["usd_value"] = usd_value
                    chain_total += usd_value

                processed.append(entry)

            return chain, processed, chain_total

        except Exception as e:
            logger.error(f"Error fetching balances from {chain}: {e}")
            return chain, [], 0.0

    # Fetch all chains in parallel
    tasks = [fetch_chain_balances(chain) for chain in chains]
    results = await asyncio.gather(*tasks)

    for chain, balances, chain_total in results:
        result["balances_by_chain"][chain] = balances
        result["all_balances"].extend(balances)
        result["chain_totals"][chain] = round(chain_total, 2)
        result["total_usd_value"] += chain_total
        result["total_token_count"] += len(balances)

    result["total_usd_value"] = round(result["total_usd_value"], 2)

    # Cache result
    cache.set(cache_key, result, int(settings.balances_ttl_seconds))

    return result
