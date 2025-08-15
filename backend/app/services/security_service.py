"""
Security service for threat detection, encryption, and security monitoring.
"""

import hashlib
import hmac
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import json
import os
import time
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import ipaddress

from ..services.redis_service import get_redis_service
from ..services.monitoring_service import get_monitoring_service
from ..services.performance_service import monitor_performance

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Security threat levels."""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_id: str
    event_type: str
    threat_level: ThreatLevel
    source_ip: str
    user_id: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]
    blocked: bool = False


class SecurityService:
    """Service for security threat detection, encryption, and monitoring."""
    
    def __init__(self):
        self._redis_service = get_redis_service()
        self._monitoring_service = get_monitoring_service()
        
        # Security configuration
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher_suite = Fernet(self._encryption_key)
        
        # Threat detection patterns
        self._malicious_patterns = {
            'sql_injection': [
                r"(?i)(union|select|insert|update|delete|drop|create|alter)\s+",
                r"(?i)(or|and)\s+\d+\s*[=><]",
                r"(?i)'\s*(or|and)\s+'.*'",
                r"(?i);.*--",
                r"(?i)/\*.*\*/"
            ],
            'xss_patterns': [
                r"(?i)<script[^>]*>.*?</script>",
                r"(?i)javascript:",
                r"(?i)on\w+\s*=",
                r"(?i)<iframe[^>]*>",
                r"(?i)eval\s*\(",
                r"(?i)document\.(cookie|domain)"
            ],
            'command_injection': [
                r"(?i)(;|&&|\|\|)\s*(cat|ls|pwd|whoami|id)",
                r"(?i)\$\(.*\)",
                r"(?i)`.*`",
                r"(?i)>\s*/",
                r"(?i)<\s*/"
            ],
            'path_traversal': [
                r"\.{2}[/\\]",
                r"(?i)(etc|passwd|shadow|hosts)",
                r"(?i)c:\\windows",
                r"(?i)/proc/",
                r"(?i)\.\.%2f"
            ]
        }
        
        # Rate limiting thresholds for different threat levels
        self._threat_thresholds = {
            ThreatLevel.LOW: {"count": 10, "window": 300},      # 10 events in 5 minutes
            ThreatLevel.MEDIUM: {"count": 5, "window": 300},    # 5 events in 5 minutes
            ThreatLevel.HIGH: {"count": 3, "window": 180},      # 3 events in 3 minutes
            ThreatLevel.CRITICAL: {"count": 1, "window": 60}    # 1 event in 1 minute
        }
        
        # Known malicious IP ranges (example)
        self._blocked_ip_ranges = [
            # Add known malicious IP ranges
            # ipaddress.ip_network("192.0.2.0/24"),  # Example
        ]
        
        logger.info("Security service initialized")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for data encryption."""
        key_env = os.getenv("ENCRYPTION_KEY")
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env)
            except Exception:
                logger.warning("Invalid ENCRYPTION_KEY format, generating new key")
        
        # Generate new key
        key = Fernet.generate_key()
        logger.warning(f"Generated new encryption key. Set ENCRYPTION_KEY={key.decode()} in environment")
        return key
    
    # =============================================================================
    # Threat Detection
    # =============================================================================
    
    @monitor_performance("security_request_analysis", "security_analysis_result")
    def analyze_request_security(
        self,
        request_data: Dict[str, Any],
        ip_address: str,
        user_id: Optional[str] = None
    ) -> SecurityEvent:
        """Analyze incoming request for security threats."""
        try:
            event_id = secrets.token_hex(8)
            threat_level = ThreatLevel.LOW
            threats_detected = []
            
            # Check IP reputation
            ip_threats = self._check_ip_reputation(ip_address)
            if ip_threats:
                threats_detected.extend(ip_threats)
                threat_level = max(threat_level, ThreatLevel.MEDIUM, key=lambda x: list(ThreatLevel).index(x))
            
            # Analyze request content for malicious patterns
            content_threats = self._analyze_content_threats(request_data)
            if content_threats:
                threats_detected.extend(content_threats)
                threat_level = max(threat_level, ThreatLevel.HIGH, key=lambda x: list(ThreatLevel).index(x))
            
            # Check rate limiting
            rate_limit_violation = self._check_rate_limiting(ip_address, user_id)
            if rate_limit_violation:
                threats_detected.append(rate_limit_violation)
                threat_level = max(threat_level, ThreatLevel.MEDIUM, key=lambda x: list(ThreatLevel).index(x))
            
            # Create security event
            security_event = SecurityEvent(
                event_id=event_id,
                event_type="request_analysis",
                threat_level=threat_level,
                source_ip=ip_address,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                details={
                    "threats_detected": threats_detected,
                    "request_size": len(str(request_data)),
                    "user_agent": request_data.get("user_agent", ""),
                },
                blocked=threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
            )
            
            # Log and store security event
            self._log_security_event(security_event)
            
            # Update threat metrics
            self._update_threat_metrics(security_event)
            
            return security_event
            
        except Exception as e:
            logger.error(f"Error analyzing request security: {e}")
            # Return safe default
            return SecurityEvent(
                event_id=secrets.token_hex(8),
                event_type="analysis_error",
                threat_level=ThreatLevel.LOW,
                source_ip=ip_address,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                details={"error": str(e)},
                blocked=False
            )
    
    def _check_ip_reputation(self, ip_address: str) -> List[str]:
        """Check IP address against known threat databases."""
        threats = []
        
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            # Check against blocked IP ranges
            for blocked_range in self._blocked_ip_ranges:
                if ip_obj in blocked_range:
                    threats.append(f"IP in blocked range: {blocked_range}")
            
            # Check Redis blacklist
            if self._redis_service.is_available():
                blacklist_key = f"ip_blacklist:{ip_address}"
                if self._redis_service.cache_exists(blacklist_key):
                    threats.append("IP in blacklist")
            
            # Check for suspicious activity patterns
            suspicious_activity = self._check_suspicious_ip_activity(ip_address)
            if suspicious_activity:
                threats.extend(suspicious_activity)
                
        except ValueError:
            threats.append("Invalid IP address format")
        
        return threats
    
    def _analyze_content_threats(self, request_data: Dict[str, Any]) -> List[str]:
        """Analyze request content for malicious patterns."""
        threats = []
        
        # Convert all request data to string for analysis
        content = json.dumps(request_data, default=str).lower()
        
        for threat_type, patterns in self._malicious_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    threats.append(f"{threat_type}: {pattern}")
        
        # Check for excessive payload size
        if len(content) > 50000:  # 50KB limit
            threats.append("Excessive payload size")
        
        # Check for suspicious file uploads
        if self._check_file_upload_threats(request_data):
            threats.append("Suspicious file upload detected")
        
        return threats
    
    def _check_file_upload_threats(self, request_data: Dict[str, Any]) -> bool:
        """Check for malicious file uploads."""
        # Look for file-related fields
        file_fields = ['file', 'upload', 'image', 'document']
        
        for field in file_fields:
            if field in request_data:
                file_data = request_data[field]
                
                # Check file extension
                if isinstance(file_data, dict) and 'filename' in file_data:
                    filename = file_data['filename'].lower()
                    dangerous_extensions = ['.exe', '.bat', '.sh', '.ps1', '.php', '.jsp']
                    if any(filename.endswith(ext) for ext in dangerous_extensions):
                        return True
                
                # Check file content (basic)
                if isinstance(file_data, str) and len(file_data) > 1000:
                    # Look for script tags or suspicious content
                    if '<script' in file_data.lower() or '<?php' in file_data.lower():
                        return True
        
        return False
    
    def _check_suspicious_ip_activity(self, ip_address: str) -> List[str]:
        """Check for suspicious activity patterns from IP."""
        threats = []
        
        if not self._redis_service.is_available():
            return threats
        
        # Check request frequency
        request_count_key = f"ip_requests:{ip_address}:1h"
        request_count = self._redis_service.get_cache(request_count_key) or 0
        
        if request_count > 1000:  # More than 1000 requests per hour
            threats.append(f"High request frequency: {request_count}/hour")
        
        # Check failed authentication attempts
        failed_auth_key = f"ip_failed_auth:{ip_address}:1h"
        failed_auth_count = self._redis_service.get_cache(failed_auth_key) or 0
        
        if failed_auth_count > 10:  # More than 10 failed auth attempts per hour
            threats.append(f"Multiple failed authentication attempts: {failed_auth_count}")
        
        return threats
    
    def _check_rate_limiting(
        self,
        ip_address: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Check if request violates rate limiting rules."""
        if not self._redis_service.is_available():
            return None
        
        current_time = int(time.time())
        
        # IP-based rate limiting
        ip_key = f"rate_limit:ip:{ip_address}"
        ip_requests = self._redis_service.get_cache(ip_key) or []
        
        # Clean old requests (outside 5-minute window)
        recent_requests = [req for req in ip_requests if current_time - req < 300]
        
        if len(recent_requests) > 60:  # More than 60 requests in 5 minutes
            return f"IP rate limit exceeded: {len(recent_requests)} requests"
        
        # Update request log
        recent_requests.append(current_time)
        self._redis_service.set_cache(ip_key, recent_requests[-100:], ttl_seconds=300)
        
        # User-based rate limiting (if authenticated)
        if user_id:
            user_key = f"rate_limit:user:{user_id}"
            user_requests = self._redis_service.get_cache(user_key) or []
            
            # Clean old requests
            recent_user_requests = [req for req in user_requests if current_time - req < 300]
            
            if len(recent_user_requests) > 100:  # More than 100 requests in 5 minutes for authenticated users
                return f"User rate limit exceeded: {len(recent_user_requests)} requests"
            
            # Update user request log
            recent_user_requests.append(current_time)
            self._redis_service.set_cache(user_key, recent_user_requests[-200:], ttl_seconds=300)
        
        return None
    
    # =============================================================================
    # Data Encryption and Security
    # =============================================================================
    
    @monitor_performance("security_encryption", "encrypted_data")
    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet encryption."""
        try:
            encrypted_data = self._cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data using Fernet encryption."""
        return self.encrypt_data(data)
    
    @monitor_performance("security_decryption", "decrypted_data")
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet decryption."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.decrypt_data(encrypted_data)
    
    def hash_data(self, data: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash data with salt for secure storage."""
        if not salt:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for key derivation
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        hashed = base64.urlsafe_b64encode(kdf.derive(data.encode())).decode()
        return hashed, salt
    
    def verify_hash(self, data: str, hashed: str, salt: str) -> bool:
        """Verify data against hash."""
        try:
            computed_hash, _ = self.hash_data(data, salt)
            return hmac.compare_digest(hashed, computed_hash)
        except Exception as e:
            logger.error(f"Hash verification error: {e}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self, user_id: str) -> Dict[str, str]:
        """Generate API key for user."""
        api_key = f"ask_{secrets.token_urlsafe(32)}"
        secret = secrets.token_urlsafe(64)
        
        # Hash the secret for storage
        hashed_secret, salt = self.hash_data(secret)
        
        # Store API key info in Redis
        if self._redis_service.is_available():
            api_key_data = {
                "user_id": user_id,
                "hashed_secret": hashed_secret,
                "salt": salt,
                "created_at": datetime.utcnow().isoformat(),
                "last_used": None,
                "is_active": True
            }
            self._redis_service.set_cache(f"api_key:{api_key}", api_key_data)
        
        return {
            "api_key": api_key,
            "secret": secret  # Only returned once
        }
    
    def encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in data dictionary."""
        sensitive_fields = ["password_hash", "api_key", "api_keys", "tokens", "pii_data", "secret"]
        result = data.copy()
        
        for field in sensitive_fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.encrypt_data(result[field])
        
        return result
    
    def decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in data dictionary."""
        sensitive_fields = ["password_hash", "api_key", "api_keys", "tokens", "pii_data", "secret"]
        result = data.copy()
        
        for field in sensitive_fields:
            if field in result and isinstance(result[field], str):
                try:
                    result[field] = self.decrypt_data(result[field])
                except Exception:
                    # If decryption fails, field might not be encrypted
                    pass
        
        return result
    
    def _hash_api_secret(self, secret: str) -> str:
        """Hash API secret for storage."""
        hashed, _ = self.hash_data(secret)
        return hashed
    
    def block_ip(self, ip_address: str, duration_hours: int = 1):
        """Block IP address."""
        self.blacklist_ip(ip_address, duration_hours)
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked."""
        return self.is_request_blocked(ip_address)
    
    def remove_ip_whitelist(self, ip_address: str):
        """Remove IP from whitelist."""
        if self._redis_service.is_available():
            self._redis_service.delete_cache(f"ip_whitelist:{ip_address}")
    
    def _hash_sha256(self, data: str) -> str:
        """Hash data using SHA256."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _hash_hmac(self, data: str, secret: str) -> str:
        """Create HMAC hash of data."""
        return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    
    def detect_pii(self, data: str) -> List[str]:
        """Detect personally identifiable information in text."""
        pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', 'ssn'),  # SSN
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email'),  # Email
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'credit_card'),  # Credit card
            (r'\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b', 'phone'),  # Phone number
        ]
        
        detected = []
        for pattern, pii_type in pii_patterns:
            if re.search(pattern, data):
                detected.append(pii_type)
        
        return detected
    
    def _calculate_threat_level(self, threats: List[str]) -> ThreatLevel:
        """Calculate threat level based on detected threats."""
        if not threats:
            return ThreatLevel.LOW
        
        critical_keywords = ['sql injection', 'command injection', 'xss', 'critical']
        high_keywords = ['malicious', 'suspicious', 'blocked']
        
        threat_text = ' '.join(threats).lower()
        
        if any(keyword in threat_text for keyword in critical_keywords):
            return ThreatLevel.CRITICAL
        elif any(keyword in threat_text for keyword in high_keywords):
            return ThreatLevel.HIGH
        elif len(threats) > 3:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML input."""
        # Basic HTML sanitization - remove script tags and dangerous attributes
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        html = re.sub(r'javascript:', '', html, flags=re.IGNORECASE)
        return html
    
    def sanitize_sql_input(self, sql_input: str) -> str:
        """Sanitize SQL input."""
        # Basic SQL injection protection
        dangerous_patterns = [
            r';.*--', r"'.*OR.*'", r'".*OR.*"', r'UNION.*SELECT', 
            r'DROP.*TABLE', r'DELETE.*FROM', r'INSERT.*INTO'
        ]
        
        for pattern in dangerous_patterns:
            sql_input = re.sub(pattern, '', sql_input, flags=re.IGNORECASE)
        
        return sql_input.strip()
    
    def sanitize_string(self, input_string: str) -> str:
        """Sanitize general string input."""
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_string)
        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        return sanitized
    
    def validate_session_security(self, session_data: Dict[str, Any]) -> bool:
        """Validate session security."""
        required_fields = ['user_id', 'created_at', 'ip_address']
        
        # Check required fields
        for field in required_fields:
            if field not in session_data:
                return False
        
        # Check session age
        try:
            created_at = datetime.fromisoformat(session_data['created_at'])
            session_age = (datetime.utcnow() - created_at).total_seconds()
            if session_age > 24 * 3600:  # 24 hours
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def detect_session_hijacking(self, session_data: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """Detect potential session hijacking."""
        # Check IP consistency
        session_ip = session_data.get('ip_address')
        request_ip = request_data.get('ip_address')
        
        if session_ip and request_ip and session_ip != request_ip:
            # Allow some IP changes for mobile users
            if not self._is_same_network(session_ip, request_ip):
                return True
        
        # Check user agent consistency
        session_ua = session_data.get('user_agent', '')
        request_ua = request_data.get('user_agent', '')
        
        if session_ua and request_ua and session_ua != request_ua:
            return True
        
        return False
    
    def _is_same_network(self, ip1: str, ip2: str) -> bool:
        """Check if two IPs are in the same network."""
        try:
            addr1 = ipaddress.ip_address(ip1)
            addr2 = ipaddress.ip_address(ip2)
            
            # Same IP
            if addr1 == addr2:
                return True
            
            # Check if both are in same private network ranges
            private_ranges = [
                ipaddress.ip_network('10.0.0.0/8'),
                ipaddress.ip_network('172.16.0.0/12'),
                ipaddress.ip_network('192.168.0.0/16'),
            ]
            
            for network in private_ranges:
                if addr1 in network and addr2 in network:
                    return True
            
            return False
        except ValueError:
            return False
    
    def detect_anomalies(self, user_id: str, activity_data: Dict[str, Any]) -> List[str]:
        """Detect anomalous user activity."""
        anomalies = []
        
        # Check request frequency
        request_count = activity_data.get('request_count', 0)
        if request_count > 1000:  # More than 1000 requests
            anomalies.append('high_request_frequency')
        
        # Check geographic anomalies
        current_location = activity_data.get('location')
        if current_location:
            # This is a simplified check - in practice you'd compare with historical data
            unusual_countries = ['TOR', 'VPN', 'PROXY']
            if any(country in current_location.upper() for country in unusual_countries):
                anomalies.append('unusual_location')
        
        # Check time-based anomalies
        access_time = activity_data.get('access_time')
        if access_time:
            try:
                access_dt = datetime.fromisoformat(access_time)
                hour = access_dt.hour
                if hour < 6 or hour > 22:  # Outside normal hours
                    anomalies.append('unusual_access_time')
            except ValueError:
                pass
        
        return anomalies
    
    def verify_api_key(self, api_key: str, secret: str) -> Optional[Dict[str, Any]]:
        """Verify API key and secret."""
        if not self._redis_service.is_available():
            return None
        
        api_key_data = self._redis_service.get_cache(f"api_key:{api_key}")
        if not api_key_data or not api_key_data.get("is_active"):
            return None
        
        # Verify secret
        if not self.verify_hash(secret, api_key_data["hashed_secret"], api_key_data["salt"]):
            return None
        
        # Update last used timestamp
        api_key_data["last_used"] = datetime.utcnow().isoformat()
        self._redis_service.set_cache(f"api_key:{api_key}", api_key_data)
        
        return api_key_data
    
    # =============================================================================
    # Security Monitoring and Logging
    # =============================================================================
    
    def _log_security_event(self, event: SecurityEvent):
        """Log security event for audit and monitoring."""
        try:
            # Convert to dict for logging
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "threat_level": event.threat_level.value,
                "source_ip": event.source_ip,
                "user_id": event.user_id,
                "timestamp": event.timestamp.isoformat(),
                "details": event.details,
                "blocked": event.blocked
            }
            
            # Use comprehensive security audit logging
            from ..services.logging_service import log_threat_detection, log_security_event
            
            if event.threat_level != ThreatLevel.LOW:
                # Log as threat detection for medium and above threats
                log_threat_detection(
                    threat_type=event.event_type,
                    threat_level=event.threat_level.value,
                    details=event.details,
                    ip_address=event.source_ip,
                    user_id=event.user_id,
                    action_taken="blocked" if event.blocked else "monitored"
                )
            else:
                # Log as general security event for low-level events
                log_security_event(
                    event_type="security_monitoring",
                    event_subtype=event.event_type,
                    severity=event.threat_level.value,
                    details=event.details,
                    user_id=event.user_id,
                    ip_address=event.source_ip
                )
            
            # Also log to application logger for backward compatibility
            logger.warning(f"Security event: {event.event_type}", extra=event_data)
            
            # Store in Redis for immediate access
            if self._redis_service.is_available():
                key = f"security_event:{event.event_id}"
                self._redis_service.set_cache(key, event_data, ttl_seconds=3600 * 24 * 7)  # 7 days
                
                # Add to recent events list
                recent_events_key = "security_events:recent"
                recent_events = self._redis_service.get_cache(recent_events_key) or []
                recent_events.append(event.event_id)
                recent_events = recent_events[-100:]  # Keep last 100 events
                self._redis_service.set_cache(recent_events_key, recent_events, ttl_seconds=3600 * 24)
            
            # Send to monitoring service
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self._monitoring_service.track_error(
                    error=Exception(f"Security threat detected: {event.event_type}"),
                    context="security_service",
                    metadata={
                        "threat_level": event.threat_level.value,
                        "source_ip": event.source_ip,
                        "blocked": event.blocked
                    }
                )
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def _update_threat_metrics(self, event: SecurityEvent):
        """Update threat metrics for monitoring."""
        if not self._redis_service.is_available():
            return
        
        try:
            # Update threat level counters
            threat_key = f"threats:{event.threat_level.value}:1h"
            current_count = self._redis_service.get_cache(threat_key) or 0
            self._redis_service.set_cache(threat_key, current_count + 1, ttl_seconds=3600)
            
            # Update IP-specific threat counter
            ip_threat_key = f"ip_threats:{event.source_ip}:24h"
            ip_threats = self._redis_service.get_cache(ip_threat_key) or 0
            self._redis_service.set_cache(ip_threat_key, ip_threats + 1, ttl_seconds=3600 * 24)
            
            # Check if IP should be temporarily blocked
            if ip_threats > 10:  # More than 10 threats in 24 hours
                self._redis_service.set_cache(f"ip_blacklist:{event.source_ip}", True, ttl_seconds=3600)
                logger.warning(f"IP {event.source_ip} temporarily blacklisted due to multiple threats")
            
        except Exception as e:
            logger.error(f"Error updating threat metrics: {e}")
    
    def get_security_metrics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get security metrics for the specified time range."""
        if not self._redis_service.is_available():
            return {"error": "Redis not available"}
        
        try:
            metrics = {}
            
            # Get threat counts by level
            for threat_level in ThreatLevel:
                key = f"threats:{threat_level.value}:{time_range_hours}h"
                count = self._redis_service.get_cache(key) or 0
                metrics[f"{threat_level.value}_threats"] = count
            
            # Get recent security events
            recent_events_key = "security_events:recent"
            recent_event_ids = self._redis_service.get_cache(recent_events_key) or []
            
            recent_events = []
            for event_id in recent_event_ids[-10:]:  # Last 10 events
                event_data = self._redis_service.get_cache(f"security_event:{event_id}")
                if event_data:
                    recent_events.append(event_data)
            
            metrics["recent_events"] = recent_events
            metrics["total_events"] = len(recent_event_ids)
            
            # Get blocked IPs count
            blocked_ips = 0
            for key in self._redis_service.get_client().keys("ip_blacklist:*") if self._redis_service.get_client() else []:
                blocked_ips += 1
            
            metrics["blocked_ips"] = blocked_ips
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting security metrics: {e}")
            return {"error": str(e)}
    
    def is_request_blocked(self, ip_address: str) -> bool:
        """Check if request should be blocked based on IP."""
        if not self._redis_service.is_available():
            return False
        
        return self._redis_service.cache_exists(f"ip_blacklist:{ip_address}")
    
    def whitelist_ip(self, ip_address: str, duration_hours: int = 24):
        """Add IP to whitelist temporarily."""
        if self._redis_service.is_available():
            self._redis_service.set_cache(
                f"ip_whitelist:{ip_address}",
                True,
                ttl_seconds=duration_hours * 3600
            )
            # Remove from blacklist if exists
            self._redis_service.delete_cache(f"ip_blacklist:{ip_address}")
    
    def blacklist_ip(self, ip_address: str, duration_hours: int = 1):
        """Add IP to blacklist temporarily."""
        if self._redis_service.is_available():
            self._redis_service.set_cache(
                f"ip_blacklist:{ip_address}",
                True,
                ttl_seconds=duration_hours * 3600
            )
            logger.warning(f"IP {ip_address} blacklisted for {duration_hours} hours")


# Global security service instance
_security_service: Optional[SecurityService] = None


def get_security_service() -> SecurityService:
    """Get the global security service instance."""
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service


def init_security_service() -> None:
    """Initialize security service."""
    global _security_service
    _security_service = SecurityService()
    logger.info("Security service initialized")