# app/schemas/chat.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal

# ============================================================
# Chat Request Models
# ============================================================

class ChatRequest(BaseModel):
    """
    Chat request with scope parameter.
    
    Scope options:
    - "all": Use all user's wallets (default)
    - "primary": Use only the primary wallet
    - "0x...": Use a specific wallet address (if user owns it)
    """
    question: str = Field(..., min_length=1, max_length=1000, description="User's question about their portfolio")
    scope: str = Field(default="all", description="Which wallets to analyze: 'all', 'primary', or specific address")
    
    @validator('scope')
    def validate_scope(cls, v):
        """Validate scope parameter."""
        if not v:
            return "all"
        
        v = v.strip().lower()
        
        # Valid options: "all", "primary", or a wallet address
        if v in ["all", "primary"]:
            return v
        
        # If it's not a keyword, assume it's a wallet address
        # Basic validation: should start with 0x
        if v.startswith("0x"):
            return v
        
        # If it doesn't start with 0x, add it
        return f"0x{v}"
    
    @validator('question')
    def validate_question(cls, v):
        """Ensure question is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What tokens do I hold?",
                "scope": "all"
            }
        }


# ============================================================
# Wallet Result Models
# ============================================================

class WalletPortfolioResult(BaseModel):
    """
    Result for a single wallet's portfolio fetch.
    Includes success status and error details if failed.
    """
    address: str = Field(..., description="Wallet address")
    label: str = Field(..., description="User-friendly wallet name")
    success: bool = Field(..., description="Whether portfolio was fetched successfully")
    error: Optional[str] = Field(None, description="Error message if fetch failed")
    data: Optional[Dict[str, Any]] = Field(None, description="Portfolio data if successful")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "address": "0x06c52...",
                    "label": "Main Wallet",
                    "success": True,
                    "error": None,
                    "data": {
                        "balances": [...],
                        "total_usd_value": 1234.56
                    }
                },
                {
                    "address": "0x123...",
                    "label": "Trading Wallet",
                    "success": False,
                    "error": "Failed to fetch account resources: HTTP 404",
                    "data": None
                }
            ]
        }


# ============================================================
# Aggregated Portfolio Models
# ============================================================

class TokenAggregate(BaseModel):
    """Aggregated token holdings across all wallets."""
    symbol: str
    total_amount: float
    total_usd_value: float
    wallet_count: int = Field(..., description="Number of wallets holding this token")


class AggregatedPortfolio(BaseModel):
    """
    Combined portfolio data across multiple wallets.
    """
    total_usd_value: float = Field(..., description="Total USD value across all wallets")
    total_wallets: int = Field(..., description="Total number of wallets analyzed")
    successful_wallets: int = Field(..., description="Number of wallets successfully fetched")
    failed_wallets: int = Field(..., description="Number of wallets that failed to fetch")
    by_token: List[TokenAggregate] = Field(default_factory=list, description="Aggregated holdings by token")
    wallets: List[Dict[str, Any]] = Field(default_factory=list, description="Individual wallet data")


# ============================================================
# Chat Response Models
# ============================================================

class ChatResponse(BaseModel):
    """
    Enhanced chat response with detailed wallet results.
    """
    answer: str = Field(..., description="AI-generated answer to the user's question")
    portfolio: AggregatedPortfolio = Field(..., description="Aggregated portfolio data")
    wallet_results: List[WalletPortfolioResult] = Field(..., description="Detailed results for each wallet")
    scope_used: str = Field(..., description="The scope that was actually used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "You hold a total of 50.5 APT across 2 wallets, valued at approximately $356.52. You also have 1,000 USDC worth $1,000.",
                "portfolio": {
                    "total_usd_value": 1356.52,
                    "total_wallets": 3,
                    "successful_wallets": 2,
                    "failed_wallets": 1,
                    "by_token": [
                        {
                            "symbol": "APT",
                            "total_amount": 50.5,
                            "total_usd_value": 356.52,
                            "wallet_count": 2
                        },
                        {
                            "symbol": "USDC",
                            "total_amount": 1000.0,
                            "total_usd_value": 1000.0,
                            "wallet_count": 1
                        }
                    ],
                    "wallets": [...]
                },
                "wallet_results": [...],
                "scope_used": "all"
            }
        }