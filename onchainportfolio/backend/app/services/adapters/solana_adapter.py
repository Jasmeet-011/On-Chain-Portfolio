# app/services/adapters/solana_adapter.py
import httpx
import base58
import logging
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from .base import ChainAdapter

logger = logging.getLogger("chainlens.adapters.solana")


class SolanaAdapter(ChainAdapter):
    """
    Adapter for Solana blockchain.
    
    Supports:
    - SOL balance
    - SPL token balances
    - Transaction history
    - Address validation
    """
    
    # Well-known SPL tokens (add more as needed)
    KNOWN_TOKENS = {
        "So11111111111111111111111111111111111111112": {
            "symbol": "SOL",
            "decimals": 9,
            "name": "Solana"
        },
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
            "symbol": "USDC",
            "decimals": 6,
            "name": "USD Coin"
        },
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
            "symbol": "USDT",
            "decimals": 6,
            "name": "Tether USD"
        },
        # Add more popular SPL tokens here
    }
    
    def __init__(self, rpc_url: str, backup_rpc_url: Optional[str] = None):
        """
        Initialize Solana adapter.
        
        Args:
            rpc_url: Primary Solana RPC endpoint
                     e.g., "https://api.mainnet-beta.solana.com"
            backup_rpc_url: Backup RPC (optional, for failover)
        """
        super().__init__(rpc_url)
        self.backup_rpc_url = backup_rpc_url
        self._client = httpx.Client(timeout=30.0)
    
    def get_chain_name(self) -> str:
        """Return chain identifier."""
        return "solana"
    
    def get_native_token_symbol(self) -> str:
        """Return native token symbol."""
        return "SOL"
    
    def get_native_token_decimals(self) -> int:
        """Return native token decimals."""
        return 9  # SOL has 9 decimals (lamports)
    
    # ============================================================
    # Address Validation
    # ============================================================
    
    def validate_address(self, address: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Solana address format.
        
        Solana addresses are base58 encoded, typically 32-44 characters.
        """
        if not address:
            return False, "Address cannot be empty"
        
        addr = address.strip()
        
        # Check length (Solana addresses are typically 32-44 chars)
        if len(addr) < 32 or len(addr) > 44:
            return False, "Solana address must be 32-44 characters"
        
        # Try to decode base58
        try:
            decoded = base58.b58decode(addr)
            # Solana public keys are 32 bytes
            if len(decoded) != 32:
                return False, "Invalid Solana address length after decoding"
            return True, None
        except (ValueError, TypeError) as e:
            logger.debug("Base58 decode failed for address: %s", e)
            return False, "Invalid base58 encoding"
    
    def normalize_address(self, address: str) -> str:
        """Normalize Solana address (just trim whitespace)."""
        return address.strip()
    
    # ============================================================
    # RPC Methods
    # ============================================================
    
    def _rpc_call(self, method: str, params: List[Any]) -> Any:
        """
        Make JSON-RPC call to Solana node.
        
        Args:
            method: RPC method name
            params: Method parameters
            
        Returns:
            Result from RPC call
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            response = self._client.post(self.rpc_url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                raise Exception(f"RPC error: {data['error']}")
            
            return data.get("result")
        
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as e:
            # Try backup RPC if primary fails
            if self.backup_rpc_url:
                try:
                    logger.warning("Primary RPC failed, trying backup...")
                    response = self._client.post(self.backup_rpc_url, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    if "error" in data:
                        raise RuntimeError(f"RPC error: {data['error']}")

                    return data.get("result")
                except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as backup_error:
                    logger.error("Backup RPC also failed: %s", backup_error)

            raise RuntimeError(f"Solana RPC call failed: {e}")
    
    # ============================================================
    # Balance Fetching
    # ============================================================
    
    def get_balance(self, address: str, token_identifier: Optional[str] = None) -> Optional[int]:
        """
        Get raw SOL balance (in lamports) or SPL token balance.
        
        Args:
            address: Solana address
            token_identifier: Token mint address (if None, returns SOL balance)
        
        Returns:
            Raw balance as integer (lamports for SOL, raw for tokens)
        """
        addr = self.normalize_address(address)
        
        try:
            if token_identifier is None:
                # Get SOL balance (native)
                result = self._rpc_call("getBalance", [addr])
                return result.get("value", 0)
            else:
                # Get SPL token balance
                # Note: This requires token account address, not just mint
                # For now, we'll get all token accounts and find the right one
                return None  # Implement if needed
        
        except (RuntimeError, httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as e:
            logger.error("Failed to get Solana balance: %s", e)
            return None

    def get_native_balance(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get native SOL balance.

        Args:
            address: Solana address

        Returns:
            Balance dictionary or None if error
        """
        addr = self.normalize_address(address)
        balance_raw = self.get_balance(addr)

        if balance_raw is None:
            return None

        amount = self.normalize_amount(str(balance_raw), 9)
        return {
            "symbol": "SOL",
            "address": "So11111111111111111111111111111111111111112",
            "decimals": 9,
            "raw": str(balance_raw),
            "amount": float(amount),
            "chain": "solana"
        }

    def get_token_balances(self, address: str) -> List[Dict[str, Any]]:
        """
        Get all SPL token balances for Solana address.
        
        Uses getTokenAccountsByOwner RPC method.
        """
        addr = self.normalize_address(address)
        balances = []
        
        try:
            # Get SOL balance first
            sol_balance_raw = self.get_balance(addr)
            if sol_balance_raw and sol_balance_raw > 0:
                sol_amount = self.normalize_amount(str(sol_balance_raw), 9)
                balances.append({
                    "symbol": "SOL",
                    "address": "So11111111111111111111111111111111111111112",  # Wrapped SOL
                    "decimals": 9,
                    "raw": str(sol_balance_raw),
                    "amount": float(sol_amount),
                    "is_native": True
                })
            
            # Get SPL token accounts
            result = self._rpc_call("getTokenAccountsByOwner", [
                addr,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},  # SPL Token program
                {"encoding": "jsonParsed"}
            ])
            
            token_accounts = result.get("value", [])
            
            for account in token_accounts:
                try:
                    parsed_data = account.get("account", {}).get("data", {}).get("parsed", {})
                    info = parsed_data.get("info", {})
                    
                    mint = info.get("mint")
                    token_amount = info.get("tokenAmount", {})
                    
                    amount_raw = token_amount.get("amount", "0")
                    decimals = token_amount.get("decimals", 0)
                    ui_amount = token_amount.get("uiAmount", 0.0)
                    
                    # Skip zero balances
                    if int(amount_raw) == 0:
                        continue
                    
                    # Get token symbol from known tokens or use mint address
                    token_info = self.KNOWN_TOKENS.get(mint, {})
                    symbol = token_info.get("symbol", mint[:8])  # Use first 8 chars if unknown
                    
                    balances.append({
                        "symbol": symbol,
                        "address": mint,
                        "decimals": decimals,
                        "raw": amount_raw,
                        "amount": ui_amount,
                        "is_native": False
                    })
                
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning("Failed to parse token account: %s", e)
                    continue

        except (RuntimeError, httpx.HTTPError, httpx.TimeoutException) as e:
            logger.error("Failed to get Solana token balances: %s", e)
        
        return balances
    
    def get_portfolio(self, address: str) -> Dict[str, Any]:
        """
        Get complete portfolio for Solana address.
        
        Returns:
            Portfolio dictionary with chain, address, balances
        """
        normalized_addr = self.normalize_address(address)
        balances = self.get_token_balances(normalized_addr)
        
        # Extract native SOL balance
        native_balance = None
        for balance in balances:
            if balance.get("is_native"):
                native_balance = {
                    "symbol": "SOL",
                    "amount": balance["amount"],
                    "raw": balance["raw"],
                    "decimals": balance["decimals"]
                }
                break
        
        return {
            "chain": "solana",
            "address": normalized_addr,
            "balances": balances,
            "native_balance": native_balance,
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
        Get transaction history for Solana address.
        
        Uses getSignaturesForAddress RPC method.
        """
        addr = self.normalize_address(address)
        
        try:
            # Get transaction signatures
            params = [addr, {"limit": limit}]
            
            # Add before parameter for pagination if offset > 0
            # Note: Solana pagination uses signatures, not numeric offset
            # For now, just fetch the first 'limit' transactions
            
            result = self._rpc_call("getSignaturesForAddress", params)
            
            transactions = []
            
            for sig_info in result or []:
                transactions.append({
                    "signature": sig_info.get("signature"),
                    "slot": sig_info.get("slot"),
                    "err": sig_info.get("err"),
                    "memo": sig_info.get("memo"),
                    "blockTime": sig_info.get("blockTime"),
                })
            
            return transactions
        
        except (RuntimeError, httpx.HTTPError, httpx.TimeoutException, ValueError) as e:
            logger.error("Failed to get Solana transactions: %s", e)
            return []
    
    # ============================================================
    # Cleanup
    # ============================================================
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except Exception:
            # Ignore cleanup errors during garbage collection
            pass