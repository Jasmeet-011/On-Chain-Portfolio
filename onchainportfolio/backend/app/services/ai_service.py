# app/services/ai_service.py
import httpx
from typing import Dict, Any, Optional
import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts Decimal to float"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.5-flash"
        
    def chat_with_portfolio(
        self, 
        question: str, 
        portfolio_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Send question + portfolio data to Gemini and get natural language response.
        
        Enhanced to handle:
        - Multiple wallets
        - Failed wallet fetches
        - Aggregated portfolio data
        """
        print(f"[DEBUG] AI Service called with question: {question}")
        
        if not self.api_key:
            print("[ERROR] No API key configured!")
            return None
        
        # Extract portfolio info
        portfolio = portfolio_data.get("portfolio", {})
        wallet_results = portfolio_data.get("wallet_results", [])
        has_failures = portfolio_data.get("has_failures", False)
        
        # Build the system prompt
        system_prompt = """You are a helpful crypto portfolio assistant for the Aptos blockchain. 
You have access to a user's on-chain portfolio data across multiple wallets. 
Answer their questions clearly and concisely based on this data.
Focus on being accurate with numbers and helpful with insights.

When multiple wallets are involved:
- Provide totals across all wallets
- Mention if data is aggregated from multiple wallets
- Be clear about which tokens are held where if relevant

If some wallets failed to fetch:
- Still provide information from successful wallets
- Briefly mention that some wallets couldn't be analyzed
- Don't dwell on failures unless asked"""

        # Build detailed portfolio summary
        portfolio_summary = []
        
        # Overall stats
        total_wallets = portfolio.get("total_wallets", 0)
        successful = portfolio.get("successful_wallets", 0)
        failed = portfolio.get("failed_wallets", 0)
        total_usd = portfolio.get("total_usd_value", 0)
        
        portfolio_summary.append(f"Portfolio Overview:")
        portfolio_summary.append(f"- Total wallets analyzed: {total_wallets}")
        portfolio_summary.append(f"- Successfully fetched: {successful}")
        if failed > 0:
            portfolio_summary.append(f"- Failed to fetch: {failed}")
        portfolio_summary.append(f"- Total USD value: ${total_usd:,.2f}")
        
        # Token aggregates
        by_token = portfolio.get("by_token", [])
        if by_token:
            portfolio_summary.append(f"\nToken Holdings (Aggregated):")
            for token in by_token:
                symbol = token.get("symbol")
                amount = token.get("total_amount", 0)
                usd_value = token.get("total_usd_value", 0)
                wallet_count = token.get("wallet_count", 0)
                
                portfolio_summary.append(
                    f"- {symbol}: {amount:,.4f} (${usd_value:,.2f}) across {wallet_count} wallet(s)"
                )
        
        # Individual wallet details
        wallets = portfolio.get("wallets", [])
        if len(wallets) > 1:
            portfolio_summary.append(f"\nIndividual Wallet Breakdown:")
            for i, wallet in enumerate(wallets, 1):
                addr = wallet.get("address", "")
                label = wallet.get("label", f"Wallet {i}")
                data = wallet.get("data", {})
                wallet_usd = data.get("total_usd_value", 0)
                
                portfolio_summary.append(f"\n{i}. {label} ({addr[:10]}...):")
                portfolio_summary.append(f"   Total value: ${wallet_usd:,.2f}")
                
                balances = data.get("balances", [])
                if balances:
                    for balance in balances:
                        symbol = balance.get("symbol")
                        amount = balance.get("amount", 0)
                        usd_val = balance.get("usd_value", 0)
                        if symbol:
                            portfolio_summary.append(
                                f"   - {symbol}: {amount:,.4f} (${usd_val:,.2f})"
                            )
        
        # Failed wallets info
        if has_failures:
            failed_wallets = [r for r in wallet_results if not r.get("success", True)]
            if failed_wallets:
                portfolio_summary.append(f"\nNote: {len(failed_wallets)} wallet(s) could not be analyzed:")
                for failed in failed_wallets:
                    label = failed.get("label", "Unknown")
                    addr = failed.get("address", "")
                    portfolio_summary.append(f"- {label} ({addr[:10]}...)")
        
        portfolio_text = "\n".join(portfolio_summary)
        
        # Build user prompt
        user_prompt = f"""User's question: {question}

Portfolio data:
{portfolio_text}

Please answer the user's question based on this portfolio data."""

        try:
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": system_prompt},
                            {"text": user_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500,
                }
            }
            
            print(f"[DEBUG] Sending request to Gemini...")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                
                print(f"[DEBUG] Gemini response status: {response.status_code}")
                
                response.raise_for_status()
                
                data = response.json()
                
                # Extract text from Gemini response
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate:
                        parts = candidate["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            answer = parts[0]["text"]
                            print(f"[DEBUG] Got answer from Gemini: {answer[:100]}...")
                            return answer
                
                print("[ERROR] No valid response from Gemini")
                return None
                
        except Exception as e:
            print(f"[ERROR] AI service failed: {e}")
            import traceback
            traceback.print_exc()
            return None