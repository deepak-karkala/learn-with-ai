from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.adk_service import ADKService, ChatRequest, ChatResponse
from app.services.config import settings, setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(settings)

# ADK service will be initialized properly with dependency injection
adk_service: Optional[ADKService] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown for proper resource management"""
    global adk_service

    # Startup
    try:
        adk_service = ADKService()
        yield
    except Exception as e:
        # Log startup error but don't crash the app
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize ADK service: {e}")
        adk_service = None
        yield
    finally:
        # Shutdown - cleanup resources
        if adk_service:
            await adk_service.cleanup()


# Create FastAPI app with proper lifecycle management
app = FastAPI(
    title=settings.api_title,
    description="Backend API for AI-powered system design learning",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://frontend-hckhrw1r3-dkarkala01-gmailcoms-projects.vercel.app",
        "https://your-app.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)


@app.get("/")
async def root() -> dict:
    """Root endpoint"""
    return {"message": "AI System Design Learning Platform API"}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running successfully",
        "version": "0.1.0",
    }


@app.get("/api/health")
async def api_health_check() -> dict:
    """API health check endpoint"""
    if adk_service is None:
        adk_status = {"status": "not_initialized"}
    else:
        adk_status = adk_service.health_check()
    return {
        "status": "healthy",
        "api_version": settings.api_version,
        "services": {
            "fastapi": "running",
            "adk": adk_status["status"],
            "database": "not_configured",
        },
        "adk_info": adk_status,
    }


@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """
    Chat with the system design learning agent using ADK.

    Args:
        request: Chat request with message, user_id, and optional session_id

    Returns:
        Chat response from the ADK agent
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received ADK chat request from user {request.user_id}")

        # Check if ADK service is available
        if adk_service is None:
            raise HTTPException(status_code=503, detail="ADK service is not available")

        # Get response from ADK service
        response = await adk_service.chat(request)

        # Log the response status
        if response.success:
            logger.info(
                f"Successfully processed ADK chat for user {request.user_id}, "
                f"session {response.session_id}"
            )
        else:
            logger.warning(
                f"ADK service returned error for user {request.user_id}: {response.error}"
            )

        return response

    except Exception as e:
        logger.error(
            f"Unexpected error in ADK chat endpoint for user {request.user_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/sessions/{user_id}/{session_id}")
async def get_session_info(user_id: str, session_id: str) -> dict:
    """
    Get information about a specific user session.

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        Session information
    """
    try:
        if adk_service is None:
            raise HTTPException(status_code=503, detail="ADK service is not available")
        session_info = adk_service.get_session_info(user_id, session_id)
        return session_info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session info: {str(e)}",
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
