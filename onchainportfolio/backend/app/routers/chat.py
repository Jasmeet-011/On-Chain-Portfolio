# backend/app/routers/chat.py - COMPLETE FIXED VERSION FOR MONGODB
"""
Chat Router - Optimized with:
- Batch price fetching
- Async parallel wallet fetching
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Set, List, Any
import logging
import asyncio

from app.models.dto import ChatRequest, ChatResponse, WalletPortfolioResult, AggregatedPortfolio, TokenAggregate
from app.deps import get_current_user, price_service
from app.services.db import wallets_collection
from app.services.adapters import get_adapter_for_chain, SUPPORTED_CHAINS
from app.services.ai_service import generate_portfolio_response

logger = logging.getLogger("chainlens.routers.chat")

router = APIRouter()


# ============================================================
# ASYNC HELPER FUNCTIONS
# ============================================================

async def fetch_wallet_balances_for_chat(wallet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch balances for a single wallet asynchronously.

    Uses asyncio.to_thread to run sync adapter code without blocking.

    Args:
        wallet: Wallet document from database

    Returns:
        Dict with wallet info and raw balances
    """
    address = wallet.get('address')
    chain = wallet.get('chain', 'aptos')

    result = {
        'wallet': wallet,
        'balances': [],
        'error': None
    }

    # Skip unsupported chains
    if chain not in SUPPORTED_CHAINS:
        result['error'] = f"Unsupported chain: {chain}"
        return result

    try:
        adapter = get_adapter_for_chain(chain)

        # Run sync adapter method in thread to not block event loop
        balances = await asyncio.to_thread(adapter.get_token_balances, address)

        result['balances'] = balances

    except Exception as e:
        logger.warning(f"Failed to fetch balances for {address}: {e}")
        result['error'] = str(e)

    return result


def get_portfolio_for_wallet(address: str, chain: str, prices: Dict[str, float] = None) -> dict:
    """
    Fetch portfolio for a single wallet using the multi-chain adapter system.

    Optimized: Accepts pre-fetched prices to avoid redundant API calls.

    Args:
        address: Wallet address
        chain: Chain identifier (e.g., 'aptos', 'solana', 'ethereum_sepolia', 'polygon_amoy')
        prices: Optional pre-fetched prices dict

    Returns:
        Portfolio data including balances and total value WITH USD prices
    """
    try:
        # Validate chain is supported
        if chain not in SUPPORTED_CHAINS:
            raise ValueError(f"Unsupported chain: {chain}. Available: {list(SUPPORTED_CHAINS.keys())}")

        # Get adapter for this chain
        adapter = get_adapter_for_chain(chain)

        # Get token balances using the adapter
        balances = adapter.get_token_balances(address)

        # Enrich balances with USD prices
        enriched_balances = []
        total_value = 0.0

        for balance in balances:
            symbol = balance.get('symbol')
            amount = balance.get('amount', 0)

            # Use pre-fetched price if available, otherwise try to get it
            usd_price = None
            usd_value = 0.0

            if prices and symbol:
                usd_price = prices.get(symbol)
            elif symbol:
                try:
                    usd_price = price_service.get_price(symbol, chain=chain)
                except Exception as e:
                    logger.warning(f"Could not fetch price for {symbol}: {e}")

            if usd_price and amount > 0:
                usd_value = amount * usd_price
                total_value += usd_value

            # Add USD fields to balance
            enriched_balance = {
                **balance,
                'usd_price': usd_price,
                'usd_value': usd_value
            }
            enriched_balances.append(enriched_balance)

        return {
            'balances': enriched_balances,
            'total_usd_value': total_value,
            'chain': chain
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio for {address} on {chain}: {e}")
        raise


def aggregate_portfolios(wallet_results: list[WalletPortfolioResult]) -> AggregatedPortfolio:
    """
    Aggregate portfolio data from multiple wallets across chains.

    Preserves chain information for each wallet.
    """
    total_usd_value = 0.0
    successful_wallets = 0
    failed_wallets = 0

    # Track tokens across all wallets
    token_aggregates = {}

    # Store wallet data with chain info
    wallets = []

    for result in wallet_results:
        if result.success and result.data:
            successful_wallets += 1
            wallet_total = result.data.get('total_usd_value', 0)
            total_usd_value += wallet_total

            wallets.append({
                'address': result.address,
                'label': result.label,
                'chain': result.chain,
                'data': result.data
            })

            # Aggregate tokens
            for balance in result.data.get('balances', []):
                symbol = balance.get('symbol', 'UNKNOWN')
                amount = balance.get('amount', 0)
                usd_value = balance.get('usd_value', 0)

                if symbol not in token_aggregates:
                    token_aggregates[symbol] = {
                        'symbol': symbol,
                        'total_amount': 0,
                        'total_usd_value': 0,
                        'wallet_count': 0,
                        'wallets': []
                    }

                token_aggregates[symbol]['total_amount'] += amount
                token_aggregates[symbol]['total_usd_value'] += usd_value
                token_aggregates[symbol]['wallet_count'] += 1
                token_aggregates[symbol]['wallets'].append(result.label)
        else:
            failed_wallets += 1

    # Convert to TokenAggregate objects
    by_token = [
        TokenAggregate(
            symbol=data['symbol'],
            total_amount=data['total_amount'],
            total_usd_value=data['total_usd_value'],
            wallet_count=data['wallet_count']
        )
        for data in token_aggregates.values()
    ]

    # Sort by USD value
    by_token.sort(key=lambda x: x.total_usd_value, reverse=True)

    return AggregatedPortfolio(
        total_usd_value=total_usd_value,
        total_wallets=len(wallet_results),
        successful_wallets=successful_wallets,
        failed_wallets=failed_wallets,
        by_token=by_token,
        wallets=wallets
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat endpoint with optimized, context-aware responses.

    Optimized with:
    - Async parallel wallet fetching (asyncio.gather)
    - Batch price fetching (single API call)
    - Async price fetching
    """
    try:
        user_id = str(current_user["_id"])
        logger.info(f"Chat request from user {user_id}")

        # Query MongoDB for user wallets
        query = {"user_id": user_id}

        # Determine which wallets to analyze based on scope
        if request.scope == "all":
            wallets_cursor = wallets_collection.find(query)
        elif request.scope == "primary":
            query["is_primary"] = True
            wallets_cursor = wallets_collection.find(query)
        else:
            query["address"] = request.scope
            wallets_cursor = wallets_collection.find(query)

        wallets = list(wallets_cursor)

        logger.info(f"Found {len(wallets)} wallet(s) for user")

        if not wallets:
            raise HTTPException(status_code=404, detail="No wallets found for this scope")

        # ============================================================
        # PHASE 1: Fetch all balances IN PARALLEL (ASYNC!)
        # ============================================================
        logger.info(f"Fetching balances for {len(wallets)} wallets in parallel")

        # Create tasks for parallel execution
        fetch_tasks = [fetch_wallet_balances_for_chat(wallet) for wallet in wallets]

        # Execute all wallet fetches concurrently
        wallet_balances: List[dict] = await asyncio.gather(*fetch_tasks)

        # Collect all unique symbols
        all_symbols: Set[str] = set()
        for wb in wallet_balances:
            for balance in wb['balances']:
                symbol = balance.get('symbol')
                if symbol and balance.get('amount', 0) > 0:
                    all_symbols.add(symbol)

        # ============================================================
        # PHASE 2: Batch fetch all prices at once (ASYNC!)
        # ============================================================
        prices: Dict[str, float] = {}
        if all_symbols:
            logger.info(f"Batch fetching prices for {len(all_symbols)} unique tokens")
            prices = await price_service.get_prices_async(list(all_symbols))

        # ============================================================
        # PHASE 3: Build wallet results with pre-fetched prices
        # ============================================================
        wallet_results = []

        for wb in wallet_balances:
            wallet = wb['wallet']
            balances = wb['balances']
            error = wb['error']

            address = wallet.get('address')
            label = wallet.get('label', 'Unknown Wallet')
            chain = wallet.get('chain', 'aptos')

            if error:
                wallet_results.append(
                    WalletPortfolioResult(
                        address=address,
                        label=label,
                        chain=chain,
                        success=False,
                        error=error,
                        data=None
                    )
                )
                continue

            # Enrich balances with prices
            enriched_balances = []
            total_value = 0.0

            for balance in balances:
                symbol = balance.get('symbol')
                amount = balance.get('amount', 0)

                usd_price = prices.get(symbol) if symbol else None
                usd_value = 0.0

                if usd_price and amount > 0:
                    usd_value = amount * usd_price
                    total_value += usd_value

                enriched_balances.append({
                    **balance,
                    'usd_price': usd_price,
                    'usd_value': usd_value
                })

            wallet_results.append(
                WalletPortfolioResult(
                    address=address,
                    label=label,
                    chain=chain,
                    success=True,
                    error=None,
                    data={
                        'balances': enriched_balances,
                        'total_usd_value': total_value,
                        'chain': chain
                    }
                )
            )

        # Aggregate portfolio data
        aggregated = aggregate_portfolios(wallet_results)

        logger.info(f"Aggregated portfolio: ${aggregated.total_usd_value:.2f} across {aggregated.total_wallets} wallets")

        # Generate optimized AI response
        answer = generate_portfolio_response(
            query=request.question,
            portfolio=aggregated,
            wallet_results=wallet_results
        )

        return ChatResponse(
            answer=answer,
            portfolio=aggregated,
            wallet_results=wallet_results,
            scope_used=request.scope
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")
