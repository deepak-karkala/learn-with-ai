"""
Tests for authentication service.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.auth_service import (
    AuthenticationService, UserRole, Permission
)


@pytest.mark.external_deps
class TestAuthenticationService:
    """Test authentication service functionality."""
    
    @pytest.fixture
    def auth_service(self):
        """Create authentication service for testing."""
        with patch('app.services.auth_service.get_redis_service'), \
             patch('app.services.auth_service.get_storage_service'), \
             patch('app.services.auth_service.get_database'):
            service = AuthenticationService()
            # Mock some internal methods for testing
            service._get_user_by_email = Mock()
            service._create_user_record = Mock()
            service._is_account_locked = Mock(return_value=False)
            service._record_failed_login = Mock()
            service._clear_failed_login_attempts = Mock()
            return service
    
    @pytest.mark.external_deps
    def test_password_hashing_and_verification(self, auth_service):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        
        # Hash password
        hashed = auth_service._hash_password(password)
        
        # Verify correct password
        assert auth_service._verify_password(password, hashed)
        
        # Verify incorrect password
        assert not auth_service._verify_password("WrongPassword", hashed)
        
        # Hash should be different each time
        hashed2 = auth_service._hash_password(password)
        assert hashed != hashed2
    
    @pytest.mark.external_deps
    def test_user_registration_success(self, auth_service):
        """Test successful user registration."""
        auth_service._validate_email = Mock(return_value=True)
        auth_service._validate_password_strength = Mock(return_value=True)
        auth_service._get_user_by_email.return_value = None
        auth_service._create_user_record.return_value = "user123"
        
        result = auth_service.register_user(
            email="test@example.com",
            password="TestPassword123!",
            full_name="Test User",
            role=UserRole.USER
        )
        
        assert result["success"]
        assert result["user_id"] == "user123"
        assert result["message"] == "User registered successfully"
    
    @pytest.mark.external_deps
    def test_user_registration_existing_user(self, auth_service):
        """Test registration with existing user."""
        auth_service._validate_email = Mock(return_value=True)
        auth_service._validate_password_strength = Mock(return_value=True)
        auth_service._get_user_by_email.return_value = {"id": "existing"}
        
        result = auth_service.register_user(
            email="existing@example.com",
            password="TestPassword123!",
            full_name="Test User"
        )
        
        assert not result["success"]
        assert result["error"] == "User already exists"
    
    @pytest.mark.external_deps
    def test_user_registration_weak_password(self, auth_service):
        """Test registration with weak password."""
        auth_service._validate_email = Mock(return_value=True)
        auth_service._validate_password_strength = Mock(return_value=False)
        
        result = auth_service.register_user(
            email="test@example.com",
            password="weak",
            full_name="Test User"
        )
        
        assert not result["success"]
        assert "password" in result["error"].lower()
    
    @pytest.mark.external_deps
    def test_authentication_success(self, auth_service):
        """Test successful authentication."""
        # Mock user data
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "password_hash": auth_service._hash_password("TestPassword123!"),
            "role": "user",
            "is_active": True
        }
        
        auth_service._get_user_by_email.return_value = user_data
        auth_service._generate_access_token = Mock(return_value="access_token")
        auth_service._generate_refresh_token = Mock(return_value="refresh_token")
        auth_service._sanitize_user_data = Mock(return_value={"id": "user123", "email": "test@example.com"})
        
        result = auth_service.authenticate_user(
            email="test@example.com",
            password="TestPassword123!",
            ip_address="127.0.0.1"
        )
        
        assert result["success"]
        assert result["access_token"] == "access_token"
        assert result["refresh_token"] == "refresh_token"
        assert result["token_type"] == "bearer"
    
    @pytest.mark.external_deps
    def test_authentication_wrong_password(self, auth_service):
        """Test authentication with wrong password."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "password_hash": auth_service._hash_password("CorrectPassword123!"),
            "role": "user",
            "is_active": True
        }
        
        auth_service._get_user_by_email.return_value = user_data
        
        result = auth_service.authenticate_user(
            email="test@example.com",
            password="WrongPassword",
            ip_address="127.0.0.1"
        )
        
        assert not result["success"]
        assert result["error"] == "Invalid credentials"
        auth_service._record_failed_login.assert_called_once()
    
    @pytest.mark.external_deps
    def test_authentication_user_not_found(self, auth_service):
        """Test authentication with non-existent user."""
        auth_service._get_user_by_email.return_value = None
        
        result = auth_service.authenticate_user(
            email="nonexistent@example.com",
            password="SomePassword",
            ip_address="127.0.0.1"
        )
        
        assert not result["success"]
        assert result["error"] == "Invalid credentials"
    
    @pytest.mark.external_deps
    def test_authentication_account_locked(self, auth_service):
        """Test authentication with locked account."""
        auth_service._is_account_locked.return_value = True
        
        result = auth_service.authenticate_user(
            email="test@example.com",
            password="SomePassword",
            ip_address="127.0.0.1"
        )
        
        assert not result["success"]
        assert "locked" in result["error"].lower()
    
    @pytest.mark.external_deps
    def test_authentication_inactive_account(self, auth_service):
        """Test authentication with inactive account."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "password_hash": auth_service._hash_password("TestPassword123!"),
            "role": "user",
            "is_active": False
        }
        
        auth_service._get_user_by_email.return_value = user_data
        
        result = auth_service.authenticate_user(
            email="test@example.com",
            password="TestPassword123!",
            ip_address="127.0.0.1"
        )
        
        assert not result["success"]
        assert "deactivated" in result["error"].lower()
    
    @pytest.mark.external_deps
    def test_jwt_token_generation(self, auth_service):
        """Test JWT token generation."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        # Generate access token
        access_token = auth_service._generate_access_token(user_data)
        assert isinstance(access_token, str)
        assert len(access_token) > 0
        
        # Generate refresh token
        refresh_token = auth_service._generate_refresh_token(user_data)
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0
        
        # Tokens should be different
        assert access_token != refresh_token
    
    @pytest.mark.external_deps
    def test_jwt_token_verification(self, auth_service):
        """Test JWT token verification."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        # Generate and verify access token
        access_token = auth_service._generate_access_token(user_data)
        token_data = auth_service.verify_token(access_token)
        
        assert token_data is not None
        assert token_data["sub"] == "user123"
        assert token_data["email"] == "test@example.com"
        assert token_data["role"] == "user"
        assert token_data["type"] == "access"
    
    @pytest.mark.external_deps
    def test_expired_token_verification(self, auth_service):
        """Test verification of expired token."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        # Mock expired token
        with patch('app.services.auth_service.datetime') as mock_datetime:
            # Set current time to future
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(hours=2)
            
            access_token = auth_service._generate_access_token(user_data)
            
            # Reset to current time for verification
            mock_datetime.utcnow.return_value = datetime.utcnow()
            
            token_data = auth_service.verify_token(access_token)
            assert token_data is None
    
    @pytest.mark.external_deps
    def test_refresh_token_functionality(self, auth_service):
        """Test refresh token functionality."""
        auth_service._verify_refresh_token = Mock(return_value={
            "user_id": "user123",
            "email": "test@example.com",
            "role": "user"
        })
        auth_service._generate_access_token = Mock(return_value="new_access_token")
        
        result = auth_service.refresh_access_token("valid_refresh_token")
        
        assert result["success"]
        assert result["access_token"] == "new_access_token"
        assert result["token_type"] == "bearer"
    
    @pytest.mark.external_deps
    def test_invalid_refresh_token(self, auth_service):
        """Test refresh with invalid token."""
        auth_service._verify_refresh_token = Mock(return_value=None)
        
        result = auth_service.refresh_access_token("invalid_refresh_token")
        
        assert not result["success"]
        assert "invalid" in result["error"].lower()
    
    @pytest.mark.external_deps
    def test_role_permissions_mapping(self, auth_service):
        """Test role-based permissions mapping."""
        # Test guest permissions
        guest_permissions = auth_service._get_user_permissions(UserRole.GUEST)
        assert Permission.CHAT_ACCESS in guest_permissions
        assert Permission.ADMIN_SYSTEM not in guest_permissions
        
        # Test user permissions
        user_permissions = auth_service._get_user_permissions(UserRole.USER)
        assert Permission.CHAT_ACCESS in user_permissions
        assert Permission.WHITEBOARD_CREATE in user_permissions
        assert Permission.ADMIN_SYSTEM not in user_permissions
        
        # Test admin permissions
        admin_permissions = auth_service._get_user_permissions(UserRole.ADMIN)
        assert Permission.CHAT_ACCESS in admin_permissions
        assert Permission.ADMIN_SYSTEM in admin_permissions
        assert len(admin_permissions) > len(user_permissions)
    
    @pytest.mark.external_deps
    def test_permission_checking(self, auth_service):
        """Test permission checking functionality."""
        user_permissions = [Permission.CHAT_ACCESS, Permission.WHITEBOARD_CREATE]
        
        # User has permission
        assert auth_service.has_permission("user123", Permission.CHAT_ACCESS, user_permissions)
        
        # User doesn't have permission
        assert not auth_service.has_permission("user123", Permission.ADMIN_SYSTEM, user_permissions)
    
    @pytest.mark.external_deps
    def test_password_strength_validation(self, auth_service):
        """Test password strength validation."""
        # Strong password
        assert auth_service._validate_password_strength("StrongPass123!")
        
        # Weak passwords
        assert not auth_service._validate_password_strength("weak")
        assert not auth_service._validate_password_strength("nouppercaselower123!")
        assert not auth_service._validate_password_strength("NOLOWERCASE123!")
        assert not auth_service._validate_password_strength("NoNumbers!")
        assert not auth_service._validate_password_strength("NoSpecialChars123")
    
    @pytest.mark.external_deps
    def test_email_validation(self, auth_service):
        """Test email validation."""
        # Valid emails
        assert auth_service._validate_email("test@example.com")
        assert auth_service._validate_email("user.name+tag@domain.co.uk")
        
        # Invalid emails
        assert not auth_service._validate_email("invalid-email")
        assert not auth_service._validate_email("@domain.com")
        assert not auth_service._validate_email("user@")
        assert not auth_service._validate_email("")
    
    @pytest.mark.external_deps
    def test_account_lockout_mechanism(self, auth_service):
        """Test account lockout after failed attempts."""
        auth_service._redis_service = Mock()
        auth_service._redis_service.is_available.return_value = True
        auth_service._redis_service.get_cache.return_value = None
        auth_service._redis_service.set_cache = Mock()
        
        email = "test@example.com"
        ip_address = "127.0.0.1"
        
        # Record failed attempts
        for i in range(auth_service._max_login_attempts):
            auth_service._record_failed_login(email, ip_address)
        
        # Check if account is locked
        auth_service._redis_service.get_cache.return_value = auth_service._max_login_attempts
        assert auth_service._is_account_locked(email)
    
    @pytest.mark.external_deps
    def test_change_password(self, auth_service):
        """Test password change functionality."""
        user_data = {
            "id": "user123",
            "password_hash": auth_service._hash_password("OldPassword123!")
        }
        
        auth_service._get_user_by_id = Mock(return_value=user_data)
        auth_service._update_user_password = Mock(return_value=True)
        
        result = auth_service.change_password(
            user_id="user123",
            current_password="OldPassword123!",
            new_password="NewPassword456!"
        )
        
        assert result["success"]
        assert "changed" in result["message"].lower()
        auth_service._update_user_password.assert_called_once()
    
    @pytest.mark.external_deps
    def test_change_password_wrong_current(self, auth_service):
        """Test password change with wrong current password."""
        user_data = {
            "id": "user123",
            "password_hash": auth_service._hash_password("OldPassword123!")
        }
        
        auth_service._get_user_by_id = Mock(return_value=user_data)
        
        result = auth_service.change_password(
            user_id="user123",
            current_password="WrongPassword",
            new_password="NewPassword456!"
        )
        
        assert not result["success"]
        assert "current password" in result["error"].lower()