# app/routers/portfolio.py
from fastapi import APIRouter, Path, Query, HTTPException
from typing import Dict, Any

from app.services.adapters import get_adapter_for_chain
from app.deps import price_service

router = APIRouter()


@router.get("/wallets/{address}/portfolio")
def get_portfolio(
    address: str = Path(..., min_length=3, max_length=200),
    chain: str = Query("aptos", description="Blockchain: aptos or solana")
) -> Dict[str, Any]:
    """
    Get complete portfolio with USD values for a wallet on any chain.
    
    Args:
        address: Wallet address
        chain: Blockchain identifier ("aptos" or "solana")
    
    Returns:
        Portfolio with balances and USD values
    """
    try:
        # Get the appropriate adapter for this chain
        adapter = get_adapter_for_chain(chain)
        
        # Fetch portfolio using adapter
        portfolio = adapter.get_portfolio(address)
        
        # Add USD prices to each balance
        total_usd_value = 0.0
        
        for balance in portfolio.get("balances", []):
            symbol = balance.get("symbol")
            amount = balance.get("amount", 0)
            
            if symbol:
                # Fetch USD price for this token
                usd_price = price_service.get_price(symbol, chain=chain)
                
                if usd_price:
                    balance["usd_price"] = float(usd_price)
                    balance["usd_value"] = float(amount) * float(usd_price)
                    total_usd_value += balance["usd_value"]
                else:
                    balance["usd_price"] = None
                    balance["usd_value"] = None
        
        # Add total USD value
        portfolio["total_usd_value"] = round(total_usd_value, 2)
        
        return portfolio
        
    except ValueError as e:
        # Chain not supported
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch portfolio: {str(e)}"
        )