"""
Integration tests for monitoring and observability features.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.monitoring_service import get_monitoring_service, init_monitoring
from app.services.alerting_service import get_alerting_service, init_alerting, AlertType, AlertLevel
from app.services.analytics_service import get_analytics_service, init_analytics
from app.services.logging_service import get_log_service, init_logging


class TestMonitoringIntegration:
    """Test monitoring service integration."""
    
    @pytest.fixture(autouse=True)
    def setup_monitoring(self):
        """Set up monitoring services for tests."""
        init_monitoring()
        init_alerting()
        init_analytics()
        init_logging()
        yield
        # Cleanup after tests
    
    def test_monitoring_service_initialization(self):
        """Test monitoring service initializes correctly."""
        monitoring = get_monitoring_service()
        assert monitoring is not None
        
        # Test health check
        assert hasattr(monitoring, 'is_enabled')
        assert hasattr(monitoring, 'track_llm_call')
        assert hasattr(monitoring, 'track_error')
    
    def test_llm_cost_tracking(self):
        """Test LLM cost tracking functionality."""
        monitoring = get_monitoring_service()
        
        # Track a mock LLM cost
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
        assert isinstance(summary, dict)
        assert "total_cost_usd" in summary
    
    def test_chat_interaction_tracking(self):
        """Test chat interaction tracking."""
        monitoring = get_monitoring_service()
        analytics = get_analytics_service()
        
        # Start a session
        analytics.start_session("test_user", "test_session")
        
        # Track a chat interaction
        monitoring.track_chat_interaction(
            user_id="test_user",
            session_id="test_session",
            user_message="Hello, how are you?",
            ai_response="I'm doing well, thank you!",
            model_name="gpt-4",
            response_time=1.5,
            token_usage={"input_tokens": 10, "output_tokens": 15},
            cost=0.005
        )
        
        analytics.track_chat_interaction(
            user_id="test_user",
            session_id="test_session",
            user_message="Hello, how are you?",
            ai_response="I'm doing well, thank you!",
            response_time=1.5
        )
        
        # End session
        analytics.end_session("test_session")
        
        # Verify tracking
        user_analytics = analytics.get_user_analytics("test_user")
        assert user_analytics is not None
        assert user_analytics["total_messages"] > 0
    
    def test_error_tracking(self):
        """Test error tracking functionality."""
        monitoring = get_monitoring_service()
        analytics = get_analytics_service()
        
        # Track an error
        test_error = ValueError("Test error")
        monitoring.track_error(
            error=test_error,
            context="test_context",
            user_id="test_user",
            session_id="test_session"
        )
        
        analytics.track_error(
            user_id="test_user",
            session_id="test_session",
            error_type="ValueError",
            context="test_context"
        )
        
        # Get performance summary
        summary = monitoring.get_performance_summary(time_range_hours=1)
        assert "total_errors" in summary
    
    def test_api_request_monitoring(self):
        """Test API request monitoring."""
        monitoring = get_monitoring_service()
        
        # Track API requests
        monitoring.track_api_request(
            endpoint="/api/chat",
            method="POST",
            status_code=200,
            response_time=0.5,
            user_id="test_user"
        )
        
        monitoring.track_api_request(
            endpoint="/api/health",
            method="GET",
            status_code=200,
            response_time=0.1
        )
        
        # Get metrics
        summary = monitoring.get_performance_summary(time_range_hours=1)
        assert summary["total_requests"] >= 2
        assert summary["average_response_time"] > 0


class TestAlertingIntegration:
    """Test alerting service integration."""
    
    @pytest.fixture(autouse=True)
    def setup_alerting(self):
        """Set up alerting service for tests."""
        init_alerting()
        init_monitoring()
        yield
    
    def test_alerting_service_initialization(self):
        """Test alerting service initializes correctly."""
        alerting = get_alerting_service()
        assert alerting is not None
        assert hasattr(alerting, 'create_alert')
        assert hasattr(alerting, 'resolve_alert')
    
    def test_alert_creation_and_resolution(self):
        """Test alert creation and resolution."""
        alerting = get_alerting_service()
        
        # Create an alert
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
    
    def test_performance_threshold_checking(self):
        """Test performance threshold checking."""
        alerting = get_alerting_service()
        
        # Test metrics that should trigger alerts
        high_error_metrics = {
            "error_rate_percent": 10.0,  # Above default 5% threshold
            "average_response_time": 5.0,  # Above default 3s threshold
            "total_cost_usd": 15.0,  # Above default $10 threshold
            "system_metrics": {
                "cpu_percent": 85.0,  # Above default 80% threshold
                "memory_percent": 90.0,  # Above default 85% threshold
                "disk_percent": 95.0  # Above default 90% threshold
            }
        }
        
        # Check thresholds
        created_alerts = alerting.check_performance_thresholds(high_error_metrics)
        
        # Should create multiple alerts
        assert len(created_alerts) > 0
        
        # Clean up created alerts
        for alert_id in created_alerts:
            alerting.resolve_alert(alert_id)
    
    def test_service_health_checking(self):
        """Test service health checking."""
        alerting = get_alerting_service()
        
        # Test unhealthy services
        unhealthy_services = {
            "database": {"status": "unhealthy", "message": "Connection failed"},
            "redis": {"status": "degraded", "message": "High latency"},
            "storage": {"status": "healthy", "message": "OK"}
        }
        
        # Check service health
        created_alerts = alerting.check_service_health(unhealthy_services)
        
        # Should create alerts for unhealthy services
        assert len(created_alerts) >= 1
        
        # Clean up
        for alert_id in created_alerts:
            alerting.resolve_alert(alert_id)


class TestAnalyticsIntegration:
    """Test analytics service integration."""
    
    @pytest.fixture(autouse=True)
    def setup_analytics(self):
        """Set up analytics service for tests."""
        init_analytics()
        yield
    
    def test_analytics_service_initialization(self):
        """Test analytics service initializes correctly."""
        analytics = get_analytics_service()
        assert analytics is not None
        assert hasattr(analytics, 'start_session')
        assert hasattr(analytics, 'track_chat_interaction')
    
    def test_user_session_lifecycle(self):
        """Test complete user session lifecycle."""
        analytics = get_analytics_service()
        
        # Start session
        analytics.start_session("test_user_lifecycle", "test_session_lifecycle")
        
        # Track multiple interactions
        for i in range(3):
            analytics.track_chat_interaction(
                user_id="test_user_lifecycle",
                session_id="test_session_lifecycle",
                user_message=f"Message {i}",
                ai_response=f"Response {i}",
                response_time=1.0 + i * 0.1
            )
        
        # Track assessment
        analytics.track_assessment(
            user_id="test_user_lifecycle",
            session_id="test_session_lifecycle",
            assessment_scores={"architecture": 8.5, "scalability": 7.0},
            overall_score=7.75
        )
        
        # Track whiteboard usage
        analytics.track_whiteboard_usage(
            user_id="test_user_lifecycle",
            session_id="test_session_lifecycle",
            action="upload",
            processing_time=2.5
        )
        
        # End session
        analytics.end_session("test_session_lifecycle")
        
        # Verify analytics
        user_analytics = analytics.get_user_analytics("test_user_lifecycle")
        assert user_analytics is not None
        assert user_analytics["total_sessions"] == 1
        assert user_analytics["total_messages"] == 3
        assert user_analytics["total_assessments"] == 1
    
    def test_platform_analytics(self):
        """Test platform-wide analytics."""
        analytics = get_analytics_service()
        
        # Create some test data
        for user_num in range(3):
            user_id = f"platform_user_{user_num}"
            session_id = f"platform_session_{user_num}"
            
            analytics.start_session(user_id, session_id)
            analytics.track_chat_interaction(
                user_id=user_id,
                session_id=session_id,
                user_message="Platform test message",
                ai_response="Platform test response",
                response_time=1.0
            )
            analytics.end_session(session_id)
        
        # Get platform analytics
        platform_data = analytics.get_platform_analytics(days=1)
        assert isinstance(platform_data, dict)
        assert "total_users" in platform_data
        assert "total_sessions" in platform_data
        assert platform_data["total_users"] >= 3
    
    def test_cohort_analysis(self):
        """Test user cohort analysis."""
        analytics = get_analytics_service()
        
        # Create users with different engagement levels
        # High engagement user
        analytics.start_session("high_engagement_user", "high_session")
        for i in range(15):
            analytics.track_chat_interaction(
                user_id="high_engagement_user",
                session_id="high_session",
                user_message=f"High engagement message {i}",
                ai_response=f"High engagement response {i}",
                response_time=1.0
            )
        analytics.track_assessment(
            user_id="high_engagement_user",
            session_id="high_session",
            assessment_scores={"architecture": 9.0},
            overall_score=9.0
        )
        analytics.end_session("high_session")
        
        # Low engagement user
        analytics.start_session("low_engagement_user", "low_session")
        analytics.track_chat_interaction(
            user_id="low_engagement_user",
            session_id="low_session",
            user_message="Low engagement message",
            ai_response="Low engagement response",
            response_time=1.0
        )
        analytics.end_session("low_session")
        
        # Get cohort analysis
        cohort_data = analytics.get_user_cohort_analysis(days=1)
        assert isinstance(cohort_data, dict)
        assert "cohorts" in cohort_data


class TestLoggingIntegration:
    """Test logging service integration."""
    
    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Set up logging service for tests."""
        init_logging()
        yield
    
    def test_logging_service_initialization(self):
        """Test logging service initializes correctly."""
        log_service = get_log_service()
        assert log_service is not None
        assert hasattr(log_service, 'add_log_entry')
        assert hasattr(log_service, 'get_log_summary')
    
    def test_log_entry_tracking(self):
        """Test log entry tracking."""
        log_service = get_log_service()
        
        # Add test log entries
        test_logs = [
            {
                "level": "INFO",
                "logger": "test.logger",
                "message": "Test info message",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "level": "ERROR",
                "logger": "test.logger",
                "message": "Test error message",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "level": "WARNING",
                "logger": "test.logger",
                "message": "Test warning message",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        for log_entry in test_logs:
            log_service.add_log_entry(log_entry)
        
        # Get log summary
        summary = log_service.get_log_summary(hours=1)
        assert isinstance(summary, dict)
        assert summary["total_logs"] >= 3
    
    def test_log_search(self):
        """Test log search functionality."""
        log_service = get_log_service()
        
        # Add searchable log entries
        log_service.add_log_entry({
            "level": "ERROR",
            "logger": "search.test",
            "message": "Database connection failed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        log_service.add_log_entry({
            "level": "INFO",
            "logger": "search.test",
            "message": "User authentication successful",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Search for error logs
        error_logs = log_service.search_logs(
            query="database",
            level="ERROR",
            hours=1,
            limit=10
        )
        
        assert len(error_logs) >= 1
        assert any("database" in log["message"].lower() for log in error_logs)
    
    def test_log_analytics(self):
        """Test log analytics functionality."""
        log_service = get_log_service()
        
        # Add various log entries
        for level in ["INFO", "WARNING", "ERROR"]:
            for i in range(2):
                log_service.add_log_entry({
                    "level": level,
                    "logger": f"analytics.test.{level.lower()}",
                    "message": f"Test {level.lower()} message {i}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Get analytics
        analytics = log_service.get_log_analytics()
        assert isinstance(analytics, dict)
        assert "error_counts_by_logger" in analytics
        assert "total_errors" in analytics
        assert analytics["total_errors"] >= 2


class TestEndToEndMonitoring:
    """End-to-end monitoring integration tests."""
    
    @pytest.fixture(autouse=True)
    def setup_all_services(self):
        """Set up all monitoring services for E2E tests."""
        init_monitoring()
        init_alerting()
        init_analytics()
        init_logging()
        yield
    
    def test_complete_user_journey_monitoring(self):
        """Test monitoring for a complete user journey."""
        monitoring = get_monitoring_service()
        analytics = get_analytics_service()
        alerting = get_alerting_service()
        log_service = get_log_service()
        
        user_id = "e2e_test_user"
        session_id = "e2e_test_session"
        
        # 1. User starts session
        analytics.start_session(user_id, session_id)
        
        # 2. User has chat interactions
        for i in range(5):
            start_time = time.time()
            
            # Simulate chat processing
            time.sleep(0.1)  # Simulate processing time
            
            processing_time = time.time() - start_time
            
            # Track with monitoring
            monitoring.track_chat_interaction(
                user_id=user_id,
                session_id=session_id,
                user_message=f"E2E test message {i}",
                ai_response=f"E2E test response {i}",
                model_name="gpt-4",
                response_time=processing_time,
                token_usage={"input_tokens": 20, "output_tokens": 30},
                cost=0.01
            )
            
            # Track with analytics
            analytics.track_chat_interaction(
                user_id=user_id,
                session_id=session_id,
                user_message=f"E2E test message {i}",
                ai_response=f"E2E test response {i}",
                response_time=processing_time
            )
            
            # Log the interaction
            log_service.add_log_entry({
                "level": "INFO",
                "logger": "app.api.chat",
                "message": f"Chat interaction {i} completed",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # 3. User completes assessment
        assessment_scores = {
            "architecture": 8.5,
            "scalability": 7.5,
            "performance": 8.0
        }
        overall_score = 8.0
        
        monitoring.track_assessment(
            user_id=user_id,
            session_id=session_id,
            assessment_scores=assessment_scores,
            overall_score=overall_score,
            confidence_score=0.85,
            model_name="gpt-4",
            processing_time=3.0
        )
        
        analytics.track_assessment(
            user_id=user_id,
            session_id=session_id,
            assessment_scores=assessment_scores,
            overall_score=overall_score
        )
        
        # 4. Simulate an error
        test_error = RuntimeError("E2E test error")
        monitoring.track_error(
            error=test_error,
            context="e2e_test",
            user_id=user_id,
            session_id=session_id
        )
        
        analytics.track_error(
            user_id=user_id,
            session_id=session_id,
            error_type="RuntimeError",
            context="e2e_test"
        )
        
        # 5. End session
        analytics.end_session(session_id)
        
        # 6. Verify all tracking worked
        
        # Check monitoring metrics
        monitoring_summary = monitoring.get_performance_summary(time_range_hours=1)
        assert monitoring_summary["total_requests"] >= 5
        assert monitoring_summary["total_errors"] >= 1
        assert monitoring_summary["total_cost_usd"] > 0
        
        # Check analytics
        user_analytics = analytics.get_user_analytics(user_id)
        assert user_analytics is not None
        assert user_analytics["total_sessions"] == 1
        assert user_analytics["total_messages"] == 5
        assert user_analytics["total_assessments"] == 1
        
        platform_analytics = analytics.get_platform_analytics(days=1)
        assert platform_analytics["total_users"] >= 1
        assert platform_analytics["total_messages"] >= 5
        
        # Check logs
        log_summary = log_service.get_log_summary(hours=1)
        assert log_summary["total_logs"] >= 5
        
        search_results = log_service.search_logs(
            query="Chat interaction",
            hours=1,
            limit=10
        )
        assert len(search_results) >= 5
        
        # Check alerting (no alerts should be created for normal operation)
        active_alerts = alerting.get_active_alerts()
        # Should be empty or minimal for normal operation
        
        # Test alert creation with high error rate
        high_error_metrics = {
            "error_rate_percent": 15.0,
            "average_response_time": 2.0,
            "total_cost_usd": 5.0
        }
        
        created_alerts = alerting.check_performance_thresholds(high_error_metrics)
        assert len(created_alerts) >= 1
        
        # Clean up alerts
        for alert_id in created_alerts:
            alerting.resolve_alert(alert_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])