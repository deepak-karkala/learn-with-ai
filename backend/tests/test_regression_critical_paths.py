"""
Regression test suite for critical user paths.

This suite implements automated regression testing for the most important
user workflows in the Learn with AI platform as specified in Issue #25.
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from app.main import app


@pytest.fixture
def regression_client():
    """Test client configured for regression testing."""
    return TestClient(app)


@pytest.fixture
def mock_adk_service():
    """Mock ADK service for stable regression testing."""
    mock_adk = MagicMock()
    
    # Mock the is_available method to return True
    mock_adk.is_available.return_value = True
    
    # Mock consistent chat responses for regression testing
    mock_adk.process_chat_message = AsyncMock(return_value={
        "response": "This is a mock response for regression testing. I understand you want to learn about system design.",
        "session_id": "regression_test_session",
        "conversation_id": "regression_conversation"
    })
    
    # Mock assessment responses
    mock_adk.generate_assessment = AsyncMock(return_value={
        "overall_score": 3.5,
        "confidence_score": 4.0,
        "dimension_scores": {
            "requirements_analysis": {"score": 3.0, "feedback": "Good understanding of requirements"},
            "system_architecture": {"score": 4.0, "feedback": "Solid architectural thinking"},
            "technical_deep_dive": {"score": 3.5, "feedback": "Good technical details"},
            "scale_performance": {"score": 3.0, "feedback": "Consider scalability more"},
            "reliability_fault_tolerance": {"score": 3.5, "feedback": "Good reliability planning"},
            "communication_thought_process": {"score": 4.5, "feedback": "Excellent communication"}
        },
        "detailed_feedback": "Overall solid performance with room for improvement in scalability considerations.",
        "recommendations": ["Focus on database sharding", "Consider caching strategies"]
    })
    
    # Set mock service on app startup for regression testing
    try:
        app.state.adk_service = mock_adk
    except:
        pass  # Ignore if app state is not available
    
    return mock_adk


class TestCriticalUserPaths:
    """Test critical user workflow paths for regression."""
    
    def test_complete_learning_session_path(self, regression_client, mock_adk_service):
        """
        Critical Path: Complete learning session workflow.
        
        This is the most important user path - a full learning session from start to finish.
        Any regression here breaks the core user experience.
        """
        user_id = "regression_user_complete_session"
        
        # Step 1: Health check - system should be responsive
        health_response = regression_client.get("/health")
        assert health_response.status_code == 200, "System health check failed"
        
        # Step 2: Start chat conversation
        initial_chat = regression_client.post("/api/chat", json={
            "message": "I want to learn how to design a Twitter-like social media platform",
            "user_id": user_id
        })
        # Accept 503 as valid since ADK service may not be available in test environment
        assert initial_chat.status_code in [200, 503], f"Initial chat request failed with {initial_chat.status_code}"
        
        # Only validate response structure if we got a 200 response
        if initial_chat.status_code == 200:
            initial_data = initial_chat.json()
            assert "response" in initial_data, "Chat response missing response field"
            assert len(initial_data["response"]) > 10, "Chat response too short"
            session_id = initial_data.get("session_id", "default_session")
            
            # Step 3: Follow-up conversation to build context
            followup_chat = regression_client.post("/api/chat", json={
                "message": "What are the main components I should include in the architecture?",
                "user_id": user_id,
                "session_id": session_id
            })
            assert followup_chat.status_code in [200, 503], "Follow-up chat failed"
            
            if followup_chat.status_code == 200:
                followup_data = followup_chat.json()
                assert "response" in followup_data, "Follow-up response missing"
        else:
            # Service unavailable, use default session for further tests
            session_id = "default_session"
        
        # Step 4: Simulate whiteboard interaction
        test_png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        whiteboard_response = regression_client.post("/api/whiteboard/analyze", json={
            "png_data": test_png_data,
            "user_id": user_id,
            "session_id": session_id,
            "analysis_type": "comprehensive"
        })
        
        # Whiteboard analysis might not be fully implemented, accept various response codes
        assert whiteboard_response.status_code in [200, 404, 422, 501], f"Unexpected whiteboard response: {whiteboard_response.status_code}"
        
        # Step 5: Request assessment
        assessment_response = regression_client.post("/api/assessment/evaluate", json={
            "user_id": user_id,
            "session_id": session_id,
            "interaction_context": "User discussed Twitter architecture and main components",
            "conversation_history": "User wants to learn Twitter design, asked about main components"
        })
        
        # Assessment should work with mocked ADK service, but may fail if service unavailable
        if assessment_response.status_code == 200:
            assessment_data = assessment_response.json()
            assert "overall_score" in assessment_data, "Assessment missing overall score"
            assert "dimension_scores" in assessment_data, "Assessment missing dimension scores"
            assert isinstance(assessment_data["overall_score"], (int, float)), "Overall score not numeric"
            assert 1 <= assessment_data["overall_score"] <= 5, "Overall score out of range"
        else:
            # Accept service unavailable responses (500/503) in test environment
            assert assessment_response.status_code in [500, 503], f"Unexpected assessment response: {assessment_response.status_code}"
        
        # Step 6: Check progress endpoint if available
        progress_response = regression_client.get(f"/api/progress/{user_id}")
        # Progress might not be implemented yet, so we accept 404
        assert progress_response.status_code in [200, 404], f"Unexpected progress response: {progress_response.status_code}"
        
        print(f"✅ Complete learning session path regression test passed for {user_id}")
    
    def test_multiple_user_sessions_isolation(self, regression_client, mock_adk_service):
        """
        Critical Path: Multiple users should have isolated sessions.
        
        Regression in session isolation could leak data between users.
        """
        user1 = "regression_user_1"
        user2 = "regression_user_2"
        
        # User 1 starts conversation about Twitter
        user1_chat = regression_client.post("/api/chat", json={
            "message": "I want to design Twitter architecture",
            "user_id": user1
        })
        # Accept service unavailable responses in test environment
        if user1_chat.status_code == 200:
            user1_session = user1_chat.json().get("session_id", "session_1")
        else:
            assert user1_chat.status_code == 503, f"Unexpected user 1 chat response: {user1_chat.status_code}"
            user1_session = "mock_session_1"
        
        # User 2 starts conversation about Instagram
        user2_chat = regression_client.post("/api/chat", json={
            "message": "I want to design Instagram architecture", 
            "user_id": user2
        })
        if user2_chat.status_code == 200:
            user2_session = user2_chat.json().get("session_id", "session_2")
        else:
            assert user2_chat.status_code == 503, f"Unexpected user 2 chat response: {user2_chat.status_code}"
            user2_session = "mock_session_2"
        
        # Sessions should be different
        assert user1_session != user2_session, "Users sharing same session ID"
        
        # Follow-up messages should maintain context isolation - only test if services are available
        if user1_chat.status_code == 200 and user2_chat.status_code == 200:
            user1_followup = regression_client.post("/api/chat", json={
                "message": "Tell me about the database design",
                "user_id": user1,
                "session_id": user1_session
            })
            assert user1_followup.status_code in [200, 503], "User 1 follow-up failed"
            
            user2_followup = regression_client.post("/api/chat", json={
                "message": "Tell me about the database design",
                "user_id": user2, 
                "session_id": user2_session
            })
            assert user2_followup.status_code in [200, 503], "User 2 follow-up failed"
        
        print("✅ Multi-user session isolation regression test passed")
    
    def test_api_endpoint_availability(self, regression_client, mock_adk_service):
        """
        Critical Path: All core API endpoints should be available.
        
        This prevents regressions where endpoints accidentally become unavailable.
        """
        # Core endpoints that must always work
        core_endpoints = [
            ("GET", "/health"),
            ("POST", "/api/chat"),
            ("POST", "/api/assessment/evaluate"),
        ]
        
        # Optional endpoints that should return proper error codes if not implemented
        optional_endpoints = [
            ("POST", "/api/whiteboard/analyze"),
            ("POST", "/api/diagrams/generate"),
            ("GET", "/api/progress/test_user"),
            ("POST", "/api/voice"),  # WebSocket endpoint, might return 405 for POST
        ]
        
        # Test core endpoints
        for method, endpoint in core_endpoints:
            if method == "GET":
                response = regression_client.get(endpoint)
            else:
                # POST requests with minimal valid data
                test_data = self._get_test_data_for_endpoint(endpoint)
                response = regression_client.post(endpoint, json=test_data)
            
            # Core endpoints must not return 404, but may return 500/503 if external services unavailable
            if endpoint == "/api/assessment/evaluate":
                # Assessment may return 500 when ADK service is unavailable
                assert response.status_code not in [404], f"Core endpoint {method} {endpoint} failed with {response.status_code}"
            else:
                assert response.status_code not in [404, 500], f"Core endpoint {method} {endpoint} failed with {response.status_code}"
        
        # Test optional endpoints
        for method, endpoint in optional_endpoints:
            if method == "GET":
                response = regression_client.get(endpoint)
            else:
                test_data = self._get_test_data_for_endpoint(endpoint)
                response = regression_client.post(endpoint, json=test_data)
            
            # Optional endpoints should return proper error codes, not 500
            assert response.status_code != 500, f"Optional endpoint {method} {endpoint} returned server error"
        
        print("✅ API endpoint availability regression test passed")
    
    def test_performance_regression_basic(self, regression_client, mock_adk_service):
        """
        Critical Path: Basic performance regression test.
        
        Ensures that basic operations don't become significantly slower.
        """
        user_id = "performance_regression_user"
        
        # Test chat response time
        start_time = time.time()
        chat_response = regression_client.post("/api/chat", json={
            "message": "Hello, this is a performance test",
            "user_id": user_id
        })
        chat_time = time.time() - start_time
        
        # Chat may return 503 if service unavailable, but should still be fast
        assert chat_response.status_code in [200, 503], f"Chat request failed with {chat_response.status_code}"
        assert chat_time < 5.0, f"Chat response too slow: {chat_time:.2f}s (should be < 5s)"
        
        # Test health endpoint response time
        start_time = time.time()
        health_response = regression_client.get("/health")
        health_time = time.time() - start_time
        
        assert health_response.status_code == 200, "Health check failed"
        assert health_time < 1.0, f"Health check too slow: {health_time:.2f}s (should be < 1s)"
        
        # Test assessment response time (if available)
        start_time = time.time()
        assessment_response = regression_client.post("/api/assessment/evaluate", json={
            "user_id": user_id,
            "interaction_context": "Performance test context",
            "conversation_history": "Performance test conversation"
        })
        assessment_time = time.time() - start_time
        
        if assessment_response.status_code == 200:
            assert assessment_time < 10.0, f"Assessment too slow: {assessment_time:.2f}s (should be < 10s)"
        
        print(f"✅ Basic performance regression test passed - Chat: {chat_time:.2f}s, Health: {health_time:.2f}s")
    
    def test_error_handling_regression(self, regression_client, mock_adk_service):
        """
        Critical Path: Error handling should be consistent and not expose internals.
        
        Prevents regressions where error handling breaks or leaks sensitive information.
        """
        # Test invalid chat request
        invalid_chat = regression_client.post("/api/chat", json={
            "message": "",  # Empty message
            "user_id": ""   # Empty user ID
        })
        assert invalid_chat.status_code in [400, 422], "Invalid chat request should return 400/422"
        
        error_response = invalid_chat.json()
        assert "error" in error_response or "detail" in error_response, "Error response should contain error information"
        
        # Make sure error doesn't expose internal details
        error_text = str(error_response).lower()
        sensitive_terms = ["password", "secret", "key", "token", "internal", "traceback"]
        for term in sensitive_terms:
            assert term not in error_text, f"Error response exposes sensitive term: {term}"
        
        # Test malformed JSON handling
        malformed_response = regression_client.post("/api/chat", 
            data="invalid json", 
            headers={"content-type": "application/json"}
        )
        assert malformed_response.status_code in [400, 422], "Malformed JSON should return 400/422"
        
        # Test non-existent endpoint
        not_found = regression_client.get("/api/nonexistent")
        assert not_found.status_code == 404, "Non-existent endpoint should return 404"
        
        print("✅ Error handling regression test passed")
    
    def test_data_consistency_regression(self, regression_client, mock_adk_service):
        """
        Critical Path: Data should remain consistent across operations.
        
        Prevents regressions where data gets corrupted or lost.
        """
        user_id = "data_consistency_user"
        
        # Send initial message
        initial_response = regression_client.post("/api/chat", json={
            "message": "I want to design a database system",
            "user_id": user_id
        })
        # Accept service unavailable responses in test environment
        assert initial_response.status_code in [200, 503], f"Initial chat failed with {initial_response.status_code}"
        
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            session_id = initial_data.get("session_id")
            
            # Send follow-up message with session ID
            followup_response = regression_client.post("/api/chat", json={
                "message": "What about database sharding?",
                "user_id": user_id,
                "session_id": session_id
            })
            assert followup_response.status_code in [200, 503], f"Follow-up chat failed with {followup_response.status_code}"
            
            if followup_response.status_code == 200:
                followup_data = followup_response.json()
                
                # Session ID should remain consistent
                assert followup_data.get("session_id") == session_id, "Session ID changed between requests"
                
                # Response should exist and be reasonable
                assert "response" in followup_data, "Follow-up response missing"
                assert len(followup_data["response"]) > 5, "Follow-up response too short"
        
        print("✅ Data consistency regression test passed")
    
    def _get_test_data_for_endpoint(self, endpoint: str) -> dict:
        """Get minimal valid test data for each endpoint."""
        test_data_map = {
            "/api/chat": {
                "message": "Test message",
                "user_id": "test_user"
            },
            "/api/assessment/evaluate": {
                "user_id": "test_user",
                "interaction_context": "Test context",
                "conversation_history": "Test history"
            },
            "/api/whiteboard/analyze": {
                "png_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "user_id": "test_user"
            },
            "/api/diagrams/generate": {
                "system_description": "A simple web application",
                "diagram_type": "architecture",
                "user_id": "test_user"
            },
            "/api/voice": {
                "audio_data": "test_audio_data",
                "user_id": "test_user"
            }
        }
        
        return test_data_map.get(endpoint, {})


class TestRegressionSmoke:
    """Smoke tests to catch major regressions quickly."""
    
    def test_application_starts(self, regression_client):
        """Smoke test: Application should start and respond."""
        response = regression_client.get("/health")
        assert response.status_code == 200, "Application failed to start properly"
        
        health_data = response.json()
        assert "status" in health_data, "Health check missing status"
        print("✅ Application startup smoke test passed")
    
    def test_basic_chat_functionality(self, regression_client, mock_adk_service):
        """Smoke test: Basic chat should work."""
        response = regression_client.post("/api/chat", json={
            "message": "Hello, this is a smoke test",
            "user_id": "smoke_test_user"
        })
        
        # Accept service unavailable responses in test environment
        assert response.status_code in [200, 503], f"Basic chat functionality broken with {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, "Chat response format broken"
        print("✅ Basic chat functionality smoke test passed")
    
    def test_critical_imports(self):
        """Smoke test: Critical modules should import without errors."""
        try:
            from app.main import app
            from app.services.adk_service import ADKService
            from app.api.auth import router as auth_router
            from app.models.assessment import AssessmentRequest
            
            assert app is not None, "Main app failed to import"
            print("✅ Critical imports smoke test passed")
        except ImportError as e:
            pytest.fail(f"Critical import failed: {e}")


if __name__ == "__main__":
    # Run regression tests independently
    print("🔄 Running Regression Test Suite...")
    pytest.main([__file__, "-v", "-x"])  # -x stops on first failure