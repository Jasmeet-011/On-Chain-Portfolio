# app/routers/portfolio.py - COMPLETE MULTI-CHAIN VERSION
"""
Portfolio Router - Optimized with:
- Batch price fetching
- Async price fetching
- Async balance fetching via thread pool
"""
from fastapi import APIRouter, Path, HTTPException
from typing import Dict, Any, List, Set
import logging
import asyncio

from app.services.adapters import get_adapter_for_chain, SUPPORTED_CHAINS
from app.services.cache import cache
from app.config import settings
from app.deps import price_service

logger = logging.getLogger("chainlens.routers.portfolio")

router = APIRouter()


@router.get("/wallets/{chain}/{address}/portfolio")
async def get_portfolio(
    chain: str = Path(..., description="Blockchain network (e.g., ethereum_sepolia, aptos)"),
    address: str = Path(..., min_length=3, max_length=200, description="Wallet address")
) -> Dict[str, Any]:
    """
    Get complete portfolio for a wallet on any supported chain.

    Optimized: Uses batch price fetching instead of individual calls.

    **Supported Chains:**
    - `ethereum_sepolia` - Ethereum Sepolia testnet
    - `ethereum` - Ethereum mainnet
    - `polygon_amoy` - Polygon Amoy testnet
    - `polygon` - Polygon mainnet
    - `base_sepolia` - Base Sepolia testnet
    - `base` - Base mainnet
    - `aptos` - Aptos (testnet)
    - `solana` - Solana (devnet)

    **Returns:**
    - Chain-specific portfolio with USD values
    - Native token balance
    - All token balances
    - Total USD value
    """
    try:
        logger.info(f"Fetching portfolio for {address[:10]}... on {chain}")

        # Validate chain is supported
        if chain not in SUPPORTED_CHAINS:
            available_chains = list(SUPPORTED_CHAINS.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported chain: {chain}. Available: {available_chains}"
            )

        # Get adapter for this chain
        adapter = get_adapter_for_chain(chain)

        # Get portfolio data from adapter (run in thread pool for non-blocking)
        portfolio = await asyncio.to_thread(adapter.get_portfolio, address)

        # ============================================================
        # PHASE 1: Collect all symbols for batch price fetch
        # ============================================================
        balances = portfolio.get("balances", [])
        native_balance = portfolio.get("native_balance")

        # Collect all unique symbols
        symbols_to_fetch: Set[str] = set()

        for balance in balances:
            symbol = balance.get("symbol")
            if symbol and balance.get("amount", 0) > 0:
                symbols_to_fetch.add(symbol)

        # Include native token symbol
        if native_balance:
            native_symbol = native_balance.get("symbol")
            if native_symbol and native_balance.get("amount", 0) > 0:
                symbols_to_fetch.add(native_symbol)

        # ============================================================
        # PHASE 2: Batch fetch all prices at once (ASYNC!)
        # ============================================================
        prices: Dict[str, float] = {}
        if symbols_to_fetch:
            logger.info(f"Batch fetching prices for {len(symbols_to_fetch)} tokens")
            prices = await price_service.get_prices_async(list(symbols_to_fetch))

        # ============================================================
        # PHASE 3: Enrich balances with cached prices
        # ============================================================
        total_usd_value = 0.0
        enriched_balances: List[Dict[str, Any]] = []

        # Track which symbols are in balances to avoid double-counting native token
        symbols_in_balances: Set[str] = set()

        for balance in balances:
            symbol = balance.get("symbol")
            amount = balance.get("amount", 0)

            if symbol:
                symbols_in_balances.add(symbol)

            usd_price = prices.get(symbol) if symbol else None
            usd_value = 0.0

            if usd_price and amount > 0:
                usd_value = float(amount) * float(usd_price)
                total_usd_value += usd_value

            # Add USD fields to balance
            enriched_balance = {
                **balance,
                "usd_price": usd_price,
                "usd_value": usd_value
            }
            enriched_balances.append(enriched_balance)

        # Enrich native balance with USD price
        # Only add to total if NOT already counted in balances (avoid double-counting)
        if native_balance:
            native_symbol = native_balance.get("symbol")
            native_amount = native_balance.get("amount", 0)

            usd_price = prices.get(native_symbol) if native_symbol else None

            if usd_price and native_amount > 0:
                usd_value = float(native_amount) * float(usd_price)
                native_balance["usd_price"] = usd_price
                native_balance["usd_value"] = usd_value

                # Only add to total if native token wasn't already in balances
                if native_symbol not in symbols_in_balances:
                    total_usd_value += usd_value

        # Build response
        result = {
            "chain": chain,
            "address": portfolio.get("address", address),
            "balances": enriched_balances,
            "native_balance": native_balance,
            "total_usd_value": round(total_usd_value, 2),
            "token_count": len(enriched_balances)
        }

        logger.info(f"Found {len(enriched_balances)} tokens, total: ${total_usd_value:.2f}")
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch portfolio for {chain}: {str(e)}"
        )


# ============================================================
# Multi-Wallet Aggregated Portfolio
# ============================================================

from pydantic import BaseModel, Field

class WalletEntry(BaseModel):
    address: str = Field(..., min_length=3, max_length=200)
    chain: str = Field(..., description="Chain identifier (e.g., solana, evm, aptos)")

class MultiWalletRequest(BaseModel):
    wallets: List[WalletEntry] = Field(..., description="List of wallet address+chain pairs")
    testnet: bool = Field(default=True, description="Use testnet chains for EVM")


@router.post("/portfolio/multi-wallet")
async def get_multi_wallet_portfolio(
    request: MultiWalletRequest,
) -> Dict[str, Any]:
    """
    Get aggregated portfolio across multiple wallets and chains.

    Accepts a list of {address, chain} pairs and returns combined balances.
    For EVM wallets (chain="evm"), queries all EVM testnet/mainnet chains.

    Used by the Dashboard when a wallet group (e.g., Phantom with Solana + EVM) is selected,
    and by the Analytics page for combined portfolio across ALL wallet providers.
    """
    # EVM chains to query when chain is "evm"
    EVM_TESTNET_CHAINS = ["ethereum_sepolia", "polygon_amoy", "base_sepolia"]
    EVM_MAINNET_CHAINS = ["ethereum", "polygon", "base"]

    all_balances: List[Dict[str, Any]] = []
    by_wallet: Dict[str, Dict[str, Any]] = {}
    total_usd_value = 0.0
    symbols_to_fetch: Set[str] = set()

    # Phase 1: Expand EVM wallets and collect all fetch tasks
    fetch_tasks: List[Dict[str, str]] = []  # {address, chain}
    for wallet_entry in request.wallets:
        addr = wallet_entry.address
        chain = wallet_entry.chain

        if chain == "evm":
            # Expand to all EVM chains
            evm_chains = EVM_TESTNET_CHAINS if request.testnet else EVM_MAINNET_CHAINS
            for evm_chain in evm_chains:
                fetch_tasks.append({"address": addr, "chain": evm_chain, "source_chain": "evm"})
        elif chain in SUPPORTED_CHAINS:
            fetch_tasks.append({"address": addr, "chain": chain, "source_chain": chain})
        else:
            logger.warning(f"Skipping unsupported chain: {chain}")

    # Phase 2: Fetch balances from all chains in parallel (with caching)
    async def fetch_chain_balances(task: Dict[str, str]) -> List[Dict[str, Any]]:
        addr = task["address"]
        chain = task["chain"]
        try:
            # Check cache first
            cache_key = f"balances:{chain}:{addr}"
            cached = cache.get(cache_key)
            if cached is not None and isinstance(cached, list):
                logger.info(f"Cache hit for {chain}:{addr[:10]}...")
                balances = cached
            else:
                adapter = get_adapter_for_chain(chain)
                balances = await asyncio.to_thread(adapter.get_token_balances, addr)
                # Cache raw balances for reuse by history endpoint
                cache.set(cache_key, balances, settings.balances_ttl_seconds)

            # Tag each balance with chain and wallet address
            for bal in balances:
                bal["chain"] = chain
                bal["wallet_address"] = addr
            return balances
        except Exception as e:
            logger.warning(f"Failed to fetch from {chain} for {addr[:10]}...: {e}")
            return []

    # Run all fetches concurrently
    results = await asyncio.gather(
        *[fetch_chain_balances(task) for task in fetch_tasks],
        return_exceptions=True
    )

    # Phase 3: Collect all balances and symbols
    raw_balances: List[Dict[str, Any]] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Fetch task failed: {result}")
            continue
        for bal in result:
            raw_balances.append(bal)
            symbol = bal.get("symbol")
            if symbol and bal.get("amount", 0) > 0:
                symbols_to_fetch.add(symbol)

    # Phase 4: Batch fetch all prices
    prices: Dict[str, float] = {}
    if symbols_to_fetch:
        logger.info(f"Batch fetching prices for {len(symbols_to_fetch)} tokens")
        prices = await price_service.get_prices_async(list(symbols_to_fetch))

    # Phase 5: Enrich balances with prices and organize by wallet
    for bal in raw_balances:
        symbol = bal.get("symbol", "UNKNOWN")
        amount = bal.get("amount", 0)
        chain = bal.get("chain", "unknown")
        wallet_addr = bal.get("wallet_address", "")

        usd_price = prices.get(symbol)
        usd_value = 0.0
        if usd_price and amount > 0:
            usd_value = float(amount) * float(usd_price)
            total_usd_value += usd_value

        enriched = {
            **bal,
            "usd_price": usd_price,
            "usd_value": usd_value,
        }
        all_balances.append(enriched)

        # Group by wallet address
        if wallet_addr not in by_wallet:
            by_wallet[wallet_addr] = {
                "address": wallet_addr,
                "balances": [],
                "total_usd_value": 0.0,
            }
        by_wallet[wallet_addr]["balances"].append(enriched)
        by_wallet[wallet_addr]["total_usd_value"] += usd_value

    # Round totals
    for w in by_wallet.values():
        w["total_usd_value"] = round(w["total_usd_value"], 2)

    logger.info(
        f"Multi-wallet portfolio: {len(request.wallets)} wallets, "
        f"{len(all_balances)} tokens, total: ${total_usd_value:.2f}"
    )

    return {
        "wallets_queried": len(request.wallets),
        "chains_queried": list(set(t["chain"] for t in fetch_tasks)),
        "all_balances": all_balances,
        "by_wallet": by_wallet,
        "total_usd_value": round(total_usd_value, 2),
        "total_tokens": len(all_balances),
    }


# Legacy endpoint for backward compatibility
@router.get("/wallets/{address}/portfolio")
async def get_portfolio_legacy(
    address: str = Path(..., min_length=3, max_length=200),
) -> Dict[str, Any]:
    """
    DEPRECATED: Legacy portfolio endpoint.
    Use /wallets/{chain}/{address}/portfolio instead.

    Defaults to Aptos for backward compatibility.
    """
    return await get_portfolio(chain="aptos", address=address)
