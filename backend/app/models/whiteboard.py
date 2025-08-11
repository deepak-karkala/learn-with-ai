"""
Whiteboard-related Pydantic models for PNG upload and analysis.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
import base64


class PNGUploadRequest(BaseModel):
    """Request model for PNG upload"""
    
    png_data: str = Field(..., description="Base64 encoded PNG data")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(
        None, description="Session identifier"
    )
    description: Optional[str] = Field(
        None, description="Optional description of the whiteboard content"
    )
    
    @validator('png_data')
    def validate_png_data(cls, v):
        """Validate PNG data format"""
        if not v:
            raise ValueError("PNG data cannot be empty")
        
        # Check if it's a valid base64 string
        try:
            # Remove data URL prefix if present
            if v.startswith('data:image/png;base64,'):
                v = v.split(',', 1)[1]
            
            # Decode base64 to check if it's valid
            decoded = base64.b64decode(v)
            
            # Basic PNG header validation (PNG files start with specific bytes)
            png_header = b'\x89PNG\r\n\x1a\n'
            if len(decoded) < 8 or decoded[:8] != png_header:
                raise ValueError("Invalid PNG format")
                
            # Check reasonable file size (max 10MB)
            max_size = 10 * 1024 * 1024
            if len(decoded) > max_size:
                raise ValueError("PNG file too large (max 10MB)")
                
        except Exception as e:
            raise ValueError(f"Invalid PNG data: {str(e)}")
        
        return v


class PNGUploadResponse(BaseModel):
    """Response model for PNG upload"""
    
    artifact_id: str = Field(..., description="Unique identifier for the uploaded PNG")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Response message")
    file_size: int = Field(..., description="File size in bytes")
    created_at: str = Field(..., description="Upload timestamp")


class WhiteboardAnalysisRequest(BaseModel):
    """Request model for whiteboard analysis"""
    
    artifact_id: str = Field(..., description="PNG artifact identifier to analyze")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")


class WhiteboardAnalysisResponse(BaseModel):
    """Response model for whiteboard analysis"""

    artifact_id: str = Field(..., description="PNG artifact identifier")
    analysis_id: str = Field(..., description="Analysis identifier")
    components_identified: list = Field(..., description="List of system components identified")
    architectural_feedback: str = Field(
        ..., description="Architectural feedback and suggestions"
    )
    suggestions: list = Field(..., description="List of improvement suggestions")
    confidence_score: float = Field(..., description="Confidence score (0.0 to 1.0)")
    status: str = Field(..., description="Analysis status")
    created_at: str = Field(..., description="Analysis timestamp")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost of analysis")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    raw_analysis: Optional[str] = Field(None, description="Raw LLM analysis text")
