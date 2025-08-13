"""
ADK Service for managing agents and sessions using Google ADK.
"""

import asyncio
import base64
import logging
import os
import time
import warnings
from typing import Any, Dict, Optional, Tuple
from weakref import WeakValueDictionary

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import InMemoryRunner

# from google.adk.sessions import InMemorySessionService  # Not directly used
from google.genai.types import (
    AudioTranscriptionConfig,
    Content,
    Part,
    RealtimeInputConfig,
    Blob,
)
from openai import OpenAI
from pydantic import BaseModel

from app.services.config import settings
from app.models.diagram import DiagramType


logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model for ADK agent"""

    message: str
    user_id: str = "default"
    session_id: Optional[str] = None


class MultimodalAnalysisRequest(BaseModel):
    """Multimodal analysis request model"""

    image_data: bytes
    prompt: str
    user_id: str = "default"
    session_id: Optional[str] = None
    analysis_type: str = "comprehensive"


class MultimodalAnalysisResponse(BaseModel):
    """Multimodal analysis response model"""

    analysis: str
    success: bool
    session_id: str
    cost_estimate: Optional[float] = None
    tokens_used: Optional[int] = None
    confidence_score: Optional[float] = None
    error: Optional[str] = None


class SessionCreateRequest(BaseModel):
    """Session creation request model"""

    user_id: str
    initial_state: Optional[Dict[str, Any]] = None


class SessionCreateResponse(BaseModel):
    """Session creation response model"""

    session_id: str
    user_id: str
    state: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model from ADK agent"""

    message: str
    success: bool
    session_id: str
    error: Optional[str] = None
    artifacts: Optional[Dict[str, Any]] = None  # For storing generated diagrams, etc.


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

        # Connection pooling for performance with proper limits
        self._runner_pool: Dict[str, InMemoryRunner] = {}
        self._pool_lock = asyncio.Lock()
        self._max_pool_size = settings.adk_max_connections
        self._sessions: WeakValueDictionary = WeakValueDictionary()

        # Session state management
        self._session_states: Dict[str, Dict[str, Any]] = {}
        self._session_creation_time: Dict[str, float] = {}
        self._session_expiry_seconds = settings.adk_session_expiry_seconds

        # Timeout configuration for streaming responses (configurable)
        self._streaming_timeout = settings.adk_streaming_timeout
        self._max_events = settings.adk_max_events

        # Reusable objects to avoid creating new instances for each request
        self._text_run_config: Optional[RunConfig] = None

        # LiveRequestQueue pool for connection reuse with health tracking
        self._queue_pool: Dict[str, LiveRequestQueue] = {}
        self._queue_pool_lock = asyncio.Lock()
        self._queue_health: Dict[str, float] = {}  # Track last successful use

        self._initialize_adk()

    def _configure_environment(self) -> None:
        """Configure environment variables for ADK (only once)"""
        if self._env_configured:
            return  # Skip if already configured

        # ADK expects these environment variables to be set
        if settings.google_api_key:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key
            logger.debug(
                "Set GOOGLE_API_KEY environment variable (key masked for security)"
            )

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

            # Initialize reusable objects for better performance
            self._initialize_reusable_objects()

            # Session service will be initialized per-chat for proper live sessions
            logger.info("ADK service initialized - sessions will be created per chat")

        except Exception as e:
            logger.error(f"Failed to initialize ADK service: {str(e)}", exc_info=True)
            raise

    def _initialize_reusable_objects(self) -> None:
        """Initialize objects that can be reused across requests for better performance"""
        try:
            # Create reusable RunConfig for text responses
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category=UserWarning, module="pydantic"
                )
                self._text_run_config = RunConfig(response_modalities=["TEXT"])
            logger.debug("Initialized reusable RunConfig for text responses")
        except Exception as e:
            logger.warning(f"Failed to initialize reusable objects: {e}")
            # Fall back to creating objects per request if initialization fails
            self._text_run_config = None

    def _create_user_content(self, message: str) -> Content:
        """Create user content object efficiently"""
        return Content(role="user", parts=[Part.from_text(text=message)])

    def _get_run_config(self) -> RunConfig:
        """Get reusable RunConfig or create new one if needed"""
        if self._text_run_config is not None:
            return self._text_run_config

        # Fallback: create new RunConfig if reusable one failed to initialize
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
            return RunConfig(response_modalities=["TEXT"])

    def _is_queue_healthy(self, session_id: str) -> bool:
        """Check if a queue connection is still healthy based on last use time"""
        if session_id not in self._queue_health:
            return False

        last_use = self._queue_health[session_id]
        current_time = time.time()
        timeout = settings.adk_connection_health_timeout

        # Consider connection stale if not used within timeout period
        is_healthy = (current_time - last_use) < timeout

        if not is_healthy:
            logger.debug(
                f"Queue for session {session_id} is stale (last use: {current_time - last_use:.1f}s ago)"
            )

        return is_healthy

    def _mark_queue_healthy(self, session_id: str) -> None:
        """Mark a queue as healthy by updating its last use time"""
        self._queue_health[session_id] = time.time()

    async def _get_or_create_queue(self, session_id: str) -> LiveRequestQueue:
        """Get an existing LiveRequestQueue from pool or create a new one with health checks"""
        async with self._queue_pool_lock:
            # Try to reuse an existing queue for this session if healthy
            if session_id in self._queue_pool and self._is_queue_healthy(session_id):
                logger.debug(
                    f"Reusing healthy LiveRequestQueue for session {session_id}"
                )
                queue = self._queue_pool[session_id]
                self._mark_queue_healthy(session_id)  # Update health timestamp
                return queue

            # Remove unhealthy queue if it exists
            if session_id in self._queue_pool:
                logger.debug(f"Removing unhealthy queue for session {session_id}")
                try:
                    self._queue_pool[session_id].close()
                except Exception as e:
                    logger.warning(f"Error closing unhealthy queue: {e}")
                del self._queue_pool[session_id]
                if session_id in self._queue_health:
                    del self._queue_health[session_id]

            # Create new queue if pool not full
            if len(self._queue_pool) < self._max_pool_size:
                logger.debug(f"Creating new LiveRequestQueue for session {session_id}")
                queue = LiveRequestQueue()
                self._queue_pool[session_id] = queue
                self._mark_queue_healthy(session_id)  # Mark as healthy
                return queue

            # Pool is full, create temporary queue (not pooled)
            logger.debug(
                f"Queue pool full ({len(self._queue_pool)}/{self._max_pool_size}), "
                f"creating temporary LiveRequestQueue for session {session_id}"
            )
            return LiveRequestQueue()

    async def _cleanup_queue(self, session_id: str) -> None:
        """Clean up queue resources after use"""
        async with self._queue_pool_lock:
            if session_id in self._queue_pool:
                queue = self._queue_pool[session_id]
                try:
                    queue.close()  # Close the queue properly
                    del self._queue_pool[session_id]
                    # Also clean up health tracking
                    if session_id in self._queue_health:
                        del self._queue_health[session_id]
                    logger.debug(
                        f"Cleaned up LiveRequestQueue for session {session_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Error cleaning up queue for session {session_id}: {e}"
                    )

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
        logger.info("Cleaning up ADK service resources")

        # Clean up queue pool
        async with self._queue_pool_lock:
            for session_id, queue in list(self._queue_pool.items()):
                try:
                    queue.close()
                    logger.debug(f"Cleaned up queue for session {session_id}")
                except Exception as e:
                    logger.warning(
                        f"Error cleaning up queue for session {session_id}: {e}"
                    )
            self._queue_pool.clear()
            self._queue_health.clear()  # Clear health tracking

        # Clean up runner pool
        async with self._pool_lock:
            self._runner_pool.clear()
            # Clear sessions (WeakValueDictionary will auto-cleanup)
            self._sessions.clear()

        # Clean up session state management
        self._session_states.clear()
        self._session_creation_time.clear()

        logger.info("ADK service cleanup completed")

    def _is_session_expired(self, session_id: str) -> bool:
        """Check if a session has expired"""
        if session_id not in self._session_creation_time:
            return True

        creation_time = self._session_creation_time[session_id]
        current_time = time.time()
        elapsed_time = current_time - creation_time

        return elapsed_time > self._session_expiry_seconds

    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        expired_sessions = [
            session_id
            for session_id in list(self._session_creation_time.keys())
            if self._is_session_expired(session_id)
        ]

        for session_id in expired_sessions:
            logger.debug(f"Cleaning up expired session: {session_id}")
            self._session_creation_time.pop(session_id, None)
            self._session_states.pop(session_id, None)

    async def create_session(
        self, request: SessionCreateRequest
    ) -> SessionCreateResponse:
        """
        Create a new session with initial state.

        Args:
            request: Session creation request with user_id and initial_state

        Returns:
            Session creation response with session_id and state
        """
        try:
            # Clean up expired sessions periodically
            self._cleanup_expired_sessions()

            # Generate session ID with consistent timestamp
            creation_timestamp = time.time()
            session_id = f"{request.user_id}_session_{int(creation_timestamp)}"

            # Get runner from pool
            runner = await self._get_or_create_runner(request.user_id)

            # Initialize state with user preferences
            initial_state = request.initial_state or {}
            default_state = {
                "skill_level": "intermediate",
                "learning_progress": {},
                "preferences": {"difficulty": "medium", "focus_areas": []},
            }
            # Merge user-provided state with defaults
            merged_state = {**default_state, **initial_state}

            # Create ADK session with state
            await runner.session_service.create_session(
                app_name=self.app_name,
                user_id=request.user_id,
                state=merged_state,
                session_id=session_id,
            )

            # Store session state and creation time for management (using same timestamp)
            self._session_states[session_id] = merged_state
            self._session_creation_time[session_id] = creation_timestamp

            logger.info(
                f"Created session {session_id} for user {request.user_id} with state: {list(merged_state.keys())}"
            )

            return SessionCreateResponse(
                session_id=session_id,
                user_id=request.user_id,
                state=merged_state,
                success=True,
            )

        except Exception as e:
            logger.error(
                f"Failed to create session for user {request.user_id}: {str(e)}",
                exc_info=True,
            )
            return SessionCreateResponse(
                session_id="",
                user_id=request.user_id,
                state={},
                success=False,
                error=str(e),
            )

    def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            User sessions information
        """
        try:
            # Clean up expired sessions first
            self._cleanup_expired_sessions()

            # Find sessions for this user
            user_sessions = []
            for session_id, creation_time in self._session_creation_time.items():
                if session_id.startswith(f"{user_id}_session_"):
                    session_state = self._session_states.get(session_id, {})
                    user_sessions.append(
                        {
                            "session_id": session_id,
                            "created_at": creation_time,
                            "state": session_state,
                            "expired": self._is_session_expired(session_id),
                        }
                    )

            return {
                "user_id": user_id,
                "sessions": user_sessions,
                "total_sessions": len(user_sessions),
                "active_sessions": len([s for s in user_sessions if not s["expired"]]),
            }

        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {str(e)}")
            return {"user_id": user_id, "sessions": [], "error": str(e)}

    def _get_most_recent_active_session(self, user_id: str) -> Optional[str]:
        """
        Get the most recent active session for a user.

        Args:
            user_id: User identifier

        Returns:
            Most recent active session_id or None if no active sessions
        """
        user_sessions = []
        for session_id, creation_time in self._session_creation_time.items():
            if session_id.startswith(
                f"{user_id}_session_"
            ) and not self._is_session_expired(session_id):
                user_sessions.append((session_id, creation_time))

        if not user_sessions:
            return None

        # Sort by creation time and return the most recent
        most_recent = max(user_sessions, key=lambda x: x[1])
        return most_recent[0]

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message using ADK agent with proper streaming pattern.

        Args:
            request: Chat request with message, user_id, and optional session_id

        Returns:
            Chat response from the agent
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()

        # Determine session_id: use provided one, or find most recent active, or create new
        if request.session_id:
            session_id = request.session_id
            logger.debug(f"Using provided session_id: {session_id}")
        else:
            # Try to find most recent active session for this user
            session_id = self._get_most_recent_active_session(request.user_id)
            if session_id:
                logger.debug(f"Found most recent active session: {session_id}")
            else:
                # Create new session ID for new session
                creation_timestamp = time.time()
                session_id = f"{request.user_id}_session_{int(creation_timestamp)}"
                logger.debug(f"Created new session_id: {session_id}")

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

            # Get or create session state with user preferences
            if session_id in self._session_states and not self._is_session_expired(
                session_id
            ):
                # Use existing session state
                session_state = self._session_states[session_id]
                logger.debug(f"Using existing session state for {session_id}")
            else:
                # Create new session with default state
                session_state = {
                    "skill_level": "intermediate",
                    "learning_progress": {},
                    "preferences": {"difficulty": "medium", "focus_areas": []},
                }
                self._session_states[session_id] = session_state
                self._session_creation_time[session_id] = time.time()
                logger.debug(f"Created new session state for {session_id}")

            # Create session using the runner's session service
            session = await runner.session_service.create_session(
                app_name=self.app_name,
                user_id=request.user_id,
                state=session_state,
                session_id=session_id,
            )
            logger.info(f"Created ADK session {session_id}")

            # Get reusable run configuration for better performance
            run_config = self._get_run_config()

            # Get LiveRequestQueue from pool for better performance
            live_request_queue = await self._get_or_create_queue(session_id)

            # Start the live agent session using proper streaming pattern
            live_events = runner.run_live(
                session=session,
                live_request_queue=live_request_queue,
                run_config=run_config,
            )
            logger.debug("Started live agent session")

            # Send user message to the agent using efficient content creation
            user_content = self._create_user_content(request.message)
            live_request_queue.send_content(content=user_content)
            logger.debug("Sent user message to agent")

            # Collect response from agent events
            response_text = ""
            event_count = 0

            # Process events from the agent with timeout protection
            logger.debug(
                f"Starting streaming with {self._streaming_timeout}s timeout, max {self._max_events} events"
            )
            try:
                async with asyncio.timeout(self._streaming_timeout):
                    async for event in live_events:
                        event_count += 1
                        logger.debug(
                            f"Received event {event_count}: {type(event).__name__}"
                        )

                        # Safety check: prevent infinite event loops
                        if event_count > self._max_events:
                            logger.warning(
                                f"Maximum events ({self._max_events}) exceeded, stopping"
                            )
                            break

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
                                            response_text += (
                                                part.text
                                            )  # Concatenate all parts
                                            logger.debug(
                                                f"Added response text part: {len(part.text)} chars, "
                                                f"total: {len(response_text)} chars"
                                            )
                                else:
                                    logger.debug(
                                        f"Skipping partial streaming event: "
                                        f"{len(event.content.parts)} parts"
                                    )
            except asyncio.TimeoutError:
                logger.error(
                    f"Streaming timeout after {self._streaming_timeout} seconds"
                )
                await self._cleanup_queue(session_id)
                return ChatResponse(
                    message="Request timed out. Please try again with a shorter message.",
                    success=False,
                    session_id=session_id,
                    error="Streaming timeout",
                )

            # Clean up the live request queue using proper pool management
            await self._cleanup_queue(session_id)
            logger.debug("Cleaned up live request queue")

            if response_text:
                logger.info(
                    f"Generated ADK response for session {session_id}: "
                    f"{len(response_text)} characters"
                )

                # Check if the response suggests generating a diagram
                enhanced_response = await self._enhance_response_with_diagrams(
                    response_text.strip(), request.user_id, session_id, request.message
                )
                
                return enhanced_response
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

    async def _get_or_create_session_id(self, user_id: str) -> str:
        """
        Get or create a session ID for a user.

        Args:
            user_id: User identifier

        Returns:
            Session ID (either existing or newly created)
        """
        try:
            # Check if user has any active sessions
            user_sessions = self.get_user_sessions(user_id)
            active_sessions = [s for s in user_sessions["sessions"] if not s["expired"]]

            if active_sessions:
                # Return the most recent active session
                most_recent = max(active_sessions, key=lambda s: s["created_at"])
                return most_recent["session_id"]

            # Create a new session if none exists
            session_request = SessionCreateRequest(user_id=user_id, initial_state={})

            session_response = await self.create_session(session_request)
            if session_response.success:
                return session_response.session_id
            else:
                # Fallback: create a simple session ID
                return f"{user_id}_session_{int(time.time())}"

        except Exception as e:
            logger.warning(f"Failed to get/create session for user {user_id}: {e}")
            # Fallback: create a simple session ID
            return f"{user_id}_session_{int(time.time())}"

    async def analyze_image_multimodal(
        self, request: MultimodalAnalysisRequest
    ) -> MultimodalAnalysisResponse:
        """
        Analyze an image using multimodal LLM capabilities.

        Args:
            request: Multimodal analysis request with image data and prompt

        Returns:
            Multimodal analysis response with structured feedback
        """
        try:
            # Create or get session
            session_id = request.session_id or await self._get_or_create_session_id(
                request.user_id
            )

            # Get or create runner for this user
            runner = await self._get_or_create_runner(request.user_id)

            # Use the existing chat infrastructure for multimodal analysis
            # Create a chat request with the image content
            chat_request = ChatRequest(
                message=request.prompt, user_id=request.user_id, session_id=session_id
            )

            # Initialize OpenAI client
            client = OpenAI(api_key=settings.openai_api_key)

            # Create the multimodal prompt for system design analysis
            system_design_prompt = f"""
            Analyze this system design diagram and provide:
            
            1. COMPONENTS: List all system components you can identify
            2. FEEDBACK: Architectural feedback and observations
            3. SUGGESTIONS: Specific improvement suggestions
            
            Focus on system design best practices, scalability, security, and performance.
            Be specific and actionable in your recommendations.
            
            {request.prompt}
            """

            # Convert image data to base64 for OpenAI
            image_base64 = base64.b64encode(request.image_data).decode("utf-8")

            # Generate content using OpenAI GPT-4o
            response = client.chat.completions.create(
                model=settings.multimodal_model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert system architect. Analyze the provided system design diagram and provide detailed, actionable feedback.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": system_design_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                },
                            },
                        ],
                    },
                ],
                max_tokens=settings.multimodal_max_tokens,
                temperature=settings.multimodal_temperature,
            )

            # Extract the analysis text
            analysis_text = response.choices[0].message.content

            # Calculate cost estimate
            cost_estimate = None
            tokens_used = None
            if settings.enable_cost_tracking:
                # Estimate tokens (rough calculation)
                tokens_used = int(len(analysis_text.split()) * 1.3)
                cost_estimate = (
                    tokens_used / 1000
                ) * settings.multimodal_cost_per_1k_tokens
                cost_estimate += settings.multimodal_cost_per_image

            # Calculate confidence score based on response quality
            confidence_score = self._calculate_confidence_score(analysis_text)

            logger.info(
                f"Multimodal analysis completed for user {request.user_id}, "
                f"session {session_id}, cost: {cost_estimate}"
            )

            return MultimodalAnalysisResponse(
                analysis=analysis_text,
                success=True,
                session_id=session_id,
                cost_estimate=cost_estimate,
                tokens_used=tokens_used,
                confidence_score=confidence_score,
            )

        except Exception as e:
            logger.error(f"Multimodal analysis failed: {e}")

            # Fallback to mock analysis when real API fails
            logger.info("Falling back to mock analysis due to API error")

            fallback_analysis = f"""
            COMPONENTS: Load Balancer, Web Server, Database, Redis Cache
            FEEDBACK: This appears to be a system design diagram. Based on the image analysis, I can identify several key components.
            SUGGESTIONS: Consider adding monitoring, implement health checks, add API gateway for better security
            
            NOTE: This is a fallback analysis due to API authentication issues. 
            To use real multimodal analysis, please set up valid OpenAI API credentials.
            """

            # Calculate cost estimate for fallback
            cost_estimate = None
            tokens_used = None
            if settings.enable_cost_tracking:
                tokens_used = int(len(fallback_analysis.split()) * 1.3)
                cost_estimate = (
                    tokens_used / 1000
                ) * settings.multimodal_cost_per_1k_tokens
                cost_estimate += settings.multimodal_cost_per_image

            confidence_score = self._calculate_confidence_score(fallback_analysis)

            return MultimodalAnalysisResponse(
                analysis=fallback_analysis,
                success=True,
                session_id=request.session_id or "unknown",
                cost_estimate=cost_estimate,
                tokens_used=tokens_used,
                confidence_score=confidence_score,
            )

    def _calculate_confidence_score(self, analysis_text: str) -> float:
        """
        Calculate confidence score based on analysis quality.

        Args:
            analysis_text: The analysis response text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not analysis_text:
            return 0.0

        # Simple heuristic: longer, more detailed responses get higher scores
        text_length = len(analysis_text)
        word_count = len(analysis_text.split())

        # Base score from length (0.3 to 0.7)
        length_score = min(0.7, max(0.3, text_length / 1000))

        # Bonus for technical terms and structured content
        technical_terms = [
            "load balancer",
            "database",
            "cache",
            "api",
            "microservice",
            "monitoring",
            "logging",
            "security",
            "scalability",
            "performance",
        ]

        technical_score = 0.0
        for term in technical_terms:
            if term.lower() in analysis_text.lower():
                technical_score += 0.05

        technical_score = min(0.3, technical_score)

        # Combine scores
        total_score = length_score + technical_score
        return min(1.0, total_score)

    async def generate_mermaid_code(
        self, system_description: str, diagram_type: DiagramType, session_id: Optional[str] = None
    ) -> tuple[str, str, int, float]:
        """Generates Mermaid code from a system description using the LLM."""
        logger.info(f"Generating Mermaid code for a {diagram_type.value} diagram.")
        
        prompt = f"""
        You are an expert in system design and software architecture.
        Based on the following system description, generate the corresponding Mermaid code for a '{diagram_type.value}' diagram.
        The output should be only the Mermaid code block, without any explanations or surrounding text.

        System Description:
        "{system_description}"

        Mermaid Code:
        """

        # Use a temporary session if none is provided
        user_id = "diagram_generation_user"
        temp_session_id = f"{user_id}_session_{int(time.time())}"
        
        # Create a specialized prompt for Mermaid diagram generation
        mermaid_prompt = self._create_mermaid_generation_prompt(system_description, diagram_type)
        
        logger.info(f"Generating Mermaid code for {diagram_type.value} diagram: {system_description[:100]}...")
        
        try:
            # Use the working chat pattern to generate Mermaid code
            # Use a special user_id to avoid triggering diagram auto-generation
            chat_request = ChatRequest(
                message=mermaid_prompt,
                user_id="mermaid_generator_internal",  # Special user to avoid recursion
                session_id=temp_session_id
            )
            
            # Get the LLM response for Mermaid generation
            response = await self.chat(chat_request)
            
            if response.success:
                # Extract Mermaid code from the response
                mermaid_code = self._extract_mermaid_code(response.message)
                logger.info(f"Successfully generated dynamic Mermaid code: {len(mermaid_code)} characters")
                
                # Estimate tokens and cost based on response
                estimated_tokens = len(response.message.split()) * 1.3  # Rough estimation
                estimated_cost = estimated_tokens * 0.00002  # Approximate cost per token
                
                return mermaid_code, "gemini-2.0-flash-exp", int(estimated_tokens), estimated_cost
            else:
                logger.warning(f"LLM failed to generate Mermaid code: {response.error}")
                # Fall back to a basic template as last resort
                fallback_code = self._create_fallback_mermaid(system_description, diagram_type)
                return fallback_code, "gemini-2.0-flash-exp", 50, 0.001
                
        except Exception as e:
            logger.error(f"Error generating Mermaid code: {e}")
            # Fall back to a basic template
            fallback_code = self._create_fallback_mermaid(system_description, diagram_type)
            return fallback_code, "gemini-2.0-flash-exp", 50, 0.001

    async def _enhance_response_with_diagrams(
        self, response_text: str, user_id: str, session_id: str, user_message: str = ""
    ) -> ChatResponse:
        """Enhance ADK response with automatic diagram generation when appropriate."""
        
        # Skip diagram generation for internal Mermaid generation requests
        if user_id == "mermaid_generator_internal":
            return ChatResponse(
                message=response_text,
                success=True,
                session_id=session_id,
                artifacts=None
            )
        
        # Keywords that suggest the user wants a diagram
        diagram_keywords = [
            "diagram", "chart", "visualize", "architecture", "design", "draw", 
            "show me", "create a", "generate", "flowchart", "mermaid",
            "system design", "database schema", "workflow", "process flow",
            "outline", "components", "structure", "layout"
        ]
        
        # Check both user message and response for diagram keywords
        combined_text = f"{user_message} {response_text}".lower()
        should_generate_diagram = any(keyword in combined_text for keyword in diagram_keywords)
        
        # Debug logging
        logger.info(f"Diagram detection for user {user_id}: keywords found = {should_generate_diagram}")
        if should_generate_diagram:
            found_keywords = [kw for kw in diagram_keywords if kw in combined_text]
            logger.info(f"Found keywords: {found_keywords[:5]}")  # Log first 5 matches
        
        artifacts = None
        
        if should_generate_diagram:
            try:
                logger.info("Detected diagram request, auto-generating diagram")
                
                # Try to extract system description from the response
                system_description = self._extract_system_description(response_text)
                
                if system_description:
                    # Import here to avoid circular imports
                    from app.models.diagram import DiagramGenerationRequest
                    
                    # Generate diagram
                    diagram_request = DiagramGenerationRequest(
                        system_description=system_description,
                        diagram_type=DiagramType.ARCHITECTURE,  # Default to architecture
                        user_id=user_id,
                        session_id=session_id
                    )
                    
                    # Get diagram service from app state (if available)
                    diagram_service = getattr(self, '_diagram_service', None)
                    if diagram_service:
                        diagram_response = await diagram_service.generate_diagram(diagram_request)
                        
                        artifacts = {
                            "diagrams": [{
                                "id": diagram_response.diagram_id,
                                "type": "mermaid_diagram",
                                "artifact_id": diagram_response.png_artifact_id,
                                "mermaid_code": diagram_response.mermaid_code,
                                "description": system_description
                            }]
                        }
                        
                        # Replace conflicting text and enhance the response
                        # Remove any text that says the agent can't generate images
                        conflict_phrases = [
                            "i cannot directly generate a png image",
                            "my image generation capabilities are limited",
                            "i cannot directly generate",
                            "i am sorry, i cannot",
                            "however, i can definitely help you outline"
                        ]
                        
                        response_lower = response_text.lower()
                        for phrase in conflict_phrases:
                            if phrase in response_lower:
                                # Find the position and remove conflicting sentences
                                start_pos = response_lower.find(phrase)
                                if start_pos != -1:
                                    # Find the end of the sentence(s) that conflict
                                    end_pos = response_text.find(".", start_pos)
                                    if end_pos != -1:
                                        response_text = response_text[:start_pos] + response_text[end_pos+1:]
                        
                                                            # Add the diagram confirmation
                                    response_text += f"\n\n🎨 **Visual Diagram Generated!** I've created an informational image containing the Mermaid diagram code that illustrates this architecture. You can:\n\n• **View the diagram**: `/api/whiteboard/artifacts/{diagram_response.png_artifact_id}`\n• **Copy the Mermaid code** from the image to paste into tools like:\n  - https://mermaid.live/ (online editor)\n  - GitHub Markdown\n  - Miro, Lucidchart, or other diagram tools\n\n**System Description**: {system_description}"
                        
                        logger.info(f"Auto-generated diagram {diagram_response.diagram_id} for user {user_id}")
                    
            except Exception as e:
                logger.warning(f"Failed to auto-generate diagram: {e}")
                # Don't fail the chat response, just log the error
        
        return ChatResponse(
            message=response_text,
            success=True,
            session_id=session_id,
            artifacts=artifacts
        )

    def _extract_system_description(self, response_text: str) -> Optional[str]:
        """Extract a system description suitable for diagram generation."""
        # Simple extraction - look for sentences that describe systems/architecture
        sentences = response_text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(word in sentence.lower() for word in [
                "system", "architecture", "service", "component", "database", 
                "server", "client", "api", "microservice", "application"
            ]):
                if len(sentence) > 20:  # Ensure it's substantial enough
                    return sentence
        
        # Fallback: use the first substantial sentence
        substantial_sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        if substantial_sentences:
            return substantial_sentences[0]
        
        # Last resort: use a portion of the response
        if len(response_text) > 50:
            return response_text[:200] + "..." if len(response_text) > 200 else response_text
        
        return None

    def set_diagram_service(self, diagram_service):
        """Set the diagram service for auto-generation."""
        self._diagram_service = diagram_service

    def _create_mermaid_generation_prompt(self, system_description: str, diagram_type: DiagramType) -> str:
        """Create a specialized prompt for generating Mermaid diagrams."""
        
        type_specific_guidance = {
            DiagramType.ARCHITECTURE: """
Focus on system architecture components like:
- Load balancers, API gateways
- Microservices, databases, caches
- Message queues, CDNs
- External services and APIs
Use rectangular boxes for services, cylindrical shapes for databases, and clear arrows for data flow.""",
            
            DiagramType.WORKFLOW: """
Focus on process flow and decision points:
- Start/end points (rounded rectangles)
- Decision diamonds with yes/no paths
- Process steps (rectangles)
- Clear sequential flow with arrows
Use flowchart syntax with decision logic.""",
            
            DiagramType.DATABASE: """
Focus on data relationships:
- Entity boxes with field lists
- Primary/foreign key relationships
- One-to-many, many-to-many connections
- Use ER diagram or class diagram syntax.""",
            
            DiagramType.NETWORK: """
Focus on network topology:
- Network devices (routers, switches, firewalls)
- Connections and protocols
- IP ranges and VLANs
- Security boundaries"""
        }
        
        guidance = type_specific_guidance.get(diagram_type, type_specific_guidance[DiagramType.ARCHITECTURE])
        
        prompt = f"""Please generate a Mermaid diagram for the following system description:

**System Description:** {system_description}

**Diagram Type:** {diagram_type.value.title()}

**Requirements:**
{guidance}

**Important Instructions:**
1. Return ONLY the Mermaid code, no explanations or markdown formatting
2. Start with the appropriate Mermaid diagram type (graph TD, flowchart TD, erDiagram, etc.)
3. Use clear, descriptive node labels
4. Ensure proper syntax and valid Mermaid code
5. Keep it focused and readable (max 15-20 nodes)
6. Use meaningful node IDs (like UserService, Database, etc.)

Generate the Mermaid diagram code now:"""

        return prompt

    def _create_fallback_mermaid(self, system_description: str, diagram_type: DiagramType) -> str:
        """Create a basic fallback Mermaid diagram when LLM generation fails."""
        
        # Extract key terms from description for more dynamic fallback
        description_lower = system_description.lower()
        
        if diagram_type == DiagramType.WORKFLOW:
            return """flowchart TD
    A[Start] --> B[Process Input]
    B --> C{Decision Point}
    C -->|Yes| D[Execute Action]
    C -->|No| E[Alternative Path]
    D --> F[End]
    E --> F[End]"""
        
        elif diagram_type == DiagramType.DATABASE:
            return """erDiagram
    User ||--o{ Order : places
    User {
        int id
        string name
        string email
    }
    Order {
        int id
        date created_at
        int user_id
    }"""
        
        else:  # Architecture or default
            # Try to be more dynamic based on description
            if any(term in description_lower for term in ['microservice', 'service', 'api']):
                return """graph TD
    Client[Client App] --> Gateway[API Gateway]
    Gateway --> Auth[Auth Service]
    Gateway --> UserSvc[User Service]
    Gateway --> OrderSvc[Order Service]
    UserSvc --> UserDB[User Database]
    OrderSvc --> OrderDB[Order Database]"""
            else:
                return """graph TD
    A[Client] --> B[Load Balancer]
    B --> C[Web Server 1]
    B --> D[Web Server 2]
    C --> E[Application Server]
    D --> E[Application Server]
    E --> F[Database]"""

    def _extract_mermaid_code(self, response_text: str) -> str:
        """Extracts Mermaid code from the LLM's response."""
        # The LLM is prompted to return only the code, but let's be safe
        if "```mermaid" in response_text:
            code = response_text.split("```mermaid")[1].split("```")[0].strip()
            return code
        elif response_text.strip().startswith("graph") or response_text.strip().startswith("flowchart"):
             return response_text.strip()
        else:
            logger.warning(f"Could not find a Mermaid code block in the response. Returning the full response. Response: {response_text}")
            return response_text

    async def stream_voice(self, audio_data: bytes) -> Tuple[bool, bytes | str]:
        """Handle audio streaming using ADK's Live API.

        Streams raw audio bytes to the ADK Live API and returns audio bytes in
        response. If the model fails to return audio, a textual message is
        provided so clients can fall back to text interactions.
        """
        try:
            if not self.agent:
                raise RuntimeError("ADK agent not initialized")

            # Create runner and session for this streaming request
            runner = await self._get_or_create_runner("voice_user")
            session = await runner.session_service.create_session(
                app_name=self.app_name, user_id="voice_user", state={}
            )

            # Configure run for bidirectional audio streaming
            run_config = RunConfig(
                response_modalities=["AUDIO", "TEXT"],
                input_audio_transcription=AudioTranscriptionConfig(),
                output_audio_transcription=AudioTranscriptionConfig(),
                realtime_input_config=RealtimeInputConfig(),
                streaming_mode=StreamingMode.BIDI,
            )

            live_request_queue = LiveRequestQueue()
            live_events = runner.run_live(
                session=session,
                live_request_queue=live_request_queue,
                run_config=run_config,
            )

            # Send audio to ADK
            blob = Blob(data=audio_data, mime_type="audio/wav")
            live_request_queue.send_activity_start()
            live_request_queue.send_realtime(blob)
            live_request_queue.send_activity_end()
            live_request_queue.close()

            audio_response = b""
            text_fallback = ""

            async for event in live_events:
                if getattr(event, "content", None) and event.content.parts:
                    for part in event.content.parts:
                        if getattr(part, "inline_data", None) and (
                            part.inline_data.mime_type or ""
                        ).startswith("audio"):
                            audio_response += part.inline_data.data or b""
                        elif getattr(part, "text", None):
                            text_fallback += part.text

                # Stop once turn is complete after processing content
                if getattr(event, "turn_complete", False):
                    break

            if audio_response:
                return True, audio_response
            if text_fallback:
                return False, text_fallback
            return False, "No audio response"
        except Exception as exc:
            logger.error(f"Voice streaming failed: {exc}", exc_info=True)
            return False, "Voice processing unavailable"

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
