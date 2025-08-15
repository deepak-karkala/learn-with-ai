"""
Middleware package for the AI System Design Learning Platform.
"""

from .security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    InputValidationMiddleware,
    PIIDetectionMiddleware,
    configure_cors,
    configure_security_middleware,
    APIKeyValidator,
    get_api_key_validator
)

from .auth_middleware import (
    AuthenticationMiddleware,
    APIKeyMiddleware,
    get_current_user,
    get_current_user_id,
    require_permission,
    require_role,
    get_current_active_user,
    get_admin_user
)

__all__ = [
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware", 
    "InputValidationMiddleware",
    "PIIDetectionMiddleware",
    "configure_cors",
    "configure_security_middleware",
    "APIKeyValidator",
    "get_api_key_validator",
    "AuthenticationMiddleware",
    "APIKeyMiddleware",
    "get_current_user",
    "get_current_user_id",
    "require_permission",
    "require_role",
    "get_current_active_user",
    "get_admin_user"
]