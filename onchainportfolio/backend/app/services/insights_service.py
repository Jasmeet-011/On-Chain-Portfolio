# backend/app/services/insights_service.py
"""
Portfolio Insights Service - MVP5

Orchestrates all analyzers to generate comprehensive portfolio intelligence.
"""
from typing import List, Dict
from app.services.chain_exposure_analyzer import ChainExposureAnalyzer
from app.services.concentration_analyzer import ConcentrationAnalyzer
from app.services.stablecoin_classifier import StablecoinClassifier
from app.services.token_dominance_calculator import TokenDominanceCalculator
from app.models.insights_models import PortfolioInsights


class InsightsService:
    """
    Service for generating advanced portfolio insights.
    
    Combines all MVP5 analyzers into unified intelligence.
    """
    
    def __init__(self):
        self.chain_analyzer = ChainExposureAnalyzer()
        self.concentration_analyzer = ConcentrationAnalyzer()
        self.stablecoin_classifier = StablecoinClassifier()
        self.dominance_calculator = TokenDominanceCalculator()
        
        print("[INSIGHTS] Insights service initialized")
    
    def generate_insights(
        self,
        token_balances: List[dict],
        wallet_metadata: List[dict] = None
    ) -> PortfolioInsights:
        """
        Generate complete portfolio insights.
        
        Args:
            token_balances: List of token balances with symbol, usd_value, chain
            wallet_metadata: Optional wallet info for chain analysis
            
        Returns:
            PortfolioInsights with all analyses
        """
        print(f"[INSIGHTS] Generating insights for {len(token_balances)} token balances")
        
        # Run all analyses
        chain_exposure = self.chain_analyzer.analyze(token_balances, wallet_metadata)
        concentration = self.concentration_analyzer.analyze(token_balances)
        volatility = self.stablecoin_classifier.classify(token_balances)
        token_dominance = self.dominance_calculator.calculate(token_balances)
        
        # Calculate totals
        total_value = sum(b.get('usd_value', 0) for b in token_balances)
        total_tokens = len(set(b.get('symbol') for b in token_balances))
        total_wallets = len(wallet_metadata) if wallet_metadata else len(
            set(b.get('wallet_address') for b in token_balances if b.get('wallet_address'))
        )
        
        # Generate high-level insights
        key_insights = self._generate_key_insights(
            chain_exposure,
            concentration,
            volatility,
            token_dominance
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            chain_exposure,
            concentration,
            volatility,
            token_dominance
        )
        
        # Calculate overall risk score
        overall_risk = self._calculate_overall_risk(
            chain_exposure,
            concentration,
            volatility
        )
        
        print(f"[INSIGHTS] ✅ Generated insights:")
        print(f"  - Overall risk: {overall_risk}")
        print(f"  - Key insights: {len(key_insights)}")
        print(f"  - Recommendations: {len(recommendations)}")
        
        return PortfolioInsights(
            chain_exposure=chain_exposure,
            concentration=concentration,
            volatility=volatility,
            token_dominance=token_dominance,
            total_value_usd=round(total_value, 2),
            total_tokens=total_tokens,
            total_wallets=total_wallets,
            overall_risk_score=overall_risk,
            key_insights=key_insights,
            recommendations=recommendations
        )
    
    def _generate_key_insights(
        self,
        chain_exposure,
        concentration,
        volatility,
        token_dominance
    ) -> List[str]:
        """Generate top 3-5 key insights."""
        insights = []
        
        # Chain exposure insight
        if chain_exposure.dominant_chain and chain_exposure.exposures:
            dominant = chain_exposure.exposures[0]
            insights.append(
                f"💎 {dominant.percentage:.0f}% concentrated in {dominant.chain.title()}"
            )
        
        # Token concentration insight
        if token_dominance.tokens:
            top_token = token_dominance.tokens[0]
            if top_token.percentage > 30:
                insights.append(
                    f"⚠️ {top_token.symbol} dominates portfolio at {top_token.percentage:.0f}%"
                )
            else:
                insights.append(
                    f"✅ Balanced holdings led by {top_token.symbol} ({top_token.percentage:.0f}%)"
                )
        
        # Volatility insight
        stable_pct = volatility.stablecoins['percentage']
        if stable_pct < 10:
            insights.append(
                f"🔴 High volatility: Only {stable_pct:.0f}% in stablecoins"
            )
        elif stable_pct > 40:
            insights.append(
                f"🟢 Conservative: {stable_pct:.0f}% in stablecoins"
            )
        else:
            insights.append(
                f"🟡 Moderate risk: {stable_pct:.0f}% in stablecoins"
            )
        
        # Diversification insight
        if concentration.overall_risk == "high":
            insights.append(
                f"⚠️ High concentration across {concentration.token_count} tokens"
            )
        elif token_dominance.total_tokens >= 8:
            insights.append(
                f"✅ Well diversified with {token_dominance.total_tokens} tokens"
            )
        
        # Chain diversity insight
        if chain_exposure.diversity_score == "low" and len(chain_exposure.exposures) == 1:
            insights.append(
                "⚠️ Single-chain portfolio - consider multi-chain diversification"
            )
        
        return insights[:5]  # Top 5 insights
    
    def _generate_recommendations(
        self,
        chain_exposure,
        concentration,
        volatility,
        token_dominance
    ) -> List[str]:
        """Generate top 3-5 recommendations."""
        recommendations = []
        
        # Stablecoin recommendations
        stable_pct = volatility.stablecoins['percentage']
        if stable_pct < 10:
            recommendations.append(
                "💰 Increase stablecoin allocation to 10-30% for stability"
            )
        
        # Concentration recommendations
        if concentration.warnings:
            top_warning = concentration.warnings[0]
            if top_warning.risk_level == "high":
                recommendations.append(
                    f"⚖️ Reduce {top_warning.token_symbol} below 40% of portfolio"
                )
        
        # Chain diversification
        if chain_exposure.diversity_score == "low":
            recommendations.append(
                "🌐 Add wallets from other chains for diversification"
            )
        
        # Token diversification
        if token_dominance.total_tokens < 5:
            recommendations.append(
                f"📊 Consider adding more tokens (currently {token_dominance.total_tokens})"
            )
        
        # Dust cleanup
        dust_tokens = self.dominance_calculator.identify_dust_tokens(
            token_dominance,
            dust_threshold=1.0
        )
        if len(dust_tokens) > 5:
            dust_value = sum(t.value_usd for t in dust_tokens)
            recommendations.append(
                f"🧹 Consider consolidating {len(dust_tokens)} small holdings (${dust_value:.2f})"
            )
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _calculate_overall_risk(
        self,
        chain_exposure,
        concentration,
        volatility
    ) -> str:
        """
        Calculate overall portfolio risk score.
        
        Considers:
        - Chain diversity
        - Token concentration
        - Volatility exposure
        """
        risk_scores = []
        
        # Chain diversity risk
        if chain_exposure.diversity_score == "low":
            risk_scores.append(2)  # High risk
        elif chain_exposure.diversity_score == "moderate":
            risk_scores.append(1)
        else:
            risk_scores.append(0)  # Low risk
        
        # Concentration risk
        if concentration.overall_risk == "high":
            risk_scores.append(2)
        elif concentration.overall_risk == "moderate":
            risk_scores.append(1)
        else:
            risk_scores.append(0)
        
        # Volatility risk
        if volatility.risk_label == "high":
            risk_scores.append(2)
        elif volatility.risk_label == "moderate":
            risk_scores.append(1)
        else:
            risk_scores.append(0)
        
        # Average risk
        avg_risk = sum(risk_scores) / len(risk_scores)
        
        if avg_risk >= 1.5:
            return "high"
        elif avg_risk >= 0.75:
            return "moderate"
        else:
            return "low"