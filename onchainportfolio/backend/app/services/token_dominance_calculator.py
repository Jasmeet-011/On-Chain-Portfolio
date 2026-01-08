# backend/app/services/token_dominance_calculator.py - MVP5 TOKEN DOMINANCE

from typing import List
from app.models.insights_models import (
    TokenDominance,
    TokenDominanceList
)


class TokenDominanceCalculator:
    """
    Calculates and ranks token holdings by portfolio dominance.
    
    Helps users understand which tokens drive their portfolio value.
    """
    
    def __init__(self):
        pass
    
    def calculate(self, token_balances: List[dict]) -> TokenDominanceList:
        """
        Calculate token dominance rankings.
        
        Args:
            token_balances: List of token balances with symbol, usd_value, chain
            
        Returns:
            TokenDominanceList with ranked tokens
        """
        if not token_balances:
            return TokenDominanceList(
                tokens=[],
                total_tokens=0
            )
        
        # Calculate total portfolio value
        total_value = sum(b.get('usd_value', 0) for b in token_balances)
        
        if total_value == 0:
            return TokenDominanceList(
                tokens=[],
                total_tokens=len(token_balances)
            )
        
        # Aggregate by token symbol (combine same token across wallets)
        token_data = {}
        
        for balance in token_balances:
            symbol = balance.get('symbol', 'UNKNOWN')
            value = balance.get('usd_value', 0)
            chain = balance.get('chain', 'unknown')
            
            if symbol in token_data:
                token_data[symbol]['value'] += value
            else:
                token_data[symbol] = {
                    'value': value,
                    'chain': chain  # Use first encountered chain
                }
        
        # Create dominance objects
        tokens = []
        for symbol, data in token_data.items():
            percentage = (data['value'] / total_value * 100) if total_value > 0 else 0
            
            tokens.append({
                'symbol': symbol,
                'value_usd': data['value'],
                'percentage': percentage,
                'chain': data['chain']
            })
        
        # Sort by value (descending)
        tokens.sort(key=lambda x: x['value_usd'], reverse=True)
        
        # Assign ranks and create TokenDominance objects
        ranked_tokens = []
        for rank, token in enumerate(tokens, start=1):
            ranked_tokens.append(TokenDominance(
                symbol=token['symbol'],
                value_usd=round(token['value_usd'], 2),
                percentage=round(token['percentage'], 2),
                rank=rank,
                chain=token['chain']
            ))
        
        return TokenDominanceList(
            tokens=ranked_tokens,
            total_tokens=len(ranked_tokens)
        )
    
    def get_top_n(self, dominance_list: TokenDominanceList, n: int = 5) -> List[TokenDominance]:
        """
        Get top N tokens by dominance.
        
        Args:
            dominance_list: Complete dominance list
            n: Number of top tokens to return
            
        Returns:
            List of top N tokens
        """
        return dominance_list.tokens[:n]
    
    def get_bottom_n(self, dominance_list: TokenDominanceList, n: int = 5) -> List[TokenDominance]:
        """
        Get bottom N tokens (smallest holdings).
        
        Useful for identifying "dust" or negligible holdings.
        """
        return dominance_list.tokens[-n:] if len(dominance_list.tokens) >= n else dominance_list.tokens
    
    def identify_dust_tokens(
        self, 
        dominance_list: TokenDominanceList,
        dust_threshold: float = 1.0  # Tokens < 1% of portfolio
    ) -> List[TokenDominance]:
        """
        Identify "dust" tokens - very small holdings.
        
        Args:
            dominance_list: Complete dominance list
            dust_threshold: Percentage threshold for dust (default 1%)
            
        Returns:
            List of dust tokens
        """
        return [
            token for token in dominance_list.tokens 
            if token.percentage < dust_threshold
        ]
    
    def get_token_concentration_tier(self, percentage: float) -> str:
        """
        Categorize token by concentration tier.
        
        Returns:
            "major" (>20%), "significant" (10-20%), "minor" (5-10%), "minimal" (<5%)
        """
        if percentage >= 20:
            return "major"
        elif percentage >= 10:
            return "significant"
        elif percentage >= 5:
            return "minor"
        else:
            return "minimal"
    
    def generate_dominance_insights(self, dominance_list: TokenDominanceList) -> List[str]:
        """
        Generate insights about token dominance.
        """
        insights = []
        
        if not dominance_list.tokens:
            return ["No tokens in portfolio"]
        
        # Top holding insight
        top_token = dominance_list.tokens[0]
        tier = self.get_token_concentration_tier(top_token.percentage)
        
        if tier == "major":
            insights.append(
                f"💎 {top_token.symbol} is your largest holding at {top_token.percentage:.1f}% "
                f"(${top_token.value_usd:.2f})"
            )
        else:
            insights.append(
                f"Your portfolio is well-balanced with {top_token.symbol} leading at {top_token.percentage:.1f}%"
            )
        
        # Diversification insight
        if dominance_list.total_tokens == 1:
            insights.append("⚠️ Single token portfolio - consider diversifying")
        elif dominance_list.total_tokens <= 3:
            insights.append(f"🟡 Limited diversification with {dominance_list.total_tokens} tokens")
        else:
            insights.append(f"✅ Diversified across {dominance_list.total_tokens} tokens")
        
        # Top 3 concentration
        if len(dominance_list.tokens) >= 3:
            top_3_percentage = sum(t.percentage for t in dominance_list.tokens[:3])
            insights.append(
                f"📊 Top 3 holdings represent {top_3_percentage:.1f}% of portfolio"
            )
        
        # Dust tokens
        dust = self.identify_dust_tokens(dominance_list)
        if len(dust) > 0:
            dust_value = sum(t.value_usd for t in dust)
            insights.append(
                f"💰 {len(dust)} small holdings (<1% each) worth ${dust_value:.2f} total"
            )
        
        return insights


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def format_token_rank(rank: int) -> str:
    """
    Format rank with ordinal suffix (1st, 2nd, 3rd, etc.)
    """
    if 10 <= rank % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank % 10, 'th')
    return f"{rank}{suffix}"


def get_dominance_emoji(percentage: float) -> str:
    """
    Get emoji based on dominance level.
    """
    if percentage >= 40:
        return "🔴"  # High concentration
    elif percentage >= 25:
        return "🟡"  # Moderate
    elif percentage >= 10:
        return "🟢"  # Significant
    elif percentage >= 5:
        return "🔵"  # Minor
    else:
        return "⚪"  # Minimal


def format_dominance_summary(dominance_list: TokenDominanceList) -> str:
    """
    Generate one-line summary of token dominance.
    """
    if not dominance_list.tokens:
        return "No tokens"
    
    if dominance_list.total_tokens == 1:
        return f"Single holding: {dominance_list.tokens[0].symbol}"
    
    top_3 = dominance_list.tokens[:3]
    top_3_names = ", ".join(t.symbol for t in top_3)
    
    if dominance_list.total_tokens <= 3:
        return f"{dominance_list.total_tokens} tokens: {top_3_names}"
    else:
        return f"{dominance_list.total_tokens} tokens led by {top_3_names}"