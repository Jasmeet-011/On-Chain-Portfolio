# app/routers/chat.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from decimal import Decimal

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    WalletPortfolioResult,
    AggregatedPortfolio,
    TokenAggregate
)
from app.deps import get_current_user, ai_service
from app.services.wallet_service import list_user_wallets, get_primary_wallet, get_wallet_by_address
from .portfolio import get_portfolio

router = APIRouter()


def aggregate_portfolios(wallet_results: List[WalletPortfolioResult]) -> AggregatedPortfolio:
    """
    Aggregate portfolio data from multiple wallets.
    
    Args:
        wallet_results: List of wallet portfolio results (successful and failed)
    
    Returns:
        AggregatedPortfolio with combined data
    """
    # Filter successful wallets
    successful_results = [r for r in wallet_results if r.success and r.data]
    
    # Calculate totals
    total_usd = 0.0
    token_aggregates: Dict[str, Dict[str, Any]] = {}
    all_wallet_data = []
    
    for result in successful_results:
        wallet_data = result.data
        
        # Add to total USD value
        if "total_usd_value" in wallet_data:
            total_usd += float(wallet_data["total_usd_value"])
        
        # Aggregate tokens
        for balance in wallet_data.get("balances", []):
            symbol = balance.get("symbol")
            if not symbol:
                continue
            
            amount = float(balance.get("amount", 0))
            usd_value = float(balance.get("usd_value", 0)) if balance.get("usd_value") else 0
            
            if symbol not in token_aggregates:
                token_aggregates[symbol] = {
                    "symbol": symbol,
                    "total_amount": 0.0,
                    "total_usd_value": 0.0,
                    "wallet_count": 0
                }
            
            token_aggregates[symbol]["total_amount"] += amount
            token_aggregates[symbol]["total_usd_value"] += usd_value
            token_aggregates[symbol]["wallet_count"] += 1
        
        # Store wallet data
        all_wallet_data.append({
            "address": result.address,
            "label": result.label,
            "data": wallet_data
        })
    
    # Convert token aggregates to list
    by_token = [
        TokenAggregate(**agg)
        for agg in token_aggregates.values()
    ]
    
    return AggregatedPortfolio(
        total_usd_value=round(total_usd, 2),
        total_wallets=len(wallet_results),
        successful_wallets=len(successful_results),
        failed_wallets=len(wallet_results) - len(successful_results),
        by_token=by_token,
        wallets=all_wallet_data
    )


@router.post("/chat", response_model=ChatResponse)
def chat_with_portfolio(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat endpoint that answers questions about user's portfolio.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Scope Options:**
    - `"all"`: Analyze all connected wallets (default)
    - `"primary"`: Analyze only the primary wallet
    - `"0x..."`: Analyze a specific wallet address (if owned by user)
    
    **Features:**
    - Automatically fetches user's wallets from database
    - Aggregates portfolio data across multiple wallets
    - Handles failed wallet fetches gracefully (returns partial results)
    - Provides detailed results showing which wallets succeeded/failed
    
    **Example Request:**
    ```json
    {
        "question": "What tokens do I hold?",
        "scope": "all"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "answer": "You hold 50.5 APT across 2 wallets...",
        "portfolio": {
            "total_usd_value": 1356.52,
            "total_wallets": 3,
            "successful_wallets": 2,
            "failed_wallets": 1,
            "by_token": [...]
        },
        "wallet_results": [...],
        "scope_used": "all"
    }
    ```
    """
    user_id = str(current_user["_id"])
    
    print(f"[CHAT] User {user_id} asked: {request.question}")
    print(f"[CHAT] Scope: {request.scope}")
    
    # Step 1: Determine which wallets to use based on scope
    user_wallets = list_user_wallets(user_id)
    
    if not user_wallets:
        raise HTTPException(
            status_code=404,
            detail="No wallets found. Please add a wallet first."
        )
    
    print(f"[CHAT] User has {len(user_wallets)} total wallets")
    
    selected_wallets = []
    
    if request.scope == "all":
        selected_wallets = user_wallets
        print(f"[CHAT] Using all {len(selected_wallets)} wallets")
    
    elif request.scope == "primary":
        primary = get_primary_wallet(user_id)
        if not primary:
            raise HTTPException(
                status_code=404,
                detail="No primary wallet found. Please set a primary wallet first."
            )
        selected_wallets = [primary]
        print(f"[CHAT] Using primary wallet: {primary['address']}")
    
    else:
        # Specific address requested
        specific_wallet = get_wallet_by_address(user_id, request.scope)
        if not specific_wallet:
            raise HTTPException(
                status_code=404,
                detail=f"Wallet {request.scope} not found or not owned by you."
            )
        selected_wallets = [specific_wallet]
        print(f"[CHAT] Using specific wallet: {request.scope}")
    
    # Step 2: Fetch portfolio for each wallet (with error handling)
    wallet_results: List[WalletPortfolioResult] = []
    
    for wallet in selected_wallets:
        address = wallet["address"]
        label = wallet["label"]
        
        print(f"[CHAT] Fetching portfolio for {label} ({address})...")
        
        try:
            portfolio_data = get_portfolio(address)
            
            wallet_results.append(WalletPortfolioResult(
                address=address,
                label=label,
                success=True,
                error=None,
                data=portfolio_data
            ))
            
            print(f"[CHAT] ✓ Successfully fetched {label}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"[CHAT] ✗ Failed to fetch {label}: {error_msg}")
            
            wallet_results.append(WalletPortfolioResult(
                address=address,
                label=label,
                success=False,
                error=error_msg,
                data=None
            ))
    
    # Step 3: Aggregate successful portfolios
    aggregated = aggregate_portfolios(wallet_results)
    
    print(f"[CHAT] Aggregated: {aggregated.successful_wallets}/{aggregated.total_wallets} wallets succeeded")
    print(f"[CHAT] Total USD value: ${aggregated.total_usd_value}")
    
    # Step 4: Check if we have any successful results
    if aggregated.successful_wallets == 0:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch portfolio data from all wallets. Please try again later."
        )
    
    # Step 5: Build context for AI including wallet failure info
    ai_context = {
        "portfolio": aggregated.dict(),
        "wallet_results": [r.dict() for r in wallet_results],
        "has_failures": aggregated.failed_wallets > 0
    }
    
    # Step 6: Get AI response
    print(f"[CHAT] Sending to AI service...")
    
    answer = ai_service.chat_with_portfolio(
        question=request.question,
        portfolio_data=ai_context
    )
    
    if not answer:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate AI response. Please try again."
        )
    
    print(f"[CHAT] ✓ Got AI response")
    
    # Step 7: Return response
    return ChatResponse(
        answer=answer,
        portfolio=aggregated,
        wallet_results=wallet_results,
        scope_used=request.scope
    )