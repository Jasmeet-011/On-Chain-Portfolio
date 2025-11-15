from fastapi import APIRouter, HTTPException, Path
from decimal import Decimal, getcontext
from typing import List, Optional
from ..models.dto import TokenBalance
from ..services.cache import cache
from ..deps import aptos_client
from ..config import settings

router = APIRouter()

# Token registry (extend as needed)
# KEY MUST MATCH THE INNER TYPE WITHIN ANGLE BRACKETS OF CoinStore<...>
TOKEN_REGISTRY = {
    "0x1::aptos_coin::AptosCoin": ("APT", 8),
    # TODO: replace with the exact USDC type for your network when needed
    # "0x...::coin::T": ("USDC", 6),
}

def _normalize_amount(raw: str, decimals: int) -> Decimal:
    getcontext().prec = 50
    return Decimal(raw) / (Decimal(10) ** decimals)

def _derive_symbol_from_type(token_type: str) -> str:
    """
    Best-effort: take the last segment after '::'
    e.g., '0x1::aptos_coin::AptosCoin' -> 'AptosCoin' -> 'APTOSCOIN' -> 'APT' if matches known alias
    """
    last = token_type.split("::")[-1]
    sym = last.upper()
    # small alias map
    if last.lower() == "aptoscoin":
        return "APT"
    return sym[:10]  # cap length

def _extract_coinstore_token_type(full_type: str) -> Optional[str]:
    # full_type like "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>"
    start = full_type.find("<")
    end = full_type.rfind(">")
    if start == -1 or end == -1:
        return None
    return full_type[start+1:end]

@router.get("/wallets/{address}/balances", response_model=List[TokenBalance])
def get_balances(address: str = Path(..., min_length=3, max_length=200)):
    key = f"balances:{address}"
    cached = cache.get(key)
    if cached:
        return cached

    try:
        resources = aptos_client.get_account_coins(address)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Aptos upstream error: {e}")

    balances: list[TokenBalance] = []

    # Handle classic CoinStore (AIP-67)
    for res in resources:
        typ = res.get("type", "")
        if "CoinStore<" not in typ:
            continue

        token_type = _extract_coinstore_token_type(typ)
        if not token_type:
            continue

        # read raw amount
        data = res.get("data", {})
        raw = data.get("coin", {}).get("value", "0")

        # known tokens via registry
        if token_type in TOKEN_REGISTRY:
            symbol, decimals = TOKEN_REGISTRY[token_type]
            amount = _normalize_amount(raw, decimals)
            balances.append(TokenBalance(
                symbol=symbol,
                address=token_type,
                decimals=decimals,
                raw=raw,
                amount=amount
            ))
        else:
            # Fallback: do not drop unknown tokens; try a reasonable default
            # Most coins use 6–8 decimals; APT is 8. Use 8 as a safe default for now.
            decimals = 8
            symbol = _derive_symbol_from_type(token_type)
            amount = _normalize_amount(raw, decimals)
            balances.append(TokenBalance(
                symbol=symbol,
                address=token_type,
                decimals=decimals,
                raw=raw,
                amount=amount
            ))

    # (Optional) Handle newer 'FungibleStore' standard if you see it in /resources
    # NOTE: Schema can vary; adapt if your resources show different fields.
    for res in resources:
        typ = res.get("type", "")
        if "FungibleStore<" not in typ:
            continue
        # Example structure (verify in your /resources payload):
        # data: { "balance": { "amount": "12345" }, "metadata": { "symbol": "...", "decimals": 6 } }
        data = res.get("data", {})
        bal_obj = data.get("balance") or {}
        meta = data.get("metadata") or {}

        raw = str(bal_obj.get("amount") or bal_obj.get("value") or "0")
        decimals = int(meta.get("decimals") or 8)
        symbol = str(meta.get("symbol") or "FA_TOKEN").upper()
        if not raw.isdigit():
            raw = "0"

        amount = _normalize_amount(raw, decimals)
        # Derive token_type from angle brackets (if present)
        token_type = _extract_coinstore_token_type(typ) or typ
        balances.append(TokenBalance(
            symbol=symbol,
            address=token_type,
            decimals=decimals,
            raw=raw,
            amount=amount
        ))

    # Cache and return
    cache.set(key, balances, int(settings.balances_ttl_seconds))
    return balances
