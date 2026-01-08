# backend/app/services/concentration_analyzer.py - MVP5 CONCENTRATION ANALYSIS

from typing import List, Tuple
import math
from app.models.insights_models import (
    ConcentrationAnalysis,
    ConcentrationWarning
)


class ConcentrationAnalyzer:
    """
    Analyzes portfolio concentration and identifies risks.
    
    Uses the Herfindahl-Hirschman Index (HHI) for concentration measurement.
    """
    
    # Risk thresholds
    HIGH_CONCENTRATION_THRESHOLD = 0.40  # 40% of portfolio
    MODERATE_CONCENTRATION_THRESHOLD = 0.25  # 25% of portfolio
    
    def __init__(self):
        pass
    
    def analyze(self, token_balances: List[dict]) -> ConcentrationAnalysis:
        """
        Analyze portfolio concentration.
        
        Args:
            token_balances: List of token balances with usd_value
            
        Returns:
            ConcentrationAnalysis with risk level and warnings
        """
        if not token_balances:
            return ConcentrationAnalysis(
                overall_risk="low",
                warnings=[],
                token_count=0,
                herfindahl_index=0.0
            )
        
        # Calculate total portfolio value
        total_value = sum(b.get('usd_value', 0) for b in token_balances)
        
        if total_value == 0:
            return ConcentrationAnalysis(
                overall_risk="low",
                warnings=[],
                token_count=len(token_balances),
                herfindahl_index=0.0
            )
        
        # Calculate percentages and identify warnings
        warnings = []
        percentages = []
        
        for balance in token_balances:
            symbol = balance.get('symbol', 'UNKNOWN')
            value = balance.get('usd_value', 0)
            percentage = (value / total_value) if total_value > 0 else 0
            
            percentages.append(percentage)
            
            # Check concentration thresholds
            if percentage >= self.HIGH_CONCENTRATION_THRESHOLD:
                warnings.append(ConcentrationWarning(
                    token_symbol=symbol,
                    percentage=percentage * 100,
                    risk_level="high",
                    message=f"{symbol} represents {percentage*100:.1f}% of your portfolio - high concentration risk"
                ))
            elif percentage >= self.MODERATE_CONCENTRATION_THRESHOLD:
                warnings.append(ConcentrationWarning(
                    token_symbol=symbol,
                    percentage=percentage * 100,
                    risk_level="moderate",
                    message=f"{symbol} represents {percentage*100:.1f}% of your portfolio - moderate concentration"
                ))
        
        # Calculate Herfindahl-Hirschman Index (HHI)
        # HHI = sum of squared market shares
        # Range: 0 (perfect diversification) to 1 (complete concentration)
        hhi = sum(p ** 2 for p in percentages)
        
        # Determine overall risk level
        overall_risk = self._calculate_overall_risk(hhi, len(token_balances), warnings)
        
        return ConcentrationAnalysis(
            overall_risk=overall_risk,
            warnings=sorted(warnings, key=lambda w: w.percentage, reverse=True),
            token_count=len(token_balances),
            herfindahl_index=round(hhi, 4)
        )
    
    def _calculate_overall_risk(
        self, 
        hhi: float, 
        token_count: int, 
        warnings: List[ConcentrationWarning]
    ) -> str:
        """
        Calculate overall concentration risk level.
        
        Factors:
        - HHI score
        - Number of tokens
        - Presence of high-risk warnings
        """
        # Check for high-risk warnings
        has_high_risk = any(w.risk_level == "high" for w in warnings)
        
        if has_high_risk:
            return "high"
        
        # HHI thresholds
        # < 0.15: Low concentration (equivalent to ~7+ equal holdings)
        # 0.15-0.25: Moderate concentration (3-6 equal holdings)
        # > 0.25: High concentration (1-3 dominant holdings)
        
        if hhi < 0.15 and token_count >= 5:
            return "low"
        elif hhi < 0.25 and token_count >= 3:
            return "moderate"
        else:
            return "high"
    
    def get_diversification_recommendations(
        self, 
        analysis: ConcentrationAnalysis
    ) -> List[str]:
        """
        Generate actionable recommendations to improve diversification.
        """
        recommendations = []
        
        if analysis.overall_risk == "high":
            # High concentration - suggest diversification
            if analysis.warnings:
                top_holding = analysis.warnings[0]
                recommendations.append(
                    f"Consider reducing {top_holding.token_symbol} allocation from {top_holding.percentage:.1f}% to below 40%"
                )
            
            if analysis.token_count < 5:
                recommendations.append(
                    f"Add more tokens to your portfolio (currently {analysis.token_count}). Aim for at least 5-7 different assets."
                )
            
            recommendations.append(
                "Consider allocating to stablecoins for balance and reduced volatility"
            )
            
        elif analysis.overall_risk == "moderate":
            if analysis.warnings:
                recommendations.append(
                    f"Monitor concentration levels - {len(analysis.warnings)} token(s) approaching concentration thresholds"
                )
            
            recommendations.append(
                "Your diversification is reasonable but could be improved"
            )
            
        else:  # low risk
            recommendations.append(
                "Your portfolio shows good diversification across multiple assets"
            )
        
        return recommendations
    
    def calculate_concentration_score(self, hhi: float) -> float:
        """
        Convert HHI to a 0-1 concentration score.
        
        0 = perfectly diversified
        1 = completely concentrated
        
        Returns:
            Float between 0 and 1
        """
        # HHI already ranges 0-1, but we can normalize it for better UX
        # Using square root to make the scale more linear for perception
        return min(1.0, math.sqrt(hhi))


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def format_concentration_message(risk_level: str, token_count: int) -> str:
    """
    Generate user-friendly concentration message.
    """
    if risk_level == "high":
        return f"⚠️ High concentration detected across {token_count} token(s)"
    elif risk_level == "moderate":
        return f"🟡 Moderate concentration across {token_count} token(s)"
    else:
        return f"🟢 Well diversified across {token_count} token(s)"


def get_concentration_color(risk_level: str) -> str:
    """
    Get color code for risk level (for frontend styling).
    """
    colors = {
        "high": "#ef4444",      # red-500
        "moderate": "#f59e0b",  # amber-500
        "low": "#10b981"        # green-500
    }
    return colors.get(risk_level, "#6b7280")  # gray-500 default