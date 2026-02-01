"""
Data Models - Pydantic models for API request/response data
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

@dataclass
class LoginRequest:
    """Login request payload"""
    phone_number: str
    country_code: str = "+91"

@dataclass
class OTPRequest:
    """OTP verification request"""
    phone_number: str
    otp: str
    session_id: Optional[str] = None

@dataclass
class LoginResponse:
    """Login response data"""
    success: bool
    auth_token: Optional[str] = None
    refresh_token: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None

@dataclass
class Product:
    """Product information"""
    id: str
    name: str
    price: float
    original_price: Optional[float] = None
    discount: Optional[float] = None
    unit: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    in_stock: bool = True
    max_quantity: Optional[int] = None

@dataclass
class SearchResult:
    """Search results"""
    query: str
    total_results: int
    products: List[Product]
    page: int = 1
    has_more: bool = False

@dataclass
class CartItem:
    """Cart item"""
    product_id: str
    product_name: str
    quantity: int
    price: float
    total_price: float
    max_quantity: Optional[int] = None

@dataclass
class Cart:
    """Shopping cart"""
    items: List[CartItem]
    total_items: int
    subtotal: float
    delivery_fee: float = 0.0
    taxes: float = 0.0
    total_amount: float = 0.0
    min_order_value: Optional[float] = None

@dataclass
class Address:
    """Delivery address"""
    id: str
    type: str  # "home", "work", "other"
    line1: str
    city: str
    state: str
    pincode: str
    line2: Optional[str] = None
    landmark: Optional[str] = None
    is_default: bool = False

class PaymentMethod(Enum):
    """Payment methods"""
    COD = "cod"
    UPI = "upi"
    CARD = "card"
    WALLET = "wallet"

@dataclass
class PaymentOption:
    """Payment option"""
    method: PaymentMethod
    display_name: str
    available: bool = True
    extra_data: Optional[Dict[str, Any]] = None

class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass
class Order:
    """Order information"""
    id: str
    status: OrderStatus
    items: List[CartItem]
    delivery_address: Address
    payment_method: PaymentMethod
    total_amount: float
    created_at: datetime
    estimated_delivery: Optional[datetime] = None
    tracking_url: Optional[str] = None

@dataclass
class APIEndpoint:
    """API endpoint definition"""
    name: str
    method: str
    path: str
    requires_auth: bool = True
    description: Optional[str] = None

# Common API endpoints (to be updated from discovery)
class Endpoints:
    """API endpoint definitions"""
    
    # Authentication
    LOGIN = APIEndpoint("login", "POST", "/api/auth/login", requires_auth=False)
    VERIFY_OTP = APIEndpoint("verify_otp", "POST", "/api/auth/verify", requires_auth=False)
    REFRESH_TOKEN = APIEndpoint("refresh", "POST", "/api/auth/refresh", requires_auth=True)
    
    # Search & Products
    SEARCH = APIEndpoint("search", "GET", "/api/search")
    PRODUCT_DETAIL = APIEndpoint("product", "GET", "/api/products/{product_id}")
    
    # Cart Operations
    CART_GET = APIEndpoint("cart_get", "GET", "/api/cart")
    CART_ADD = APIEndpoint("cart_add", "POST", "/api/cart/add")
    CART_UPDATE = APIEndpoint("cart_update", "PUT", "/api/cart/update")
    CART_REMOVE = APIEndpoint("cart_remove", "DELETE", "/api/cart/remove")
    
    # Address Management
    ADDRESSES_GET = APIEndpoint("addresses", "GET", "/api/addresses")
    ADDRESS_CREATE = APIEndpoint("address_create", "POST", "/api/addresses")
    
    # Checkout & Orders
    CHECKOUT = APIEndpoint("checkout", "POST", "/api/checkout")
    PAYMENT_METHODS = APIEndpoint("payment_methods", "GET", "/api/payment-methods")
    PLACE_ORDER = APIEndpoint("place_order", "POST", "/api/orders")
    ORDER_STATUS = APIEndpoint("order_status", "GET", "/api/orders/{order_id}")
    
    @classmethod
    def get_all(cls) -> List[APIEndpoint]:
        """Get all defined endpoints"""
        return [getattr(cls, attr) for attr in dir(cls) 
                if isinstance(getattr(cls, attr), APIEndpoint)]
    
    @classmethod
    def update_from_discovery(cls, discovered_endpoints: List[str]):
        """Update endpoint paths based on API discovery"""
        # This will be implemented once we have discovery results
        pass