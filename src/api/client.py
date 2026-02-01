"""
Blinkit API Client - Updated with Discovered Endpoints
Direct integration with real Blinkit APIs found through automated discovery
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
    """API Configuration with discovered endpoints"""
    base_url: str = "https://blinkit.com"
    jumbo_url: str = "https://jumbo.blinkit.com"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.5  # From discovery: use 500ms delays

class BlinkitAPIClient:
    """
    Enhanced Blinkit API Client with discovered endpoints
    Based on automated API discovery findings (80% feasibility)
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Authentication tokens discovered in API analysis
        self.auth_tokens = {
            'auth_key': None,
            'session_uuid': None, 
            'access_token': None,
            'feature_flag_key': None
        }
        
        self.session_cookies: Dict[str, str] = {}
        self.last_request_time: float = 0
        
        # Real API endpoints discovered through automation
        self.endpoints = {
            # Authentication & Session (DISCOVERED)
            'secondary_data': '/v2/services/secondary-data/',
            'feature_flags': '/api/feature-flags/receive',
            'user_property': '/v1/user/user_property/{user_id}',
            
            # Search APIs (DISCOVERED & VERIFIED)
            'search_layout': '/v1/layout/search',            # ⭐ PRIMARY search API
            'search_suggest': '/v1/actions/auto_suggest',    # ⭐ Autocomplete API  
            'search_deeplink': '/v2/search/deeplink/',       # Search deeplinks
            'search_empty': '/v1/layout/empty_search',       # Empty search handling
            
            # Cart API (DISCOVERED & VERIFIED)
            'carts': '/v5/carts',                           # ⭐ PRIMARY cart API
            
            # Address API (DISCOVERED & VERIFIED) 
            'address': '/v4/address',                        # ⭐ PRIMARY address API
            
            # User & Orders (DISCOVERED)
            'order_count': '/v1/order_count',               # Order history count
            'eta': '/v1/consumerweb/eta',                   # Delivery estimates
            
            # External endpoints
            'events': '/event'  # Will use jumbo_url as base
        }
        
    async def __aenter__(self):
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
    
    async def start_session(self):
        """Initialize HTTP session with discovered headers"""
        if self.session and not self.session.closed:
            return
            
        # Headers based on successful API discovery  
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'application/json, text/plain, */*',
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
        
        logger.info("Enhanced API session started with discovered endpoints")
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("API session closed")
    
    def load_auth_tokens_from_session(self, session_file: str = None):
        """Load authentication tokens and cookies from saved session"""
        try:
            import os
            
            # Try API session first
            session_path = session_file or os.path.expanduser("~/.blinkit_api_session.json")
            
            if os.path.exists(session_path):
                with open(session_path, 'r') as f:
                    session_data = json.load(f)
                
                # Load discovered auth token types
                for token_type in self.auth_tokens.keys():
                    if token_type in session_data:
                        self.auth_tokens[token_type] = session_data[token_type]
                        logger.info(f"Loaded {token_type} from session")
                
                # Load cookies
                if 'cookies' in session_data:
                    self.session_cookies.update(session_data['cookies'])
                    logger.info(f"Loaded {len(self.session_cookies)} cookies from session")
                
                return True
            
            # Fallback: try to load from browser session
            browser_session_path = os.path.expanduser("~/.blinkit_mcp/cookies/auth.json")
            
            if os.path.exists(browser_session_path):
                with open(browser_session_path, 'r') as f:
                    browser_data = json.load(f)
                
                # Extract cookies from browser session
                if 'cookies' in browser_data:
                    for cookie in browser_data['cookies']:
                        if 'name' in cookie and 'value' in cookie:
                            # Focus on Blinkit domain cookies
                            if '.blinkit.com' in cookie.get('domain', ''):
                                self.session_cookies[cookie['name']] = cookie['value']
                
                logger.info(f"Loaded {len(self.session_cookies)} cookies from browser session")
                return True
                
        except Exception as e:
            logger.warning(f"Could not load session: {e}")
        
        return False
    
    def save_auth_tokens_to_session(self, session_file: str = None):
        """Save authentication tokens to session"""
        try:
            import os
            session_path = session_file or os.path.expanduser("~/.blinkit_api_session.json")
            
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'auth_tokens': self.auth_tokens,
                'cookies': self.session_cookies
            }
            
            # Create directory if needed
            os.makedirs(os.path.dirname(session_path), exist_ok=True)
            
            with open(session_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Saved session to {session_path}")
            return True
        except Exception as e:
            logger.error(f"Could not save session: {e}")
            return False
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        use_jumbo: bool = False
    ) -> Dict[str, Any]:
        """
        Make authenticated API request using discovered patterns
        """
        if not self.session:
            await self.start_session()
        
        # Rate limiting based on discovery findings (500ms delay)
        now = asyncio.get_event_loop().time()
        if now - self.last_request_time < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - (now - self.last_request_time))
        
        # Build URL with correct base
        if use_jumbo:
            url = f"{self.config.jumbo_url}{endpoint}"
        else:
            url = f"{self.config.base_url}{endpoint}"
        
        # Prepare headers with discovered auth tokens
        request_headers = {}
        if headers:
            request_headers.update(headers)
            
        # Add discovered authentication tokens
        for token_type, token_value in self.auth_tokens.items():
            if token_value:
                request_headers[token_type] = token_value
        
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
                        logger.warning(f"API error {response.status}: {response_text[:200]}")
                        # Return error structure instead of raising for API testing
                        return {
                            "error": True,
                            "status": response.status,
                            "message": response_text[:500]
                        }
                    
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
        
        # All retries exhausted - return error structure for testing
        return {
            "error": True,
            "message": str(last_exception) if last_exception else "Max retries exceeded"
        }
    
    # =============================================================================
    # DISCOVERED API METHODS (Based on real Blinkit endpoints)
    # =============================================================================
    
    async def get_secondary_data(self) -> Dict[str, Any]:
        """Get secondary data - discovered endpoint"""
        # Add required location headers based on error message
        headers = {
            'Lat': '18.470896',  # Working Pune location from address API
            'Lon': '73.86407'    # Working Pune longitude from address API
        }
        return await self._make_request('GET', self.endpoints['secondary_data'], headers=headers)
    
    async def get_feature_flags(self) -> Dict[str, Any]:
        """Get feature flags - discovered endpoint"""
        return await self._make_request('GET', self.endpoints['feature_flags'])
    
    async def get_user_property(self, user_id: str) -> Dict[str, Any]:
        """Get user properties - discovered endpoint"""
        endpoint = self.endpoints['user_property'].format(user_id=user_id)
        return await self._make_request('GET', endpoint)
    
    async def search_products(self, query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for products using discovered search API"""
        # Build search payload based on discovered patterns
        payload = {
            "query": query,
            "page": 0,
            "size": 20,
            # Use serviceable location from working address API
            "lat": 18.470896,   # Working Pune location from address API
            "lng": 73.86407
        }
        
        # Merge any additional filters
        if filters:
            payload.update(filters)
        
        return await self._make_request('POST', self.endpoints['search_layout'], data=payload)
    
    async def get_search_suggestions(self, query: str) -> Dict[str, Any]:
        """Get autocomplete suggestions - discovered endpoint"""
        payload = {
            "query": query,
            "lat": 18.470896,  # Working Pune location from address API
            "lng": 73.86407    # Working Pune longitude from address API
        }
        return await self._make_request('POST', self.endpoints['search_suggest'], data=payload)
    
    async def manage_cart(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage cart using discovered cart API"""
        logger.info(f"Cart operation: {action_data}")
        return await self._make_request('POST', self.endpoints['carts'], data=action_data)
    
    async def get_addresses(self) -> Dict[str, Any]:
        """Get user addresses - discovered endpoint"""
        return await self._make_request('GET', self.endpoints['address'])
    
    async def get_order_count(self) -> Dict[str, Any]:
        """Get order history count - discovered endpoint"""
        return await self._make_request('GET', self.endpoints['order_count'])
    
    async def get_eta(self) -> Dict[str, Any]:
        """Get delivery ETA - discovered endpoint"""
        return await self._make_request('GET', self.endpoints['eta'])
    
    async def send_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send analytics event to Jumbo domain - discovered endpoint"""
        return await self._make_request('POST', self.endpoints['events'], data=event_data, use_jumbo=True)
    
    # Generic methods for testing
    async def get(self, endpoint: str, params: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request('GET', endpoint, params=params, **kwargs)
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request('POST', endpoint, data=data, **kwargs)
    
    def is_authenticated(self) -> bool:
        """Check if client has authentication tokens"""
        return any(self.auth_tokens.values()) or bool(self.session_cookies)
    
    def set_auth_tokens(self, **tokens):
        """Set discovered authentication tokens"""
        for token_type, token_value in tokens.items():
            if token_type in self.auth_tokens:
                self.auth_tokens[token_type] = token_value
                logger.info(f"Set {token_type}: {str(token_value)[:20]}...")