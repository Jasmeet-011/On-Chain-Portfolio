from fastapi import APIRouter, Query
from typing import Dict
from decimal import Decimal
from ..deps import price_service

router = APIRouter()

@router.get("/prices")
def get_prices(symbols: str = Query(..., description="Comma-separated symbols, e.g., APT,USDC")) -> Dict[str, Decimal | None]:
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return {s: price_service.get_prices([s]).get(s) for s in syms}
