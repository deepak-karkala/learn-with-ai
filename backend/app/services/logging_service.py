"""
Centralized logging service with structured logging and log aggregation.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Create base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add thread/process info if available
        if hasattr(record, 'process'):
            log_entry["process_id"] = record.process
        if hasattr(record, 'thread'):
            log_entry["thread_id"] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add custom fields from extra
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class LogAggregationService:
    """Service for centralized log aggregation and analysis."""
    
    def __init__(self):
        self._log_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 1000
        self._log_file_path = None
        self._setup_structured_logging()
        
        # Initialize log analysis counters
        self._error_counts = {}
        self._warning_counts = {}
        self._info_counts = {}
        
        logger = logging.getLogger(__name__)
        logger.info("Log aggregation service initialized")
    
    def _setup_structured_logging(self) -> None:
        """Set up structured logging configuration."""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Set up log file path
            self._log_file_path = logs_dir / f"app_{datetime.utcnow().strftime('%Y%m%d')}.log"
            
            # Create structured formatter
            formatter = StructuredFormatter()
            
            # Set up file handler for structured logs
            file_handler = logging.FileHandler(self._log_file_path)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            
            # Set up console handler for development
            console_handler = logging.StreamHandler(sys.stdout)
            if os.getenv("ENVIRONMENT") == "production":
                # Use structured logging in production
                console_handler.setFormatter(formatter)
            else:
                # Use readable logging in development
                console_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            console_handler.setLevel(logging.INFO)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            
            # Remove existing handlers to avoid duplicates
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Add our handlers
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            # Configure specific loggers
            self._configure_app_loggers()
            
        except Exception as e:
            print(f"Error setting up structured logging: {e}")
    
    def _configure_app_loggers(self) -> None:
        """Configure application-specific loggers."""
        # Configure app loggers
        app_loggers = [
            "app.services",
            "app.api", 
            "app.main",
            "app.models",
            "app.database"
        ]
        
        for logger_name in app_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            # Prevent propagation to avoid duplicate logs
            logger.propagate = True
        
        # Configure third-party loggers to reduce noise
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("google").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
    
    def add_log_entry(self, log_data: Dict[str, Any]) -> None:
        """Add a log entry to the aggregation buffer."""
        try:
            # Add timestamp if not present
            if "timestamp" not in log_data:
                log_data["timestamp"] = datetime.utcnow().isoformat()
            
            # Add to buffer
            self._log_buffer.append(log_data)
            
            # Update counters
            level = log_data.get("level", "").lower()
            if level == "error":
                self._error_counts[log_data.get("logger", "unknown")] = \
                    self._error_counts.get(log_data.get("logger", "unknown"), 0) + 1
            elif level == "warning":
                self._warning_counts[log_data.get("logger", "unknown")] = \
                    self._warning_counts.get(log_data.get("logger", "unknown"), 0) + 1
            elif level == "info":
                self._info_counts[log_data.get("logger", "unknown")] = \
                    self._info_counts.get(log_data.get("logger", "unknown"), 0) + 1
            
            # Flush buffer if it gets too large
            if len(self._log_buffer) >= self._max_buffer_size:
                self._flush_log_buffer()
            
        except Exception as e:
            # Use print to avoid logging recursion
            print(f"Error adding log entry: {e}")
    
    def _flush_log_buffer(self) -> None:
        """Flush the log buffer to persistent storage."""
        try:
            if not self._log_buffer:
                return
            
            # Write buffered logs to file
            if self._log_file_path:
                with open(self._log_file_path, 'a') as f:
                    for log_entry in self._log_buffer:
                        f.write(json.dumps(log_entry, default=str) + '\n')
            
            # Clear buffer
            self._log_buffer.clear()
            
        except Exception as e:
            print(f"Error flushing log buffer: {e}")
    
    def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of log activity for the specified time range."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            
            # Filter recent logs
            recent_logs = [
                log for log in self._log_buffer
                if datetime.fromisoformat(log["timestamp"].replace("Z", "")).timestamp() > cutoff_time
            ]
            
            # Count by level
            level_counts = {}
            for log in recent_logs:
                level = log.get("level", "unknown")
                level_counts[level] = level_counts.get(level, 0) + 1
            
            # Count by logger
            logger_counts = {}
            for log in recent_logs:
                logger = log.get("logger", "unknown")
                logger_counts[logger] = logger_counts.get(logger, 0) + 1
            
            # Get top error messages
            error_logs = [log for log in recent_logs if log.get("level") == "ERROR"]
            error_messages = {}
            for log in error_logs:
                message = log.get("message", "")[:100]  # Truncate for grouping
                error_messages[message] = error_messages.get(message, 0) + 1
            
            top_errors = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "time_range_hours": hours,
                "total_logs": len(recent_logs),
                "level_counts": level_counts,
                "logger_counts": logger_counts,
                "top_errors": dict(top_errors),
                "buffer_size": len(self._log_buffer),
                "summary_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting log summary: {e}")
            return {}
    
    def search_logs(
        self,
        query: str,
        level: Optional[str] = None,
        logger: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search logs based on query parameters."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            
            # Filter logs
            filtered_logs = []
            for log in self._log_buffer:
                # Time filter
                if datetime.fromisoformat(log["timestamp"].replace("Z", "")).timestamp() <= cutoff_time:
                    continue
                
                # Level filter
                if level and log.get("level", "").lower() != level.lower():
                    continue
                
                # Logger filter
                if logger and logger.lower() not in log.get("logger", "").lower():
                    continue
                
                # Query filter (search in message)
                if query and query.lower() not in log.get("message", "").lower():
                    continue
                
                filtered_logs.append(log)
            
            # Sort by timestamp (most recent first)
            filtered_logs.sort(
                key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "")),
                reverse=True
            )
            
            # Limit results
            return filtered_logs[:limit]
            
        except Exception as e:
            print(f"Error searching logs: {e}")
            return []
    
    def get_log_analytics(self) -> Dict[str, Any]:
        """Get analytics about log patterns and issues."""
        try:
            return {
                "error_counts_by_logger": dict(self._error_counts),
                "warning_counts_by_logger": dict(self._warning_counts),
                "info_counts_by_logger": dict(self._info_counts),
                "total_errors": sum(self._error_counts.values()),
                "total_warnings": sum(self._warning_counts.values()),
                "total_info": sum(self._info_counts.values()),
                "buffer_size": len(self._log_buffer),
                "log_file_path": str(self._log_file_path) if self._log_file_path else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting log analytics: {e}")
            return {}
    
    def cleanup_old_logs(self, days_old: int = 30) -> int:
        """Clean up old log files."""
        try:
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return 0
            
            cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 3600)
            cleaned_count = 0
            
            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")
            return 0
    
    def export_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        output_file: Optional[str] = None
    ) -> str:
        """Export logs for the specified time range."""
        try:
            # Filter logs by time range
            filtered_logs = []
            for log in self._log_buffer:
                log_time = datetime.fromisoformat(log["timestamp"].replace("Z", ""))
                if start_time <= log_time <= end_time:
                    filtered_logs.append(log)
            
            # Sort by timestamp
            filtered_logs.sort(
                key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", ""))
            )
            
            # Generate output file name if not provided
            if not output_file:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                output_file = f"logs/exported_logs_{timestamp}.json"
            
            # Ensure logs directory exists
            Path(output_file).parent.mkdir(exist_ok=True)
            
            # Write logs to file
            with open(output_file, 'w') as f:
                json.dump(filtered_logs, f, indent=2, default=str)
            
            return output_file
            
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return ""


# Global log aggregation service instance
_log_service: Optional[LogAggregationService] = None


def get_log_service() -> LogAggregationService:
    """Get the global log aggregation service instance."""
    global _log_service
    if _log_service is None:
        _log_service = LogAggregationService()
    return _log_service


def init_logging() -> None:
    """Initialize log aggregation service."""
    global _log_service
    _log_service = LogAggregationService()


# Custom logging functions with structured data
def log_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    response_time: float,
    user_id: Optional[str] = None
) -> None:
    """Log API request with structured data."""
    logger = logging.getLogger("app.api.requests")
    logger.info(
        f"{method} {endpoint} - {status_code} - {response_time:.3f}s",
        extra={
            "event_type": "api_request",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id
        }
    )


def log_llm_interaction(
    model_name: str,
    operation: str,
    tokens_used: int,
    cost: float,
    user_id: str,
    session_id: str
) -> None:
    """Log LLM interaction with structured data."""
    logger = logging.getLogger("app.services.llm")
    logger.info(
        f"LLM {operation}: {model_name} - {tokens_used} tokens - ${cost:.4f}",
        extra={
            "event_type": "llm_interaction",
            "model_name": model_name,
            "operation": operation,
            "tokens_used": tokens_used,
            "cost_usd": cost,
            "user_id": user_id,
            "session_id": session_id
        }
    )


def log_business_event(
    event_type: str,
    event_data: Dict[str, Any],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> None:
    """Log business events with structured data."""
    logger = logging.getLogger("app.business.events")
    logger.info(
        f"Business event: {event_type}",
        extra={
            "event_type": "business_event",
            "business_event_type": event_type,
            "event_data": event_data,
            "user_id": user_id,
            "session_id": session_id
        }
    )