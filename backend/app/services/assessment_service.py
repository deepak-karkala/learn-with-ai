import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import json

from app.models.assessment import (
    AssessmentRequest,
    AssessmentResponse,
    AssessmentDimension,
    DimensionScore,
    AssessmentHistoryResponse,
    AssessmentSummary
)
from app.services.config import settings

logger = logging.getLogger(__name__)


class AssessmentService:
    """Service for managing system design assessments using LLM judge"""
    
    def __init__(self):
        self.assessments: Dict[str, AssessmentResponse] = {}
        self.user_assessments: Dict[str, List[str]] = {}
        
    async def evaluate_assessment(
        self, 
        request: AssessmentRequest
    ) -> AssessmentResponse:
        """
        Evaluate a user's system design performance using LLM judge
        
        Args:
            request: Assessment request with user interaction context
            
        Returns:
            AssessmentResponse with 6-dimensional scores and feedback
        """
        try:
            logger.info(f"Starting assessment evaluation for user: {request.user_id}")
            
            # Generate assessment ID
            assessment_id = str(uuid.uuid4())
            
            # Create assessment prompt
            assessment_prompt = self._create_assessment_prompt(request)
            
            # For now, use mock assessment until we integrate with OpenAI
            # TODO: Replace with actual OpenAI API call
            assessment_result = await self._get_mock_assessment(
                request, assessment_prompt
            )
            
            # Create assessment response
            assessment = AssessmentResponse(
                assessment_id=assessment_id,
                user_id=request.user_id,
                session_id=request.session_id,
                timestamp=datetime.now(timezone.utc),
                dimension_scores=assessment_result["dimension_scores"],
                overall_score=assessment_result["overall_score"],
                confidence_score=assessment_result["confidence_score"],
                detailed_feedback=assessment_result["detailed_feedback"],
                summary=assessment_result["summary"],
                assessment_type=request.assessment_type,
                model_used="gpt-4o",  # Will be dynamic when integrated
                tokens_used=assessment_result["tokens_used"],
                cost_estimate=assessment_result["cost_estimate"],
                recommendations=assessment_result["recommendations"],
                next_steps=assessment_result["next_steps"]
            )
            
            # Store assessment
            self._store_assessment(assessment)
            
            logger.info(
                f"Assessment completed for user {request.user_id}. "
                f"Overall score: {assessment.overall_score}"
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Assessment evaluation failed: {str(e)}")
            raise
    
    def _create_assessment_prompt(self, request: AssessmentRequest) -> str:
        """Create comprehensive assessment prompt for LLM judge"""
        
        prompt = f"""
        You are an expert system design interviewer and assessor. 
        Evaluate the following user interaction across 6 key dimensions.
        
        USER CONTEXT:
        {request.interaction_context}
        
        WHITEBOARD FEEDBACK:
        {json.dumps(request.whiteboard_feedback) if request.whiteboard_feedback else "None provided"}
        
        CONVERSATION HISTORY:
        {request.conversation_history if request.conversation_history else "None provided"}
        
        ASSESSMENT RUBRIC:
        
        1. REQUIREMENTS_ANALYSIS (1-5):
           - Understanding of problem requirements
           - Clarification questions asked
           - Scope definition accuracy
        
        2. SYSTEM_ARCHITECTURE (1-5):
           - High-level design approach
           - Component identification
           - Architecture patterns used
        
        3. TECHNICAL_DEEP_DIVE (1-5):
           - Technical knowledge depth
           - Trade-off analysis
           - Implementation details
        
        4. SCALE_PERFORMANCE (1-5):
           - Scalability considerations
           - Performance optimization
           - Load handling approach
        
        5. RELIABILITY_FAULT_TOLERANCE (1-5):
           - Error handling strategies
           - Fault tolerance design
           - Monitoring and alerting
        
        6. COMMUNICATION_THOUGHT_PROCESS (1-5):
           - Clarity of explanation
           - Logical thinking flow
           - Communication effectiveness
        
        SCORING GUIDELINES:
        - 1: Poor - Major gaps, incorrect understanding
        - 2: Below Average - Some understanding, significant issues
        - 3: Average - Basic understanding, room for improvement
        - 4: Above Average - Good understanding, minor gaps
        - 5: Excellent - Strong understanding, comprehensive approach
        
        Provide your assessment in the following JSON format:
        {{
            "dimension_scores": {{
                "requirements_analysis": {{
                    "score": 4.0,
                    "feedback": "Good understanding of requirements...",
                    "strengths": ["Clear problem identification"],
                    "areas_for_improvement": ["Ask more clarifying questions"],
                    "confidence": 4.5
                }},
                "system_architecture": {{...}},
                "technical_deep_dive": {{...}},
                "scale_performance": {{...}},
                "reliability_fault_tolerance": {{...}},
                "communication_thought_process": {{...}}
            }},
            "overall_score": 4.2,
            "confidence_score": 4.3,
            "detailed_feedback": "Comprehensive assessment...",
            "summary": "Strong performance with room for improvement in...",
            "recommendations": ["Focus on...", "Practice..."],
            "next_steps": ["Review...", "Study..."]
        }}
        
        Be thorough, fair, and constructive in your feedback.
        """
        
        return prompt
    
    async def _get_mock_assessment(
        self, 
        request: AssessmentRequest, 
        prompt: str
    ) -> Dict:
        """Generate mock assessment for development/testing"""
        
        # This is a realistic mock assessment that demonstrates the structure
        # In production, this would call OpenAI API with the prompt
        
        mock_scores = {
            AssessmentDimension.REQUIREMENTS_ANALYSIS: DimensionScore(
                score=4.0,
                feedback="Good understanding of system requirements. User demonstrated clear problem identification and asked relevant clarifying questions. Could improve by exploring edge cases more thoroughly.",
                strengths=["Clear problem identification", "Relevant clarifying questions"],
                areas_for_improvement=["Explore edge cases", "Consider non-functional requirements"],
                confidence=4.2
            ),
            AssessmentDimension.SYSTEM_ARCHITECTURE: DimensionScore(
                score=4.5,
                feedback="Strong architectural thinking with good component identification. User showed understanding of common patterns and trade-offs. Architecture was well-structured and scalable.",
                strengths=["Good component identification", "Understanding of patterns", "Scalable design"],
                areas_for_improvement=["Consider alternative architectures", "Document design decisions"],
                confidence=4.3
            ),
            AssessmentDimension.TECHNICAL_DEEP_DIVE: DimensionScore(
                score=3.8,
                feedback="Solid technical knowledge with good understanding of core concepts. User could dive deeper into implementation details and explore more advanced optimization techniques.",
                strengths=["Core technical knowledge", "Basic optimization understanding"],
                areas_for_improvement=["Implementation details", "Advanced optimization techniques"],
                confidence=4.0
            ),
            AssessmentDimension.SCALE_PERFORMANCE: DimensionScore(
                score=4.2,
                feedback="Good awareness of scalability concerns and performance considerations. User identified key bottlenecks and proposed reasonable solutions. Could explore more advanced scaling strategies.",
                strengths=["Scalability awareness", "Bottleneck identification"],
                areas_for_improvement=["Advanced scaling strategies", "Performance metrics"],
                confidence=4.1
            ),
            AssessmentDimension.RELIABILITY_FAULT_TOLERANCE: DimensionScore(
                score=3.5,
                feedback="Basic understanding of reliability concepts. User mentioned some error handling but could explore fault tolerance patterns, monitoring, and alerting strategies more thoroughly.",
                strengths=["Basic error handling awareness"],
                areas_for_improvement=["Fault tolerance patterns", "Monitoring strategies", "Alerting systems"],
                confidence=3.8
            ),
            AssessmentDimension.COMMUNICATION_THOUGHT_PROCESS: DimensionScore(
                score=4.3,
                feedback="Clear communication with logical thinking flow. User explained concepts well and showed structured problem-solving approach. Could improve by providing more concrete examples.",
                strengths=["Clear communication", "Logical thinking", "Structured approach"],
                areas_for_improvement=["Concrete examples", "Visual aids"],
                confidence=4.4
            )
        }
        
        # Calculate overall score (weighted average)
        overall_score = sum(score.score for score in mock_scores.values()) / len(mock_scores)
        overall_score = round(overall_score, 2)
        
        # Calculate confidence score
        confidence_score = sum(score.confidence for score in mock_scores.values()) / len(mock_scores)
        confidence_score = round(confidence_score, 2)
        
        return {
            "dimension_scores": mock_scores,
            "overall_score": overall_score,
            "confidence_score": confidence_score,
            "detailed_feedback": f"Overall, this is a strong performance demonstrating solid understanding of system design principles. The user shows particular strength in system architecture and requirements analysis. Areas for improvement include deeper technical exploration and more comprehensive reliability planning. This performance suggests readiness for intermediate-level system design challenges.",
            "summary": f"Strong performance (Score: {overall_score}/5) with excellent system architecture skills. Focus on technical depth and reliability planning for continued improvement.",
            "recommendations": [
                "Practice implementing fault tolerance patterns in your designs",
                "Study advanced scaling strategies and performance optimization techniques",
                "Work on providing concrete examples and implementation details",
                "Explore monitoring and observability best practices"
            ],
            "next_steps": [
                "Review fault tolerance patterns and implement them in practice",
                "Study advanced performance optimization techniques",
                "Practice explaining complex concepts with concrete examples",
                "Build monitoring and alerting into your system designs"
            ],
            "tokens_used": 1250,  # Mock token count
            "cost_estimate": 0.025  # Mock cost estimate
        }
    
    def _store_assessment(self, assessment: AssessmentResponse):
        """Store assessment in memory (will be replaced with database)"""
        self.assessments[assessment.assessment_id] = assessment
        
        if assessment.user_id not in self.user_assessments:
            self.user_assessments[assessment.user_id] = []
        
        self.user_assessments[assessment.user_id].append(assessment.assessment_id)
    
    async def get_assessment_history(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        assessment_type: Optional[str] = None
    ) -> AssessmentHistoryResponse:
        """Retrieve assessment history for a user"""
        
        if user_id not in self.user_assessments:
            return AssessmentHistoryResponse(
                user_id=user_id,
                assessments=[],
                total_count=0,
                has_more=False
            )
        
        # Get assessment IDs for user
        assessment_ids = self.user_assessments[user_id]
        
        # Apply filters
        filtered_assessments = []
        for assessment_id in assessment_ids:
            assessment = self.assessments[assessment_id]
            if assessment_type and assessment.assessment_type != assessment_type:
                continue
            filtered_assessments.append(assessment)
        
        # Sort by timestamp (newest first)
        filtered_assessments.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        total_count = len(filtered_assessments)
        paginated_assessments = filtered_assessments[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return AssessmentHistoryResponse(
            user_id=user_id,
            assessments=paginated_assessments,
            total_count=total_count,
            has_more=has_more
        )
    
    async def get_assessment_summary(self, user_id: str) -> AssessmentSummary:
        """Generate assessment summary and analytics for a user"""
        
        if user_id not in self.user_assessments:
            return AssessmentSummary(
                user_id=user_id,
                total_assessments=0,
                average_overall_score=0.0,
                average_confidence=0.0,
                dimension_averages={},
                recent_trend="No assessments",
                strongest_dimension=AssessmentDimension.REQUIREMENTS_ANALYSIS,
                weakest_dimension=AssessmentDimension.REQUIREMENTS_ANALYSIS,
                top_recommendations=[],
                next_assessment_date=None
            )
        
        # Get all assessments for user
        user_assessments = [
            self.assessments[assessment_id] 
            for assessment_id in self.user_assessments[user_id]
        ]
        
        if not user_assessments:
            return AssessmentSummary(
                user_id=user_id,
                total_assessments=0,
                average_overall_score=0.0,
                average_confidence=0.0,
                dimension_averages={},
                recent_trend="No assessments",
                strongest_dimension=AssessmentDimension.REQUIREMENTS_ANALYSIS,
                weakest_dimension=AssessmentDimension.REQUIREMENTS_ANALYSIS,
                top_recommendations=[],
                next_assessment_date=None
            )
        
        # Calculate averages
        total_assessments = len(user_assessments)
        average_overall_score = sum(a.overall_score for a in user_assessments) / total_assessments
        average_confidence = sum(a.confidence_score for a in user_assessments) / total_assessments
        
        # Calculate dimension averages
        dimension_totals = {dim: [] for dim in AssessmentDimension}
        for assessment in user_assessments:
            for dim, score in assessment.dimension_scores.items():
                dimension_totals[dim].append(score.score)
        
        dimension_averages = {
            dim: sum(scores) / len(scores) if scores else 0.0
            for dim, scores in dimension_totals.items()
        }
        
        # Determine strongest and weakest dimensions
        strongest_dimension = max(dimension_averages.items(), key=lambda x: x[1])[0]
        weakest_dimension = min(dimension_averages.items(), key=lambda x: x[1])[0]
        
        # Analyze recent trend (last 3 assessments)
        recent_assessments = sorted(user_assessments, key=lambda x: x.timestamp)[-3:]
        if len(recent_assessments) >= 2:
            recent_scores = [a.overall_score for a in recent_assessments]
            if recent_scores[-1] > recent_scores[0]:
                recent_trend = "Improving"
            elif recent_scores[-1] < recent_scores[0]:
                recent_trend = "Declining"
            else:
                recent_trend = "Stable"
        else:
            recent_trend = "Insufficient data"
        
        # Generate top recommendations
        all_recommendations = []
        for assessment in user_assessments:
            all_recommendations.extend(assessment.recommendations)
        
        # Count recommendation frequency
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        # Get top 3 most frequent recommendations
        top_recommendations = sorted(
            recommendation_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        top_recommendations = [rec[0] for rec in top_recommendations]
        
        # Suggest next assessment date (every 2 weeks)
        if user_assessments:
            last_assessment = max(user_assessments, key=lambda x: x.timestamp)
            next_assessment_date = last_assessment.timestamp.replace(
                day=last_assessment.timestamp.day + 14
            )
        else:
            next_assessment_date = None
        
        return AssessmentSummary(
            user_id=user_id,
            total_assessments=total_assessments,
            average_overall_score=round(average_overall_score, 2),
            average_confidence=round(average_confidence, 2),
            dimension_averages=dimension_averages,
            recent_trend=recent_trend,
            strongest_dimension=strongest_dimension,
            weakest_dimension=weakest_dimension,
            top_recommendations=top_recommendations,
            next_assessment_date=next_assessment_date
        )
    
    def get_assessment(self, assessment_id: str) -> Optional[AssessmentResponse]:
        """Retrieve a specific assessment by ID"""
        return self.assessments.get(assessment_id)
    
    def delete_assessment(self, assessment_id: str) -> bool:
        """Delete an assessment (admin function)"""
        if assessment_id in self.assessments:
            assessment = self.assessments[assessment_id]
            user_id = assessment.user_id
            
            # Remove from user's assessment list
            if user_id in self.user_assessments:
                self.user_assessments[user_id] = [
                    aid for aid in self.user_assessments[user_id] 
                    if aid != assessment_id
                ]
            
            # Remove assessment
            del self.assessments[assessment_id]
            return True
        
        return False
    
    def cleanup_old_assessments(self, max_age_days: int = 90):
        """Clean up old assessments (memory management)"""
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time.replace(day=current_time.day - max_age_days)
        
        assessments_to_delete = []
        for assessment_id, assessment in self.assessments.items():
            if assessment.timestamp < cutoff_time:
                assessments_to_delete.append(assessment_id)
        
        for assessment_id in assessments_to_delete:
            self.delete_assessment(assessment_id)
        
        logger.info(f"Cleaned up {len(assessments_to_delete)} old assessments")
