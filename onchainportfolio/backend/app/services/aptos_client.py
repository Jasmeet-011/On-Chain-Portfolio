# app/services/aptos_client.py
import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import quote


class AptosClient:
    def __init__(self, base_url: str):
        """
        HTTP client for talking to an Aptos fullnode REST API.
        base_url is expected like: "https://fullnode.testnet.aptoslabs.com/v1"
        """
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def get_account_resources(self, address: str) -> List[Dict[str, Any]]:
        """
        Fetch all resources for an account.
        Hitting: GET {base_url}/accounts/{address}/resources
        """
        addr = address.lower()
        if not addr.startswith("0x"):
            addr = "0x" + addr
            
        try:
            r = self._client.get(f"/accounts/{addr}/resources")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise
        except Exception as e:
            raise Exception(f"Failed to fetch account resources: {str(e)}")

    def get_account_balance(self, address: str, asset_type: str) -> Optional[int]:
        """
        Get account balance using the official /balance/ endpoint.
        """
        addr = address.lower()
        if not addr.startswith("0x"):
            addr = "0x" + addr
        
        # URL encode the asset type (handles ::, <, > characters)
        encoded_asset = quote(asset_type, safe="")
        
        print(f"[DEBUG] get_account_balance called")
        print(f"[DEBUG]   address: {addr}")
        print(f"[DEBUG]   asset_type: {asset_type}")
        print(f"[DEBUG]   encoded_asset: {encoded_asset}")
        
        try:
            url = f"/accounts/{addr}/balance/{encoded_asset}"
            print(f"[DEBUG]   full URL: {self.base_url}{url}")
            
            r = self._client.get(url)
            
            print(f"[DEBUG]   status_code: {r.status_code}")
            print(f"[DEBUG]   response text: {r.text}")
            
            if r.status_code == 404:
                return None
            
            r.raise_for_status()
            
            balance = r.json()
            print(f"[DEBUG]   parsed balance: {balance}, type: {type(balance)}")
            
            if isinstance(balance, dict):
                return int(balance.get("balance") or balance.get("amount") or "0")
            else:
                return int(balance)
                
        except Exception as e:
            print(f"[ERROR] get_account_balance exception: {e}")
            import traceback
            traceback.print_exc()
            return None

    def close(self):
        """Close the HTTP client"""
        self._client.close()