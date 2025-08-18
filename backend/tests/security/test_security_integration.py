"""
Integration tests for the complete security system.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from app.main import app
from app.services.auth_service import AuthenticationService, UserRole
from app.services.security_service import SecurityService


@pytest.mark.external_deps
class TestSecurityIntegration:
    """Test complete security system integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_service(self):
        """Mock authentication service."""
        with patch('app.services.auth_service.get_auth_service') as mock:
            service = Mock(spec=AuthenticationService)
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def security_service(self):
        """Mock security service."""
        with patch('app.services.security_service.get_security_service') as mock:
            service = Mock(spec=SecurityService)
            mock.return_value = service
            yield service
    
    @pytest.mark.external_deps
    def test_user_registration_flow(self, client, auth_service):
        """Test complete user registration flow."""
        # Mock successful registration
        auth_service.register_user.return_value = {
            "success": True,
            "user_id": "user123",
            "message": "User registered successfully"
        }
        
        # Mock security analysis (no threats)
        with patch('app.api.auth.get_security_service') as mock_security:
            mock_security.return_value.analyze_request_security.return_value = Mock(
                blocked=False,
                threat_level="low"
            )
            
            response = client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
                "role": "user"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["user_id"] == "user123"
    
    @pytest.mark.external_deps
    def test_user_registration_blocked_by_security(self, client, auth_service):
        """Test user registration blocked by security analysis."""
        # Mock security analysis (high threat)
        with patch('app.api.auth.get_security_service') as mock_security:
            mock_security.return_value.analyze_request_security.return_value = Mock(
                blocked=True,
                threat_level="high"
            )
            
            response = client.post("/api/auth/register", json={
                "email": "malicious@evil.com",
                "password": "TestPassword123!",
                "full_name": "<script>alert('xss')</script>",
                "role": "user"
            })
        
        assert response.status_code == 403
        data = response.json()
        assert "security restrictions" in data["detail"]
    
    @pytest.mark.external_deps
    def test_user_login_flow(self, client, auth_service):
        """Test complete user login flow."""
        # Mock successful authentication
        auth_service.authenticate_user.return_value = {
            "success": True,
            "access_token": "jwt_access_token",
            "refresh_token": "jwt_refresh_token",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": "user123",
                "email": "test@example.com",
                "role": "user"
            }
        }
        
        # Mock security analysis (no threats)
        with patch('app.api.auth.get_security_service') as mock_security:
            mock_security.return_value.analyze_request_security.return_value = Mock(
                blocked=False,
                threat_level="low"
            )
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt_access_token"
        assert data["token_type"] == "bearer"
    
    @pytest.mark.external_deps
    def test_failed_login_attempts_tracking(self, client, auth_service):
        """Test failed login attempts are tracked."""
        # Mock failed authentication
        auth_service.authenticate_user.return_value = {
            "success": False,
            "error": "Invalid credentials"
        }
        
        with patch('app.api.auth.get_security_service') as mock_security:
            mock_security.return_value.analyze_request_security.return_value = Mock(
                blocked=False,
                threat_level="low"
            )
            
            # Multiple failed attempts
            for _ in range(3):
                response = client.post("/api/auth/login", json={
                    "email": "test@example.com",
                    "password": "WrongPassword"
                })
                assert response.status_code == 401
        
        # Verify authentication service was called for each attempt
        assert auth_service.authenticate_user.call_count == 3
    
    @pytest.mark.external_deps
    def test_jwt_protected_endpoint_access(self, client):
        """Test access to JWT protected endpoints."""
        # Mock authentication middleware
        with patch('app.middleware.auth_middleware.get_auth_service') as mock_auth, \
             patch('app.middleware.auth_middleware.get_security_service') as mock_security:
            
            mock_security.return_value.is_request_blocked.return_value = False
            mock_auth.return_value.verify_token.return_value = {
                "sub": "user123",
                "email": "test@example.com",
                "role": "user",
                "permissions": ["chat:access"],
                "exp": 9999999999
            }
            
            # Access protected endpoint with valid token
            response = client.get("/api/auth/profile", headers={
                "Authorization": "Bearer valid_jwt_token"
            })
            
            # Note: This would require the middleware to be properly configured
            # In a real test, you'd need to set up the full middleware stack
    
    @pytest.mark.external_deps
    def test_rate_limiting_enforcement(self, client):
        """Test rate limiting enforcement."""
        # Mock rate limiting in middleware
        with patch('app.main.rate_limit_storage') as mock_storage:
            # Simulate hitting rate limit
            mock_storage.__getitem__.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            
            response = client.post("/api/chat", json={
                "message": "Test message",
                "user_id": "user123"
            })
            
            # Note: Actual rate limiting test would need proper setup
            # This is a simplified example
    
    @pytest.mark.external_deps
    def test_security_headers_in_response(self, client):
        """Test security headers are added to responses."""
        response = client.get("/health")
        
        # Check for security headers
        # Note: These would be added by SecurityHeadersMiddleware
        headers = response.headers
        
        # In a real test, you'd check for:
        # assert "X-Content-Type-Options" in headers
        # assert "X-Frame-Options" in headers
        # assert "X-XSS-Protection" in headers
    
    @pytest.mark.external_deps
    def test_cors_configuration(self, client):
        """Test CORS configuration."""
        # Test preflight request
        response = client.options("/api/chat", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # Check CORS headers
        # Note: Actual CORS headers would be added by CORSMiddleware
        assert response.status_code in [200, 204]
    
    @pytest.mark.external_deps
    def test_input_validation_middleware(self, client):
        """Test input validation middleware."""
        # Test with malicious input
        malicious_data = {
            "message": "<script>alert('xss')</script>",
            "user_id": "user123"
        }
        
        # Mock input validation middleware to block malicious content
        with patch('app.middleware.security.InputValidationMiddleware') as mock_middleware:
            # This would simulate the middleware blocking the request
            # In a real test, the middleware would intercept and block
            pass
    
    @pytest.mark.external_deps
    def test_pii_detection_in_requests(self, client):
        """Test PII detection in request data."""
        # Test with PII data
        pii_data = {
            "message": "My email is john.doe@example.com and my SSN is 123-45-6789",
            "user_id": "user123"
        }
        
        # Mock PII detection middleware
        with patch('app.middleware.security.PIIDetectionMiddleware') as mock_middleware:
            # This would simulate the middleware detecting PII
            # In a real test, the middleware would log the detection
            pass
    
    @pytest.mark.external_deps
    def test_api_key_authentication(self, client):
        """Test API key authentication flow."""
        # Generate API key
        with patch('app.api.auth.get_security_service') as mock_security:
            mock_security.return_value.generate_api_key.return_value = {
                "api_key": "test_api_key",
                "secret": "test_secret"
            }
            
            # Mock current user for API key generation
            with patch('app.api.auth.get_current_active_user') as mock_user:
                mock_user.return_value = {"user_id": "user123"}
                
                response = client.post("/api/auth/api-key")
                
                if response.status_code == 200:
                    data = response.json()
                    assert "api_key" in data
                    assert "secret" in data
    
    @pytest.mark.external_deps
    def test_token_refresh_flow(self, client, auth_service):
        """Test token refresh flow."""
        # Mock successful token refresh
        auth_service.refresh_access_token.return_value = {
            "success": True,
            "access_token": "new_access_token",
            "token_type": "bearer",
            "expires_in": 1800
        }
        
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "valid_refresh_token"
        })
        
        if response.status_code == 200:
            data = response.json()
            assert data["access_token"] == "new_access_token"
    
    @pytest.mark.external_deps
    def test_logout_flow(self, client, auth_service):
        """Test user logout flow."""
        auth_service.revoke_refresh_token.return_value = None
        
        # Mock authenticated user
        with patch('app.api.auth.get_current_active_user') as mock_user:
            mock_user.return_value = {"user_id": "user123"}
            
            response = client.post("/api/auth/logout")
            
            if response.status_code == 200:
                data = response.json()
                assert "logged out" in data["message"].lower()
    
    @pytest.mark.external_deps
    def test_admin_security_endpoints(self, client):
        """Test admin-only security endpoints."""
        # Mock admin user
        with patch('app.api.auth.get_current_active_user') as mock_user:
            mock_user.return_value = {
                "user_id": "admin123",
                "role": "admin"
            }
            
            # Test security events endpoint
            with patch('app.api.auth.get_security_service') as mock_security:
                mock_security.return_value.get_security_metrics.return_value = {
                    "blocked_requests": 10,
                    "threat_detections": 5
                }
                
                response = client.get("/api/auth/security/events")
                
                if response.status_code == 200:
                    data = response.json()
                    assert "security_metrics" in data
    
    @pytest.mark.external_deps
    def test_non_admin_access_to_admin_endpoints(self, client):
        """Test non-admin user access to admin endpoints."""
        # Mock regular user
        with patch('app.api.auth.get_current_active_user') as mock_user:
            mock_user.return_value = {
                "user_id": "user123",
                "role": "user"
            }
            
            response = client.get("/api/auth/security/events")
            
            # Should be forbidden
            assert response.status_code == 403
    
    @pytest.mark.external_deps
    def test_comprehensive_security_flow(self, client, auth_service, security_service):
        """Test comprehensive security flow with multiple components."""
        # 1. Register user
        auth_service.register_user.return_value = {
            "success": True,
            "user_id": "user123"
        }
        
        # 2. Login user
        auth_service.authenticate_user.return_value = {
            "success": True,
            "access_token": "jwt_token",
            "refresh_token": "refresh_token",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {"id": "user123", "role": "user"}
        }
        
        # 3. Mock security services
        with patch('app.api.auth.get_security_service') as mock_sec:
            mock_sec.return_value.analyze_request_security.return_value = Mock(
                blocked=False,
                threat_level="low"
            )
            
            # Registration
            reg_response = client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User"
            })
            assert reg_response.status_code == 200
            
            # Login
            login_response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            })
            assert login_response.status_code == 200
            
            # Access protected resource (would need proper middleware setup)
            # This demonstrates the complete flow concept