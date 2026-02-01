"""
Cart Management Module - Handles shopping cart operations via API
"""

import logging
from typing import List, Dict, Any, Optional

from .client import BlinkitAPIClient
from .models import Cart, CartItem
from .exceptions import CartError, ProductNotFoundError

logger = logging.getLogger(__name__)

class BlinkitCart:
    """
    Shopping Cart Manager
    Handles cart operations through direct API calls
    """
    
    def __init__(self, client: BlinkitAPIClient):
        self.client = client
        self._cart_cache: Optional[Cart] = None
    
    async def get_cart(self) -> Cart:
        """
        Get current cart contents
        """
        cart_endpoints = [
            "/v2/cart/",
            "/api/cart",
            "/v1/cart/details",
            "/cart"
        ]
        
        last_error = None
        for endpoint in cart_endpoints:
            try:
                logger.info(f"Fetching cart via {endpoint}")
                
                response = await self.client.get(endpoint)
                
                if self._is_valid_cart_response(response):
                    cart = self._parse_cart_response(response)
                    self._cart_cache = cart
                    return cart
                    
            except Exception as e:
                logger.warning(f"Cart endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        # Return empty cart if all endpoints fail
        logger.error(f"All cart endpoints failed: {last_error}")
        empty_cart = Cart(
            items=[],
            total_items=0,
            subtotal=0.0,
            total_amount=0.0
        )
        self._cart_cache = empty_cart
        return empty_cart
    
    async def add_to_cart(self, product_id: str, quantity: int = 1) -> bool:
        """
        Add product to cart
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        add_endpoints = [
            "/v2/cart/add/",
            "/api/cart/add",
            "/v1/cart/items",
            "/cart/add"
        ]
        
        add_data = {
            "product_id": product_id,
            "quantity": quantity,
            "action": "add"
        }
        
        last_error = None
        for endpoint in add_endpoints:
            try:
                logger.info(f"Adding to cart via {endpoint}: product {product_id}, qty {quantity}")
                
                response = await self.client.post(endpoint, data=add_data)
                
                if self._is_successful_cart_operation(response):
                    logger.info(f"Successfully added product {product_id} to cart")
                    # Invalidate cache
                    self._cart_cache = None
                    return True
                    
            except Exception as e:
                logger.warning(f"Add to cart endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise CartError(f"Failed to add product {product_id} to cart: {last_error}")
    
    async def update_cart_item(self, product_id: str, quantity: int) -> bool:
        """
        Update quantity of item in cart
        """
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        if quantity == 0:
            return await self.remove_from_cart(product_id)
        
        update_endpoints = [
            "/v2/cart/update/",
            "/api/cart/update",
            f"/v1/cart/items/{product_id}",
            "/cart/update"
        ]
        
        update_data = {
            "product_id": product_id,
            "quantity": quantity,
            "action": "update"
        }
        
        last_error = None
        for endpoint in update_endpoints:
            try:
                logger.info(f"Updating cart via {endpoint}: product {product_id}, qty {quantity}")
                
                # Try both POST and PUT methods
                for method in ['post', 'put']:
                    try:
                        if method == 'post':
                            response = await self.client.post(endpoint, data=update_data)
                        else:
                            response = await self.client.put(endpoint, data=update_data)
                        
                        if self._is_successful_cart_operation(response):
                            logger.info(f"Successfully updated product {product_id} quantity to {quantity}")
                            self._cart_cache = None
                            return True
                    except Exception:
                        continue
                        
            except Exception as e:
                logger.warning(f"Update cart endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise CartError(f"Failed to update product {product_id} in cart: {last_error}")
    
    async def remove_from_cart(self, product_id: str) -> bool:
        """
        Remove product from cart completely
        """
        remove_endpoints = [
            "/v2/cart/remove/",
            "/api/cart/remove",
            f"/v1/cart/items/{product_id}",
            "/cart/remove"
        ]
        
        remove_data = {
            "product_id": product_id,
            "action": "remove"
        }
        
        last_error = None
        for endpoint in remove_endpoints:
            try:
                logger.info(f"Removing from cart via {endpoint}: product {product_id}")
                
                # Try DELETE method first, then POST
                for method in ['delete', 'post']:
                    try:
                        if method == 'delete':
                            response = await self.client.delete(endpoint)
                        else:
                            response = await self.client.post(endpoint, data=remove_data)
                        
                        if self._is_successful_cart_operation(response):
                            logger.info(f"Successfully removed product {product_id} from cart")
                            self._cart_cache = None
                            return True
                    except Exception:
                        continue
                        
            except Exception as e:
                logger.warning(f"Remove from cart endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise CartError(f"Failed to remove product {product_id} from cart: {last_error}")
    
    async def clear_cart(self) -> bool:
        """
        Clear all items from cart
        """
        clear_endpoints = [
            "/v2/cart/clear/",
            "/api/cart/clear",
            "/v1/cart/clear",
            "/cart/clear"
        ]
        
        last_error = None
        for endpoint in clear_endpoints:
            try:
                logger.info(f"Clearing cart via {endpoint}")
                
                response = await self.client.post(endpoint, data={})
                
                if self._is_successful_cart_operation(response):
                    logger.info("Successfully cleared cart")
                    self._cart_cache = None
                    return True
                    
            except Exception as e:
                logger.warning(f"Clear cart endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise CartError(f"Failed to clear cart: {last_error}")
    
    def _is_valid_cart_response(self, response: Dict[str, Any]) -> bool:
        """Check if response contains valid cart data"""
        if not response:
            return False
        
        # Look for cart indicators
        cart_indicators = [
            'items' in response,
            'cart' in response,
            'products' in response,
            'total' in response or 'total_amount' in response
        ]
        
        return any(cart_indicators)
    
    def _is_successful_cart_operation(self, response: Dict[str, Any]) -> bool:
        """Check if cart operation was successful"""
        if not response:
            return False
        
        success_indicators = [
            response.get('success') is True,
            response.get('status') == 'success',
            response.get('error') is None,
            'cart' in response,
            response.get('message', '').lower().find('success') != -1
        ]
        
        return any(success_indicators)
    
    def _parse_cart_response(self, response: Dict[str, Any]) -> Cart:
        """Parse cart data from API response"""
        try:
            # Handle different response structures
            cart_data = response
            if 'cart' in response:
                cart_data = response['cart']
            elif 'data' in response:
                cart_data = response['data']
            
            # Parse cart items
            items = []
            item_lists = [
                cart_data.get('items', []),
                cart_data.get('products', []),
                cart_data.get('cart_items', [])
            ]
            
            for item_list in item_lists:
                if item_list:
                    for item_data in item_list:
                        cart_item = self._parse_cart_item(item_data)
                        if cart_item:
                            items.append(cart_item)
                    break
            
            # Extract totals
            subtotal = self._extract_amount(cart_data, ['subtotal', 'sub_total', 'items_total'])
            delivery_fee = self._extract_amount(cart_data, ['delivery_fee', 'shipping_fee', 'delivery_charge'])
            taxes = self._extract_amount(cart_data, ['taxes', 'tax', 'gst', 'vat'])
            total_amount = self._extract_amount(cart_data, ['total', 'total_amount', 'grand_total'])
            
            # If total_amount is not available, calculate it
            if total_amount == 0.0 and subtotal > 0:
                total_amount = subtotal + delivery_fee + taxes
            
            return Cart(
                items=items,
                total_items=len(items),
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                taxes=taxes,
                total_amount=total_amount,
                min_order_value=cart_data.get('min_order_value')
            )
            
        except Exception as e:
            logger.error(f"Error parsing cart response: {e}")
            return Cart(items=[], total_items=0, subtotal=0.0, total_amount=0.0)
    
    def _parse_cart_item(self, item_data: Dict[str, Any]) -> Optional[CartItem]:
        """Parse individual cart item"""
        try:
            product_id = str(item_data.get('product_id') or item_data.get('id') or item_data.get('sku'))
            if not product_id:
                return None
            
            product_name = (item_data.get('name') or 
                          item_data.get('product_name') or 
                          item_data.get('title') or 
                          'Unknown Product')
            
            quantity = int(item_data.get('quantity', 1))
            price = float(item_data.get('price', 0) or item_data.get('unit_price', 0))
            total_price = float(item_data.get('total_price', 0) or item_data.get('line_total', 0))
            
            # Calculate total if not provided
            if total_price == 0.0 and price > 0:
                total_price = price * quantity
            
            max_quantity = item_data.get('max_quantity') or item_data.get('stock_limit')
            
            return CartItem(
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                price=price,
                total_price=total_price,
                max_quantity=max_quantity
            )
            
        except Exception as e:
            logger.error(f"Error parsing cart item: {e}")
            return None
    
    def _extract_amount(self, data: Dict[str, Any], field_names: List[str]) -> float:
        """Extract monetary amount from data"""
        for field in field_names:
            value = data.get(field)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return 0.0