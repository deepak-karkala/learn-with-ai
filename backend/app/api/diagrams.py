from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.diagram import DiagramGenerationRequest, DiagramGenerationResponse
from app.services.diagram_service import DiagramService

router = APIRouter(prefix="/diagrams", tags=["diagrams"])

def get_diagram_service(request: Request) -> DiagramService:
    # This dependency assumes the service is attached to the app state
    diagram_service = getattr(request.app.state, "diagram_service", None)
    if diagram_service is None:
        raise HTTPException(status_code=503, detail="Diagram service is not available.")
    return diagram_service


@router.post("/generate", response_model=DiagramGenerationResponse)
async def generate_diagram(
    request: DiagramGenerationRequest,
    diagram_service: DiagramService = Depends(get_diagram_service),
):
    """
    Generates a system design diagram from a natural language description.
    """
    try:
        response = await diagram_service.generate_diagram(request)
        return response
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Diagram rendering failed: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
