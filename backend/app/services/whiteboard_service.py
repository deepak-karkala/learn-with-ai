"""
Whiteboard service for handling PNG uploads and analysis.
"""

import base64
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.whiteboard import (
    PNGUploadRequest, 
    PNGUploadResponse,
    WhiteboardAnalysisRequest,
    WhiteboardAnalysisResponse
)
from app.services.adk_service import ADKService
from app.services.performance_service import monitor_performance

logger = logging.getLogger(__name__)


class WhiteboardService:
    """Service for managing whiteboard PNG uploads and analysis."""
    
    def __init__(self, adk_service: ADKService):
        """Initialize the whiteboard service."""
        self.adk_service = adk_service
        self._artifacts: Dict[str, Dict[str, Any]] = {}
        self._analyses: Dict[str, Dict[str, Any]] = {}
    
    async def upload_png(self, request: PNGUploadRequest) -> PNGUploadResponse:
        """Upload and store PNG data as an artifact."""
        try:
            # Generate unique artifact ID
            artifact_id = str(uuid.uuid4())
            
            # Extract PNG data (remove data URL prefix if present)
            png_data = request.png_data
            if png_data.startswith('data:image/png;base64,'):
                png_data = png_data.split(',', 1)[1]
            
            # Decode to get file size
            decoded_data = base64.b64decode(png_data)
            file_size = len(decoded_data)
            
            # Store artifact metadata
            artifact = {
                'id': artifact_id,
                'user_id': request.user_id,
                'session_id': request.session_id,
                'png_data': png_data,
                'file_size': file_size,
                'description': request.description,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'stored'
            }
            
            self._artifacts[artifact_id] = artifact
            
            # Store in ADK artifacts system if available
            try:
                if hasattr(self.adk_service, 'store_artifact'):
                    await self.adk_service.store_artifact(
                        artifact_id, 
                        decoded_data,
                        metadata={
                            'type': 'whiteboard_png',
                            'user_id': request.user_id,
                            'session_id': request.session_id,
                            'description': request.description
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to store in ADK artifacts: {e}")
                # Continue with local storage
            
            logger.info(f"PNG uploaded successfully: {artifact_id} ({file_size} bytes)")
            
            return PNGUploadResponse(
                artifact_id=artifact_id,
                user_id=request.user_id,
                session_id=request.session_id,
                status="success",
                message="PNG uploaded successfully",
                file_size=file_size,
                created_at=artifact['created_at']
            )
            
        except Exception as e:
            logger.error(f"Failed to upload PNG: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    @monitor_performance("whiteboard_analysis", "whiteboard_analysis_result")
    async def analyze_whiteboard(
        self, 
        request: WhiteboardAnalysisRequest
    ) -> WhiteboardAnalysisResponse:
        """Analyze whiteboard PNG using multimodal LLM."""
        try:
            # Get artifact
            artifact = self._artifacts.get(request.artifact_id)
            if not artifact:
                raise Exception("Artifact not found")
            
            # Generate analysis ID
            analysis_id = str(uuid.uuid4())
            
            # Create structured analysis prompt
            analysis_prompt = self._create_analysis_prompt(request.analysis_type)
            
            # Decode PNG data for analysis
            png_data = artifact['png_data']
            if png_data.startswith('data:image/png;base64,'):
                png_data = png_data.split(',', 1)[1]
            
            decoded_data = base64.b64decode(png_data)
            
            # Use ADK service for multimodal analysis
            from app.services.adk_service import MultimodalAnalysisRequest
            
            multimodal_request = MultimodalAnalysisRequest(
                image_data=decoded_data,
                prompt=analysis_prompt,
                user_id=request.user_id,
                session_id=request.session_id,
                analysis_type=request.analysis_type
            )
            
            # Perform multimodal analysis
            multimodal_response = await self.adk_service.analyze_image_multimodal(
                multimodal_request
            )
            
            if not multimodal_response.success:
                raise Exception(f"Multimodal analysis failed: {multimodal_response.error}")
            
            # Parse the analysis response to extract structured information
            parsed_analysis = self._parse_analysis_response(
                multimodal_response.analysis,
                request.analysis_type
            )
            
            # Store analysis metadata
            analysis = {
                'id': analysis_id,
                'artifact_id': request.artifact_id,
                'components_identified': parsed_analysis['components'],
                'architectural_feedback': parsed_analysis['feedback'],
                'suggestions': parsed_analysis['suggestions'],
                'confidence_score': multimodal_response.confidence_score or 0.8,
                'status': 'completed',
                'created_at': datetime.utcnow().isoformat(),
                'cost_estimate': multimodal_response.cost_estimate,
                'tokens_used': multimodal_response.tokens_used,
                'raw_analysis': multimodal_response.analysis
            }
            
            self._analyses[analysis_id] = analysis
            
            logger.info(
                f"Whiteboard analysis completed: {analysis_id}, "
                f"cost: {multimodal_response.cost_estimate}"
            )
            
            return WhiteboardAnalysisResponse(
                artifact_id=request.artifact_id,
                analysis_id=analysis_id,
                components_identified=analysis['components_identified'],
                architectural_feedback=analysis['architectural_feedback'],
                suggestions=analysis['suggestions'],
                confidence_score=analysis['confidence_score'],
                status=analysis['status'],
                created_at=analysis['created_at'],
                cost_estimate=analysis['cost_estimate'],
                tokens_used=analysis['tokens_used'],
                raw_analysis=analysis['raw_analysis']
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze whiteboard: {e}")
            raise Exception(f"Analysis failed: {str(e)}")
    
    def _create_analysis_prompt(self, analysis_type: str) -> str:
        """Create a structured prompt for whiteboard analysis."""
        base_prompt = """
        Analyze this system design whiteboard diagram and provide structured feedback.
        
        Please identify:
        1. System components and their types (e.g., Load Balancer, Web Server, Database, Cache, etc.)
        2. Architectural patterns and design decisions
        3. Potential improvements and best practices
        4. Any security, scalability, or performance considerations
        
        Format your response as:
        COMPONENTS: [list of identified components]
        FEEDBACK: [architectural feedback and observations]
        SUGGESTIONS: [specific improvement suggestions]
        """
        
        if analysis_type == "comprehensive":
            base_prompt += """
            Additional analysis should include:
            - Data flow patterns
            - Integration points
            - Monitoring and observability considerations
            - Disaster recovery and backup strategies
            """
        elif analysis_type == "security":
            base_prompt += """
            Focus on security aspects:
            - Authentication and authorization
            - Data encryption
            - Network security
            - Compliance considerations
            """
        elif analysis_type == "performance":
            base_prompt += """
            Focus on performance aspects:
            - Bottlenecks and optimization opportunities
            - Caching strategies
            - Load balancing considerations
            - Scalability patterns
            """
        
        return base_prompt.strip()
    
    def _parse_analysis_response(self, analysis_text: str, analysis_type: str) -> Dict[str, Any]:
        """Parse the LLM analysis response to extract structured information."""
        # Default fallback values
        components = []
        feedback = "Analysis completed successfully."
        suggestions = []
        
        try:
            # Try to extract structured information from the response
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('COMPONENTS:'):
                    components_text = line.replace('COMPONENTS:', '').strip()
                    components = [c.strip() for c in components_text.split(',') if c.strip()]
                elif line.startswith('FEEDBACK:'):
                    feedback = line.replace('FEEDBACK:', '').strip()
                elif line.startswith('SUGGESTIONS:'):
                    suggestions_text = line.replace('SUGGESTIONS:', '').strip()
                    suggestions = [s.strip() for s in suggestions_text.split(',') if s.strip()]
            
            # If structured parsing failed, try to extract information from the text
            if not components:
                # Look for common system components in the text
                component_keywords = [
                    'load balancer', 'web server', 'database', 'cache', 'redis',
                    'api gateway', 'microservice', 'message queue', 'monitoring',
                    'logging', 'authentication', 'authorization'
                ]
                
                for keyword in component_keywords:
                    if keyword.lower() in analysis_text.lower():
                        components.append(keyword.title())
            
            if not suggestions:
                # Extract suggestions from the text
                suggestion_indicators = ['should', 'could', 'consider', 'add', 'implement']
                sentences = analysis_text.split('.')
                for sentence in sentences:
                    if any(indicator in sentence.lower() for indicator in suggestion_indicators):
                        suggestions.append(sentence.strip())
                        if len(suggestions) >= 5:  # Limit to 5 suggestions
                            break
            
            # Ensure we have at least some content
            if not components:
                components = ['System Components (Analysis in progress)']
            if not feedback:
                feedback = analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text
            if not suggestions:
                suggestions = ['Review the architecture for best practices']
                
        except Exception as e:
            logger.warning(f"Failed to parse analysis response: {e}")
            # Use fallback values
        
        return {
            'components': components,
            'feedback': feedback,
            'suggestions': suggestions
        }
    
    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact by ID."""
        return self._artifacts.get(artifact_id)
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID."""
        return self._analyses.get(analysis_id)
    
    def get_user_artifacts(self, user_id: str) -> list:
        """Get all artifacts for a user."""
        return [
            artifact for artifact in self._artifacts.values()
            if artifact['user_id'] == user_id
        ]
    
    def cleanup_old_artifacts(self, max_age_hours: int = 24) -> int:
        """Clean up old artifacts to free memory."""
        from datetime import datetime, timezone
        
        current_time = datetime.now(timezone.utc)
        max_age_seconds = max_age_hours * 3600
        
        artifacts_to_remove = []
        for artifact_id, artifact in self._artifacts.items():
            try:
                # Parse the ISO timestamp and make it timezone-aware
                created_time = datetime.fromisoformat(artifact['created_at'])
                if created_time.tzinfo is None:
                    created_time = created_time.replace(tzinfo=timezone.utc)
                
                # Calculate age in seconds
                age_seconds = (current_time - created_time).total_seconds()
                
                if age_seconds > max_age_seconds:
                    artifacts_to_remove.append(artifact_id)
                    
            except Exception as e:
                logger.warning(f"Error processing artifact {artifact_id}: {e}")
                continue
        
        for artifact_id in artifacts_to_remove:
            del self._artifacts[artifact_id]
        
        logger.info(f"Cleaned up {len(artifacts_to_remove)} old artifacts")
        return len(artifacts_to_remove)

    async def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact data by ID."""
        return self._artifacts.get(artifact_id)
