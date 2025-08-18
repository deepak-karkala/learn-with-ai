"""
Tests for security service.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.security_service import (
    SecurityService, SecurityEvent, ThreatLevel
)


@pytest.mark.external_deps
class TestSecurityService:
    """Test security service functionality."""
    
    @pytest.fixture
    def security_service(self):
        """Create security service for testing."""
        with patch('app.services.security_service.get_redis_service'), \
             patch('app.services.security_service.get_monitoring_service'):
            service = SecurityService()
            service._redis_service = Mock()
            service._monitoring_service = Mock()
            return service
    
    @pytest.mark.external_deps
    def test_data_encryption_and_decryption(self, security_service):
        """Test data encryption and decryption."""
        original_data = "This is sensitive data that needs encryption"
        
        # Encrypt data
        encrypted = security_service.encrypt_data(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, str)
        
        # Decrypt data
        decrypted = security_service.decrypt_data(encrypted)
        assert decrypted == original_data
    
    @pytest.mark.external_deps
    def test_encrypt_sensitive_fields(self, security_service):
        """Test encryption of sensitive fields in data."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password_hash": "hashed_password",
            "api_key": "secret_api_key",
            "public_info": "not sensitive"
        }
        
        encrypted_data = security_service.encrypt_sensitive_fields(data)
        
        # Non-sensitive fields should remain unchanged
        assert encrypted_data["name"] == "John Doe"
        assert encrypted_data["public_info"] == "not sensitive"
        
        # Sensitive fields should be encrypted
        assert encrypted_data["password_hash"] != "hashed_password"
        assert encrypted_data["api_key"] != "secret_api_key"
        
        # Decrypt and verify
        decrypted_data = security_service.decrypt_sensitive_fields(encrypted_data)
        assert decrypted_data == data
    
    @pytest.mark.external_deps
    def test_request_security_analysis_clean(self, security_service):
        """Test security analysis of clean request."""
        request_data = {
            "message": "Hello, how are you?",
            "user_agent": "Mozilla/5.0"
        }
        
        security_event = security_service.analyze_request_security(
            request_data=request_data,
            ip_address="127.0.0.1",
            user_id="user123"
        )
        
        assert isinstance(security_event, SecurityEvent)
        assert security_event.threat_level == ThreatLevel.LOW
        assert not security_event.blocked
        assert security_event.source_ip == "127.0.0.1"
        assert security_event.user_id == "user123"
    
    @pytest.mark.external_deps
    def test_request_security_analysis_malicious_content(self, security_service):
        """Test security analysis with malicious content."""
        request_data = {
            "message": "<script>alert('xss')</script>",
            "user_agent": "Mozilla/5.0"
        }
        
        security_event = security_service.analyze_request_security(
            request_data=request_data,
            ip_address="192.168.1.100",
            user_id="user123"
        )
        
        assert security_event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        assert security_event.blocked
        assert len(security_event.details["threats_detected"]) > 0
    
    @pytest.mark.external_deps
    def test_content_threat_detection(self, security_service):
        """Test content threat detection."""
        # XSS attempt
        xss_data = {"input": "<script>alert('xss')</script>"}
        threats = security_service._analyze_content_threats(xss_data)
        assert len(threats) > 0
        assert any("xss" in threat.lower() for threat in threats)
        
        # SQL injection attempt
        sql_data = {"query": "'; DROP TABLE users; --"}
        threats = security_service._analyze_content_threats(sql_data)
        assert len(threats) > 0
        assert any("sql" in threat.lower() for threat in threats)
        
        # Command injection attempt
        cmd_data = {"command": "rm -rf /"}
        threats = security_service._analyze_content_threats(cmd_data)
        assert len(threats) > 0
        
        # Clean content
        clean_data = {"message": "Hello, world!"}
        threats = security_service._analyze_content_threats(clean_data)
        assert len(threats) == 0
    
    @pytest.mark.external_deps
    def test_ip_reputation_checking(self, security_service):
        """Test IP reputation checking."""
        # Test with known good IP
        good_ip = "8.8.8.8"
        threats = security_service._check_ip_reputation(good_ip)
        assert isinstance(threats, list)
        
        # Test with localhost
        localhost = "127.0.0.1"
        threats = security_service._check_ip_reputation(localhost)
        assert isinstance(threats, list)
        
        # Test with private IP
        private_ip = "192.168.1.1"
        threats = security_service._check_ip_reputation(private_ip)
        assert isinstance(threats, list)
    
    @pytest.mark.external_deps
    def test_rate_limiting_check(self, security_service):
        """Test rate limiting functionality."""
        security_service._redis_service.is_available.return_value = True
        security_service._redis_service.get_cache.return_value = None
        
        ip_address = "127.0.0.1"
        user_id = "user123"
        
        # First request should pass
        result = security_service._check_rate_limiting(ip_address, user_id)
        assert result is None or "rate_limit" not in result.lower()
        
        # Simulate multiple rapid requests
        security_service._redis_service.get_cache.return_value = 100  # High count
        result = security_service._check_rate_limiting(ip_address, user_id)
        assert result is not None
        assert "rate" in result.lower()
    
    @pytest.mark.external_deps
    def test_api_key_generation(self, security_service):
        """Test API key generation."""
        user_id = "user123"
        
        result = security_service.generate_api_key(user_id)
        
        assert "api_key" in result
        assert "secret" in result
        assert len(result["api_key"]) > 10
        assert len(result["secret"]) > 10
        assert result["api_key"] != result["secret"]
    
    @pytest.mark.external_deps
    def test_api_key_verification(self, security_service):
        """Test API key verification."""
        user_id = "user123"
        
        # Generate API key
        result = security_service.generate_api_key(user_id)
        api_key = result["api_key"]
        secret = result["secret"]
        
        # Mock storage
        security_service._get_stored_api_key = Mock(return_value={
            "user_id": user_id,
            "secret_hash": security_service._hash_api_secret(secret),
            "is_active": True
        })
        
        # Verify correct key and secret
        verification = security_service.verify_api_key(api_key, secret)
        assert verification is not None
        assert verification["user_id"] == user_id
        
        # Verify incorrect secret
        verification = security_service.verify_api_key(api_key, "wrong_secret")
        assert verification is None
    
    @pytest.mark.external_deps
    def test_ip_blocking_and_whitelisting(self, security_service):
        """Test IP blocking and whitelisting functionality."""
        ip_address = "192.168.1.100"
        
        # Initially not blocked
        assert not security_service.is_ip_blocked(ip_address)
        
        # Block IP
        security_service.block_ip(ip_address, duration_hours=1)
        assert security_service.is_ip_blocked(ip_address)
        
        # Whitelist IP (should override block)
        security_service.whitelist_ip(ip_address, duration_hours=2)
        assert not security_service.is_ip_blocked(ip_address)
        
        # Remove from whitelist
        security_service.remove_ip_whitelist(ip_address)
        # Should be blocked again since block is still active
        assert security_service.is_ip_blocked(ip_address)
    
    @pytest.mark.external_deps
    def test_request_blocking_logic(self, security_service):
        """Test overall request blocking logic."""
        # Mock IP blocking
        security_service.is_ip_blocked = Mock(return_value=False)
        security_service.is_ip_whitelisted = Mock(return_value=False)
        
        ip_address = "192.168.1.100"
        
        # Normal request should not be blocked
        assert not security_service.is_request_blocked(ip_address)
        
        # Blocked IP should be blocked
        security_service.is_ip_blocked.return_value = True
        assert security_service.is_request_blocked(ip_address)
        
        # Whitelisted IP should not be blocked even if on blocklist
        security_service.is_ip_whitelisted.return_value = True
        assert not security_service.is_request_blocked(ip_address)
    
    @pytest.mark.external_deps
    def test_security_metrics_collection(self, security_service):
        """Test security metrics collection."""
        security_service._redis_service.is_available.return_value = True
        security_service._redis_service.get_cache.return_value = None
        
        metrics = security_service.get_security_metrics()
        
        assert isinstance(metrics, dict)
        assert "blocked_requests" in metrics
        assert "threat_detections" in metrics
        assert "api_key_usage" in metrics
        assert "ip_blocks" in metrics
    
    @pytest.mark.external_deps
    def test_security_event_logging(self, security_service):
        """Test security event logging."""
        security_service._redis_service.is_available.return_value = True
        security_service._redis_service.set_cache = Mock()
        security_service._monitoring_service.track_error = Mock()
        
        event = SecurityEvent(
            event_id="test123",
            event_type="test_threat",
            threat_level=ThreatLevel.HIGH,
            source_ip="192.168.1.100",
            user_id="user123",
            timestamp=datetime.utcnow(),
            details={"test": "data"},
            blocked=True
        )
        
        security_service._log_security_event(event)
        
        # Should store in Redis
        security_service._redis_service.set_cache.assert_called()
        
        # Should send to monitoring for high threats
        security_service._monitoring_service.track_error.assert_called()
    
    @pytest.mark.external_deps
    def test_hash_functions(self, security_service):
        """Test hashing functions."""
        data = "test_data_to_hash"
        
        # Test SHA-256 hashing
        hash1 = security_service._hash_sha256(data)
        hash2 = security_service._hash_sha256(data)
        
        assert hash1 == hash2  # Same input should produce same hash
        assert len(hash1) == 64  # SHA-256 produces 64-character hex string
        
        # Test HMAC hashing
        secret = "test_secret"
        hmac1 = security_service._hash_hmac(data, secret)
        hmac2 = security_service._hash_hmac(data, secret)
        
        assert hmac1 == hmac2  # Same input and secret should produce same HMAC
        assert hmac1 != hash1  # HMAC should be different from plain hash
    
    @pytest.mark.external_deps
    def test_pii_detection(self, security_service):
        """Test PII detection in data."""
        # Data with PII
        pii_data = {
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "ssn": "123-45-6789",
            "name": "John Doe"
        }
        
        detected_pii = security_service.detect_pii(pii_data)
        
        assert "email" in detected_pii
        assert "phone" in detected_pii
        assert "ssn" in detected_pii
        
        # Data without PII
        clean_data = {
            "message": "Hello world",
            "count": 42,
            "active": True
        }
        
        detected_pii = security_service.detect_pii(clean_data)
        assert len(detected_pii) == 0
    
    @pytest.mark.external_deps
    def test_threat_level_escalation(self, security_service):
        """Test threat level escalation logic."""
        # Multiple low threats should escalate
        threats = ["suspicious_pattern", "unusual_timing", "high_frequency"]
        level = security_service._calculate_threat_level(threats)
        assert level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]
        
        # Single critical threat
        critical_threats = ["sql_injection"]
        level = security_service._calculate_threat_level(critical_threats)
        assert level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        
        # No threats
        no_threats = []
        level = security_service._calculate_threat_level(no_threats)
        assert level == ThreatLevel.LOW
    
    @pytest.mark.external_deps
    def test_data_sanitization(self, security_service):
        """Test data sanitization functions."""
        # Test HTML sanitization
        dirty_html = "<script>alert('xss')</script><p>Safe content</p>"
        clean_html = security_service.sanitize_html(dirty_html)
        assert "<script>" not in clean_html
        assert "Safe content" in clean_html
        
        # Test SQL input sanitization
        sql_input = "'; DROP TABLE users; --"
        clean_sql = security_service.sanitize_sql_input(sql_input)
        assert "DROP TABLE" not in clean_sql
        
        # Test general string sanitization
        dirty_string = "normal text <script>evil()</script> more text"
        clean_string = security_service.sanitize_string(dirty_string)
        assert "<script>" not in clean_string
        assert "normal text" in clean_string
    
    @pytest.mark.external_deps
    def test_session_security(self, security_service):
        """Test session security features."""
        user_id = "user123"
        session_id = "session456"
        ip_address = "192.168.1.100"
        
        # Validate session
        security_service._validate_session_security = Mock(return_value=True)
        is_valid = security_service.validate_session_security(
            user_id, session_id, ip_address
        )
        assert is_valid
        
        # Test session hijacking detection
        security_service._detect_session_hijacking = Mock(return_value=False)
        is_hijacked = security_service.detect_session_hijacking(
            session_id, ip_address, "Mozilla/5.0"
        )
        assert not is_hijacked
    
    @pytest.mark.external_deps
    def test_anomaly_detection(self, security_service):
        """Test anomaly detection in user behavior."""
        user_id = "user123"
        
        # Normal behavior pattern
        normal_activity = {
            "login_time": "09:00",
            "location": "usual_city",
            "device": "regular_device"
        }
        
        anomalies = security_service.detect_anomalies(user_id, normal_activity)
        assert len(anomalies) == 0
        
        # Suspicious behavior pattern
        suspicious_activity = {
            "login_time": "03:00",  # Unusual time
            "location": "foreign_country",  # Unusual location
            "device": "unknown_device"  # New device
        }
        
        security_service._get_user_behavior_baseline = Mock(return_value={
            "usual_login_hours": [8, 9, 10, 17, 18, 19],
            "usual_locations": ["usual_city"],
            "known_devices": ["regular_device"]
        })
        
        anomalies = security_service.detect_anomalies(user_id, suspicious_activity)
        assert len(anomalies) > 0