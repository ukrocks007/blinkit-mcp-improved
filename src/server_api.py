"""
Blinkit MCP Server - API Implementation
Hybrid approach using discovered APIs where possible, browser fallback when needed
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import os

# MCP Server framework
try:
    from mcp import server, McpServer
    from mcp.types import Resource, Tool, TextContent, CallToolResult
    from mcp.shared.exceptions import McpError
except ImportError:
    print("MCP not available - creating minimal server structure for testing")
    
    # Minimal server structures for testing
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema
    
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    class CallToolResult:
        def __init__(self, content: List[TextContent]):
            self.content = content

# Import our API implementation
import sys
sys.path.append('/home/user/blinkit-mcp-ace/src')

from api.client import BlinkitAPIClient
from api.search import BlinkitSearch
from api.exceptions import BlinkitAPIError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlinkitMCPServer:
    """
    Enhanced Blinkit MCP Server with API-first approach
    Falls back to browser automation when APIs aren't available
    """
    
    def __init__(self):
        self.client: Optional[BlinkitAPIClient] = None
        self.search_service: Optional[BlinkitSearch] = None
        self.browser_fallback_available = True
        
        # Load browser automation as fallback
        try:
            sys.path.append('/home/user/blinkit-mcp/src')
            from order.blinkit_order import BlinkitOrder
            self.browser_fallback = BlinkitOrder
            logger.info("Browser fallback available")
        except ImportError:
            self.browser_fallback = None
            self.browser_fallback_available = False
            logger.warning("Browser fallback not available")
    
    async def initialize(self):
        """Initialize API client and services"""
        try:
            self.client = BlinkitAPIClient()
            await self.client.start_session()
            
            # Load authentication from discovery
            self.load_authentication()
            
            # Initialize search service
            self.search_service = BlinkitSearch(self.client)
            
            logger.info("API services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize API services: {e}")
            return False
    
    def load_authentication(self):
        """Load authentication tokens from discovery and browser session"""
        try:
            # Load from discovery
            discovery_file = "/home/user/blinkit-mcp-ace/automated_blinkit_api_discovery_20260201_093120.json"
            
            if os.path.exists(discovery_file):
                with open(discovery_file, 'r') as f:
                    discovery_data = json.load(f)
                
                auth_tokens = discovery_data.get('auth_tokens_found', {})
                if auth_tokens:
                    self.client.set_auth_tokens(**auth_tokens)
                    logger.info(f"Loaded {len(auth_tokens)} auth tokens from discovery")
            
            # Load browser cookies
            if self.client.load_auth_tokens_from_session():
                logger.info("Loaded browser session cookies")
            
        except Exception as e:
            logger.warning(f"Could not load authentication: {e}")
    
    def get_tools(self) -> List[Tool]:
        """Define MCP tools"""
        return [
            Tool(
                name="search_products",
                description="Search for products using Blinkit API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Product search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_address",
                description="Get user addresses from Blinkit API",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="test_api_status",
                description="Test API connectivity and authentication status",
                inputSchema={
                    "type": "object", 
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="search_products_browser",
                description="Search products using browser fallback (if API fails)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Product search query"
                        },
                        "limit": {
                            "type": "integer", 
                            "description": "Maximum number of results",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle MCP tool calls"""
        try:
            if name == "search_products":
                return await self.handle_search_products(arguments)
            elif name == "get_address":
                return await self.handle_get_address(arguments)
            elif name == "test_api_status":
                return await self.handle_test_api_status(arguments)
            elif name == "search_products_browser":
                return await self.handle_search_products_browser(arguments)
            else:
                raise McpError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return CallToolResult([
                TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )
            ])
    
    async def handle_search_products(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle product search via API"""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        
        if not self.search_service:
            return CallToolResult([
                TextContent(
                    type="text",
                    text="❌ Search service not initialized"
                )
            ])
        
        try:
            # Use API search
            search_result = await self.search_service.search_products(query, limit=limit)
            
            if search_result.products:
                # Format results
                result_text = f"🔍 **Search Results for '{query}'**\n\n"
                result_text += f"📊 Found {len(search_result.products)} products:\n\n"
                
                for i, product in enumerate(search_result.products[:limit], 1):
                    price_text = f"₹{product.price}" if product.price > 0 else "Price N/A"
                    result_text += f"{i}. **{product.name}** - {price_text}\n"
                    
                    if product.brand:
                        result_text += f"   Brand: {product.brand}\n"
                    if product.unit:
                        result_text += f"   Unit: {product.unit}\n"
                    
                    result_text += f"   Stock: {'✅ Available' if product.in_stock else '❌ Out of Stock'}\n"
                    result_text += f"   ID: `{product.id}`\n\n"
                
                result_text += f"**API Status**: ✅ Direct API integration working!"
                
            else:
                result_text = f"⚠️ No products found for '{query}' via API\n"
                result_text += "This might indicate API access limitations or location restrictions."
            
            return CallToolResult([
                TextContent(type="text", text=result_text)
            ])
            
        except Exception as e:
            logger.error(f"API search failed: {e}")
            
            # Return error with fallback suggestion
            error_text = f"❌ **API Search Failed**\n\n"
            error_text += f"Query: '{query}'\n"
            error_text += f"Error: {str(e)}\n\n"
            error_text += "💡 Try using `search_products_browser` for browser-based fallback."
            
            return CallToolResult([
                TextContent(type="text", text=error_text)
            ])
    
    async def handle_get_address(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle address retrieval via API"""
        if not self.client:
            return CallToolResult([
                TextContent(
                    type="text", 
                    text="❌ API client not initialized"
                )
            ])
        
        try:
            response = await self.client.get_addresses()
            
            if response.get('error'):
                return CallToolResult([
                    TextContent(
                        type="text",
                        text=f"❌ Address API Error: {response.get('message')}"
                    )
                ])
            
            # Parse addresses
            addresses = response.get('addresses', [])
            
            if addresses:
                result_text = f"🏠 **User Addresses** ({len(addresses)} found)\n\n"
                
                for i, addr in enumerate(addresses, 1):
                    result_text += f"{i}. **{addr.get('label', 'Address')}**\n"
                    result_text += f"   📍 {addr.get('display_address', 'N/A')}\n"
                    
                    if 'location' in addr:
                        loc = addr['location']
                        result_text += f"   🗺️  Coordinates: {loc.get('latitude')}, {loc.get('longitude')}\n"
                    
                    result_text += f"   🏷️  Type: {addr.get('label_id', 'N/A')}\n\n"
                
                result_text += "**API Status**: ✅ Address API working perfectly!"
                
            else:
                result_text = "⚠️ No addresses found"
            
            return CallToolResult([
                TextContent(type="text", text=result_text)
            ])
            
        except Exception as e:
            logger.error(f"Address API failed: {e}")
            
            return CallToolResult([
                TextContent(
                    type="text",
                    text=f"❌ Address API Error: {str(e)}"
                )
            ])
    
    async def handle_test_api_status(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Test API connectivity and auth status"""
        if not self.client:
            return CallToolResult([
                TextContent(
                    type="text",
                    text="❌ API client not initialized"
                )
            ])
        
        status_text = "🧪 **API Status Report**\n\n"
        
        # Check authentication
        auth_status = self.client.is_authenticated()
        status_text += f"🔐 Authentication: {'✅ Active' if auth_status else '❌ Missing'}\n"
        
        # Check cookies
        cookie_count = len(self.client.session_cookies)
        status_text += f"🍪 Session Cookies: {cookie_count}\n"
        
        # Check auth tokens
        token_count = sum(1 for v in self.client.auth_tokens.values() if v)
        status_text += f"🔑 Auth Tokens: {token_count}/4\n\n"
        
        # Test working endpoint (addresses)
        status_text += "📡 **API Endpoint Tests**:\n\n"
        
        try:
            addr_response = await self.client.get_addresses()
            if addr_response.get('error'):
                status_text += "🏠 Addresses: ❌ Failed\n"
            else:
                addr_count = len(addr_response.get('addresses', []))
                status_text += f"🏠 Addresses: ✅ Working ({addr_count} addresses)\n"
        except Exception as e:
            status_text += f"🏠 Addresses: ❌ Error: {str(e)}\n"
        
        # Test search endpoint
        try:
            search_response = await self.client.search_products("milk")
            if search_response.get('error'):
                status_text += f"🔍 Search: ❌ {search_response.get('error')}\n"
            else:
                status_text += "🔍 Search: ✅ Working\n"
        except Exception as e:
            status_text += f"🔍 Search: ❌ {str(e)}\n"
        
        status_text += f"\n**Overall**: {'🎉 Partially Working' if auth_status else '⚠️ Limited Functionality'}"
        
        return CallToolResult([
            TextContent(type="text", text=status_text)
        ])
    
    async def handle_search_products_browser(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle product search using browser fallback"""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        
        if not self.browser_fallback_available:
            return CallToolResult([
                TextContent(
                    type="text",
                    text="❌ Browser fallback not available. API-only mode."
                )
            ])
        
        # This would integrate with the existing browser automation
        # For now, return a placeholder
        result_text = f"🌐 **Browser Fallback Search**\n\n"
        result_text += f"Query: '{query}'\n"
        result_text += f"Limit: {limit}\n\n"
        result_text += "⚠️ Browser automation integration pending.\n"
        result_text += "This would use the existing Playwright-based search from the original MCP server."
        
        return CallToolResult([
            TextContent(type="text", text=result_text)
        ])
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close_session()
            logger.info("API client cleaned up")

# Standalone server for testing
async def run_standalone_test():
    """Run server in standalone mode for testing"""
    print("🚀 STARTING BLINKIT MCP SERVER (API Implementation)")
    print("=" * 55)
    
    server = BlinkitMCPServer()
    
    # Initialize
    initialized = await server.initialize()
    print(f"🔧 Initialization: {'✅ Success' if initialized else '❌ Failed'}")
    
    if not initialized:
        print("❌ Server initialization failed")
        return
    
    # Test tools
    print("\n🧪 Testing MCP Tools:")
    
    test_cases = [
        ("test_api_status", {}),
        ("get_address", {}),
        ("search_products", {"query": "milk", "limit": 3}),
        ("search_products", {"query": "davidoff coffee", "limit": 2})
    ]
    
    for tool_name, args in test_cases:
        print(f"\n🔧 Testing {tool_name}...")
        try:
            result = await server.call_tool(tool_name, args)
            
            # Print result
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    print(content.text[:500] + "..." if len(content.text) > 500 else content.text)
                else:
                    print(f"Result: {content}")
            else:
                print("No content returned")
                
        except Exception as e:
            print(f"❌ Tool error: {e}")
    
    # Cleanup
    await server.cleanup()
    print("\n🎉 Standalone test completed!")

if __name__ == "__main__":
    asyncio.run(run_standalone_test())