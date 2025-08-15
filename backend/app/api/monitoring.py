"""
Monitoring and health check API endpoints for production.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from ..services.monitoring_service import get_monitoring_service
from ..services.redis_service import get_redis_service
from ..services.storage_service import get_storage_service
from ..services.memory_service import get_memory_service
from ..services.alerting_service import get_alerting_service
from ..services.analytics_service import get_analytics_service
from ..services.logging_service import get_log_service
from ..database.connection import check_database_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/monitoring/health")
async def comprehensive_health_check() -> Dict[str, Any]:
    """Comprehensive health check for all production services."""
    try:
        monitoring = get_monitoring_service()
        redis = get_redis_service()
        storage = get_storage_service()
        memory = get_memory_service()
        
        # Check all services
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "services": {
                "api": {
                    "status": "healthy",
                    "message": "API is running"
                },
                "database": {
                    "status": "healthy" if check_database_connection() else "unhealthy",
                    "message": "Database connectivity check"
                },
                "redis": {
                    "status": "healthy" if redis.is_available() else "unhealthy", 
                    "info": redis.get_connection_info()
                },
                "storage": {
                    "status": "healthy" if storage.is_available() else "unhealthy",
                    "stats": storage.get_storage_stats()
                },
                "memory_service": {
                    "status": "healthy" if memory.is_available() else "unhealthy",
                    "stats": memory.get_memory_stats()
                },
                "monitoring": {
                    "status": "healthy" if monitoring.is_enabled() else "degraded",
                    "enabled": monitoring.is_enabled()
                }
            },
            "system_metrics": monitoring.get_system_metrics() if monitoring.is_enabled() else {}
        }
        
        # Determine overall status
        unhealthy_services = [
            service for service, info in health_status["services"].items()
            if info["status"] == "unhealthy"
        ]
        
        if unhealthy_services:
            health_status["overall_status"] = "degraded"
            health_status["issues"] = unhealthy_services
        
        # Return appropriate HTTP status
        status_code = 200 if health_status["overall_status"] == "healthy" else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
        )


@router.get("/monitoring/metrics")
async def get_performance_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours (max 7 days)")
) -> Dict[str, Any]:
    """Get performance metrics for the specified time range."""
    try:
        monitoring = get_monitoring_service()
        
        if not monitoring.is_enabled():
            raise HTTPException(
                status_code=503,
                detail="Monitoring service is not enabled"
            )
        
        metrics = monitoring.get_performance_summary(time_range_hours=hours)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_range_hours": hours,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/monitoring/costs")
async def get_cost_metrics(
    days: int = Query(default=7, ge=1, le=30, description="Time range in days (max 30 days)")
) -> Dict[str, Any]:
    """Get cost metrics and usage statistics."""
    try:
        monitoring = get_monitoring_service()
        
        if not monitoring.is_enabled():
            raise HTTPException(
                status_code=503,
                detail="Monitoring service is not enabled"
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Export cost-related metrics
        cost_metrics = monitoring.export_metrics(
            start_time=start_date,
            end_time=end_date,
            metric_types=["llm_cost", "api_request"]
        )
        
        # Aggregate costs
        total_cost = 0.0
        total_requests = 0
        model_costs = {}
        
        for metric in cost_metrics:
            if metric["type"] == "llm_cost":
                cost = metric["data"].get("cost_usd", 0)
                total_cost += cost
                
                model = metric["data"].get("model_name", "unknown")
                if model not in model_costs:
                    model_costs[model] = {"cost": 0, "tokens": 0}
                model_costs[model]["cost"] += cost
                model_costs[model]["tokens"] += metric["data"].get("total_tokens", 0)
                
            elif metric["type"] == "api_request":
                total_requests += 1
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_range_days": days,
            "cost_summary": {
                "total_cost_usd": round(total_cost, 4),
                "total_requests": total_requests,
                "average_cost_per_request": round(total_cost / total_requests, 6) if total_requests > 0 else 0,
                "cost_by_model": model_costs
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cost metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cost metrics: {str(e)}"
        )


@router.get("/monitoring/errors")
async def get_error_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of errors to return")
) -> Dict[str, Any]:
    """Get error metrics and recent error logs."""
    try:
        monitoring = get_monitoring_service()
        
        if not monitoring.is_enabled():
            raise HTTPException(
                status_code=503,
                detail="Monitoring service is not enabled"
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours)
        
        # Export error metrics
        error_metrics = monitoring.export_metrics(
            start_time=start_date,
            end_time=end_date,
            metric_types=["error_occurrence", "rate_limit"]
        )
        
        # Sort by timestamp (most recent first)
        error_metrics.sort(
            key=lambda x: x["data"]["timestamp"], 
            reverse=True
        )
        
        # Limit results
        error_metrics = error_metrics[:limit]
        
        # Categorize errors
        error_categories = {}
        for error in error_metrics:
            error_type = error["data"].get("error_type", "unknown")
            if error_type not in error_categories:
                error_categories[error_type] = 0
            error_categories[error_type] += 1
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_range_hours": hours,
            "error_summary": {
                "total_errors": len(error_metrics),
                "error_categories": error_categories
            },
            "recent_errors": error_metrics,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting error metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get error metrics: {str(e)}"
        )


@router.get("/monitoring/storage")
async def get_storage_metrics() -> Dict[str, Any]:
    """Get storage usage metrics and statistics."""
    try:
        storage = get_storage_service()
        
        if not storage.is_available():
            raise HTTPException(
                status_code=503,
                detail="Storage service is not available"
            )
        
        stats = storage.get_storage_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "storage_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting storage metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage metrics: {str(e)}"
        )


@router.post("/monitoring/cleanup")
async def cleanup_old_data(
    days_old: int = Query(default=90, ge=30, le=365, description="Age threshold in days")
) -> Dict[str, Any]:
    """Clean up old monitoring data and artifacts."""
    try:
        monitoring = get_monitoring_service()
        storage = get_storage_service()
        memory = get_memory_service()
        
        cleanup_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "days_old": days_old,
            "results": {}
        }
        
        # Cleanup monitoring metrics
        if monitoring.is_enabled():
            metrics_flushed = monitoring.flush_metrics_buffer()
            cleanup_results["results"]["monitoring"] = {
                "metrics_flushed": metrics_flushed
            }
        
        # Cleanup storage artifacts
        if storage.is_available():
            storage_cleanup = storage.cleanup_old_artifacts(days_old=days_old)
            cleanup_results["results"]["storage"] = storage_cleanup
        
        # Cleanup memory service
        if memory.is_available():
            memory_cleanup = memory.cleanup_old_memories(days_old=days_old)
            cleanup_results["results"]["memory"] = memory_cleanup
        
        return cleanup_results
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard() -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data."""
    try:
        monitoring = get_monitoring_service()
        redis = get_redis_service()
        storage = get_storage_service()
        
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "services": {},
            "metrics": {},
            "alerts": []
        }
        
        # Service status
        dashboard_data["services"] = {
            "database": {"status": "healthy" if check_database_connection() else "unhealthy"},
            "redis": {"status": "healthy" if redis.is_available() else "unhealthy"},
            "storage": {"status": "healthy" if storage.is_available() else "unhealthy"},
            "monitoring": {"status": "healthy" if monitoring.is_enabled() else "degraded"}
        }
        
        # Performance metrics
        if monitoring.is_enabled():
            dashboard_data["metrics"] = monitoring.get_performance_summary(time_range_hours=1)
            dashboard_data["system"] = monitoring.get_system_metrics()
        
        # Check for alerts using alerting service
        alerting = get_alerting_service()
        alerts = []
        
        if monitoring.is_enabled():
            # Check performance thresholds
            metrics = monitoring.get_performance_summary(time_range_hours=1)
            performance_alerts = alerting.check_performance_thresholds(metrics)
            
            # Check service health
            service_alerts = alerting.check_service_health(dashboard_data["services"])
            
            # Get active alerts for dashboard
            active_alerts = alerting.get_active_alerts()
            
            # Format alerts for dashboard
            for alert in active_alerts:
                alerts.append({
                    "level": alert["level"],
                    "message": alert["message"],
                    "timestamp": alert["timestamp"],
                    "alert_type": alert["alert_type"]
                })
        
        dashboard_data["alerts"] = alerts
        
        # Overall status
        if any(alert["level"] == "error" for alert in alerts):
            dashboard_data["status"] = "error"
        elif alerts:
            dashboard_data["status"] = "warning"
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/monitoring/alerts")
async def get_alerts(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    active_only: bool = Query(default=False, description="Show only active alerts")
) -> Dict[str, Any]:
    """Get alerts for the specified time range."""
    try:
        alerting = get_alerting_service()
        
        if active_only:
            alerts = alerting.get_active_alerts()
        else:
            alerts = alerting.get_alert_history(hours=hours)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_range_hours": hours,
            "active_only": active_only,
            "alert_count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_message: str = Query(default="", description="Optional resolution message")
) -> Dict[str, Any]:
    """Resolve an active alert."""
    try:
        alerting = get_alerting_service()
        
        success = alerting.resolve_alert(alert_id, resolution_message)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Alert not found or already resolved"
            )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_id": alert_id,
            "status": "resolved",
            "message": "Alert resolved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve alert: {str(e)}"
        )


@router.post("/monitoring/alerts/test")
async def test_alert_system() -> Dict[str, Any]:
    """Test the alerting system by creating a test alert."""
    try:
        alerting = get_alerting_service()
        
        from ..services.alerting_service import AlertType, AlertLevel
        
        alert_id = alerting.create_alert(
            alert_type=AlertType.SYSTEM_RESOURCE,
            level=AlertLevel.INFO,
            title="Test Alert",
            message="This is a test alert to verify the alerting system is working correctly.",
            metadata={"test": True, "created_by": "monitoring_api"},
            auto_send=True
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_id": alert_id,
            "status": "created",
            "message": "Test alert created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating test alert: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create test alert: {str(e)}"
        )


@router.get("/monitoring/analytics/platform")
async def get_platform_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Time range in days")
) -> Dict[str, Any]:
    """Get platform-wide analytics and usage statistics."""
    try:
        analytics = get_analytics_service()
        
        platform_data = analytics.get_platform_analytics(days=days)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "platform_analytics": platform_data
        }
        
    except Exception as e:
        logger.error(f"Error getting platform analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get platform analytics: {str(e)}"
        )


@router.get("/monitoring/analytics/user/{user_id}")
async def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """Get analytics for a specific user."""
    try:
        analytics = get_analytics_service()
        
        user_data = analytics.get_user_analytics(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="User analytics not found"
            )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "user_analytics": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user analytics: {str(e)}"
        )


@router.get("/monitoring/analytics/cohorts")
async def get_cohort_analysis(
    days: int = Query(default=30, ge=1, le=365, description="Time range in days")
) -> Dict[str, Any]:
    """Get user cohort analysis and retention metrics."""
    try:
        analytics = get_analytics_service()
        
        cohort_data = analytics.get_user_cohort_analysis(days=days)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cohort_analysis": cohort_data
        }
        
    except Exception as e:
        logger.error(f"Error getting cohort analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cohort analysis: {str(e)}"
        )


@router.post("/monitoring/analytics/cleanup")
async def cleanup_analytics_data(
    days_old: int = Query(default=90, ge=30, le=365, description="Age threshold in days")
) -> Dict[str, Any]:
    """Clean up old analytics data."""
    try:
        analytics = get_analytics_service()
        
        cleaned_count = analytics.cleanup_old_data(days_old=days_old)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "days_old": days_old,
            "records_cleaned": cleaned_count,
            "message": f"Cleaned up {cleaned_count} old analytics records"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up analytics data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clean up analytics data: {str(e)}"
        )


@router.get("/monitoring/logs/summary")
async def get_log_summary(
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours")
) -> Dict[str, Any]:
    """Get summary of log activity for the specified time range."""
    try:
        log_service = get_log_service()
        
        summary = log_service.get_log_summary(hours=hours)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "log_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting log summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get log summary: {str(e)}"
        )


@router.get("/monitoring/logs/search")
async def search_logs(
    query: str = Query(..., description="Search query"),
    level: Optional[str] = Query(default=None, description="Log level filter"),
    logger_name: Optional[str] = Query(default=None, description="Logger name filter"),
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results")
) -> Dict[str, Any]:
    """Search logs based on query parameters."""
    try:
        log_service = get_log_service()
        
        results = log_service.search_logs(
            query=query,
            level=level,
            logger=logger_name,
            hours=hours,
            limit=limit
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "search_params": {
                "query": query,
                "level": level,
                "logger": logger_name,
                "hours": hours,
                "limit": limit
            },
            "result_count": len(results),
            "logs": results
        }
        
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search logs: {str(e)}"
        )


@router.get("/monitoring/logs/analytics")
async def get_log_analytics() -> Dict[str, Any]:
    """Get analytics about log patterns and issues."""
    try:
        log_service = get_log_service()
        
        analytics = log_service.get_log_analytics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "log_analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting log analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get log analytics: {str(e)}"
        )


@router.post("/monitoring/logs/export")
async def export_logs(
    start_time: str = Query(..., description="Start time (ISO format)"),
    end_time: str = Query(..., description="End time (ISO format)"),
    output_file: Optional[str] = Query(default=None, description="Output file path")
) -> Dict[str, Any]:
    """Export logs for the specified time range."""
    try:
        log_service = get_log_service()
        
        # Parse datetime strings
        start_dt = datetime.fromisoformat(start_time.replace("Z", ""))
        end_dt = datetime.fromisoformat(end_time.replace("Z", ""))
        
        exported_file = log_service.export_logs(
            start_time=start_dt,
            end_time=end_dt,
            output_file=output_file
        )
        
        if not exported_file:
            raise HTTPException(
                status_code=500,
                detail="Failed to export logs"
            )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "exported_file": exported_file,
            "start_time": start_time,
            "end_time": end_time,
            "message": "Logs exported successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid datetime format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error exporting logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export logs: {str(e)}"
        )


@router.post("/monitoring/logs/cleanup")
async def cleanup_old_logs(
    days_old: int = Query(default=30, ge=7, le=365, description="Age threshold in days")
) -> Dict[str, Any]:
    """Clean up old log files."""
    try:
        log_service = get_log_service()
        
        cleaned_count = log_service.cleanup_old_logs(days_old=days_old)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "days_old": days_old,
            "files_cleaned": cleaned_count,
            "message": f"Cleaned up {cleaned_count} old log files"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clean up logs: {str(e)}"
        )