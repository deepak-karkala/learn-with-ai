"""
Security configuration management for the AI System Design Learning Platform.
"""

import os
import secrets
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security configuration levels."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class AuthenticationConfig:
    """Authentication configuration settings."""
    jwt_secret: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special_chars: bool = True
    enable_api_key_auth: bool = True
    api_key_length: int = 32
    
    def validate(self) -> List[str]:
        """Validate authentication configuration."""
        errors = []
        
        if len(self.jwt_secret) < 32:
            errors.append("JWT secret must be at least 32 characters long")
        
        if self.access_token_expire_minutes < 5:
            errors.append("Access token expiration must be at least 5 minutes")
        
        if self.refresh_token_expire_days < 1:
            errors.append("Refresh token expiration must be at least 1 day")
        
        if self.max_login_attempts < 3:
            errors.append("Max login attempts must be at least 3")
        
        if self.lockout_duration_minutes < 5:
            errors.append("Lockout duration must be at least 5 minutes")
        
        if self.password_min_length < 8:
            errors.append("Password minimum length must be at least 8 characters")
        
        return errors


@dataclass
class EncryptionConfig:
    """Encryption configuration settings."""
    encryption_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    encrypt_sensitive_data: bool = True
    encrypt_logs: bool = False
    encrypt_database_fields: List[str] = field(default_factory=lambda: [
        "password_hash", "api_keys", "tokens", "pii_data"
    ])
    
    def validate(self) -> List[str]:
        """Validate encryption configuration."""
        errors = []
        
        if len(self.encryption_key) < 32:
            errors.append("Encryption key must be at least 32 characters long")
        
        if self.key_rotation_days < 30:
            errors.append("Key rotation period must be at least 30 days")
        
        return errors


@dataclass
class RateLimitingConfig:
    """Rate limiting configuration settings."""
    enable_rate_limiting: bool = True
    default_requests_per_minute: int = 60
    burst_requests: int = 10
    rate_limit_window_seconds: int = 60
    strict_rate_limiting: bool = False
    whitelist_ips: List[str] = field(default_factory=list)
    blacklist_ips: List[str] = field(default_factory=list)
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "/api/chat": {"requests_per_minute": 30, "burst_requests": 5},
        "/api/whiteboard": {"requests_per_minute": 20, "burst_requests": 3},
        "/api/assessment": {"requests_per_minute": 10, "burst_requests": 2},
        "/api/diagrams": {"requests_per_minute": 15, "burst_requests": 3}
    })
    
    def validate(self) -> List[str]:
        """Validate rate limiting configuration."""
        errors = []
        
        if self.default_requests_per_minute < 1:
            errors.append("Default requests per minute must be at least 1")
        
        if self.burst_requests < 1:
            errors.append("Burst requests must be at least 1")
        
        if self.rate_limit_window_seconds < 10:
            errors.append("Rate limit window must be at least 10 seconds")
        
        return errors


@dataclass
class SecurityMonitoringConfig:
    """Security monitoring configuration settings."""
    enable_threat_detection: bool = True
    enable_pii_detection: bool = True
    enable_input_validation: bool = True
    enable_security_headers: bool = True
    enable_cors_protection: bool = True
    log_security_events: bool = True
    alert_on_high_threats: bool = True
    alert_on_multiple_failures: bool = True
    failure_threshold: int = 5
    failure_window_minutes: int = 10
    blocked_patterns: List[str] = field(default_factory=lambda: [
        "<script", "javascript:", "vbscript:", "onload=", "onerror=",
        "eval(", "exec(", "system(", "shell_exec",
        "union select", "drop table", "delete from", "insert into", "update set",
        "&&", "||", ";rm", ";cat", "&cat", "|cat"
    ])
    
    def validate(self) -> List[str]:
        """Validate security monitoring configuration."""
        errors = []
        
        if self.failure_threshold < 3:
            errors.append("Failure threshold must be at least 3")
        
        if self.failure_window_minutes < 5:
            errors.append("Failure window must be at least 5 minutes")
        
        return errors


@dataclass
class SecurityConfig:
    """Complete security configuration."""
    security_level: SecurityLevel = SecurityLevel.DEVELOPMENT
    authentication: AuthenticationConfig = field(default_factory=AuthenticationConfig)
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)
    rate_limiting: RateLimitingConfig = field(default_factory=RateLimitingConfig)
    monitoring: SecurityMonitoringConfig = field(default_factory=SecurityMonitoringConfig)
    
    # Security headers configuration
    enable_hsts: bool = True
    enable_csp: bool = True
    enable_frame_protection: bool = True
    enable_content_type_options: bool = True
    
    # CORS configuration
    allowed_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "https://learn-with-ai.vercel.app"
    ])
    allowed_methods: List[str] = field(default_factory=lambda: [
        "GET", "POST", "PUT", "DELETE", "OPTIONS"
    ])
    allowed_headers: List[str] = field(default_factory=lambda: [
        "Accept", "Accept-Language", "Content-Language", "Content-Type",
        "Authorization", "X-Requested-With", "X-User-ID", "X-Session-ID"
    ])
    
    def validate(self) -> List[str]:
        """Validate complete security configuration."""
        errors = []
        
        # Validate sub-configurations
        errors.extend(self.authentication.validate())
        errors.extend(self.encryption.validate())
        errors.extend(self.rate_limiting.validate())
        errors.extend(self.monitoring.validate())
        
        # Additional validations based on security level
        if self.security_level == SecurityLevel.PRODUCTION:
            if not self.enable_hsts:
                errors.append("HSTS must be enabled in production")
            
            if not self.enable_csp:
                errors.append("CSP must be enabled in production")
            
            if self.authentication.access_token_expire_minutes > 60:
                errors.append("Access token expiration should be <= 60 minutes in production")
            
            if not self.encryption.encrypt_sensitive_data:
                errors.append("Sensitive data encryption must be enabled in production")
        
        return errors
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables for current configuration."""
        env_vars = {
            # Security level
            "SECURITY_LEVEL": self.security_level.value,
            
            # Authentication
            "JWT_SECRET": self.authentication.jwt_secret,
            "JWT_ALGORITHM": self.authentication.jwt_algorithm,
            "ACCESS_TOKEN_EXPIRE_MINUTES": str(self.authentication.access_token_expire_minutes),
            "REFRESH_TOKEN_EXPIRE_DAYS": str(self.authentication.refresh_token_expire_days),
            "MAX_LOGIN_ATTEMPTS": str(self.authentication.max_login_attempts),
            "LOCKOUT_DURATION_MINUTES": str(self.authentication.lockout_duration_minutes),
            "ENABLE_API_KEY_AUTH": str(self.authentication.enable_api_key_auth).lower(),
            
            # Encryption
            "ENCRYPTION_KEY": self.encryption.encryption_key,
            "ENCRYPT_SENSITIVE_DATA": str(self.encryption.encrypt_sensitive_data).lower(),
            "KEY_ROTATION_DAYS": str(self.encryption.key_rotation_days),
            
            # Rate limiting
            "ENABLE_RATE_LIMITING": str(self.rate_limiting.enable_rate_limiting).lower(),
            "RATE_LIMIT_REQUESTS_PER_MINUTE": str(self.rate_limiting.default_requests_per_minute),
            "RATE_LIMIT_BURST_SIZE": str(self.rate_limiting.burst_requests),
            
            # Security monitoring
            "ENABLE_THREAT_DETECTION": str(self.monitoring.enable_threat_detection).lower(),
            "ENABLE_PII_DETECTION": str(self.monitoring.enable_pii_detection).lower(),
            "ENABLE_INPUT_VALIDATION": str(self.monitoring.enable_input_validation).lower(),
            "ENABLE_SECURITY_HEADERS": str(self.monitoring.enable_security_headers).lower(),
            
            # Security headers
            "ENABLE_HSTS": str(self.enable_hsts).lower(),
            "ENABLE_CSP": str(self.enable_csp).lower(),
            
            # CORS
            "ALLOWED_ORIGINS": ",".join(self.allowed_origins),
        }
        
        return env_vars


class SecurityConfigManager:
    """Manager for security configuration."""
    
    def __init__(self):
        self._config: Optional[SecurityConfig] = None
        self._logger = logging.getLogger(__name__)
    
    def load_from_environment(self) -> SecurityConfig:
        """Load security configuration from environment variables."""
        try:
            # Determine security level
            security_level_str = os.getenv("SECURITY_LEVEL", "development")
            try:
                security_level = SecurityLevel(security_level_str)
            except ValueError:
                self._logger.warning(f"Invalid security level: {security_level_str}, using development")
                security_level = SecurityLevel.DEVELOPMENT
            
            # Load authentication config
            auth_config = AuthenticationConfig(
                jwt_secret=os.getenv("JWT_SECRET", secrets.token_urlsafe(32)),
                jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
                access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
                refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
                max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
                lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
                enable_api_key_auth=os.getenv("ENABLE_API_KEY_AUTH", "true").lower() == "true"
            )
            
            # Load encryption config
            encryption_config = EncryptionConfig(
                encryption_key=os.getenv("ENCRYPTION_KEY", secrets.token_urlsafe(32)),
                encrypt_sensitive_data=os.getenv("ENCRYPT_SENSITIVE_DATA", "true").lower() == "true",
                key_rotation_days=int(os.getenv("KEY_ROTATION_DAYS", "90"))
            )
            
            # Load rate limiting config
            rate_limiting_config = RateLimitingConfig(
                enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
                default_requests_per_minute=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
                burst_requests=int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))
            )
            
            # Load monitoring config
            monitoring_config = SecurityMonitoringConfig(
                enable_threat_detection=os.getenv("ENABLE_THREAT_DETECTION", "true").lower() == "true",
                enable_pii_detection=os.getenv("ENABLE_PII_DETECTION", "true").lower() == "true",
                enable_input_validation=os.getenv("ENABLE_INPUT_VALIDATION", "true").lower() == "true",
                enable_security_headers=os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
            )
            
            # Load CORS config
            allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
            allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()] or [
                "http://localhost:3000",
                "https://learn-with-ai.vercel.app"
            ]
            
            # Create complete config
            config = SecurityConfig(
                security_level=security_level,
                authentication=auth_config,
                encryption=encryption_config,
                rate_limiting=rate_limiting_config,
                monitoring=monitoring_config,
                enable_hsts=os.getenv("ENABLE_HSTS", "true").lower() == "true",
                enable_csp=os.getenv("ENABLE_CSP", "true").lower() == "true",
                allowed_origins=allowed_origins
            )
            
            # Validate configuration
            errors = config.validate()
            if errors:
                self._logger.error(f"Security configuration validation errors: {errors}")
                # Use defaults for invalid configurations in non-production
                if security_level == SecurityLevel.PRODUCTION:
                    raise ValueError(f"Invalid security configuration for production: {errors}")
            
            self._config = config
            self._logger.info(f"Security configuration loaded for {security_level.value} environment")
            
            return config
            
        except ValueError as e:
            # Re-raise validation errors for production
            self._logger.error(f"Failed to load security configuration: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Failed to load security configuration: {e}")
            # Return safe defaults for non-validation errors
            return SecurityConfig()
    
    def get_config(self) -> SecurityConfig:
        """Get current security configuration."""
        if self._config is None:
            self._config = self.load_from_environment()
        return self._config
    
    def validate_production_readiness(self) -> Tuple[bool, List[str]]:
        """Validate if current configuration is production ready."""
        config = self.get_config()
        errors = []
        
        # Check required environment variables
        required_env_vars = [
            "JWT_SECRET", "ENCRYPTION_KEY", "DATABASE_URL",
            "REDIS_URL", "ALLOWED_ORIGINS"
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Validate configuration
        config_errors = config.validate()
        errors.extend(config_errors)
        
        # Check security level
        if config.security_level != SecurityLevel.PRODUCTION:
            errors.append("Security level must be set to 'production'")
        
        # Additional production checks
        if len(config.authentication.jwt_secret) < 64:
            errors.append("JWT secret should be at least 64 characters in production")
        
        if len(config.encryption.encryption_key) < 32:
            errors.append("Encryption key should be at least 32 characters in production")
        
        is_ready = len(errors) == 0
        return is_ready, errors
    
    def generate_example_env_file(self, security_level: SecurityLevel = SecurityLevel.DEVELOPMENT) -> str:
        """Generate example .env file for given security level."""
        config = SecurityConfig(security_level=security_level)
        
        if security_level == SecurityLevel.PRODUCTION:
            # Use stronger defaults for production
            config.authentication.access_token_expire_minutes = 15
            config.authentication.max_login_attempts = 3
            config.authentication.lockout_duration_minutes = 30
            config.rate_limiting.default_requests_per_minute = 30
            config.rate_limiting.strict_rate_limiting = True
        
        env_vars = config.get_environment_variables()
        
        lines = [
            f"# Security Configuration for {security_level.value.upper()} Environment",
            f"# Generated on {datetime.utcnow().isoformat()}",
            "",
            "# =============================================================================",
            "# Security Level",
            "# =============================================================================",
            "",
        ]
        
        # Group environment variables by category
        categories = {
            "Security Level": ["SECURITY_LEVEL"],
            "Authentication": [
                "JWT_SECRET", "JWT_ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES",
                "REFRESH_TOKEN_EXPIRE_DAYS", "MAX_LOGIN_ATTEMPTS", 
                "LOCKOUT_DURATION_MINUTES", "ENABLE_API_KEY_AUTH"
            ],
            "Encryption": [
                "ENCRYPTION_KEY", "ENCRYPT_SENSITIVE_DATA", "KEY_ROTATION_DAYS"
            ],
            "Rate Limiting": [
                "ENABLE_RATE_LIMITING", "RATE_LIMIT_REQUESTS_PER_MINUTE", 
                "RATE_LIMIT_BURST_SIZE"
            ],
            "Security Monitoring": [
                "ENABLE_THREAT_DETECTION", "ENABLE_PII_DETECTION",
                "ENABLE_INPUT_VALIDATION", "ENABLE_SECURITY_HEADERS"
            ],
            "Security Headers": ["ENABLE_HSTS", "ENABLE_CSP"],
            "CORS": ["ALLOWED_ORIGINS"]
        }
        
        for category, vars_list in categories.items():
            lines.extend([
                f"# {category}",
                "# " + "=" * (len(category) + 2),
                ""
            ])
            
            for var in vars_list:
                if var in env_vars:
                    value = env_vars[var]
                    # Add security warning for secrets
                    if var in ["JWT_SECRET", "ENCRYPTION_KEY"]:
                        lines.append(f"# WARNING: Keep this secret secure!")
                    lines.append(f"{var}={value}")
            
            lines.append("")
        
        return "\n".join(lines)


# Global security config manager
_security_config_manager: Optional[SecurityConfigManager] = None


def get_security_config_manager() -> SecurityConfigManager:
    """Get the global security configuration manager."""
    global _security_config_manager
    if _security_config_manager is None:
        _security_config_manager = SecurityConfigManager()
    return _security_config_manager


def get_security_config() -> SecurityConfig:
    """Get current security configuration."""
    return get_security_config_manager().get_config()