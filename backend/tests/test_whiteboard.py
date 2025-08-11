"""
Tests for whiteboard PNG upload and analysis functionality.
"""

import pytest
import base64
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient

from app.models.whiteboard import PNGUploadRequest, WhiteboardAnalysisRequest
from app.services.whiteboard_service import WhiteboardService
from app.services.adk_service import ADKService


class TestWhiteboardService:
    """Test whiteboard service functionality."""
    
    @pytest.fixture
    def mock_adk_service(self):
        """Mock ADK service."""
        mock_service = Mock(spec=ADKService)
        mock_service.store_artifact = AsyncMock()
        
        # Mock multimodal analysis response
        mock_multimodal_response = Mock()
        mock_multimodal_response.success = True
        mock_multimodal_response.analysis = """
        COMPONENTS: Load Balancer, Web Server, Database, Redis Cache
        FEEDBACK: Good basic architecture with clear separation of concerns.
        SUGGESTIONS: Add health check endpoints, Implement circuit breakers
        """
        mock_multimodal_response.confidence_score = 0.85
        mock_multimodal_response.cost_estimate = 0.005
        mock_multimodal_response.tokens_used = 150
        
        mock_service.analyze_image_multimodal = AsyncMock(
            return_value=mock_multimodal_response
        )
        
        return mock_service
    
    @pytest.fixture
    def whiteboard_service(self, mock_adk_service):
        """Whiteboard service instance."""
        return WhiteboardService(mock_adk_service)
    
    @pytest.fixture
    def sample_png_data(self):
        """Sample PNG data for testing."""
        # Create a minimal valid PNG file (1x1 transparent pixel)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'  # PNG header
            b'\x00\x00\x00\x0d'   # IHDR chunk length
            b'IHDR'                # IHDR chunk type
            b'\x00\x00\x00\x01'   # Width: 1
            b'\x00\x00\x00\x01'   # Height: 1
            b'\x08'                # Bit depth: 8
            b'\x06'                # Color type: RGBA
            b'\x00'                # Compression: deflate
            b'\x00'                # Filter: none
            b'\x00'                # Interlace: none
            b'\x1f\x15\xc4\x89'   # CRC
            b'\x00\x00\x00\x0c'   # IDAT chunk length
            b'IDAT'                # IDAT chunk type
            b'\x08\x99\x01\x01\x00\x00\x00\xff\xff'  # Compressed data
            b'\x00\x00\x00\x00'   # CRC
            b'\x00\x00\x00\x00'   # IEND chunk length
            b'IEND'                # IEND chunk type
            b'\xae\x42\x60\x82'   # CRC
        )
        return base64.b64encode(png_bytes).decode()
    
    @pytest.mark.asyncio
    async def test_upload_png_success(self, whiteboard_service, sample_png_data):
        """Test successful PNG upload."""
        request = PNGUploadRequest(
            png_data=sample_png_data,
            user_id="test_user",
            session_id="test_session",
            description="Test diagram"
        )
        
        response = await whiteboard_service.upload_png(request)
        
        assert response.status == "success"
        assert response.user_id == "test_user"
        assert response.session_id == "test_session"
        assert response.file_size > 0
        assert response.artifact_id is not None
        
        # Verify artifact was stored
        artifact = whiteboard_service.get_artifact(response.artifact_id)
        assert artifact is not None
        assert artifact['user_id'] == "test_user"
        assert artifact['png_data'] == sample_png_data
    
    @pytest.mark.asyncio
    async def test_upload_png_with_data_url(self, whiteboard_service, sample_png_data):
        """Test PNG upload with data URL prefix."""
        data_url = f"data:image/png;base64,{sample_png_data}"
        request = PNGUploadRequest(
            png_data=data_url,
            user_id="test_user",
            session_id="test_session"
        )
        
        response = await whiteboard_service.upload_png(request)
        
        assert response.status == "success"
        assert response.artifact_id is not None
        
        # Verify data URL prefix was removed
        artifact = whiteboard_service.get_artifact(response.artifact_id)
        assert artifact['png_data'] == sample_png_data
    
    def test_upload_png_invalid_format_validation(self):
        """Test PNG upload validation with invalid format."""
        invalid_data = "invalid_png_data"
        
        with pytest.raises(Exception, match="Invalid PNG data"):
            PNGUploadRequest(
                png_data=invalid_data,
                user_id="test_user"
            )
    
    def test_upload_png_empty_data_validation(self):
        """Test PNG upload validation with empty data."""
        with pytest.raises(Exception, match="PNG data cannot be empty"):
            PNGUploadRequest(
                png_data="",
                user_id="test_user"
            )
    
    @pytest.mark.asyncio
    async def test_analyze_whiteboard_success(self, whiteboard_service, sample_png_data):
        """Test successful whiteboard analysis using multimodal LLM."""
        # First upload a PNG
        upload_request = PNGUploadRequest(
            png_data=sample_png_data,
            user_id="test_user",
            session_id="test_session"
        )
        
        upload_response = await whiteboard_service.upload_png(upload_request)
        artifact_id = upload_response.artifact_id
        
        # Request analysis
        analysis_request = WhiteboardAnalysisRequest(
            artifact_id=artifact_id,
            user_id="test_user",
            session_id="test_session",
            analysis_type="comprehensive"
        )
        
        response = await whiteboard_service.analyze_whiteboard(analysis_request)
        
        assert response.artifact_id == artifact_id
        assert response.status == "completed"
        assert response.confidence_score > 0
        assert len(response.components_identified) > 0
        assert response.architectural_feedback
        assert len(response.suggestions) > 0
        
        # Verify analysis was stored with metadata
        analysis = whiteboard_service.get_analysis(response.analysis_id)
        assert analysis is not None
        assert analysis['cost_estimate'] is not None
        assert analysis['tokens_used'] is not None
        assert analysis['raw_analysis'] is not None
        
        # Verify ADK service was called
        whiteboard_service.adk_service.analyze_image_multimodal.assert_called_once()
    
    def test_create_analysis_prompt(self, whiteboard_service):
        """Test analysis prompt creation for different types."""
        # Test comprehensive analysis
        comprehensive_prompt = whiteboard_service._create_analysis_prompt("comprehensive")
        assert "COMPONENTS:" in comprehensive_prompt
        assert "FEEDBACK:" in comprehensive_prompt
        assert "SUGGESTIONS:" in comprehensive_prompt
        assert "Data flow patterns" in comprehensive_prompt
        assert "monitoring" in comprehensive_prompt.lower()
        
        # Test security analysis
        security_prompt = whiteboard_service._create_analysis_prompt("security")
        assert "security" in security_prompt.lower()
        assert "authentication" in security_prompt.lower()
        assert "encryption" in security_prompt.lower()
        
        # Test performance analysis
        performance_prompt = whiteboard_service._create_analysis_prompt("performance")
        assert "performance" in performance_prompt.lower()
        assert "bottlenecks" in performance_prompt.lower()
        assert "caching" in performance_prompt.lower()
    
    def test_parse_analysis_response(self, whiteboard_service):
        """Test parsing of LLM analysis responses."""
        # Test structured response parsing
        structured_response = """
        COMPONENTS: Load Balancer, Web Server, Database
        FEEDBACK: Good architecture with clear separation
        SUGGESTIONS: Add monitoring, implement caching
        """
        
        parsed = whiteboard_service._parse_analysis_response(
            structured_response, "comprehensive"
        )
        
        assert "Load Balancer" in parsed['components']
        assert "Web Server" in parsed['components']
        assert "Database" in parsed['components']
        assert "Good architecture" in parsed['feedback']
        assert "Add monitoring" in parsed['suggestions']
        
        # Test fallback parsing for unstructured responses
        unstructured_response = "This is a system with a load balancer and web server. You should add monitoring."
        
        parsed = whiteboard_service._parse_analysis_response(
            unstructured_response, "comprehensive"
        )
        
        assert "Load Balancer" in parsed['components']
        assert "Web Server" in parsed['components']
        assert "monitoring" in parsed['suggestions'][0].lower()
    
    @pytest.mark.asyncio
    async def test_analyze_whiteboard_artifact_not_found(self, whiteboard_service):
        """Test analysis with non-existent artifact."""
        request = WhiteboardAnalysisRequest(
            artifact_id="non_existent_id",
            user_id="test_user"
        )
        
        with pytest.raises(Exception, match="Artifact not found"):
            await whiteboard_service.analyze_whiteboard(request)
    
    def test_get_user_artifacts(self, whiteboard_service, sample_png_data):
        """Test retrieving user artifacts."""
        # Upload multiple PNGs for different users
        user1_artifacts = []
        user2_artifacts = []
        
        for i in range(3):
            # Create mock artifacts
            artifact_id = f"artifact_{i}"
            whiteboard_service._artifacts[artifact_id] = {
                'id': artifact_id,
                'user_id': f"user_{i % 2 + 1}",
                'png_data': sample_png_data,
                'file_size': 100,
                'created_at': "2025-01-01T00:00:00"
            }
            
            if i % 2 == 0:
                user1_artifacts.append(artifact_id)
            else:
                user2_artifacts.append(artifact_id)
        
        # Get artifacts for user 1
        user1_results = whiteboard_service.get_user_artifacts("user_1")
        assert len(user1_results) == 2
        
        # Get artifacts for user 2
        user2_results = whiteboard_service.get_user_artifacts("user_2")
        assert len(user2_results) == 1
    
    def test_cleanup_old_artifacts(self, whiteboard_service):
        """Test cleanup of old artifacts."""
        from datetime import datetime, timedelta
        
        # Create mock artifacts with proper datetime objects
        now = datetime.utcnow()
        old_timestamp = (now - timedelta(hours=3)).isoformat()  # 3 hours old
        recent_timestamp = now.isoformat()
        
        whiteboard_service._artifacts = {
            "old1": {"created_at": old_timestamp},
            "old2": {"created_at": old_timestamp},
            "recent": {"created_at": recent_timestamp}
        }
        
        # Clean up artifacts older than 1 hour
        cleaned_count = whiteboard_service.cleanup_old_artifacts(max_age_hours=1)
        
        assert cleaned_count == 2
        assert "recent" in whiteboard_service._artifacts
        assert "old1" not in whiteboard_service._artifacts
        assert "old2" not in whiteboard_service._artifacts


class TestWhiteboardAPI:
    """Test whiteboard API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Test client with initialized services."""
        from app.main import app
        from app.services.whiteboard_service import WhiteboardService
        from app.services.adk_service import ADKService
        
        # Create a test client with manually initialized services
        test_app = app
        
        # Initialize services for testing
        test_adk_service = ADKService()
        test_whiteboard_service = WhiteboardService(test_adk_service)
        
        # Override the global services in the app
        import app.main
        app.main.whiteboard_service = test_whiteboard_service
        app.main.adk_service = test_adk_service
        
        return TestClient(test_app)
    
    @pytest.fixture
    def sample_png_data(self):
        """Sample PNG data for testing."""
        # Create a minimal valid PNG file (1x1 transparent pixel)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'  # PNG header
            b'\x00\x00\x00\x0d'   # IHDR chunk length
            b'IHDR'                # IHDR chunk type
            b'\x00\x00\x00\x01'   # Width: 1
            b'\x00\x00\x00\x01'   # Height: 1
            b'\x08'                # Bit depth: 8
            b'\x06'                # Color type: RGBA
            b'\x00'                # Compression: deflate
            b'\x00'                # Filter: none
            b'\x00'                # Interlace: none
            b'\x1f\x15\xc4\x89'   # CRC
            b'\x00\x00\x00\x0c'   # IDAT chunk length
            b'IDAT'                # IDAT chunk type
            b'\x08\x99\x01\x01\x00\x00\x00\xff\xff'  # Compressed data
            b'\x00\x00\x00\x00'   # CRC
            b'\x00\x00\x00\x00'   # IEND chunk length
            b'IEND'                # IEND chunk type
            b'\xae\x42\x60\x82'   # CRC
        )
        return base64.b64encode(png_bytes).decode()
    
    def test_upload_png_endpoint(self, client, sample_png_data):
        """Test PNG upload endpoint."""
        response = client.post("/api/whiteboard/upload", json={
            "png_data": sample_png_data,
            "user_id": "test_user",
            "session_id": "test_session",
            "description": "Test diagram"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "artifact_id" in data
        assert data["user_id"] == "test_user"
        assert data["file_size"] > 0
    
    def test_upload_png_invalid_data(self, client):
        """Test PNG upload with invalid data."""
        response = client.post("/api/whiteboard/upload", json={
            "png_data": "invalid_data",
            "user_id": "test_user"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_png_missing_data(self, client):
        """Test PNG upload with missing data."""
        response = client.post("/api/whiteboard/upload", json={
            "user_id": "test_user"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_whiteboard_endpoint(self, client, sample_png_data):
        """Test whiteboard analysis endpoint."""
        # First upload a PNG
        upload_response = client.post("/api/whiteboard/upload", json={
            "png_data": sample_png_data,
            "user_id": "test_user"
        })
        assert upload_response.status_code == 200
        artifact_id = upload_response.json()["artifact_id"]
        
        # Then analyze it
        analysis_response = client.post("/api/whiteboard/analyze", json={
            "artifact_id": artifact_id,
            "user_id": "test_user",
            "analysis_type": "comprehensive"
        })
        
        assert analysis_response.status_code == 200
        data = analysis_response.json()
        assert data["status"] == "completed"
        assert data["artifact_id"] == artifact_id
        assert "components_identified" in data
        assert "architectural_feedback" in data
        assert "suggestions" in data
        assert "confidence_score" in data
    
    def test_analyze_whiteboard_artifact_not_found(self, client):
        """Test analysis with non-existent artifact."""
        response = client.post("/api/whiteboard/analyze", json={
            "artifact_id": "non_existent_id",
            "user_id": "test_user"
        })
        
        assert response.status_code == 500
