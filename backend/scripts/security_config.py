#!/usr/bin/env python3
"""
Security configuration management CLI tool.

Usage:
    python scripts/security_config.py validate
    python scripts/security_config.py generate-env [--level=production]
    python scripts/security_config.py check-production
    python scripts/security_config.py rotate-keys
"""

import sys
import os
import argparse
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.security import (
    SecurityConfigManager, SecurityLevel, get_security_config_manager
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_config():
    """Validate current security configuration."""
    logger.info("Validating security configuration...")
    
    manager = get_security_config_manager()
    config = manager.get_config()
    
    errors = config.validate()
    
    if errors:
        logger.error("Security configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    else:
        logger.info(f"Security configuration is valid for {config.security_level.value} environment")
        return True


def generate_env_file(security_level: SecurityLevel, output_file: str = None):
    """Generate example .env file."""
    logger.info(f"Generating .env file for {security_level.value} environment...")
    
    manager = get_security_config_manager()
    env_content = manager.generate_example_env_file(security_level)
    
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = Path(f".env.{security_level.value}")
    
    # Backup existing file if it exists
    if output_path.exists():
        backup_path = output_path.with_suffix(f"{output_path.suffix}.backup")
        output_path.rename(backup_path)
        logger.info(f"Backed up existing file to {backup_path}")
    
    output_path.write_text(env_content)
    logger.info(f"Generated environment file: {output_path}")
    
    if security_level == SecurityLevel.PRODUCTION:
        logger.warning("IMPORTANT: Review and customize the generated file before using in production!")
        logger.warning("Ensure all secret values are properly secured!")


def check_production_readiness():
    """Check if configuration is production ready."""
    logger.info("Checking production readiness...")
    
    manager = get_security_config_manager()
    is_ready, errors = manager.validate_production_readiness()
    
    if is_ready:
        logger.info("✅ Configuration is production ready!")
        return True
    else:
        logger.error("❌ Configuration is NOT production ready:")
        for error in errors:
            logger.error(f"  - {error}")
        return False


def rotate_keys():
    """Generate new security keys."""
    logger.info("Generating new security keys...")
    
    import secrets
    
    new_jwt_secret = secrets.token_urlsafe(64)
    new_encryption_key = secrets.token_urlsafe(32)
    
    logger.info("New keys generated:")
    logger.info(f"JWT_SECRET={new_jwt_secret}")
    logger.info(f"ENCRYPTION_KEY={new_encryption_key}")
    
    logger.warning("IMPORTANT:")
    logger.warning("1. Update your environment variables with these new keys")
    logger.warning("2. Restart all application instances")
    logger.warning("3. Invalidate all existing JWT tokens")
    logger.warning("4. Re-encrypt data if using database encryption")


def audit_security():
    """Perform security audit of current configuration."""
    logger.info("Performing security audit...")
    
    manager = get_security_config_manager()
    config = manager.get_config()
    
    issues = []
    recommendations = []
    
    # Check authentication settings
    if config.authentication.access_token_expire_minutes > 30:
        issues.append("Access token expiration is longer than recommended (30 minutes)")
    
    if config.authentication.max_login_attempts > 5:
        issues.append("Max login attempts is higher than recommended (5)")
    
    if not config.authentication.password_require_special_chars:
        issues.append("Password policy should require special characters")
    
    # Check encryption settings
    if not config.encryption.encrypt_sensitive_data:
        issues.append("Sensitive data encryption is disabled")
    
    if config.encryption.key_rotation_days > 90:
        recommendations.append("Consider shorter key rotation period (90 days or less)")
    
    # Check rate limiting
    if not config.rate_limiting.enable_rate_limiting:
        issues.append("Rate limiting is disabled")
    
    if config.rate_limiting.default_requests_per_minute > 100:
        recommendations.append("Consider lower rate limits for better protection")
    
    # Check monitoring
    if not config.monitoring.enable_threat_detection:
        issues.append("Threat detection is disabled")
    
    if not config.monitoring.log_security_events:
        issues.append("Security event logging is disabled")
    
    # Check security headers
    if not config.enable_hsts:
        issues.append("HSTS is disabled")
    
    if not config.enable_csp:
        issues.append("Content Security Policy is disabled")
    
    # Report results
    if issues:
        logger.error("Security issues found:")
        for issue in issues:
            logger.error(f"  ❌ {issue}")
    
    if recommendations:
        logger.info("Security recommendations:")
        for rec in recommendations:
            logger.info(f"  💡 {rec}")
    
    if not issues and not recommendations:
        logger.info("✅ No security issues found!")
    
    return len(issues) == 0


def main():
    parser = argparse.ArgumentParser(description="Security configuration management tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate current configuration")
    
    # Generate env command
    gen_parser = subparsers.add_parser("generate-env", help="Generate example .env file")
    gen_parser.add_argument(
        "--level", 
        choices=["development", "testing", "staging", "production"],
        default="development",
        help="Security level"
    )
    gen_parser.add_argument(
        "--output", "-o",
        help="Output file path"
    )
    
    # Check production command
    prod_parser = subparsers.add_parser("check-production", help="Check production readiness")
    
    # Rotate keys command
    rotate_parser = subparsers.add_parser("rotate-keys", help="Generate new security keys")
    
    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Perform security audit")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "validate":
            return 0 if validate_config() else 1
        
        elif args.command == "generate-env":
            security_level = SecurityLevel(args.level)
            generate_env_file(security_level, args.output)
            return 0
        
        elif args.command == "check-production":
            return 0 if check_production_readiness() else 1
        
        elif args.command == "rotate-keys":
            rotate_keys()
            return 0
        
        elif args.command == "audit":
            return 0 if audit_security() else 1
        
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())