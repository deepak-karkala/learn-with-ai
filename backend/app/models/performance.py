"""
Pydantic models for performance monitoring and optimization API.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class PerformanceMetricType(str, Enum):
    """Performance metric types."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PerformanceStatsResponse(BaseModel):
    """Response model for performance statistics."""
    operation: str
    time_window_hours: int
    stats: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate (0-1)")
    hits: int = Field(..., ge=0, description="Number of cache hits")
    misses: int = Field(..., ge=0, description="Number of cache misses")
    total: int = Field(..., ge=0, description="Total cache operations")


class SlowOperationResponse(BaseModel):
    """Response model for slow operations."""
    operation: str
    duration_ms: float = Field(..., ge=0, description="Operation duration in milliseconds")
    timestamp: str
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    user_id: Optional[str] = None


class PerformanceAlert(BaseModel):
    """Performance alert model."""
    alert_id: str
    severity: AlertSeverity
    operation: str
    duration_ms: float
    threshold_ms: float
    timestamp: str
    endpoint: Optional[str] = None
    user_id: Optional[str] = None
    message: Optional[str] = None


class PerformanceMetric(BaseModel):
    """Performance metric model."""
    metric_type: PerformanceMetricType
    value: float
    timestamp: datetime
    operation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PerformanceRecommendation(BaseModel):
    """Performance optimization recommendation."""
    type: str = Field(..., description="Type of recommendation")
    priority: str = Field(..., description="Priority level (info, medium, high, critical)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    actions: List[str] = Field(..., description="Recommended actions")
    slow_operations: Optional[List[str]] = None


class PerformanceHealthResponse(BaseModel):
    """Performance health check response."""
    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    timestamp: str
    service: str
    recent_events: int = Field(..., ge=0)
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0)
    uptime_hours: float = Field(..., ge=0.0)
    warning: Optional[str] = None
    error: Optional[str] = None


class OptimizationRequest(BaseModel):
    """Request model for performance optimization."""
    operations: Optional[List[str]] = Field(None, description="Specific operations to optimize")
    cache_clear: bool = Field(False, description="Whether to clear cache")
    force_optimization: bool = Field(False, description="Force optimization even if recent")


class OptimizationResponse(BaseModel):
    """Response model for optimization requests."""
    success: bool
    message: str
    timestamp: str
    status: str = Field(..., description="Optimization status")
    details: Optional[Dict[str, Any]] = None


class LoadTestRequest(BaseModel):
    """Request model for load testing."""
    endpoint: str = Field(..., description="Endpoint to test")
    concurrent_users: int = Field(10, ge=1, le=100, description="Number of concurrent users")
    duration_seconds: int = Field(30, ge=5, le=300, description="Test duration in seconds")
    requests_per_second: Optional[int] = Field(None, ge=1, le=1000)
    test_data: Optional[Dict[str, Any]] = Field(None, description="Test request data")


class LoadTestResult(BaseModel):
    """Load test results."""
    test_id: str
    endpoint: str
    concurrent_users: int
    duration_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    throughput_mb_per_sec: Optional[float] = None
    timestamp: str
    status: str


class PerformanceTrend(BaseModel):
    """Performance trend data."""
    metric_type: PerformanceMetricType
    operation: Optional[str] = None
    time_points: List[datetime]
    values: List[float]
    trend_direction: str = Field(..., description="improving, degrading, stable")
    trend_percentage: float = Field(..., description="Trend change percentage")


class SystemResourceUsage(BaseModel):
    """System resource usage metrics."""
    timestamp: datetime
    cpu_percent: float = Field(..., ge=0.0, le=100.0)
    memory_percent: float = Field(..., ge=0.0, le=100.0)
    disk_usage_percent: float = Field(..., ge=0.0, le=100.0)
    network_io_mbps: Optional[float] = None
    active_connections: int = Field(..., ge=0)


class DatabasePerformanceStats(BaseModel):
    """Database performance statistics."""
    avg_query_time_ms: float = Field(..., ge=0.0)
    slow_queries_count: int = Field(..., ge=0)
    active_connections: int = Field(..., ge=0)
    connection_pool_usage: float = Field(..., ge=0.0, le=1.0)
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0)
    deadlocks_count: int = Field(..., ge=0)


class CachePerformanceStats(BaseModel):
    """Cache performance statistics."""
    hit_rate: float = Field(..., ge=0.0, le=1.0)
    miss_rate: float = Field(..., ge=0.0, le=1.0)
    total_operations: int = Field(..., ge=0)
    avg_get_time_ms: float = Field(..., ge=0.0)
    avg_set_time_ms: float = Field(..., ge=0.0)
    evictions_count: int = Field(..., ge=0)
    memory_usage_mb: float = Field(..., ge=0.0)


class APIEndpointStats(BaseModel):
    """API endpoint performance statistics."""
    endpoint: str
    method: str
    total_requests: int = Field(..., ge=0)
    avg_response_time_ms: float = Field(..., ge=0.0)
    min_response_time_ms: float = Field(..., ge=0.0)
    max_response_time_ms: float = Field(..., ge=0.0)
    p95_response_time_ms: float = Field(..., ge=0.0)
    p99_response_time_ms: float = Field(..., ge=0.0)
    error_count: int = Field(..., ge=0)
    error_rate: float = Field(..., ge=0.0, le=1.0)
    throughput_req_per_sec: float = Field(..., ge=0.0)


class PerformanceReport(BaseModel):
    """Comprehensive performance report."""
    report_id: str
    generated_at: datetime
    time_window_hours: int
    overall_health: str
    total_requests: int
    avg_response_time_ms: float
    error_rate: float
    cache_hit_rate: float
    
    # Detailed statistics
    endpoint_stats: List[APIEndpointStats]
    database_stats: DatabasePerformanceStats
    cache_stats: CachePerformanceStats
    system_resources: SystemResourceUsage
    
    # Trends and recommendations
    trends: List[PerformanceTrend]
    recommendations: List[PerformanceRecommendation]
    alerts: List[PerformanceAlert]
    
    # Summary metrics
    top_slow_operations: List[SlowOperationResponse]
    most_requested_endpoints: List[str]
    peak_traffic_hours: List[int]