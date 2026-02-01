"""
Search & Products Module - Handles product search and details via API
"""

import logging
from typing import List, Dict, Any, Optional

from .client import BlinkitAPIClient
from .models import Product, SearchResult
from .exceptions import ProductNotFoundError

logger = logging.getLogger(__name__)

class BlinkitSearch:
    """
    Product Search and Details Manager
    Handles search queries and product information retrieval
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
        Search for products using discovered API endpoints
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        # Based on discovered endpoints, try different search patterns
        search_endpoints = [
            "/v2/search/",
            "/api/search",
            "/v1/search/products",
            "/search"
        ]
        
        search_params = {
            "q": query.strip(),
            "limit": limit,
            "offset": offset,
            "include_out_of_stock": "true"
        }
        
        # Add location if provided
        if location:
            search_params.update({
                "lat": location.get("latitude"),
                "lng": location.get("longitude"),
                "pincode": location.get("pincode")
            })
        
        last_error = None
        for endpoint in search_endpoints:
            try:
                logger.info(f"Searching products via {endpoint}: '{query}'")
                
                response = await self.client.get(endpoint, params=search_params)
                
                if self._is_valid_search_response(response):
                    products = self._parse_products_from_response(response)
                    
                    return SearchResult(
                        query=query,
                        total_results=response.get('total', len(products)),
                        products=products,
                        page=offset // limit + 1,
                        has_more=response.get('has_more', len(products) == limit)
                    )
                    
            except Exception as e:
                logger.warning(f"Search endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        # If all endpoints fail, return empty results
        logger.error(f"All search endpoints failed for query '{query}': {last_error}")
        return SearchResult(
            query=query,
            total_results=0,
            products=[],
            page=1,
            has_more=False
        )
    
    async def get_product_details(self, product_id: str) -> Product:
        """
        Get detailed product information
        """
        detail_endpoints = [
            f"/v2/products/{product_id}/",
            f"/api/products/{product_id}",
            f"/v1/products/{product_id}/details"
        ]
        
        last_error = None
        for endpoint in detail_endpoints:
            try:
                logger.info(f"Fetching product details: {product_id}")
                
                response = await self.client.get(endpoint)
                
                if response and 'id' in response:
                    return self._parse_single_product(response)
                    
            except Exception as e:
                logger.warning(f"Product detail endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise ProductNotFoundError(f"Product {product_id} not found: {last_error}")
    
    async def get_autocomplete_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions/autocomplete
        """
        autocomplete_endpoints = [
            "/v2/search/autocomplete/",
            "/api/search/suggest",
            "/v1/autocomplete"
        ]
        
        params = {
            "q": query,
            "limit": limit
        }
        
        for endpoint in autocomplete_endpoints:
            try:
                response = await self.client.get(endpoint, params=params)
                
                if response and 'suggestions' in response:
                    return response['suggestions'][:limit]
                elif isinstance(response, list):
                    return [str(item) for item in response[:limit]]
                    
            except Exception as e:
                logger.warning(f"Autocomplete endpoint {endpoint} failed: {e}")
                continue
        
        return []
    
    def _is_valid_search_response(self, response: Dict[str, Any]) -> bool:
        """Check if search response is valid"""
        if not response:
            return False
        
        # Look for common search response indicators
        indicators = [
            'products' in response,
            'results' in response,
            'items' in response,
            'data' in response and isinstance(response['data'], list)
        ]
        
        return any(indicators)
    
    def _parse_products_from_response(self, response: Dict[str, Any]) -> List[Product]:
        """Parse products from API response"""
        products = []
        
        # Try different response structures
        product_lists = [
            response.get('products', []),
            response.get('results', []),
            response.get('items', []),
            response.get('data', []) if isinstance(response.get('data'), list) else []
        ]
        
        for product_list in product_lists:
            if product_list:
                for item in product_list:
                    try:
                        product = self._parse_single_product(item)
                        if product:
                            products.append(product)
                    except Exception as e:
                        logger.warning(f"Failed to parse product: {e}")
                        continue
                break
        
        return products
    
    def _parse_single_product(self, item: Dict[str, Any]) -> Optional[Product]:
        """Parse single product from API response"""
        try:
            # Handle different field name patterns
            product_id = str(item.get('id') or item.get('product_id') or item.get('sku'))
            if not product_id:
                return None
            
            # Product name
            name = (item.get('name') or 
                   item.get('title') or 
                   item.get('product_name') or 
                   'Unknown Product')
            
            # Price handling
            price = self._extract_price(item)
            original_price = self._extract_original_price(item)
            
            # Stock status
            in_stock = self._extract_stock_status(item)
            
            # Additional fields
            brand = item.get('brand') or item.get('brand_name')
            category = item.get('category') or item.get('category_name')
            unit = item.get('unit') or item.get('quantity_unit')
            image_url = self._extract_image_url(item)
            max_quantity = item.get('max_quantity') or item.get('stock_quantity')
            
            # Calculate discount
            discount = None
            if original_price and price and original_price > price:
                discount = round(((original_price - price) / original_price) * 100, 2)
            
            return Product(
                id=product_id,
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
            logger.error(f"Error parsing product: {e}")
            return None
    
    def _extract_price(self, item: Dict[str, Any]) -> float:
        """Extract price from product data"""
        price_fields = ['price', 'selling_price', 'discounted_price', 'final_price', 'mrp']
        
        for field in price_fields:
            value = item.get(field)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        return 0.0
    
    def _extract_original_price(self, item: Dict[str, Any]) -> Optional[float]:
        """Extract original/MRP from product data"""
        original_fields = ['original_price', 'mrp', 'list_price', 'base_price']
        
        for field in original_fields:
            value = item.get(field)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_stock_status(self, item: Dict[str, Any]) -> bool:
        """Extract stock status"""
        # Check explicit stock fields
        if 'in_stock' in item:
            return bool(item['in_stock'])
        if 'available' in item:
            return bool(item['available'])
        if 'stock_status' in item:
            return item['stock_status'].lower() in ['available', 'in_stock', 'true']
        
        # Check quantity
        if 'quantity' in item or 'stock_quantity' in item:
            qty = item.get('quantity') or item.get('stock_quantity')
            try:
                return int(qty) > 0
            except (ValueError, TypeError):
                pass
        
        # Default to available if no stock info
        return True
    
    def _extract_image_url(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract product image URL"""
        image_fields = ['image_url', 'image', 'thumbnail', 'photo', 'picture']
        
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
                return first_image.get('url') or first_image.get('src')
        
        return None