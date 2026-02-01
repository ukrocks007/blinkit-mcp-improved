"""
Checkout & Orders Module - Handles order placement and payment via API
"""

import logging
from typing import List, Dict, Any, Optional

from .client import BlinkitAPIClient
from .models import Address, PaymentOption, PaymentMethod, Order, OrderStatus
from .exceptions import OrderError, ValidationError

logger = logging.getLogger(__name__)

class BlinkitCheckout:
    """
    Checkout and Order Management
    Handles address selection, payment, and order placement
    """
    
    def __init__(self, client: BlinkitAPIClient):
        self.client = client
    
    async def get_addresses(self) -> List[Address]:
        """
        Get user's saved delivery addresses
        """
        address_endpoints = [
            "/v2/addresses/",
            "/api/addresses",
            "/v1/user/addresses",
            "/addresses"
        ]
        
        last_error = None
        for endpoint in address_endpoints:
            try:
                logger.info(f"Fetching addresses via {endpoint}")
                
                response = await self.client.get(endpoint)
                
                if self._is_valid_addresses_response(response):
                    addresses = self._parse_addresses_response(response)
                    logger.info(f"Found {len(addresses)} saved addresses")
                    return addresses
                    
            except Exception as e:
                logger.warning(f"Address endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        logger.error(f"All address endpoints failed: {last_error}")
        return []
    
    async def add_address(self, address: Address) -> bool:
        """
        Add new delivery address
        """
        add_address_endpoints = [
            "/v2/addresses/",
            "/api/addresses",
            "/v1/user/addresses/add"
        ]
        
        address_data = {
            "type": address.type,
            "line1": address.line1,
            "line2": address.line2,
            "city": address.city,
            "state": address.state,
            "pincode": address.pincode,
            "landmark": address.landmark,
            "is_default": address.is_default
        }
        
        # Remove None values
        address_data = {k: v for k, v in address_data.items() if v is not None}
        
        last_error = None
        for endpoint in add_address_endpoints:
            try:
                logger.info(f"Adding address via {endpoint}")
                
                response = await self.client.post(endpoint, data=address_data)
                
                if self._is_successful_operation(response):
                    logger.info("Address added successfully")
                    return True
                    
            except Exception as e:
                logger.warning(f"Add address endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise OrderError(f"Failed to add address: {last_error}")
    
    async def get_payment_methods(self) -> List[PaymentOption]:
        """
        Get available payment methods
        """
        payment_endpoints = [
            "/v2/payment/methods/",
            "/api/payment-methods",
            "/v1/checkout/payment-options",
            "/payment/methods"
        ]
        
        last_error = None
        for endpoint in payment_endpoints:
            try:
                logger.info(f"Fetching payment methods via {endpoint}")
                
                response = await self.client.get(endpoint)
                
                if self._is_valid_payment_methods_response(response):
                    payment_methods = self._parse_payment_methods_response(response)
                    logger.info(f"Found {len(payment_methods)} payment methods")
                    return payment_methods
                    
            except Exception as e:
                logger.warning(f"Payment methods endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        # Return default payment methods if API fails
        logger.warning("Using default payment methods")
        return [
            PaymentOption(method=PaymentMethod.COD, display_name="Cash on Delivery"),
            PaymentOption(method=PaymentMethod.UPI, display_name="UPI"),
            PaymentOption(method=PaymentMethod.CARD, display_name="Credit/Debit Card")
        ]
    
    async def place_order(
        self, 
        address_id: str, 
        payment_method: PaymentMethod,
        payment_details: Dict[str, Any] = None
    ) -> Order:
        """
        Place order with selected address and payment method
        """
        order_endpoints = [
            "/v2/orders/",
            "/api/orders/place",
            "/v1/checkout/place-order",
            "/orders/create"
        ]
        
        order_data = {
            "address_id": address_id,
            "payment_method": payment_method.value,
            "payment_details": payment_details or {}
        }
        
        last_error = None
        for endpoint in order_endpoints:
            try:
                logger.info(f"Placing order via {endpoint}")
                
                response = await self.client.post(endpoint, data=order_data)
                
                if self._is_successful_order_response(response):
                    order = self._parse_order_response(response)
                    logger.info(f"Order placed successfully: {order.id}")
                    return order
                    
            except Exception as e:
                logger.warning(f"Place order endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise OrderError(f"Failed to place order: {last_error}")
    
    async def get_order_status(self, order_id: str) -> Order:
        """
        Get order status and details
        """
        status_endpoints = [
            f"/v2/orders/{order_id}/",
            f"/api/orders/{order_id}",
            f"/v1/orders/{order_id}/status"
        ]
        
        last_error = None
        for endpoint in status_endpoints:
            try:
                logger.info(f"Fetching order status via {endpoint}")
                
                response = await self.client.get(endpoint)
                
                if response and 'id' in response:
                    order = self._parse_order_response(response)
                    return order
                    
            except Exception as e:
                logger.warning(f"Order status endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise OrderError(f"Failed to get order status for {order_id}: {last_error}")
    
    async def initiate_checkout(self) -> Dict[str, Any]:
        """
        Initiate checkout process and get available options
        """
        checkout_endpoints = [
            "/v2/checkout/",
            "/api/checkout/init",
            "/v1/checkout/initialize"
        ]
        
        last_error = None
        for endpoint in checkout_endpoints:
            try:
                logger.info(f"Initiating checkout via {endpoint}")
                
                response = await self.client.post(endpoint, data={})
                
                if response:
                    return {
                        'checkout_id': response.get('checkout_id'),
                        'session_id': response.get('session_id'),
                        'available_slots': response.get('delivery_slots', []),
                        'estimated_delivery': response.get('estimated_delivery'),
                        'min_order_value': response.get('min_order_value'),
                        'delivery_fee': response.get('delivery_fee')
                    }
                    
            except Exception as e:
                logger.warning(f"Checkout init endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        logger.error(f"Failed to initiate checkout: {last_error}")
        return {}
    
    def _is_valid_addresses_response(self, response: Dict[str, Any]) -> bool:
        """Check if addresses response is valid"""
        if not response:
            return False
        
        indicators = [
            'addresses' in response,
            'data' in response and isinstance(response['data'], list),
            isinstance(response, list)
        ]
        
        return any(indicators)
    
    def _is_valid_payment_methods_response(self, response: Dict[str, Any]) -> bool:
        """Check if payment methods response is valid"""
        if not response:
            return False
        
        indicators = [
            'payment_methods' in response,
            'methods' in response,
            'data' in response and isinstance(response['data'], list),
            isinstance(response, list)
        ]
        
        return any(indicators)
    
    def _is_successful_operation(self, response: Dict[str, Any]) -> bool:
        """Check if operation was successful"""
        if not response:
            return False
        
        success_indicators = [
            response.get('success') is True,
            response.get('status') == 'success',
            response.get('error') is None,
            'id' in response  # New resource created
        ]
        
        return any(success_indicators)
    
    def _is_successful_order_response(self, response: Dict[str, Any]) -> bool:
        """Check if order placement was successful"""
        if not response:
            return False
        
        success_indicators = [
            response.get('success') is True,
            response.get('status') == 'success',
            'order_id' in response,
            'id' in response and 'status' in response
        ]
        
        return any(success_indicators)
    
    def _parse_addresses_response(self, response: Dict[str, Any]) -> List[Address]:
        """Parse addresses from API response"""
        addresses = []
        
        # Get address list from different response structures
        address_lists = [
            response.get('addresses', []),
            response.get('data', []) if isinstance(response.get('data'), list) else [],
            response if isinstance(response, list) else []
        ]
        
        for address_list in address_lists:
            if address_list:
                for addr_data in address_list:
                    address = self._parse_single_address(addr_data)
                    if address:
                        addresses.append(address)
                break
        
        return addresses
    
    def _parse_single_address(self, addr_data: Dict[str, Any]) -> Optional[Address]:
        """Parse single address from data"""
        try:
            address_id = str(addr_data.get('id') or addr_data.get('address_id'))
            if not address_id:
                return None
            
            return Address(
                id=address_id,
                type=addr_data.get('type', 'other'),
                line1=addr_data.get('line1') or addr_data.get('address_line_1') or '',
                line2=addr_data.get('line2') or addr_data.get('address_line_2'),
                city=addr_data.get('city', ''),
                state=addr_data.get('state', ''),
                pincode=addr_data.get('pincode') or addr_data.get('postal_code') or '',
                landmark=addr_data.get('landmark'),
                is_default=bool(addr_data.get('is_default', False))
            )
            
        except Exception as e:
            logger.error(f"Error parsing address: {e}")
            return None
    
    def _parse_payment_methods_response(self, response: Dict[str, Any]) -> List[PaymentOption]:
        """Parse payment methods from API response"""
        payment_options = []
        
        # Get payment methods list
        method_lists = [
            response.get('payment_methods', []),
            response.get('methods', []),
            response.get('data', []) if isinstance(response.get('data'), list) else [],
            response if isinstance(response, list) else []
        ]
        
        for method_list in method_lists:
            if method_list:
                for method_data in method_list:
                    payment_option = self._parse_single_payment_method(method_data)
                    if payment_option:
                        payment_options.append(payment_option)
                break
        
        return payment_options
    
    def _parse_single_payment_method(self, method_data: Dict[str, Any]) -> Optional[PaymentOption]:
        """Parse single payment method"""
        try:
            method_code = method_data.get('code') or method_data.get('type') or method_data.get('method')
            display_name = method_data.get('name') or method_data.get('display_name') or method_code
            available = bool(method_data.get('available', True))
            
            # Map method codes to enum
            method_mapping = {
                'cod': PaymentMethod.COD,
                'cash_on_delivery': PaymentMethod.COD,
                'upi': PaymentMethod.UPI,
                'card': PaymentMethod.CARD,
                'credit_card': PaymentMethod.CARD,
                'debit_card': PaymentMethod.CARD,
                'wallet': PaymentMethod.WALLET
            }
            
            method_enum = method_mapping.get(method_code.lower()) if method_code else None
            if not method_enum:
                return None
            
            return PaymentOption(
                method=method_enum,
                display_name=display_name,
                available=available,
                extra_data=method_data.get('extra_data')
            )
            
        except Exception as e:
            logger.error(f"Error parsing payment method: {e}")
            return None
    
    def _parse_order_response(self, response: Dict[str, Any]) -> Order:
        """Parse order from API response"""
        try:
            from datetime import datetime
            
            order_id = str(response.get('id') or response.get('order_id'))
            
            # Parse status
            status_str = response.get('status', 'pending').lower()
            status_mapping = {
                'pending': OrderStatus.PENDING,
                'confirmed': OrderStatus.CONFIRMED,
                'preparing': OrderStatus.PREPARING,
                'out_for_delivery': OrderStatus.OUT_FOR_DELIVERY,
                'delivered': OrderStatus.DELIVERED,
                'cancelled': OrderStatus.CANCELLED
            }
            status = status_mapping.get(status_str, OrderStatus.PENDING)
            
            # Parse timestamps
            created_at = datetime.now()
            if 'created_at' in response:
                try:
                    created_at = datetime.fromisoformat(response['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            
            estimated_delivery = None
            if 'estimated_delivery' in response:
                try:
                    estimated_delivery = datetime.fromisoformat(response['estimated_delivery'].replace('Z', '+00:00'))
                except:
                    pass
            
            return Order(
                id=order_id,
                status=status,
                items=[],  # Would need to parse items if included
                delivery_address=Address(id="", type="", line1="", city="", state="", pincode=""),  # Placeholder
                payment_method=PaymentMethod.COD,  # Would parse from response
                total_amount=float(response.get('total_amount', 0)),
                created_at=created_at,
                estimated_delivery=estimated_delivery,
                tracking_url=response.get('tracking_url')
            )
            
        except Exception as e:
            logger.error(f"Error parsing order response: {e}")
            raise OrderError(f"Invalid order response: {e}")