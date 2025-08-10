# AI System Design Learning Platform

### Document Information
- **Version**: 1.0
- **Date**: June 2025
- **Purpose**: Detailed development phases, testing, and deployment strategies
- **Companion Document**: ADK Feature Mapping

---

## 1. Development Phases Implementation

### 1.1 Phase 1: Foundation (Weeks 1-4)
**ADK Setup & Core Agent**
```python
# Minimal viable agent setup
basic_agent = LlmAgent(
    name="system_design_tutor_v1",
    model="gemini-2.0-flash",
    instruction="Teach system design concepts interactively",
    tools=[basic_whiteboard_tool]  # PNG analysis only
)

# In-memory services for development
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

# Basic runner
runner = Runner(
    agent=basic_agent,
    app_name="systemdesign_ai_dev",
    session_service=session_service,
    artifact_service=artifact_service
)
```

### 1.2 Phase 2: Whiteboard & Assessment (Weeks 5-8)
**Enhanced Tools & Callbacks**
```python
# Add comprehensive tools
enhanced_agent = LlmAgent(
    name="system_design_tutor_v2",
    model="gemini-2.0-flash",
    instruction="Teach system design with real-time feedback",
    tools=[
        whiteboard_analysis_tool,
        diagram_generator_tool,
        assessment_tool
    ]
)

# Add monitoring callbacks
callbacks = [
    LearningSessionCallbacks(),
    ModelCallbacks(),
    OpikMonitoringCallbacks()
]
```

### 1.3 Phase 3: Voice & Polish (Weeks 9-12)
**Live API Integration**
```python
# Voice-enabled agent
voice_agent = LlmAgent(
    name="system_design_tutor_voice",
    model="gemini-2.0-flash",  # Live API compatible
    instruction="Provide system design tutoring via voice and text",
    tools=[all_tools],
    enable_live_streaming=True
)

# Production services
session_service = VertexAiSessionService(...)
artifact_service = GcsArtifactService(...)
memory_service = VertexAiRagMemoryService(...)
```

### 1.4 Phase 4: Production Ready (Weeks 13-16)
**Deployment & Scaling**
```python
# Production deployment configuration
production_config = {
    "agent_engine": VertexAiAgentEngine(...),
    "auto_scaling": True,
    "monitoring": True,
    "security": True
}
```

---

## 2. Cost Optimization Strategies

### 2.1 Token Management
```python
class CostOptimization:
    """Strategies for managing API costs"""
    
    def optimize_chapter_loading(self, chapter_id: str, context: CallbackContext):
        """Smart chapter content loading"""
        # Check if already loaded
        if context.state.get(f"app:chapter_{chapter_id}_loaded"):
            return  # Skip reloading
        
        # Load incrementally based on conversation
        current_topic = self.extract_current_topic(context)
        relevant_sections = self.get_relevant_sections(chapter_id, current_topic)
        
        # Store in session state to avoid reloading
        context.state[f"app:chapter_{chapter_id}_content"] = relevant_sections
```

### 2.2 Usage Tracking
```python
class UsageTracking:
    """Track and limit expensive operations"""
    
    def track_api_usage(self, context: CallbackContext):
        """Monitor per-user API costs"""
        user_usage = context.state.get("user:monthly_api_usage", 0)
        estimated_cost = self.estimate_current_call_cost(context)
        
        context.state["user:monthly_api_usage"] = user_usage + estimated_cost
        
        # Rate limiting for free tier users
        if not self.is_premium_user(context) and user_usage > FREE_TIER_LIMIT:
            raise RateLimitException("Monthly usage limit exceeded")
```

### 2.3 Response Caching Strategy
```python
class ResponseCaching:
    """Intelligent caching for expensive operations"""
    
    def __init__(self):
        self.cache_service = RedisCacheService()
        self.cache_ttl = {
            "whiteboard_analysis": 3600,  # 1 hour
            "diagram_generation": 1800,   # 30 minutes
            "assessment": 900,            # 15 minutes
            "chapter_content": 86400      # 24 hours
        }
    
    async def get_cached_response(self, operation_type: str, inputs: dict) -> Optional[dict]:
        """Check cache for existing response"""
        cache_key = self.generate_cache_key(operation_type, inputs)
        cached_result = await self.cache_service.get(cache_key)
        
        if cached_result:
            self.track_cache_hit(operation_type)
            return cached_result
        
        return None
    
    def generate_cache_key(self, operation_type: str, inputs: dict) -> str:
        """Generate unique cache key for operation"""
        input_hash = hashlib.md5(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
        return f"{operation_type}:{input_hash}"
```

### 2.4 Batch Processing Optimization
```python
class BatchOptimization:
    """Optimize batch operations for cost efficiency"""
    
    async def batch_diagram_generation(self, diagram_requests: List[dict], context: CallbackContext):
        """Generate multiple diagrams in single LLM call"""
        
        # Combine requests into single prompt
        batch_prompt = self.create_batch_diagram_prompt(diagram_requests)
        
        # Single LLM call for multiple diagrams
        batch_response = await call_llm(batch_prompt, model="gemini-2.0-flash")
        
        # Parse individual diagrams from batch response
        individual_diagrams = self.parse_batch_response(batch_response, len(diagram_requests))
        
        # Save each diagram as artifact
        results = []
        for i, diagram_code in enumerate(individual_diagrams):
            rendered_png = await mermaid_mcp_render(diagram_code)
            filename = await self.save_diagram_artifact(diagram_code, rendered_png, context)
            results.append({"diagram_file": filename, "mermaid_code": diagram_code})
        
        return results
```

---

## 3. Testing Strategy with ADK

### 3.1 Unit Testing for Tools
```python
import pytest
from unittest.mock import Mock
from google.adk.tools import ToolContext

class TestSystemDesignTools:
    """Unit tests for our custom tools"""
    
    @pytest.fixture
    def mock_tool_context(self):
        """Mock ToolContext for testing"""
        context = Mock(spec=ToolContext)
        context.state = {
            "user:current_chapter": "design_twitter",
            "user:skill_level": "intermediate"
        }
        context.load_artifact = Mock()
        context.save_artifact = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_whiteboard_analysis_tool(self, mock_tool_context):
        """Test whiteboard analysis accuracy"""
        # Setup
        mock_png_data = b"fake_png_data"
        mock_tool_context.load_artifact.return_value = types.Part.from_bytes(
            mock_png_data, mime_type="image/png"
        )
        
        # Execute
        result = await analyze_whiteboard_design(
            png_filename="test_whiteboard.png",
            analysis_type="comprehensive", 
            tool_context=mock_tool_context
        )
        
        # Assert
        assert "components_identified" in result
        assert "architectural_feedback" in result
        assert result["status"] == "success"
        mock_tool_context.load_artifact.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assessment_tool_consistency(self, mock_tool_context):
        """Test assessment tool produces consistent results"""
        test_input = {
            "interaction_context": "User explained microservices architecture",
            "whiteboard_feedback": {"components": ["api_gateway", "services", "database"]}
        }
        
        # Run assessment multiple times
        results = []
        for _ in range(5):
            result = await assess_user_performance(
                interaction_context=test_input["interaction_context"],
                whiteboard_feedback=test_input["whiteboard_feedback"],
                tool_context=mock_tool_context
            )
            results.append(result)
        
        # Check consistency (scores should be within reasonable range)
        scores = [r["overall_score"] for r in results]
        score_variance = np.var(scores)
        assert score_variance < 0.5, "Assessment scores too inconsistent"
```

### 3.2 Integration Testing
```python
class TestLearningSessionFlow:
    """Integration tests for complete learning sessions"""
    
    @pytest.fixture
    def test_agent(self):
        """Create test agent with mock services"""
        return LlmAgent(
            name="test_tutor",
            model="gemini-2.0-flash",
            instruction="Test system design tutor",
            tools=[whiteboard_analysis_tool, assessment_tool]
        )
    
    @pytest.fixture
    def test_runner(self, test_agent):
        """Create test runner with in-memory services"""
        return Runner(
            agent=test_agent,
            app_name="test_app",
            session_service=InMemorySessionService(),
            artifact_service=InMemoryArtifactService()
        )
    
    @pytest.mark.asyncio
    async def test_complete_learning_session(self, test_runner):
        """Test end-to-end learning session"""
        user_id = "test_user"
        
        # Step 1: Start session
        response1 = await test_runner.run_async(
            user_id=user_id,
            user_content=Content(parts=[Part.from_text("I want to learn about designing Twitter")])
        )
        
        assert "Twitter" in response1.parts[0].text
        
        # Step 2: Submit whiteboard for analysis
        session = await test_runner.session_service.get_session("test_app", user_id)
        session.state["app:active_whiteboard"] = "test_twitter_design.png"
        
        response2 = await test_runner.run_async(
            user_id=user_id,
            user_content=Content(parts=[Part.from_text("Please analyze my whiteboard design")])
        )
        
        assert "feedback" in response2.parts[0].text.lower()
        
        # Step 3: Assessment
        response3 = await test_runner.run_async(
            user_id=user_id,
            user_content=Content(parts=[Part.from_text("I'm ready for assessment")])
        )
        
        # Verify assessment was triggered
        final_session = await test_runner.session_service.get_session("test_app", user_id)
        assert "assessment_history" in final_session.state.get("user", {})
```

### 3.3 Agent Trajectory Testing
```python
from google.adk.evaluation import TrajectoryEvaluator

class SystemDesignTrajectoryTests:
    """Test agent behavior across multi-turn conversations"""
    
    def __init__(self):
        self.evaluator = TrajectoryEvaluator()
    
    async def test_twitter_design_trajectory(self):
        """Test complete Twitter design learning trajectory"""
        
        trajectory = [
            {
                "turn": 1,
                "user_input": "I want to learn how to design Twitter",
                "expected_topics": ["requirements", "components", "architecture"],
                "expected_actions": ["load_chapter_content"]
            },
            {
                "turn": 2, 
                "user_input": "What are the main functional requirements?",
                "expected_topics": ["tweets", "timeline", "followers"],
                "expected_actions": ["provide_requirements_explanation"]
            },
            {
                "turn": 3,
                "user_action": "submit_whiteboard",
                "whiteboard_content": "basic_twitter_architecture.png",
                "expected_actions": ["analyze_whiteboard", "provide_feedback"],
                "expected_feedback_topics": ["database_design", "caching", "load_balancing"]
            },
            {
                "turn": 4,
                "user_input": "How should I handle the database for billions of tweets?",
                "expected_topics": ["sharding", "nosql", "consistency"],
                "expected_actions": ["generate_diagram"]
            },
            {
                "turn": 5,
                "user_input": "I think I'm ready for assessment",
                "expected_actions": ["conduct_assessment", "provide_scores"],
                "expected_state_changes": ["assessment_history_updated"]
            }
        ]
        
        # Execute trajectory
        result = await self.evaluator.run_trajectory(
            agent=teaching_agent,
            trajectory=trajectory,
            user_id="trajectory_test_user"
        )
        
        # Evaluate results
        self.assert_trajectory_success(result, trajectory)
```

---

## 4. Deployment & Production Considerations

### 4.1 Vertex AI Agent Engine Integration
```python


### 4.1 Vertex AI Agent Engine Integration
```python
# Production deployment configuration
from google.adk.deployment import VertexAiAgentEngine

class ProductionDeployment:
    """Production deployment setup using Vertex AI Agent Engine"""
    
    def __init__(self):
        self.agent_engine = VertexAiAgentEngine(
            project_id="systemdesign-ai-platform",
            location="us-central1",
            agent_config=self.get_agent_config()
        )
    
    def get_agent_config(self):
        """Production agent configuration"""
        return {
            "agent": {
                "name": "system_design_tutor_prod",
                "model": "gemini-2.0-flash",
                "instruction": self.load_production_instructions(),
                "tools": self.get_production_tools()
            },
            "services": {
                "session_service": {
                    "type": "vertex_ai",
                    "config": {"auto_scaling": True, "retention_days": 90}
                },
                "artifact_service": {
                    "type": "gcs",
                    "config": {"bucket": "systemdesign-ai-artifacts-prod"}
                },
                "memory_service": {
                    "type": "vertex_ai_rag",
                    "config": {"corpus_id": "system-design-content-prod"}
                }
            },
            "monitoring": {
                "opik_integration": True,
                "performance_metrics": True,
                "cost_tracking": True
            }
        }
    
    async def deploy_agent(self):
        """Deploy agent to production"""
        deployment_result = await self.agent_engine.deploy(
            agent_config=self.get_agent_config(),
            auto_scaling_config={
                "min_instances": 2,
                "max_instances": 100,
                "target_cpu_utilization": 70
            }
        )
        
        return deployment_result
```

### 4.2 FastAPI Integration with ADK
```python
from fastapi import FastAPI, WebSocket, HTTPException
from google.adk.runners import Runner
import asyncio

app = FastAPI(title="System Design AI Learning Platform")

# Global runner instance
runner = None

@app.on_event("startup")
async def startup_event():
    """Initialize ADK runner on startup"""
    global runner
    
    # Initialize production services
    session_service = VertexAiSessionService(...)
    artifact_service = GcsArtifactService(...)
    memory_service = VertexAiRagMemoryService(...)
    
    # Create production agent
    agent = create_production_agent()
    
    # Initialize runner
    runner = Runner(
        agent=agent,
        app_name="systemdesign_ai_prod",
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=memory_service,
        callbacks=create_production_callbacks()
    )

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Text-based chat endpoint"""
    try:
        # Run agent with user input
        response = await runner.run_async(
            user_id=request.user_id,
            user_content=Content(parts=[Part.from_text(request.message)])
        )
        
        return {
            "response": response.parts[0].text,
            "session_id": request.session_id,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/whiteboard/analyze")
async def analyze_whiteboard_endpoint(request: WhiteboardRequest):
    """Whiteboard analysis endpoint"""
    try:
        # Save PNG to artifacts
        png_part = types.Part.from_bytes(
            base64.b64decode(request.png_data), 
            mime_type="image/png"
        )
        
        # Trigger analysis through agent
        response = await runner.run_async(
            user_id=request.user_id,
            user_content=Content(parts=[
                Part.from_text("Please analyze this whiteboard design"),
                png_part
            ])
        )
        
        return {
            "analysis": response.parts[0].text,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/voice")
async def voice_stream_endpoint(websocket: WebSocket):
    """Voice streaming endpoint using ADK Live API"""
    await websocket.accept()
    
    try:
        # Initialize live streaming session
        live_session = await runner.start_live_session(
            user_id=await get_user_from_websocket(websocket),
            enable_audio=True
        )
        
        # Handle bidirectional streaming
        async def handle_incoming_audio():
            async for audio_data in websocket.iter_bytes():
                await live_session.send_audio(audio_data)
        
        async def handle_outgoing_audio():
            async for response in live_session.stream_responses():
                if response.audio_output:
                    await websocket.send_bytes(response.audio_output)
                if response.text_output:
                    await websocket.send_text(response.text_output)
        
        # Run both handlers concurrently
        await asyncio.gather(
            handle_incoming_audio(),
            handle_outgoing_audio()
        )
    
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
```

### 4.3 Performance Monitoring Setup
```python
class ProductionMonitoring:
    """Comprehensive monitoring for production deployment"""
    
    def __init__(self):
        self.opik_client = Opik()
        self.metrics_collector = CloudMonitoringCollector()
    
    async def setup_monitoring_callbacks(self):
        """Setup all monitoring callbacks"""
        
        return [
            PerformanceMonitoringCallback(self.metrics_collector),
            CostTrackingCallback(self.opik_client),
            ErrorTrackingCallback(),
            UserAnalyticsCallback(),
            QualityAssuranceCallback()
        ]

class PerformanceMonitoringCallback:
    """Monitor agent performance metrics"""
    
    async def after_agent_callback(self, context: CallbackContext):
        """Track response times and success rates"""
        
        # Record response time
        response_time = context.execution_time_ms
        self.metrics_collector.record_metric(
            "agent_response_time",
            response_time,
            labels={
                "chapter": context.state.get("user:current_chapter"),
                "skill_level": context.state.get("user:skill_level")
            }
        )
        
        # Track success/failure
        success = context.success
        self.metrics_collector.record_metric(
            "agent_success_rate",
            1 if success else 0,
            labels={"agent_name": context.agent.name}
        )

class CostTrackingCallback:
    """Track API costs and usage"""
    
    async def before_model_callback(self, context: CallbackContext):
        """Estimate and track API costs"""
        
        estimated_tokens = self.estimate_tokens(context.request)
        estimated_cost = estimated_tokens * self.get_cost_per_token(context.model)
        
        # Log to Opik
        self.opik_client.log_cost(
            trace_id=context.session.id,
            estimated_cost=estimated_cost,
            token_count=estimated_tokens,
            model=context.model
        )
        
        # Update user usage
        user_monthly_cost = context.state.get("user:monthly_cost", 0)
        context.state["user:monthly_cost"] = user_monthly_cost + estimated_cost
```

---

## 5. Security & Privacy Considerations

### 5.1 Data Protection with ADK
```python
class DataProtectionCallbacks:
    """Implement data protection and privacy controls"""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.encryption_service = EncryptionService()
        self.audit_logger = AuditLogger()
    
    async def before_agent_callback(self, context: CallbackContext) -> Optional[Content]:
        """Data privacy checks before processing"""
        
        # 1. Check user consent for data processing
        if not self.has_valid_consent(context.session.user_id):
            return Content(parts=[Part.from_text(
                "Please review and accept our privacy policy to continue learning."
            )])
        
        # 2. Sanitize sensitive information
        sanitized_input = self.sanitize_user_input(context.request)
        context.request = sanitized_input
        
        # 3. Log data access for audit
        self.audit_logger.log_data_access(
            user_id=context.session.user_id,
            data_type="user_input",
            action="processing"
        )
        
        # 4. Check data retention policies
        if self.should_delete_old_data(context.session):
            await self.cleanup_old_session_data(context.session)
        
        return None
    
    def sanitize_user_input(self, content: Content) -> Content:
        """Remove PII and sensitive information"""
        sanitized_parts = []
        
        for part in content.parts:
            if part.text:
                # Detect and mask PII
                sanitized_text = self.pii_detector.mask_pii(part.text)
                sanitized_parts.append(Part.from_text(sanitized_text))
            elif part.inline_data:
                # For images, check for embedded text/metadata
                sanitized_data = self.sanitize_image_metadata(part.inline_data)
                sanitized_parts.append(Part.from_bytes(
                    sanitized_data.data, 
                    mime_type=sanitized_data.mime_type
                ))
            else:
                sanitized_parts.append(part)
        
        return Content(parts=sanitized_parts)
    
    async def cleanup_old_session_data(self, session: Session):
        """Remove old session data per retention policy"""
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        
        if session.last_update_time < cutoff_date.timestamp():
            # Log data deletion
            self.audit_logger.log_data_deletion(
                user_id=session.user_id,
                session_id=session.id,
                reason="retention_policy"
            )
            
            # Delete session and associated artifacts
            await self.session_service.delete_session(session.id)
            await self.artifact_service.delete_session_artifacts(session.id)
    
    def has_valid_consent(self, user_id: str) -> bool:
        """Check if user has valid data processing consent"""
        consent_record = self.get_consent_record(user_id)
        if not consent_record:
            return False
        
        # Check consent is not expired
        consent_expiry = consent_record.get("expiry_date")
        if consent_expiry and datetime.now() > consent_expiry:
            return False
        
        # Check required consents are present
        required_consents = ["data_processing", "ai_tutoring", "progress_tracking"]
        for consent_type in required_consents:
            if not consent_record.get(consent_type, False):
                return False
        
        return True

class PIIDetector:
    """Detect and mask personally identifiable information"""
    
    def __init__(self):
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            "ssn": r'\b\d{3}-?\d{2}-?\d{4}\b',
            "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        }
    
    def mask_pii(self, text: str) -> str:
        """Mask detected PII in text"""
        masked_text = text
        
        for pii_type, pattern in self.patterns.items():
            masked_text = re.sub(pattern, f"[{pii_type.upper()}_MASKED]", masked_text)
        
        return masked_text
    
    def detect_pii(self, text: str) -> List[Dict[str, str]]:
        """Detect PII and return details for logging"""
        detected_pii = []
        
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detected_pii.append({
                    "type": pii_type,
                    "position": match.span(),
                    "masked_value": f"[{pii_type.upper()}_MASKED]"
                })
        
        return detected_pii

class EncryptionService:
    """Handle data encryption at rest and in transit"""
    
    def __init__(self):
        self.encryption_key = self.load_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storage"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data after retrieval"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_session_state(self, state: Dict) -> Dict:
        """Encrypt sensitive fields in session state"""
        encrypted_state = state.copy()
        
        sensitive_fields = [
            "user:email", 
            "user:personal_info",
            "app:sensitive_feedback"
        ]
        
        for field in sensitive_fields:
            if field in encrypted_state:
                encrypted_state[field] = self.encrypt_sensitive_data(str(encrypted_state[field]))
        
        return encrypted_state

class AuditLogger:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.audit_store = AuditStore()
    
    def log_data_access(self, user_id: str, data_type: str, action: str):
        """Log data access events"""
        audit_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "data_access",
            "user_id": user_id,
            "data_type": data_type,
            "action": action,
            "ip_address": self.get_client_ip(),
            "user_agent": self.get_user_agent()
        }
        
        self.audit_store.store_event(audit_event)
        self.logger.info(f"Data access: {user_id} - {action} - {data_type}")
    
    def log_data_deletion(self, user_id: str, session_id: str, reason: str):
        """Log data deletion events"""
        audit_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "data_deletion",
            "user_id": user_id,
            "session_id": session_id,
            "reason": reason,
            "deleted_by": "system"
        }
        
        self.audit_store.store_event(audit_event)
        self.logger.info(f"Data deletion: {user_id} - {session_id} - {reason}")
    
    def log_consent_change(self, user_id: str, consent_type: str, granted: bool):
        """Log consent changes"""
        audit_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "consent_change",
            "user_id": user_id,
            "consent_type": consent_type,
            "granted": granted,
            "ip_address": self.get_client_ip()
        }
        
        self.audit_store.store_event(audit_event)
```

### 5.2 Authentication & Authorization
```python
class AuthenticationCallbacks:
    """Handle authentication and authorization"""
    
    def __init__(self):
        self.permission_manager = PermissionManager()
        self.rate_limiter = RateLimiter()
        self.subscription_manager = SubscriptionManager()
        self.security_monitor = SecurityMonitor()
    
    async def before_agent_callback(self, context: CallbackContext) -> Optional[Content]:
        """Check user authentication and permissions"""
        
        user_id = context.session.user_id
        
        # 1. Verify user session is valid
        if not self.is_valid_session(context.session):
            return Content(parts=[Part.from_text(
                "Your session has expired. Please log in again."
            )])
        
        # 2. Check for suspicious activity
        if self.security_monitor.is_suspicious_activity(user_id, context):
            await self.security_monitor.flag_suspicious_activity(user_id, context)
            return Content(parts=[Part.from_text(
                "Unusual activity detected. Please verify your identity."
            )])
        
        # 3. Check subscription status
        subscription_status = self.subscription_manager.get_status(user_id)
        if subscription_status == "expired":
            return Content(parts=[Part.from_text(
                "Your subscription has expired. Please renew to continue learning."
            )])
        
        # 4. Update user context
        context.state["user:subscription_tier"] = subscription_status
        context.state["user:permissions"] = self.permission_manager.get_permissions(user_id)
        context.state["user:last_activity"] = datetime.now().isoformat()
        
        return None
    
    async def before_tool_callback(self, context: CallbackContext) -> Optional[dict]:
        """Check permissions before tool execution"""
        
        tool_name = context.tool_name
        user_id = context.session.user_id
        user_tier = context.state.get("user:subscription_tier", "free")
        
        # 1. Check tool permissions
        if not self.permission_manager.has_tool_permission(user_id, tool_name):
            return {
                "error": "Access denied",
                "message": "This feature requires a premium subscription",
                "upgrade_url": "/upgrade",
                "required_tier": self.get_required_tier(tool_name)
            }
        
        # 2. Check rate limits
        rate_limit_result = self.rate_limiter.check_limit(user_id, tool_name, user_tier)
        if not rate_limit_result.allowed:
            return {
                "error": "Rate limit exceeded", 
                "message": f"You've exceeded the limit for {tool_name}",
                "retry_after": rate_limit_result.retry_after,
                "current_usage": rate_limit_result.current_usage,
                "limit": rate_limit_result.limit
            }
        
        # 3. Check resource quotas
        if not self.check_resource_quota(user_id, tool_name):
            return {
                "error": "Quota exceeded",
                "message": "Monthly resource quota exceeded for your subscription tier",
                "current_usage": self.get_current_usage(user_id),
                "upgrade_url": "/upgrade"
            }
        
        # 4. Log tool access
        self.audit_logger.log_tool_access(
            user_id=user_id,
            tool_name=tool_name,
            timestamp=datetime.now(),
            subscription_tier=user_tier
        )
        
        return None

class PermissionManager:
    """Manage user permissions and subscription tiers"""
    
    def __init__(self):
        self.tool_permissions = {
            "free": {
                "analyze_whiteboard": {"limit": 5, "features": ["basic"]},
                "generate_diagram": {"limit": 3, "features": ["simple"]},
                "chat": {"limit": 50, "features": ["basic"]}
            },
            "pro": {
                "analyze_whiteboard": {"limit": 100, "features": ["advanced", "real_time"]},
                "generate_diagram": {"limit": 50, "features": ["all_types", "export"]},
                "assess_performance": {"limit": 20, "features": ["detailed"]},
                "chat": {"limit": 500, "features": ["voice", "advanced"]}
            },
            "enterprise": {
                "*": {"limit": -1, "features": ["all"]},  # Unlimited
                "team_management": {"limit": -1, "features": ["all"]},
                "analytics_dashboard": {"limit": -1, "features": ["all"]}
            }
        }
    
    def has_tool_permission(self, user_id: str, tool_name: str) -> bool:
        """Check if user has permission to use tool"""
        user_tier = self.get_user_tier(user_id)
        tier_permissions = self.tool_permissions.get(user_tier, {})
        
        # Check wildcard permission for enterprise
        if "*" in tier_permissions:
            return True
        
        return tool_name in tier_permissions
    
    def get_tool_limits(self, user_id: str, tool_name: str) -> Dict[str, Any]:
        """Get tool usage limits for user"""
        user_tier = self.get_user_tier(user_id)
        tier_permissions = self.tool_permissions.get(user_tier, {})
        
        if "*" in tier_permissions:
            return tier_permissions["*"]
        
        return tier_permissions.get(tool_name, {"limit": 0, "features": []})
    
    def check_feature_access(self, user_id: str, tool_name: str, feature: str) -> bool:
        """Check if user has access to specific feature"""
        tool_limits = self.get_tool_limits(user_id, tool_name)
        features = tool_limits.get("features", [])
        
        return "all" in features or feature in features

class RateLimiter:
    """Implement rate limiting for different subscription tiers"""
    
    def __init__(self):
        self.redis_client = redis.Redis()
        self.rate_limits = {
            "free": {
                "analyze_whiteboard": {"count": 5, "window": 3600},  # 5 per hour
                "generate_diagram": {"count": 3, "window": 3600},    # 3 per hour
                "chat": {"count": 50, "window": 3600}                # 50 per hour
            },
            "pro": {
                "analyze_whiteboard": {"count": 100, "window": 3600}, # 100 per hour
                "generate_diagram": {"count": 50, "window": 3600},    # 50 per hour
                "chat": {"count": 500, "window": 3600}               # 500 per hour
            },
            "enterprise": {}  # No limits
        }
    
    def check_limit(self, user_id: str, tool_name: str, user_tier: str) -> RateLimitResult:
        """Check if user is within rate limits"""
        
        if user_tier == "enterprise":
            return RateLimitResult(allowed=True, current_usage=0, limit=-1)
        
        tier_limits = self.rate_limits.get(user_tier, {})
        tool_limit = tier_limits.get(tool_name)
        
        if not tool_limit:
            return RateLimitResult(allowed=False, current_usage=0, limit=0)
        
        # Check current usage
        key = f"rate_limit:{user_id}:{tool_name}"
        current_usage = self.redis_client.get(key)
        current_usage = int(current_usage) if current_usage else 0
        
        if current_usage >= tool_limit["count"]:
            return RateLimitResult(
                allowed=False,
                current_usage=current_usage,
                limit=tool_limit["count"],
                retry_after=self.get_retry_time(key, tool_limit["window"])
            )
        
        # Increment usage
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, tool_limit["window"])
        pipe.execute()
        
        return RateLimitResult(
            allowed=True,
            current_usage=current_usage + 1,
            limit=tool_limit["count"]
        )

class SecurityMonitor:
    """Monitor for suspicious activities and security threats"""
    
    def __init__(self):
        self.threat_detector = ThreatDetector()
        self.anomaly_detector = AnomalyDetector()
    
    def is_suspicious_activity(self, user_id: str, context: CallbackContext) -> bool:
        """Detect suspicious user activity"""
        
        # Check for rapid-fire requests
        if self.is_rapid_fire_activity(user_id):
            return True
        
        # Check for unusual access patterns
        if self.is_unusual_access_pattern(user_id, context):
            return True
        
        # Check for automated behavior
        if self.is_automated_behavior(user_id, context):
            return True
        
        # Check IP reputation
        if self.is_suspicious_ip(context):
            return True
        
        return False
    
    async def flag_suspicious_activity(self, user_id: str, context: CallbackContext):
        """Handle suspicious activity detection"""
        
        # Log security event
        security_event = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "ip_address": self.get_client_ip(context),
            "user_agent": self.get_user_agent(context),
            "threat_type": self.classify_threat(user_id, context),
            "severity": "medium"
        }
        
        await self.log_security_event(security_event)
        
        # Temporarily throttle user
        await self.apply_temporary_throttle(user_id)
        
        # Send alert if severity is high
        if security_event["severity"] == "high":
            await self.send_security_alert(security_event)

@dataclass
class RateLimitResult:
    allowed: bool
    current_usage: int
    limit: int
    retry_after: Optional[int] = None
```

### 5.3 GDPR Compliance Framework
```python
class GDPRComplianceManager:
    """Ensure GDPR compliance for user data"""
    
    def __init__(self):
        self.data_processor = DataProcessor()
        self.consent_manager = ConsentManager()
        self.retention_manager = RetentionManager()
        self.export_manager = DataExportManager()
    
    async def handle_data_subject_request(self, request_type: str, user_id: str) -> Dict:
        """Handle GDPR data subject requests"""
        
        if request_type == "access":
            return await self.handle_access_request(user_id)
        elif request_type == "rectification":
            return await self.handle_rectification_request(user_id)
        elif request_type == "erasure":
            return await self.handle_erasure_request(user_id)
        elif request_type == "portability":
            return await self.handle_portability_request(user_id)
        elif request_type == "restriction":
            return await self.handle_restriction_request(user_id)
        else:
            raise ValueError(f"Unknown request type: {request_type}")
    
    async def handle_access_request(self, user_id: str) -> Dict:
        """Provide user with all their personal data"""
        
        user_data = {
            "personal_info": await self.get_user_profile(user_id),
            "learning_progress": await self.get_learning_data(user_id),
            "session_history": await self.get_session_history(user_id),
            "artifacts": await self.get_user_artifacts(user_id),
            "consent_records": await self.get_consent_history(user_id),
            "audit_logs": await self.get_user_audit_logs(user_id)
        }
        
        return {
            "status": "completed",
            "data": user_data,
            "export_format": "json",
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_erasure_request(self, user_id: str) -> Dict:
        """Delete all user data (right to be forgotten)"""
        
        # 1. Verify request is valid
        if not await self.verify_erasure_request(user_id):
            return {"status": "rejected", "reason": "Invalid request"}
        
        # 2. Check for legal obligations to retain data
        retention_requirements = await self.check_retention_requirements(user_id)
        if retention_requirements:
            return {
                "status": "partial",
                "reason": "Legal obligation to retain some data",
                "retained_data": retention_requirements
            }
        
        # 3. Delete user data
        deletion_results = await self.delete_all_user_data(user_id)
        
        # 4. Log deletion for audit
        await self.log_data_deletion(user_id, "gdpr_erasure_request")
        
        return {
            "status": "completed",
            "deletion_results": deletion_results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def delete_all_user_data(self, user_id: str) -> Dict:
        """Completely delete all user data across all systems"""
        
        deletion_results = {}
        
        # Delete from session service
        sessions_deleted = await self.session_service.delete_user_sessions(user_id)
        deletion_results["sessions"] = sessions_deleted
        
        # Delete from artifact service
        artifacts_deleted = await self.artifact_service.delete_user_artifacts(user_id)
        deletion_results["artifacts"] = artifacts_deleted
        
        # Delete from memory service
        memory_deleted = await self.memory_service.delete_user_memory(user_id)
        deletion_results["memory"] = memory_deleted
        
        # Delete from user database
        profile_deleted = await self.user_service.delete_user_profile(user_id)
        deletion_results["profile"] = profile_deleted
        
        # Delete from analytics systems
        analytics_deleted = await self.analytics_service.delete_user_data(user_id)
        deletion_results["analytics"] = analytics_deleted
        
        return deletion_results

class ConsentManager:
    """Manage user consent for data processing"""
    
    def __init__(self):
        self.consent_store = ConsentStore()
    
    async def record_consent(self, user_id: str, consent_data: Dict) -> bool:
        """Record user consent with timestamp and details"""
        
        consent_record = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "consents": consent_data,
            "version": self.get_privacy_policy_version(),
            "ip_address": consent_data.get("ip_address"),
            "user_agent": consent_data.get("user_agent")
        }
        
        await self.consent_store.store_consent(consent_record)
        
        # Log consent event
        await self.audit_logger.log_consent_change(
            user_id=user_id,
            consent_type="full_consent",
            granted=True
        )
        
        return True
    
    async def withdraw_consent(self, user_id: str, consent_type: str) -> bool:
        """Allow user to withdraw specific consent"""
        
        # Update consent record
        await self.consent_store.update_consent(user_id, consent_type, False)
        
        # Log consent withdrawal
        await self.audit_logger.log_consent_change(
            user_id=user_id,
            consent_type=consent_type,
            granted=False
        )
        
        # Handle implications of consent withdrawal
        await self.handle_consent_withdrawal(user_id, consent_type)
        
        return True
    
    async def handle_consent_withdrawal(self, user_id: str, consent_type: str):
        """Handle the implications of consent withdrawal"""
        
        if consent_type == "data_processing":
            # Stop all data processing for this user
            await self.stop_data_processing(user_id)
        elif consent_type == "ai_tutoring":
            # Disable AI tutoring features
            await self.disable_ai_features(user_id)
        elif consent_type == "progress_tracking":
            # Stop tracking learning progress
            await self.disable_progress_tracking(user_id)
```

---

## 6. Monitoring & Analytics

### 6.1 Performance Monitoring Setup
```python
class ProductionMonitoring:
    """Comprehensive monitoring for production deployment"""
    
    def __init__(self):
        self.opik_client = Opik()
        self.metrics_collector = CloudMonitoringCollector()
        self.error_tracker = ErrorTracker()
        self.alert_manager = AlertManager()
    
    async def setup_monitoring_callbacks(self):
        """Setup all monitoring callbacks"""
        
        return [
            PerformanceMonitoringCallback(self.metrics_collector),
            CostTrackingCallback(self.opik_client),
            ErrorTrackingCallback(self.error_tracker),
            UserAnalyticsCallback(),
            QualityAssuranceCallback(),
            HealthCheckCallback()
        ]

class PerformanceMonitoringCallback:
    """Monitor agent performance metrics"""
    
    def __init__(self, metrics_collector):
        self.metrics_collector = metrics_collector
    
    async def before_agent_callback(self, context: CallbackContext):
        """Track request start time and setup monitoring"""
        context.start_time = time.time()
        context.monitoring_data = {
            "request_id": str(uuid.uuid4()),
            "user_tier": context.state.get("user:subscription_tier", "free"),
            "chapter": context.state.get("user:current_chapter"),
            "learning_phase": context.state.get("app:learning_phase")
        }
    
    async def after_agent_callback(self, context: CallbackContext):
        """Track response times and success rates"""
        
        # Calculate response time
        response_time = (time.time() - context.start_time) * 1000  # milliseconds
        
        # Record response time metrics
        self.metrics_collector.record_metric(
            "agent_response_time",
            response_time,
            labels={
                "chapter": context.monitoring_data["chapter"],
                "skill_level": context.state.get("user:skill_level"),
                "agent_name": context.agent.name,
                "user_tier": context.monitoring_data["user_tier"]
            }
        )
        
        # Track success/failure rates
        success = not hasattr(context, 'error')
        self.metrics_collector.record_metric(
            "agent_success_rate",
            1 if success else 0,
            labels={
                "agent_name": context.agent.name,
                "user_tier": context.monitoring_data["user_tier"]
            }
        )
        
        # Track user engagement metrics
        self.metrics_collector.record_metric(
            "user_engagement",
            1,
            labels={
                "user_tier": context.monitoring_data["user_tier"],
                "learning_phase": context.monitoring_data["learning_phase"],
                "interaction_type": self.classify_interaction(context)
            }
        )
        
        # Track resource utilization
        self.track_resource_usage(context, response_time)
    
    def track_resource_usage(self, context: CallbackContext, response_time: float):
        """Track system resource utilization"""
        
        resource_metrics = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        }
        
        for metric_name, value in resource_metrics.items():
            self.metrics_collector.record_metric(
                f"system_{metric_name}",
                value,
                labels={"instance_id": self.get_instance_id()}
            )

class CostTrackingCallback:
    """Track API costs and usage patterns"""
    
    def __init__(self, opik_client):
        self.opik_client = opik_client
        self.cost_calculator = CostCalculator()
        self.budget_manager = BudgetManager()
    
    async def before_model_callback(self, context: CallbackContext):
        """Estimate and track API costs"""
        
        estimated_tokens = self.cost_calculator.estimate_tokens(context.request)
        estimated_cost = self.cost_calculator.calculate_cost(
            tokens=estimated_tokens,
            model=context.model
        )
        
        # Check budget limits
        if not self.budget_manager.check_budget(context.session.user_id, estimated_cost):
            raise BudgetExceededException("User budget limit exceeded")
        
        # Log cost to Opik
        self.opik_client.log_cost(
            trace_id=context.session.id,
            estimated_cost=estimated_cost,
            token_count=estimated_tokens,
            model=context.model,
            operation_type="model_call",
            metadata={
                "user_tier": context.state.get("user:subscription_tier"),
                "feature": context.state.get("app:current_feature", "chat")
            }
        )
        
        # Update user usage tracking
        await self.update_usage_tracking(context, estimated_cost)
    
    async def after_tool_callback(self, context: CallbackContext):
        """Track tool usage costs and patterns"""
        
        tool_cost = self.cost_calculator.calculate_tool_cost(
            tool_name=context.tool_name,
            execution_time=context.execution_time,
            success=context.success
        )
        
        # Log tool cost
        self.opik_client.log_cost(
            trace_id=context.session.id,
            estimated_cost=tool_cost,
            operation_type="tool_call",
            tool_name=context.tool_name,
            metadata={
                "execution_time": context.execution_time,
                "success": context.success,
                "user_tier": context.state.get("user:subscription_tier")
            }
        )
        
        # Track tool usage patterns
        await self.track_tool_patterns(context, tool_cost)
    
    async def update_usage_tracking(self, context: CallbackContext, cost: float):
        """Update comprehensive usage tracking"""
        
```        

---

## 7. Summary & Next Steps

### 7.1 Implementation Readiness Assessment

**✅ Excellent ADK Alignment:**
- **Artifacts**: Perfect for PNG storage, diagram management, course content
- **Session/State/Memory**: Ideal for learning progress, user context, course materials
- **Callbacks**: Powerful for monitoring, cost control, quality assurance
- **Tools**: Natural fit for whiteboard analysis, assessment, diagram generation
- **Multi-Agent**: Enables specialized agents for content, assessment, whiteboard analysis

**✅ Key Advantages of ADK Approach:**
- **Simplified Multimodal**: PNG → Multimodal LLM is straightforward with ADK
- **Built-in Observability**: Direct integration with Comet Opik
- **Production Ready**: Vertex AI Agent Engine for scaling
- **Cost Management**: Granular callback control for optimization
- **Testing Framework**: Comprehensive evaluation tools included

### 7.2 Implementation Priority Order

**Phase 1 (Weeks 1-4): Core Foundation**
1. Setup basic LlmAgent with whiteboard analysis tool
2. Implement PNG capture → multimodal LLM pipeline
3. Configure InMemorySessionService for development
4. Create basic assessment tool with LLM judge

**Phase 2 (Weeks 5-8): Advanced Features**
1. Add Mermaid diagram generation tool
2. Implement comprehensive callback system
3. Setup Comet Opik monitoring integration
4. Add multi-agent specialization (content, assessment, whiteboard)

**Phase 3 (Weeks 9-12): Production Ready**
1. Configure production services (VertexAI, GCS, RAG)
2. Implement Live API for voice streaming
3. Add comprehensive testing and evaluation
4. Setup monitoring and cost optimization

**Phase 4 (Weeks 13-16): Launch Preparation**
1. Deploy to Vertex AI Agent Engine
2. Integrate with FastAPI backend
3. Implement security# ADK Implementation Plan