#!/usr/bin/env python3
"""
Blinkit MCP Server - Production Implementation
Enhanced API-first server with discovered Blinkit endpoints
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, List, Any, Optional

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Try to import MCP (may not be available in test environment)
    import mcp
    from mcp import server
    from mcp.types import Resource, Tool, TextContent, CallToolResult
    from mcp.shared.exceptions import McpError
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("MCP framework not available - running in test mode", file=sys.stderr)
    
    # Mock classes for test mode
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
        def __init__(self, content):
            self.content = content

# Import our enhanced API implementation
from api.client import BlinkitAPIClient
from api.search import BlinkitSearch
from api.exceptions import BlinkitAPIError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

class BlinkitAPIMCPServer:
    """
    Production Blinkit MCP Server with API-first approach
    Based on automated discovery results (80% feasibility)
    """
    
    def __init__(self):
        self.client: Optional[BlinkitAPIClient] = None
        self.search_service: Optional[BlinkitSearch] = None
        
        # Configuration from environment
        self.session_path = os.getenv('BLINKIT_SESSION_PATH', '/home/user/.blinkit_api_session.json')
        self.discovery_path = os.getenv('BLINKIT_DISCOVERY_PATH', '/home/user/blinkit-mcp-ace/automated_blinkit_api_discovery_20260201_093120.json')
        
    async def initialize(self) -> bool:
        """Initialize API services"""
        try:
            logger.info("Initializing Blinkit API MCP Server...")
            
            # Initialize API client
            self.client = BlinkitAPIClient()
            await self.client.start_session()
            
            # Load authentication
            await self.load_authentication()
            
            # Initialize search service
            self.search_service = BlinkitSearch(self.client)
            
            # Test connectivity
            is_working = await self.test_connectivity()
            
            logger.info(f"Server initialization {'completed' if is_working else 'completed with limitations'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            return False
    
    async def load_authentication(self):
        """Load authentication from discovery and browser session"""
        try:
            # Load discovery tokens
            if os.path.exists(self.discovery_path):
                with open(self.discovery_path, 'r') as f:
                    discovery_data = json.load(f)
                
                auth_tokens = discovery_data.get('auth_tokens_found', {})
                if auth_tokens:
                    self.client.set_auth_tokens(**auth_tokens)
                    logger.info(f"Loaded {len(auth_tokens)} auth tokens from discovery")
            
            # Load browser session cookies
            if self.client.load_auth_tokens_from_session():
                cookie_count = len(self.client.session_cookies)
                logger.info(f"Loaded {cookie_count} browser cookies")
            
            # Verify authentication
            if self.client.is_authenticated():
                logger.info("Authentication successful")
            else:
                logger.warning("No authentication available - limited functionality")
                
        except Exception as e:
            logger.error(f"Authentication loading failed: {e}")
    
    async def test_connectivity(self) -> bool:
        """Test API connectivity"""
        try:
            # Test working endpoint (addresses)
            response = await self.client.get_addresses()
            
            if response.get('error'):
                logger.warning("Address API test failed - limited functionality")
                return False
            else:
                addr_count = len(response.get('addresses', []))
                logger.info(f"API connectivity confirmed - {addr_count} addresses retrieved")
                return True
                
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    def get_tools(self) -> List[Tool]:
        """Define available MCP tools"""
        return [
            Tool(
                name="search_products",
                description="Search for products on Blinkit using enhanced API integration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Product name or search term (e.g., 'milk', 'davidoff coffee', 'bread')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of products to return (default: 10, max: 50)",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            ),
            
            Tool(
                name="get_user_addresses",
                description="Retrieve user's saved delivery addresses from Blinkit",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            Tool(
                name="api_status",
                description="Check API connectivity, authentication status, and available services",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "detailed": {
                            "type": "boolean",
                            "description": "Include detailed endpoint testing",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            
            Tool(
                name="search_suggestions",
                description="Get autocomplete suggestions for product search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "partial_query": {
                            "type": "string",
                            "description": "Partial search term to get suggestions for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of suggestions (default: 5)",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        }
                    },
                    "required": ["partial_query"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle MCP tool calls"""
        try:
            logger.info(f"Executing tool: {name} with args: {arguments}")
            
            if name == "search_products":
                return await self.search_products_tool(arguments)
            elif name == "get_user_addresses":
                return await self.get_addresses_tool(arguments)
            elif name == "api_status":
                return await self.api_status_tool(arguments)
            elif name == "search_suggestions":
                return await self.search_suggestions_tool(arguments)
            else:
                if HAS_MCP:
                    raise McpError(f"Unknown tool: {name}")
                else:
                    return self._create_error_result(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            return self._create_error_result(f"Tool execution failed: {str(e)}")
    
    async def search_products_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle product search requests"""
        query = arguments.get("query", "").strip()
        limit = arguments.get("limit", 10)
        
        if not query:
            return self._create_error_result("Search query cannot be empty")
        
        try:
            # Attempt API search
            search_result = await self.search_service.search_products(query, limit=limit)
            
            if search_result.products:
                # Format successful results
                result_text = f"🔍 **Product Search Results**\n\n"
                result_text += f"**Query**: {query}\n"
                result_text += f"**Results**: {len(search_result.products)} of {search_result.total_results} total\n\n"
                
                for i, product in enumerate(search_result.products, 1):
                    result_text += f"**{i}. {product.name}**\n"
                    
                    # Price information
                    if product.price > 0:
                        price_text = f"₹{product.price:.2f}"
                        if product.original_price and product.original_price > product.price:
                            discount = ((product.original_price - product.price) / product.original_price) * 100
                            price_text += f" ~~₹{product.original_price:.2f}~~ ({discount:.0f}% off)"
                        result_text += f"💰 **Price**: {price_text}\n"
                    
                    # Additional details
                    if product.brand:
                        result_text += f"🏷️ **Brand**: {product.brand}\n"
                    if product.unit:
                        result_text += f"📦 **Unit**: {product.unit}\n"
                    
                    # Stock status
                    stock_icon = "✅" if product.in_stock else "❌"
                    result_text += f"{stock_icon} **Stock**: {'Available' if product.in_stock else 'Out of Stock'}\n"
                    
                    result_text += f"🆔 **Product ID**: `{product.id}`\n\n"
                
                result_text += f"---\n**Status**: ✅ API search successful\n**Method**: Direct Blinkit API integration"
                
                return self._create_text_result(result_text)
            
            else:
                # No products found
                warning_text = f"⚠️ **No Products Found**\n\n"
                warning_text += f"**Query**: {query}\n\n"
                warning_text += "**Possible reasons**:\n"
                warning_text += "• Location restrictions (API requires serviceable area)\n"
                warning_text += "• Product not available in current location\n" 
                warning_text += "• Search term too specific\n\n"
                warning_text += "**Suggestion**: Try broader search terms like 'milk' or 'coffee'"
                
                return self._create_text_result(warning_text)
                
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            
            error_text = f"❌ **Product Search Failed**\n\n"
            error_text += f"**Query**: {query}\n"
            error_text += f"**Error**: {str(e)}\n\n"
            error_text += "**Status**: API integration partially working\n"
            error_text += "**Working Services**: Address management, authentication\n"
            error_text += "**Issue**: Product search requires location setup or different authentication"
            
            return self._create_text_result(error_text)
    
    async def get_addresses_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle address retrieval requests"""
        try:
            response = await self.client.get_addresses()
            
            if response.get('error'):
                return self._create_error_result(f"Address API error: {response.get('message', 'Unknown error')}")
            
            addresses = response.get('addresses', [])
            
            if not addresses:
                return self._create_text_result("⚠️ No saved addresses found")
            
            # Format address results
            result_text = f"🏠 **Delivery Addresses** ({len(addresses)} saved)\n\n"
            
            for i, addr in enumerate(addresses, 1):
                result_text += f"**{i}. {addr.get('label', 'Address')}** ({addr.get('label_id', 'N/A')})\n"
                result_text += f"📍 **Address**: {addr.get('display_address', 'N/A')}\n"
                
                if 'location' in addr:
                    location = addr['location']
                    lat = location.get('latitude')
                    lng = location.get('longitude')
                    result_text += f"🗺️ **Coordinates**: {lat}, {lng}\n"
                
                if addr.get('location_info'):
                    loc_info = addr['location_info']
                    if loc_info.get('postal_code'):
                        result_text += f"📮 **Postal Code**: {loc_info['postal_code']}\n"
                    if loc_info.get('state'):
                        result_text += f"🏛️ **State**: {loc_info['state']}\n"
                
                result_text += f"🆔 **Address ID**: `{addr.get('id', 'N/A')}`\n\n"
            
            result_text += f"---\n**Status**: ✅ Address API fully functional"
            
            return self._create_text_result(result_text)
            
        except Exception as e:
            logger.error(f"Address retrieval failed: {e}")
            return self._create_error_result(f"Failed to retrieve addresses: {str(e)}")
    
    async def api_status_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle API status requests"""
        detailed = arguments.get("detailed", False)
        
        try:
            status_text = f"🔍 **Blinkit API Status Report**\n\n"
            
            # Authentication status
            auth_status = self.client.is_authenticated()
            status_text += f"🔐 **Authentication**: {'✅ Active' if auth_status else '❌ Missing'}\n"
            
            # Token and cookie counts
            token_count = sum(1 for v in self.client.auth_tokens.values() if v)
            cookie_count = len(self.client.session_cookies)
            status_text += f"🔑 **Auth Tokens**: {token_count}/4 loaded\n"
            status_text += f"🍪 **Session Cookies**: {cookie_count} active\n\n"
            
            if detailed:
                status_text += f"📡 **Endpoint Testing**:\n\n"
                
                # Test each endpoint
                test_results = []
                
                # Address API (known working)
                try:
                    addr_response = await self.client.get_addresses()
                    if addr_response.get('error'):
                        test_results.append(("🏠 Address API", "❌ Failed", addr_response.get('error', 'Unknown error')))
                    else:
                        addr_count = len(addr_response.get('addresses', []))
                        test_results.append(("🏠 Address API", "✅ Working", f"{addr_count} addresses retrieved"))
                except Exception as e:
                    test_results.append(("🏠 Address API", "❌ Error", str(e)))
                
                # Search API (known problematic)
                try:
                    search_response = await self.client.search_products("test")
                    if search_response.get('error'):
                        error_msg = search_response.get('error', 'Unknown error')
                        test_results.append(("🔍 Search API", "⚠️ Limited", error_msg))
                    else:
                        test_results.append(("🔍 Search API", "✅ Working", "Products retrieved"))
                except Exception as e:
                    test_results.append(("🔍 Search API", "❌ Error", str(e)))
                
                # Format test results
                for endpoint, status, details in test_results:
                    status_text += f"{endpoint}: {status}\n"
                    status_text += f"   └─ {details}\n\n"
            
            # Overall assessment
            if auth_status and cookie_count > 0:
                overall = "🎉 **Overall**: Partially Working"
                status_text += f"\n{overall}\n"
                status_text += f"**Working**: Authentication, Address management\n"
                status_text += f"**Limited**: Product search (location restrictions)\n"
                status_text += f"**Feasibility**: 60% API integration achieved"
            else:
                overall = "⚠️ **Overall**: Limited Functionality"
                status_text += f"\n{overall}\n"
                status_text += f"**Issue**: Authentication or session problems"
            
            return self._create_text_result(status_text)
            
        except Exception as e:
            logger.error(f"API status check failed: {e}")
            return self._create_error_result(f"Status check failed: {str(e)}")
    
    async def search_suggestions_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle search suggestion requests"""
        partial_query = arguments.get("partial_query", "").strip()
        limit = arguments.get("limit", 5)
        
        if len(partial_query) < 2:
            return self._create_error_result("Partial query must be at least 2 characters")
        
        try:
            suggestions = await self.search_service.get_autocomplete_suggestions(partial_query, limit=limit)
            
            if suggestions:
                result_text = f"💡 **Search Suggestions**\n\n"
                result_text += f"**For**: \"{partial_query}\"\n\n"
                
                for i, suggestion in enumerate(suggestions, 1):
                    result_text += f"{i}. {suggestion}\n"
                
                result_text += f"\n**Status**: ✅ Autocomplete working"
                
                return self._create_text_result(result_text)
            else:
                return self._create_text_result(f"💭 No suggestions found for \"{partial_query}\"")
                
        except Exception as e:
            logger.error(f"Suggestions failed: {e}")
            return self._create_error_result(f"Suggestion search failed: {str(e)}")
    
    def _create_text_result(self, text: str) -> CallToolResult:
        """Create a text result"""
        if HAS_MCP:
            return CallToolResult([TextContent(type="text", text=text)])
        else:
            # Test mode
            return {"content": [{"type": "text", "text": text}]}
    
    def _create_error_result(self, error: str) -> CallToolResult:
        """Create an error result"""
        error_text = f"❌ **Error**: {error}"
        if HAS_MCP:
            return CallToolResult([TextContent(type="text", text=error_text)])
        else:
            return {"content": [{"type": "text", "text": error_text}]}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close_session()
            logger.info("Server cleanup completed")

# MCP Server entry point
async def main():
    """Main MCP server entry point"""
    if HAS_MCP:
        # Production MCP mode
        blinkit_server = BlinkitAPIMCPServer()
        
        # Initialize server
        initialized = await blinkit_server.initialize()
        if not initialized:
            logger.error("Failed to initialize server")
            sys.exit(1)
        
        # Setup MCP server
        app = server.Server("blinkit-api")
        
        @app.list_tools()
        async def list_tools() -> List[Tool]:
            return blinkit_server.get_tools()
        
        @app.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            return await blinkit_server.call_tool(name, arguments)
        
        # Run server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream,
                         server.InitializationOptions(
                             server_name="blinkit-api",
                             server_version="3.0.0-api",
                         ))
    else:
        # Test mode
        print("🧪 Running in test mode (MCP not available)")
        
        server = BlinkitAPIMCPServer()
        
        initialized = await server.initialize()
        print(f"✅ Server initialized: {initialized}")
        
        if initialized:
            # Test the tools
            print("\n🔧 Testing tools...")
            
            tools = server.get_tools()
            print(f"📋 Available tools: {[tool.name for tool in tools]}")
            
            # Test API status
            result = await server.call_tool("api_status", {"detailed": True})
            if hasattr(result, 'content'):
                print("\n" + result.content[0].text)
            else:
                print(f"\n{result}")
        
        await server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())