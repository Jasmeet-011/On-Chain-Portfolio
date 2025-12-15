# app/routers/prices.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional
from pydantic import BaseModel

from ..deps import price_service

router = APIRouter()


class PriceResponse(BaseModel):
    symbol: str
    usd_price: Optional[float]


class PricesResponse(BaseModel):
    prices: Dict[str, Optional[float]]


@router.get("/prices/{symbol}", response_model=PriceResponse)
def get_price(symbol: str):
    """
    Get USD price for a single token.
    
    Example: GET /v1/prices/APT
    Returns: {"symbol": "APT", "usd_price": 9.12}
    """
    symbol = symbol.upper()
    price = price_service.get_price(symbol)
    
    return PriceResponse(
        symbol=symbol,
        usd_price=price
    )


@router.get("/prices", response_model=PricesResponse)
def get_prices(symbols: str = Query(..., description="Comma-separated symbols (e.g., APT,USDC)")):
    """
    Get USD prices for multiple tokens.
    
    Example: GET /v1/prices?symbols=APT,USDC,BTC
    Returns: {"prices": {"APT": 9.12, "USDC": 0.99, "BTC": 42500.00}}
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")
    
    prices = price_service.get_prices(symbol_list)
    
    return PricesResponse(prices=prices)