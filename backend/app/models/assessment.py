from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class AssessmentDimension(str, Enum):
    """The 6 dimensions of system design assessment"""
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    SYSTEM_ARCHITECTURE = "system_architecture"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    SCALE_PERFORMANCE = "scale_performance"
    RELIABILITY_FAULT_TOLERANCE = "reliability_fault_tolerance"
    COMMUNICATION_THOUGHT_PROCESS = "communication_thought_process"


class AssessmentRequest(BaseModel):
    """Request model for assessment evaluation"""
    user_id: str = Field(..., description="Unique identifier for the user")
    session_id: Optional[str] = Field(
        None, description="Session identifier if available"
    )
    interaction_context: str = Field(
        ..., description="Context of the user interaction"
    )
    whiteboard_feedback: Optional[Dict] = Field(
        None, description="Feedback from whiteboard analysis"
    )
    conversation_history: Optional[str] = Field(
        None, description="Recent conversation context"
    )
    assessment_type: str = Field(
        default="system_design", description="Type of assessment"
    )
    
    @field_validator('interaction_context')
    @classmethod
    def validate_interaction_context(cls, v):
        if not v.strip():
            raise ValueError("Interaction context cannot be empty")
        if len(v) > 10000:
            raise ValueError(
                "Interaction context too long (max 10000 characters)"
            )
        return v.strip()


class DimensionScore(BaseModel):
    """Individual dimension score with feedback"""
    score: float = Field(..., ge=1.0, le=5.0, description="Score from 1-5")
    feedback: str = Field(..., description="Detailed feedback for this dimension")
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas to improve")
    confidence: float = Field(..., ge=1.0, le=5.0, description="Confidence in this assessment")


class AssessmentResponse(BaseModel):
    """Response model for assessment evaluation"""
    assessment_id: str = Field(..., description="Unique identifier for this assessment")
    user_id: str = Field(..., description="User who received the assessment")
    session_id: Optional[str] = Field(None, description="Session identifier if available")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When assessment was created")
    
    # 6-dimensional scores
    dimension_scores: Dict[AssessmentDimension, DimensionScore] = Field(
        ..., description="Scores for each of the 6 dimensions"
    )
    
    # Overall assessment
    overall_score: float = Field(..., ge=1.0, le=5.0, description="Overall score (1-5)")
    confidence_score: float = Field(..., ge=1.0, le=5.0, description="Overall confidence (1-5)")
    
    # Detailed feedback
    detailed_feedback: str = Field(..., description="Comprehensive assessment feedback")
    summary: str = Field(..., description="Executive summary of the assessment")
    
    # Metadata
    assessment_type: str = Field(..., description="Type of assessment performed")
    model_used: str = Field(..., description="LLM model used for assessment")
    tokens_used: int = Field(..., description="Number of tokens consumed")
    cost_estimate: float = Field(..., description="Estimated cost of assessment")
    
    # Recommendations
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    next_steps: List[str] = Field(..., description="Suggested next steps")
    
    @field_validator('overall_score')
    @classmethod
    def validate_overall_score(cls, v):
        if not 1.0 <= v <= 5.0:
            raise ValueError("Overall score must be between 1.0 and 5.0")
        return round(v, 2)
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v):
        if not 1.0 <= v <= 5.0:
            raise ValueError("Confidence score must be between 1.0 and 5.0")
        return round(v, 2)


class AssessmentHistoryRequest(BaseModel):
    """Request model for retrieving assessment history"""
    user_id: str = Field(..., description="User identifier")
    limit: Optional[int] = Field(default=50, le=100, description="Maximum number of assessments to return")
    offset: Optional[int] = Field(default=0, ge=0, description="Number of assessments to skip")
    assessment_type: Optional[str] = Field(None, description="Filter by assessment type")


class AssessmentHistoryResponse(BaseModel):
    """Response model for assessment history"""
    user_id: str = Field(..., description="User identifier")
    assessments: List[AssessmentResponse] = Field(..., description="List of assessments")
    total_count: int = Field(..., description="Total number of assessments for this user")
    has_more: bool = Field(..., description="Whether there are more assessments available")


class AssessmentSummary(BaseModel):
    """Summary statistics for assessment analytics"""
    user_id: str = Field(..., description="User identifier")
    total_assessments: int = Field(..., description="Total number of assessments")
    average_overall_score: float = Field(..., description="Average overall score")
    average_confidence: float = Field(..., description="Average confidence score")
    
    # Dimension averages
    dimension_averages: Dict[AssessmentDimension, float] = Field(
        ..., description="Average scores for each dimension"
    )
    
    # Trend analysis
    recent_trend: str = Field(..., description="Trend description (improving, declining, stable)")
    strongest_dimension: AssessmentDimension = Field(..., description="User's strongest dimension")
    weakest_dimension: AssessmentDimension = Field(..., description="User's weakest dimension")
    
    # Recommendations
    top_recommendations: List[str] = Field(..., description="Top recommendations for improvement")
    next_assessment_date: Optional[datetime] = Field(None, description="Suggested next assessment date")
