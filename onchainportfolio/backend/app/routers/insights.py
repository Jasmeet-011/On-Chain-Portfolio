# backend/app/routers/insights.py
"""
Portfolio Insights Router - MVP5

Endpoints for advanced portfolio intelligence.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.insights_models import PortfolioInsights
from app.services.insights_service import InsightsService
from app.services.db import wallets_collection
from app.deps import get_current_user
from app.services.adapters.aptos_adapter import AptosAdapter
from app.services.adapters.solana_adapter import SolanaAdapter
from app.deps import price_service
import os

router = APIRouter()

# Initialize insights service
insights_service = InsightsService()


# ============================================================
# INSIGHTS ENDPOINTS
# ============================================================

@router.get("/", response_model=PortfolioInsights)
async def get_portfolio_insights(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive portfolio insights.
    
    Returns:
        PortfolioInsights with all MVP5 analyses
    """
    user_id = str(current_user["_id"])
    
    print(f"[INSIGHTS] Generating insights for user {user_id}")
    
    # Get all user wallets
    wallets = list(wallets_collection.find({"user_id": user_id}))
    
    if not wallets:
        raise HTTPException(status_code=404, detail="No wallets found")
    
    # Initialize adapters
    aptos_rpc = os.getenv("APTOS_RPC_URL", "https://fullnode.testnet.aptoslabs.com/v1")
    solana_rpc = os.getenv("SOLANA_RPC_URL", "https://api.testnet.solana.com")
    
    aptos_client = AptosAdapter(rpc_url=aptos_rpc)
    solana_client = SolanaAdapter(rpc_url=solana_rpc)
    
    # Fetch balances for all wallets
    all_balances = []
    wallet_metadata = []
    
    for wallet in wallets:
        address = wallet.get("address")
        chain = wallet.get("chain", "aptos")
        wallet_id = str(wallet.get("_id"))
        
        wallet_metadata.append({
            "address": address,
            "chain": chain,
            "wallet_id": wallet_id,
            "label": wallet.get("label", "Wallet")
        })
        
        try:
            # Fetch balances
            if chain == "aptos":
                balances = aptos_client.get_token_balances(address)
            elif chain == "solana":
                balances = solana_client.get_token_balances(address)
            else:
                continue
            
            # Add USD values
            for balance in balances:
                symbol = balance.get("symbol")
                amount = balance.get("amount", 0)
                
                if not symbol or amount <= 0:
                    continue
                
                try:
                    usd_price = price_service.get_price(symbol, chain=chain)
                    
                    if usd_price and usd_price > 0:
                        usd_value = float(amount) * float(usd_price)
                        
                        all_balances.append({
                            "symbol": symbol,
                            "amount": amount,
                            "usd_value": usd_value,
                            "usd_price": usd_price,
                            "chain": chain,
                            "wallet_address": address,
                            "wallet_id": wallet_id
                        })
                except Exception as price_error:
                    print(f"[INSIGHTS] ⚠️  Price fetch failed for {symbol}: {price_error}")
                    continue
        
        except Exception as e:
            print(f"[INSIGHTS] ⚠️  Failed to fetch balances for {address}: {e}")
            continue
    
    if not all_balances:
        raise HTTPException(
            status_code=404,
            detail="No token balances found with valid prices"
        )
    
    print(f"[INSIGHTS] Found {len(all_balances)} token balances across {len(wallets)} wallets")
    
    # Generate insights
    try:
        insights = insights_service.generate_insights(
            token_balances=all_balances,
            wallet_metadata=wallet_metadata
        )
        
        return insights
    
    except Exception as e:
        print(f"[INSIGHTS] ❌ Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chain-exposure")
async def get_chain_exposure(
    current_user: dict = Depends(get_current_user)
):
    """
    Get chain exposure analysis only.
    
    Returns:
        ChainExposureAnalysis
    """
    insights = await get_portfolio_insights(current_user)
    return insights.chain_exposure


@router.get("/concentration")
async def get_concentration(
    current_user: dict = Depends(get_current_user)
):
    """
    Get concentration analysis only.
    
    Returns:
        ConcentrationAnalysis
    """
    insights = await get_portfolio_insights(current_user)
    return insights.concentration


@router.get("/volatility")
async def get_volatility(
    current_user: dict = Depends(get_current_user)
):
    """
    Get volatility breakdown only.
    
    Returns:
        VolatilityBreakdown
    """
    insights = await get_portfolio_insights(current_user)
    return insights.volatility


@router.get("/dominance")
async def get_token_dominance(
    current_user: dict = Depends(get_current_user)
):
    """
    Get token dominance rankings only.
    
    Returns:
        TokenDominanceList
    """
    insights = await get_portfolio_insights(current_user)
    return insights.token_dominance


@router.get("/summary")
async def get_insights_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get quick summary of insights.
    
    Returns:
        Key insights and recommendations only
    """
    insights = await get_portfolio_insights(current_user)
    
    return {
        "overall_risk_score": insights.overall_risk_score,
        "key_insights": insights.key_insights,
        "recommendations": insights.recommendations,
        "total_value_usd": insights.total_value_usd,
        "total_tokens": insights.total_tokens,
        "total_wallets": insights.total_wallets
    }