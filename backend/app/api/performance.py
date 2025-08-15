"""
Performance monitoring and optimization API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..services.performance_service import get_performance_service
from ..services.load_testing_service import get_load_testing_service, run_standard_load_tests
from ..services.auth_service import get_auth_service, Permission
from ..middleware.auth_middleware import get_current_active_user, require_permission
from ..models.performance import (
    PerformanceStatsResponse,
    PerformanceAlert,
    CacheStatsResponse,
    SlowOperationResponse,
    LoadTestRequest,
    LoadTestResult
)

router = APIRouter(prefix="/api/performance", tags=["Performance"])
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=PerformanceStatsResponse)
async def get_performance_stats(
    operation: Optional[str] = Query(None, description="Specific operation to analyze"),
    hours: int = Query(24, description="Time window in hours", ge=1, le=168),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get performance statistics for operations."""
    try:
        # Check if user has monitoring permissions (admin or developer)
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view performance statistics"
            )
        
        performance_service = get_performance_service()
        stats = performance_service.get_performance_stats(operation, hours)
        
        return PerformanceStatsResponse(
            operation=stats.get("operation", "all"),
            time_window_hours=hours,
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance statistics")


@router.get("/slow-operations", response_model=List[SlowOperationResponse])
async def get_slow_operations(
    threshold_ms: float = Query(2000, description="Duration threshold in milliseconds"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get slowest operations above threshold."""
    try:
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view slow operations"
            )
        
        performance_service = get_performance_service()
        slow_ops = performance_service.get_slow_operations(threshold_ms, limit)
        
        return [SlowOperationResponse(**op) for op in slow_ops]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get slow operations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve slow operations")


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get cache performance statistics."""
    try:
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view cache statistics"
            )
        
        performance_service = get_performance_service()
        cache_stats = performance_service._get_cache_stats()
        
        return CacheStatsResponse(**cache_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")


@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Cache key pattern to clear"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Clear performance cache."""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only administrators can clear cache"
            )
        
        performance_service = get_performance_service()
        performance_service.clear_cache(pattern)
        
        return {
            "success": True,
            "message": f"Cache cleared {'with pattern: ' + pattern if pattern else 'completely'}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/health")
async def performance_health_check():
    """Health check endpoint for performance monitoring."""
    try:
        performance_service = get_performance_service()
        
        # Get basic stats to verify service is working
        stats = performance_service.get_performance_stats(hours=1)
        cache_stats = performance_service._get_cache_stats()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "performance_monitoring",
            "recent_events": stats.get("total_events", 0),
            "cache_hit_rate": cache_stats.get("hit_rate", 0.0),
            "uptime_hours": 1,  # Simplified - would track actual uptime
        }
        
        # Check if performance is degraded
        if stats.get("error_rate", 0) > 0.1:  # 10% error rate
            health_data["status"] = "degraded"
            health_data["warning"] = "High error rate detected"
        
        if stats.get("avg_duration_ms", 0) > 5000:  # 5 second average
            health_data["status"] = "degraded"
            health_data["warning"] = "High average response time"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "performance_monitoring",
            "error": str(e)
        }


@router.post("/optimize")
async def optimize_performance(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Trigger performance optimization tasks."""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only administrators can trigger optimization"
            )
        
        # Add background optimization tasks
        background_tasks.add_task(run_performance_optimization)
        
        return {
            "success": True,
            "message": "Performance optimization started",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "running"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger optimization: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger optimization")


@router.get("/alerts", response_model=List[PerformanceAlert])
async def get_performance_alerts(
    hours: int = Query(24, description="Time window in hours", ge=1, le=168),
    severity: Optional[str] = Query(None, description="Filter by severity: warning, critical"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get performance alerts."""
    try:
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view performance alerts"
            )
        
        # This would integrate with the monitoring service to get alerts
        # For now, return a simplified response
        alerts = []
        
        performance_service = get_performance_service()
        slow_ops = performance_service.get_slow_operations(2000, 20)  # Get more for alerts
        
        for op in slow_ops:
            if severity and (
                (severity == "warning" and op["duration_ms"] < 5000) or
                (severity == "critical" and op["duration_ms"] >= 5000)
            ):
                continue
                
            alert_severity = "critical" if op["duration_ms"] >= 5000 else "warning"
            alerts.append(PerformanceAlert(
                alert_id=f"perf_alert_{op['operation']}_{int(datetime.fromisoformat(op['timestamp']).timestamp())}",
                severity=alert_severity,
                operation=op["operation"],
                duration_ms=op["duration_ms"],
                threshold_ms=2000,
                timestamp=op["timestamp"],
                endpoint=op.get("endpoint"),
                user_id=op.get("user_id")
            ))
        
        return alerts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance alerts")


async def run_performance_optimization():
    """Background task for performance optimization."""
    try:
        logger.info("Starting performance optimization...")
        
        performance_service = get_performance_service()
        
        # Analyze performance patterns
        stats = performance_service.get_performance_stats(hours=24)
        
        # Identify optimization opportunities
        if stats.get("cache_stats", {}).get("hit_rate", 0) < 0.8:
            logger.info("Cache hit rate is low, analyzing cache patterns...")
            
        # Clean up old performance data
        # This would be implemented based on the storage strategy
        
        # Preload commonly used data
        # This would preload frequently accessed data into cache
        
        logger.info("Performance optimization completed")
        
    except Exception as e:
        logger.error(f"Performance optimization failed: {e}")


@router.get("/recommendations")
async def get_performance_recommendations(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get performance optimization recommendations."""
    try:
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view recommendations"
            )
        
        performance_service = get_performance_service()
        stats = performance_service.get_performance_stats(hours=24)
        cache_stats = performance_service._get_cache_stats()
        slow_ops = performance_service.get_slow_operations(2000, 10)
        
        recommendations = []
        
        # Cache optimization recommendations
        if cache_stats.get("hit_rate", 0) < 0.8:
            recommendations.append({
                "type": "cache",
                "priority": "high",
                "title": "Improve Cache Hit Rate",
                "description": f"Current cache hit rate is {cache_stats.get('hit_rate', 0)*100:.1f}%. Target is >80%.",
                "actions": [
                    "Review cache TTL settings",
                    "Identify frequently accessed data for preloading",
                    "Consider cache warming strategies"
                ]
            })
        
        # Slow operations recommendations
        if slow_ops:
            recommendations.append({
                "type": "performance",
                "priority": "critical" if any(op["duration_ms"] > 5000 for op in slow_ops) else "high",
                "title": "Optimize Slow Operations",
                "description": f"Found {len(slow_ops)} operations slower than 2 seconds.",
                "actions": [
                    "Review and optimize database queries",
                    "Add caching for expensive operations",
                    "Consider asynchronous processing for heavy tasks"
                ],
                "slow_operations": [op["operation"] for op in slow_ops[:5]]
            })
        
        # Error rate recommendations
        error_rate = stats.get("error_rate", 0)
        if error_rate > 0.05:  # 5% error rate
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "title": "Reduce Error Rate",
                "description": f"Current error rate is {error_rate*100:.1f}%. Target is <5%.",
                "actions": [
                    "Investigate root causes of errors",
                    "Improve error handling and retry logic",
                    "Add more comprehensive input validation"
                ]
            })
        
        # General recommendations
        avg_duration = stats.get("avg_duration_ms", 0)
        if avg_duration > 1000:  # 1 second average
            recommendations.append({
                "type": "general",
                "priority": "medium",
                "title": "Improve Overall Response Times",
                "description": f"Average response time is {avg_duration:.0f}ms. Target is <1000ms.",
                "actions": [
                    "Profile code to identify bottlenecks",
                    "Optimize database connections and queries",
                    "Consider request compression",
                    "Review third-party API call patterns"
                ]
            })
        
        if not recommendations:
            recommendations.append({
                "type": "success",
                "priority": "info",
                "title": "Performance is Good",
                "description": "No critical performance issues detected.",
                "actions": [
                    "Continue monitoring performance metrics",
                    "Consider load testing for peak usage scenarios"
                ]
            })
        
        return {
            "recommendations": recommendations,
            "stats_summary": {
                "avg_duration_ms": avg_duration,
                "error_rate": error_rate,
                "cache_hit_rate": cache_stats.get("hit_rate", 0),
                "slow_operations_count": len(slow_ops)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.post("/load-test", response_model=LoadTestResult)
async def run_load_test(
    request: LoadTestRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Run a load test on a specific endpoint."""
    try:
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to run load tests"
            )
        
        load_testing_service = get_load_testing_service()
        result = await load_testing_service.run_load_test(request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run load test: {e}")
        raise HTTPException(status_code=500, detail="Failed to run load test")


@router.post("/load-test/standard")
async def run_standard_load_tests_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Run standard load test suite."""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only administrators can run standard load tests"
            )
        
        results = await run_standard_load_tests()
        
        # Calculate summary statistics
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.error_rate < 0.1)
        avg_rps = sum(r.requests_per_second for r in results.values()) / total_tests if total_tests > 0 else 0
        avg_response_time = sum(r.avg_response_time_ms for r in results.values()) / total_tests if total_tests > 0 else 0
        
        return {
            "test_suite": "standard",
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "pass_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "avg_requests_per_second": avg_rps,
            "avg_response_time_ms": avg_response_time,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run standard load tests: {e}")
        raise HTTPException(status_code=500, detail="Failed to run standard load tests")


@router.get("/load-test/active")
async def get_active_load_tests(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get information about active load tests."""
    try:
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view load test status"
            )
        
        load_testing_service = get_load_testing_service()
        active_tests = load_testing_service.get_active_tests()
        
        return {
            "active_tests": active_tests,
            "total_active": len(active_tests),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active load tests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active load tests")


@router.get("/load-test/{test_id}")
async def get_load_test_status(
    test_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get status of a specific load test."""
    try:
        if not (current_user["role"] in ["admin", "developer"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view load test status"
            )
        
        load_testing_service = get_load_testing_service()
        test_status = load_testing_service.get_test_status(test_id)
        
        if not test_status:
            raise HTTPException(
                status_code=404,
                detail=f"Load test {test_id} not found"
            )
        
        return {
            "test_id": test_id,
            "status": test_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get load test status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve load test status")