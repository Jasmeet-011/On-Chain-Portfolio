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
        """Generate top 5 key insights with specific dollar amounts and context."""
        insights = []

        # 1. Chain exposure — show dominant chain with dollar value
        if chain_exposure.exposures:
            dominant = chain_exposure.exposures[0]
            chain_count = len(chain_exposure.exposures)
            if chain_count == 1:
                insights.append(
                    f"⛓️ Single-chain portfolio — 100% on {dominant.chain.title()} (${dominant.value_usd:,.2f})"
                )
            elif dominant.percentage >= 80:
                insights.append(
                    f"⚠️ {dominant.percentage:.0f}% on {dominant.chain.title()} (${dominant.value_usd:,.2f}) across {chain_count} chains"
                )
            else:
                chains_text = ", ".join(e.chain.title() for e in chain_exposure.exposures[:3])
                insights.append(
                    f"🌐 Spread across {chain_count} chains ({chains_text}) — top is {dominant.chain.title()} at {dominant.percentage:.0f}%"
                )

        # 2. Top token dominance — with dollar value
        if token_dominance.tokens:
            top = token_dominance.tokens[0]
            if top.percentage >= 50:
                insights.append(
                    f"⚠️ {top.symbol} is {top.percentage:.0f}% of portfolio (${top.value_usd:,.2f}) — very high concentration"
                )
            elif top.percentage >= 30:
                insights.append(
                    f"🟡 {top.symbol} leads at {top.percentage:.0f}% (${top.value_usd:,.2f}) — moderate concentration"
                )
            else:
                top3 = token_dominance.tokens[:3]
                top3_pct = sum(t.percentage for t in top3)
                insights.append(
                    f"✅ Well balanced — top 3 tokens ({', '.join(t.symbol for t in top3)}) hold {top3_pct:.0f}% combined"
                )

        # 3. Volatility / stablecoin allocation
        stable_pct = volatility.stablecoins['percentage']
        stable_val = volatility.stablecoins['value_usd']
        volatile_val = volatility.volatile['value_usd']
        if stable_pct < 5:
            insights.append(
                f"🔴 Nearly 0% in stablecoins — all ${volatile_val:,.2f} in volatile assets"
            )
        elif stable_pct < 15:
            insights.append(
                f"🟠 Low stablecoin buffer: ${stable_val:,.2f} ({stable_pct:.0f}%) stable vs ${volatile_val:,.2f} volatile"
            )
        elif stable_pct > 50:
            insights.append(
                f"🟢 Conservative: ${stable_val:,.2f} ({stable_pct:.0f}%) in stablecoins — strong downside protection"
            )
        else:
            insights.append(
                f"🟡 Balanced mix: ${stable_val:,.2f} ({stable_pct:.0f}%) stablecoins + ${volatile_val:,.2f} volatile assets"
            )

        # 4. Concentration / HHI analysis
        hhi = concentration.herfindahl_index
        token_count = concentration.token_count
        if concentration.overall_risk == "high":
            insights.append(
                f"⚠️ High concentration (HHI {hhi:.2f}) across {token_count} token{'s' if token_count != 1 else ''} — portfolio heavily skewed"
            )
        elif concentration.overall_risk == "moderate":
            insights.append(
                f"🟡 Moderate spread across {token_count} tokens (HHI {hhi:.2f}) — reasonable but improvable"
            )
        else:
            insights.append(
                f"✅ Good diversification across {token_count} tokens (HHI {hhi:.2f})"
            )

        # 5. Dust / small holdings
        dust_tokens = self.dominance_calculator.identify_dust_tokens(token_dominance, dust_threshold=1.0)
        if len(dust_tokens) >= 3:
            dust_value = sum(t.value_usd for t in dust_tokens)
            insights.append(
                f"💡 {len(dust_tokens)} small holdings (<1% each) worth ${dust_value:.2f} total — consider consolidating"
            )
        elif token_dominance.total_tokens >= 10:
            insights.append(
                f"📊 Holding {token_dominance.total_tokens} different tokens across your wallets"
            )

        return insights[:5]

    def _generate_recommendations(
        self,
        chain_exposure,
        concentration,
        volatility,
        token_dominance
    ) -> List[str]:
        """Generate actionable recommendations with specific dollar targets."""
        recommendations = []

        total_value = sum(
            e.value_usd for e in chain_exposure.exposures
        ) if chain_exposure.exposures else 0

        # 1. Stablecoin recommendations with target amounts
        stable_pct = volatility.stablecoins['percentage']
        stable_val = volatility.stablecoins['value_usd']
        if stable_pct < 10 and total_value > 0:
            target_stable = total_value * 0.15
            needed = target_stable - stable_val
            recommendations.append(
                f"💰 Move ~${needed:,.2f} to USDC/USDT to reach a safer 15% stablecoin allocation"
            )
        elif stable_pct < 5:
            recommendations.append(
                "💰 Add stablecoins (USDC or USDT) to cushion against market drops"
            )

        # 2. Concentration — specific token reduction target
        if concentration.warnings:
            top_warning = concentration.warnings[0]
            if top_warning.risk_level == "high" and total_value > 0:
                target_val = total_value * 0.35
                token_val = (top_warning.percentage / 100) * total_value
                excess = token_val - target_val
                recommendations.append(
                    f"⚖️ {top_warning.token_symbol} is {top_warning.percentage:.0f}% of portfolio — "
                    f"consider reducing by ~${excess:,.2f} to diversify risk"
                )
            elif top_warning.risk_level == "moderate":
                recommendations.append(
                    f"🔍 Monitor {top_warning.token_symbol} ({top_warning.percentage:.0f}%) — "
                    f"approaching high concentration threshold (40%)"
                )

        # 3. Chain diversification — name specific chains to explore
        if chain_exposure.diversity_score == "low":
            current_chains = {e.chain.lower() for e in chain_exposure.exposures}
            all_chains = ["solana", "aptos", "ethereum", "polygon", "base"]
            missing = [c.title() for c in all_chains if c not in current_chains][:2]
            if missing:
                recommendations.append(
                    f"🌐 Explore {' or '.join(missing)} to reduce single-chain risk"
                )
            else:
                recommendations.append(
                    "🌐 Rebalance across your chains to reduce single-chain concentration"
                )

        # 4. Token count diversification
        if token_dominance.total_tokens < 4:
            recommendations.append(
                f"📊 Only {token_dominance.total_tokens} token(s) held — consider diversifying into "
                f"{'stablecoins and blue-chips' if token_dominance.total_tokens == 1 else 'a few more assets'}"
            )

        # 5. Dust consolidation
        dust_tokens = self.dominance_calculator.identify_dust_tokens(token_dominance, dust_threshold=1.0)
        if len(dust_tokens) > 5:
            dust_value = sum(t.value_usd for t in dust_tokens)
            recommendations.append(
                f"🧹 Consolidate {len(dust_tokens)} dust holdings worth ${dust_value:.2f} "
                f"(each <1% of portfolio) to simplify tracking"
            )

        return recommendations[:5]
    
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