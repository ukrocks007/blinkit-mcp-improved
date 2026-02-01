"""
API Exceptions - Custom exceptions for Blinkit API operations
"""

class BlinkitAPIError(Exception):
    """Base exception for all Blinkit API errors"""
    pass

class AuthenticationError(BlinkitAPIError):
    """Raised when authentication fails"""
    pass

class RateLimitError(BlinkitAPIError):
    """Raised when API rate limit is exceeded"""
    pass

class ProductNotFoundError(BlinkitAPIError):
    """Raised when a product is not found"""
    pass

class CartError(BlinkitAPIError):
    """Raised for cart-related errors"""
    pass

class OrderError(BlinkitAPIError):
    """Raised for order-related errors"""
    pass

class NetworkError(BlinkitAPIError):
    """Raised for network-related issues"""
    pass

class ValidationError(BlinkitAPIError):
    """Raised for data validation errors"""
    pass