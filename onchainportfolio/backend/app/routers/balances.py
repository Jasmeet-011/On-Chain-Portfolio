from fastapi import APIRouter, HTTPException, Path
from decimal import Decimal, getcontext
from typing import List

from ..models.dto import TokenBalance
from ..services.cache import cache
from ..deps import aptos_client, price_service  # ← Add price_service
from ..config import settings

router = APIRouter()

APT_ASSET_TYPE = "0x1::aptos_coin::AptosCoin"

TOKEN_REGISTRY = {
    APT_ASSET_TYPE: ("APT", 8),
    # Add more tokens:
    # "0x...::usdc::USDC": ("USDC", 6),
}


def _normalize_amount(raw: str, decimals: int) -> Decimal:
    """Convert raw amount string to decimal with proper precision"""
    getcontext().prec = 50
    return Decimal(raw) / (Decimal(10) ** decimals)


@router.get("/wallets/{address}/balances", response_model=List[TokenBalance])
def get_balances(address: str = Path(..., min_length=3, max_length=200)):
    """
    Get token balances for a wallet with USD prices.
    """
    addr = address.lower()
    if not addr.startswith("0x"):
        addr = "0x" + addr

    # Check cache
    cache_key = f"balances:{addr}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    balances: List[TokenBalance] = []

    # Query each token in the registry
    for asset_type, (symbol, decimals) in TOKEN_REGISTRY.items():
        try:
            balance_raw = aptos_client.get_account_balance(addr, asset_type)
            
            if balance_raw is None or balance_raw == 0:
                continue
            
            amount = _normalize_amount(str(balance_raw), decimals)
            
            # Fetch USD price
            usd_price = None
            usd_value = None
            try:
                usd_price = price_service.get_price(symbol)
                if usd_price:
                    usd_value = float(amount) * usd_price
            except Exception as e:
                print(f"[WARNING] Could not fetch price for {symbol}: {e}")
            
            balances.append(
                TokenBalance(
                    symbol=symbol,
                    address=asset_type,
                    decimals=decimals,
                    raw=str(balance_raw),
                    amount=amount,
                    usd_price=usd_price,
                    usd_value=usd_value
                )
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch balance for {symbol}: {e}")
            continue

    # Cache and return
    cache.set(cache_key, balances, int(settings.balances_ttl_seconds))
    return balances