"""
Authentication API endpoints for user registration, login, and token management.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any, Optional
import logging

from ..services.auth_service import get_auth_service, UserRole
from ..services.security_service import get_security_service
from ..middleware.auth_middleware import get_current_active_user, get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Request/Response models

class UserRegistrationRequest(BaseModel):
    """User registration request model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=1, max_length=100, description="User full name")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserLoginRequest(BaseModel):
    """User login request model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class APIKeyResponse(BaseModel):
    """API key response model."""
    api_key: str = Field(..., description="API key")
    secret: str = Field(..., description="API secret (only shown once)")
    message: str = Field(..., description="Instructions")


# Authentication endpoints

@router.post("/register", response_model=Dict[str, Any])
async def register_user(
    request: Request,
    user_data: UserRegistrationRequest
):
    """Register a new user account."""
    try:
        auth_service = get_auth_service()
        security_service = get_security_service()
        
        # Get client IP for security analysis
        client_ip = request.client.host if request.client else "unknown"
        
        # Analyze registration request for security threats
        security_event = security_service.analyze_request_security(
            request_data=user_data.dict(),
            ip_address=client_ip
        )
        
        # Block if high threat level detected
        if security_event.blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration blocked due to security restrictions"
            )
        
        # Attempt registration
        result = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": result["user_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: Request,
    login_data: UserLoginRequest
):
    """Authenticate user and return JWT tokens."""
    try:
        auth_service = get_auth_service()
        security_service = get_security_service()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Analyze login request for security threats
        security_event = security_service.analyze_request_security(
            request_data=login_data.dict(),
            ip_address=client_ip
        )
        
        # Block if high threat level detected
        if security_event.blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Login blocked due to security restrictions"
            )
        
        # Attempt authentication
        result = auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            ip_address=client_ip
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"],
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=result["user"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        auth_service = get_auth_service()
        
        result = auth_service.refresh_access_token(refresh_data.refresh_token)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"],
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Logout user by revoking refresh token."""
    try:
        auth_service = get_auth_service()
        
        user_id = current_user["user_id"]
        
        # Revoke refresh token
        auth_service.revoke_refresh_token(user_id)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Change user password."""
    try:
        auth_service = get_auth_service()
        
        result = auth_service.change_password(
            user_id=current_user["user_id"],
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {"message": result["message"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/profile")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current user profile information."""
    try:
        # Remove sensitive information
        safe_user = current_user.copy()
        safe_user.pop("permissions", None)  # Don't expose permissions in profile
        
        return {
            "user": safe_user,
            "permissions": current_user.get("permissions", [])
        }
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile retrieval failed"
        )


@router.post("/api-key", response_model=APIKeyResponse)
async def generate_api_key(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Generate API key for programmatic access."""
    try:
        security_service = get_security_service()
        
        result = security_service.generate_api_key(current_user["user_id"])
        
        return APIKeyResponse(
            api_key=result["api_key"],
            secret=result["secret"],
            message="Store the secret safely. It will not be shown again."
        )
        
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key generation failed"
        )


@router.get("/verify")
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Verify current token is valid."""
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"]
    }


# Security endpoints

@router.get("/security/events")
async def get_security_events(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get recent security events (admin only)."""
    try:
        # Check admin permission
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        security_service = get_security_service()
        metrics = security_service.get_security_metrics()
        
        return {
            "security_metrics": metrics,
            "user_id": current_user["user_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security events error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )


@router.post("/security/whitelist-ip")
async def whitelist_ip(
    request: Request,
    ip_address: str,
    duration_hours: int = 24,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Whitelist an IP address (admin only)."""
    try:
        # Check admin permission
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        security_service = get_security_service()
        security_service.whitelist_ip(ip_address, duration_hours)
        
        return {
            "message": f"IP {ip_address} whitelisted for {duration_hours} hours",
            "ip_address": ip_address,
            "duration_hours": duration_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IP whitelist error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="IP whitelist failed"
        )


@router.post("/security/blacklist-ip")
async def blacklist_ip(
    request: Request,
    ip_address: str,
    duration_hours: int = 1,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Blacklist an IP address (admin only)."""
    try:
        # Check admin permission
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        security_service = get_security_service()
        security_service.blacklist_ip(ip_address, duration_hours)
        
        return {
            "message": f"IP {ip_address} blacklisted for {duration_hours} hours",
            "ip_address": ip_address,
            "duration_hours": duration_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IP blacklist error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="IP blacklist failed"
        )