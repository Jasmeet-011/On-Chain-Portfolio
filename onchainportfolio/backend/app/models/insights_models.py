# backend/app/models/insights_models.py
"""
Portfolio Insights Models - MVP5

Pydantic models for advanced portfolio intelligence.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# ============================================================
# CHAIN EXPOSURE MODELS
# ============================================================

class ChainExposure(BaseModel):
    """Individual chain exposure."""
    chain: str
    value_usd: float
    percentage: float
    wallet_count: int


class ChainExposureAnalysis(BaseModel):
    """Complete chain exposure analysis."""
    exposures: List[ChainExposure]
    diversity_score: str  # "low", "moderate", "high"
    dominant_chain: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "exposures": [
                    {
                        "chain": "solana",
                        "value_usd": 1250.50,
                        "percentage": 65.2,
                        "wallet_count": 2
                    }
                ],
                "diversity_score": "moderate",
                "dominant_chain": "solana"
            }
        }


# ============================================================
# CONCENTRATION MODELS
# ============================================================

class ConcentrationWarning(BaseModel):
    """Warning for concentrated token holdings."""
    token_symbol: str
    percentage: float
    risk_level: str  # "high", "moderate"
    message: str


class ConcentrationAnalysis(BaseModel):
    """Portfolio concentration analysis."""
    overall_risk: str  # "low", "moderate", "high"
    warnings: List[ConcentrationWarning]
    token_count: int
    herfindahl_index: float  # 0-1, higher = more concentrated
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_risk": "moderate",
                "warnings": [
                    {
                        "token_symbol": "SOL",
                        "percentage": 45.2,
                        "risk_level": "high",
                        "message": "SOL represents 45.2% of your portfolio"
                    }
                ],
                "token_count": 5,
                "herfindahl_index": 0.2847
            }
        }


# ============================================================
# VOLATILITY MODELS
# ============================================================

class VolatilityBreakdown(BaseModel):
    """Stablecoin vs volatile asset breakdown."""
    stablecoins: Dict[str, float]  # {"value_usd": 500, "percentage": 25}
    volatile: Dict[str, float]      # {"value_usd": 1500, "percentage": 75}
    risk_label: str  # "balanced", "moderate", "high"
    stablecoin_list: List[str]  # List of stablecoin symbols held
    
    class Config:
        json_schema_extra = {
            "example": {
                "stablecoins": {
                    "value_usd": 500.0,
                    "percentage": 25.0
                },
                "volatile": {
                    "value_usd": 1500.0,
                    "percentage": 75.0
                },
                "risk_label": "balanced",
                "stablecoin_list": ["USDC", "USDT"]
            }
        }


# ============================================================
# TOKEN DOMINANCE MODELS
# ============================================================

class TokenDominance(BaseModel):
    """Individual token dominance ranking."""
    symbol: str
    value_usd: float
    percentage: float
    rank: int
    chain: str


class TokenDominanceList(BaseModel):
    """Complete token dominance rankings."""
    tokens: List[TokenDominance]
    total_tokens: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "tokens": [
                    {
                        "symbol": "SOL",
                        "value_usd": 1000.0,
                        "percentage": 50.0,
                        "rank": 1,
                        "chain": "solana"
                    }
                ],
                "total_tokens": 5
            }
        }


# ============================================================
# COMBINED INSIGHTS RESPONSE
# ============================================================

class PortfolioInsights(BaseModel):
    """
    Complete portfolio intelligence insights.
    
    Combines all MVP5 analyses into single response.
    """
    chain_exposure: ChainExposureAnalysis
    concentration: ConcentrationAnalysis
    volatility: VolatilityBreakdown
    token_dominance: TokenDominanceList
    
    # Summary metrics
    total_value_usd: float
    total_tokens: int
    total_wallets: int
    
    # High-level insights
    overall_risk_score: str  # "low", "moderate", "high"
    key_insights: List[str]  # Top 3-5 insights
    recommendations: List[str]  # Top 3-5 recommendations
    
    class Config:
        json_schema_extra = {
            "example": {
                "chain_exposure": {},
                "concentration": {},
                "volatility": {},
                "token_dominance": {},
                "total_value_usd": 2000.0,
                "total_tokens": 5,
                "total_wallets": 2,
                "overall_risk_score": "moderate",
                "key_insights": [
                    "Portfolio concentrated in Solana (65%)",
                    "SOL dominates at 45% of portfolio",
                    "Low stablecoin allocation (15%)"
                ],
                "recommendations": [
                    "Increase stablecoin allocation to 25-30%",
                    "Consider adding Aptos exposure",
                    "Reduce SOL concentration below 40%"
                ]
            }
        }


# ============================================================
# PERFORMANCE MODELS (for future use)
# ============================================================

class PerformanceSummary(BaseModel):
    """Portfolio performance summary."""
    period: str  # "24h", "7d", "30d", "90d"
    total_change_usd: float
    total_change_percent: float
    best_performer: Optional[TokenDominance] = None
    worst_performer: Optional[TokenDominance] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": "7d",
                "total_change_usd": 125.50,
                "total_change_percent": 6.8,
                "best_performer": {
                    "symbol": "APT",
                    "value_usd": 500.0,
                    "percentage": 25.0,
                    "rank": 2,
                    "chain": "aptos"
                },
                "worst_performer": None
            }
        }