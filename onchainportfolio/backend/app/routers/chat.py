# backend/app/routers/chat.py - COMPLETE FIXED VERSION FOR MONGODB

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import os
from app.models.dto import ChatRequest, ChatResponse, WalletPortfolioResult, AggregatedPortfolio, TokenAggregate
from app.deps import get_current_user, price_service  # ✅ Import price_service
from app.services.db import wallets_collection
from app.services.adapters.aptos_adapter import AptosAdapter
from app.services.adapters.solana_adapter import SolanaAdapter
from app.services.ai_service import generate_portfolio_response

router = APIRouter()

# ✅ Initialize with RPC URLs from environment
APTOS_RPC_URL = os.getenv("APTOS_RPC_URL", "https://fullnode.testnet.aptoslabs.com/v1")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.testnet.solana.com")

aptos_client = AptosAdapter(rpc_url=APTOS_RPC_URL)
solana_client = SolanaAdapter(rpc_url=SOLANA_RPC_URL)


def get_portfolio_for_wallet(address: str, chain: str) -> dict:
    """
    Fetch portfolio for a single wallet on specified chain.
    
    Args:
        address: Wallet address
        chain: 'aptos' or 'solana'
        
    Returns:
        Portfolio data including balances and total value WITH USD prices
    """
    try:
        if chain == 'aptos':
            balances = aptos_client.get_token_balances(address)
        elif chain == 'solana':
            balances = solana_client.get_token_balances(address)
        else:
            raise ValueError(f"Unsupported chain: {chain}")
        
        # ✅ NEW: Enrich balances with USD prices
        enriched_balances = []
        total_value = 0.0
        
        for balance in balances:
            symbol = balance.get('symbol')
            amount = balance.get('amount', 0)
            
            # Fetch USD price for this token
            try:
                usd_price = price_service.get_price(symbol, chain=chain)
                usd_value = (amount * usd_price) if usd_price else 0.0
            except Exception as e:
                print(f"[WARNING] Could not fetch price for {symbol}: {e}")
                usd_price = None
                usd_value = 0.0
            
            # Add USD fields to balance
            enriched_balance = {
                **balance,
                'usd_price': usd_price,
                'usd_value': usd_value
            }
            enriched_balances.append(enriched_balance)
            total_value += usd_value
        
        return {
            'balances': enriched_balances,
            'total_usd_value': total_value,
            'chain': chain
        }
    except Exception as e:
        print(f"Error fetching portfolio for {address} on {chain}: {e}")
        raise


def aggregate_portfolios(wallet_results: list[WalletPortfolioResult]) -> AggregatedPortfolio:
    """
    Aggregate portfolio data from multiple wallets across chains.
    
    ✅ UPDATED: Preserves chain information for each wallet
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
    
    ✅ FIXED: Uses MongoDB _id field (not id)
    ✅ FIXED: Uses correct adapter methods
    ✅ UPDATED: Ensures chain information is preserved throughout
    """
    try:
        # ✅ FIXED: Extract user_id from MongoDB _id field
        user_id = str(current_user["_id"])
        print(f"[DEBUG] User ID: {user_id}")
        print(f"[DEBUG] User email: {current_user.get('email')}")
        
        # ✅ FIXED: Query MongoDB with correct user_id
        query = {"user_id": user_id}
        
        # Determine which wallets to analyze based on scope
        if request.scope == "all":
            # Get all user wallets
            wallets_cursor = wallets_collection.find(query)
        elif request.scope == "primary":
            # Get primary wallet only
            query["is_primary"] = True
            wallets_cursor = wallets_collection.find(query)
        else:
            # Specific wallet by address
            query["address"] = request.scope
            wallets_cursor = wallets_collection.find(query)
        
        # Convert cursor to list
        wallets = list(wallets_cursor)
        
        print(f"[DEBUG] Found {len(wallets)} wallet(s) for user")
        
        if not wallets:
            raise HTTPException(status_code=404, detail="No wallets found for this scope")
        
        # Fetch portfolio for each wallet
        wallet_results = []
        
        for wallet in wallets:
            address = wallet.get('address')
            label = wallet.get('label', 'Unknown Wallet')
            chain = wallet.get('chain', 'aptos')  # Default to aptos for backward compatibility
            
            print(f"[DEBUG] Processing wallet: {label} ({chain}) - {address}")
            
            try:
                portfolio_data = get_portfolio_for_wallet(address, chain)
                
                wallet_results.append(
                    WalletPortfolioResult(
                        address=address,
                        label=label,
                        chain=chain,
                        success=True,
                        error=None,
                        data=portfolio_data
                    )
                )
            except Exception as e:
                print(f"[ERROR] Failed to fetch portfolio for {address}: {e}")
                wallet_results.append(
                    WalletPortfolioResult(
                        address=address,
                        label=label,
                        chain=chain,
                        success=False,
                        error=str(e),
                        data=None
                    )
                )
        
        # Aggregate portfolio data
        aggregated = aggregate_portfolios(wallet_results)
        
        print(f"[DEBUG] Aggregated portfolio: ${aggregated.total_usd_value:.2f} across {aggregated.total_wallets} wallets")
        
        # Generate optimized AI response
        answer = generate_portfolio_response(
            query=request.question,
            portfolio=aggregated,
            wallet_results=wallet_results
        )
        
        print(f"[DEBUG] Generated answer: {answer[:100]}...")
        
        return ChatResponse(
            answer=answer,
            portfolio=aggregated,
            wallet_results=wallet_results,
            scope_used=request.scope
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")