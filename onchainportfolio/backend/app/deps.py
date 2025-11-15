from .services.aptos_client import AptosClient
from .services.price_service import PriceService
from .config import settings

aptos_client = AptosClient(base_url=settings.aptos_node_url)
price_service = PriceService(ttl_seconds=settings.prices_ttl_seconds)
