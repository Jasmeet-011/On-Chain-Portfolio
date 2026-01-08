# app/services/adapters/aptos_adapter.py
import httpx
import re
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, getcontext
from urllib.parse import quote

from .base import ChainAdapter


class AptosAdapter(ChainAdapter):
    """
    Adapter for Aptos blockchain.
    
    Refactored from the original AptosClient to implement ChainAdapter interface.
    """
    
    # Token registry for known Aptos tokens
    TOKEN_REGISTRY = {
        "0x1::aptos_coin::AptosCoin": ("APT", 8),
        # Add more as needed:
        # "0x...::usdc::USDC": ("USDC", 6),
        # "0x...::usdt::USDT": ("USDT", 6),
    }
    
    def __init__(self, rpc_url: str):
        """
        Initialize Aptos adapter.
        
        Args:
            rpc_url: Aptos fullnode REST API endpoint
                     e.g., "https://fullnode.testnet.aptoslabs.com/v1"
        """
        super().__init__(rpc_url)
        self._client = httpx.Client(base_url=self.rpc_url.rstrip("/"), timeout=30.0)
    
    def get_chain_name(self) -> str:
        """Return chain identifier."""
        return "aptos"
    
    def get_native_token_symbol(self) -> str:
        """Return native token symbol."""
        return "APT"
    
    def get_native_token_decimals(self) -> int:
        """Return native token decimals."""
        return 8
    
    # ============================================================
    # Address Validation
    # ============================================================
    
    def validate_address(self, address: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Aptos address format.
        
        Rules:
        - Must start with 0x
        - Must contain only hexadecimal characters (0-9, a-f, A-F)
        - Must be between 1-64 hex characters (after 0x)
        """
        if not address:
            return False, "Address cannot be empty"
        
        addr = address.strip()
        
        if not addr.lower().startswith("0x"):
            return False, "Address must start with '0x'"
        
        hex_part = addr[2:]
        
        if len(hex_part) == 0:
            return False, "Address must have at least one character after '0x'"
        
        if len(hex_part) > 64:
            return False, "Address cannot be longer than 64 hex characters"
        
        if not re.match(r'^[0-9a-fA-F]+$', hex_part):
            return False, "Address must contain only hexadecimal characters"
        
        return True, None
    
    def normalize_address(self, address: str) -> str:
        """Normalize to lowercase with 0x prefix."""
        addr = address.lower().strip()
        if not addr.startswith("0x"):
            addr = "0x" + addr
        return addr
    
    def verify_on_chain(self, address: str) -> Tuple[bool, Optional[str]]:
        """
        Check if address exists on Aptos blockchain.
        
        Returns:
            (True, None) if exists, (False, error) if not
        """
        try:
            normalized = self.normalize_address(address)
            resources = self.get_account_resources(normalized)
            
            # If we get a list, account exists
            if isinstance(resources, list):
                return True, None
            
            return False, "Address not found on Aptos blockchain"
        except Exception as e:
            # If there's an error, log but don't fail validation
            print(f"[WARN] Could not verify Aptos address on-chain: {e}")
            return True, None
    
    # ============================================================
    # Balance Fetching
    # ============================================================
    
    def get_balance(self, address: str, token_identifier: Optional[str] = None) -> Optional[int]:
        """
        Get raw token balance for Aptos address.
        
        Args:
            address: Aptos address
            token_identifier: Coin type (e.g., "0x1::aptos_coin::AptosCoin")
                             If None, returns APT balance
        
        Returns:
            Raw balance as integer, or None if not found
        """
        if token_identifier is None:
            token_identifier = "0x1::aptos_coin::AptosCoin"
        
        addr = self.normalize_address(address)
        encoded_asset = quote(token_identifier, safe="")
        
        try:
            url = f"/accounts/{addr}/balance/{encoded_asset}"
            response = self._client.get(url)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            balance_data = response.json()
            
            if isinstance(balance_data, dict):
                return int(balance_data.get("balance") or balance_data.get("amount") or "0")
            else:
                return int(balance_data)
        
        except Exception as e:
            print(f"[ERROR] Failed to get Aptos balance: {e}")
            return None
    
    def get_token_balances(self, address: str) -> List[Dict[str, Any]]:
        """
        Get all token balances for Aptos address.
        
        Returns:
            List of token balance dictionaries
        """
        balances = []
        
        for asset_type, (symbol, decimals) in self.TOKEN_REGISTRY.items():
            try:
                balance_raw = self.get_balance(address, asset_type)
                
                if balance_raw is None or balance_raw == 0:
                    continue
                
                amount = self.normalize_amount(str(balance_raw), decimals)
                
                balances.append({
                    "symbol": symbol,
                    "address": asset_type,
                    "decimals": decimals,
                    "raw": str(balance_raw),
                    "amount": float(amount)
                })
            
            except Exception as e:
                print(f"[ERROR] Failed to fetch {symbol} balance: {e}")
                continue
        
        return balances
    
    def get_portfolio(self, address: str) -> Dict[str, Any]:
        """
        Get complete portfolio for Aptos address.
        
        Returns:
            Portfolio dictionary with chain, address, balances
        """
        normalized_addr = self.normalize_address(address)
        balances = self.get_token_balances(normalized_addr)
        
        # Get native balance separately for metadata
        native_raw = self.get_balance(normalized_addr)
        native_balance = None
        
        if native_raw is not None:
            native_amount = self.normalize_amount(str(native_raw), 8)
            native_balance = {
                "symbol": "APT",
                "amount": float(native_amount),
                "raw": str(native_raw),
                "decimals": 8
            }
        
        return {
            "chain": "aptos",
            "address": normalized_addr,
            "balances": balances,
            "native_balance": native_balance,
            # Note: USD values added by price service layer
        }
    
    # ============================================================
    # Transaction Fetching
    # ============================================================
    
    def get_transactions(
        self, 
        address: str, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history for Aptos address.
        
        Args:
            address: Aptos address
            limit: Max transactions to return
            offset: Pagination offset
            
        Returns:
            List of transaction dictionaries
        """
        addr = self.normalize_address(address)
        
        try:
            url = f"/accounts/{addr}/transactions"
            params = {"limit": limit, "start": offset}
            
            response = self._client.get(url, params=params)
            
            if response.status_code == 404:
                return []
            
            response.raise_for_status()
            raw_txns = response.json()
            
            # Filter to user transactions only
            user_txns = [
                txn for txn in raw_txns 
                if txn.get("type") == "user_transaction"
            ]
            
            return user_txns
        
        except Exception as e:
            print(f"[ERROR] Failed to fetch Aptos transactions: {e}")
            return []
    
    # ============================================================
    # Helper Methods (Internal)
    # ============================================================
    
    def get_account_resources(self, address: str) -> List[Dict[str, Any]]:
        """
        Fetch all resources for an Aptos account.
        
        Internal method used for on-chain verification.
        """
        addr = self.normalize_address(address)
        
        try:
            response = self._client.get(f"/accounts/{addr}/resources")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise
        except Exception as e:
            raise Exception(f"Failed to fetch account resources: {str(e)}")
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass