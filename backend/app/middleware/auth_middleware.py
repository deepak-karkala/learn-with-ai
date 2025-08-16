"""
Authentication middleware for JWT token validation and user authorization.
"""

import logging
from typing import Optional, Dict, Any, Set, List
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time

from ..services.auth_service import get_auth_service, Permission
from ..services.security_service import get_security_service

logger = logging.getLogger(__name__)

# HTTP Bearer token extractor
security = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication and authorization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = get_auth_service()
        self.security_service = get_security_service()
        
        # Endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            # DEMO MODE: All API endpoints are public for demo/MVP purposes
            # This allows investors and recruiters to test without account creation
            # TODO: Re-enable authentication before public release
            "/api/chat",
            "/api/whiteboard/upload",
            "/api/whiteboard/analyze",
            "/api/assessment",
            "/api/progress",
            "/api/monitoring"
        }
        
        # Endpoints that require authentication
        # DEMO MODE: All API authentication disabled for demo purposes
        # TODO: Uncomment these for production deployment
        self.auth_required_prefixes = {
            # "/api/chat",           # Disabled for demo
            # "/api/whiteboard",     # Disabled for demo
            # "/api/assessment",     # Disabled for demo
            # "/api/progress",       # Disabled for demo
            # "/api/monitoring",     # Disabled for demo
            "/admin"  # Keep admin endpoints protected
        }
        
        # Permission requirements for specific endpoints
        # DEMO MODE: All permission requirements disabled for demo purposes
        # TODO: Uncomment these for production deployment
        self.endpoint_permissions = {
            # "/api/whiteboard/analyze": [Permission.WHITEBOARD_ANALYZE],  # Disabled for demo
            # "/api/assessment": [Permission.ASSESSMENT_TAKE],              # Disabled for demo
            # "/api/progress": [Permission.PROGRESS_VIEW],                  # Disabled for demo
            # "/api/monitoring": [Permission.ADMIN_MONITORING],             # Disabled for demo
            "/admin": [Permission.ADMIN_SYSTEM]  # Keep admin endpoints protected
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process authentication for incoming requests."""
        try:
            start_time = time.time()
            
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Check if IP is blocked
            if self.security_service.is_request_blocked(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied due to security restrictions"}
                )
            
            # Check if endpoint requires authentication
            if not self._requires_auth(request.url.path):
                response = await call_next(request)
                self._log_request(request, None, time.time() - start_time)
                return response
            
            # Extract and validate token
            token_data = await self._extract_and_validate_token(request)
            if not token_data:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or missing authentication token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Check permissions
            if not self._check_permissions(request.url.path, token_data):
                # Log authorization failure
                from ..services.logging_service import log_authorization_event
                log_authorization_event(
                    action="access",
                    resource=request.url.path,
                    result="denied",
                    user_id=token_data["sub"],
                    required_permissions=self._get_required_permissions(request.url.path),
                    user_permissions=token_data.get("permissions", []),
                    ip_address=self._get_client_ip(request)
                )
                
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Insufficient permissions"}
                )
            
            # Add user context to request
            request.state.user = {
                "user_id": token_data["sub"],
                "email": token_data["email"],
                "role": token_data["role"],
                "permissions": token_data.get("permissions", [])
            }
            
            # Process request
            response = await call_next(request)
            
            # Log successful request
            self._log_request(request, token_data["sub"], time.time() - start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Authentication error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        client_host = request.client.host if request.client else "unknown"
        return client_host
    
    def _requires_auth(self, path: str) -> bool:
        """Check if endpoint requires authentication."""
        # Public endpoints
        if path in self.public_endpoints:
            return False
        
        # Check if path starts with any auth-required prefix
        return any(path.startswith(prefix) for prefix in self.auth_required_prefixes)
    
    async def _extract_and_validate_token(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract and validate JWT token from request."""
        try:
            # Try to get token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return None
            
            if not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            
            # Validate token
            token_data = self.auth_service.verify_token(token)
            if not token_data:
                return None
            
            # Additional validation
            if not self._validate_token_claims(token_data):
                return None
            
            return token_data
            
        except Exception as e:
            logger.error(f"Token extraction error: {e}")
            return None
    
    def _validate_token_claims(self, token_data: Dict[str, Any]) -> bool:
        """Validate token claims for security."""
        required_claims = ["sub", "email", "role", "exp"]
        
        # Check required claims exist
        for claim in required_claims:
            if claim not in token_data:
                logger.warning(f"Missing required claim: {claim}")
                return False
        
        # Check token hasn't expired (additional check)
        current_time = time.time()
        if token_data["exp"] < current_time:
            logger.warning("Token expired")
            return False
        
        # Check token isn't too old (issued more than max time ago)
        max_token_age = 24 * 3600  # 24 hours
        if "iat" in token_data:
            if current_time - token_data["iat"] > max_token_age:
                logger.warning("Token too old")
                return False
        
        return True
    
    def _get_required_permissions(self, path: str) -> List[str]:
        """Get required permissions for endpoint."""
        for endpoint_pattern, permissions in self.endpoint_permissions.items():
            if path.startswith(endpoint_pattern):
                return [perm.value for perm in permissions]
        return []
    
    def _check_permissions(self, path: str, token_data: Dict[str, Any]) -> bool:
        """Check if user has required permissions for endpoint."""
        # Get required permissions for this endpoint
        required_permissions = None
        
        for endpoint_pattern, permissions in self.endpoint_permissions.items():
            if path.startswith(endpoint_pattern):
                required_permissions = permissions
                break
        
        # If no specific permissions required, allow access
        if not required_permissions:
            return True
        
        # Get user permissions from token
        user_permissions = set(token_data.get("permissions", []))
        
        # Check if user has all required permissions
        required_permissions_set = {perm.value for perm in required_permissions}
        return required_permissions_set.issubset(user_permissions)
    
    def _log_request(self, request: Request, user_id: Optional[str], duration: float):
        """Log authenticated requests for audit trail."""
        try:
            log_data = {
                "method": request.method,
                "path": request.url.path,
                "user_id": user_id,
                "ip_address": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", ""),
                "duration": duration,
                "timestamp": time.time()
            }
            
            logger.info(f"API request: {request.method} {request.url.path}", extra=log_data)
            
        except Exception as e:
            logger.error(f"Request logging error: {e}")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication (alternative to JWT)."""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_service = get_security_service()
        
        # Endpoints that support API key authentication
        self.api_key_endpoints = {
            "/api/v1/",  # API v1 endpoints
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process API key authentication."""
        try:
            # Check if this endpoint supports API key auth
            if not self._supports_api_key_auth(request.url.path):
                return await call_next(request)
            
            # Extract API key and secret
            api_key = request.headers.get("X-API-Key")
            api_secret = request.headers.get("X-API-Secret")
            
            if not api_key or not api_secret:
                # No API key provided, let other auth middleware handle it
                return await call_next(request)
            
            # Verify API key
            api_key_data = self.security_service.verify_api_key(api_key, api_secret)
            if not api_key_data:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid API key or secret"}
                )
            
            # Add API key context to request
            request.state.api_key = {
                "api_key": api_key,
                "user_id": api_key_data["user_id"],
                "authenticated_via": "api_key"
            }
            
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"API key middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "API key authentication error"}
            )
    
    def _supports_api_key_auth(self, path: str) -> bool:
        """Check if endpoint supports API key authentication."""
        return any(path.startswith(prefix) for prefix in self.api_key_endpoints)


# Utility functions for extracting current user from request context

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from request context."""
    return getattr(request.state, "user", None)

def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from request context."""
    user = get_current_user(request)
    return user["user_id"] if user else None

def require_permission(request: Request, permission: Permission) -> bool:
    """Check if current user has specific permission."""
    user = get_current_user(request)
    if not user:
        return False
    
    user_permissions = set(user.get("permissions", []))
    return permission.value in user_permissions

def require_role(request: Request, required_role: str) -> bool:
    """Check if current user has specific role."""
    user = get_current_user(request)
    if not user:
        return False
    
    return user["role"] == required_role


# Dependency for FastAPI routes to require authentication

async def get_current_active_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

async def get_admin_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency to require admin role."""
    user = await get_current_active_user(request)
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user