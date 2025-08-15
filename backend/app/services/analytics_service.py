"""
User analytics service for tracking user behavior and engagement.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import json

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """User session data."""
    user_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_messages: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    topics_discussed: List[str] = None
    assessment_count: int = 0
    whiteboard_count: int = 0
    diagram_count: int = 0
    errors_encountered: int = 0
    satisfaction_score: Optional[float] = None
    
    def __post_init__(self):
        if self.topics_discussed is None:
            self.topics_discussed = []


@dataclass
class UserAnalytics:
    """User analytics summary."""
    user_id: str
    total_sessions: int
    total_time_spent: float  # in seconds
    avg_session_duration: float
    total_messages: int
    avg_messages_per_session: float
    total_assessments: int
    avg_assessment_score: float
    improvement_trend: float  # positive = improving
    favorite_topics: List[str]
    engagement_score: float  # 0-100
    last_active: datetime
    streak_days: int
    preferred_time_slots: List[str]  # e.g., ["morning", "evening"]


class AnalyticsService:
    """Service for tracking and analyzing user behavior."""
    
    def __init__(self):
        self._user_sessions: Dict[str, UserSession] = {}
        self._session_history: List[UserSession] = []
        self._user_analytics: Dict[str, UserAnalytics] = {}
        self._interaction_buffer: List[Dict[str, Any]] = []
        
        self._topic_keywords = {
            "system_design": ["system", "design", "architecture", "scalability", "database", "api"],
            "microservices": ["microservice", "service", "container", "docker", "kubernetes"],
            "database": ["database", "sql", "nosql", "redis", "mongodb", "postgresql"],
            "caching": ["cache", "caching", "redis", "memcached", "cdn"],
            "messaging": ["queue", "kafka", "rabbitmq", "pubsub", "messaging"],
            "monitoring": ["monitoring", "logging", "metrics", "observability", "prometheus"],
            "security": ["security", "authentication", "authorization", "oauth", "jwt"],
            "performance": ["performance", "latency", "throughput", "optimization", "load"]
        }
        
        logger.info("Analytics service initialized")
    
    def start_session(self, user_id: str, session_id: str) -> None:
        """Start tracking a new user session."""
        try:
            session = UserSession(
                user_id=user_id,
                session_id=session_id,
                start_time=datetime.utcnow()
            )
            
            self._user_sessions[session_id] = session
            logger.debug(f"Started session tracking for user {user_id}, session {session_id}")
            
        except Exception as e:
            logger.error(f"Error starting session tracking: {e}")
    
    def end_session(self, session_id: str) -> None:
        """End tracking for a user session."""
        try:
            if session_id in self._user_sessions:
                session = self._user_sessions[session_id]
                session.end_time = datetime.utcnow()
                
                # Calculate average response time
                if session.total_messages > 0:
                    session.avg_response_time = session.total_response_time / session.total_messages
                
                # Move to history
                self._session_history.append(session)
                del self._user_sessions[session_id]
                
                # Update user analytics
                self._update_user_analytics(session)
                
                logger.debug(f"Ended session tracking for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error ending session tracking: {e}")
    
    def track_chat_interaction(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        ai_response: str,
        response_time: float
    ) -> None:
        """Track a chat interaction."""
        try:
            # Update session if exists
            if session_id in self._user_sessions:
                session = self._user_sessions[session_id]
                session.total_messages += 1
                session.total_response_time += response_time
                
                # Extract topics from the conversation
                topics = self._extract_topics(user_message + " " + ai_response)
                for topic in topics:
                    if topic not in session.topics_discussed:
                        session.topics_discussed.append(topic)
            
            # Store interaction for analysis
            interaction = {
                "type": "chat",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_message_length": len(user_message),
                "ai_response_length": len(ai_response),
                "response_time": response_time,
                "topics": self._extract_topics(user_message + " " + ai_response)
            }
            
            self._interaction_buffer.append(interaction)
            
        except Exception as e:
            logger.error(f"Error tracking chat interaction: {e}")
    
    def track_assessment(
        self,
        user_id: str,
        session_id: str,
        assessment_scores: Dict[str, float],
        overall_score: float
    ) -> None:
        """Track an assessment completion."""
        try:
            # Update session if exists
            if session_id in self._user_sessions:
                session = self._user_sessions[session_id]
                session.assessment_count += 1
            
            # Store assessment for analysis
            assessment = {
                "type": "assessment",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "assessment_scores": assessment_scores,
                "overall_score": overall_score
            }
            
            self._interaction_buffer.append(assessment)
            
        except Exception as e:
            logger.error(f"Error tracking assessment: {e}")
    
    def track_whiteboard_usage(
        self,
        user_id: str,
        session_id: str,
        action: str,  # "upload", "analyze"
        processing_time: float
    ) -> None:
        """Track whiteboard usage."""
        try:
            # Update session if exists
            if session_id in self._user_sessions:
                session = self._user_sessions[session_id]
                if action == "upload":
                    session.whiteboard_count += 1
            
            # Store whiteboard interaction
            whiteboard = {
                "type": "whiteboard",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "processing_time": processing_time
            }
            
            self._interaction_buffer.append(whiteboard)
            
        except Exception as e:
            logger.error(f"Error tracking whiteboard usage: {e}")
    
    def track_diagram_generation(
        self,
        user_id: str,
        session_id: str,
        diagram_type: str,
        generation_time: float,
        success: bool
    ) -> None:
        """Track diagram generation."""
        try:
            # Update session if exists
            if session_id in self._user_sessions:
                session = self._user_sessions[session_id]
                if success:
                    session.diagram_count += 1
            
            # Store diagram generation
            diagram = {
                "type": "diagram",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "diagram_type": diagram_type,
                "generation_time": generation_time,
                "success": success
            }
            
            self._interaction_buffer.append(diagram)
            
        except Exception as e:
            logger.error(f"Error tracking diagram generation: {e}")
    
    def track_error(
        self,
        user_id: str,
        session_id: str,
        error_type: str,
        context: str
    ) -> None:
        """Track errors encountered by users."""
        try:
            # Update session if exists
            if session_id in self._user_sessions:
                session = self._user_sessions[session_id]
                session.errors_encountered += 1
            
            # Store error for analysis
            error = {
                "type": "error",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error_type": error_type,
                "context": context
            }
            
            self._interaction_buffer.append(error)
            
        except Exception as e:
            logger.error(f"Error tracking error: {e}")
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text based on keywords."""
        text_lower = text.lower()
        topics = []
        
        for topic, keywords in self._topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _update_user_analytics(self, session: UserSession) -> None:
        """Update user analytics based on completed session."""
        try:
            user_id = session.user_id
            
            # Get existing analytics or create new
            if user_id not in self._user_analytics:
                self._user_analytics[user_id] = UserAnalytics(
                    user_id=user_id,
                    total_sessions=0,
                    total_time_spent=0.0,
                    avg_session_duration=0.0,
                    total_messages=0,
                    avg_messages_per_session=0.0,
                    total_assessments=0,
                    avg_assessment_score=0.0,
                    improvement_trend=0.0,
                    favorite_topics=[],
                    engagement_score=0.0,
                    last_active=datetime.utcnow(),
                    streak_days=0,
                    preferred_time_slots=[]
                )
            
            analytics = self._user_analytics[user_id]
            
            # Update session data
            analytics.total_sessions += 1
            
            if session.end_time:
                session_duration = (session.end_time - session.start_time).total_seconds()
                analytics.total_time_spent += session_duration
                analytics.avg_session_duration = analytics.total_time_spent / analytics.total_sessions
            
            analytics.total_messages += session.total_messages
            analytics.avg_messages_per_session = analytics.total_messages / analytics.total_sessions
            analytics.total_assessments += session.assessment_count
            analytics.last_active = session.end_time or datetime.utcnow()
            
            # Update favorite topics
            topic_counter = Counter(analytics.favorite_topics + session.topics_discussed)
            analytics.favorite_topics = [topic for topic, _ in topic_counter.most_common(5)]
            
            # Calculate engagement score
            analytics.engagement_score = self._calculate_engagement_score(analytics, session)
            
            # Update improvement trend and streak
            self._update_improvement_metrics(analytics)
            
        except Exception as e:
            logger.error(f"Error updating user analytics: {e}")
    
    def _calculate_engagement_score(self, analytics: UserAnalytics, session: UserSession) -> float:
        """Calculate user engagement score (0-100)."""
        try:
            score = 0.0
            
            # Session frequency (30%)
            if analytics.total_sessions >= 10:
                score += 30
            elif analytics.total_sessions >= 5:
                score += 20
            elif analytics.total_sessions >= 1:
                score += 10
            
            # Messages per session (25%)
            if analytics.avg_messages_per_session >= 20:
                score += 25
            elif analytics.avg_messages_per_session >= 10:
                score += 15
            elif analytics.avg_messages_per_session >= 5:
                score += 10
            
            # Assessment participation (20%)
            if analytics.total_assessments >= 5:
                score += 20
            elif analytics.total_assessments >= 2:
                score += 15
            elif analytics.total_assessments >= 1:
                score += 10
            
            # Feature usage diversity (15%)
            feature_count = 0
            if session.whiteboard_count > 0:
                feature_count += 1
            if session.diagram_count > 0:
                feature_count += 1
            if session.assessment_count > 0:
                feature_count += 1
            
            if feature_count >= 3:
                score += 15
            elif feature_count >= 2:
                score += 10
            elif feature_count >= 1:
                score += 5
            
            # Low error rate (10%)
            if session.errors_encountered == 0:
                score += 10
            elif session.errors_encountered <= 2:
                score += 5
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0
    
    def _update_improvement_metrics(self, analytics: UserAnalytics) -> None:
        """Update improvement trend and streak metrics."""
        try:
            # Calculate improvement trend based on recent assessments
            recent_assessments = [
                interaction for interaction in self._interaction_buffer[-20:]
                if (interaction["type"] == "assessment" and 
                    interaction["user_id"] == analytics.user_id)
            ]
            
            if len(recent_assessments) >= 2:
                recent_scores = [a["overall_score"] for a in recent_assessments[-5:]]
                if len(recent_scores) >= 2:
                    analytics.improvement_trend = recent_scores[-1] - recent_scores[0]
                    analytics.avg_assessment_score = sum(recent_scores) / len(recent_scores)
            
            # Calculate streak days (simplified)
            days_since_last_active = (datetime.utcnow() - analytics.last_active).days
            if days_since_last_active <= 1:
                analytics.streak_days += 1
            else:
                analytics.streak_days = 1 if days_since_last_active <= 1 else 0
            
        except Exception as e:
            logger.error(f"Error updating improvement metrics: {e}")
    
    def get_user_analytics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific user."""
        try:
            if user_id in self._user_analytics:
                return asdict(self._user_analytics[user_id])
            return None
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return None
    
    def get_platform_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get platform-wide analytics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Filter recent interactions
            recent_interactions = [
                interaction for interaction in self._interaction_buffer
                if datetime.fromisoformat(interaction["timestamp"]) >= cutoff_date
            ]
            
            # Filter recent sessions
            recent_sessions = [
                session for session in self._session_history
                if session.start_time >= cutoff_date
            ]
            
            # Calculate metrics
            total_users = len(set(interaction["user_id"] for interaction in recent_interactions))
            total_sessions = len(recent_sessions)
            total_messages = len([i for i in recent_interactions if i["type"] == "chat"])
            total_assessments = len([i for i in recent_interactions if i["type"] == "assessment"])
            total_whiteboards = len([i for i in recent_interactions if i["type"] == "whiteboard"])
            total_diagrams = len([i for i in recent_interactions if i["type"] == "diagram"])
            
            # Average metrics
            avg_session_duration = 0.0
            if recent_sessions:
                session_durations = [
                    (s.end_time - s.start_time).total_seconds()
                    for s in recent_sessions if s.end_time
                ]
                if session_durations:
                    avg_session_duration = sum(session_durations) / len(session_durations)
            
            # Popular topics
            all_topics = []
            for interaction in recent_interactions:
                if "topics" in interaction:
                    all_topics.extend(interaction["topics"])
            
            topic_counts = Counter(all_topics)
            popular_topics = dict(topic_counts.most_common(10))
            
            # Engagement metrics
            active_users = len([
                user_id for user_id, analytics in self._user_analytics.items()
                if (datetime.utcnow() - analytics.last_active).days <= 7
            ])
            
            avg_engagement_score = 0.0
            if self._user_analytics:
                avg_engagement_score = sum(
                    analytics.engagement_score for analytics in self._user_analytics.values()
                ) / len(self._user_analytics)
            
            return {
                "time_period_days": days,
                "total_users": total_users,
                "active_users": active_users,
                "total_sessions": total_sessions,
                "avg_session_duration_seconds": avg_session_duration,
                "total_messages": total_messages,
                "total_assessments": total_assessments,
                "total_whiteboards": total_whiteboards,
                "total_diagrams": total_diagrams,
                "popular_topics": popular_topics,
                "avg_engagement_score": round(avg_engagement_score, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting platform analytics: {e}")
            return {}
    
    def get_user_cohort_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get user cohort analysis."""
        try:
            # Group users by engagement level
            cohorts = {
                "high_engagement": [],
                "medium_engagement": [],
                "low_engagement": [],
                "new_users": []
            }
            
            for user_id, analytics in self._user_analytics.items():
                if analytics.total_sessions == 1:
                    cohorts["new_users"].append(user_id)
                elif analytics.engagement_score >= 70:
                    cohorts["high_engagement"].append(user_id)
                elif analytics.engagement_score >= 40:
                    cohorts["medium_engagement"].append(user_id)
                else:
                    cohorts["low_engagement"].append(user_id)
            
            # Calculate retention metrics
            retention_analysis = {}
            for cohort_name, user_ids in cohorts.items():
                active_users = [
                    user_id for user_id in user_ids
                    if user_id in self._user_analytics and
                    (datetime.utcnow() - self._user_analytics[user_id].last_active).days <= 7
                ]
                
                retention_analysis[cohort_name] = {
                    "total_users": len(user_ids),
                    "active_users": len(active_users),
                    "retention_rate": len(active_users) / len(user_ids) if user_ids else 0
                }
            
            return {
                "cohorts": retention_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cohort analysis: {e}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 90) -> int:
        """Clean up old analytics data."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Clean interaction buffer
            original_count = len(self._interaction_buffer)
            self._interaction_buffer = [
                interaction for interaction in self._interaction_buffer
                if datetime.fromisoformat(interaction["timestamp"]) >= cutoff_date
            ]
            
            # Clean session history
            self._session_history = [
                session for session in self._session_history
                if session.start_time >= cutoff_date
            ]
            
            cleaned_count = original_count - len(self._interaction_buffer)
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old analytics records")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up analytics data: {e}")
            return 0


# Global analytics service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get the global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


def init_analytics() -> None:
    """Initialize analytics service."""
    global _analytics_service
    _analytics_service = AnalyticsService()
    logger.info("Analytics service initialized")