"""
Basic monitoring tests that don't require external dependencies.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.monitoring_service import get_monitoring_service, init_monitoring
from app.services.alerting_service import get_alerting_service, init_alerting, AlertType, AlertLevel
from app.services.analytics_service import get_analytics_service, init_analytics
from app.services.logging_service import get_log_service, init_logging


class TestBasicMonitoring:
    """Test basic monitoring functionality without external dependencies."""
    
    def test_monitoring_service_initialization(self):
        """Test monitoring service initializes correctly."""
        init_monitoring()
        monitoring = get_monitoring_service()
        assert monitoring is not None
        
        # Test basic methods exist
        assert hasattr(monitoring, 'is_enabled')
        assert hasattr(monitoring, 'track_llm_call')
        assert hasattr(monitoring, 'track_error')
        assert hasattr(monitoring, 'track_chat_interaction')
        assert hasattr(monitoring, 'get_system_metrics')
    
    def test_monitoring_service_disabled_without_dependencies(self):
        """Test monitoring service handles missing dependencies gracefully."""
        init_monitoring()
        monitoring = get_monitoring_service()
        
        # Should not crash even if psutil/opik are not available
        system_metrics = monitoring.get_system_metrics()
        assert isinstance(system_metrics, dict)
        assert "timestamp" in system_metrics
    
    def test_alerting_service_initialization(self):
        """Test alerting service initializes correctly."""
        init_alerting()
        alerting = get_alerting_service()
        assert alerting is not None
        
        # Test basic methods exist
        assert hasattr(alerting, 'create_alert')
        assert hasattr(alerting, 'resolve_alert')
        assert hasattr(alerting, 'get_active_alerts')
        assert hasattr(alerting, 'check_performance_thresholds')
    
    def test_alerting_basic_functionality(self):
        """Test basic alerting functionality."""
        init_alerting()
        alerting = get_alerting_service()
        
        # Create a test alert (without sending email)
        alert_id = alerting.create_alert(
            alert_type=AlertType.HIGH_ERROR_RATE,
            level=AlertLevel.WARNING,
            title="Test Alert",
            message="This is a test alert",
            metadata={"test": True},
            auto_send=False  # Don't send email in tests
        )
        
        assert alert_id != ""
        
        # Get active alerts
        active_alerts = alerting.get_active_alerts()
        assert len(active_alerts) > 0
        
        # Resolve the alert
        success = alerting.resolve_alert(alert_id, "Test resolution")
        assert success
        
        # Verify alert is resolved
        active_alerts_after = alerting.get_active_alerts()
        assert len(active_alerts_after) < len(active_alerts)
    
    def test_analytics_service_initialization(self):
        """Test analytics service initializes correctly."""
        init_analytics()
        analytics = get_analytics_service()
        assert analytics is not None
        
        # Test basic methods exist
        assert hasattr(analytics, 'start_session')
        assert hasattr(analytics, 'track_chat_interaction')
        assert hasattr(analytics, 'end_session')
        assert hasattr(analytics, 'get_user_analytics')
    
    def test_analytics_basic_functionality(self):
        """Test basic analytics functionality."""
        init_analytics()
        analytics = get_analytics_service()
        
        # Start session
        analytics.start_session("test_user", "test_session")
        
        # Track interaction
        analytics.track_chat_interaction(
            user_id="test_user",
            session_id="test_session",
            user_message="Hello",
            ai_response="Hi there!",
            response_time=1.0
        )
        
        # End session
        analytics.end_session("test_session")
        
        # Get analytics
        user_analytics = analytics.get_user_analytics("test_user")
        assert user_analytics is not None
        assert user_analytics["total_sessions"] == 1
        assert user_analytics["total_messages"] == 1
    
    def test_logging_service_initialization(self):
        """Test logging service initializes correctly."""
        init_logging()
        log_service = get_log_service()
        assert log_service is not None
        
        # Test basic methods exist
        assert hasattr(log_service, 'add_log_entry')
        assert hasattr(log_service, 'get_log_summary')
        assert hasattr(log_service, 'search_logs')
    
    def test_logging_basic_functionality(self):
        """Test basic logging functionality."""
        init_logging()
        log_service = get_log_service()
        
        # Add log entry
        log_service.add_log_entry({
            "level": "INFO",
            "logger": "test.logger",
            "message": "Test log message",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Get log summary
        summary = log_service.get_log_summary(hours=1)
        assert isinstance(summary, dict)
        assert summary["total_logs"] >= 1
        
        # Search logs
        results = log_service.search_logs(
            query="Test log",
            hours=1,
            limit=10
        )
        assert len(results) >= 1
    
    def test_performance_threshold_checking(self):
        """Test performance threshold checking without external services."""
        init_alerting()
        alerting = get_alerting_service()
        
        # Test normal metrics (should not trigger alerts)
        normal_metrics = {
            "error_rate_percent": 2.0,  # Below 5% threshold
            "average_response_time": 1.5,  # Below 3s threshold
            "total_cost_usd": 5.0,  # Below $10 threshold
            "system_metrics": {
                "cpu_percent": 50.0,  # Below 80% threshold
                "memory_percent": 60.0,  # Below 85% threshold
                "disk_percent": 70.0  # Below 90% threshold
            }
        }
        
        # Should not create alerts for normal metrics
        created_alerts = alerting.check_performance_thresholds(normal_metrics)
        assert len(created_alerts) == 0
        
        # Test high metrics (should trigger alerts)
        high_metrics = {
            "error_rate_percent": 10.0,  # Above 5% threshold
            "average_response_time": 5.0,  # Above 3s threshold
            "total_cost_usd": 15.0,  # Above $10 threshold
            "system_metrics": {
                "cpu_percent": 85.0,  # Above 80% threshold
                "memory_percent": 90.0,  # Above 85% threshold
                "disk_percent": 95.0  # Above 90% threshold
            }
        }
        
        # Should create alerts for high metrics
        created_alerts = alerting.check_performance_thresholds(high_metrics)
        assert len(created_alerts) > 0
        
        # Clean up created alerts
        for alert_id in created_alerts:
            alerting.resolve_alert(alert_id)
    
    def test_service_health_monitoring(self):
        """Test service health monitoring."""
        init_alerting()
        alerting = get_alerting_service()
        
        # Test healthy services (should not trigger alerts)
        healthy_services = {
            "database": {"status": "healthy", "message": "OK"},
            "redis": {"status": "healthy", "message": "OK"},
            "storage": {"status": "healthy", "message": "OK"}
        }
        
        created_alerts = alerting.check_service_health(healthy_services)
        assert len(created_alerts) == 0
        
        # Test unhealthy services (should trigger alerts)
        unhealthy_services = {
            "database": {"status": "unhealthy", "message": "Connection failed"},
            "redis": {"status": "degraded", "message": "High latency"},
            "storage": {"status": "healthy", "message": "OK"}
        }
        
        created_alerts = alerting.check_service_health(unhealthy_services)
        assert len(created_alerts) >= 1
        
        # Clean up
        for alert_id in created_alerts:
            alerting.resolve_alert(alert_id)
    
    def test_monitoring_error_tracking(self):
        """Test error tracking functionality."""
        init_monitoring()
        monitoring = get_monitoring_service()
        
        # Track an error
        test_error = ValueError("Test error")
        monitoring.track_error(
            error=test_error,
            context="test_context",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Get performance summary
        summary = monitoring.get_performance_summary(time_range_hours=1)
        assert isinstance(summary, dict)
        assert "total_errors" in summary
    
    def test_cost_tracking(self):
        """Test cost tracking functionality."""
        init_monitoring()
        monitoring = get_monitoring_service()
        
        # Track LLM cost
        monitoring.track_llm_cost(
            model_name="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.015,
            user_id="test_user",
            session_id="test_session"
        )
        
        # Get performance summary
        summary = monitoring.get_performance_summary(time_range_hours=1)
        assert "total_cost_usd" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])