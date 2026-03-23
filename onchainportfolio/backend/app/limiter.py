# app/limiter.py
"""
Shared rate limiter instance for the application.

Uses slowapi (wraps limits library) on top of FastAPI.
Register on app with:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_real_ip(request: Request) -> str:
    """
    Extract client IP, honouring X-Forwarded-For set by Railway / Render
    reverse proxies.  Falls back to the direct socket address.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


limiter = Limiter(key_func=get_real_ip)
