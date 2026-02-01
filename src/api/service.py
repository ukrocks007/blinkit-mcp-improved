"""
Blinkit API Service - High-level integration of all API modules
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .client import BlinkitAPIClient, APIConfig
from .auth import BlinkitAuth
from .search import BlinkitSearch
from .cart import BlinkitCart
from .checkout import BlinkitCheckout
from .models import *
from .exceptions import *

logger = logging.getLogger(__name__)

class BlinkitAPIService:
    """
    High-level Blinkit API Service
    Provides a unified interface for all grocery ordering operations
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
        self.client = BlinkitAPIClient(self.config)
        
        # Initialize modules
        self.auth = BlinkitAuth(self.client)
        self.search = BlinkitSearch(self.client)
        self.cart = BlinkitCart(self.client)
        self.checkout = BlinkitCheckout(self.client)
        
        self._session_started = False
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
    
    async def start(self):
        """Initialize the API service"""
        if not self._session_started:
            await self.client.start_session()
            self._session_started = True
            logger.info("Blinkit API service started")
    
    async def stop(self):
        """Cleanup and close the API service"""
        if self._session_started:
            await self.client.close_session()
            self._session_started = False
            logger.info("Blinkit API service stopped")
    
    # Authentication Methods
    async def login_with_phone_and_otp(self, phone_number: str, otp: str = None) -> LoginResponse:
        """
        Login using phone number and OTP (file-based or direct)
        """
        await self.start()
        
        if otp:
            # Direct OTP login
            login_result = await self.auth.login_with_phone(phone_number)
            session_id = login_result.get('session_id')
            return await self.auth.verify_otp(phone_number, otp, session_id)
        else:
            # File-based OTP (compatible with existing workflow)
            return await self.auth.login_with_otp_file(phone_number)
    
    async def is_logged_in(self) -> bool:
        """Check if user is authenticated"""
        if not self._session_started:
            await self.start()
        return self.auth.is_authenticated()
    
    async def load_saved_session(self) -> bool:
        """Load previously saved authentication session"""
        await self.start()
        return await self.auth.load_session()
    
    # Product Search Methods
    async def search_products(self, query: str, limit: int = 20) -> SearchResult:
        """Search for products"""
        await self.start()
        return await self.search.search_products(query, limit=limit)
    
    async def get_product_details(self, product_id: str) -> Product:
        """Get detailed product information"""
        await self.start()
        return await self.search.get_product_details(product_id)
    
    # Cart Management Methods
    async def get_cart(self) -> Cart:
        """Get current cart contents"""
        await self.start()
        return await self.cart.get_cart()
    
    async def add_to_cart(self, product_id: str, quantity: int = 1) -> bool:
        """Add product to cart"""
        await self.start()
        return await self.cart.add_to_cart(product_id, quantity)
    
    async def update_cart_quantity(self, product_id: str, quantity: int) -> bool:
        """Update product quantity in cart"""
        await self.start()
        return await self.cart.update_cart_item(product_id, quantity)
    
    async def remove_from_cart(self, product_id: str) -> bool:
        """Remove product from cart"""
        await self.start()
        return await self.cart.remove_from_cart(product_id)
    
    async def clear_cart(self) -> bool:
        """Clear all items from cart"""
        await self.start()
        return await self.cart.clear_cart()
    
    # Checkout & Order Methods
    async def get_delivery_addresses(self) -> List[Address]:
        """Get saved delivery addresses"""
        await self.start()
        return await self.checkout.get_addresses()
    
    async def get_payment_methods(self) -> List[PaymentOption]:
        """Get available payment methods"""
        await self.start()
        return await self.checkout.get_payment_methods()
    
    async def place_order(
        self, 
        address_id: str, 
        payment_method: PaymentMethod = PaymentMethod.COD
    ) -> Order:
        """Place order with address and payment method"""
        await self.start()
        return await self.checkout.place_order(address_id, payment_method)
    
    async def get_order_status(self, order_id: str) -> Order:
        """Get order status and tracking information"""
        await self.start()
        return await self.checkout.get_order_status(order_id)
    
    # High-level Workflow Methods
    async def complete_order_workflow(
        self,
        search_query: str,
        product_index: int = 0,
        quantity: int = 1,
        address_index: int = 0,
        payment_method: PaymentMethod = PaymentMethod.COD
    ) -> Dict[str, Any]:
        """
        Complete end-to-end order workflow
        Returns detailed results of each step
        """
        workflow_result = {
            'success': False,
            'steps': {},
            'order': None,
            'error': None
        }
        
        try:
            await self.start()
            
            # Step 1: Search for products
            logger.info(f"Step 1: Searching for '{search_query}'")
            search_result = await self.search_products(search_query, limit=10)
            workflow_result['steps']['search'] = {
                'success': True,
                'products_found': len(search_result.products),
                'query': search_query
            }
            
            if not search_result.products:
                raise ValueError(f"No products found for '{search_query}'")
            
            if product_index >= len(search_result.products):
                raise ValueError(f"Product index {product_index} out of range (found {len(search_result.products)} products)")
            
            selected_product = search_result.products[product_index]
            logger.info(f"Selected product: {selected_product.name} (₹{selected_product.price})")
            
            # Step 2: Add to cart
            logger.info(f"Step 2: Adding {quantity} x {selected_product.name} to cart")
            add_success = await self.add_to_cart(selected_product.id, quantity)
            workflow_result['steps']['add_to_cart'] = {
                'success': add_success,
                'product_id': selected_product.id,
                'product_name': selected_product.name,
                'quantity': quantity
            }
            
            if not add_success:
                raise CartError(f"Failed to add {selected_product.name} to cart")
            
            # Step 3: Get cart contents
            cart = await self.get_cart()
            workflow_result['steps']['cart_verification'] = {
                'success': len(cart.items) > 0,
                'total_items': cart.total_items,
                'total_amount': cart.total_amount
            }
            
            # Step 4: Get delivery addresses
            logger.info("Step 4: Getting delivery addresses")
            addresses = await self.get_delivery_addresses()
            workflow_result['steps']['addresses'] = {
                'success': len(addresses) > 0,
                'addresses_found': len(addresses)
            }
            
            if not addresses:
                raise OrderError("No delivery addresses found. Please add an address first.")
            
            if address_index >= len(addresses):
                raise OrderError(f"Address index {address_index} out of range (found {len(addresses)} addresses)")
            
            selected_address = addresses[address_index]
            logger.info(f"Selected address: {selected_address.type} - {selected_address.city}")
            
            # Step 5: Place order
            logger.info(f"Step 5: Placing order with {payment_method.value} payment")
            order = await self.place_order(selected_address.id, payment_method)
            workflow_result['steps']['order_placement'] = {
                'success': True,
                'order_id': order.id,
                'total_amount': order.total_amount,
                'payment_method': payment_method.value
            }
            
            workflow_result['success'] = True
            workflow_result['order'] = order
            
            logger.info(f"🎉 Order workflow completed successfully! Order ID: {order.id}")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Order workflow failed: {e}")
            workflow_result['error'] = str(e)
            return workflow_result
    
    async def search_and_add_to_cart(
        self,
        search_query: str,
        product_index: int = 0,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Search for products and add selected one to cart
        """
        try:
            await self.start()
            
            # Search
            search_result = await self.search_products(search_query)
            if not search_result.products:
                return {'success': False, 'error': 'No products found'}
            
            if product_index >= len(search_result.products):
                return {'success': False, 'error': f'Product index {product_index} out of range'}
            
            # Add to cart
            selected_product = search_result.products[product_index]
            add_success = await self.add_to_cart(selected_product.id, quantity)
            
            return {
                'success': add_success,
                'product': {
                    'id': selected_product.id,
                    'name': selected_product.name,
                    'price': selected_product.price
                },
                'quantity': quantity,
                'total_products_found': len(search_result.products)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def update_from_discovery_data(self, discovery_file_path: str):
        """
        Update API configuration based on discovery results
        """
        try:
            import json
            with open(discovery_file_path, 'r') as f:
                discovery_data = json.load(f)
            
            # Update client configuration
            await self.client.update_endpoints_from_discovery(discovery_data)
            
            # Update endpoint definitions in models
            from .models import Endpoints
            if 'api_calls' in discovery_data:
                discovered_endpoints = [call['url'] for call in discovery_data['api_calls']]
                Endpoints.update_from_discovery(discovered_endpoints)
            
            logger.info("API configuration updated from discovery data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update from discovery data: {e}")
            return False