
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict

from app.services.progress_service import ProgressService
from app.models.progress import (
    ProgressSummary,
    ProgressPoint,
    ProgressTimeline,
    Goal
)
from app.services.assessment_service import AssessmentService, AssessmentDimension
from app.models.assessment import (
    AssessmentResponse,
    DimensionScore,
    AssessmentHistoryResponse
)


@pytest.fixture
def mock_assessment_service():
    service = AsyncMock(spec=AssessmentService)
    return service


@pytest.fixture
def progress_service(mock_assessment_service):
    return ProgressService(mock_assessment_service)


@pytest.mark.asyncio
async def test_get_progress_summary(progress_service, mock_assessment_service):
    mock_history = AssessmentHistoryResponse(
        user_id="test_user",
        assessments=[
            AssessmentResponse(
                assessment_id="1",
                user_id="test_user",
                timestamp=datetime.now() - timedelta(days=2),
                dimension_scores={
                    AssessmentDimension.REQUIREMENTS_ANALYSIS: DimensionScore(
                        score=3.0, feedback="", strengths=[],
                        areas_for_improvement=[], confidence=3.0
                    ),
                    AssessmentDimension.SYSTEM_ARCHITECTURE: DimensionScore(
                        score=3.5, feedback="", strengths=[],
                        areas_for_improvement=[], confidence=3.5
                    ),
                },
                overall_score=3.25,
                confidence_score=3.25,
                detailed_feedback="",
                summary="",
                assessment_type="",
                model_used="",
                tokens_used=0,
                cost_estimate=0.0,
                recommendations=[],
                next_steps=[]
            ),
            AssessmentResponse(
                assessment_id="2",
                user_id="test_user",
                timestamp=datetime.now() - timedelta(days=1),
                dimension_scores={
                    AssessmentDimension.REQUIREMENTS_ANALYSIS: DimensionScore(
                        score=4.0, feedback="", strengths=[],
                        areas_for_improvement=[], confidence=4.0
                    ),
                    AssessmentDimension.SYSTEM_ARCHITECTURE: DimensionScore(
                        score=4.5, feedback="", strengths=[],
                        areas_for_improvement=[], confidence=4.5
                    ),
                },
                overall_score=4.25,
                confidence_score=4.25,
                detailed_feedback="",
                summary="",
                assessment_type="",
                model_used="",
                tokens_used=0,
                cost_estimate=0.0,
                recommendations=["Practice more"],
                next_steps=[]
            )
        ],
        total_count=2,
        has_more=False
    )
    
    mock_assessment_service.get_assessment_history.return_value = mock_history
    
    progress_service.user_goals["test_user"] = [
        Goal(
            id="g1",
            description="Test goal",
            progress=50.0,
            status="active"
        )
    ]
    
    summary = await progress_service.get_progress_summary("test_user")
    
    assert isinstance(summary, ProgressSummary)
    assert len(summary.timeline.points) == 2
    assert summary.trends.overall_trend == "Improving"
    assert len(summary.recommendations) > 0
    assert len(summary.goals) == 1


def test_set_goal(progress_service):
    goal = progress_service.set_goal(
        "test_user",
        "Learn system design",
        datetime.now() + timedelta(days=30)
    )
    
    assert isinstance(goal, Goal)
    assert goal.description == "Learn system design"
    assert goal.status == "active"
    assert goal.progress == 0.0


def test_get_goals(progress_service):
    progress_service.set_goal("test_user", "Goal 1")
    progress_service.set_goal("test_user", "Goal 2")
    
    goals = progress_service.get_goals("test_user")
    assert len(goals) == 2
    assert all(isinstance(g, Goal) for g in goals)


def test_update_goal_progress(progress_service):
    goal = progress_service.set_goal("test_user", "Test goal")
    
    updated = progress_service.update_goal_progress(
        "test_user", goal.id, 75.0, "in_progress"
    )
    assert updated is not None
    assert updated.progress == 75.0
    assert updated.status == "in_progress"
    
    completed = progress_service.update_goal_progress(
        "test_user", goal.id, 100.0
    )
    assert completed.status == "completed"
    
    invalid = progress_service.update_goal_progress(
        "test_user", "bad_id", 50.0
    )
    assert invalid is None


@pytest.mark.asyncio
async def test_export_progress_report(progress_service, mock_assessment_service):
    # Build a minimal real AssessmentResponse to avoid attribute errors
    assessment = AssessmentResponse(
        assessment_id="a1",
        user_id="test_user",
        timestamp=datetime.now(),
        dimension_scores={
            AssessmentDimension.REQUIREMENTS_ANALYSIS: DimensionScore(
                score=3.5,
                feedback="",
                strengths=[],
                areas_for_improvement=[],
                confidence=3.5,
            ),
            AssessmentDimension.SYSTEM_ARCHITECTURE: DimensionScore(
                score=3.8,
                feedback="",
                strengths=[],
                areas_for_improvement=[],
                confidence=3.8,
            ),
        },
        overall_score=3.65,
        confidence_score=3.65,
        detailed_feedback="",
        summary="",
        assessment_type="system_design",
        model_used="gpt-4",
        tokens_used=100,
        cost_estimate=0.001,
        recommendations=[],
        next_steps=[],
    )

    mock_assessment_service.get_assessment_history.return_value = (
        AssessmentHistoryResponse(
            user_id="test_user",
            assessments=[assessment],
            total_count=1,
            has_more=False,
        )
    )
    
    report = await progress_service.export_progress_report("test_user")
    
    assert isinstance(report, Dict)
    assert "user_id" in report
    assert "generated_at" in report
    assert "summary" in report
    assert "detailed_history" in report
    assert len(report["detailed_history"]) == 1


def test_calculate_trends(progress_service):
    timeline = ProgressTimeline(points=[
        ProgressPoint(
            date=datetime.now() - timedelta(days=1),
            overall_score=3.0,
            dimension_scores={
                AssessmentDimension.REQUIREMENTS_ANALYSIS: 3.0
            }
        ),
        ProgressPoint(
            date=datetime.now(),
            overall_score=4.0,
            dimension_scores={
                AssessmentDimension.REQUIREMENTS_ANALYSIS: 4.0
            }
        )
    ])
    
    trends = progress_service._calculate_trends(timeline)
    assert trends.overall_trend == "Improving"
    assert (
        AssessmentDimension.REQUIREMENTS_ANALYSIS in trends.improving_dimensions
    )
