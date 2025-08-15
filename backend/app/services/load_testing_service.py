"""
Load testing service for performance validation and optimization.
"""

import asyncio
import aiohttp
import time
import statistics
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..services.performance_service import get_performance_service
from ..models.performance import LoadTestRequest, LoadTestResult

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    base_url: str = "http://localhost:8000"
    default_headers: Dict[str, str] = field(default_factory=lambda: {
        "Content-Type": "application/json",
        "User-Agent": "LoadTester/1.0"
    })
    timeout_seconds: float = 30.0
    max_concurrent: int = 100


@dataclass
class RequestResult:
    """Result of a single request during load testing."""
    status_code: int
    response_time_ms: float
    success: bool
    error: Optional[str] = None
    response_size: Optional[int] = None


class LoadTestingService:
    """Service for conducting load tests on API endpoints."""
    
    def __init__(self, config: Optional[LoadTestConfig] = None):
        self.config = config or LoadTestConfig()
        self.performance_service = get_performance_service()
        self._active_tests: Dict[str, Dict[str, Any]] = {}
        
    async def run_load_test(self, request: LoadTestRequest) -> LoadTestResult:
        """Run a load test on the specified endpoint."""
        test_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Starting load test {test_id} on {request.endpoint}")
        
        # Store test metadata
        self._active_tests[test_id] = {
            "start_time": start_time,
            "endpoint": request.endpoint,
            "concurrent_users": request.concurrent_users,
            "status": "running"
        }
        
        try:
            # Run the load test
            results = await self._execute_load_test(request)
            
            # Calculate statistics
            test_result = self._calculate_test_results(
                test_id=test_id,
                request=request,
                results=results,
                start_time=start_time
            )
            
            # Record performance data
            await self._record_load_test_results(test_result)
            
            self._active_tests[test_id]["status"] = "completed"
            return test_result
            
        except Exception as e:
            logger.error(f"Load test {test_id} failed: {e}")
            self._active_tests[test_id]["status"] = "failed"
            self._active_tests[test_id]["error"] = str(e)
            raise
        finally:
            # Clean up after some time
            asyncio.create_task(self._cleanup_test_data(test_id, delay=300))  # 5 minutes
    
    async def _execute_load_test(self, request: LoadTestRequest) -> List[RequestResult]:
        """Execute the actual load test with concurrent requests."""
        results = []
        
        # Create semaphore to limit concurrent connections
        semaphore = asyncio.Semaphore(min(request.concurrent_users, self.config.max_concurrent))
        
        async def make_request(session: aiohttp.ClientSession, request_id: int) -> RequestResult:
            """Make a single request and return the result."""
            async with semaphore:
                start_time = time.time()
                try:
                    url = f"{self.config.base_url.rstrip('/')}{request.endpoint}"
                    
                    # Prepare request data
                    kwargs = {
                        "headers": self.config.default_headers,
                        "timeout": aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                    }
                    
                    if request.test_data:
                        kwargs["json"] = request.test_data
                        method = "post"
                    else:
                        method = "get"
                    
                    # Make the request
                    async with getattr(session, method)(url, **kwargs) as response:
                        response_time_ms = (time.time() - start_time) * 1000
                        
                        # Read response for size calculation
                        response_data = await response.read()
                        
                        return RequestResult(
                            status_code=response.status,
                            response_time_ms=response_time_ms,
                            success=200 <= response.status < 400,
                            response_size=len(response_data)
                        )
                        
                except asyncio.TimeoutError:
                    return RequestResult(
                        status_code=0,
                        response_time_ms=(time.time() - start_time) * 1000,
                        success=False,
                        error="timeout"
                    )
                except Exception as e:
                    return RequestResult(
                        status_code=0,
                        response_time_ms=(time.time() - start_time) * 1000,
                        success=False,
                        error=str(e)
                    )
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(limit=self.config.max_concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # Calculate request timing
            if request.requests_per_second:
                request_interval = 1.0 / request.requests_per_second
                total_requests = min(
                    request.requests_per_second * request.duration_seconds,
                    request.concurrent_users * request.duration_seconds
                )
            else:
                # Continuous load for duration
                request_interval = 0.1  # 10 requests per second per user
                total_requests = int(request.duration_seconds / request_interval) * request.concurrent_users
            
            # Generate requests
            tasks = []
            request_id = 0
            
            end_time = time.time() + request.duration_seconds
            
            while time.time() < end_time and request_id < total_requests:
                # Create batch of concurrent requests
                batch_size = min(request.concurrent_users, total_requests - request_id)
                batch_tasks = []
                
                for _ in range(batch_size):
                    if time.time() >= end_time:
                        break
                    
                    task = asyncio.create_task(make_request(session, request_id))
                    batch_tasks.append(task)
                    request_id += 1
                
                # Wait for batch completion or interval
                if request.requests_per_second:
                    await asyncio.sleep(request_interval)
                
                tasks.extend(batch_tasks)
                
                # Process completed tasks to avoid memory buildup
                if len(tasks) > 100:
                    done_tasks = [task for task in tasks if task.done()]
                    results.extend([await task for task in done_tasks])
                    tasks = [task for task in tasks if not task.done()]
            
            # Wait for all remaining tasks
            if tasks:
                results.extend(await asyncio.gather(*tasks, return_exceptions=True))
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, RequestResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Request failed with exception: {result}")
                valid_results.append(RequestResult(
                    status_code=0,
                    response_time_ms=0,
                    success=False,
                    error=str(result)
                ))
        
        return valid_results
    
    def _calculate_test_results(
        self,
        test_id: str,
        request: LoadTestRequest,
        results: List[RequestResult],
        start_time: datetime
    ) -> LoadTestResult:
        """Calculate test statistics from request results."""
        if not results:
            return LoadTestResult(
                test_id=test_id,
                endpoint=request.endpoint,
                concurrent_users=request.concurrent_users,
                duration_seconds=request.duration_seconds,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0.0,
                min_response_time_ms=0.0,
                max_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                requests_per_second=0.0,
                error_rate=1.0,
                timestamp=start_time.isoformat(),
                status="completed"
            )
        
        # Calculate basic statistics
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = self._calculate_percentile(response_times, 95)
            p99_response_time = self._calculate_percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p95_response_time = p99_response_time = 0.0
        
        # Calculate throughput
        actual_duration = (datetime.utcnow() - start_time).total_seconds()
        requests_per_second = len(results) / max(actual_duration, 0.1)
        
        # Calculate throughput in MB/s if response sizes available
        total_bytes = sum(r.response_size or 0 for r in results)
        throughput_mb_per_sec = (total_bytes / (1024 * 1024)) / max(actual_duration, 0.1) if total_bytes > 0 else None
        
        return LoadTestResult(
            test_id=test_id,
            endpoint=request.endpoint,
            concurrent_users=request.concurrent_users,
            duration_seconds=request.duration_seconds,
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=len(failed_results) / len(results),
            throughput_mb_per_sec=throughput_mb_per_sec,
            timestamp=start_time.isoformat(),
            status="completed"
        )
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile for response time data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        # Use the nearest rank method for percentile calculation
        index = (percentile / 100.0) * (len(sorted_data) - 1)
        if index == int(index):
            return sorted_data[int(index)]
        else:
            # Linear interpolation between two nearest values
            lower_index = int(index)
            upper_index = min(lower_index + 1, len(sorted_data) - 1)
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    async def _record_load_test_results(self, result: LoadTestResult):
        """Record load test results in performance service."""
        try:
            # Record as performance event
            await self.performance_service._record_performance_event(
                operation="load_test",
                duration_ms=result.avg_response_time_ms,
                status_code=200 if result.error_rate < 0.1 else 500,
                metadata={
                    "test_id": result.test_id,
                    "endpoint": result.endpoint,
                    "concurrent_users": result.concurrent_users,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "requests_per_second": result.requests_per_second,
                    "error_rate": result.error_rate,
                    "p95_response_time_ms": result.p95_response_time_ms,
                    "p99_response_time_ms": result.p99_response_time_ms,
                }
            )
            
            logger.info(f"Load test results recorded: {result.test_id}")
            
        except Exception as e:
            logger.error(f"Failed to record load test results: {e}")
    
    async def _cleanup_test_data(self, test_id: str, delay: int = 300):
        """Clean up test data after delay."""
        await asyncio.sleep(delay)
        self._active_tests.pop(test_id, None)
        logger.debug(f"Cleaned up test data for {test_id}")
    
    def get_active_tests(self) -> Dict[str, Any]:
        """Get information about currently active tests."""
        return {
            test_id: {
                **test_info,
                "duration_seconds": (datetime.utcnow() - test_info["start_time"]).total_seconds()
            }
            for test_id, test_info in self._active_tests.items()
        }
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific test."""
        return self._active_tests.get(test_id)


# Pre-defined test scenarios
class StandardLoadTests:
    """Standard load test scenarios for common endpoints."""
    
    @staticmethod
    def chat_endpoint_test(concurrent_users: int = 10, duration_seconds: int = 30) -> LoadTestRequest:
        """Standard chat endpoint load test."""
        return LoadTestRequest(
            endpoint="/api/chat",
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            test_data={
                "message": "Hello, this is a load test message.",
                "user_id": "load_test_user"
            }
        )
    
    @staticmethod
    def health_endpoint_test(concurrent_users: int = 50, duration_seconds: int = 10) -> LoadTestRequest:
        """Health endpoint stress test."""
        return LoadTestRequest(
            endpoint="/health",
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds
        )
    
    @staticmethod
    def session_creation_test(concurrent_users: int = 20, duration_seconds: int = 60) -> LoadTestRequest:
        """Session creation load test."""
        return LoadTestRequest(
            endpoint="/api/session",
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            test_data={
                "user_id": "load_test_user"
            }
        )


# Global service instance
_load_testing_service: Optional[LoadTestingService] = None


def get_load_testing_service() -> LoadTestingService:
    """Get the global load testing service instance."""
    global _load_testing_service
    if _load_testing_service is None:
        _load_testing_service = LoadTestingService()
    return _load_testing_service


async def run_standard_load_tests() -> Dict[str, LoadTestResult]:
    """Run a suite of standard load tests."""
    service = get_load_testing_service()
    
    tests = {
        "health_check": StandardLoadTests.health_endpoint_test(50, 10),
        "chat_moderate": StandardLoadTests.chat_endpoint_test(10, 30),
        "chat_heavy": StandardLoadTests.chat_endpoint_test(25, 60),
        "session_creation": StandardLoadTests.session_creation_test(20, 30)
    }
    
    results = {}
    for test_name, test_request in tests.items():
        logger.info(f"Running standard load test: {test_name}")
        try:
            result = await service.run_load_test(test_request)
            results[test_name] = result
            logger.info(f"Completed {test_name}: {result.requests_per_second:.1f} req/s, {result.error_rate*100:.1f}% errors")
        except Exception as e:
            logger.error(f"Failed to run {test_name}: {e}")
            # Create failed result
            results[test_name] = LoadTestResult(
                test_id=str(uuid.uuid4()),
                endpoint=test_request.endpoint,
                concurrent_users=test_request.concurrent_users,
                duration_seconds=test_request.duration_seconds,
                total_requests=0,
                successful_requests=0,
                failed_requests=1,
                avg_response_time_ms=0.0,
                min_response_time_ms=0.0,
                max_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                requests_per_second=0.0,
                error_rate=1.0,
                timestamp=datetime.utcnow().isoformat(),
                status="failed"
            )
    
    return results