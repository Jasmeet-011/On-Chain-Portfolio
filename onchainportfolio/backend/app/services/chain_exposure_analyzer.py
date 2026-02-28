# backend/app/services/chain_exposure_analyzer.py - MVP5 CHAIN EXPOSURE ANALYSIS

import math
from typing import List, Dict
from collections import defaultdict
from app.models.insights_models import (
    ChainExposure,
    ChainExposureAnalysis
)


class ChainExposureAnalyzer:
    """
    Analyzes portfolio exposure across different blockchains.
    
    Helps users understand their multi-chain diversification.
    """
    
    # Diversity thresholds (based on dominant chain percentage)
    HIGH_DIVERSITY_THRESHOLD = 0.60  # No chain > 60%
    LOW_DIVERSITY_THRESHOLD = 0.80   # One chain > 80%
    
    def __init__(self):
        pass
    
    def analyze(
        self, 
        token_balances: List[dict],
        wallet_metadata: List[dict] = None
    ) -> ChainExposureAnalysis:
        """
        Analyze portfolio exposure across chains.
        
        Args:
            token_balances: List of token balances with chain and usd_value
            wallet_metadata: Optional list of wallet info for counting wallets per chain
            
        Returns:
            ChainExposureAnalysis with breakdown by chain
        """
        if not token_balances:
            return ChainExposureAnalysis(
                exposures=[],
                diversity_score="high",
                dominant_chain=None
            )
        
        # Aggregate by chain
        chain_data = defaultdict(lambda: {
            'value': 0.0,
            'wallet_count': 0,
            'wallets': set()
        })
        
        total_value = 0.0
        
        for balance in token_balances:
            chain = balance.get('chain', 'unknown').lower()
            value = balance.get('usd_value', 0)
            wallet_address = balance.get('wallet_address')
            
            chain_data[chain]['value'] += value
            total_value += value
            
            if wallet_address:
                chain_data[chain]['wallets'].add(wallet_address)
        
        # If wallet metadata provided, count wallets more accurately
        if wallet_metadata:
            wallet_chain_map = defaultdict(set)
            for wallet in wallet_metadata:
                chain = wallet.get('chain', 'unknown').lower()
                address = wallet.get('address')
                if address:
                    wallet_chain_map[chain].add(address)
            
            # Update wallet counts
            for chain in chain_data:
                if chain in wallet_chain_map:
                    chain_data[chain]['wallet_count'] = len(wallet_chain_map[chain])
        else:
            # Use wallets from balances
            for chain in chain_data:
                chain_data[chain]['wallet_count'] = len(chain_data[chain]['wallets'])
        
        # Create exposure objects
        exposures = []
        for chain, data in chain_data.items():
            percentage = (data['value'] / total_value * 100) if total_value > 0 else 0
            
            exposures.append(ChainExposure(
                chain=chain,
                value_usd=round(data['value'], 2),
                percentage=round(percentage, 2),
                wallet_count=data['wallet_count']
            ))
        
        # Sort by value (descending)
        exposures.sort(key=lambda x: x.value_usd, reverse=True)
        
        # Determine dominant chain
        dominant_chain = exposures[0].chain if exposures else None
        dominant_percentage = exposures[0].percentage / 100 if exposures else 0
        
        # Calculate diversity score
        diversity_score = self._calculate_diversity_score(
            dominant_percentage,
            len(exposures)
        )
        
        return ChainExposureAnalysis(
            exposures=exposures,
            diversity_score=diversity_score,
            dominant_chain=dominant_chain
        )
    
    def _calculate_diversity_score(
        self, 
        dominant_percentage: float, 
        chain_count: int
    ) -> str:
        """
        Calculate chain diversity score.
        
        Factors:
        - Dominance of largest chain
        - Number of chains
        """
        if chain_count == 1:
            return "low"
        
        if dominant_percentage < self.HIGH_DIVERSITY_THRESHOLD:
            return "high"
        elif dominant_percentage < self.LOW_DIVERSITY_THRESHOLD:
            return "moderate"
        else:
            return "low"
    
    def get_diversification_recommendations(
        self, 
        analysis: ChainExposureAnalysis
    ) -> List[str]:
        """
        Generate recommendations for chain diversification.
        """
        recommendations = []
        
        if not analysis.exposures:
            recommendations.append("Add wallets to start tracking chain exposure")
            return recommendations
        
        chain_count = len(analysis.exposures)
        dominant = analysis.exposures[0] if analysis.exposures else None
        
        if analysis.diversity_score == "low":
            if chain_count == 1:
                recommendations.append(
                    f"Your portfolio is entirely on {dominant.chain.title()}. "
                    f"Consider adding wallets from other chains for diversification."
                )
            else:
                recommendations.append(
                    f"{dominant.chain.title()} represents {dominant.percentage:.1f}% of your portfolio. "
                    f"Consider rebalancing to reduce single-chain risk."
                )
                
        elif analysis.diversity_score == "moderate":
            recommendations.append(
                f"Your portfolio has moderate chain diversification across {chain_count} chain(s)."
            )
            if dominant:
                recommendations.append(
                    f"Monitor {dominant.chain.title()} exposure ({dominant.percentage:.1f}%)"
                )
                
        else:  # high diversity
            recommendations.append(
                f"Good chain diversification across {chain_count} chain(s)!"
            )
        
        # Suggest specific chains if very concentrated
        if chain_count < 2:
            popular_chains = ["Solana", "Aptos", "Ethereum", "Polygon"]
            current_chain = dominant.chain.title() if dominant else ""
            other_chains = [c for c in popular_chains if c != current_chain]
            
            if other_chains:
                recommendations.append(
                    f"Consider adding wallets from: {', '.join(other_chains[:2])}"
                )
        
        return recommendations
    
    def calculate_chain_diversity_score(self, exposures: List[ChainExposure]) -> float:
        """
        Calculate a 0-1 diversity score based on chain distribution.
        
        Uses inverse of dominance - more chains with balanced distribution = higher score.
        
        Returns:
            Float between 0 (single chain) and 1 (perfectly balanced multi-chain)
        """
        if not exposures or len(exposures) == 1:
            return 0.0
        
        # Calculate entropy-based diversity
        # Higher entropy = more diverse
        percentages = [e.percentage / 100 for e in exposures]
        
        # Shannon entropy
        entropy = -sum(p * math.log2(p) if p > 0 else 0 for p in percentages)
        
        # Normalize by max possible entropy (log2 of number of chains)
        max_entropy = math.log2(len(exposures))
        
        if max_entropy == 0:
            return 0.0
        
        return entropy / max_entropy


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def format_chain_exposure_message(
    dominant_chain: str, 
    percentage: float, 
    chain_count: int
) -> str:
    """
    Generate user-friendly chain exposure message.
    """
    if chain_count == 1:
        return f"Portfolio entirely on {dominant_chain.title()}"
    else:
        return f"{dominant_chain.title()} dominant ({percentage:.1f}%) across {chain_count} chains"


def get_chain_emoji(chain: str) -> str:
    """
    Get emoji representation for blockchain.
    """
    emojis = {
        "solana": "◎",
        "aptos": "⬢",
        "ethereum": "Ξ",
        "polygon": "⬡",
        "base": "🔵",
        "avalanche": "🔺",
        "arbitrum": "🔷",
    }
    return emojis.get(chain.lower(), "⛓️")


def get_chain_color(chain: str) -> str:
    """
    Get color code for blockchain (for frontend styling).
    """
    colors = {
        "solana": "#8b5cf6",    # purple-500
        "aptos": "#3b82f6",     # blue-500
        "ethereum": "#6366f1",  # indigo-500
        "polygon": "#8b5cf6",   # purple-500
        "base": "#3b82f6",      # blue-500
        "avalanche": "#ef4444", # red-500
        "arbitrum": "#0ea5e9",  # sky-500
    }
    return colors.get(chain.lower(), "#6b7280")  # gray-500 default