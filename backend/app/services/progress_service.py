
import logging
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.models.progress import (
    ProgressSummary,
    ProgressPoint,
    ProgressTimeline,
    TrendAnalysis,
    Recommendation,
    Goal
)
from app.services.assessment_service import AssessmentService

logger = logging.getLogger(__name__)


class ProgressService:
    """Service for managing user progress tracking and analytics"""
    
    def __init__(self, assessment_service: AssessmentService):
        self.assessment_service = assessment_service
        # user_id -> list of goals
        self.user_goals: Dict[str, List[Goal]] = {}
        # Cache for summaries
        self.progress_summaries: Dict[str, ProgressSummary] = {}

    async def get_progress_summary(
        self, user_id: str
    ) -> ProgressSummary:
        """Get comprehensive progress summary for user"""
        try:
            history = await self.assessment_service.get_assessment_history(
                user_id
            )
            
            timeline = self._calculate_timeline(history.assessments)
            trends = self._calculate_trends(timeline)
            recommendations = self._generate_recommendations(
                trends, history.assessments
            )
            goals = self.get_goals(user_id)
            
            summary = ProgressSummary(
                timeline=timeline,
                trends=trends,
                recommendations=recommendations,
                goals=goals,
                last_updated=datetime.now()
            )
            
            self.progress_summaries[user_id] = summary
            return summary
            
        except Exception as e:
            logger.error(
                f"Failed to generate progress summary for {user_id}: {str(e)}"
            )
            raise

    def _calculate_timeline(self, assessments: List) -> ProgressTimeline:
        """Calculate progress timeline from assessments"""
        points = []
        for assessment in sorted(assessments, key=lambda x: x.timestamp):
            dimension_scores = {
                dim: score.score
                for dim, score in assessment.dimension_scores.items()
            }
            points.append(
                ProgressPoint(
                    date=assessment.timestamp,
                    overall_score=assessment.overall_score,
                    dimension_scores=dimension_scores,
                )
            )
        return ProgressTimeline(points=points)

    def _calculate_trends(self, timeline: ProgressTimeline) -> TrendAnalysis:
        """Analyze trends from timeline data"""
        if len(timeline.points) < 2:
            return TrendAnalysis(
                overall_trend="Insufficient data",
                improving_dimensions=[],
                declining_dimensions=[],
            )
        
        recent = timeline.points[-1]
        previous = (
            timeline.points[0] if len(timeline.points) == 2 else timeline.points[-2]
        )
        
        overall_trend = (
            "Improving" if recent.overall_score > previous.overall_score else
            "Declining" if recent.overall_score < previous.overall_score else 
            "Stable"
        )
        
        improving: List = []
        declining: List = []
        for dim in recent.dimension_scores:
            delta = (
                recent.dimension_scores[dim] -
                previous.dimension_scores.get(dim, 0)
            )
            if delta > 0.5:
                improving.append(dim)
            elif delta < -0.5:
                declining.append(dim)
        
        return TrendAnalysis(
            overall_trend=overall_trend,
            improving_dimensions=improving,
            declining_dimensions=declining,
        )

    def _generate_recommendations(
        self, trends: TrendAnalysis, assessments: List
    ) -> List[Recommendation]:
        """Generate personalized recommendations"""
        recommendations: List[Recommendation] = []
        
        for dim in trends.declining_dimensions:
            description = (
                f"Focus on improving {dim.value.replace('_', ' ')} "
                "through targeted practice"
            )
            recommendations.append(
                Recommendation(
                    dimension=dim,
                    description=description,
                    priority=1,
                )
            )
        
        if assessments:
            recent = assessments[-1]
            weak_dims = sorted(
                recent.dimension_scores.items(),
                key=lambda x: x[1].score,
            )[:2]
            
            for dim, score in weak_dims:
                description = (
                    f"Review resources on {dim.value.replace('_', ' ')} "
                    f"to improve from {score.score}"
                )
                priority = 2 if score.score < 3 else 3
                recommendations.append(
                    Recommendation(
                        dimension=dim,
                        description=description,
                        priority=priority,
                    )
                )
        
        return recommendations[:5]

    def set_goal(
        self, user_id: str, description: str, target_date: Optional[datetime] = None
    ) -> Goal:
        """Set a new learning goal for user"""
        goal = Goal(
            id=str(uuid.uuid4()),
            description=description,
            target_date=target_date,
            status="active",
            progress=0.0,
        )
        
        if user_id not in self.user_goals:
            self.user_goals[user_id] = []
        self.user_goals[user_id].append(goal)
        
        return goal

    def get_goals(self, user_id: str) -> List[Goal]:
        """Get user's learning goals"""
        return self.user_goals.get(user_id, [])

    def update_goal_progress(
        self,
        user_id: str,
        goal_id: str,
        progress: float,
        status: Optional[str] = None,
    ) -> Optional[Goal]:
        """Update goal progress and status"""
        goals = self.user_goals.get(user_id, [])
        for goal in goals:
            if goal.id == goal_id:
                goal.progress = max(0.0, min(100.0, progress))
                if status:
                    goal.status = status
                if goal.progress >= 100.0:
                    goal.status = "completed"
                return goal
        return None

    async def export_progress_report(self, user_id: str) -> Dict:
        """Generate JSON data for progress report export"""
        summary = await self.get_progress_summary(user_id)
        
        detailed_history = [
            ass.dict() for ass in (
                await self.assessment_service.get_assessment_history(user_id)
            ).assessments
        ]
        
        return {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "summary": summary.dict(),
            "detailed_history": detailed_history,
        }

    def _cleanup_summaries(self):
        """Cleanup method if needed"""
        pass
