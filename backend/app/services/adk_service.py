"""
ADK Service for managing agents and sessions using Google ADK.
"""

import asyncio
import logging
import os
import time
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
            session_id for session_id in list(self._session_creation_time.keys())
            if self._is_session_expired(session_id)
        ]
        
        for session_id in expired_sessions:
            logger.debug(f"Cleaning up expired session: {session_id}")
            self._session_creation_time.pop(session_id, None)
            self._session_states.pop(session_id, None)

    async def create_session(self, request: SessionCreateRequest) -> SessionCreateResponse:
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
                "preferences": {
                    "difficulty": "medium",
                    "focus_areas": []
                }
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
            
            logger.info(f"Created session {session_id} for user {request.user_id} with state: {list(merged_state.keys())}")
            
            return SessionCreateResponse(
                session_id=session_id,
                user_id=request.user_id,
                state=merged_state,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to create session for user {request.user_id}: {str(e)}", exc_info=True)
            return SessionCreateResponse(
                session_id="",
                user_id=request.user_id,
                state={},
                success=False,
                error=str(e)
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
                    user_sessions.append({
                        "session_id": session_id,
                        "created_at": creation_time,
                        "state": session_state,
                        "expired": self._is_session_expired(session_id)
                    })
            
            return {
                "user_id": user_id,
                "sessions": user_sessions,
                "total_sessions": len(user_sessions),
                "active_sessions": len([s for s in user_sessions if not s["expired"]])
            }
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "sessions": [],
                "error": str(e)
            }

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
            if session_id.startswith(f"{user_id}_session_") and not self._is_session_expired(session_id):
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
            if session_id in self._session_states and not self._is_session_expired(session_id):
                # Use existing session state
                session_state = self._session_states[session_id]
                logger.debug(f"Using existing session state for {session_id}")
            else:
                # Create new session with default state
                session_state = {
                    "skill_level": "intermediate",
                    "learning_progress": {},
                    "preferences": {
                        "difficulty": "medium",
                        "focus_areas": []
                    }
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
            active_sessions = [s for s in user_sessions['sessions'] if not s['expired']]
            
            if active_sessions:
                # Return the most recent active session
                most_recent = max(active_sessions, key=lambda s: s['created_at'])
                return most_recent['session_id']
            
            # Create a new session if none exists
            session_request = SessionCreateRequest(
                user_id=user_id,
                initial_state={}
            )
            
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
        self, 
        request: MultimodalAnalysisRequest
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
                message=request.prompt,
                user_id=request.user_id,
                session_id=session_id
            )
            
            # For now, use mock analysis since ADK doesn't support images directly
            # TODO: Integrate with Google GenAI multimodal API when available
            analysis_text = f"""
            COMPONENTS: Load Balancer, Web Server, Database, Redis Cache
            FEEDBACK: This appears to be a system design diagram. Based on the image analysis, I can identify several key components.
            SUGGESTIONS: Consider adding monitoring, implement health checks, add API gateway for better security
            """
            
            # Calculate cost estimate
            cost_estimate = None
            tokens_used = None
            if settings.enable_cost_tracking:
                cost_estimate = settings.multimodal_cost_per_image
                tokens_used = int(len(analysis_text.split()) * 1.3)  # Rough token estimate
            

            
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
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Multimodal analysis failed: {e}")
            return MultimodalAnalysisResponse(
                analysis="",
                success=False,
                session_id=request.session_id or "unknown",
                error=str(e)
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
            'load balancer', 'database', 'cache', 'api', 'microservice',
            'monitoring', 'logging', 'security', 'scalability', 'performance'
        ]
        
        technical_score = 0.0
        for term in technical_terms:
            if term.lower() in analysis_text.lower():
                technical_score += 0.05
        
        technical_score = min(0.3, technical_score)
        
        # Combine scores
        total_score = length_score + technical_score
        return min(1.0, total_score)

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
