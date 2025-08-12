import pytest
from datetime import datetime, timezone

from app.models.assessment import (
    AssessmentRequest,
    AssessmentResponse,
    AssessmentDimension,
    DimensionScore
)
from app.services.assessment_service import AssessmentService


class TestAssessmentService:
    """Test cases for AssessmentService"""
    
    @pytest.fixture
    def assessment_service(self):
        return AssessmentService()
    
    @pytest.fixture
    def sample_assessment_request(self):
        return AssessmentRequest(
            user_id="test_user_123",
            interaction_context="User explained microservices architecture",
            assessment_type="system_design"
        )
    
    @pytest.mark.asyncio
    async def test_evaluate_assessment_success(self, assessment_service, sample_assessment_request):
        """Test successful assessment evaluation"""
        assessment = await assessment_service.evaluate_assessment(sample_assessment_request)
        
        # Verify assessment structure
        assert assessment.assessment_id is not None
        assert assessment.user_id == sample_assessment_request.user_id
        assert assessment.assessment_type == sample_assessment_request.assessment_type
        
        # Verify 6-dimensional scores
        assert len(assessment.dimension_scores) == 6
        assert AssessmentDimension.REQUIREMENTS_ANALYSIS in assessment.dimension_scores
        assert AssessmentDimension.SYSTEM_ARCHITECTURE in assessment.dimension_scores
        assert AssessmentDimension.TECHNICAL_DEEP_DIVE in assessment.dimension_scores
        assert AssessmentDimension.SCALE_PERFORMANCE in assessment.dimension_scores
        assert AssessmentDimension.RELIABILITY_FAULT_TOLERANCE in assessment.dimension_scores
        assert AssessmentDimension.COMMUNICATION_THOUGHT_PROCESS in assessment.dimension_scores
        
        # Verify scores are within valid range
        for dimension_score in assessment.dimension_scores.values():
            assert 1.0 <= dimension_score.score <= 5.0
            assert 1.0 <= dimension_score.confidence <= 5.0
            assert dimension_score.feedback is not None
            assert len(dimension_score.strengths) > 0
            assert len(dimension_score.areas_for_improvement) > 0
        
        # Verify overall assessment
        assert 1.0 <= assessment.overall_score <= 5.0
        assert 1.0 <= assessment.confidence_score <= 5.0
        assert assessment.detailed_feedback is not None
        assert assessment.summary is not None
        assert len(assessment.recommendations) > 0
        assert len(assessment.next_steps) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_assessment_storage(self, assessment_service, sample_assessment_request):
        """Test that assessment is properly stored after evaluation"""
        # Verify no assessments exist initially
        assert len(assessment_service.assessments) == 0
        assert len(assessment_service.user_assessments) == 0
        
        # Evaluate assessment
        assessment = await assessment_service.evaluate_assessment(sample_assessment_request)
        
        # Verify assessment is stored
        assert len(assessment_service.assessments) == 1
        assert assessment.assessment_id in assessment_service.assessments
        
        # Verify user assessment mapping
        assert sample_assessment_request.user_id in assessment_service.user_assessments
        assert assessment.assessment_id in assessment_service.user_assessments[sample_assessment_request.user_id]
    
    def test_create_assessment_prompt(self, assessment_service, sample_assessment_request):
        """Test assessment prompt creation"""
        prompt = assessment_service._create_assessment_prompt(sample_assessment_request)
        
        # Verify prompt contains required elements
        assert "expert system design interviewer" in prompt
        assert "6 key dimensions" in prompt
        assert sample_assessment_request.interaction_context in prompt
        assert "REQUIREMENTS_ANALYSIS" in prompt
        assert "SYSTEM_ARCHITECTURE" in prompt
        assert "TECHNICAL_DEEP_DIVE" in prompt
        assert "SCALE_PERFORMANCE" in prompt
        assert "RELIABILITY_FAULT_TOLERANCE" in prompt
        assert "COMMUNICATION_THOUGHT_PROCESS" in prompt
        assert "JSON format" in prompt


class TestAssessmentModels:
    """Test cases for assessment models"""
    
    def test_assessment_request_validation(self):
        """Test AssessmentRequest validation"""
        # Valid request
        request = AssessmentRequest(
            user_id="test_user",
            interaction_context="Valid context"
        )
        assert request.user_id == "test_user"
        assert request.interaction_context == "Valid context"
        assert request.assessment_type == "system_design"  # default value
        
        # Test empty context validation
        with pytest.raises(ValueError, match="cannot be empty"):
            AssessmentRequest(
                user_id="test_user",
                interaction_context=""
            )
    
    def test_dimension_score_validation(self):
        """Test DimensionScore validation"""
        # Valid score
        score = DimensionScore(
            score=4.0,
            feedback="Good feedback",
            strengths=["Strength 1"],
            areas_for_improvement=["Area 1"],
            confidence=4.5
        )
        assert score.score == 4.0
        assert score.confidence == 4.5
