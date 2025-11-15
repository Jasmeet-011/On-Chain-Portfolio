# app/services/aptos_client.py
import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import quote

class AptosClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.Client(base_url=base_url, timeout=10.0)

    def get_account_coins(self, address: str) -> List[Dict[str, Any]]:
        r = self._client.get(f"/accounts/{address}/resources")
        r.raise_for_status()
        return r.json()

    def get_coin_info(self, token_type: str) -> Optional[Dict[str, Any]]:
        """
        Read 0x1::coin::CoinInfo<token_type>.
        IMPORTANT: resource type must be URL-encoded (encode '<', '>', and ',').
        """
        try:
            issuer_addr = token_type.split("::", 1)[0]
            type_str = f"0x1::coin::CoinInfo<{token_type}>"
            encoded = quote(type_str, safe=":,")  # encode < > and commas
            r = self._client.get(f"/accounts/{issuer_addr}/resource/{encoded}")
            if r.status_code == 200:
                j = r.json()
                # some nodes return {"data": {...}}, others return {...} directly
                return (j.get("data") if isinstance(j, dict) else None) or j
            return None
        except Exception:
            return None
