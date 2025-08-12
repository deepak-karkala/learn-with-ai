
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Optional, List
from datetime import datetime

from app.services.progress_service import ProgressService
from app.models.progress import (
    ProgressSummary,
    ProgressTimeline,
    TrendAnalysis,
    Goal
)

router = APIRouter(prefix="/progress", tags=["progress"])


def get_progress_service(request: Request) -> ProgressService:
    service = getattr(request.app.state, "progress_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Progress service not available")
    return service


@router.get("/summary/{user_id}", response_model=ProgressSummary)
async def get_progress_summary(
    user_id: str,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Get comprehensive progress summary"""
    return await progress_service.get_progress_summary(user_id)


@router.get("/timeline/{user_id}", response_model=ProgressTimeline)
async def get_progress_timeline(
    user_id: str,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Get progress timeline data"""
    summary = await progress_service.get_progress_summary(user_id)
    return summary.timeline


@router.get("/trends/{user_id}", response_model=TrendAnalysis)
async def get_trend_analysis(
    user_id: str,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Get trend analysis data"""
    summary = await progress_service.get_progress_summary(user_id)
    return summary.trends


@router.post("/goals/{user_id}", response_model=Goal)
async def set_goal(
    user_id: str,
    description: str,
    target_date: Optional[datetime] = None,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Set new learning goal"""
    return progress_service.set_goal(user_id, description, target_date)


@router.get("/goals/{user_id}", response_model=List[Goal])
async def get_goals(
    user_id: str,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Get user's learning goals"""
    return progress_service.get_goals(user_id)


@router.put("/goals/{user_id}/{goal_id}", response_model=Goal)
async def update_goal(
    user_id: str,
    goal_id: str,
    progress: float,
    status: Optional[str] = None,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Update goal progress and status"""
    updated = progress_service.update_goal_progress(
        user_id, goal_id, progress, status
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Goal not found")
    return updated


@router.get("/export/{user_id}", response_model=Dict)
async def export_progress_report(
    user_id: str,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """Export progress report as JSON"""
    return await progress_service.export_progress_report(user_id)
