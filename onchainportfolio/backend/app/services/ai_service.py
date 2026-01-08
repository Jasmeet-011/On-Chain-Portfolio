# backend/app/services/ai_service.py - COMPATIBLE VERSION

import os
import re
from typing import List, Dict, Any, Optional

import google.generativeai as genai

from app.models.dto import WalletPortfolioResult, AggregatedPortfolio, TokenAggregate


class AIService:
    """
    AI service for portfolio analysis with optimized, context-aware responses.
    
    Uses google-generativeai (stable API)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI service.
        
        Args:
            api_key: Gemini API key (optional, falls back to env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided and not found in environment")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _extract_token_from_query(self, query: str) -> Optional[str]:
        """
        Extract token symbol from user query.
        
        Examples:
        - "How much SOL do I have?" → "SOL"
        - "Show my APT balance" → "APT"
        - "Do I have any USDC?" → "USDC"
        """
        query_lower = query.lower()
        
        # Common token patterns
        token_patterns = {
            r'\b(sol|solana)\b': 'SOL',
            r'\b(apt|aptos)\b': 'APT',
            r'\b(usdc)\b': 'USDC',
            r'\b(usdt|tether)\b': 'USDT',
            r'\b(eth|ethereum)\b': 'ETH',
            r'\b(btc|bitcoin)\b': 'BTC',
        }
        
        for pattern, token in token_patterns.items():
            if re.search(pattern, query_lower):
                return token
        
        return None

    def _filter_wallets_by_token(
        self,
        portfolio: AggregatedPortfolio,
        token_symbol: str
    ) -> List[Dict[str, Any]]:
        """
        Filter wallets to only show those containing the requested token.
        
        Returns list of wallets with their token holdings.
        """
        relevant_wallets = []
        
        for wallet_data in portfolio.wallets:
            if not wallet_data.get('data'):
                continue
                
            balances = wallet_data['data'].get('balances', [])
            
            # Check if this wallet has the requested token
            for balance in balances:
                if balance.get('symbol', '').upper() == token_symbol.upper():
                    relevant_wallets.append({
                        'label': wallet_data.get('label', 'Unknown Wallet'),
                        'address': wallet_data.get('address', ''),
                        'chain': wallet_data.get('chain', 'unknown'),
                        'token_symbol': balance.get('symbol'),
                        'token_amount': balance.get('amount', 0),
                        'token_value': balance.get('usd_value', 0),
                    })
                    break  # Only count each wallet once per token
        
        return relevant_wallets

    def _build_smart_context(
        self,
        query: str,
        portfolio: AggregatedPortfolio,
        wallet_results: List[WalletPortfolioResult]
    ) -> str:
        """
        Build smart, optimized context based on user query.
        
        Only includes relevant information instead of dumping all data.
        """
        # Extract what token user is asking about
        requested_token = self._extract_token_from_query(query)
        
        if requested_token:
            # User asking about specific token - show only relevant wallets
            relevant_wallets = self._filter_wallets_by_token(portfolio, requested_token)
            
            if relevant_wallets:
                context_parts = [
                    f"User Query: {query}",
                    f"\nRequested Token: {requested_token}",
                    f"\nTotal {requested_token} Holdings:",
                    f"- Total Amount: {sum(w['token_amount'] for w in relevant_wallets):.4f} {requested_token}",
                    f"- Total Value: ${sum(w['token_value'] for w in relevant_wallets):.2f}",
                    f"\nFound in {len(relevant_wallets)} wallet(s):",
                ]
                
                for wallet in relevant_wallets:
                    chain_emoji = "⬢" if wallet['chain'] == 'aptos' else "◎"
                    context_parts.append(
                        f"- {wallet['label']} ({chain_emoji} {wallet['chain'].upper()}): "
                        f"{wallet['token_amount']:.4f} {wallet['token_symbol']} "
                        f"(${wallet['token_value']:.2f})"
                    )
                
                context_parts.extend([
                    f"\nINSTRUCTIONS FOR RESPONSE:",
                    f"1. Answer the user's question about {requested_token}",
                    f"2. ONLY mention the {len(relevant_wallets)} wallet(s) listed above that contain {requested_token}",
                    f"3. Format: 'You have X {requested_token} worth $Y'",
                    f"4. Then list wallets: 'Found in: [Wallet Name] - X {requested_token}'",
                    f"5. Use wallet NAMES only, do NOT show addresses",
                    f"6. Do NOT mention wallets without {requested_token}",
                    f"7. Keep response concise and focused on {requested_token}",
                ])
                
                return "\n".join(context_parts)
        
        # General portfolio query - show all wallets with summary
        context_parts = [
            f"User Query: {query}",
            f"\nPortfolio Summary:",
            f"- Total Value: ${portfolio.total_usd_value:.2f}",
            f"- Total Wallets: {portfolio.total_wallets}",
            f"- Successful: {portfolio.successful_wallets}",
        ]
        
        if portfolio.by_token:
            context_parts.append(f"\nToken Holdings:")
            for token in portfolio.by_token[:10]:  # Top 10 tokens
                context_parts.append(
                    f"- {token.symbol}: {token.total_amount:.4f} "
                    f"(${token.total_usd_value:.2f}) across {token.wallet_count} wallet(s)"
                )
        
        if portfolio.wallets:
            context_parts.append(f"\nWallet Breakdown:")
            for wallet_data in portfolio.wallets:
                if wallet_data.get('data'):
                    chain = wallet_data.get('chain', 'unknown')
                    chain_emoji = "⬢" if chain == 'aptos' else "◎"
                    total_value = wallet_data['data'].get('total_usd_value', 0)
                    context_parts.append(
                        f"- {wallet_data['label']} ({chain_emoji} {chain.upper()}): ${total_value:.2f}"
                    )
        
        context_parts.extend([
            f"\nINSTRUCTIONS FOR RESPONSE:",
            f"1. Answer the user's question clearly",
            f"2. Use wallet NAMES only (no addresses needed)",
            f"3. Show token amounts for relevant wallets",
            f"4. Keep response focused and concise",
            f"5. Use emojis for chains (⬢ for Aptos, ◎ for Solana)",
        ])
        
        return "\n".join(context_parts)

    def _build_system_prompt(self) -> str:
        """System prompt for optimized responses."""
        return """You are a helpful portfolio assistant. 

CRITICAL RULES:
1. **Be Specific**: Only mention wallets that are relevant to the user's question
2. **No Addresses**: Use wallet names only, never show addresses
3. **Token Focus**: When user asks about a specific token, ONLY show wallets with that token
4. **Concise**: Keep responses short and to the point
5. **Format**: Use this structure:
   - Direct answer with total amount and value
   - List of relevant wallets with their holdings
   - No extra commentary

EXAMPLES:

User: "How much SOL do I have?"
Good Response: 
"You have **2.5 SOL**, valued at **$314.15**. This is held in your Phantom Wallet."

Bad Response:
"You have 2.5 SOL worth $314.15. Your portfolio includes: 
- test (APTOS): $14.29
- Petra Wallet (APTOS): $7.69  
- Phantom Wallet (SOLANA): $314.15"
❌ Don't list irrelevant wallets!

User: "How much APT do I have?"
Good Response:
"You have **3.2 APT**, valued at **$22.40**. Found in 2 wallets:
- Main Aptos: 2.0 APT
- Test Wallet: 1.2 APT"

Bad Response:
"You have APT in wallets 0xe037e2... ($14.29) and 0x06c525... ($7.69)"
❌ Don't show addresses!

Remember: Context-aware, wallet-focused, address-free!"""

    def generate_response(
        self,
        query: str,
        portfolio: AggregatedPortfolio,
        wallet_results: List[WalletPortfolioResult]
    ) -> str:
        """
        Generate optimized AI response using Gemini.
        
        Args:
            query: User's question
            portfolio: Aggregated portfolio data
            wallet_results: Individual wallet results
            
        Returns:
            Optimized, context-aware response
        """
        try:
            # Build smart context
            context = self._build_smart_context(query, portfolio, wallet_results)
            system_prompt = self._build_system_prompt()
            
            # Generate response
            full_prompt = f"{system_prompt}\n\n{context}\n\nUser Question: {query}\n\nYour Response:"
            
            response = self.model.generate_content(full_prompt)
            
            if response and response.text:
                return response.text.strip()
            
            return "I couldn't generate a response. Please try again."
                
        except Exception as e:
            print(f"Error generating AI response: {e}")
            # Fall back to non-AI response
            return self.generate_fallback_response(query, portfolio)

    def generate_fallback_response(
        self,
        query: str,
        portfolio: AggregatedPortfolio
    ) -> str:
        """
        Generate fallback response without AI (for when Gemini fails).
        
        Still applies smart filtering logic.
        """
        # Check if asking about specific token
        requested_token = self._extract_token_from_query(query)
        
        if requested_token:
            relevant_wallets = self._filter_wallets_by_token(portfolio, requested_token)
            
            if not relevant_wallets:
                return f"You don't have any {requested_token} in your connected wallets."
            
            total_amount = sum(w['token_amount'] for w in relevant_wallets)
            total_value = sum(w['token_value'] for w in relevant_wallets)
            
            response_parts = [
                f"You have **{total_amount:.4f} {requested_token}**, valued at **${total_value:.2f}**.",
            ]
            
            if len(relevant_wallets) == 1:
                response_parts.append(f"This is held in your {relevant_wallets[0]['label']}.")
            else:
                response_parts.append(f"\nFound in {len(relevant_wallets)} wallets:")
                for wallet in relevant_wallets:
                    response_parts.append(
                        f"- {wallet['label']}: {wallet['token_amount']:.4f} {requested_token}"
                    )
            
            return "\n".join(response_parts)
        
        # General portfolio query
        return (
            f"Your portfolio is worth **${portfolio.total_usd_value:.2f}** "
            f"across {portfolio.total_wallets} wallet(s). "
            f"You have {len(portfolio.by_token or [])} different tokens."
        )


# Convenience function for backward compatibility
def generate_portfolio_response(
    query: str,
    portfolio: AggregatedPortfolio,
    wallet_results: List[WalletPortfolioResult],
    api_key: Optional[str] = None
) -> str:
    """
    Generate optimized AI response.
    
    Args:
        query: User's question
        portfolio: Aggregated portfolio data
        wallet_results: Individual wallet results
        api_key: Optional API key (falls back to env var)
    """
    service = AIService(api_key=api_key)
    return service.generate_response(query, portfolio, wallet_results)