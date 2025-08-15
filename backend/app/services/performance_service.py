"""
Performance monitoring and optimization service for the AI System Design Learning Platform.
"""

import asyncio
import time
import statistics
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import hashlib
from functools import wraps
import threading

from ..services.redis_service import get_redis_service
from ..services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)


class PerformanceMetric(str, Enum):
    """Performance metric types."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DATABASE_QUERY_TIME = "database_query_time"
    EXTERNAL_API_TIME = "external_api_time"


@dataclass
class PerformanceEvent:
    """Performance event data structure."""
    event_id: str
    operation: str
    duration_ms: float
    timestamp: datetime
    status_code: int
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Performance statistics aggregation."""
    operation: str
    count: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    error_count: int
    error_rate: float
    timestamp_window: str


class PerformanceService:
    """Service for performance monitoring and optimization."""
    
    def __init__(self):
        self._redis_service = get_redis_service()
        self._monitoring_service = get_monitoring_service()
        
        # Performance thresholds
        self._thresholds = {
            PerformanceMetric.RESPONSE_TIME: 2000,  # 2 seconds in ms
            PerformanceMetric.ERROR_RATE: 0.05,     # 5% error rate
            PerformanceMetric.CACHE_HIT_RATE: 0.80,  # 80% cache hit rate
        }
        
        # In-memory performance data buffer
        self._events_buffer = []
        self._buffer_size = 1000
        self._buffer_lock = threading.Lock()
        
        # Cache for expensive operations
        self._operation_cache = {}
        self._cache_stats = {"hits": 0, "misses": 0, "total": 0}
        
        logger.info("Performance service initialized")
    
    def performance_monitor(self, operation: str, cache_key: Optional[str] = None):
        """Decorator to monitor performance of functions."""
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    error_occurred = False
                    result = None
                    
                    try:
                        # Check cache first if cache_key is provided
                        if cache_key:
                            cached_result = await self._get_cached_result(cache_key, *args, **kwargs)
                            if cached_result is not None:
                                self._record_cache_hit(operation)
                                duration_ms = (time.time() - start_time) * 1000
                                await self._record_performance_event(
                                    operation=f"{operation}_cached",
                                    duration_ms=duration_ms,
                                    status_code=200,
                                    metadata={"cache_hit": True}
                                )
                                return cached_result
                            else:
                                self._record_cache_miss(operation)
                        
                        # Execute the function
                        result = await func(*args, **kwargs)
                        
                        # Cache the result if cache_key is provided
                        if cache_key and result is not None:
                            await self._cache_result(cache_key, result, *args, **kwargs)
                        
                    except Exception as e:
                        error_occurred = True
                        logger.error(f"Error in {operation}: {e}")
                        raise
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        status_code = 500 if error_occurred else 200
                        
                        await self._record_performance_event(
                            operation=operation,
                            duration_ms=duration_ms,
                            status_code=status_code,
                            metadata={"cached": cache_key is not None and cache_key in self._operation_cache}
                        )
                        
                        # Check for performance alerts
                        if duration_ms > self._thresholds[PerformanceMetric.RESPONSE_TIME]:
                            await self._trigger_performance_alert(operation, duration_ms)
                    
                    return result
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    error_occurred = False
                    result = None
                    
                    try:
                        # Check cache first if cache_key is provided
                        if cache_key:
                            cached_result = self._get_cached_result_sync(cache_key, *args, **kwargs)
                            if cached_result is not None:
                                self._record_cache_hit(operation)
                                duration_ms = (time.time() - start_time) * 1000
                                self._record_performance_event_sync(
                                    operation=f"{operation}_cached",
                                    duration_ms=duration_ms,
                                    status_code=200,
                                    metadata={"cache_hit": True}
                                )
                                return cached_result
                            else:
                                self._record_cache_miss(operation)
                        
                        # Execute the function
                        result = func(*args, **kwargs)
                        
                        # Cache the result if cache_key is provided
                        if cache_key and result is not None:
                            self._cache_result_sync(cache_key, result, *args, **kwargs)
                        
                    except Exception as e:
                        error_occurred = True
                        logger.error(f"Error in {operation}: {e}")
                        raise
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        status_code = 500 if error_occurred else 200
                        
                        self._record_performance_event_sync(
                            operation=operation,
                            duration_ms=duration_ms,
                            status_code=status_code,
                            metadata={"cached": cache_key is not None and cache_key in self._operation_cache}
                        )
                        
                        # Check for performance alerts
                        if duration_ms > self._thresholds[PerformanceMetric.RESPONSE_TIME]:
                            try:
                                asyncio.create_task(self._trigger_performance_alert(operation, duration_ms))
                            except RuntimeError:
                                # No event loop running, skip alert for testing
                                pass
                    
                    return result
                return sync_wrapper
        return decorator
    
    async def _get_cached_result(self, cache_key: str, *args, **kwargs) -> Optional[Any]:
        """Get cached result for operation."""
        # Generate unique cache key based on function arguments
        key_hash = self._generate_cache_key(cache_key, *args, **kwargs)
        
        # Check in-memory cache first
        if key_hash in self._operation_cache:
            cache_entry = self._operation_cache[key_hash]
            if not self._is_cache_expired(cache_entry):
                return cache_entry["result"]
        
        # Check Redis cache if available
        if self._redis_service.is_available():
            cached_data = self._redis_service.get_cache(f"perf_cache:{key_hash}")
            if cached_data:
                return json.loads(cached_data)
        
        return None
    
    def _get_cached_result_sync(self, cache_key: str, *args, **kwargs) -> Optional[Any]:
        """Get cached result for operation (sync version)."""
        key_hash = self._generate_cache_key(cache_key, *args, **kwargs)
        
        if key_hash in self._operation_cache:
            cache_entry = self._operation_cache[key_hash]
            if not self._is_cache_expired(cache_entry):
                return cache_entry["result"]
        
        if self._redis_service.is_available():
            cached_data = self._redis_service.get_cache(f"perf_cache:{key_hash}")
            if cached_data:
                return json.loads(cached_data)
        
        return None
    
    async def _cache_result(self, cache_key: str, result: Any, *args, **kwargs):
        """Cache operation result."""
        key_hash = self._generate_cache_key(cache_key, *args, **kwargs)
        
        # Cache in memory (with TTL)
        self._operation_cache[key_hash] = {
            "result": result,
            "cached_at": datetime.utcnow(),
            "ttl_seconds": 300  # 5 minutes default
        }
        
        # Cache in Redis if available
        if self._redis_service.is_available():
            try:
                self._redis_service.set_cache(
                    f"perf_cache:{key_hash}",
                    json.dumps(result, default=str),
                    ttl_seconds=300
                )
            except Exception as e:
                logger.warning(f"Failed to cache in Redis: {e}")
    
    def _cache_result_sync(self, cache_key: str, result: Any, *args, **kwargs):
        """Cache operation result (sync version)."""
        key_hash = self._generate_cache_key(cache_key, *args, **kwargs)
        
        self._operation_cache[key_hash] = {
            "result": result,
            "cached_at": datetime.utcnow(),
            "ttl_seconds": 300
        }
        
        if self._redis_service.is_available():
            try:
                self._redis_service.set_cache(
                    f"perf_cache:{key_hash}",
                    json.dumps(result, default=str),
                    ttl_seconds=300
                )
            except Exception as e:
                logger.warning(f"Failed to cache in Redis: {e}")
    
    def _generate_cache_key(self, base_key: str, *args, **kwargs) -> str:
        """Generate unique cache key from function arguments."""
        key_data = f"{base_key}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        cached_at = cache_entry["cached_at"]
        ttl_seconds = cache_entry.get("ttl_seconds", 300)
        return (datetime.utcnow() - cached_at).total_seconds() > ttl_seconds
    
    def _record_cache_hit(self, operation: str):
        """Record cache hit for statistics."""
        self._cache_stats["hits"] += 1
        self._cache_stats["total"] += 1
    
    def _record_cache_miss(self, operation: str):
        """Record cache miss for statistics."""
        self._cache_stats["misses"] += 1
        self._cache_stats["total"] += 1
    
    async def _record_performance_event(
        self,
        operation: str,
        duration_ms: float,
        status_code: int,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record performance event."""
        event = PerformanceEvent(
            event_id=f"perf_{int(time.time() * 1000)}_{operation}",
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            status_code=status_code,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            metadata=metadata or {}
        )
        
        # Add to buffer
        with self._buffer_lock:
            self._events_buffer.append(event)
            if len(self._events_buffer) > self._buffer_size:
                self._events_buffer = self._events_buffer[-self._buffer_size:]
        
        # Store in Redis for persistence
        if self._redis_service.is_available():
            try:
                event_data = {
                    "event_id": event.event_id,
                    "operation": event.operation,
                    "duration_ms": event.duration_ms,
                    "timestamp": event.timestamp.isoformat(),
                    "status_code": event.status_code,
                    "user_id": event.user_id,
                    "endpoint": event.endpoint,
                    "method": event.method,
                    "metadata": event.metadata
                }
                
                # Store individual event
                self._redis_service.set_cache(
                    f"perf_event:{event.event_id}",
                    event_data,
                    ttl_seconds=3600 * 24  # 24 hours
                )
                
                # Add to operation-specific list
                operation_key = f"perf_ops:{operation}"
                operation_events = self._redis_service.get_cache(operation_key) or []
                operation_events.append(event.event_id)
                operation_events = operation_events[-100:]  # Keep last 100 events
                self._redis_service.set_cache(operation_key, operation_events, ttl_seconds=3600 * 24)
                
            except Exception as e:
                logger.warning(f"Failed to store performance event in Redis: {e}")
    
    def _record_performance_event_sync(
        self,
        operation: str,
        duration_ms: float,
        status_code: int,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record performance event (sync version)."""
        event = PerformanceEvent(
            event_id=f"perf_{int(time.time() * 1000)}_{operation}",
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            status_code=status_code,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            metadata=metadata or {}
        )
        
        with self._buffer_lock:
            self._events_buffer.append(event)
            if len(self._events_buffer) > self._buffer_size:
                self._events_buffer = self._events_buffer[-self._buffer_size:]
    
    async def _trigger_performance_alert(self, operation: str, duration_ms: float):
        """Trigger performance alert for slow operations."""
        try:
            alert_data = {
                "operation": operation,
                "duration_ms": duration_ms,
                "threshold_ms": self._thresholds[PerformanceMetric.RESPONSE_TIME],
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "warning" if duration_ms < 5000 else "critical"
            }
            
            logger.warning(f"Performance alert: {operation} took {duration_ms}ms")
            
            # Send to monitoring service
            if hasattr(self._monitoring_service, 'track_performance_alert'):
                self._monitoring_service.track_performance_alert(alert_data)
                
        except Exception as e:
            logger.error(f"Failed to trigger performance alert: {e}")
    
    def get_performance_stats(self, operation: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for operations."""
        try:
            stats = {}
            
            # Get events from buffer and Redis
            events = self._get_recent_events(operation, hours)
            
            if not events:
                return {"message": "No performance data available", "operation": operation}
            
            # Calculate statistics
            durations = [event.duration_ms for event in events]
            error_events = [event for event in events if event.status_code >= 400]
            
            stats = {
                "operation": operation or "all",
                "time_window_hours": hours,
                "total_events": len(events),
                "avg_duration_ms": statistics.mean(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p95_duration_ms": self._calculate_percentile(durations, 95),
                "p99_duration_ms": self._calculate_percentile(durations, 99),
                "error_count": len(error_events),
                "error_rate": len(error_events) / len(events) if events else 0,
                "cache_stats": self._get_cache_stats()
            }
            
            # Group by operation if no specific operation requested
            if not operation:
                operations_stats = {}
                operations = set(event.operation for event in events)
                for op in operations:
                    op_events = [e for e in events if e.operation == op]
                    op_durations = [e.duration_ms for e in op_events]
                    op_errors = [e for e in op_events if e.status_code >= 400]
                    
                    operations_stats[op] = {
                        "count": len(op_events),
                        "avg_duration_ms": statistics.mean(op_durations),
                        "max_duration_ms": max(op_durations),
                        "error_rate": len(op_errors) / len(op_events) if op_events else 0
                    }
                
                stats["operations"] = operations_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}
    
    def _get_recent_events(self, operation: Optional[str], hours: int) -> List[PerformanceEvent]:
        """Get recent performance events."""
        events = []
        
        # Get from buffer
        with self._buffer_lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            buffer_events = [
                event for event in self._events_buffer
                if event.timestamp > cutoff_time and (not operation or event.operation == operation)
            ]
            events.extend(buffer_events)
        
        # Get from Redis if available
        if self._redis_service.is_available():
            try:
                if operation:
                    operation_events = self._redis_service.get_cache(f"perf_ops:{operation}") or []
                else:
                    # Get all operations
                    operation_events = []
                    # This is a simplified approach - in production you'd use Redis SCAN
                
                # Fetch event details
                for event_id in operation_events:
                    event_data = self._redis_service.get_cache(f"perf_event:{event_id}")
                    if event_data:
                        try:
                            event = PerformanceEvent(
                                event_id=event_data["event_id"],
                                operation=event_data["operation"],
                                duration_ms=event_data["duration_ms"],
                                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                                status_code=event_data["status_code"],
                                user_id=event_data.get("user_id"),
                                endpoint=event_data.get("endpoint"),
                                method=event_data.get("method"),
                                metadata=event_data.get("metadata", {})
                            )
                            events.append(event)
                        except Exception as e:
                            logger.warning(f"Failed to parse event {event_id}: {e}")
            
            except Exception as e:
                logger.warning(f"Failed to get events from Redis: {e}")
        
        return events
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile for data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._cache_stats["total"]
        if total == 0:
            return {"hit_rate": 0.0, "hits": 0, "misses": 0, "total": 0}
        
        return {
            "hit_rate": self._cache_stats["hits"] / total,
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "total": total
        }
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear performance cache."""
        if pattern:
            # Clear specific pattern
            keys_to_remove = [key for key in self._operation_cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._operation_cache[key]
        else:
            # Clear all cache
            self._operation_cache.clear()
        
        # Reset cache stats
        self._cache_stats = {"hits": 0, "misses": 0, "total": 0}
        
        logger.info(f"Performance cache cleared (pattern: {pattern})")
    
    def get_slow_operations(self, threshold_ms: float = 2000, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest operations above threshold."""
        try:
            events = self._get_recent_events(None, 24)  # Last 24 hours
            slow_events = [
                event for event in events
                if event.duration_ms > threshold_ms
            ]
            
            # Sort by duration descending
            slow_events.sort(key=lambda x: x.duration_ms, reverse=True)
            
            result = []
            for event in slow_events[:limit]:
                result.append({
                    "operation": event.operation,
                    "duration_ms": event.duration_ms,
                    "timestamp": event.timestamp.isoformat(),
                    "endpoint": event.endpoint,
                    "status_code": event.status_code,
                    "user_id": event.user_id
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get slow operations: {e}")
            return []


# Global performance service instance
_performance_service: Optional[PerformanceService] = None


def get_performance_service() -> PerformanceService:
    """Get the global performance service instance."""
    global _performance_service
    if _performance_service is None:
        _performance_service = PerformanceService()
    return _performance_service


def init_performance_service() -> None:
    """Initialize performance service."""
    global _performance_service
    _performance_service = PerformanceService()
    logger.info("Performance service initialized")


# Convenience decorator
def monitor_performance(operation: str, cache_key: Optional[str] = None):
    """Convenience decorator for performance monitoring."""
    service = get_performance_service()
    return service.performance_monitor(operation, cache_key)