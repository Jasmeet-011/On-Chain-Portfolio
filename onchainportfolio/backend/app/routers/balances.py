# app/routers/balances.py
from fastapi import APIRouter, HTTPException, Path, Query
from decimal import Decimal, getcontext
from typing import List, Dict, Any

from ..models.dto import TokenBalance
from ..services.cache import cache
from ..services.adapters import get_adapter_for_chain  # ← NEW: Use adapters
from ..deps import price_service
from ..config import settings

router = APIRouter()


def _normalize_amount(raw: str, decimals: int) -> Decimal:
    """Convert raw amount string to decimal with proper precision"""
    getcontext().prec = 50
    return Decimal(raw) / (Decimal(10) ** decimals)


@router.get("/wallets/{address}/balances", response_model=List[TokenBalance])
def get_balances(
    address: str = Path(..., min_length=3, max_length=200),
    chain: str = Query("aptos", description="Blockchain: aptos or solana")  # ← NEW
):
    """
    Get token balances for a wallet with USD prices.
    Now supports multiple chains!
    """
    
    try:
        # Get the appropriate adapter for this chain
        adapter = get_adapter_for_chain(chain)  # ← NEW
        normalized_addr = adapter.normalize_address(address)  # ← NEW
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check cache (include chain in cache key)
    cache_key = f"balances:{chain}:{normalized_addr}"  # ← UPDATED
    cached = cache.get(cache_key)
    if cached:
        print(f"[CACHE] Returning cached balances for {normalized_addr} on {chain}")
        return cached

    balances: List[TokenBalance] = []

    try:
        # Fetch balances using adapter (this returns list of dicts)
        raw_balances = adapter.get_token_balances(normalized_addr)  # ← NEW
        
        # Convert to TokenBalance objects and add USD prices
        for bal in raw_balances:
            symbol = bal.get("symbol")
            amount_float = bal.get("amount", 0)
            decimals = bal.get("decimals", 0)
            raw_str = bal.get("raw", "0")
            token_address = bal.get("address", "")
            
            # Convert amount to Decimal
            amount = Decimal(str(amount_float))
            
            # Fetch USD price
            usd_price = None
            usd_value = None
            try:
                usd_price = price_service.get_price(symbol, chain=chain)  # ← UPDATED: Pass chain
                if usd_price:
                    usd_value = float(amount) * usd_price
            except Exception as e:
                print(f"[WARNING] Could not fetch price for {symbol}: {e}")
            
            balances.append(
                TokenBalance(
                    symbol=symbol,
                    address=token_address,
                    decimals=decimals,
                    raw=raw_str,
                    amount=amount,
                    usd_price=usd_price,
                    usd_value=usd_value
                )
            )
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch balances for {chain}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch balances: {str(e)}"
        )

    # Cache and return
    cache.set(cache_key, balances, int(settings.balances_ttl_seconds))
    return balances