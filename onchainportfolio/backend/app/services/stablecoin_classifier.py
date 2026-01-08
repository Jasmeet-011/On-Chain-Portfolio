# backend/app/services/stablecoin_classifier.py - MVP5 STABLECOIN CLASSIFICATION

from typing import List, Dict, Set
from app.models.insights_models import VolatilityBreakdown


class StablecoinClassifier:
    """
    Classifies tokens as stablecoins or volatile assets.
    
    Helps users understand their risk exposure through asset volatility.
    """
    
    # Known stablecoins (case-insensitive)
    STABLECOINS = {
        # USD-pegged
        "USDC", "USDT", "DAI", "BUSD", "TUSD", "USDP", "GUSD", "USDD",
        "FRAX", "LUSD", "SUSD", "UST", "USDN", "USDK", "HUSD",
        
        # Other pegged stables
        "EURS", "EURT", "TGBP", "XSGD", "TRYB", "BIDR",
        
        # Algorithmic stables
        "FEI", "AMPL", "RAI", "FLOAT",
        
        # Protocol-specific stables
        "aUSDC", "cUSDC", "fUSDC",  # Aave, Compound, etc.
    }
    
    # Risk thresholds
    BALANCED_THRESHOLD = 0.30  # 30%+ stablecoins = balanced
    HIGH_RISK_THRESHOLD = 0.10  # <10% stablecoins = high risk
    
    def __init__(self, additional_stablecoins: List[str] = None):
        """
        Initialize classifier with optional custom stablecoins.
        
        Args:
            additional_stablecoins: Additional stablecoin symbols to recognize
        """
        self.stablecoins = self.STABLECOINS.copy()
        
        if additional_stablecoins:
            self.stablecoins.update(s.upper() for s in additional_stablecoins)
    
    def is_stablecoin(self, symbol: str) -> bool:
        """
        Check if a token is a stablecoin.
        
        Args:
            symbol: Token symbol
            
        Returns:
            True if stablecoin, False otherwise
        """
        # Check exact match
        if symbol.upper() in self.stablecoins:
            return True
        
        # Check common patterns
        symbol_upper = symbol.upper()
        
        # USD-prefixed tokens
        if symbol_upper.startswith("USD") and len(symbol) <= 6:
            return True
        
        # Wrapped/protocol versions
        if any(symbol_upper.startswith(prefix) for prefix in ["A", "C", "F", "Y"]):
            base = symbol_upper[1:]
            if base in self.stablecoins:
                return True
        
        return False
    
    def classify(self, token_balances: List[dict]) -> VolatilityBreakdown:
        """
        Classify portfolio tokens by volatility.
        
        Args:
            token_balances: List of token balances with symbol and usd_value
            
        Returns:
            VolatilityBreakdown with stablecoin vs volatile breakdown
        """
        if not token_balances:
            return VolatilityBreakdown(
                stablecoins={"value_usd": 0, "percentage": 0},
                volatile={"value_usd": 0, "percentage": 0},
                risk_label="balanced",
                stablecoin_list=[]
            )
        
        # Calculate totals
        stable_value = 0.0
        volatile_value = 0.0
        stablecoin_symbols = set()
        
        for balance in token_balances:
            symbol = balance.get('symbol', '')
            value = balance.get('usd_value', 0)
            
            if self.is_stablecoin(symbol):
                stable_value += value
                stablecoin_symbols.add(symbol)
            else:
                volatile_value += value
        
        total_value = stable_value + volatile_value
        
        # Calculate percentages
        stable_percentage = (stable_value / total_value * 100) if total_value > 0 else 0
        volatile_percentage = (volatile_value / total_value * 100) if total_value > 0 else 0
        
        # Determine risk label
        risk_label = self._calculate_risk_label(stable_percentage)
        
        return VolatilityBreakdown(
            stablecoins={
                "value_usd": round(stable_value, 2),
                "percentage": round(stable_percentage, 2)
            },
            volatile={
                "value_usd": round(volatile_value, 2),
                "percentage": round(volatile_percentage, 2)
            },
            risk_label=risk_label,
            stablecoin_list=sorted(list(stablecoin_symbols))
        )
    
    def _calculate_risk_label(self, stable_percentage: float) -> str:
        """
        Calculate risk label based on stablecoin allocation.
        
        Args:
            stable_percentage: Percentage of portfolio in stablecoins
            
        Returns:
            "balanced", "moderate", or "high"
        """
        stable_ratio = stable_percentage / 100
        
        if stable_ratio >= self.BALANCED_THRESHOLD:
            return "balanced"
        elif stable_ratio >= self.HIGH_RISK_THRESHOLD:
            return "moderate"
        else:
            return "high"
    
    def get_risk_recommendations(self, breakdown: VolatilityBreakdown) -> List[str]:
        """
        Generate recommendations based on volatility breakdown.
        """
        recommendations = []
        
        stable_pct = breakdown.stablecoins['percentage']
        
        if breakdown.risk_label == "high":
            recommendations.append(
                f"⚠️ High volatility exposure: Only {stable_pct:.1f}% in stablecoins"
            )
            recommendations.append(
                "Consider increasing stablecoin allocation to 10-30% for stability"
            )
            
            if not breakdown.stablecoin_list:
                recommendations.append(
                    "Add stablecoins like USDC or USDT to your portfolio"
                )
            
        elif breakdown.risk_label == "moderate":
            recommendations.append(
                f"🟡 Moderate risk: {stable_pct:.1f}% in stablecoins"
            )
            recommendations.append(
                "Consider increasing to 30%+ for a more balanced portfolio"
            )
            
        else:  # balanced
            recommendations.append(
                f"✅ Balanced allocation: {stable_pct:.1f}% in stablecoins"
            )
            recommendations.append(
                "Good mix of stability and growth potential"
            )
        
        return recommendations
    
    def add_stablecoin(self, symbol: str):
        """
        Add a custom stablecoin to the classifier.
        
        Useful for new stablecoins or chain-specific stables.
        """
        self.stablecoins.add(symbol.upper())
    
    def remove_stablecoin(self, symbol: str):
        """
        Remove a stablecoin from the classifier.
        
        Useful if a stablecoin depegs or is no longer considered stable.
        """
        self.stablecoins.discard(symbol.upper())
    
    def get_all_stablecoins(self) -> Set[str]:
        """
        Get all recognized stablecoins.
        """
        return self.stablecoins.copy()


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def format_volatility_message(risk_label: str, stable_percentage: float) -> str:
    """
    Generate user-friendly volatility message.
    """
    messages = {
        "high": f"⚠️ High risk: {stable_percentage:.1f}% stable, {100-stable_percentage:.1f}% volatile",
        "moderate": f"🟡 Moderate risk: {stable_percentage:.1f}% stable, {100-stable_percentage:.1f}% volatile",
        "balanced": f"✅ Balanced: {stable_percentage:.1f}% stable, {100-stable_percentage:.1f}% volatile"
    }
    return messages.get(risk_label, "Unknown risk profile")


def get_risk_color(risk_label: str) -> str:
    """
    Get color code for risk level (for frontend styling).
    """
    colors = {
        "high": "#ef4444",      # red-500
        "moderate": "#f59e0b",  # amber-500
        "balanced": "#10b981"   # green-500
    }
    return colors.get(risk_label, "#6b7280")  # gray-500 default


def calculate_sharpe_estimate(
    volatile_percentage: float,
    stable_percentage: float
) -> float:
    """
    Rough estimate of risk-adjusted return potential.
    
    This is a simplified proxy - NOT actual Sharpe ratio.
    Just for educational/indicative purposes.
    
    Returns:
        Float between 0 (all volatile) and 1 (all stable)
    """
    stable_ratio = stable_percentage / 100
    
    # Penalize extremes, reward balance
    # Optimal around 20-30% stable
    if 0.2 <= stable_ratio <= 0.4:
        return 1.0
    elif stable_ratio < 0.1:
        return 0.3  # Very high risk
    elif stable_ratio > 0.7:
        return 0.5  # Very conservative
    else:
        return 0.7  # Decent balance


def suggest_rebalance(
    current_stable_pct: float,
    target_stable_pct: float,
    total_value: float
) -> Dict[str, float]:
    """
    Suggest rebalancing to achieve target stablecoin allocation.
    
    Returns:
        Dictionary with suggested actions
    """
    current_stable = total_value * (current_stable_pct / 100)
    target_stable = total_value * (target_stable_pct / 100)
    
    difference = target_stable - current_stable
    
    if difference > 0:
        return {
            "action": "buy",
            "amount_usd": round(abs(difference), 2),
            "message": f"Buy ${abs(difference):.2f} in stablecoins to reach {target_stable_pct}%"
        }
    elif difference < 0:
        return {
            "action": "sell",
            "amount_usd": round(abs(difference), 2),
            "message": f"Sell ${abs(difference):.2f} in stablecoins to reach {target_stable_pct}%"
        }
    else:
        return {
            "action": "hold",
            "amount_usd": 0,
            "message": "Already at target allocation"
        }