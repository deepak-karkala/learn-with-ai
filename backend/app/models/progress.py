
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.models.assessment import AssessmentDimension


class ProgressPoint(BaseModel):
    date: datetime = Field(
        ..., description="Date of the data point"
    )
    overall_score: float = Field(
        ..., description="Overall score at this point"
    )
    dimension_scores: Dict[AssessmentDimension, float] = Field(
        ..., description="Dimension scores"
    )


class ProgressTimeline(BaseModel):
    points: List[ProgressPoint] = Field(
        ..., description="Timeline data points"
    )


class TrendAnalysis(BaseModel):
    overall_trend: str = Field(
        ..., description="Overall performance trend"
    )
    improving_dimensions: List[AssessmentDimension] = Field(
        ..., description="Improving areas"
    )
    declining_dimensions: List[AssessmentDimension] = Field(
        ..., description="Declining areas"
    )


class Recommendation(BaseModel):
    dimension: Optional[AssessmentDimension] = Field(
        None, description="Related dimension"
    )
    description: str = Field(
        ..., description="Recommendation text"
    )
    priority: int = Field(
        ..., ge=1, le=5, description="Priority level"
    )


class Goal(BaseModel):
    id: str = Field(
        ..., description="Unique goal identifier"
    )
    description: str = Field(
        ..., description="Goal description"
    )
    target_date: Optional[datetime] = Field(
        None, description="Target completion date"
    )
    status: str = Field(
        default="active", description="Goal status"
    )
    progress: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Completion progress"
    )


class ProgressSummary(BaseModel):
    timeline: ProgressTimeline = Field(
        ..., description="Historical progress data"
    )
    trends: TrendAnalysis = Field(
        ..., description="Trend analysis"
    )
    recommendations: List[Recommendation] = Field(
        ..., description="Personalized recommendations"
    )
    goals: List[Goal] = Field(
        default_factory=list, description="User goals"
    )
    last_updated: datetime = Field(
        ..., description="Last update timestamp"
    )
