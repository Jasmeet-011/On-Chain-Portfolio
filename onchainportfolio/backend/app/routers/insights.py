# backend/app/routers/insights.py
"""
Portfolio Insights Router - MVP5

Endpoints for advanced portfolio intelligence.
Optimized with:
- Batch price fetching for better performance
- Async parallel wallet fetching for concurrent data loading
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Set, Any
import logging
import asyncio

from app.models.insights_models import PortfolioInsights
from app.services.insights_service import InsightsService
from app.services.db import wallets_collection
from app.deps import get_current_user
from app.services.adapters import get_adapter_for_chain, SUPPORTED_CHAINS
from app.deps import price_service

logger = logging.getLogger("chainlens.routers.insights")

router = APIRouter()

# Initialize insights service
insights_service = InsightsService()


# ============================================================
# EMPTY INSIGHTS HELPER
# ============================================================

def _get_empty_insights() -> PortfolioInsights:
    """Return empty insights when no data is available."""
    return PortfolioInsights(
        total_value_usd=0.0,
        total_tokens=0,
        total_wallets=0,
        chain_exposure={
            "exposures": [],
            "diversity_score": "low",
            "primary_chain": None,
            "recommendation": "Add wallets to see chain exposure analysis"
        },
        concentration={
            "token_count": 0,
            "herfindahl_index": 0.0,
            "top_holding_percentage": 0.0,
            "overall_risk": "low",
            "warnings": []
        },
        volatility={
            "stablecoins": {"value_usd": 0.0, "percentage": 0.0},
            "volatile": {"value_usd": 0.0, "percentage": 0.0},
            "stablecoin_list": [],
            "risk_label": "balanced"
        },
        token_dominance={
            "tokens": [],
            "total_tokens": 0
        },
        overall_risk_score="low",
        key_insights=["Add wallets and tokens to see portfolio insights"],
        recommendations=["Connect a wallet or add one manually to get started"]
    )


# ============================================================
# HELPER FUNCTIONS FOR ASYNC PARALLEL FETCHING
# ============================================================

async def fetch_wallet_balances(
    wallet: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fetch balances for a single wallet asynchronously.

    Uses asyncio.to_thread to run sync adapter code without blocking.

    Args:
        wallet: Wallet document from database

    Returns:
        Dict with wallet metadata and raw balances
    """
    address = wallet.get("address")
    chain = wallet.get("chain", "aptos")
    wallet_id = str(wallet.get("_id"))

    result = {
        "wallet_id": wallet_id,
        "address": address,
        "chain": chain,
        "label": wallet.get("label", "Wallet"),
        "balances": [],
        "error": None
    }

    # Skip unsupported chains
    if chain not in SUPPORTED_CHAINS:
        result["error"] = f"Unsupported chain: {chain}"
        return result

    try:
        # Get adapter and fetch balances in thread pool (non-blocking)
        adapter = get_adapter_for_chain(chain)

        # Run sync adapter method in thread to not block event loop
        balances = await asyncio.to_thread(adapter.get_token_balances, address)

        # Extract valid balances
        for balance in balances:
            symbol = balance.get("symbol")
            amount = balance.get("amount", 0)

            if symbol and amount > 0:
                result["balances"].append({
                    "symbol": symbol,
                    "amount": amount,
                    "chain": chain,
                    "wallet_address": address,
                    "wallet_id": wallet_id
                })

    except Exception as e:
        logger.warning(f"Failed to fetch balances for {address}: {e}")
        result["error"] = str(e)

    return result


# ============================================================
# INSIGHTS ENDPOINTS
# ============================================================

@router.get("/", response_model=PortfolioInsights)
async def get_portfolio_insights(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive portfolio insights.

    Optimized with:
    - Async parallel wallet fetching (asyncio.gather)
    - Batch price fetching (single API call)
    - Async price fetching

    Returns:
        PortfolioInsights with all MVP5 analyses
    """
    user_id = str(current_user["_id"])

    logger.info(f"Generating insights for user {user_id}")

    # Get all user wallets
    wallets = list(wallets_collection.find({"user_id": user_id, "is_active": True}))

    if not wallets:
        logger.info(f"No wallets found for user {user_id}, returning empty insights")
        return _get_empty_insights()

    # ============================================================
    # PHASE 1: Fetch all wallet balances IN PARALLEL
    # ============================================================
    logger.info(f"Fetching balances for {len(wallets)} wallets in parallel")

    # Create tasks for parallel execution
    fetch_tasks = [fetch_wallet_balances(wallet) for wallet in wallets]

    # Execute all wallet fetches concurrently
    wallet_results = await asyncio.gather(*fetch_tasks)

    # Collect results
    raw_balances = []
    wallet_metadata = []

    for result in wallet_results:
        # Add wallet metadata
        wallet_metadata.append({
            "address": result["address"],
            "chain": result["chain"],
            "wallet_id": result["wallet_id"],
            "label": result["label"]
        })

        # Collect balances
        raw_balances.extend(result["balances"])

        # Log any errors
        if result["error"]:
            logger.warning(f"Wallet {result['address']}: {result['error']}")

    if not raw_balances:
        logger.info(f"No token balances found for user {user_id}, returning empty insights")
        return _get_empty_insights()

    # ============================================================
    # PHASE 2: Batch fetch all prices at once (ASYNC)
    # ============================================================
    unique_symbols: Set[str] = {b["symbol"] for b in raw_balances}

    logger.info(f"Batch fetching prices for {len(unique_symbols)} unique tokens")

    # Use async price fetching
    prices: Dict[str, float] = await price_service.get_prices_async(list(unique_symbols))

    # ============================================================
    # PHASE 3: Enrich balances with cached prices
    # ============================================================
    all_balances = []

    for balance in raw_balances:
        symbol = balance["symbol"]
        amount = balance["amount"]

        usd_price = prices.get(symbol)

        if usd_price and usd_price > 0:
            usd_value = float(amount) * float(usd_price)

            all_balances.append({
                "symbol": symbol,
                "amount": amount,
                "usd_value": usd_value,
                "usd_price": usd_price,
                "chain": balance["chain"],
                "wallet_address": balance["wallet_address"],
                "wallet_id": balance["wallet_id"]
            })

    if not all_balances:
        logger.info(f"No token balances with valid prices for user {user_id}, returning empty insights")
        return _get_empty_insights()

    logger.info(f"Found {len(all_balances)} token balances across {len(wallets)} wallets")

    # Generate insights
    try:
        insights = insights_service.generate_insights(
            token_balances=all_balances,
            wallet_metadata=wallet_metadata
        )

        return insights

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
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
