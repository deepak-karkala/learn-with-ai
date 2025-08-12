from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models.assessment import (
    AssessmentRequest,
    AssessmentResponse,
    AssessmentHistoryResponse,
    AssessmentSummary
)
from app.services.assessment_service import AssessmentService


router = APIRouter(prefix="/api/assessment", tags=["assessment"])


# Dependency to get assessment service
def get_assessment_service() -> AssessmentService:
    return AssessmentService()


@router.post("/evaluate", response_model=AssessmentResponse)
async def evaluate_assessment(
    request: AssessmentRequest,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """
    Evaluate a user's system design performance using LLM judge
    
    This endpoint provides comprehensive 6-dimensional assessment across:
    - Requirements Analysis
    - System Architecture  
    - Technical Deep Dive
    - Scale & Performance
    - Reliability & Fault Tolerance
    - Communication & Thought Process
    """
    try:
        assessment = await assessment_service.evaluate_assessment(request)
        return assessment
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Assessment evaluation failed: {str(e)}"
        )


@router.get("/history/{user_id}", response_model=AssessmentHistoryResponse)
async def get_assessment_history(
    user_id: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    assessment_type: Optional[str] = None,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """
    Retrieve assessment history for a specific user
    
    Supports pagination and filtering by assessment type
    """
    try:
        if limit > 100:
            limit = 100  # Cap at 100 for performance
        
        history = await assessment_service.get_assessment_history(
            user_id=user_id,
            limit=limit,
            offset=offset,
            assessment_type=assessment_type
        )
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve assessment history: {str(e)}"
        )


@router.get("/summary/{user_id}", response_model=AssessmentSummary)
async def get_assessment_summary(
    user_id: str,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """
    Get comprehensive assessment summary and analytics for a user
    
    Includes:
    - Overall performance metrics
    - Dimension averages
    - Trend analysis
    - Top recommendations
    - Next assessment suggestions
    """
    try:
        summary = await assessment_service.get_assessment_summary(user_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate assessment summary: {str(e)}"
        )


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """
    Retrieve a specific assessment by ID
    """
    try:
        assessment = assessment_service.get_assessment(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=404,
                detail="Assessment not found"
            )
        return assessment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve assessment: {str(e)}"
        )


@router.delete("/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """
    Delete an assessment (admin function)
    """
    try:
        success = assessment_service.delete_assessment(assessment_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Assessment not found"
            )
        return {"message": "Assessment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete assessment: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_assessments(
    max_age_days: int = 90,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """
    Clean up old assessments (admin function)
    
    Removes assessments older than specified days for memory management
    """
    try:
        assessment_service.cleanup_old_assessments(max_age_days)
        return {
            "message": (
                f"Cleanup completed for assessments older than {max_age_days} days"
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )
