# app/services/transaction_parser.py
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation

logger = logging.getLogger("chainlens.services.transaction_parser")

class TransactionParser:
    """
    Service for parsing Aptos transaction payloads to extract detailed information.
    
    Handles:
    - Transfer amounts and recipients
    - Swap details (tokens, amounts)
    - Stake/unstake amounts
    - NFT transfers
    - Contract calls
    """
    
    @staticmethod
    def parse_transaction(raw_txn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a raw Aptos transaction and extract detailed information.
        
        Args:
            raw_txn: Raw transaction dict from Aptos API
            
        Returns:
            Parsed transaction with enhanced details
        """
        parsed = {
            "hash": raw_txn.get("hash", ""),
            "version": str(raw_txn.get("version", "")),
            "success": raw_txn.get("success", False),
            "timestamp": str(raw_txn.get("timestamp", "")),
            "gas_used": int(raw_txn.get("gas_used", 0)),
            "sender": raw_txn.get("sender", ""),
            "sequence_number": raw_txn.get("sequence_number", 0),
            "type": "Unknown",
            "category": "unknown",
            "details": {}
        }
        
        # Parse payload for details
        payload = raw_txn.get("payload", {})
        if payload and isinstance(payload, dict):
            function = payload.get("function", "")
            
            if function:
                # Parse based on function
                parsed.update(TransactionParser._parse_by_function(function, payload, raw_txn))
            else:
                parsed["type"] = "Script"
                parsed["category"] = "script"
        
        # Try to extract events for additional details
        events = raw_txn.get("events", [])
        if events:
            parsed = TransactionParser._enhance_with_events(parsed, events)
        
        return parsed
    
    @staticmethod
    def _parse_by_function(function: str, payload: Dict[str, Any], raw_txn: Dict[str, Any]) -> Dict[str, Any]:
        """Parse transaction based on function name."""
        func_lower = function.lower()
        
        # Transfer
        if "transfer" in func_lower or "coin::transfer" in func_lower:
            return TransactionParser._parse_transfer(function, payload, raw_txn)
        
        # Swap
        elif "swap" in func_lower:
            return TransactionParser._parse_swap(function, payload, raw_txn)
        
        # Stake
        elif "stake" in func_lower or "delegation_pool" in func_lower:
            return TransactionParser._parse_stake(function, payload, raw_txn)
        
        # Mint (NFT or token)
        elif "mint" in func_lower:
            return TransactionParser._parse_mint(function, payload, raw_txn)
        
        # Default: Contract call
        else:
            return {
                "type": "Contract Call",
                "category": "contract",
                "function": function,
                "details": {
                    "function": function,
                    "arguments": payload.get("arguments", [])
                }
            }
    
    @staticmethod
    def _parse_transfer(function: str, payload: Dict[str, Any], raw_txn: Dict[str, Any]) -> Dict[str, Any]:
        """Parse coin transfer transaction."""
        args = payload.get("arguments", [])
        type_args = payload.get("type_arguments", [])
        
        # Extract recipient
        recipient = args[0] if len(args) > 0 else "Unknown"
        
        # Extract amount (raw)
        amount_raw = args[1] if len(args) > 1 else "0"
        
        # Determine coin type
        coin_type = type_args[0] if type_args else "0x1::aptos_coin::AptosCoin"
        symbol = TransactionParser._extract_coin_symbol(coin_type)
        
        # Normalize amount
        decimals = 8 if symbol == "APT" else 6  # Default decimals
        try:
            amount = Decimal(amount_raw) / (Decimal(10) ** decimals)
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.debug("Failed to parse transfer amount: %s", e)
            amount = Decimal(0)
        
        return {
            "type": "Transfer",
            "category": "transfer",
            "function": function,
            "details": {
                "recipient": recipient,
                "amount": float(amount),
                "amount_raw": amount_raw,
                "symbol": symbol,
                "coin_type": coin_type,
                "direction": "sent"  # Always sent for user transactions
            }
        }
    
    @staticmethod
    def _parse_swap(function: str, payload: Dict[str, Any], raw_txn: Dict[str, Any]) -> Dict[str, Any]:
        """Parse swap transaction."""
        args = payload.get("arguments", [])
        type_args = payload.get("type_arguments", [])
        
        from_coin = type_args[0] if len(type_args) > 0 else "Unknown"
        to_coin = type_args[1] if len(type_args) > 1 else "Unknown"
        
        from_symbol = TransactionParser._extract_coin_symbol(from_coin)
        to_symbol = TransactionParser._extract_coin_symbol(to_coin)
        
        # Try to extract amounts from args
        from_amount_raw = args[0] if len(args) > 0 else "0"
        min_out_raw = args[1] if len(args) > 1 else "0"
        
        return {
            "type": "Swap",
            "category": "swap",
            "function": function,
            "details": {
                "from_coin": from_symbol,
                "to_coin": to_symbol,
                "from_coin_type": from_coin,
                "to_coin_type": to_coin,
                "from_amount_raw": from_amount_raw,
                "min_out_raw": min_out_raw
            }
        }
    
    @staticmethod
    def _parse_stake(function: str, payload: Dict[str, Any], raw_txn: Dict[str, Any]) -> Dict[str, Any]:
        """Parse staking transaction."""
        args = payload.get("arguments", [])
        
        # Determine stake action
        if "add_stake" in function.lower():
            action = "stake"
        elif "unlock" in function.lower():
            action = "unstake"
        elif "withdraw" in function.lower():
            action = "withdraw"
        else:
            action = "stake"
        
        # Extract amount
        amount_raw = args[1] if len(args) > 1 else "0"
        
        try:
            amount = Decimal(amount_raw) / (Decimal(10) ** 8)  # APT decimals
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.debug("Failed to parse stake amount: %s", e)
            amount = Decimal(0)
        
        return {
            "type": "Stake",
            "category": "stake",
            "function": function,
            "details": {
                "action": action,
                "amount": float(amount),
                "amount_raw": amount_raw,
                "symbol": "APT",
                "pool": args[0] if len(args) > 0 else None
            }
        }
    
    @staticmethod
    def _parse_mint(function: str, payload: Dict[str, Any], raw_txn: Dict[str, Any]) -> Dict[str, Any]:
        """Parse mint transaction (NFT or token)."""
        args = payload.get("arguments", [])
        
        # Check if it's NFT or token mint
        if "token" in function.lower() and "nft" not in function.lower():
            # Token mint
            amount_raw = args[1] if len(args) > 1 else "0"
            
            return {
                "type": "Mint",
                "category": "mint",
                "function": function,
                "details": {
                    "mint_type": "token",
                    "amount_raw": amount_raw
                }
            }
        else:
            # NFT mint
            return {
                "type": "NFT Mint",
                "category": "nft",
                "function": function,
                "details": {
                    "mint_type": "nft",
                    "collection": args[0] if len(args) > 0 else "Unknown"
                }
            }
    
    @staticmethod
    def _enhance_with_events(parsed: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance transaction details using events."""
        # Look for withdraw/deposit events to get actual amounts
        for event in events:
            event_type = event.get("type", "")
            data = event.get("data", {})
            
            # Withdraw event (sent)
            if "WithdrawEvent" in event_type or "withdraw" in event_type.lower():
                if "amount" in data and parsed["category"] == "transfer":
                    parsed["details"]["amount_from_event"] = data["amount"]
            
            # Deposit event (received)
            elif "DepositEvent" in event_type or "deposit" in event_type.lower():
                if "amount" in data:
                    parsed["details"]["received_amount"] = data["amount"]
            
            # Swap events
            elif "swap" in event_type.lower():
                if parsed["category"] == "swap":
                    parsed["details"]["event_data"] = data
        
        return parsed
    
    @staticmethod
    def _extract_coin_symbol(coin_type: str) -> str:
        """Extract coin symbol from coin type."""
        if "aptos_coin::AptosCoin" in coin_type:
            return "APT"
        elif "usdc" in coin_type.lower():
            return "USDC"
        elif "usdt" in coin_type.lower():
            return "USDT"
        else:
            # Try to extract from type string
            parts = coin_type.split("::")
            return parts[-1] if parts else "Unknown"
    
    @staticmethod
    def calculate_usd_value(amount: float, symbol: str, prices: Dict[str, float]) -> Optional[float]:
        """Calculate USD value for a transaction."""
        if symbol in prices and prices[symbol]:
            return amount * prices[symbol]
        return None