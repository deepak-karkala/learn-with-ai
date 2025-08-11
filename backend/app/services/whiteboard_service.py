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
            
            # For now, return mock analysis
            # TODO: Integrate with actual multimodal LLM
            analysis = {
                'id': analysis_id,
                'artifact_id': request.artifact_id,
                'components_identified': [
                    'Load Balancer',
                    'Web Server', 
                    'Database',
                    'Redis Cache'
                ],
                'architectural_feedback': (
                    "Good basic architecture with clear separation of concerns. "
                    "Consider adding monitoring, logging, and API gateway for "
                    "production readiness."
                ),
                'suggestions': [
                    'Add health check endpoints',
                    'Implement circuit breakers',
                    'Consider CDN for static assets',
                    'Add message queue for async processing'
                ],
                'confidence_score': 0.85,
                'status': 'completed',
                'created_at': datetime.utcnow().isoformat()
            }
            
            self._analyses[analysis_id] = analysis
            
            logger.info(f"Whiteboard analysis completed: {analysis_id}")
            
            return WhiteboardAnalysisResponse(
                artifact_id=request.artifact_id,
                analysis_id=analysis_id,
                components_identified=analysis['components_identified'],
                architectural_feedback=analysis['architectural_feedback'],
                suggestions=analysis['suggestions'],
                confidence_score=analysis['confidence_score'],
                status=analysis['status'],
                created_at=analysis['created_at']
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze whiteboard: {e}")
            raise Exception(f"Analysis failed: {str(e)}")
    
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
