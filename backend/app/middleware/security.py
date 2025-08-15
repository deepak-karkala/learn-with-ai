"""
Security middleware for the AI System Design Learning Platform.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Set, Callable
from urllib.parse import urlparse

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from ..services.redis_service import get_redis_service

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app, enable_hsts: bool = True):
        super().__init__(app)
        self.enable_hsts = enable_hsts
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # HSTS header for HTTPS
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(
        self,
        app,
        default_requests_per_minute: int = 60,
        burst_requests: int = 10,
        rate_limit_rules: Optional[Dict[str, Dict[str, int]]] = None
    ):
        super().__init__(app)
        self.default_rpm = default_requests_per_minute
        self.burst_requests = burst_requests
        self.rate_limit_rules = rate_limit_rules or {}
        self.redis_service = get_redis_service()
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from headers or auth
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _get_rate_limit_for_endpoint(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint."""
        # Check for specific endpoint rules
        for pattern, limits in self.rate_limit_rules.items():
            if pattern in path:
                return limits
        
        # Default limits
        return {
            "requests_per_minute": self.default_rpm,
            "burst_requests": self.burst_requests
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)
        
        client_id = self._get_client_identifier(request)
        endpoint_path = request.url.path
        
        # Get rate limit configuration
        limits = self._get_rate_limit_for_endpoint(endpoint_path)
        rpm = limits["requests_per_minute"]
        
        # Check rate limit
        rate_limit_key = f"rate_limit:{endpoint_path}"
        rate_limit_result = self.redis_service.check_rate_limit(
            key=rate_limit_key,
            limit=rpm,
            window_seconds=60,
            identifier=client_id
        )
        
        if not rate_limit_result["allowed"]:
            # Track rate limit hit
            from ..services.monitoring_service import get_monitoring_service
            monitoring = get_monitoring_service()
            monitoring.track_rate_limit_hit(
                user_id=client_id,
                endpoint=endpoint_path,
                limit=rpm,
                current_count=rate_limit_result.get("current_count", 0)
            )
            
            # Return rate limit error
            headers = {
                "X-RateLimit-Limit": str(rpm),
                "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                "X-RateLimit-Reset": str(rate_limit_result["reset_time"]),
                "Retry-After": str(60)  # Seconds
            }
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {rpm} requests per minute",
                    "retry_after": 60
                },
                headers=headers
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rpm)
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization."""
    
    def __init__(
        self,
        app,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        blocked_patterns: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.blocked_patterns = blocked_patterns or [
            # Common injection patterns
            "<script",
            "javascript:",
            "vbscript:",
            "onload=",
            "onerror=",
            "eval(",
            "exec(",
            "system(",
            "shell_exec",
            # SQL injection patterns
            "union select",
            "drop table",
            "delete from",
            "insert into",
            "update set",
            # Command injection
            "&&",
            "||",
            ";rm",
            ";cat",
            "&cat",
            "|cat"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and sanitize input."""
        try:
            # Check request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_request_size:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "Request too large",
                        "message": f"Request size exceeds {self.max_request_size} bytes"
                    }
                )
            
            # For POST/PUT requests, validate body content
            if request.method in ["POST", "PUT", "PATCH"]:
                # Get request body
                body = await request.body()
                
                if body:
                    try:
                        # Try to decode as text for validation
                        body_text = body.decode('utf-8').lower()
                        
                        # Check for blocked patterns
                        for pattern in self.blocked_patterns:
                            if pattern.lower() in body_text:
                                logger.warning(f"Blocked request with pattern: {pattern}")
                                return JSONResponse(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    content={
                                        "error": "Invalid input",
                                        "message": "Request contains potentially malicious content"
                                    }
                                )
                    
                    except UnicodeDecodeError:
                        # Binary content, skip text validation
                        pass
                
                # Recreate request with validated body
                request._body = body
            
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error in input validation middleware: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "Request validation failed"
                }
            )


class PIIDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and mask PII in requests/responses."""
    
    def __init__(
        self,
        app,
        enable_pii_masking: bool = True,
        log_pii_detections: bool = True
    ):
        super().__init__(app)
        self.enable_pii_masking = enable_pii_masking
        self.log_pii_detections = log_pii_detections
        
        # PII detection patterns
        import re
        self.pii_patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        }
    
    def _detect_and_mask_pii(self, text: str) -> tuple[str, List[str]]:
        """Detect and mask PII in text."""
        detected_types = []
        masked_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_types.append(pii_type)
                if self.enable_pii_masking:
                    masked_text = pattern.sub(f"[MASKED_{pii_type.upper()}]", masked_text)
        
        return masked_text, detected_types
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Detect PII in requests and responses."""
        # For now, just log PII detections without modifying the request/response
        # In a full implementation, you might want to mask PII in logs
        
        try:
            # Process request
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    try:
                        body_text = body.decode('utf-8')
                        _, detected_pii = self._detect_and_mask_pii(body_text)
                        
                        if detected_pii and self.log_pii_detections:
                            logger.warning(f"PII detected in request: {detected_pii}")
                            
                            # Track PII detection
                            from ..services.monitoring_service import get_monitoring_service
                            monitoring = get_monitoring_service()
                            monitoring.track_error(
                                error=Exception(f"PII detected: {detected_pii}"),
                                context="pii_detection",
                                metadata={
                                    "pii_types": detected_pii,
                                    "endpoint": str(request.url.path)
                                }
                            )
                    
                    except UnicodeDecodeError:
                        pass
                
                # Recreate request with body
                request._body = body
            
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Error in PII detection middleware: {e}")
            return await call_next(request)


def configure_cors(app, allowed_origins: Optional[List[str]] = None) -> None:
    """Configure CORS middleware."""
    # Get allowed origins from environment or use defaults
    if not allowed_origins:
        origins_env = os.getenv("ALLOWED_ORIGINS", "")
        if origins_env:
            allowed_origins = [origin.strip() for origin in origins_env.split(",")]
        else:
            # Default allowed origins
            allowed_origins = [
                "http://localhost:3000",
                "https://learn-with-ai.vercel.app",
                "https://frontend-lua5my5jr-dkarkala01-gmailcoms-projects.vercel.app"
            ]
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-User-ID",
            "X-Session-ID"
        ],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset"
        ]
    )
    
    logger.info(f"CORS configured with origins: {allowed_origins}")


def configure_security_middleware(app) -> None:
    """Configure all security middleware."""
    # Get configuration from environment
    enable_rate_limiting = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    enable_input_validation = os.getenv("ENABLE_INPUT_VALIDATION", "true").lower() == "true"
    enable_pii_detection = os.getenv("ENABLE_PII_DETECTION", "true").lower() == "true"
    
    # Rate limiting configuration
    rate_limit_rpm = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    rate_limit_burst = int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))
    
    # Custom rate limits for specific endpoints
    rate_limit_rules = {
        "/api/chat": {"requests_per_minute": 30, "burst_requests": 5},
        "/api/whiteboard": {"requests_per_minute": 20, "burst_requests": 3},
        "/api/assessment": {"requests_per_minute": 10, "burst_requests": 2},
        "/api/diagrams": {"requests_per_minute": 15, "burst_requests": 3}
    }
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)
    
    # Add rate limiting middleware
    if enable_rate_limiting:
        app.add_middleware(
            RateLimitMiddleware,
            default_requests_per_minute=rate_limit_rpm,
            burst_requests=rate_limit_burst,
            rate_limit_rules=rate_limit_rules
        )
        logger.info("Rate limiting middleware enabled")
    
    # Add input validation middleware
    if enable_input_validation:
        max_request_size = int(os.getenv("MAX_REQUEST_SIZE", str(10 * 1024 * 1024)))
        app.add_middleware(
            InputValidationMiddleware,
            max_request_size=max_request_size
        )
        logger.info("Input validation middleware enabled")
    
    # Add PII detection middleware
    if enable_pii_detection:
        app.add_middleware(
            PIIDetectionMiddleware,
            enable_pii_masking=False,  # Just detect and log for now
            log_pii_detections=True
        )
        logger.info("PII detection middleware enabled")
    
    logger.info("Security middleware configuration completed")


class APIKeyValidator:
    """Utility class for API key validation."""
    
    def __init__(self):
        self.valid_api_keys: Set[str] = set()
        self._load_api_keys()
    
    def _load_api_keys(self) -> None:
        """Load valid API keys from environment."""
        api_keys_env = os.getenv("VALID_API_KEYS", "")
        if api_keys_env:
            self.valid_api_keys = set(key.strip() for key in api_keys_env.split(","))
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate an API key."""
        return api_key in self.valid_api_keys
    
    def add_api_key(self, api_key: str) -> None:
        """Add a new valid API key."""
        self.valid_api_keys.add(api_key)
    
    def remove_api_key(self, api_key: str) -> None:
        """Remove an API key."""
        self.valid_api_keys.discard(api_key)


# Global API key validator
_api_key_validator = APIKeyValidator()


def get_api_key_validator() -> APIKeyValidator:
    """Get the global API key validator."""
    return _api_key_validator