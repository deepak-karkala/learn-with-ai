"""
ADK Service for managing agents and sessions using Google ADK.
"""

import asyncio
import logging
import os
import warnings
from typing import Any, Dict, Optional
from weakref import WeakValueDictionary

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner

# from google.adk.sessions import InMemorySessionService  # Not directly used
from google.genai.types import Content, Part
from pydantic import BaseModel

from app.services.config import settings

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model for ADK agent"""

    message: str
    user_id: str = "default"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model from ADK agent"""

    message: str
    success: bool
    session_id: str
    error: Optional[str] = None


class ADKService:
    """
    Service for managing Google ADK agents and sessions.
    """

    def __init__(self) -> None:
        """Initialize the ADK service"""
        self.session_service: Optional[Any] = None
        self.agent: Optional[Agent] = None
        self.app_name: str = "systemdesign-ai-platform"
        self._env_configured: bool = False  # Track if environment is already configured

        # Connection pooling for performance
        self._runner_pool: Dict[str, InMemoryRunner] = {}
        self._pool_lock = asyncio.Lock()
        self._max_pool_size = 10
        self._sessions: WeakValueDictionary = WeakValueDictionary()

        self._initialize_adk()

    def _configure_environment(self) -> None:
        """Configure environment variables for ADK (only once)"""
        if self._env_configured:
            return  # Skip if already configured

        # ADK expects these environment variables to be set
        if settings.google_api_key:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key
            logger.debug("Set GOOGLE_API_KEY environment variable (key masked for security)")

        if settings.google_genai_use_vertexai:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
            if settings.google_cloud_project:
                os.environ["GOOGLE_CLOUD_PROJECT"] = settings.google_cloud_project
            if settings.google_cloud_location:
                os.environ["GOOGLE_CLOUD_LOCATION"] = settings.google_cloud_location
            logger.debug("Set Vertex AI environment variables")
        else:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
            logger.debug("Set Google AI Studio configuration")

        # Fix SSL certificate issue (as per ADK documentation)
        try:
            import certifi

            os.environ["SSL_CERT_FILE"] = certifi.where()
            logger.debug(f"Set SSL_CERT_FILE to {certifi.where()}")
        except ImportError:
            logger.warning("certifi not installed, SSL verification may fail")

        # Mark environment as configured to avoid redundant setup
        self._env_configured = True
        logger.debug("ADK environment configuration completed")

    def _initialize_adk(self) -> None:
        """Initialize ADK components"""
        try:
            logger.info("Initializing ADK service...")

            # Set environment variables that ADK expects
            self._configure_environment()

            # Create the system design agent using Agent (following streaming pattern)
            self.agent = Agent(
                name="system_design_agent",
                model=settings.adk_model_name,  # Configurable model name
                description="Expert system design interviewer and tutor",
                instruction="""
You are an expert system design interviewer and tutor. Your role is to:

1. **Help software engineers prepare for system design interviews**
   - Guide them through the structured approach to system design
   - Ask clarifying questions about requirements
   - Help them think about scale, constraints, and trade-offs

2. **Provide clear, practical guidance on system architecture**
   - Explain architectural patterns and when to use them
   - Discuss data storage solutions and their trade-offs
   - Cover load balancing, caching, and scalability strategies

3. **Ask thoughtful follow-up questions to deepen understanding**
   - Challenge their assumptions respectfully
   - Help them consider edge cases and failure scenarios
   - Guide them to think about monitoring and observability

4. **Give constructive feedback on design decisions**
   - Point out potential issues and suggest improvements
   - Explain why certain approaches work better than others
   - Help them understand the reasoning behind design choices

**Communication Style:**
- Keep responses conversational, educational, and encouraging
- Focus on real-world system design principles and best practices
- Remember context from previous messages in the conversation
- Ask one question at a time to avoid overwhelming the user
- Provide specific examples when explaining concepts

**Session Context:**
You have access to the conversation history through the session state. Use this to:
- Reference previous design decisions discussed
- Build upon concepts already covered
- Maintain continuity in the interview simulation
                """,
                tools=[],  # Will add tools in future phases for whiteboard analysis, etc.
            )
            logger.info(f"Agent '{self.agent.name}' created successfully")

            # Session service will be initialized per-chat for proper live sessions
            logger.info("ADK service initialized - sessions will be created per chat")

        except Exception as e:
            logger.error(f"Failed to initialize ADK service: {str(e)}", exc_info=True)
            raise

    async def _get_or_create_runner(self, user_id: str) -> InMemoryRunner:
        """Get an existing runner from pool or create a new one for better performance"""
        if self.agent is None:
            raise ValueError("ADK agent not initialized")

        async with self._pool_lock:
            # Try to reuse an existing runner for this user
            if user_id in self._runner_pool:
                logger.debug(f"Reusing existing runner for user {user_id}")
                return self._runner_pool[user_id]

            # Create new runner if pool not full
            if len(self._runner_pool) < self._max_pool_size:
                logger.debug(f"Creating new runner for user {user_id}")
                runner = InMemoryRunner(agent=self.agent)
                self._runner_pool[user_id] = runner
                return runner

            # Pool is full, create temporary runner (not pooled)
            logger.debug(f"Pool full, creating temporary runner for user {user_id}")
            return InMemoryRunner(agent=self.agent)

    async def _cleanup_runner(self, user_id: str) -> None:
        """Clean up runner resources (optional, for explicit cleanup)"""
        async with self._pool_lock:
            if user_id in self._runner_pool:
                # In a production system, you might want to add runner cleanup logic here
                logger.debug(f"Runner cleanup requested for user {user_id}")
                pass  # ADK runners should clean themselves up

    async def cleanup(self) -> None:
        """Clean up all resources for graceful shutdown"""
        async with self._pool_lock:
            logger.info("Cleaning up ADK service resources")
            # Clear the runner pool
            self._runner_pool.clear()
            # Clear sessions (WeakValueDictionary will auto-cleanup)
            self._sessions.clear()
            logger.info("ADK service cleanup completed")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message using ADK agent with proper streaming pattern.

        Args:
            request: Chat request with message, user_id, and optional session_id

        Returns:
            Chat response from the agent
        """
        session_id = request.session_id or f"{request.user_id}_session"

        try:
            if not self.agent:
                logger.error("ADK agent not properly initialized")
                return ChatResponse(
                    message="Service not available. Please try again later.",
                    success=False,
                    session_id=session_id,
                    error="Agent not initialized",
                )

            logger.info(
                f"Processing ADK chat for user {request.user_id}, session {session_id}"
            )
            logger.info(f"Message length: {len(request.message)}")

            # Get runner from pool for better performance
            runner = await self._get_or_create_runner(request.user_id)
            logger.debug("Obtained runner from pool")

            # Create session using the runner's session service
            session = await runner.session_service.create_session(
                app_name=self.app_name,
                user_id=request.user_id,
                state={},  # Initialize with empty state
                session_id=session_id,
            )
            logger.info(f"Created session {session_id}")

            # Set up run configuration for text responses
            # Note: ADK expects string values for response_modalities
            # The Pydantic warning is expected and can be safely ignored
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
                run_config = RunConfig(response_modalities=["TEXT"])

            # Create LiveRequestQueue for this session
            live_request_queue = LiveRequestQueue()

            # Start the live agent session using proper streaming pattern
            live_events = runner.run_live(
                session=session,
                live_request_queue=live_request_queue,
                run_config=run_config,
            )
            logger.debug("Started live agent session")

            # Send user message to the agent
            user_content = Content(
                role="user", parts=[Part.from_text(text=request.message)]
            )
            live_request_queue.send_content(content=user_content)
            logger.debug("Sent user message to agent")

            # Collect response from agent events
            response_text = ""

            # Process events from the agent
            async for event in live_events:
                logger.debug(f"Received event: {type(event).__name__}")

                # Check if turn is complete
                if hasattr(event, "turn_complete") and event.turn_complete:
                    logger.debug("Turn completed")
                    break

                # Extract text content from the event
                # Only process non-partial events (final complete response) to avoid duplication
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts") and event.content.parts:
                        # Check if this is a partial event (streaming) or final complete event
                        is_partial = hasattr(event, "partial") and event.partial
                        if not is_partial:  # Only use final complete response
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    response_text += part.text  # Concatenate all parts
                                    logger.debug(
                                        f"Added response text part: {len(part.text)} chars, total: {len(response_text)} chars"
                                    )
                        else:
                            logger.debug(
                                f"Skipping partial streaming event: "
                                f"{len(event.content.parts)} parts"
                            )

            # Close the live request queue
            live_request_queue.close()
            logger.debug("Closed live request queue")

            if response_text:
                logger.info(
                    f"Generated ADK response for session {session_id}: "
                    f"{len(response_text)} characters"
                )

                return ChatResponse(
                    message=response_text.strip(), success=True, session_id=session_id
                )
            else:
                logger.warning(f"Empty response from ADK for session {session_id}")
                return ChatResponse(
                    message="I apologize, but I couldn't generate a response. Please try again.",
                    success=False,
                    session_id=session_id,
                    error="Empty response from agent",
                )

        except ImportError as e:
            logger.error(f"ADK import error for session {session_id}: {str(e)}")
            return ChatResponse(
                message="ADK service is not properly configured. Please check installation.",
                success=False,
                session_id=session_id,
                error="ADK configuration error",
            )
        except ValueError as e:
            logger.error(f"ADK configuration error for session {session_id}: {str(e)}")
            return ChatResponse(
                message="Configuration error. Please check ADK settings.",
                success=False,
                session_id=session_id,
                error="Configuration error",
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in ADK chat for session {session_id}: {str(e)}",
                exc_info=True,
            )
            return ChatResponse(
                message="I'm experiencing technical difficulties. Please try again in a moment.",
                success=False,
                session_id=session_id,
                error="Internal error",
            )

    def health_check(self) -> Dict[str, Any]:
        """Check if the ADK service is properly configured and ready"""
        try:
            agent_configured = self.agent is not None

            return {
                "configured": agent_configured,
                "agent_name": getattr(self.agent, "name", None) if self.agent else None,
                "model_info": (
                    {"type": "Gemini", "model": "gemini-2.0-flash-exp"}
                    if self.agent
                    else None
                ),
                "architecture": "streaming",
                "session_management": "per-chat (InMemoryRunner + InMemorySessionService)",
                "app_name": self.app_name,
                "status": "ready" if agent_configured else "not_configured",
                "capabilities": (
                    [
                        "text_streaming",
                        "live_request_queue",
                        "bidirectional_communication",
                    ]
                    if agent_configured
                    else []
                ),
            }
        except Exception as e:
            logger.error(f"ADK health check failed: {str(e)}")
            return {"configured": False, "status": "error", "error": str(e)}

    def get_session_info(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get information about a specific session"""
        try:
            # ADK session introspection (basic implementation)
            # In the streaming architecture, sessions are created per-chat
            return {
                "user_id": user_id,
                "session_id": session_id,
                "app_name": self.app_name,
                "service_type": "InMemorySessionService",
                "architecture": "streaming",
                "note": "Sessions are created per-chat in the streaming architecture",
            }
        except Exception as e:
            logger.error(f"Failed to get ADK session info: {str(e)}")
            return {"error": str(e)}
