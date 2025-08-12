from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DiagramType(str, Enum):
    ARCHITECTURE = "architecture"
    SEQUENCE = "sequence"
    FLOWCHART = "flowchart"
    WORKFLOW = "workflow"
    CLASS = "class"
    DATABASE = "database"
    NETWORK = "network"
    STATE = "state"
    GANTT = "gantt"


class DiagramGenerationRequest(BaseModel):
    system_description: str = Field(
        ...,
        description="A natural language description of the system to be diagrammed.",
        example="A simple web application with a load balancer, two web servers, and a database.",
    )
    diagram_type: DiagramType = Field(
        ...,
        description="The type of diagram to generate.",
        example=DiagramType.ARCHITECTURE,
    )
    user_id: str = Field(..., description="The ID of the user requesting the diagram.")
    session_id: Optional[str] = Field(
        None, description="The session ID for context, if available."
    )


class DiagramGenerationResponse(BaseModel):
    diagram_id: str = Field(..., description="The unique ID of the generated diagram artifact.")
    mermaid_code: str = Field(..., description="The generated Mermaid markdown code.")
    png_artifact_id: str = Field(
        ..., description="The artifact ID of the rendered PNG image."
    )
    status: str = Field("success", description="The status of the generation request.")
    model_used: str = Field(
        ..., description="The model used for generating the Mermaid code."
    )
    tokens_used: int = Field(..., description="The number of tokens used.")
    cost_estimate: float = Field(..., description="The estimated cost of the generation.")
