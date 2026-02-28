# # backend/app/services/alert_checker.py - 3-TIER ALERT CHECKING

# from typing import List, Dict, Optional
# from datetime import datetime
# import logging

# logger = logging.getLogger(__name__)


# class AlertChecker:
#     """
#     Checks and triggers alerts across all 3 tiers:
#     - Portfolio alerts
#     - Token alerts  
#     - Wallet alerts
#     """
    
#     def __init__(self, db, price_service, email_service):
#         self.db = db
#         self.price_service = price_service
#         self.email_service = email_service
    
    
#     # ========================================================================
#     # TIER 1: PORTFOLIO ALERTS
#     # ========================================================================
    
#     async def check_portfolio_alerts(self, user_id: str) -> List[Dict]:
#         """
#         Check all portfolio-level alerts for a user
        
#         Returns list of triggered alerts
#         """
#         # Get all active portfolio alerts
#         alerts = await self.db.alerts.find({
#             "user_id": user_id,
#             "alert_type": "portfolio",
#             "is_active": True
#         }).to_list(None)
        
#         if not alerts:
#             return []
        
#         triggered = []
        
#         # Get user's complete portfolio data
#         portfolio_data = await self._get_user_portfolio(user_id)
        
#         for alert in alerts:
#             try:
#                 metric = alert.get("portfolio_metric")
                
#                 if metric == "value":
#                     current_value = portfolio_data["total_value"]
#                     if self._check_condition(
#                         current_value, 
#                         alert["condition"], 
#                         alert["target_value"]
#                     ):
#                         triggered.append(await self._trigger_portfolio_alert(
#                             alert, 
#                             current_value, 
#                             portfolio_data
#                         ))
                
#                 elif metric == "change_percent":
#                     change = await self._calculate_portfolio_change(user_id, "24h")
#                     if abs(change) >= alert["target_value"]:
#                         triggered.append(await self._trigger_portfolio_alert(
#                             alert, 
#                             change, 
#                             portfolio_data
#                         ))
                
#                 elif metric == "risk_level":
#                     risk_level = await self._calculate_risk_level(user_id)
#                     # Convert risk levels to numeric: low=1, moderate=2, high=3
#                     risk_map = {"low": 1, "moderate": 2, "high": 3}
#                     current_risk = risk_map.get(risk_level, 0)
#                     target_risk = risk_map.get(alert["target_value"], 0)
                    
#                     if current_risk >= target_risk:
#                         triggered.append(await self._trigger_portfolio_alert(
#                             alert, 
#                             risk_level, 
#                             portfolio_data
#                         ))
                
#                 elif metric == "concentration":
#                     concentration = await self._calculate_max_concentration(user_id)
#                     if concentration >= alert["target_value"]:
#                         triggered.append(await self._trigger_portfolio_alert(
#                             alert, 
#                             concentration, 
#                             portfolio_data
#                         ))
                
#             except Exception as e:
#                 logger.error(f"Error checking portfolio alert {alert['_id']}: {e}")
        
#         return triggered
    
    
#     # ========================================================================
#     # TIER 2: TOKEN ALERTS
#     # ========================================================================
    
#     async def check_token_alerts(self, user_id: str) -> List[Dict]:
#         """
#         Check all token price alerts for a user
        
#         Handles both:
#         - Global token alerts (all wallets)
#         - Wallet-specific token alerts
        
#         Returns list of triggered alerts
#         """
#         # Get all active token alerts
#         alerts = await self.db.alerts.find({
#             "user_id": user_id,
#             "alert_type": "token",
#             "is_active": True
#         }).to_list(None)
        
#         if not alerts:
#             return []
        
#         triggered = []
        
#         for alert in alerts:
#             try:
#                 token_symbol = alert["token_symbol"]
                
#                 # Get current token price
#                 price = await self.price_service.get_token_price(token_symbol)
                
#                 if not price:
#                     continue
                
#                 # Check if price condition is met
#                 if not self._check_condition(
#                     price, 
#                     alert["condition"], 
#                     alert["target_price"]
#                 ):
#                     continue
                
#                 # Get user's holdings of this token
#                 if alert.get("wallet_address"):
#                     # Specific wallet only
#                     holdings = await self._get_token_holdings_in_wallet(
#                         user_id,
#                         token_symbol,
#                         alert["wallet_address"]
#                     )
#                 else:
#                     # All wallets
#                     holdings = await self._get_token_holdings_all_wallets(
#                         user_id,
#                         token_symbol
#                     )
                
#                 if holdings["total_amount"] > 0:
#                     triggered.append(await self._trigger_token_alert(
#                         alert,
#                         price,
#                         holdings
#                     ))
            
#             except Exception as e:
#                 logger.error(f"Error checking token alert {alert['_id']}: {e}")
        
#         return triggered
    
    
#     # ========================================================================
#     # TIER 3: WALLET ALERTS
#     # ========================================================================
    
#     async def check_wallet_alerts(self, user_id: str) -> List[Dict]:
#         """
#         Check all wallet-specific alerts for a user
        
#         Returns list of triggered alerts
#         """
#         # Get all active wallet alerts
#         alerts = await self.db.alerts.find({
#             "user_id": user_id,
#             "alert_type": "wallet",
#             "is_active": True
#         }).to_list(None)
        
#         if not alerts:
#             return []
        
#         triggered = []
        
#         for alert in alerts:
#             try:
#                 wallet_address = alert["wallet_address"]
                
#                 # Get current wallet value
#                 wallet_data = await self._get_wallet_value(user_id, wallet_address)
#                 current_value = wallet_data["total_value"]
                
#                 # Check if condition is met
#                 if self._check_condition(
#                     current_value,
#                     alert["condition"],
#                     alert["target_value"]
#                 ):
#                     triggered.append(await self._trigger_wallet_alert(
#                         alert,
#                         current_value,
#                         wallet_data
#                     ))
            
#             except Exception as e:
#                 logger.error(f"Error checking wallet alert {alert['_id']}: {e}")
        
#         return triggered
    
    
#     # ========================================================================
#     # HELPER FUNCTIONS
#     # ========================================================================
    
#     def _check_condition(self, current: float, condition: str, target: float) -> bool:
#         """Check if alert condition is met"""
#         if condition == "above":
#             return current >= target
#         elif condition == "below":
#             return current <= target
#         elif condition == "equals":
#             # Allow 1% tolerance for equals
#             return abs(current - target) / target < 0.01
#         return False
    
#     async def _get_user_portfolio(self, user_id: str) -> Dict:
#         """Get complete portfolio data for user"""
#         # Fetch all user wallets
#         wallets = await self.db.wallets.find({"user_id": user_id}).to_list(None)
        
#         total_value = 0
#         all_balances = []
        
#         for wallet in wallets:
#             # Get portfolio for each wallet
#             portfolio = await self._get_wallet_portfolio(
#                 wallet["address"],
#                 wallet["chain"]
#             )
#             total_value += portfolio.get("total_usd_value", 0)
#             all_balances.extend(portfolio.get("balances", []))
        
#         return {
#             "total_value": total_value,
#             "wallet_count": len(wallets),
#             "balances": all_balances
#         }
    
#     async def _get_token_holdings_all_wallets(
#         self, 
#         user_id: str, 
#         token_symbol: str
#     ) -> Dict:
#         """Get token holdings across all user wallets"""
#         wallets = await self.db.wallets.find({"user_id": user_id}).to_list(None)
        
#         total_amount = 0
#         total_value = 0
#         wallets_with_token = []
        
#         for wallet in wallets:
#             portfolio = await self._get_wallet_portfolio(
#                 wallet["address"],
#                 wallet["chain"]
#             )
            
#             # Find token in this wallet
#             for balance in portfolio.get("balances", []):
#                 if balance["symbol"] == token_symbol:
#                     total_amount += balance["amount"]
#                     total_value += balance.get("usd_value", 0)
#                     wallets_with_token.append({
#                         "address": wallet["address"],
#                         "label": wallet.get("label"),
#                         "chain": wallet["chain"],
#                         "amount": balance["amount"],
#                         "value": balance.get("usd_value", 0)
#                     })
        
#         return {
#             "token_symbol": token_symbol,
#             "total_amount": total_amount,
#             "total_value": total_value,
#             "wallet_count": len(wallets_with_token),
#             "wallets": wallets_with_token
#         }
    
#     async def _trigger_portfolio_alert(
#         self, 
#         alert: Dict, 
#         current_value: float,
#         portfolio_data: Dict
#     ) -> Dict:
#         """Trigger a portfolio alert and send notification"""
#         alert_id = str(alert["_id"])
        
#         # Update alert in database
#         await self.db.alerts.update_one(
#             {"_id": alert["_id"]},
#             {
#                 "$set": {
#                     "triggered_at": datetime.utcnow(),
#                     "is_active": False,  # Pause after trigger
#                     "last_checked": datetime.utcnow()
#                 }
#             }
#         )
        
#         # Send email notification
#         await self._send_portfolio_alert_email(alert, current_value, portfolio_data)
        
#         return {
#             "alert_id": alert_id,
#             "alert_type": "portfolio",
#             "triggered_at": datetime.utcnow(),
#             "current_value": current_value
#         }
    
#     async def _trigger_token_alert(
#         self,
#         alert: Dict,
#         current_price: float,
#         holdings: Dict
#     ) -> Dict:
#         """Trigger a token alert and send notification"""
#         alert_id = str(alert["_id"])
        
#         # Update alert
#         await self.db.alerts.update_one(
#             {"_id": alert["_id"]},
#             {
#                 "$set": {
#                     "triggered_at": datetime.utcnow(),
#                     "is_active": False,
#                     "last_checked": datetime.utcnow()
#                 }
#             }
#         )
        
#         # Send email
#         await self._send_token_alert_email(alert, current_price, holdings)
        
#         return {
#             "alert_id": alert_id,
#             "alert_type": "token",
#             "triggered_at": datetime.utcnow(),
#             "current_price": current_price,
#             "holdings": holdings
#         }
    
#     async def _trigger_wallet_alert(
#         self,
#         alert: Dict,
#         current_value: float,
#         wallet_data: Dict
#     ) -> Dict:
#         """Trigger a wallet alert and send notification"""
#         alert_id = str(alert["_id"])
        
#         # Update alert
#         await self.db.alerts.update_one(
#             {"_id": alert["_id"]},
#             {
#                 "$set": {
#                     "triggered_at": datetime.utcnow(),
#                     "is_active": False,
#                     "last_checked": datetime.utcnow()
#                 }
#             }
#         )
        
#         # Send email
#         await self._send_wallet_alert_email(alert, current_value, wallet_data)
        
#         return {
#             "alert_id": alert_id,
#             "alert_type": "wallet",
#             "triggered_at": datetime.utcnow(),
#             "current_value": current_value
#         }
    
#     async def _send_portfolio_alert_email(
#         self,
#         alert: Dict,
#         current_value: float,
#         portfolio_data: Dict
#     ):
#         """Send email for portfolio alert"""
#         # Implementation depends on your email service
#         pass
    
#     async def _send_token_alert_email(
#         self,
#         alert: Dict,
#         current_price: float,
#         holdings: Dict
#     ):
#         """Send email for token alert"""
#         pass
    
#     async def _send_wallet_alert_email(
#         self,
#         alert: Dict,
#         current_value: float,
#         wallet_data: Dict
#     ):
#         """Send email for wallet alert"""
#         pass