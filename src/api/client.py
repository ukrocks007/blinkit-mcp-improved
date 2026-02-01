"""
Blinkit API Client - Core Implementation
Direct API integration for fast, reliable operations
"""

import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .exceptions import BlinkitAPIError, AuthenticationError, RateLimitError
from .models import LoginResponse, SearchResult, CartItem, Address, Order

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """API Configuration"""
    base_url: str = "https://blinkit.com"  # Will be updated based on discovery
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0

class BlinkitAPIClient:
    """
    Core Blinkit API Client
    Handles authentication, requests, and response processing
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session_cookies: Dict[str, str] = {}
        self.last_request_time: float = 0
        
    async def __aenter__(self):
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
    
    async def start_session(self):
        """Initialize HTTP session with proper headers"""
        if self.session and not self.session.closed:
            return
            
        # Headers based on API discovery findings
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://blinkit.com',
            'Referer': 'https://blinkit.com/'
        }
        
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar()
        )
        
        logger.info("API session started")
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("API session closed")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Make authenticated API request with retry logic
        """
        if not self.session:
            await self.start_session()
        
        # Rate limiting
        now = asyncio.get_event_loop().time()
        if now - self.last_request_time < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - (now - self.last_request_time))
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        # Prepare headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
            
        # Add authentication if required and available
        if require_auth and self.auth_token:
            request_headers['Authorization'] = f'Bearer {self.auth_token}'
            
        # Add session cookies
        if self.session_cookies:
            cookie_str = '; '.join([f'{k}={v}' for k, v in self.session_cookies.items()])
            request_headers['Cookie'] = cookie_str
        
        # Retry logic
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                self.last_request_time = asyncio.get_event_loop().time()
                
                logger.debug(f"API Request: {method} {url} (attempt {attempt + 1})")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data if method in ['POST', 'PUT', 'PATCH'] else None,
                    params=params,
                    headers=request_headers
                ) as response:
                    
                    # Update cookies from response
                    if response.cookies:
                        for cookie in response.cookies:
                            self.session_cookies[cookie.key] = cookie.value
                    
                    response_text = await response.text()
                    
                    # Handle different response types
                    if response.status == 401:
                        raise AuthenticationError("Authentication failed or token expired")
                    elif response.status == 429:
                        raise RateLimitError("Rate limit exceeded")
                    elif response.status >= 400:
                        raise BlinkitAPIError(f"API error {response.status}: {response_text}")
                    
                    # Try to parse JSON response
                    try:
                        result = json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        result = {"raw_response": response_text}
                    
                    logger.debug(f"API Response: {response.status} {len(response_text)} bytes")
                    return result
                    
            except aiohttp.ClientError as e:
                last_exception = BlinkitAPIError(f"Network error: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
            except (RateLimitError, AuthenticationError):
                # Don't retry authentication and rate limit errors
                raise
            except Exception as e:
                last_exception = BlinkitAPIError(f"Unexpected error: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
        
        # All retries exhausted
        raise last_exception or BlinkitAPIError("Max retries exceeded")
    
    async def get(self, endpoint: str, params: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request('GET', endpoint, params=params, **kwargs)
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request('POST', endpoint, data=data, **kwargs)
    
    async def put(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._make_request('PUT', endpoint, data=data, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._make_request('DELETE', endpoint, **kwargs)
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return bool(self.auth_token or self.session_cookies)
    
    def set_auth_token(self, token: str, token_type: str = 'Bearer'):
        """Set authentication token"""
        self.auth_token = token
        logger.info(f"Authentication token set ({token_type})")
    
    def set_session_cookies(self, cookies: Dict[str, str]):
        """Set session cookies"""
        self.session_cookies.update(cookies)
        logger.info(f"Session cookies updated ({len(cookies)} cookies)")
    
    async def update_endpoints_from_discovery(self, discovery_data: Dict[str, Any]):
        """Update client configuration based on API discovery results"""
        # Extract base URL from discovered endpoints
        endpoints = discovery_data.get('api_calls', [])
        blinkit_urls = [call['url'] for call in endpoints if 'blinkit.com' in call.get('url', '')]
        
        if blinkit_urls:
            # Find most common base URL pattern
            common_base = max(set(url.split('/api')[0] for url in blinkit_urls if '/api' in url), 
                            key=blinkit_urls.count, default=self.config.base_url)
            self.config.base_url = common_base
            logger.info(f"Updated base URL to: {common_base}")
        
        # Extract authentication patterns
        auth_tokens = discovery_data.get('auth_tokens', {})
        if auth_tokens:
            logger.info(f"Discovered auth patterns: {list(auth_tokens.keys())}")
        
        return True