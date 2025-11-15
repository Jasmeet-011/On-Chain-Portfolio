from decimal import Decimal
from typing import Dict, Iterable
from .cache import cache

# Map symbols to a pretend provider key; swap this with a real provider later
FAKE_SPOT = {
    "APT": Decimal("7.10"),
    "USDC": Decimal("1.00"),
    "USDT": Decimal("1.00"),
}

class PriceService:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds

    def get_prices(self, symbols: Iterable[str]) -> Dict[str, Decimal]:
        syms = [s.upper() for s in symbols]
        key = f"prices:{','.join(sorted(syms))}"
        cached = cache.get(key)
        if cached:
            return cached
        # TODO: swap with real provider (e.g., CoinGecko, Pyth, Switchboard)
        data = {s: FAKE_SPOT.get(s) for s in syms}
        cache.set(key, data, self.ttl)
        return data
