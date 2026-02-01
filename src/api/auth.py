"""
Authentication Module - Handles Blinkit login and session management
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .client import BlinkitAPIClient
from .models import LoginRequest, OTPRequest, LoginResponse
from .exceptions import AuthenticationError, ValidationError

logger = logging.getLogger(__name__)

class BlinkitAuth:
    """
    Blinkit Authentication Manager
    Handles phone-based login, OTP verification, and session persistence
    """
    
    def __init__(self, client: BlinkitAPIClient):
        self.client = client
        self.session_file = "/home/user/.blinkit_api_session.json"
        self.current_login: Optional[LoginResponse] = None
        
    async def login_with_phone(self, phone_number: str, country_code: str = "+91") -> Dict[str, Any]:
        """
        Initiate login process with phone number
        Based on discovered endpoints from API analysis
        """
        if not phone_number.isdigit() or len(phone_number) != 10:
            raise ValidationError("Phone number must be 10 digits")
        
        # Try different endpoint patterns discovered from network analysis
        login_endpoints = [
            "/v2/accounts/auth_key/",
            "/api/auth/login",
            "/v1/auth/login",
            "/auth/phone"
        ]
        
        login_data = {
            "phone": phone_number,
            "country_code": country_code.replace("+", ""),
            "device_id": self._generate_device_id(),
            "app_version": "1.0.0",
            "platform": "web"
        }
        
        last_error = None
        for endpoint in login_endpoints:
            try:
                logger.info(f"Trying login endpoint: {endpoint}")
                response = await self.client.post(
                    endpoint, 
                    data=login_data,
                    require_auth=False
                )
                
                if response.get('success') or response.get('status') == 'success':
                    logger.info("Login request successful")
                    return {
                        'status': 'otp_sent',
                        'session_id': response.get('session_id'),
                        'message': 'OTP sent to your phone'
                    }
                    
            except Exception as e:
                logger.warning(f"Login endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise AuthenticationError(f"All login endpoints failed. Last error: {last_error}")
    
    async def verify_otp(self, phone_number: str, otp: str, session_id: str = None) -> LoginResponse:
        """
        Verify OTP and complete authentication
        """
        if not otp.isdigit() or len(otp) not in [4, 6]:
            raise ValidationError("OTP must be 4 or 6 digits")
        
        # Try different OTP verification endpoints
        otp_endpoints = [
            "/v2/accounts/verify/",
            "/api/auth/verify",
            "/v1/auth/verify-otp",
            "/auth/verify"
        ]
        
        otp_data = {
            "phone": phone_number,
            "otp": otp,
            "device_id": self._generate_device_id()
        }
        
        if session_id:
            otp_data["session_id"] = session_id
        
        last_error = None
        for endpoint in otp_endpoints:
            try:
                logger.info(f"Trying OTP verification: {endpoint}")
                response = await self.client.post(
                    endpoint,
                    data=otp_data,
                    require_auth=False
                )
                
                if self._is_successful_response(response):
                    # Extract authentication data
                    auth_token = self._extract_auth_token(response)
                    if auth_token:
                        self.client.set_auth_token(auth_token)
                    
                    # Store session cookies
                    if self.client.session_cookies:
                        self.client.set_session_cookies(self.client.session_cookies)
                    
                    login_response = LoginResponse(
                        success=True,
                        auth_token=auth_token,
                        session_id=response.get('session_id'),
                        user_id=response.get('user_id'),
                        message="Login successful"
                    )
                    
                    self.current_login = login_response
                    await self._save_session(login_response)
                    
                    logger.info("OTP verification successful")
                    return login_response
                    
            except Exception as e:
                logger.warning(f"OTP endpoint {endpoint} failed: {e}")
                last_error = e
                continue
        
        raise AuthenticationError(f"OTP verification failed. Last error: {last_error}")
    
    async def login_with_otp_file(self, phone_number: str, otp_file_path: str = "/tmp/blinkit_otp.txt") -> LoginResponse:
        """
        Complete login using file-based OTP system (compatible with existing workflow)
        """
        # Start login process
        login_result = await self.login_with_phone(phone_number)
        session_id = login_result.get('session_id')
        
        print(f"📱 OTP sent! Please create file: echo 'YOUR_OTP' > {otp_file_path}")
        print("⏳ Waiting for OTP file...")
        
        # Wait for OTP file
        otp = await self._wait_for_otp_file(otp_file_path, timeout=300)  # 5 minutes
        
        if not otp:
            raise AuthenticationError("OTP timeout - no OTP received within 5 minutes")
        
        # Verify OTP
        return await self.verify_otp(phone_number, otp, session_id)
    
    async def _wait_for_otp_file(self, file_path: str, timeout: int = 300) -> Optional[str]:
        """Wait for OTP file to be created and read the OTP"""
        import os
        
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        otp = f.read().strip()
                    
                    # Clean up file
                    os.remove(file_path)
                    
                    if otp and otp.isdigit():
                        print(f"📨 Found OTP: {otp}")
                        return otp
                except Exception as e:
                    logger.warning(f"Error reading OTP file: {e}")
            
            await asyncio.sleep(1)  # Check every second
        
        return None
    
    async def load_session(self) -> bool:
        """Load saved session from file"""
        try:
            import os
            if not os.path.exists(self.session_file):
                return False
            
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is still valid
            if session_data.get('expires_at'):
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if expires_at < datetime.now():
                    logger.info("Saved session expired")
                    return False
            
            # Restore session
            if session_data.get('auth_token'):
                self.client.set_auth_token(session_data['auth_token'])
            
            if session_data.get('cookies'):
                self.client.set_session_cookies(session_data['cookies'])
            
            self.current_login = LoginResponse(
                success=True,
                auth_token=session_data.get('auth_token'),
                session_id=session_data.get('session_id'),
                user_id=session_data.get('user_id')
            )
            
            logger.info("Session loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
    
    async def _save_session(self, login_response: LoginResponse):
        """Save session to file"""
        try:
            session_data = {
                'auth_token': login_response.auth_token,
                'session_id': login_response.session_id,
                'user_id': login_response.user_id,
                'cookies': dict(self.client.session_cookies),
                'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Session saved to {self.session_file}")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        return bool(self.current_login and self.client.is_authenticated())
    
    def _generate_device_id(self) -> str:
        """Generate a device ID for API requests"""
        import uuid
        return str(uuid.uuid4())
    
    def _is_successful_response(self, response: Dict[str, Any]) -> bool:
        """Check if API response indicates success"""
        success_indicators = [
            response.get('success') is True,
            response.get('status') == 'success',
            response.get('error') is None,
            'token' in response,
            'auth_token' in response
        ]
        return any(success_indicators)
    
    def _extract_auth_token(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract authentication token from response"""
        # Try different token field names
        token_fields = ['auth_token', 'token', 'access_token', 'jwt', 'bearer_token']
        
        for field in token_fields:
            if field in response and response[field]:
                return str(response[field])
        
        # Check nested objects
        if 'data' in response:
            for field in token_fields:
                if field in response['data'] and response['data'][field]:
                    return str(response['data'][field])
        
        return None