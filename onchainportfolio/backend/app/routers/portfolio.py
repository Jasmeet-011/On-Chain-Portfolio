from fastapi import APIRouter, Path
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict
from ..models.dto import PortfolioSummary, TokenBalance
from ..services.cache import cache
from ..config import settings
from .balances import get_balances  # reuse
from ..deps import price_service

router = APIRouter()

@router.get("/wallets/{address}/portfolio", response_model=PortfolioSummary)
def get_portfolio(address: str = Path(..., min_length=3, max_length=200)):
    key = f"portfolio:{address}"
    cached = cache.get(key)
    if cached:
        return cached

    tokens: list[TokenBalance] = get_balances(address)  # uses cache internally
    syms = [t.symbol for t in tokens]
    prices = price_service.get_prices(syms)

    total = Decimal("0")
    by_token: Dict[str, Decimal] = {}

    enriched: list[TokenBalance] = []
    for t in tokens:
        p = prices.get(t.symbol)
        usd_value = None
        if p is not None:
            usd_value = (t.amount * p).quantize(Decimal("0.0001"))
            total += usd_value
            by_token[t.symbol] = by_token.get(t.symbol, Decimal("0")) + usd_value
        enriched.append(TokenBalance(**t.model_dump(), usd_price=p, usd_value=usd_value))

    summary = PortfolioSummary(
        address=address,
        total_usd=total.quantize(Decimal("0.0001")),
        tokens=enriched,
        by_token={k: v.quantize(Decimal("0.0001")) for k, v in by_token.items()},
        updated_at=datetime.now(timezone.utc)
    )
    cache.set(key, summary, int(settings.balances_ttl_seconds))
    return summary
