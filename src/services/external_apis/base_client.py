"""
Base API client with common functionality for external API integrations.
"""
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


@dataclass
class APIResponse:
    """Standardized API response wrapper."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


class RateLimiter:
    """Token bucket rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 100, burst_size: Optional[int] = None):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.tokens = self.burst_size
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire a token for making a request."""
        async with self._lock:
            now = time.time()
            # Refill tokens based on time elapsed
            time_elapsed = now - self.last_refill
            tokens_to_add = time_elapsed * (self.requests_per_minute / 60.0)
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    async def wait_for_token(self) -> None:
        """Wait until a token is available."""
        while not await self.acquire():
            await asyncio.sleep(0.1)


class APIClient(ABC):
    """Abstract base class for external API clients."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        requests_per_minute: int = 100,
        retry_attempts: int = 3,
        retry_backoff: float = 1.0,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff
        self.timeout = timeout
        
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.client = httpx.AsyncClient(timeout=timeout)
        self.logger = structlog.get_logger(self.__class__.__name__)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        pass
    
    def get_default_headers(self) -> Dict[str, str]:
        """Get default headers for all requests."""
        headers = {
            'User-Agent': 'ConcertDataPlatform/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        headers.update(self.get_auth_headers())
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Make an HTTP request with rate limiting and retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.get_default_headers()
        if headers:
            request_headers.update(headers)
        
        # Wait for rate limit token
        await self.rate_limiter.wait_for_token()
        
        for attempt in range(self.retry_attempts):
            try:
                self.logger.debug(
                    "Making API request",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                    params=params
                )
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                )
                
                # Parse rate limit headers if available
                rate_limit_remaining = None
                rate_limit_reset = None
                
                if 'X-RateLimit-Remaining' in response.headers:
                    rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
                
                if 'X-RateLimit-Reset' in response.headers:
                    reset_timestamp = int(response.headers['X-RateLimit-Reset'])
                    rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
                
                if response.is_success:
                    try:
                        response_data = response.json()
                    except Exception:
                        response_data = {"raw_response": response.text}
                    
                    self.logger.debug(
                        "API request successful",
                        status_code=response.status_code,
                        rate_limit_remaining=rate_limit_remaining
                    )
                    
                    return APIResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status_code,
                        rate_limit_remaining=rate_limit_remaining,
                        rate_limit_reset=rate_limit_reset
                    )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(
                        "Rate limit exceeded, waiting",
                        retry_after=retry_after,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep(retry_after)
                    continue
                
                # Handle server errors (5xx) - retry
                if 500 <= response.status_code < 600:
                    if attempt < self.retry_attempts - 1:
                        wait_time = self.retry_backoff * (2 ** attempt)
                        self.logger.warning(
                            "Server error, retrying",
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            wait_time=wait_time
                        )
                        await asyncio.sleep(wait_time)
                        continue
                
                # Client errors (4xx) - don't retry
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                    elif 'message' in error_data:
                        error_msg = error_data['message']
                except Exception:
                    pass
                
                self.logger.error(
                    "API request failed",
                    status_code=response.status_code,
                    error=error_msg
                )
                
                return APIResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code,
                    rate_limit_remaining=rate_limit_remaining,
                    rate_limit_reset=rate_limit_reset
                )
                
            except httpx.TimeoutException:
                if attempt < self.retry_attempts - 1:
                    wait_time = self.retry_backoff * (2 ** attempt)
                    self.logger.warning(
                        "Request timeout, retrying",
                        attempt=attempt + 1,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                error_msg = "Request timeout"
                self.logger.error("Request timeout after all retries")
                return APIResponse(success=False, error=error_msg)
                
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = self.retry_backoff * (2 ** attempt)
                    self.logger.warning(
                        "Request failed with exception, retrying",
                        error=str(e),
                        attempt=attempt + 1,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                error_msg = f"Request failed: {str(e)}"
                self.logger.error("Request failed after all retries", error=str(e))
                return APIResponse(success=False, error=error_msg)
        
        return APIResponse(success=False, error="All retry attempts failed")
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Make a GET request."""
        return await self._make_request('GET', endpoint, params=params, headers=headers)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Make a POST request."""
        return await self._make_request('POST', endpoint, params=params, data=data, headers=headers)