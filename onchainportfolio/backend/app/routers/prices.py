# app/routers/prices.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional
from pydantic import BaseModel

from app.deps import price_service

router = APIRouter()


class PriceResponse(BaseModel):
    symbol: str
    usd_price: Optional[float]


class PricesResponse(BaseModel):
    prices: Dict[str, Optional[float]]


@router.get("/prices/{symbol}", response_model=PriceResponse)
def get_price(
    symbol: str,
    chain: Optional[str] = Query(None, description="Optional chain hint: aptos or solana")  # ← NEW
):
    """
    Get USD price for a single token.
    
    Examples:
        GET /v1/prices/APT
        GET /v1/prices/SOL?chain=solana
    
    Returns: {"symbol": "APT", "usd_price": 9.12}
    
    The chain parameter is optional but helps select the best price source:
    - Aptos tokens use CoinGecko
    - Solana tokens use Jupiter API (better coverage)
    """
    symbol = symbol.upper()
    price = price_service.get_price(symbol, chain=chain)  # ← Pass chain
    
    return PriceResponse(
        symbol=symbol,
        usd_price=price
    )


@router.get("/prices", response_model=PricesResponse)
def get_prices(
    symbols: str = Query(..., description="Comma-separated symbols (e.g., APT,USDC)"),
    chain: Optional[str] = Query(None, description="Optional chain hint: aptos or solana")  # ← NEW
):
    """
    Get USD prices for multiple tokens.
    
    Examples:
        GET /v1/prices?symbols=APT,USDC,BTC
        GET /v1/prices?symbols=SOL,USDC&chain=solana
    
    Returns: {"prices": {"APT": 9.12, "USDC": 0.99, "BTC": 42500.00}}
    
    The chain parameter is optional but helps select the best price source:
    - Aptos tokens use CoinGecko
    - Solana tokens use Jupiter API (better coverage)
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")
    
    prices = price_service.get_prices(symbol_list, chain=chain)  # ← Pass chain
    
    return PricesResponse(prices=prices)