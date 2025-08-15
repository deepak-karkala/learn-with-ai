"""
Monitoring and observability service with Comet Opik integration for production.
"""

import json
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from functools import wraps
from contextlib import contextmanager

try:
    import psutil
except ImportError:
    psutil = None

try:
    from opik import Opik, track
    from opik.api_objects import span, trace
except ImportError:
    Opik = None
    track = None
    span = None
    trace = None

logger = logging.getLogger(__name__)


class MonitoringService:
    """Comprehensive monitoring service with Comet Opik integration."""
    
    def __init__(self):
        self._opik_client: Optional[Opik] = None
        self._enabled = False
        self._metrics_buffer: List[Dict[str, Any]] = []
        self._error_buffer: List[Dict[str, Any]] = []
        self._performance_metrics: Dict[str, List[float]] = {}
        
        self._initialize_monitoring()
    
    def _initialize_monitoring(self) -> None:
        """Initialize monitoring services."""
        try:
            # Initialize Comet Opik
            if Opik is not None:
                opik_api_key = os.getenv("OPIK_API_KEY")
                opik_project = os.getenv("OPIK_PROJECT_NAME", "systemdesign-ai-production")
                opik_workspace = os.getenv("OPIK_WORKSPACE")
                
                if opik_api_key:
                    self._opik_client = Opik(
                        api_key=opik_api_key,
                        project_name=opik_project,
                        workspace=opik_workspace
                    )
                    self._enabled = True
                    logger.info("Comet Opik monitoring initialized successfully")
                else:
                    logger.warning("OPIK_API_KEY not configured, monitoring features will be limited")
            else:
                logger.warning("Opik package not available, monitoring features will be limited")
            
            # Set up system monitoring
            self._setup_system_monitoring()
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}")
            self._enabled = False
    
    def _setup_system_monitoring(self) -> None:
        """Set up system-level monitoring."""
        try:
            # Initialize performance tracking
            self._performance_metrics = {
                "cpu_usage": [],
                "memory_usage": [],
                "response_times": [],
                "request_counts": [],
                "error_rates": []
            }
            
            logger.info("System monitoring setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up system monitoring: {e}")
    
    def is_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self._enabled
    
    # =============================================================================
    # LLM Call Tracking
    # =============================================================================
    
    @contextmanager
    def track_llm_call(
        self,
        operation_name: str,
        model_name: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracking LLM calls."""
        start_time = time.time()
        operation_metadata = {
            "model_name": model_name,
            "user_id": user_id,
            "session_id": session_id,
            "operation_name": operation_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            operation_metadata.update(metadata)
        
        try:
            if self._enabled and self._opik_client:
                # Start Opik trace
                with self._opik_client.trace(
                    name=operation_name,
                    metadata=operation_metadata
                ) as opik_trace:
                    yield {
                        "trace": opik_trace,
                        "start_time": start_time,
                        "metadata": operation_metadata
                    }
            else:
                # Fallback tracking
                yield {
                    "trace": None,
                    "start_time": start_time,
                    "metadata": operation_metadata
                }
                
        except Exception as e:
            # Track error
            self.track_error(
                error=e,
                context=operation_name,
                user_id=user_id,
                session_id=session_id,
                metadata=operation_metadata
            )
            raise
        finally:
            # Track completion metrics
            duration = time.time() - start_time
            self._track_operation_completion(
                operation_name=operation_name,
                duration=duration,
                metadata=operation_metadata
            )
    
    def track_chat_interaction(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        ai_response: str,
        model_name: str,
        response_time: float,
        token_usage: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None
    ) -> None:
        """Track chat interactions."""
        try:
            interaction_data = {
                "user_id": user_id,
                "session_id": session_id,
                "user_message_length": len(user_message),
                "ai_response_length": len(ai_response),
                "model_name": model_name,
                "response_time": response_time,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": token_usage or {},
                "cost": cost
            }
            
            if self._enabled and self._opik_client:
                # Log to Opik
                with self._opik_client.trace(name="chat_interaction") as trace:
                    trace.log(
                        input=user_message[:500],  # Truncate for privacy
                        output=ai_response[:500],
                        metadata=interaction_data
                    )
            
            # Store in local buffer
            self._metrics_buffer.append({
                "type": "chat_interaction",
                "data": interaction_data
            })
            
            # Update performance metrics
            self._performance_metrics["response_times"].append(response_time)
            self._performance_metrics["request_counts"].append(1)
            
            logger.debug(f"Chat interaction tracked for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking chat interaction: {e}")
    
    def track_assessment(
        self,
        user_id: str,
        session_id: str,
        assessment_scores: Dict[str, float],
        overall_score: float,
        confidence_score: float,
        model_name: str,
        processing_time: float
    ) -> None:
        """Track assessment operations."""
        try:
            assessment_data = {
                "user_id": user_id,
                "session_id": session_id,
                "assessment_scores": assessment_scores,
                "overall_score": overall_score,
                "confidence_score": confidence_score,
                "model_name": model_name,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self._enabled and self._opik_client:
                with self._opik_client.trace(name="assessment_generation") as trace:
                    trace.log(
                        input=f"Assessment for session {session_id}",
                        output=f"Overall score: {overall_score}",
                        metadata=assessment_data
                    )
            
            self._metrics_buffer.append({
                "type": "assessment",
                "data": assessment_data
            })
            
            logger.debug(f"Assessment tracked for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking assessment: {e}")
    
    def track_whiteboard_analysis(
        self,
        user_id: str,
        session_id: str,
        image_size_bytes: int,
        analysis_result: Dict[str, Any],
        model_name: str,
        processing_time: float,
        cost: Optional[float] = None
    ) -> None:
        """Track whiteboard analysis operations."""
        try:
            analysis_data = {
                "user_id": user_id,
                "session_id": session_id,
                "image_size_bytes": image_size_bytes,
                "analysis_result_size": len(str(analysis_result)),
                "model_name": model_name,
                "processing_time": processing_time,
                "cost": cost,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self._enabled and self._opik_client:
                with self._opik_client.trace(name="whiteboard_analysis") as trace:
                    trace.log(
                        input=f"Whiteboard image ({image_size_bytes} bytes)",
                        output=str(analysis_result)[:500],
                        metadata=analysis_data
                    )
            
            self._metrics_buffer.append({
                "type": "whiteboard_analysis",
                "data": analysis_data
            })
            
            logger.debug(f"Whiteboard analysis tracked for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking whiteboard analysis: {e}")
    
    # =============================================================================
    # Error Tracking
    # =============================================================================
    
    def track_error(
        self,
        error: Exception,
        context: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track errors and exceptions."""
        try:
            error_data = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "traceback": traceback.format_exc()
            }
            
            if metadata:
                error_data["metadata"] = metadata
            
            if self._enabled and self._opik_client:
                with self._opik_client.trace(name="error_occurrence") as trace:
                    trace.log(
                        input=f"Error in {context}",
                        output=f"{type(error).__name__}: {str(error)}",
                        metadata=error_data
                    )
            
            self._error_buffer.append(error_data)
            
            # Also add to metrics buffer for performance summary
            self._metrics_buffer.append({
                "type": "error_occurrence",
                "data": error_data
            })
            
            # Update error rate metrics
            self._performance_metrics["error_rates"].append(1)
            
            logger.error(f"Error tracked: {error_data['error_type']} in {context}")
            
        except Exception as e:
            logger.error(f"Error tracking error (meta-error): {e}")
    
    def track_rate_limit_hit(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        current_count: int
    ) -> None:
        """Track rate limit violations."""
        try:
            rate_limit_data = {
                "user_id": user_id,
                "endpoint": endpoint,
                "limit": limit,
                "current_count": current_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self._enabled and self._opik_client:
                with self._opik_client.trace(name="rate_limit_hit") as trace:
                    trace.log(
                        input=f"Rate limit hit for {endpoint}",
                        output=f"User {user_id} exceeded {limit} requests",
                        metadata=rate_limit_data
                    )
            
            self._metrics_buffer.append({
                "type": "rate_limit",
                "data": rate_limit_data
            })
            
            logger.warning(f"Rate limit hit: {user_id} on {endpoint}")
            
        except Exception as e:
            logger.error(f"Error tracking rate limit: {e}")
    
    # =============================================================================
    # Performance Monitoring
    # =============================================================================
    
    def track_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ) -> None:
        """Track API request metrics."""
        try:
            request_data = {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time": response_time,
                "user_id": user_id,
                "request_size": request_size,
                "response_size": response_size,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self._enabled and self._opik_client:
                with self._opik_client.trace(name="api_request") as trace:
                    trace.log(
                        input=f"{method} {endpoint}",
                        output=f"Status: {status_code}, Time: {response_time:.3f}s",
                        metadata=request_data
                    )
            
            self._metrics_buffer.append({
                "type": "api_request",
                "data": request_data
            })
            
            # Update performance metrics
            self._performance_metrics["response_times"].append(response_time)
            if status_code >= 400:
                self._performance_metrics["error_rates"].append(1)
            
        except Exception as e:
            logger.error(f"Error tracking API request: {e}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            if psutil is None:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "psutil not available",
                    "cpu_percent": 0,
                    "memory_percent": 0,
                    "disk_percent": 0
                }
                
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            system_metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024),
                "process_memory_mb": process_memory.rss / (1024 * 1024),
                "process_cpu_percent": process.cpu_percent()
            }
            
            # Update local metrics
            self._performance_metrics["cpu_usage"].append(cpu_percent)
            self._performance_metrics["memory_usage"].append(memory.percent)
            
            return system_metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}
    
    def _track_operation_completion(
        self,
        operation_name: str,
        duration: float,
        metadata: Dict[str, Any]
    ) -> None:
        """Track completion of an operation."""
        try:
            completion_data = {
                "operation_name": operation_name,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
                **metadata
            }
            
            self._metrics_buffer.append({
                "type": "operation_completion",
                "data": completion_data
            })
            
        except Exception as e:
            logger.error(f"Error tracking operation completion: {e}")
    
    # =============================================================================
    # Cost Tracking
    # =============================================================================
    
    def track_llm_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        user_id: str,
        session_id: Optional[str] = None,
        operation_type: str = "chat"
    ) -> None:
        """Track LLM usage costs."""
        try:
            cost_data = {
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": cost_usd,
                "cost_per_token": cost_usd / (input_tokens + output_tokens) if (input_tokens + output_tokens) > 0 else 0,
                "user_id": user_id,
                "session_id": session_id,
                "operation_type": operation_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self._enabled and self._opik_client:
                with self._opik_client.trace(name="llm_cost_tracking") as trace:
                    trace.log(
                        input=f"Model: {model_name}, Tokens: {input_tokens + output_tokens}",
                        output=f"Cost: ${cost_usd:.4f}",
                        metadata=cost_data
                    )
            
            self._metrics_buffer.append({
                "type": "llm_cost",
                "data": cost_data
            })
            
            logger.debug(f"LLM cost tracked: ${cost_usd:.4f} for {model_name}")
            
        except Exception as e:
            logger.error(f"Error tracking LLM cost: {e}")
    
    # =============================================================================
    # Analytics and Reporting
    # =============================================================================
    
    def get_performance_summary(
        self,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance summary for the specified time range."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            # Filter metrics within time range
            filtered_metrics = []
            for metric in self._metrics_buffer:
                metric_time = datetime.fromisoformat(metric["data"]["timestamp"])
                if metric_time >= cutoff_time:
                    filtered_metrics.append(metric)
            
            # Calculate summary statistics
            total_requests = len([m for m in filtered_metrics if m["type"] in ["api_request", "chat_interaction"]])
            total_errors = len([m for m in filtered_metrics if m["type"] in ["error_occurrence", "rate_limit"]])
            total_cost = sum([
                m["data"].get("cost_usd", m["data"].get("cost", 0)) 
                for m in filtered_metrics 
                if m["type"] in ["llm_cost", "chat_interaction"] and (m["data"].get("cost_usd") or m["data"].get("cost"))
            ])
            
            response_times = [m["data"]["response_time"] for m in filtered_metrics if m["type"] in ["api_request", "chat_interaction"] and "response_time" in m["data"]]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "time_range_hours": time_range_hours,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate_percent": round(error_rate, 2),
                "average_response_time": round(avg_response_time, 3),
                "total_cost_usd": round(total_cost, 4),
                "system_metrics": self.get_system_metrics()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    def export_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        metric_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Export metrics for external analysis."""
        try:
            exported_metrics = []
            
            for metric in self._metrics_buffer:
                metric_time = datetime.fromisoformat(metric["data"]["timestamp"])
                
                if start_time <= metric_time <= end_time:
                    if not metric_types or metric["type"] in metric_types:
                        exported_metrics.append(metric)
            
            return exported_metrics
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return []
    
    def flush_metrics_buffer(self) -> int:
        """Flush metrics buffer and return number of metrics flushed."""
        try:
            count = len(self._metrics_buffer)
            self._metrics_buffer.clear()
            self._error_buffer.clear()
            
            # Keep only recent performance metrics
            for key in self._performance_metrics:
                self._performance_metrics[key] = self._performance_metrics[key][-1000:]  # Keep last 1000 entries
            
            logger.info(f"Flushed {count} metrics from buffer")
            return count
            
        except Exception as e:
            logger.error(f"Error flushing metrics buffer: {e}")
            return 0


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


def init_monitoring() -> None:
    """Initialize monitoring service."""
    global _monitoring_service
    _monitoring_service = MonitoringService()
    logger.info("Monitoring service initialized")


# Decorator for automatic API monitoring
def monitor_api_call(endpoint_name: str = None):
    """Decorator to automatically monitor API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitoring = get_monitoring_service()
            start_time = time.time()
            endpoint = endpoint_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                
                # Track successful call
                duration = time.time() - start_time
                monitoring.track_api_request(
                    endpoint=endpoint,
                    method="unknown",
                    status_code=200,
                    response_time=duration
                )
                
                return result
                
            except Exception as e:
                # Track error
                duration = time.time() - start_time
                monitoring.track_error(
                    error=e,
                    context=endpoint,
                    metadata={"duration": duration}
                )
                monitoring.track_api_request(
                    endpoint=endpoint,
                    method="unknown",
                    status_code=500,
                    response_time=duration
                )
                raise
                
        return wrapper
    return decorator