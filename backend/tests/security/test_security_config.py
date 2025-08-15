"""
Tests for security configuration management.
"""

import pytest
import os
from unittest.mock import patch, Mock

from app.config.security import (
    SecurityConfig, SecurityLevel, AuthenticationConfig,
    EncryptionConfig, RateLimitingConfig, SecurityMonitoringConfig,
    SecurityConfigManager
)


class TestSecurityConfigClasses:
    """Test security configuration classes."""
    
    def test_authentication_config_defaults(self):
        """Test authentication config default values."""
        config = AuthenticationConfig()
        
        assert config.jwt_algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 7
        assert config.max_login_attempts == 5
        assert config.lockout_duration_minutes == 15
        assert config.password_min_length == 8
        assert config.password_require_uppercase is True
        assert config.enable_api_key_auth is True
        assert len(config.jwt_secret) >= 32
    
    def test_authentication_config_validation(self):
        """Test authentication config validation."""
        # Valid config
        config = AuthenticationConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid config
        config = AuthenticationConfig(
            jwt_secret="short",  # Too short
            access_token_expire_minutes=2,  # Too short
            max_login_attempts=1,  # Too low
            password_min_length=4  # Too short
        )
        errors = config.validate()
        assert len(errors) > 0
        assert any("JWT secret" in error for error in errors)
        assert any("Access token" in error for error in errors)
        assert any("login attempts" in error for error in errors)
        assert any("Password minimum" in error for error in errors)
    
    def test_encryption_config_defaults(self):
        """Test encryption config default values."""
        config = EncryptionConfig()
        
        assert config.encryption_algorithm == "AES-256-GCM"
        assert config.key_rotation_days == 90
        assert config.encrypt_sensitive_data is True
        assert config.encrypt_logs is False
        assert "password_hash" in config.encrypt_database_fields
        assert "api_keys" in config.encrypt_database_fields
        assert len(config.encryption_key) >= 32
    
    def test_encryption_config_validation(self):
        """Test encryption config validation."""
        # Valid config
        config = EncryptionConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid config
        config = EncryptionConfig(
            encryption_key="short",  # Too short
            key_rotation_days=15  # Too short
        )
        errors = config.validate()
        assert len(errors) > 0
        assert any("Encryption key" in error for error in errors)
        assert any("rotation period" in error for error in errors)
    
    def test_rate_limiting_config_defaults(self):
        """Test rate limiting config default values."""
        config = RateLimitingConfig()
        
        assert config.enable_rate_limiting is True
        assert config.default_requests_per_minute == 60
        assert config.burst_requests == 10
        assert config.rate_limit_window_seconds == 60
        assert isinstance(config.endpoint_limits, dict)
        assert "/api/chat" in config.endpoint_limits
    
    def test_rate_limiting_config_validation(self):
        """Test rate limiting config validation."""
        # Valid config
        config = RateLimitingConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid config
        config = RateLimitingConfig(
            default_requests_per_minute=0,  # Too low
            burst_requests=0,  # Too low
            rate_limit_window_seconds=5  # Too short
        )
        errors = config.validate()
        assert len(errors) > 0
    
    def test_security_monitoring_config_defaults(self):
        """Test security monitoring config default values."""
        config = SecurityMonitoringConfig()
        
        assert config.enable_threat_detection is True
        assert config.enable_pii_detection is True
        assert config.enable_input_validation is True
        assert config.log_security_events is True
        assert config.failure_threshold == 5
        assert config.failure_window_minutes == 10
        assert len(config.blocked_patterns) > 0
        assert "<script" in config.blocked_patterns
    
    def test_security_monitoring_config_validation(self):
        """Test security monitoring config validation."""
        # Valid config
        config = SecurityMonitoringConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid config
        config = SecurityMonitoringConfig(
            failure_threshold=1,  # Too low
            failure_window_minutes=2  # Too short
        )
        errors = config.validate()
        assert len(errors) > 0
    
    def test_complete_security_config_defaults(self):
        """Test complete security config default values."""
        config = SecurityConfig()
        
        assert config.security_level == SecurityLevel.DEVELOPMENT
        assert isinstance(config.authentication, AuthenticationConfig)
        assert isinstance(config.encryption, EncryptionConfig)
        assert isinstance(config.rate_limiting, RateLimitingConfig)
        assert isinstance(config.monitoring, SecurityMonitoringConfig)
        
        assert config.enable_hsts is True
        assert config.enable_csp is True
        assert len(config.allowed_origins) > 0
        assert "http://localhost:3000" in config.allowed_origins
    
    def test_security_config_validation_development(self):
        """Test security config validation for development."""
        config = SecurityConfig(security_level=SecurityLevel.DEVELOPMENT)
        errors = config.validate()
        assert len(errors) == 0  # Development should be lenient
    
    def test_security_config_validation_production(self):
        """Test security config validation for production."""
        config = SecurityConfig(security_level=SecurityLevel.PRODUCTION)
        
        # Default config should pass production validation
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid production config
        config.enable_hsts = False
        config.enable_csp = False
        config.authentication.access_token_expire_minutes = 120  # Too long
        config.encryption.encrypt_sensitive_data = False
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("HSTS" in error for error in errors)
        assert any("CSP" in error for error in errors)
        assert any("token expiration" in error for error in errors)
        assert any("encryption" in error for error in errors)
    
    def test_environment_variables_generation(self):
        """Test environment variables generation."""
        config = SecurityConfig()
        env_vars = config.get_environment_variables()
        
        # Check required variables
        assert "SECURITY_LEVEL" in env_vars
        assert "JWT_SECRET" in env_vars
        assert "ENCRYPTION_KEY" in env_vars
        assert "ENABLE_RATE_LIMITING" in env_vars
        assert "ALLOWED_ORIGINS" in env_vars
        
        # Check values
        assert env_vars["SECURITY_LEVEL"] == "development"
        assert env_vars["ENABLE_RATE_LIMITING"] == "true"
        assert len(env_vars["JWT_SECRET"]) >= 32
        assert len(env_vars["ENCRYPTION_KEY"]) >= 32


class TestSecurityConfigManager:
    """Test security configuration manager."""
    
    @pytest.fixture
    def config_manager(self):
        """Create security config manager."""
        return SecurityConfigManager()
    
    def test_load_from_environment_defaults(self, config_manager):
        """Test loading config from environment with defaults."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            config = config_manager.load_from_environment()
            
            assert config.security_level == SecurityLevel.DEVELOPMENT
            assert config.authentication.access_token_expire_minutes == 30
            assert config.rate_limiting.enable_rate_limiting is True
    
    def test_load_from_environment_custom(self, config_manager):
        """Test loading config from environment with custom values."""
        env_vars = {
            "SECURITY_LEVEL": "production",
            "JWT_SECRET": "custom_jwt_secret_" + "x" * 50,
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            "ENABLE_RATE_LIMITING": "false",
            "ALLOWED_ORIGINS": "https://example.com,https://app.example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            config = config_manager.load_from_environment()
            
            assert config.security_level == SecurityLevel.PRODUCTION
            assert config.authentication.jwt_secret.startswith("custom_jwt_secret_")
            assert config.authentication.access_token_expire_minutes == 15
            assert config.rate_limiting.enable_rate_limiting is False
            assert "https://example.com" in config.allowed_origins
    
    def test_load_invalid_security_level(self, config_manager):
        """Test loading config with invalid security level."""
        with patch.dict(os.environ, {"SECURITY_LEVEL": "invalid_level"}):
            config = config_manager.load_from_environment()
            # Should default to development
            assert config.security_level == SecurityLevel.DEVELOPMENT
    
    def test_production_readiness_validation_success(self, config_manager):
        """Test production readiness validation success."""
        # Set up production environment
        env_vars = {
            "SECURITY_LEVEL": "production",
            "JWT_SECRET": "x" * 64,
            "ENCRYPTION_KEY": "x" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "ALLOWED_ORIGINS": "https://example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            config_manager.load_from_environment()
            is_ready, errors = config_manager.validate_production_readiness()
            
            assert is_ready
            assert len(errors) == 0
    
    def test_production_readiness_validation_failure(self, config_manager):
        """Test production readiness validation failure."""
        # Missing required environment variables
        with patch.dict(os.environ, {"SECURITY_LEVEL": "development"}):
            config_manager.load_from_environment()
            is_ready, errors = config_manager.validate_production_readiness()
            
            assert not is_ready
            assert len(errors) > 0
            assert any("JWT_SECRET" in error for error in errors)
            assert any("production" in error for error in errors)
    
    def test_generate_example_env_file_development(self, config_manager):
        """Test generating example env file for development."""
        env_content = config_manager.generate_example_env_file(SecurityLevel.DEVELOPMENT)
        
        assert "# Security Configuration for DEVELOPMENT Environment" in env_content
        assert "SECURITY_LEVEL=development" in env_content
        assert "ACCESS_TOKEN_EXPIRE_MINUTES=30" in env_content
        assert "ENABLE_RATE_LIMITING=true" in env_content
        assert "JWT_SECRET=" in env_content
        assert "ENCRYPTION_KEY=" in env_content
    
    def test_generate_example_env_file_production(self, config_manager):
        """Test generating example env file for production."""
        env_content = config_manager.generate_example_env_file(SecurityLevel.PRODUCTION)
        
        assert "# Security Configuration for PRODUCTION Environment" in env_content
        assert "SECURITY_LEVEL=production" in env_content
        assert "ACCESS_TOKEN_EXPIRE_MINUTES=15" in env_content  # Stricter for production
        assert "MAX_LOGIN_ATTEMPTS=3" in env_content  # Stricter for production
        assert "WARNING: Keep this secret secure!" in env_content
    
    def test_get_config_caching(self, config_manager):
        """Test config caching behavior."""
        # First call should load from environment
        with patch.object(config_manager, 'load_from_environment') as mock_load:
            mock_load.return_value = SecurityConfig()
            
            config1 = config_manager.get_config()
            config2 = config_manager.get_config()
            
            # Should only load once
            mock_load.assert_called_once()
            assert config1 is config2
    
    def test_config_validation_with_logging(self, config_manager):
        """Test config validation with proper logging."""
        # Create invalid config that should generate warnings
        env_vars = {
            "SECURITY_LEVEL": "development",
            "JWT_SECRET": "short",  # Too short
            "ACCESS_TOKEN_EXPIRE_MINUTES": "1"  # Too short
        }
        
        with patch.dict(os.environ, env_vars):
            with patch.object(config_manager, '_logger') as mock_logger:
                config = config_manager.load_from_environment()
                
                # Should log validation errors
                mock_logger.error.assert_called()
                assert config is not None  # Should still return config
    
    def test_production_validation_strict_mode(self, config_manager):
        """Test production validation in strict mode."""
        # Production with validation errors should raise exception
        env_vars = {
            "SECURITY_LEVEL": "production",
            "JWT_SECRET": "short",  # Invalid for production
        }
        
        with patch.dict(os.environ, env_vars):
            with pytest.raises(ValueError) as exc_info:
                config_manager.load_from_environment()
            
            assert "Invalid security configuration for production" in str(exc_info.value)


class TestSecurityLevels:
    """Test security level specific configurations."""
    
    def test_development_security_level(self):
        """Test development security level settings."""
        config = SecurityConfig(security_level=SecurityLevel.DEVELOPMENT)
        
        # Development should be more permissive
        assert config.authentication.access_token_expire_minutes == 30
        errors = config.validate()
        assert len(errors) == 0
    
    def test_production_security_level(self):
        """Test production security level settings."""
        config = SecurityConfig(security_level=SecurityLevel.PRODUCTION)
        
        # Production should be more restrictive
        assert config.enable_hsts is True
        assert config.enable_csp is True
        
        # Should pass validation with defaults
        errors = config.validate()
        assert len(errors) == 0
    
    def test_staging_security_level(self):
        """Test staging security level settings."""
        config = SecurityConfig(security_level=SecurityLevel.STAGING)
        
        # Staging should be between development and production
        errors = config.validate()
        assert len(errors) == 0
    
    def test_testing_security_level(self):
        """Test testing security level settings."""
        config = SecurityConfig(security_level=SecurityLevel.TESTING)
        
        # Testing should allow for test-specific configurations
        errors = config.validate()
        assert len(errors) == 0