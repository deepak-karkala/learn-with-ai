"""
Performance monitoring middleware for API request tracking and optimization.
"""

import time
import logging
import json
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio
import psutil

from ..services.performance_service import get_performance_service
from ..services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance and optimization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.performance_service = get_performance_service()
        self.monitoring_service = get_monitoring_service()
        
        # Performance thresholds
        self.slow_request_threshold = 2000  # 2 seconds in ms
        self.very_slow_threshold = 5000     # 5 seconds in ms
        
        # Request tracking
        self.active_requests = {}
        
        logger.info("Performance middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Monitor and optimize API request performance."""
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        # Track active request
        self.active_requests[request_id] = {
            "start_time": start_time,
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("User-Agent", ""),
        }
        
        try:
            # Get system metrics before request
            cpu_before = psutil.cpu_percent()
            memory_before = psutil.virtual_memory().percent
            
            # Process request with timeout protection
            response = await asyncio.wait_for(
                call_next(request),
                timeout=30.0  # 30 second timeout
            )
            
            # Calculate performance metrics
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Get system metrics after request
            cpu_after = psutil.cpu_percent()
            memory_after = psutil.virtual_memory().percent
            
            # Record performance event
            await self._record_request_performance(
                request=request,
                response=response,
                duration_ms=duration_ms,
                request_id=request_id,
                cpu_usage=cpu_after - cpu_before,
                memory_usage=memory_after - memory_before
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            
            # Check for performance alerts
            if duration_ms > self.slow_request_threshold:
                await self._handle_slow_request(request, duration_ms, request_id)
            
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {request.url.path} after 30 seconds")
            await self._record_timeout_event(request, request_id)
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"},
                headers={"X-Request-ID": request_id}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Request error in {request.url.path}: {e}")
            
            # Record error performance event
            await self._record_request_error(request, e, duration_ms, request_id)
            
            # Re-raise the exception to let other error handlers process it
            raise
            
        finally:
            # Clean up active request tracking
            self.active_requests.pop(request_id, None)
    
    async def _record_request_performance(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        request_id: str,
        cpu_usage: float,
        memory_usage: float
    ):
        """Record request performance metrics."""
        try:
            # Determine user ID if available
            user_id = None
            if hasattr(request.state, 'user') and request.state.user:
                user_id = request.state.user.get('user_id')
            
            # Record in performance service
            await self.performance_service._record_performance_event(
                operation=f"api_{request.method.lower()}_{request.url.path}",
                duration_ms=duration_ms,
                status_code=response.status_code,
                user_id=user_id,
                endpoint=request.url.path,
                method=request.method,
                metadata={
                    "request_id": request_id,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "query_params": dict(request.query_params),
                    "content_length": response.headers.get("content-length"),
                    "user_agent": request.headers.get("User-Agent", ""),
                }
            )
            
            # Send to monitoring service for real-time tracking
            if hasattr(self.monitoring_service, 'track_api_performance'):
                self.monitoring_service.track_api_performance({
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "user_id": user_id,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                })
            
        except Exception as e:
            logger.error(f"Failed to record request performance: {e}")
    
    async def _handle_slow_request(self, request: Request, duration_ms: float, request_id: str):
        """Handle slow request detection and alerting."""
        try:
            severity = "critical" if duration_ms > self.very_slow_threshold else "warning"
            
            alert_data = {
                "request_id": request_id,
                "endpoint": request.url.path,
                "method": request.method,
                "duration_ms": duration_ms,
                "threshold_ms": self.slow_request_threshold,
                "severity": severity,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("User-Agent", ""),
            }
            
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {self.slow_request_threshold}ms)"
            )
            
            # Send alert to monitoring
            if hasattr(self.monitoring_service, 'track_performance_alert'):
                self.monitoring_service.track_performance_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Failed to handle slow request alert: {e}")
    
    async def _record_timeout_event(self, request: Request, request_id: str):
        """Record request timeout event."""
        try:
            await self.performance_service._record_performance_event(
                operation=f"api_timeout_{request.method.lower()}_{request.url.path}",
                duration_ms=30000,  # 30 second timeout
                status_code=504,
                endpoint=request.url.path,
                method=request.method,
                metadata={
                    "request_id": request_id,
                    "timeout": True,
                    "query_params": dict(request.query_params),
                }
            )
        except Exception as e:
            logger.error(f"Failed to record timeout event: {e}")
    
    async def _record_request_error(
        self,
        request: Request,
        error: Exception,
        duration_ms: float,
        request_id: str
    ):
        """Record request error performance event."""
        try:
            await self.performance_service._record_performance_event(
                operation=f"api_error_{request.method.lower()}_{request.url.path}",
                duration_ms=duration_ms,
                status_code=500,
                endpoint=request.url.path,
                method=request.method,
                metadata={
                    "request_id": request_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "query_params": dict(request.query_params),
                }
            )
        except Exception as e:
            logger.error(f"Failed to record error event: {e}")
    
    def get_active_requests(self) -> Dict[str, Any]:
        """Get currently active requests for debugging."""
        current_time = time.time()
        active = {}
        
        for request_id, request_info in self.active_requests.items():
            duration_ms = (current_time - request_info["start_time"]) * 1000
            active[request_id] = {
                **request_info,
                "current_duration_ms": duration_ms,
                "is_slow": duration_ms > self.slow_request_threshold,
            }
        
        return active


class DatabasePerformanceMiddleware:
    """Middleware for monitoring database query performance."""
    
    def __init__(self):
        self.performance_service = get_performance_service()
        self.query_threshold_ms = 1000  # 1 second threshold for slow queries
        
    def monitor_query(self, operation: str):
        """Decorator for monitoring database query performance."""
        return self.performance_service.performance_monitor(
            operation=f"db_{operation}",
            cache_key=f"db_cache_{operation}"
        )
    
    async def record_slow_query(self, query: str, duration_ms: float, params: Any = None):
        """Record slow database query."""
        if duration_ms > self.query_threshold_ms:
            await self.performance_service._record_performance_event(
                operation="slow_database_query",
                duration_ms=duration_ms,
                status_code=200,
                metadata={
                    "query": query[:500],  # First 500 chars of query
                    "params": str(params) if params else None,
                    "threshold_ms": self.query_threshold_ms,
                }
            )
            
            logger.warning(f"Slow database query detected: {duration_ms:.2f}ms")


class CachePerformanceTracker:
    """Track and optimize cache performance."""
    
    def __init__(self):
        self.performance_service = get_performance_service()
        
    def monitor_cache_operation(self, operation: str, cache_type: str = "redis"):
        """Monitor cache operations (get, set, delete)."""
        return self.performance_service.performance_monitor(
            operation=f"cache_{cache_type}_{operation}"
        )
    
    async def record_cache_miss_expensive_operation(self, cache_key: str, duration_ms: float):
        """Record when cache miss leads to expensive operation."""
        await self.performance_service._record_performance_event(
            operation="cache_miss_expensive",
            duration_ms=duration_ms,
            status_code=200,
            metadata={
                "cache_key": cache_key,
                "cost_without_cache": duration_ms,
            }
        )
        
        if duration_ms > 5000:  # 5+ seconds
            logger.warning(
                f"Expensive cache miss: {cache_key} took {duration_ms:.2f}ms. "
                "Consider preloading or increasing TTL."
            )


# Global middleware instances
_db_performance_middleware: Optional[DatabasePerformanceMiddleware] = None
_cache_performance_tracker: Optional[CachePerformanceTracker] = None


def get_db_performance_middleware() -> DatabasePerformanceMiddleware:
    """Get database performance middleware instance."""
    global _db_performance_middleware
    if _db_performance_middleware is None:
        _db_performance_middleware = DatabasePerformanceMiddleware()
    return _db_performance_middleware


def get_cache_performance_tracker() -> CachePerformanceTracker:
    """Get cache performance tracker instance."""
    global _cache_performance_tracker
    if _cache_performance_tracker is None:
        _cache_performance_tracker = CachePerformanceTracker()
    return _cache_performance_tracker