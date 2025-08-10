from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI System Design Learning Platform API"}


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_health_check():
    """Test the API health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert data["services"]["fastapi"] == "running"


def test_chat_endpoint_validation():
    """Test chat endpoint input validation"""
    # Test empty message
    response = client.post("/api/chat", json={
        "message": "",
        "user_id": "test_user"
    })
    assert response.status_code == 422
    
    # Test message with only whitespace
    response = client.post("/api/chat", json={
        "message": "   ",
        "user_id": "test_user"
    })
    assert response.status_code == 422
    
    # Test message too long
    long_message = "a" * 5001
    response = client.post("/api/chat", json={
        "message": long_message,
        "user_id": "test_user"
    })
    assert response.status_code == 422
    
    # Test message with harmful content
    response = client.post("/api/chat", json={
        "message": "Hello <script>alert('xss')</script>",
        "user_id": "test_user"
    })
    assert response.status_code == 422
    
    # Test valid message
    response = client.post("/api/chat", json={
        "message": "Hello, I want to learn system design",
        "user_id": "test_user"
    })
    # Should get 503 since ADK service is not available in test environment
    assert response.status_code in [503, 500]


def test_rate_limiting():
    """Test rate limiting functionality"""
    # Make multiple requests to trigger rate limiting
    for i in range(12):  # Exceed the limit of 10 requests per minute
        response = client.post("/api/chat", json={
            "message": f"Test message {i}",
            "user_id": f"test_user_{i}"
        })
        
        if i < 10:
            # First 10 requests should go through (though they may fail due to ADK service)
            assert response.status_code in [503, 500, 429]
        else:
            # 11th request should be rate limited
            assert response.status_code == 429
            data = response.json()
            assert "Rate limit exceeded" in data["error"]
            assert "retry_after" in data


def test_session_endpoints():
    """Test session management endpoints"""
    # Test create session
    response = client.post("/api/session/create", json={
        "user_id": "test_user",
        "initial_state": {"skill_level": "beginner"}
    })
    # Should get 503 since ADK service is not available in test environment
    assert response.status_code in [503, 500]
    
    # Test get user sessions
    response = client.get("/api/session/test_user")
    # Should get 503 since ADK service is not available in test environment
    assert response.status_code in [503, 500]


def test_cors_headers():
    """Test CORS headers are properly set"""
    response = client.options("/api/chat", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    })
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
