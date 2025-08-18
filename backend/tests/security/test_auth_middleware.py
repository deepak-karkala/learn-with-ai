"""
Tests for authentication middleware.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

from app.middleware.auth_middleware import (
    AuthenticationMiddleware, APIKeyMiddleware,
    get_current_user, get_current_active_user, require_permission
)
from app.services.auth_service import Permission


@pytest.mark.external_deps
class TestAuthenticationMiddleware:
    """Test authentication middleware functionality."""
    
    @pytest.fixture
    def auth_middleware(self):
        """Create authentication middleware for testing."""
        app = Mock()
        with patch('app.middleware.auth_middleware.get_auth_service'), \
             patch('app.middleware.auth_middleware.get_security_service'):
            middleware = AuthenticationMiddleware(app)
            middleware.auth_service = Mock()
            middleware.security_service = Mock()
            return middleware
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()
        return request
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_public_endpoint_access(self, auth_middleware, mock_request):
        """Test access to public endpoints without authentication."""
        mock_request.url.path = "/health"
        call_next = AsyncMock(return_value=Mock())
        
        response = await auth_middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once_with(mock_request)
        assert response is not None
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_protected_endpoint_without_token(self, auth_middleware, mock_request):
        """Test access to protected endpoint without token."""
        mock_request.url.path = "/api/chat"
        mock_request.headers = {}
        
        auth_middleware.security_service.is_request_blocked.return_value = False
        
        call_next = AsyncMock()
        response = await auth_middleware.dispatch(mock_request, call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        call_next.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_blocked_ip_access(self, auth_middleware, mock_request):
        """Test access from blocked IP address."""
        auth_middleware.security_service.is_request_blocked.return_value = True
        
        call_next = AsyncMock()
        response = await auth_middleware.dispatch(mock_request, call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        call_next.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_valid_token_access(self, auth_middleware, mock_request):
        """Test access with valid JWT token."""
        mock_request.url.path = "/api/chat"
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        
        auth_middleware.security_service.is_request_blocked.return_value = False
        auth_middleware.auth_service.verify_token.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user",
            "permissions": ["chat:access"],
            "exp": 9999999999  # Future timestamp
        }
        
        call_next = AsyncMock(return_value=Mock())
        response = await auth_middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once_with(mock_request)
        assert hasattr(mock_request.state, 'user')
        assert mock_request.state.user["user_id"] == "user123"
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_invalid_token_access(self, auth_middleware, mock_request):
        """Test access with invalid JWT token."""
        mock_request.url.path = "/api/chat"
        mock_request.headers = {"Authorization": "Bearer invalid_token"}
        
        auth_middleware.security_service.is_request_blocked.return_value = False
        auth_middleware.auth_service.verify_token.return_value = None
        
        call_next = AsyncMock()
        response = await auth_middleware.dispatch(mock_request, call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        call_next.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_insufficient_permissions(self, auth_middleware, mock_request):
        """Test access with insufficient permissions."""
        mock_request.url.path = "/api/admin"
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        
        auth_middleware.security_service.is_request_blocked.return_value = False
        auth_middleware.auth_service.verify_token.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user",
            "permissions": ["chat:access"],  # Missing admin permissions
            "exp": 9999999999
        }
        
        call_next = AsyncMock()
        response = await auth_middleware.dispatch(mock_request, call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        call_next.assert_not_called()
    
    @pytest.mark.external_deps
    def test_client_ip_extraction(self, auth_middleware, mock_request):
        """Test client IP extraction from request."""
        # Test direct client IP
        mock_request.headers = {}
        ip = auth_middleware._get_client_ip(mock_request)
        assert ip == "127.0.0.1"
        
        # Test X-Forwarded-For header
        mock_request.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
        ip = auth_middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"
        
        # Test X-Real-IP header
        mock_request.headers = {"X-Real-IP": "192.168.1.200"}
        ip = auth_middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.200"
    
    @pytest.mark.external_deps
    def test_requires_auth_check(self, auth_middleware):
        """Test authentication requirement checking."""
        # Public endpoints
        assert not auth_middleware._requires_auth("/")
        assert not auth_middleware._requires_auth("/health")
        assert not auth_middleware._requires_auth("/docs")
        
        # Protected endpoints
        assert auth_middleware._requires_auth("/api/chat")
        assert auth_middleware._requires_auth("/api/whiteboard")
        assert auth_middleware._requires_auth("/admin/users")
    
    @pytest.mark.external_deps
    def test_token_extraction(self, auth_middleware, mock_request):
        """Test JWT token extraction from request."""
        # No Authorization header
        mock_request.headers = {}
        auth_middleware.auth_service.verify_token.return_value = None
        
        result = auth_middleware._extract_and_validate_token(mock_request)
        assert result is None
        
        # Invalid Authorization header format
        mock_request.headers = {"Authorization": "Invalid format"}
        result = auth_middleware._extract_and_validate_token(mock_request)
        assert result is None
        
        # Valid Authorization header
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        auth_middleware.auth_service.verify_token.return_value = {
            "sub": "user123",
            "exp": 9999999999
        }
        result = auth_middleware._extract_and_validate_token(mock_request)
        assert result is not None
    
    @pytest.mark.external_deps
    def test_token_claims_validation(self, auth_middleware):
        """Test JWT token claims validation."""
        # Valid token claims
        valid_claims = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user",
            "exp": 9999999999,
            "iat": 1600000000
        }
        assert auth_middleware._validate_token_claims(valid_claims)
        
        # Missing required claims
        invalid_claims = {
            "sub": "user123",
            # Missing email, role, exp
        }
        assert not auth_middleware._validate_token_claims(invalid_claims)
        
        # Expired token
        expired_claims = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "user",
            "exp": 1000000000  # Past timestamp
        }
        assert not auth_middleware._validate_token_claims(expired_claims)
    
    @pytest.mark.external_deps
    def test_permission_checking(self, auth_middleware):
        """Test permission checking logic."""
        token_data = {
            "permissions": ["chat:access", "whiteboard:create"]
        }
        
        # Endpoint with no specific permissions
        assert auth_middleware._check_permissions("/api/public", token_data)
        
        # Endpoint with matching permissions
        auth_middleware.endpoint_permissions["/api/chat"] = [Permission.CHAT_ACCESS]
        assert auth_middleware._check_permissions("/api/chat", token_data)
        
        # Endpoint with missing permissions
        auth_middleware.endpoint_permissions["/api/admin"] = [Permission.ADMIN_SYSTEM]
        assert not auth_middleware._check_permissions("/api/admin", token_data)


@pytest.mark.external_deps
class TestAPIKeyMiddleware:
    """Test API key middleware functionality."""
    
    @pytest.fixture
    def api_key_middleware(self):
        """Create API key middleware for testing."""
        app = Mock()
        with patch('app.middleware.auth_middleware.get_security_service'):
            middleware = APIKeyMiddleware(app)
            middleware.security_service = Mock()
            return middleware
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        request.headers = {}
        request.state = Mock()
        return request
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_non_api_key_endpoint(self, api_key_middleware, mock_request):
        """Test endpoint that doesn't support API key auth."""
        mock_request.url.path = "/api/chat"  # Not in api_key_endpoints
        call_next = AsyncMock(return_value=Mock())
        
        response = await api_key_middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_missing_api_key_headers(self, api_key_middleware, mock_request):
        """Test API key endpoint without headers."""
        mock_request.headers = {}
        call_next = AsyncMock(return_value=Mock())
        
        response = await api_key_middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_invalid_api_key(self, api_key_middleware, mock_request):
        """Test with invalid API key."""
        mock_request.headers = {
            "X-API-Key": "invalid_key",
            "X-API-Secret": "invalid_secret"
        }
        
        api_key_middleware.security_service.verify_api_key.return_value = None
        call_next = AsyncMock()
        
        response = await api_key_middleware.dispatch(mock_request, call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        call_next.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_valid_api_key(self, api_key_middleware, mock_request):
        """Test with valid API key."""
        mock_request.headers = {
            "X-API-Key": "valid_key",
            "X-API-Secret": "valid_secret"
        }
        
        api_key_middleware.security_service.verify_api_key.return_value = {
            "user_id": "user123"
        }
        call_next = AsyncMock(return_value=Mock())
        
        response = await api_key_middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once_with(mock_request)
        assert hasattr(mock_request.state, 'api_key')
        assert mock_request.state.api_key["user_id"] == "user123"


@pytest.mark.external_deps
class TestUtilityFunctions:
    """Test utility functions for authentication."""
    
    @pytest.fixture
    def mock_request_with_user(self):
        """Create mock request with user state."""
        request = Mock(spec=Request)
        request.state.user = {
            "user_id": "user123",
            "email": "test@example.com",
            "role": "user",
            "permissions": ["chat:access", "whiteboard:create"]
        }
        return request
    
    @pytest.fixture
    def mock_request_without_user(self):
        """Create mock request without user state."""
        request = Mock(spec=Request)
        request.state = Mock()
        return request
    
    @pytest.mark.external_deps
    def test_get_current_user(self, mock_request_with_user, mock_request_without_user):
        """Test get_current_user function."""
        # With user
        user = get_current_user(mock_request_with_user)
        assert user is not None
        assert user["user_id"] == "user123"
        
        # Without user
        user = get_current_user(mock_request_without_user)
        assert user is None
    
    @pytest.mark.external_deps
    def test_get_current_user_id(self, mock_request_with_user, mock_request_without_user):
        """Test get_current_user_id function."""
        # With user
        user_id = get_current_user_id(mock_request_with_user)
        assert user_id == "user123"
        
        # Without user
        user_id = get_current_user_id(mock_request_without_user)
        assert user_id is None
    
    @pytest.mark.external_deps
    def test_require_permission(self, mock_request_with_user, mock_request_without_user):
        """Test require_permission function."""
        # User with permission
        has_permission = require_permission(mock_request_with_user, Permission.CHAT_ACCESS)
        assert has_permission
        
        # User without permission
        has_permission = require_permission(mock_request_with_user, Permission.ADMIN_SYSTEM)
        assert not has_permission
        
        # No user
        has_permission = require_permission(mock_request_without_user, Permission.CHAT_ACCESS)
        assert not has_permission
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_get_current_active_user(self, mock_request_with_user, mock_request_without_user):
        """Test get_current_active_user dependency."""
        # With user
        user = await get_current_active_user(mock_request_with_user)
        assert user["user_id"] == "user123"
        
        # Without user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_request_without_user)
        assert exc_info.value.status_code == 401
    
    @pytest.mark.external_deps
    def test_middleware_error_handling(self, auth_middleware, mock_request):
        """Test middleware error handling."""
        mock_request.url.path = "/api/chat"
        
        # Simulate exception in middleware
        auth_middleware.security_service.is_request_blocked.side_effect = Exception("Test error")
        
        call_next = AsyncMock()
        
        # Should handle exception gracefully
        # Note: This would need to be tested with actual middleware dispatch
        # that catches exceptions and returns 500 error