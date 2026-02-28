# backend/app/services/adapters/evm_adapter.py
"""
EVM Base Adapter - Foundation for all EVM-compatible chains

Supports: Ethereum, Polygon, Base, Arbitrum, Optimism, etc.
Uses web3.py for blockchain interactions.
"""
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
import re

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("[WARNING] web3 not installed. Run: pip install web3")

from .base_chain_adapter import BaseChainAdapter


# ============================================================
# Standard ERC20 ABI (minimal for balance checking)
# ============================================================

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]


class EVMAdapter(BaseChainAdapter):
    """
    Base adapter for all EVM-compatible blockchains.
    
    Subclasses should override:
    - CHAIN_ID
    - CHAIN_NAME  
    - NATIVE_TOKEN
    - NATIVE_DECIMALS
    - DEFAULT_RPC_URL
    - TOKEN_REGISTRY
    """
    
    # Override in subclasses
    CHAIN_ID: int = 1
    CHAIN_NAME: str = "ethereum"
    NATIVE_TOKEN: str = "ETH"
    NATIVE_DECIMALS: int = 18
    DEFAULT_RPC_URL: str = "https://eth.llamarpc.com"
    
    # Token registry - override in subclasses
    # Format: {symbol: {"address": "0x...", "decimals": 18}}
    TOKEN_REGISTRY: Dict[str, Dict[str, Any]] = {}
    
    def get_chain_name(self) -> str:
        """Return chain identifier (e.g., 'ethereum', 'ethereum_sepolia')."""
        return self.CHAIN_NAME

    def __init__(self, rpc_url: str = None):
        """
        Initialize EVM adapter.

        Args:
            rpc_url: RPC endpoint URL (uses default if not provided)
        """
        if not WEB3_AVAILABLE:
            raise ImportError("web3 package required. Install with: pip install web3")

        self.rpc_url = rpc_url or self.DEFAULT_RPC_URL
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={'timeout': 30}))
        self.chain = self.CHAIN_NAME
        
        # Verify connection
        try:
            connected = self.w3.is_connected()
            if connected:
                chain_id = self.w3.eth.chain_id
                print(f"[{self.CHAIN_NAME.upper()}] ✅ Connected to chain ID: {chain_id}")
            else:
                print(f"[{self.CHAIN_NAME.upper()}] ⚠️ Not connected to RPC")
        except Exception as e:
            print(f"[{self.CHAIN_NAME.upper()}] ⚠️ Connection check failed: {e}")
    
    # ============================================================
    # Address Validation
    # ============================================================
    
    def validate_address(self, address: str) -> Tuple[bool, Optional[str]]:
        """
        Validate EVM address format.
        
        EVM addresses:
        - Start with 0x
        - 40 hex characters (20 bytes)
        - Case-insensitive (but checksum matters for validation)
        """
        if not address:
            return False, "Address cannot be empty"
        
        addr = address.strip()
        
        # Check 0x prefix
        if not addr.startswith("0x") and not addr.startswith("0X"):
            return False, "Address must start with '0x'"
        
        # Check length (0x + 40 hex chars = 42 total)
        if len(addr) != 42:
            return False, f"Address must be 42 characters (got {len(addr)})"
        
        # Check hex characters
        hex_part = addr[2:]
        if not re.match(r'^[0-9a-fA-F]+$', hex_part):
            return False, "Address must contain only hexadecimal characters"
        
        # Validate checksum if mixed case
        if not addr[2:].islower() and not addr[2:].isupper():
            try:
                checksum_addr = self.w3.to_checksum_address(addr)
                if checksum_addr != addr:
                    # Invalid checksum but valid hex - accept with warning
                    print(f"[{self.CHAIN_NAME}] Address checksum mismatch, normalizing")
            except Exception:
                return False, "Invalid address checksum"
        
        return True, None
    
    def normalize_address(self, address: str) -> str:
        """
        Normalize EVM address to checksum format.
        """
        addr = address.strip()
        
        if not addr.startswith("0x"):
            addr = "0x" + addr
        
        try:
            return self.w3.to_checksum_address(addr)
        except Exception:
            return addr.lower()
    
    def verify_on_chain(self, address: str) -> Tuple[bool, Optional[str]]:
        """
        Verify address exists on chain by checking if it has any activity.
        
        For EVM, we check:
        1. If it's a contract (has code)
        2. If it has balance
        3. If it has any transactions (nonce > 0)
        """
        try:
            normalized = self.normalize_address(address)
            
            # Check if it's a contract
            code = self.w3.eth.get_code(normalized)
            if code and code != b'' and code != '0x':
                return True, None  # It's a contract
            
            # Check balance
            balance = self.w3.eth.get_balance(normalized)
            if balance > 0:
                return True, None
            
            # Check transaction count
            nonce = self.w3.eth.get_transaction_count(normalized)
            if nonce > 0:
                return True, None
            
            # Address is valid format but no on-chain activity
            # This is still valid - could be a new wallet
            return True, None
            
        except Exception as e:
            return False, f"Failed to verify on chain: {str(e)}"
    
    # ============================================================
    # Balance Fetching
    # ============================================================
    
    def get_native_balance(self, address: str) -> Dict[str, Any]:
        """
        Get native token balance (ETH, MATIC, etc.)
        """
        try:
            normalized = self.normalize_address(address)
            balance_wei = self.w3.eth.get_balance(normalized)
            balance = Decimal(balance_wei) / Decimal(10 ** self.NATIVE_DECIMALS)
            
            return {
                "symbol": self.NATIVE_TOKEN,
                "address": "native",
                "decimals": self.NATIVE_DECIMALS,
                "raw": str(balance_wei),
                "amount": float(balance),
                "chain": self.chain
            }
        except Exception as e:
            print(f"[{self.CHAIN_NAME}] Error fetching native balance: {e}")
            return None
    
    def get_token_balance(
        self, 
        wallet_address: str, 
        token_address: str,
        symbol: str = None,
        decimals: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get ERC20 token balance for a wallet.
        
        Args:
            wallet_address: Wallet address
            token_address: Token contract address
            symbol: Token symbol (optional, will fetch if not provided)
            decimals: Token decimals (optional, will fetch if not provided)
        """
        try:
            wallet = self.normalize_address(wallet_address)
            token = self.normalize_address(token_address)
            
            # Create contract instance
            contract = self.w3.eth.contract(address=token, abi=ERC20_ABI)
            
            # Fetch balance
            balance_raw = contract.functions.balanceOf(wallet).call()
            
            if balance_raw == 0:
                return None
            
            # Get decimals if not provided
            if decimals is None:
                try:
                    decimals = contract.functions.decimals().call()
                except Exception:
                    decimals = 18  # Default to 18
            
            # Get symbol if not provided
            if symbol is None:
                try:
                    symbol = contract.functions.symbol().call()
                except Exception:
                    symbol = "UNKNOWN"
            
            balance = Decimal(balance_raw) / Decimal(10 ** decimals)
            
            return {
                "symbol": symbol,
                "address": token,
                "decimals": decimals,
                "raw": str(balance_raw),
                "amount": float(balance),
                "chain": self.chain
            }
            
        except Exception as e:
            print(f"[{self.CHAIN_NAME}] Error fetching token balance for {symbol or token_address}: {e}")
            return None
    
    def get_token_balances(self, address: str) -> List[Dict[str, Any]]:
        """
        Get all token balances for an address.
        
        Fetches:
        1. Native token balance
        2. All tokens in TOKEN_REGISTRY
        """
        balances = []
        
        print(f"[{self.CHAIN_NAME}] Fetching balances for {address[:10]}...")
        
        # 1. Native token
        native = self.get_native_balance(address)
        if native and native.get("amount", 0) > 0:
            balances.append(native)
            print(f"[{self.CHAIN_NAME}]   ✓ {self.NATIVE_TOKEN}: {native['amount']}")
        
        # 2. Registry tokens
        for symbol, token_info in self.TOKEN_REGISTRY.items():
            token_address = token_info.get("address")
            decimals = token_info.get("decimals", 18)
            
            if not token_address:
                continue
            
            balance = self.get_token_balance(
                address, 
                token_address,
                symbol=symbol,
                decimals=decimals
            )
            
            if balance and balance.get("amount", 0) > 0:
                balances.append(balance)
                print(f"[{self.CHAIN_NAME}]   ✓ {symbol}: {balance['amount']}")
        
        print(f"[{self.CHAIN_NAME}] Found {len(balances)} tokens with balance")
        return balances
    
    # ============================================================
    # Transaction Fetching (Basic)
    # ============================================================
    
    def get_transactions(
        self,
        address: str,
        limit: int = 20,
        offset: int = 0,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get recent transactions for an address.

        Note: EVM transaction history requires an indexer API (Etherscan/Alchemy).
        Basic web3.py has no transaction-history endpoint — returns empty list
        until an indexer integration is added.
        """
        print(f"[{self.CHAIN_NAME}] ⚠️ Transaction history requires indexer API (Etherscan/Alchemy)")
        return []
    
    def get_transaction_detail(
        self, 
        tx_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific transaction.
        """
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            return {
                "hash": tx_hash,
                "block_number": tx.blockNumber,
                "from": tx["from"],
                "to": tx.to,
                "value": str(tx.value),
                "value_eth": float(Decimal(tx.value) / Decimal(10**18)),
                "gas_used": receipt.gasUsed,
                "gas_price": tx.gasPrice,
                "success": receipt.status == 1,
                "chain": self.chain
            }
        except Exception as e:
            print(f"[{self.CHAIN_NAME}] Error fetching transaction: {e}")
            return None
    
    # ============================================================
    # Utility Methods
    # ============================================================
    
    def get_block_number(self) -> int:
        """Get current block number."""
        return self.w3.eth.block_number
    
    def get_gas_price(self) -> int:
        """Get current gas price in wei."""
        return self.w3.eth.gas_price
    
    def is_contract(self, address: str) -> bool:
        """Check if address is a contract."""
        try:
            normalized = self.normalize_address(address)
            code = self.w3.eth.get_code(normalized)
            return code and code != b'' and code != '0x'
        except Exception:
            return False
    
    def get_chain_info(self) -> Dict[str, Any]:
        """Get chain information."""
        try:
            return {
                "chain": self.chain,
                "chain_id": self.w3.eth.chain_id,
                "block_number": self.w3.eth.block_number,
                "gas_price_gwei": self.w3.eth.gas_price / 10**9,
                "connected": self.w3.is_connected(),
                "native_token": self.NATIVE_TOKEN,
                "rpc_url": self.rpc_url[:50] + "..." if len(self.rpc_url) > 50 else self.rpc_url
            }
        except Exception as e:
            return {
                "chain": self.chain,
                "error": str(e),
                "connected": False
            }