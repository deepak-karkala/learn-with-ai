"""
Authentication and authorization service for secure user management.
"""

import hashlib
import hmac
import jwt
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
import os
import bcrypt

from ..services.redis_service import get_redis_service
from ..services.storage_service import get_storage_service
from ..database.models import User
from ..database.connection import get_database

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    DEVELOPER = "developer"


class Permission(str, Enum):
    """System permissions."""
    # Chat permissions
    CHAT_ACCESS = "chat:access"
    CHAT_HISTORY = "chat:history"
    
    # Whiteboard permissions  
    WHITEBOARD_CREATE = "whiteboard:create"
    WHITEBOARD_ANALYZE = "whiteboard:analyze"
    WHITEBOARD_SHARE = "whiteboard:share"
    
    # Assessment permissions
    ASSESSMENT_TAKE = "assessment:take"
    ASSESSMENT_VIEW_RESULTS = "assessment:view_results"
    
    # Progress permissions
    PROGRESS_VIEW = "progress:view"
    PROGRESS_EXPORT = "progress:export"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_MONITORING = "admin:monitoring"
    
    # API permissions
    API_RATE_LIMIT_BYPASS = "api:rate_limit_bypass"
    API_DEBUG_ACCESS = "api:debug_access"


class AuthenticationService:
    """Service for handling authentication and authorization."""
    
    def __init__(self):
        self._redis_service = get_redis_service()
        self._storage_service = get_storage_service()
        self._db = get_database()
        
        # Security configuration
        self._jwt_secret = os.getenv("JWT_SECRET", self._generate_secure_secret())
        self._jwt_algorithm = "HS256"
        self._access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self._refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self._max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self._lockout_duration_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
        
        # Role-based permissions mapping
        user_permissions = [
            Permission.CHAT_ACCESS,
            Permission.CHAT_HISTORY,
            Permission.WHITEBOARD_CREATE,
            Permission.WHITEBOARD_ANALYZE,
            Permission.ASSESSMENT_TAKE,
            Permission.ASSESSMENT_VIEW_RESULTS,
            Permission.PROGRESS_VIEW,
            Permission.PROGRESS_EXPORT,
        ]
        
        self._role_permissions = {
            UserRole.GUEST: [
                Permission.CHAT_ACCESS,
            ],
            UserRole.USER: user_permissions,
            UserRole.DEVELOPER: [
                # All user permissions plus development access
                *user_permissions,
                Permission.API_DEBUG_ACCESS,
            ],
            UserRole.ADMIN: [
                # All permissions
                *[perm for perm in Permission],
            ]
        }
        
        logger.info("Authentication service initialized")
    
    def _generate_secure_secret(self) -> str:
        """Generate a secure secret for JWT signing."""
        return secrets.token_urlsafe(32)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    # =============================================================================
    # User Registration and Management
    # =============================================================================
    
    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.USER,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a new user."""
        try:
            # Validate email format
            if not self._validate_email(email):
                return {"success": False, "error": "Invalid email format"}
            
            # Check password strength
            if not self._validate_password_strength(password):
                return {"success": False, "error": "Password does not meet security requirements"}
            
            # Check if user already exists
            if self._get_user_by_email(email):
                return {"success": False, "error": "User already exists"}
            
            # Hash password
            hashed_password = self._hash_password(password)
            
            # Create user record
            user_data = {
                "email": email,
                "password_hash": hashed_password,
                "full_name": full_name,
                "role": role.value,
                "is_active": True,
                "is_verified": False,
                "created_at": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            user_id = self._create_user_record(user_data)
            
            # Log registration  
            from ..services.logging_service import log_authentication_event
            log_authentication_event(
                action="register",
                result="success",
                user_id=user_id,
                email=email,
                additional_data={"role": role.value}
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "User registered successfully"
            }
            
        except Exception as e:
            logger.error(f"User registration error: {e}")
            return {"success": False, "error": "Registration failed"}
    
    def authenticate_user(self, email: str, password: str, ip_address: str = "") -> Dict[str, Any]:
        """Authenticate user credentials."""
        try:
            # Import security logging
            from ..services.logging_service import log_authentication_event
            
            # Check for account lockout
            if self._is_account_locked(email):
                log_authentication_event(
                    action="login",
                    result="failed",
                    email=email,
                    ip_address=ip_address,
                    additional_data={"reason": "account_locked"}
                )
                return {"success": False, "error": "Account temporarily locked due to failed login attempts"}
            
            # Get user by email
            user = self._get_user_by_email(email)
            if not user:
                self._record_failed_login(email, ip_address)
                log_authentication_event(
                    action="login",
                    result="failed",
                    email=email,
                    ip_address=ip_address,
                    additional_data={"reason": "user_not_found"}
                )
                return {"success": False, "error": "Invalid credentials"}
            
            # Verify password
            if not self._verify_password(password, user["password_hash"]):
                self._record_failed_login(email, ip_address)
                log_authentication_event(
                    action="login",
                    result="failed",
                    user_id=user.get("user_id"),
                    email=email,
                    ip_address=ip_address,
                    additional_data={"reason": "invalid_password"}
                )
                return {"success": False, "error": "Invalid credentials"}
            
            # Check if account is active
            if not user.get("is_active", False):
                log_authentication_event(
                    action="login",
                    result="failed",
                    user_id=user.get("user_id"),
                    email=email,
                    ip_address=ip_address,
                    additional_data={"reason": "account_deactivated"}
                )
                return {"success": False, "error": "Account is deactivated"}
            
            # Clear failed login attempts
            self._clear_failed_login_attempts(email)
            
            # Generate tokens
            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token(user)
            
            # Log successful login
            log_authentication_event(
                action="login",
                result="success",
                user_id=user.get("id"),
                email=email,
                ip_address=ip_address,
                additional_data={"role": user.get("role")}
            )
            
            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self._access_token_expire_minutes * 60,
                "user": self._sanitize_user_data(user)
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
    
    # =============================================================================
    # JWT Token Management
    # =============================================================================
    
    def _generate_access_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT access token."""
        payload = {
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
            "permissions": [perm.value for perm in self._get_user_permissions(user["role"])],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self._access_token_expire_minutes),
            "type": "access"
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)
    
    def _generate_refresh_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT refresh token."""
        payload = {
            "sub": str(user["id"]),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=self._refresh_token_expire_days),
            "type": "refresh"
        }
        refresh_token = jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)
        
        # Store refresh token in Redis with expiration
        if self._redis_service.is_available():
            self._redis_service.set_cache(
                f"refresh_token:{user['id']}", 
                refresh_token,
                ttl_seconds=self._refresh_token_expire_days * 24 * 3600
            )
        
        return refresh_token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Check expiration
            if payload.get("exp") < time.time():
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            
            if payload.get("type") != "refresh":
                return {"success": False, "error": "Invalid token type"}
            
            user_id = payload.get("sub")
            if not user_id:
                return {"success": False, "error": "Invalid token payload"}
            
            # Check if refresh token exists in Redis
            if self._redis_service.is_available():
                stored_token = self._redis_service.get_cache(f"refresh_token:{user_id}")
                if stored_token != refresh_token:
                    return {"success": False, "error": "Token not found or revoked"}
            
            # Get user data
            user = self._get_user_by_id(user_id)
            if not user or not user.get("is_active", False):
                return {"success": False, "error": "User not found or inactive"}
            
            # Generate new access token
            access_token = self._generate_access_token(user)
            
            return {
                "success": True,
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self._access_token_expire_minutes * 60
            }
            
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Refresh token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid refresh token"}
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return {"success": False, "error": "Token refresh failed"}
    
    def revoke_refresh_token(self, user_id: str) -> bool:
        """Revoke refresh token for user."""
        try:
            if self._redis_service.is_available():
                return self._redis_service.delete_cache(f"refresh_token:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            return False
    
    # =============================================================================
    # Authorization and Permissions
    # =============================================================================
    
    def has_permission(self, user_id: str, permission: Permission, user_permissions: List[Permission] = None) -> bool:
        """Check if user has specific permission."""
        if user_permissions is not None:
            # If permissions provided directly, check against them
            return permission in user_permissions
        
        # Otherwise get user from database and check role permissions
        user = self._get_user_by_id(user_id)
        if not user:
            return False
        
        user_role_permissions = self._role_permissions.get(UserRole(user["role"]), [])
        return permission in user_role_permissions
    
    def has_role_permission(self, user_role: str, permission: Permission) -> bool:
        """Check if user role has specific permission."""
        user_permissions = self._role_permissions.get(UserRole(user_role), [])
        return permission in user_permissions
    
    def _get_user_permissions(self, role: str) -> List[Permission]:
        """Get all permissions for a user role."""
        return self._role_permissions.get(UserRole(role), [])
    
    def check_api_access(self, user_id: str, endpoint: str, method: str) -> bool:
        """Check if user has access to specific API endpoint."""
        # This can be extended with more granular endpoint-based permissions
        user = self._get_user_by_id(user_id)
        if not user:
            return False
        
        # Basic access control - can be expanded
        sensitive_endpoints = ["/admin", "/monitoring", "/debug"]
        if any(endpoint.startswith(ep) for ep in sensitive_endpoints):
            return self.has_role_permission(user["role"], Permission.ADMIN_SYSTEM)
        
        return True
    
    # =============================================================================
    # Account Security
    # =============================================================================
    
    def _is_account_locked(self, email: str) -> bool:
        """Check if account is locked due to failed login attempts."""
        if not self._redis_service.is_available():
            return False
        
        failed_attempts = self._redis_service.get_cache(f"failed_login:{email}") or 0
        return failed_attempts >= self._max_login_attempts
    
    def _record_failed_login(self, email: str, ip_address: str = ""):
        """Record failed login attempt."""
        if not self._redis_service.is_available():
            return
        
        # Increment failed attempts
        key = f"failed_login:{email}"
        attempts = self._redis_service.get_cache(key) or 0
        attempts += 1
        
        # Set with lockout duration expiration
        self._redis_service.set_cache(
            key, 
            attempts, 
            ttl_seconds=self._lockout_duration_minutes * 60
        )
        
        # Log security event
        self._log_security_event("failed_login", {
            "email": email,
            "ip_address": ip_address,
            "attempts": attempts
        })
    
    def _clear_failed_login_attempts(self, email: str):
        """Clear failed login attempts after successful login."""
        if self._redis_service.is_available():
            self._redis_service.delete_cache(f"failed_login:{email}")
    
    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Change user password with verification."""
        try:
            # Get user
            user = self._get_user_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Verify current password
            if not self._verify_password(current_password, user["password_hash"]):
                return {"success": False, "error": "Current password incorrect"}
            
            # Validate new password
            if not self._validate_password_strength(new_password):
                return {"success": False, "error": "New password does not meet security requirements"}
            
            # Hash new password
            new_password_hash = self._hash_password(new_password)
            
            # Update password in database
            self._update_user_password(user_id, new_password_hash)
            
            # Revoke all refresh tokens
            self.revoke_refresh_token(user_id)
            
            # Log security event
            self._log_security_event("password_changed", {
                "user_id": user_id,
                "email": user["email"]
            })
            
            return {"success": True, "message": "Password changed successfully"}
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return {"success": False, "error": "Password change failed"}
    
    # =============================================================================
    # Validation Functions
    # =============================================================================
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False
        
        # Check for uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    # =============================================================================
    # Database Operations (placeholder - implement based on your database)
    # =============================================================================
    
    def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from database."""
        # Placeholder implementation
        # In real implementation, query your database
        return None
    
    def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from database."""
        # Placeholder implementation
        return None
    
    def _create_user_record(self, user_data: Dict[str, Any]) -> str:
        """Create user record in database."""
        # Placeholder implementation
        return "user_id"
    
    def _update_user_password(self, user_id: str, password_hash: str):
        """Update user password in database."""
        # Placeholder implementation
        pass
    
    def _sanitize_user_data(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from user object."""
        safe_user = user.copy()
        safe_user.pop("password_hash", None)
        return safe_user
    
    # =============================================================================
    # Security Logging
    # =============================================================================
    
    def _log_security_event(self, event_type: str, data: Dict[str, Any]):
        """Log security events for audit trail."""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "data": data,
                "service": "auth"
            }
            
            # Log to application logger
            logger.info(f"Security event: {event_type}", extra=log_entry)
            
            # Store in Redis for immediate access if available
            if self._redis_service.is_available():
                key = f"security_log:{int(time.time())}"
                self._redis_service.set_cache(key, log_entry, ttl_seconds=3600 * 24)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")


# Global authentication service instance
_auth_service: Optional[AuthenticationService] = None


def get_auth_service() -> AuthenticationService:
    """Get the global authentication service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service


def init_auth_service() -> None:
    """Initialize authentication service."""
    global _auth_service
    _auth_service = AuthenticationService()
    logger.info("Authentication service initialized")