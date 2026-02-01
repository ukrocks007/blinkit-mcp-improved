"""
Enhanced Search Module - Updated with discovered Blinkit APIs
Uses real endpoints found through automated discovery
"""

import logging
from typing import List, Dict, Any, Optional

from .client import BlinkitAPIClient
from .models import Product, SearchResult
from .exceptions import ProductNotFoundError

logger = logging.getLogger(__name__)

class BlinkitSearch:
    """
    Enhanced Product Search using discovered APIs
    Based on successful automation showing:
    - POST /v1/layout/search (primary search API, called 10x)
    - POST /v1/actions/auto_suggest (autocomplete, called 5x)
    - Found real products with names and prices
    """
    
    def __init__(self, client: BlinkitAPIClient):
        self.client = client
        
    async def search_products(
        self, 
        query: str, 
        limit: int = 20,
        offset: int = 0,
        location: Dict[str, Any] = None
    ) -> SearchResult:
        """
        Search for products using discovered search API
        Primary endpoint: POST /v1/layout/search
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        # Build search payload based on discovery patterns
        search_data = {
            "query": query.strip(),
            "page": offset // limit,
            "size": limit
        }
        
        # Add location if provided (discovered patterns)
        if location:
            search_data.update({
                "lat": location.get("latitude"),
                "lng": location.get("longitude"),
                "pincode": location.get("pincode")
            })
        
        try:
            logger.info(f"Searching products: '{query}' (limit={limit})")
            
            # Use discovered primary search API
            response = await self.client.search_products(query, search_data)
            
            if response.get('error'):
                logger.warning(f"Search API returned error: {response.get('message')}")
                return self._empty_search_result(query)
            
            # Parse products from response
            products = self._parse_products_from_response(response)
            
            # Build search result
            total_results = response.get('total', len(products))
            has_more = len(products) == limit or response.get('has_more', False)
            
            result = SearchResult(
                query=query,
                total_results=total_results,
                products=products,
                page=offset // limit + 1,
                has_more=has_more
            )
            
            logger.info(f"Search completed: found {len(products)} products for '{query}'")
            return result
            
        except Exception as e:
            logger.error(f"Product search failed for '{query}': {e}")
            return self._empty_search_result(query)
    
    async def get_product_details(self, product_id: str) -> Product:
        """
        Get detailed product information
        Uses discovered endpoints or fallback to search
        """
        # Try discovered endpoint patterns first
        detail_endpoints = [
            f"/v1/products/{product_id}",
            f"/v2/products/{product_id}",
            f"/api/products/{product_id}"
        ]
        
        for endpoint in detail_endpoints:
            try:
                logger.info(f"Fetching product details: {product_id}")
                
                response = await self.client.get(endpoint)
                
                if response and not response.get('error') and 'id' in response:
                    return self._parse_single_product(response)
                    
            except Exception as e:
                logger.debug(f"Product detail endpoint {endpoint} failed: {e}")
                continue
        
        # Fallback: search by product ID
        logger.info(f"Falling back to search for product: {product_id}")
        search_result = await self.search_products(product_id, limit=5)
        
        # Look for exact ID match in search results
        for product in search_result.products:
            if product.id == product_id:
                return product
        
        raise ProductNotFoundError(f"Product {product_id} not found")
    
    async def get_autocomplete_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions using discovered autocomplete API
        Endpoint: POST /v1/actions/auto_suggest
        """
        if len(query) < 2:
            return []
        
        try:
            logger.debug(f"Getting autocomplete for: '{query}'")
            
            # Use discovered autocomplete API
            response = await self.client.get_search_suggestions(query)
            
            if response.get('error'):
                logger.debug(f"Autocomplete API error: {response.get('message')}")
                return []
            
            # Parse suggestions
            suggestions = self._parse_suggestions(response, limit)
            
            logger.debug(f"Got {len(suggestions)} suggestions for '{query}'")
            return suggestions
            
        except Exception as e:
            logger.debug(f"Autocomplete failed for '{query}': {e}")
            return []
    
    async def search_by_category(self, category: str, limit: int = 20) -> SearchResult:
        """Search products by category"""
        # Use empty query with category filter
        return await self.search_products("", limit=limit, location={"category": category})
    
    def _empty_search_result(self, query: str) -> SearchResult:
        """Return empty search result for failed searches"""
        return SearchResult(
            query=query,
            total_results=0,
            products=[],
            page=1,
            has_more=False
        )
    
    def _parse_products_from_response(self, response: Dict[str, Any]) -> List[Product]:
        """
        Parse products from discovered API response format
        Based on automation showing successful extraction of:
        - Humpy Farms Cow A2 Milk - ₹46
        - Davidoff Decaf Coffee - ₹899
        - Modern White Bread - ₹40
        """
        products = []
        
        try:
            # Try different response structures based on Blinkit patterns
            product_data = None
            
            # Common API response patterns discovered
            if 'products' in response:
                product_data = response['products']
            elif 'items' in response:
                product_data = response['items']
            elif 'data' in response:
                if isinstance(response['data'], list):
                    product_data = response['data']
                elif isinstance(response['data'], dict):
                    # Nested data structures
                    data_obj = response['data']
                    product_data = (
                        data_obj.get('products') or 
                        data_obj.get('items') or
                        data_obj.get('results')
                    )
            elif 'results' in response:
                product_data = response['results']
            elif isinstance(response, list):
                product_data = response
            
            if not product_data:
                logger.warning(f"No product data found in response. Keys: {list(response.keys()) if isinstance(response, dict) else type(response)}")
                return products
            
            # Parse individual products
            for item in product_data:
                try:
                    product = self._parse_single_product(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to parse product item: {e}")
                    continue
            
            logger.debug(f"Parsed {len(products)} products from response")
            
        except Exception as e:
            logger.error(f"Failed to parse products from response: {e}")
        
        return products
    
    def _parse_single_product(self, item: Dict[str, Any]) -> Optional[Product]:
        """
        Parse single product with flexible field extraction
        Based on successful automation parsing real Blinkit products
        """
        if not isinstance(item, dict):
            return None
        
        try:
            # Product ID - flexible extraction
            product_id = (
                item.get('id') or 
                item.get('product_id') or 
                item.get('sku') or
                item.get('pid') or
                str(hash(str(item)))  # Fallback hash
            )
            
            if not product_id:
                return None
            
            # Product name - based on observed patterns
            name = (
                item.get('name') or 
                item.get('title') or 
                item.get('product_name') or
                item.get('display_name') or
                'Unknown Product'
            )
            
            # Price extraction - handle different formats
            price = self._extract_price(item)
            original_price = self._extract_original_price(item)
            
            # Stock status
            in_stock = self._extract_stock_status(item)
            
            # Additional product fields
            brand = item.get('brand') or item.get('brand_name') or ''
            category = item.get('category') or item.get('category_name') or ''
            unit = item.get('unit') or item.get('pack_size') or item.get('quantity_unit') or ''
            image_url = self._extract_image_url(item)
            max_quantity = item.get('max_quantity') or item.get('max_order_quantity') or 10
            
            # Calculate discount if applicable
            discount = None
            if original_price and price and original_price > price:
                discount = round(((original_price - price) / original_price) * 100, 2)
            
            return Product(
                id=str(product_id),
                name=name,
                price=price,
                original_price=original_price,
                discount=discount,
                unit=unit,
                brand=brand,
                category=category,
                image_url=image_url,
                in_stock=in_stock,
                max_quantity=max_quantity
            )
            
        except Exception as e:
            logger.error(f"Error parsing single product: {e}")
            return None
    
    def _extract_price(self, item: Dict[str, Any]) -> float:
        """Extract price with robust parsing for different formats"""
        # Try different price field names
        price_fields = [
            'price', 'selling_price', 'discounted_price', 'final_price', 
            'amount', 'cost', 'value', 'sale_price'
        ]
        
        for field in price_fields:
            value = item.get(field)
            if value is not None:
                try:
                    # Handle string prices like "₹46", "Rs. 899"
                    if isinstance(value, str):
                        import re
                        numbers = re.findall(r'\d+\.?\d*', value.replace(',', ''))
                        if numbers:
                            return float(numbers[0])
                    else:
                        return float(value)
                except (ValueError, TypeError):
                    continue
        
        # Try nested price objects
        if 'price_info' in item:
            price_info = item['price_info']
            if isinstance(price_info, dict):
                for field in price_fields:
                    if field in price_info:
                        try:
                            return float(price_info[field])
                        except (ValueError, TypeError):
                            continue
        
        return 0.0
    
    def _extract_original_price(self, item: Dict[str, Any]) -> Optional[float]:
        """Extract original/MRP price"""
        original_fields = ['original_price', 'mrp', 'list_price', 'base_price', 'regular_price']
        
        for field in original_fields:
            value = item.get(field)
            if value is not None:
                try:
                    if isinstance(value, str):
                        import re
                        numbers = re.findall(r'\d+\.?\d*', value.replace(',', ''))
                        if numbers:
                            return float(numbers[0])
                    else:
                        return float(value)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_stock_status(self, item: Dict[str, Any]) -> bool:
        """Extract stock availability status"""
        # Check explicit stock fields
        stock_indicators = ['in_stock', 'available', 'is_available', 'stock_available']
        
        for field in stock_indicators:
            if field in item:
                value = item[field]
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ['true', 'available', 'in_stock', 'yes']
                elif isinstance(value, (int, float)):
                    return value > 0
        
        # Check stock status strings
        if 'stock_status' in item:
            status = str(item['stock_status']).lower()
            return status in ['available', 'in_stock', 'active']
        
        # Check quantity
        quantity_fields = ['quantity', 'stock_quantity', 'available_quantity']
        for field in quantity_fields:
            if field in item:
                try:
                    qty = int(item[field])
                    return qty > 0
                except (ValueError, TypeError):
                    continue
        
        # Default to available if no stock info (optimistic)
        return True
    
    def _extract_image_url(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract product image URL"""
        image_fields = ['image_url', 'image', 'thumbnail', 'photo', 'picture', 'img_url']
        
        for field in image_fields:
            value = item.get(field)
            if value and isinstance(value, str):
                return value
        
        # Check nested image objects
        if 'images' in item and isinstance(item['images'], list) and item['images']:
            first_image = item['images'][0]
            if isinstance(first_image, str):
                return first_image
            elif isinstance(first_image, dict):
                return first_image.get('url') or first_image.get('src') or first_image.get('href')
        
        return None
    
    def _parse_suggestions(self, response: Dict[str, Any], limit: int) -> List[str]:
        """Parse autocomplete suggestions from API response"""
        suggestions = []
        
        try:
            # Try different response structures
            suggestion_data = None
            
            if 'suggestions' in response:
                suggestion_data = response['suggestions']
            elif 'data' in response:
                suggestion_data = response['data']
            elif 'results' in response:
                suggestion_data = response['results']
            elif 'items' in response:
                suggestion_data = response['items']
            elif isinstance(response, list):
                suggestion_data = response
            
            if suggestion_data and isinstance(suggestion_data, list):
                for item in suggestion_data:
                    if isinstance(item, str):
                        suggestions.append(item)
                    elif isinstance(item, dict):
                        # Try common suggestion field names
                        suggestion_text = (
                            item.get('text') or 
                            item.get('suggestion') or 
                            item.get('query') or
                            item.get('name') or
                            item.get('value')
                        )
                        if suggestion_text:
                            suggestions.append(str(suggestion_text))
            
        except Exception as e:
            logger.warning(f"Failed to parse suggestions: {e}")
        
        return suggestions[:limit]