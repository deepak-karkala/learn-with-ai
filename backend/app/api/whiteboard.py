from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.whiteboard import (
    PNGUploadRequest,
    PNGUploadResponse,
    WhiteboardAnalysisRequest,
    WhiteboardAnalysisResponse,
)
from app.services.whiteboard_service import WhiteboardService

router = APIRouter(prefix="/whiteboard", tags=["whiteboard"])


def get_whiteboard_service(request: Request) -> WhiteboardService:
    whiteboard_service = getattr(request.app.state, "whiteboard_service", None)
    if whiteboard_service is None:
        raise HTTPException(
            status_code=503, detail="Whiteboard service is not available."
        )
    return whiteboard_service


@router.post("/upload", response_model=PNGUploadResponse)
async def upload_png(
    request: PNGUploadRequest,
    whiteboard_service: WhiteboardService = Depends(get_whiteboard_service),
):
    try:
        response = await whiteboard_service.upload_png(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/analyze", response_model=WhiteboardAnalysisResponse)
async def analyze_whiteboard(
    request: WhiteboardAnalysisRequest,
    whiteboard_service: WhiteboardService = Depends(get_whiteboard_service),
):
    try:
        response = await whiteboard_service.analyze_whiteboard(request)
        return response
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/artifacts/{artifact_id}")
async def get_artifact(
    artifact_id: str,
    whiteboard_service: WhiteboardService = Depends(get_whiteboard_service),
):
    """Download a PNG artifact by ID."""
    try:
        artifact_data = await whiteboard_service.get_artifact(artifact_id)
        if not artifact_data:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Return the PNG data with proper headers
        from fastapi.responses import Response
        import base64
        
        png_data = base64.b64decode(artifact_data['png_data'])
        
        return Response(
            content=png_data,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=diagram_{artifact_id}.png"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )
