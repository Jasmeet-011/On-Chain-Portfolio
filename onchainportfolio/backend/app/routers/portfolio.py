# app/routers/portfolio.py
from fastapi import APIRouter, Path
from typing import List, Dict, Any

from .balances import get_balances

router = APIRouter()


@router.get("/wallets/{address}/portfolio")
def get_portfolio(address: str = Path(..., min_length=3, max_length=200)) -> Dict[str, Any]:
    """
    Get complete portfolio with USD values for a wallet.
    """
    # Get balances (this already includes usd_price and usd_value)
    balances = get_balances(address)
    
    # Convert to dict format and calculate total
    total_usd_value = 0.0
    balance_list = []
    
    for balance in balances:
        # Convert all Decimal values to float for JSON serialization
        balance_dict = {
            "symbol": balance.symbol,
            "address": balance.address,
            "decimals": balance.decimals,
            "raw": balance.raw,
            "amount": float(balance.amount) if balance.amount else 0.0,  # ← Convert Decimal to float
            "usd_price": float(balance.usd_price) if balance.usd_price else None,
            "usd_value": float(balance.usd_value) if balance.usd_value else None
        }
        
        balance_list.append(balance_dict)
        
        # Add to total if we have a USD value
        if balance.usd_value is not None:
            total_usd_value += float(balance.usd_value)
    
    return {
        "address": address,
        "balances": balance_list,
        "total_usd_value": round(total_usd_value, 2)
    }