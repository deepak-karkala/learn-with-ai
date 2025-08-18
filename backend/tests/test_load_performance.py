"""
Performance load testing suite for the Learn with AI platform.

This test suite implements comprehensive load testing scenarios as specified in Issue #25.
Tests concurrent usage, response times, throughput, and system stability under load.
"""

import asyncio
import time
import statistics
import concurrent.futures
from typing import List, Dict, Any
import pytest
from fastapi.testclient import TestClient
import random
import threading
from unittest.mock import MagicMock, AsyncMock

from app.main import app


class LoadTestMetrics:
    """Collects and analyzes performance metrics during load testing."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.status_codes: Dict[int, int] = {}
        self.concurrent_users = 0
        self.start_time = None
        self.end_time = None
        self._lock = threading.Lock()
    
    def record_response(self, response_time: float, status_code: int, error: str = None):
        """Record metrics from a single request."""
        with self._lock:
            self.response_times.append(response_time)
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
            if error:
                self.errors.append(error)
    
    def start_timing(self):
        """Start timing the load test."""
        self.start_time = time.time()
    
    def stop_timing(self):
        """Stop timing the load test."""
        self.end_time = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate performance summary report."""
        if not self.response_times:
            return {"error": "No response times recorded"}
        
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        total_requests = len(self.response_times)
        
        return {
            "total_requests": total_requests,
            "total_time": round(total_time, 2),
            "requests_per_second": round(total_requests / total_time, 2) if total_time > 0 else 0,
            "response_times": {
                "avg": round(statistics.mean(self.response_times), 3),
                "min": round(min(self.response_times), 3),
                "max": round(max(self.response_times), 3),
                "p95": round(statistics.quantiles(self.response_times, n=20)[18], 3),
                "p99": round(statistics.quantiles(self.response_times, n=100)[98], 3),
            },
            "status_codes": self.status_codes,
            "error_rate": round(len(self.errors) / total_requests * 100, 2) if total_requests > 0 else 0,
            "errors": self.errors[:10]  # Show first 10 errors
        }


@pytest.fixture
def load_test_client():
    """Test client optimized for load testing."""
    return TestClient(app)


@pytest.fixture
def mock_services():
    """Mock external services to focus on application performance."""
    # Mock ADK service to avoid external calls during load testing
    mock_adk = MagicMock()
    mock_adk.process_chat_message = AsyncMock(return_value={
        "response": "Mock response for load testing",
        "session_id": "test_session"
    })
    
    app.state.adk_service = mock_adk
    return mock_adk


class TestChatEndpointLoad:
    """Load tests for chat endpoint - the most critical user interaction."""
    
    def test_chat_concurrent_users_light_load(self, load_test_client, mock_services):
        """Test 10 concurrent users - light load scenario."""
        metrics = LoadTestMetrics()
        num_users = 10
        requests_per_user = 5
        
        def simulate_user(user_id: int):
            """Simulate a single user's interaction pattern."""
            for i in range(requests_per_user):
                start_time = time.time()
                try:
                    response = load_test_client.post("/api/chat", json={
                        "message": f"Hello from user {user_id}, request {i}",
                        "user_id": f"load_test_user_{user_id}"
                    })
                    response_time = time.time() - start_time
                    metrics.record_response(response_time, response.status_code)
                except Exception as e:
                    response_time = time.time() - start_time
                    metrics.record_response(response_time, 500, str(e))
                
                # Simulate natural user delay
                time.sleep(random.uniform(0.1, 0.5))
        
        metrics.start_timing()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(num_users)]
            concurrent.futures.wait(futures)
        metrics.stop_timing()
        
        summary = metrics.get_summary()
        print(f"Light Load Test Summary: {summary}")
        
        # Assertions for light load
        assert summary["error_rate"] < 5.0, f"Error rate too high: {summary['error_rate']}%"
        assert summary["response_times"]["avg"] < 2.0, f"Average response time too slow: {summary['response_times']['avg']}s"
        assert summary["response_times"]["p95"] < 3.0, f"95th percentile too slow: {summary['response_times']['p95']}s"
        assert summary["requests_per_second"] > 5, f"Too few requests per second: {summary['requests_per_second']}"
    
    def test_chat_concurrent_users_medium_load(self, load_test_client, mock_services):
        """Test 25 concurrent users - medium load scenario."""
        metrics = LoadTestMetrics()
        num_users = 25
        requests_per_user = 4
        
        def simulate_user(user_id: int):
            for i in range(requests_per_user):
                start_time = time.time()
                try:
                    response = load_test_client.post("/api/chat", json={
                        "message": f"Medium load test from user {user_id}, message {i}",
                        "user_id": f"med_load_user_{user_id}"
                    })
                    response_time = time.time() - start_time
                    metrics.record_response(response_time, response.status_code)
                except Exception as e:
                    response_time = time.time() - start_time
                    metrics.record_response(response_time, 500, str(e))
                
                time.sleep(random.uniform(0.05, 0.3))
        
        metrics.start_timing()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(num_users)]
            concurrent.futures.wait(futures)
        metrics.stop_timing()
        
        summary = metrics.get_summary()
        print(f"Medium Load Test Summary: {summary}")
        
        # Assertions for medium load
        assert summary["error_rate"] < 10.0, f"Error rate too high: {summary['error_rate']}%"
        assert summary["response_times"]["avg"] < 3.0, f"Average response time too slow: {summary['response_times']['avg']}s"
        assert summary["response_times"]["p95"] < 5.0, f"95th percentile too slow: {summary['response_times']['p95']}s"


class TestWhiteboardEndpointLoad:
    """Load tests for whiteboard analysis endpoint."""
    
    def test_whiteboard_analysis_concurrent_load(self, load_test_client, mock_services):
        """Test concurrent whiteboard analysis requests."""
        metrics = LoadTestMetrics()
        num_concurrent = 15
        
        # Mock PNG data for testing
        test_png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        def analyze_whiteboard():
            start_time = time.time()
            try:
                response = load_test_client.post("/api/whiteboard/analyze", json={
                    "png_data": test_png_data,
                    "user_id": f"wb_user_{threading.get_ident()}",
                    "analysis_type": "basic"
                })
                response_time = time.time() - start_time
                metrics.record_response(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                metrics.record_response(response_time, 500, str(e))
        
        metrics.start_timing()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(analyze_whiteboard) for _ in range(num_concurrent)]
            concurrent.futures.wait(futures)
        metrics.stop_timing()
        
        summary = metrics.get_summary()
        print(f"Whiteboard Load Test Summary: {summary}")
        
        # Whiteboard analysis is more CPU intensive, so we allow higher response times
        assert summary["error_rate"] < 15.0, f"Error rate too high: {summary['error_rate']}%"
        assert summary["response_times"]["avg"] < 5.0, f"Average response time too slow: {summary['response_times']['avg']}s"


class TestMixedWorkloadLoad:
    """Test mixed workload scenarios simulating real user behavior."""
    
    def test_realistic_user_session_load(self, load_test_client, mock_services):
        """Test realistic user session with mixed API calls."""
        metrics = LoadTestMetrics()
        num_users = 15
        
        def simulate_learning_session(user_id: int):
            """Simulate a complete learning session with mixed API calls."""
            user_name = f"mixed_user_{user_id}"
            
            # 1. Start with chat
            start_time = time.time()
            try:
                response = load_test_client.post("/api/chat", json={
                    "message": "I want to learn about system design",
                    "user_id": user_name
                })
                response_time = time.time() - start_time
                metrics.record_response(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                metrics.record_response(response_time, 500, str(e))
            
            time.sleep(random.uniform(0.5, 1.0))  # User reading time
            
            # 2. Follow up chat
            start_time = time.time()
            try:
                response = load_test_client.post("/api/chat", json={
                    "message": "What are the main components of Twitter?",
                    "user_id": user_name
                })
                response_time = time.time() - start_time
                metrics.record_response(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                metrics.record_response(response_time, 500, str(e))
            
            time.sleep(random.uniform(1.0, 2.0))  # User thinking time
            
            # 3. Request progress (if endpoint exists)
            start_time = time.time()
            try:
                response = load_test_client.get(f"/api/progress/{user_name}")
                response_time = time.time() - start_time
                metrics.record_response(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                metrics.record_response(response_time, 500 if "Connection" in str(e) else 404, str(e))
            
            time.sleep(random.uniform(0.2, 0.8))
            
            # 4. Health check (lightweight request)
            start_time = time.time()
            try:
                response = load_test_client.get("/health")
                response_time = time.time() - start_time
                metrics.record_response(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                metrics.record_response(response_time, 500, str(e))
        
        metrics.start_timing()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_learning_session, i) for i in range(num_users)]
            concurrent.futures.wait(futures)
        metrics.stop_timing()
        
        summary = metrics.get_summary()
        print(f"Mixed Workload Test Summary: {summary}")
        
        # Mixed workload should handle variety of requests well
        assert summary["error_rate"] < 20.0, f"Error rate too high for mixed workload: {summary['error_rate']}%"
        assert summary["response_times"]["avg"] < 4.0, f"Average response time too slow: {summary['response_times']['avg']}s"
        assert summary["total_requests"] >= num_users * 3, "Not all requests were processed"


class TestSystemStability:
    """Test system stability and resource management under load."""
    
    def test_memory_usage_stability(self, load_test_client, mock_services):
        """Test that memory usage remains stable during load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        metrics = LoadTestMetrics()
        num_requests = 50
        
        def make_request(i: int):
            start_time = time.time()
            try:
                response = load_test_client.post("/api/chat", json={
                    "message": f"Memory test request {i}",
                    "user_id": f"memory_test_user_{i % 10}"  # Reuse some user IDs
                })
                response_time = time.time() - start_time
                metrics.record_response(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                metrics.record_response(response_time, 500, str(e))
        
        metrics.start_timing()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            concurrent.futures.wait(futures)
        metrics.stop_timing()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        summary = metrics.get_summary()
        summary["memory_usage"] = {
            "initial_mb": round(initial_memory, 2),
            "final_mb": round(final_memory, 2),
            "increase_mb": round(memory_increase, 2)
        }
        
        print(f"Memory Stability Test Summary: {summary}")
        
        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase}MB"
        assert summary["error_rate"] < 10.0, f"Error rate too high: {summary['error_rate']}%"
    
    def test_rapid_fire_requests(self, load_test_client, mock_services):
        """Test handling of rapid successive requests from same user."""
        metrics = LoadTestMetrics()
        num_requests = 30
        user_id = "rapid_fire_user"
        
        def rapid_request(i: int):
            start_time = time.time()
            try:
                response = load_test_client.post("/api/chat", json={
                    "message": f"Rapid request {i}",
                    "user_id": user_id
                })
                response_time = time.time() - start_time
                metrics.record_response(response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                metrics.record_response(response_time, 500, str(e))
        
        metrics.start_timing()
        # Fire requests as fast as possible
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(rapid_request, i) for i in range(num_requests)]
            concurrent.futures.wait(futures)
        metrics.stop_timing()
        
        summary = metrics.get_summary()
        print(f"Rapid Fire Test Summary: {summary}")
        
        # Should handle rapid requests reasonably well
        assert summary["error_rate"] < 25.0, f"Error rate too high for rapid requests: {summary['error_rate']}%"
        assert summary["requests_per_second"] > 10, f"Throughput too low: {summary['requests_per_second']}"


if __name__ == "__main__":
    # Run load tests independently for manual testing
    print("Running Load Performance Tests...")
    pytest.main([__file__, "-v", "-s"])