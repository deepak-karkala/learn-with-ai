"""
Alerting service for critical system issues and monitoring notifications.
"""

import logging
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"  
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_RESPONSE = "slow_response"
    SERVICE_DOWN = "service_down"
    HIGH_COST = "high_cost"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SYSTEM_RESOURCE = "system_resource"
    AUTHENTICATION_FAILURE = "auth_failure"


@dataclass
class Alert:
    """Alert data structure."""
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class AlertingService:
    """Service for managing alerts and notifications."""
    
    def __init__(self):
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._email_enabled = False
        self._smtp_config = {}
        self._alert_recipients = []
        self._alert_thresholds = {
            "error_rate_percent": 5.0,
            "response_time_seconds": 3.0,
            "cost_threshold_usd": 10.0,
            "cpu_threshold_percent": 80.0,
            "memory_threshold_percent": 85.0,
            "disk_threshold_percent": 90.0
        }
        
        self._initialize_alerting()
    
    def _initialize_alerting(self) -> None:
        """Initialize alerting configuration."""
        try:
            # Email configuration
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            
            if smtp_username and smtp_password:
                self._smtp_config = {
                    "server": smtp_server,
                    "port": smtp_port,
                    "username": smtp_username,
                    "password": smtp_password
                }
                self._email_enabled = True
                logger.info("Email alerting configured")
            else:
                logger.warning("SMTP credentials not configured, email alerts disabled")
            
            # Alert recipients
            recipients = os.getenv("ALERT_RECIPIENTS", "")
            if recipients:
                self._alert_recipients = [email.strip() for email in recipients.split(",")]
                logger.info(f"Alert recipients configured: {len(self._alert_recipients)} recipients")
            
            # Custom thresholds
            for key, default_value in self._alert_thresholds.items():
                env_key = f"ALERT_THRESHOLD_{key.upper()}"
                env_value = os.getenv(env_key)
                if env_value:
                    try:
                        self._alert_thresholds[key] = float(env_value)
                    except ValueError:
                        logger.warning(f"Invalid threshold value for {env_key}: {env_value}")
            
            logger.info("Alerting service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize alerting service: {e}")
    
    def create_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        auto_send: bool = True
    ) -> str:
        """Create a new alert."""
        try:
            alert_id = f"{alert_type.value}_{int(datetime.utcnow().timestamp())}"
            
            alert = Alert(
                alert_type=alert_type,
                level=level,
                title=title,
                message=message,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Store alert
            self._active_alerts[alert_id] = alert
            self._alert_history.append(alert)
            
            logger.warning(f"Alert created: {level.value.upper()} - {title}")
            
            # Send notification if enabled
            if auto_send:
                self._send_alert_notification(alert)
            
            return alert_id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return ""
    
    def resolve_alert(self, alert_id: str, resolution_message: str = "") -> bool:
        """Resolve an active alert."""
        try:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.resolved = True
                alert.resolution_time = datetime.utcnow()
                
                if resolution_message:
                    alert.metadata["resolution_message"] = resolution_message
                
                # Remove from active alerts
                del self._active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {alert.title}")
                
                # Send resolution notification for critical alerts
                if alert.level == AlertLevel.CRITICAL:
                    self._send_resolution_notification(alert)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    def check_performance_thresholds(self, metrics: Dict[str, Any]) -> List[str]:
        """Check metrics against thresholds and create alerts if needed."""
        created_alerts = []
        
        try:
            # Error rate check
            error_rate = metrics.get("error_rate_percent", 0)
            if error_rate > self._alert_thresholds["error_rate_percent"]:
                alert_id = self.create_alert(
                    alert_type=AlertType.HIGH_ERROR_RATE,
                    level=AlertLevel.WARNING if error_rate < 10 else AlertLevel.ERROR,
                    title=f"High Error Rate: {error_rate:.1f}%",
                    message=f"Error rate ({error_rate:.1f}%) exceeds threshold ({self._alert_thresholds['error_rate_percent']:.1f}%)",
                    metadata={"error_rate": error_rate, "threshold": self._alert_thresholds["error_rate_percent"]}
                )
                created_alerts.append(alert_id)
            
            # Response time check
            avg_response_time = metrics.get("average_response_time", 0)
            if avg_response_time > self._alert_thresholds["response_time_seconds"]:
                alert_id = self.create_alert(
                    alert_type=AlertType.SLOW_RESPONSE,
                    level=AlertLevel.WARNING if avg_response_time < 5 else AlertLevel.ERROR,
                    title=f"Slow Response Time: {avg_response_time:.2f}s",
                    message=f"Average response time ({avg_response_time:.2f}s) exceeds threshold ({self._alert_thresholds['response_time_seconds']:.1f}s)",
                    metadata={"response_time": avg_response_time, "threshold": self._alert_thresholds["response_time_seconds"]}
                )
                created_alerts.append(alert_id)
            
            # Cost monitoring
            total_cost = metrics.get("total_cost_usd", 0)
            if total_cost > self._alert_thresholds["cost_threshold_usd"]:
                alert_id = self.create_alert(
                    alert_type=AlertType.HIGH_COST,
                    level=AlertLevel.WARNING,
                    title=f"High API Costs: ${total_cost:.2f}",
                    message=f"Total API costs (${total_cost:.2f}) exceed threshold (${self._alert_thresholds['cost_threshold_usd']:.2f})",
                    metadata={"total_cost": total_cost, "threshold": self._alert_thresholds["cost_threshold_usd"]}
                )
                created_alerts.append(alert_id)
            
            # System resource checks
            system_metrics = metrics.get("system_metrics", {})
            if system_metrics:
                # CPU usage
                cpu_percent = system_metrics.get("cpu_percent", 0)
                if cpu_percent > self._alert_thresholds["cpu_threshold_percent"]:
                    alert_id = self.create_alert(
                        alert_type=AlertType.SYSTEM_RESOURCE,
                        level=AlertLevel.WARNING,
                        title=f"High CPU Usage: {cpu_percent:.1f}%",
                        message=f"CPU usage ({cpu_percent:.1f}%) exceeds threshold ({self._alert_thresholds['cpu_threshold_percent']:.1f}%)",
                        metadata={"cpu_percent": cpu_percent, "threshold": self._alert_thresholds["cpu_threshold_percent"]}
                    )
                    created_alerts.append(alert_id)
                
                # Memory usage
                memory_percent = system_metrics.get("memory_percent", 0)
                if memory_percent > self._alert_thresholds["memory_threshold_percent"]:
                    alert_id = self.create_alert(
                        alert_type=AlertType.SYSTEM_RESOURCE,
                        level=AlertLevel.WARNING,
                        title=f"High Memory Usage: {memory_percent:.1f}%",
                        message=f"Memory usage ({memory_percent:.1f}%) exceeds threshold ({self._alert_thresholds['memory_threshold_percent']:.1f}%)",
                        metadata={"memory_percent": memory_percent, "threshold": self._alert_thresholds["memory_threshold_percent"]}
                    )
                    created_alerts.append(alert_id)
                
                # Disk usage
                disk_percent = system_metrics.get("disk_percent", 0)
                if disk_percent > self._alert_thresholds["disk_threshold_percent"]:
                    alert_id = self.create_alert(
                        alert_type=AlertType.SYSTEM_RESOURCE,
                        level=AlertLevel.ERROR,
                        title=f"High Disk Usage: {disk_percent:.1f}%",
                        message=f"Disk usage ({disk_percent:.1f}%) exceeds threshold ({self._alert_thresholds['disk_threshold_percent']:.1f}%)",
                        metadata={"disk_percent": disk_percent, "threshold": self._alert_thresholds["disk_threshold_percent"]}
                    )
                    created_alerts.append(alert_id)
            
            return created_alerts
            
        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")
            return []
    
    def check_service_health(self, service_statuses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Check service health and create alerts for unhealthy services."""
        created_alerts = []
        
        try:
            for service_name, status_info in service_statuses.items():
                status = status_info.get("status", "unknown")
                
                if status == "unhealthy":
                    alert_id = self.create_alert(
                        alert_type=AlertType.SERVICE_DOWN,
                        level=AlertLevel.CRITICAL,
                        title=f"Service Down: {service_name}",
                        message=f"Service {service_name} is reporting unhealthy status",
                        metadata={"service": service_name, "status_info": status_info}
                    )
                    created_alerts.append(alert_id)
                elif status == "degraded":
                    alert_id = self.create_alert(
                        alert_type=AlertType.SERVICE_DOWN,
                        level=AlertLevel.WARNING,
                        title=f"Service Degraded: {service_name}",
                        message=f"Service {service_name} is reporting degraded status",
                        metadata={"service": service_name, "status_info": status_info}
                    )
                    created_alerts.append(alert_id)
            
            return created_alerts
            
        except Exception as e:
            logger.error(f"Error checking service health: {e}")
            return []
    
    def _send_alert_notification(self, alert: Alert) -> None:
        """Send alert notification via email."""
        try:
            if not self._email_enabled or not self._alert_recipients:
                return
            
            # Skip sending for low-priority alerts unless they're critical
            if alert.level == AlertLevel.INFO:
                return
            
            subject = f"[{alert.level.value.upper()}] {alert.title}"
            
            # Create email content
            body = f"""
Alert Details:
=============
Type: {alert.alert_type.value}
Level: {alert.level.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

Metadata:
{self._format_metadata(alert.metadata)}

---
AI System Design Learning Platform Monitoring
"""
            
            self._send_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
    
    def _send_resolution_notification(self, alert: Alert) -> None:
        """Send alert resolution notification."""
        try:
            if not self._email_enabled or not self._alert_recipients:
                return
            
            subject = f"[RESOLVED] {alert.title}"
            
            body = f"""
Alert Resolved:
==============
Original Alert: {alert.title}
Resolved Time: {alert.resolution_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
Duration: {(alert.resolution_time - alert.timestamp).total_seconds() / 60:.1f} minutes

Resolution Message:
{alert.metadata.get('resolution_message', 'Alert automatically resolved')}

---
AI System Design Learning Platform Monitoring
"""
            
            self._send_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending resolution notification: {e}")
    
    def _send_email(self, subject: str, body: str) -> None:
        """Send email using SMTP configuration."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self._smtp_config["username"]
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self._smtp_config["server"], self._smtp_config["port"]) as server:
                server.starttls()
                server.login(self._smtp_config["username"], self._smtp_config["password"])
                
                # Send to all recipients
                for recipient in self._alert_recipients:
                    msg['To'] = recipient
                    server.send_message(msg)
                    del msg['To']
            
            logger.info(f"Alert email sent to {len(self._alert_recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for email display."""
        if not metadata:
            return "None"
        
        formatted = []
        for key, value in metadata.items():
            formatted.append(f"  {key}: {value}")
        
        return "\n".join(formatted)
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return [asdict(alert) for alert in self._active_alerts.values()]
    
    def get_alert_history(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alert history for the specified time range."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            filtered_alerts = [
                alert for alert in self._alert_history
                if alert.timestamp >= cutoff_time
            ]
            
            # Sort by timestamp (most recent first)
            filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Limit results
            filtered_alerts = filtered_alerts[:limit]
            
            return [asdict(alert) for alert in filtered_alerts]
            
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []
    
    def cleanup_old_alerts(self, days_old: int = 30) -> int:
        """Clean up old alerts from history."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            
            original_count = len(self._alert_history)
            self._alert_history = [
                alert for alert in self._alert_history
                if alert.timestamp >= cutoff_time
            ]
            
            cleaned_count = original_count - len(self._alert_history)
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old alerts")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {e}")
            return 0
    
    def is_enabled(self) -> bool:
        """Check if alerting is enabled."""
        return self._email_enabled or bool(self._alert_recipients)


# Global alerting service instance
_alerting_service: Optional[AlertingService] = None


def get_alerting_service() -> AlertingService:
    """Get the global alerting service instance."""
    global _alerting_service
    if _alerting_service is None:
        _alerting_service = AlertingService()
    return _alerting_service


def init_alerting() -> None:
    """Initialize alerting service."""
    global _alerting_service
    _alerting_service = AlertingService()
    logger.info("Alerting service initialized")