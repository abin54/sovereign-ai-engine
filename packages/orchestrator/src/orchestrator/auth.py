from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_429_TOO_MANY_REQUESTS
import time
from collections import defaultdict
from typing import Dict, Any

from shared.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Simple rate limiter (In-memory for MVP, use Redis in production)
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int) -> bool:
        now = time.time()
        # Clean up old requests (older than 60s)
        self.requests[key] = [t for t in self.requests[key] if now - t < 60]
        if len(self.requests[key]) >= limit:
            return False
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

# Initial set of keys (can be expanded via settings)
VALID_KEYS: Dict[str, Dict[str, Any]] = {
    settings.system_auth_token: {"role": "admin", "rate_limit": 1000}
} if settings.system_auth_token else {
    "sk-sovereign-admin": {"role": "admin", "rate_limit": 1000}
}

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not api_key or api_key not in VALID_KEYS:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Invalid or missing API key"
        )
    
    key_info = VALID_KEYS[api_key]
    if not rate_limiter.is_allowed(api_key, key_info["rate_limit"]):
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS, 
            detail="Rate limit exceeded. Try again in a minute."
        )
    
    return key_info
