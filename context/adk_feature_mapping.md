# ADK Feature Mapping
## AI System Design Learning Platform

### Document Information
- **Version**: 1.0
- **Date**: June 2025
- **Purpose**: Map product features to ADK capabilities
- **Companion Document**: ADK Implementation Plan

---

## 1. ADK Feature Mapping Overview

### 1.1 Core Product Features → ADK Capabilities

| Product Feature | ADK Component | Implementation Strategy |
|-----------------|---------------|-------------------------|
| **Whiteboard PNG Analysis** | Artifacts + MultiModal LLM | Store PNG as artifacts, analyze via multimodal model |
| **Course Content Context** | Memory + Session State | Load chapter content into memory, maintain learning progress in state |
| **Real-time Feedback** | Callbacks + Tools | Use callbacks for monitoring, tools for whiteboard analysis |
| **Progress Tracking** | Session State + Memory | Store assessment scores in state, historical data in memory |
| **AI Diagram Generation** | Artifacts + Tools | Generate Mermaid code, save rendered PNGs as artifacts |
| **Voice Interaction** | Live API + Streaming | Use Gemini Live API for bidirectional audio streaming |
| **Assessment System** | Tools + Callbacks | LLM judge as tool, validation callbacks |
| **Session Management** | SessionService + State | Persistent sessions with learning progress state |

---

## 2. Detailed Feature Implementation Mapping

### 2.1 Artifacts Management Strategy

#### **Whiteboard PNG Storage**
```python
# Implementation Pattern
from google.adk.artifacts import GcsArtifactService
from google.adk.tools import ToolContext

def save_whiteboard_png(png_data: bytes, session_id: str, tool_context: ToolContext):
    """Save user's whiteboard drawing as artifact"""
    filename = f"whiteboard_{session_id}_{timestamp}.png"
    artifact_part = types.Part.from_bytes(png_data, mime_type="image/png")
    tool_context.save_artifact(filename, artifact_part)
    return filename

def analyze_whiteboard(filename: str, tool_context: ToolContext):
    """Load and analyze whiteboard PNG"""
    artifact = tool_context.load_artifact(filename)
    # Send to multimodal LLM for analysis
    return llm_analyze_image(artifact)
```

#### **AI-Generated Diagrams**
```python
def save_generated_diagram(mermaid_code: str, rendered_png: bytes, tool_context: ToolContext):
    """Save both Mermaid code and rendered diagram"""
    # Save source code
    code_part = types.Part.from_text(mermaid_code)
    tool_context.save_artifact(f"diagram_source_{timestamp}.mmd", code_part)
    
    # Save rendered image
    png_part = types.Part.from_bytes(rendered_png, mime_type="image/png")
    tool_context.save_artifact(f"diagram_render_{timestamp}.png", png_part)
```

**ADK Configuration**:
```python
# Production: Use GCS for persistent storage
artifact_service = GcsArtifactService(
    bucket_name="systemdesign-ai-artifacts",
    project_id="your-project-id"
)

# Development: Use in-memory for testing
artifact_service = InMemoryArtifactService()
```

### 2.2 Session, State & Memory Architecture

#### **Session State Structure**
```python
# Session state organization for our platform
session_state = {
    # User profile and progress
    "user:skill_level": "intermediate",
    "user:current_chapter": "design_twitter", 
    "user:completed_chapters": ["design_url_shortener"],
    "user:assessment_history": [
        {"chapter": "design_url_shortener", "overall_score": 3.8, "timestamp": "..."}
    ],
    
    # Current session context
    "app:active_whiteboard": "whiteboard_session_001.png",
    "app:learning_phase": "interview_simulation",  # study | interview_simulation | assessment
    "app:current_feedback": {"strengths": [...], "improvements": [...]},
    
    # Temporary data for current interaction
    "temp:last_user_question": "How should I handle database sharding?",
    "temp:ai_diagram_queue": ["architecture_diagram_001", "sequence_diagram_002"]
}
```

#### **Memory Service for Course Content**
```python
# Strategy: Load entire chapter content into context vs. chunked retrieval
class ChapterContentStrategy:
    def __init__(self, memory_service: BaseMemoryService):
        self.memory_service = memory_service
    
    async def load_chapter_full_context(self, chapter_id: str) -> str:
        """Load complete chapter content into LLM context"""
        # For MVP: Load entire chapter (evaluate cost/latency)
        search_results = await self.memory_service.search_memory(
            query=f"chapter:{chapter_id} complete_content",
            limit=1
        )
        return search_results[0].content if search_results else None
    
    async def load_chapter_chunked(self, chapter_id: str, topic: str) -> List[str]:
        """Load relevant sections based on current discussion topic"""
        # For optimization: Retrieve relevant chunks only
        search_results = await self.memory_service.search_memory(
            query=f"chapter:{chapter_id} topic:{topic}",
            limit=5
        )
        return [result.content for result in search_results]

# Memory service configuration
memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/your-project/locations/us-central1/ragCorpora/system-design-content",
    similarity_top_k=10,
    vector_distance_threshold=0.7
)
```

### 2.3 Callbacks for Monitoring & Control

#### **Before/After Agent Callbacks**
```python
from google.adk.agents import CallbackContext
from google.adk.callbacks import BeforeAgentCallback, AfterAgentCallback

class LearningSessionCallbacks:
    """Callbacks for monitoring and controlling learning sessions"""
    
    async def before_agent_callback(self, context: CallbackContext) -> Optional[Content]:
        """Execute before agent processes user input"""
        # 1. Load user's current learning context
        session_state = context.state
        current_chapter = session_state.get("user:current_chapter")
        
        # 2. Ensure chapter content is loaded
        if current_chapter and not session_state.get(f"app:chapter_{current_chapter}_loaded"):
            await self._load_chapter_context(current_chapter, context)
            context.state[f"app:chapter_{current_chapter}_loaded"] = True
        
        # 3. Update activity tracking
        context.state["app:last_interaction"] = datetime.now().isoformat()
        
        return None  # Continue normal execution
    
    async def after_agent_callback(self, context: CallbackContext) -> Optional[Content]:
        """Execute after agent generates response"""
        # 1. Log interaction for analytics
        await self._log_interaction(context)
        
        # 2. Update learning progress
        await self._update_learning_progress(context)
        
        return None  # Don't override response
```

### 2.4 Tools Integration

#### **Whiteboard Analysis Tool**
```python
from google.adk.tools import FunctionTool, ToolContext

async def analyze_whiteboard_design(
    png_filename: str,
    analysis_type: str = "comprehensive",
    tool_context: ToolContext
) -> dict:
    """Analyze user's whiteboard design using multimodal LLM"""
    
    # 1. Load whiteboard PNG from artifacts
    whiteboard_artifact = tool_context.load_artifact(png_filename)
    if not whiteboard_artifact:
        return {"error": f"Whiteboard {png_filename} not found"}
    
    # 2. Get current learning context
    current_chapter = tool_context.state.get("user:current_chapter")
    skill_level = tool_context.state.get("user:skill_level", "intermediate")
    
    # 3. Construct analysis prompt
    analysis_prompt = f"""
    Analyze this system design whiteboard drawing for a {skill_level} level student 
    studying {current_chapter}. Provide {analysis_type} feedback on:
    
    1. Component identification and relationships
    2. Architectural soundness 
    3. Scalability considerations
    4. Missing critical components
    5. Specific suggestions for improvement
    
    Respond in structured JSON format matching the assessment rubric.
    """
    
    # 4. Call multimodal LLM
    response = await call_multimodal_llm(
        prompt=analysis_prompt,
        image=whiteboard_artifact,
        model="gemini-2.0-flash"  # Supports vision
    )
    
    # 5. Parse and store feedback
    feedback = parse_assessment_response(response)
    tool_context.state["app:last_whiteboard_feedback"] = feedback
    
    return feedback

# Register tool
whiteboard_analysis_tool = FunctionTool(func=analyze_whiteboard_design)
```

#### **Mermaid Diagram Generation Tool**
```python
async def generate_system_diagram(
    system_description: str,
    diagram_type: str = "architecture",  # architecture, sequence, flowchart
    tool_context: ToolContext
) -> dict:
    """Generate Mermaid diagram and render to PNG"""
    
    # 1. Generate Mermaid code using LLM
    mermaid_prompt = f"""
    Generate a {diagram_type} diagram in Mermaid syntax for this system:
    {system_description}
    
    Return only the Mermaid code, properly formatted.
    """
    
    mermaid_code = await call_llm(mermaid_prompt, model="gemini-2.0-flash")
    
    # 2. Render to PNG using MCP server
    rendered_png = await mermaid_mcp_render(mermaid_code)
    
    # 3. Save both source and rendered image as artifacts
    timestamp = int(time.time())
    source_filename = f"diagram_source_{timestamp}.mmd"
    png_filename = f"diagram_render_{timestamp}.png"
    
    # Save artifacts
    tool_context.save_artifact(source_filename, types.Part.from_text(mermaid_code))
    tool_context.save_artifact(png_filename, types.Part.from_bytes(rendered_png, mime_type="image/png"))
    
    return {
        "status": "success",
        "mermaid_code": mermaid_code,
        "png_filename": png_filename,
        "source_filename": source_filename
    }

# Register tool
diagram_generator_tool = FunctionTool(func=generate_system_diagram)
```

### 2.5 Comet Opik Integration

#### **ADK → Opik Monitoring Bridge**
```python
from opik import Opik
from google.adk.callbacks import CallbackContext

class OpikMonitoringCallbacks:
    """Bridge ADK events to Comet Opik for observability"""
    
    def __init__(self):
        self.opik_client = Opik()
    
    async def after_agent_callback(self, context: CallbackContext):
        """Log agent interactions to Opik"""
        
        # 1. Create trace for user session
        trace_id = context.session.id
        
        # 2. Log agent response
        self.opik_client.log_llm_call(
            trace_id=trace_id,
            model=context.agent.model,
            input=context.request.parts[0].text if context.request.parts else "",
            output=context.response.parts[0].text if context.response.parts else "",
            metadata={
                "chapter": context.state.get("user:current_chapter"),
                "learning_phase": context.state.get("app:learning_phase"),
                "skill_level": context.state.get("user:skill_level")
            }
        )
    
    async def after_tool_callback(self, context: CallbackContext):
        """Log tool usage to Opik"""
        
        self.opik_client.log_tool_call(
            trace_id=context.session.id,
            tool_name=context.tool_name,
            input=context.tool_input,
            output=context.tool_output,
            metadata={
                "execution_time": context.execution_time,
                "success": context.success
            }
        )
```

### 2.6 Voice/Streaming Integration

#### **Live API Configuration**
```python
from google.adk.agents import LlmAgent
from google.adk.runners import Runner

# Configure agent for voice streaming
teaching_agent = LlmAgent(
    name="system_design_tutor",
    model="gemini-2.0-flash",  # Supports Live API
    instruction="""
    You are an expert system design tutor. Provide clear, patient explanations 
    suitable for voice interaction. Ask follow-up questions to ensure understanding.
    Adapt your teaching style based on the user's responses and skill level.
    """,
    tools=[whiteboard_analysis_tool, diagram_generator_tool]
)

# Enable streaming for real-time interaction
runner = Runner(
    agent=teaching_agent,
    session_service=session_service,
    artifact_service=artifact_service,
    memory_service=memory_service
)

# Voice streaming endpoint
async def handle_voice_stream(websocket):
    """Handle bidirectional voice streaming"""
    async for audio_chunk in websocket:
        # Process incoming audio
        response_events = runner.stream_live(
            user_id="current_user",
            audio_input=audio_chunk,
            enable_voice_output=True
        )
        
        # Stream back audio responses
        async for event in response_events:
            if event.audio_output:
                await websocket.send(event.audio_output)
```

---

## 3. Agent Architecture Design

### 3.1 Multi-Agent System
```python
# Specialized agents for different capabilities
content_agent = LlmAgent(
    name="content_specialist",
    model="gemini-2.0-flash",
    instruction="Provide structured system design education content",
    tools=[load_chapter_content]
)

assessment_agent = LlmAgent(
    name="assessment_specialist", 
    model="gemini-2.0-flash",
    instruction="Evaluate student performance using structured rubrics",
    tools=[assessment_tool]
)

whiteboard_agent = LlmAgent(
    name="whiteboard_specialist",
    model="gemini-2.0-flash", 
    instruction="Analyze and provide feedback on system design diagrams",
    tools=[whiteboard_analysis_tool, diagram_generator_tool]
)

# Root coordinating agent
root_agent = LlmAgent(
    name="system_design_tutor",
    model="gemini-2.0-flash",
    instruction="""
    You are the main system design tutor. Coordinate with specialists:
    - Use content_specialist for educational material
    - Use whiteboard_specialist for diagram analysis and generation  
    - Use assessment_specialist for performance evaluation
    
    Guide students through: Study → Practice → Assessment → Progress Review
    """,
    tools=[
        AgentTool(content_agent),
        AgentTool(whiteboard_agent), 
        AgentTool(assessment_agent)
    ]
)
```

### 3.2 Service Configuration
```python
# Production service setup
from google.adk.sessions import VertexAiSessionService
from google.adk.artifacts import GcsArtifactService  
from google.adk.memory import VertexAiRagMemoryService

# Session service for persistent conversations
session_service = VertexAiSessionService(
    project_id="systemdesign-ai-platform",
    location="us-central1"
)

# Artifact service for PNGs, diagrams, course content
artifact_service = GcsArtifactService(
    bucket_name="systemdesign-ai-artifacts",
    project_id="systemdesign-ai-platform"
)

# Memory service for course content and user history
memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/systemdesign-ai-platform/locations/us-central1/ragCorpora/course-content",
    similarity_top_k=10
)

# Runner with all services
runner = Runner(
    agent=root_agent,
    app_name="systemdesign_ai_tutor",
    session_service=session_service,
    artifact_service=artifact_service,
    memory_service=memory_service,
    callbacks=[
        LearningSessionCallbacks(),
        OpikMonitoringCallbacks()
    ]
)
```

---

## 4. Key Implementation Advantages

### 4.1 Perfect Feature Alignment
- **Artifacts**: Ideal for PNG storage, diagram management, course content
- **Session/State/Memory**: Perfect for learning progress, user context, course materials
- **Callbacks**: Powerful for monitoring, cost control, quality assurance
- **Tools**: Natural fit for whiteboard analysis, assessment, diagram generation
- **Multi-Agent**: Enables specialized agents for different capabilities

### 4.2 Simplified Implementation
- **PNG → Multimodal LLM**: Straightforward with ADK's artifact system
- **Built-in Observability**: Direct integration with Comet Opik
- **Production Ready**: Vertex AI Agent Engine for scaling
- **Cost Management**: Granular callback control for optimization
- **Testing Framework**: Comprehensive evaluation tools included

### 4.3 Reduced Technical Risk
- **No Complex Shape Recognition**: Simple PNG analysis approach
- **Framework Maturity**: Built on proven Google infrastructure
- **Extensive Documentation**: Comprehensive guides and examples
- **Community Support**: Active development and community

---

*This document provides the foundation for understanding how ADK's features map to our product requirements. See the companion ADK Implementation Plan document for detailed development phases, testing strategies, and production deployment guidance.*