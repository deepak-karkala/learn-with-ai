# Project Context
## AI System Design Learning Platform - Detailed Context for Claude Code

### Business Context

#### Problem Statement
Software engineers struggle with system design interview preparation due to:
- Fragmented learning resources
- Lack of real-time feedback
- No interactive practice environments
- Difficulty tracking progress across competencies

#### Solution Overview
An AI-powered learning platform that provides:
- **Interactive AI Tutor**: Expert-level conversational guidance
- **Real-time Whiteboard Feedback**: Instant analysis of drawn architectures
- **Professional Diagram Generation**: High-quality system architecture diagrams
- **Comprehensive Assessment**: Multi-dimensional evaluation with detailed feedback
- **Progress Analytics**: Timeline visualization and personalized recommendations

#### Target Users
- **Primary**: Mid-level to Senior Software Engineers (3-8 years experience)
- **Secondary**: New graduates and bootcamp students
- **Use Case**: Preparing for FAANG/top-tier company system design interviews

### Technical Architecture

#### Core Components
1. **Frontend (NextJS)**
   - Interactive chat interface
   - HTML5 Canvas whiteboard
   - Progress dashboard with charts
   - Responsive design for desktop/tablet

2. **Backend (FastAPI + Google ADK)**
   - AI agent orchestration
   - Session and state management
   - Multimodal LLM integration
   - RESTful APIs and WebSocket support

3. **AI Layer (Google ADK)**
   - Multi-agent system with specialized agents
   - Context management and memory
   - Tool calling capabilities
   - Callback system for monitoring

#### Data Flow
```
User Input → Frontend → FastAPI → ADK Agent → LLM → Tools → Response
    ↓           ↓         ↓         ↓        ↓     ↓       ↓
   UI         API      Session   Context  Tools State  Artifacts
```

#### Key Technologies
- **Google ADK**: Agent orchestration and LLM integration
- **Multimodal LLMs**: GPT-4V/Claude 3.5 Sonnet for image analysis
- **Mermaid MCP**: Diagram generation and rendering
- **Vercel**: Deployment platform for frontend and serverless backend
- **PostgreSQL**: Production database for sessions and user data
- **Redis**: Caching and rate limiting
- **Comet Opik**: LLM monitoring and observability

### Core Features Deep Dive

#### 1. Interactive AI Tutor
**Purpose**: Provide expert-level system design guidance through conversation

**Implementation**:
- Google ADK LlmAgent with teaching persona
- Session-based context management
- Adaptive responses based on user skill level
- Tool calling for specialized functions

**Key Requirements**:
- Response time <2 seconds
- Context retention across conversation
- Natural, educational conversation style
- Integration with assessment and feedback systems

#### 2. Whiteboard Analysis
**Purpose**: Real-time feedback on user-drawn system architectures

**Technical Approach**:
- HTML5 Canvas for drawing interface
- PNG capture (not shape recognition)
- Multimodal LLM analysis of architectural drawings
- Structured feedback generation

**Implementation Details**:
```python
# Whiteboard analysis flow
canvas_png = capture_canvas_as_png()
analysis_prompt = create_analysis_prompt(user_context, skill_level)
feedback = multimodal_llm.analyze(canvas_png, analysis_prompt)
structured_response = parse_feedback(feedback)
store_as_artifact(canvas_png, feedback)
```

**Key Requirements**:
- Support freehand drawing and basic shapes
- Analysis latency <1 second
- Structured feedback with specific suggestions
- Integration with assessment system

#### 3. AI Diagram Generation
**Purpose**: Generate professional system architecture diagrams from conversation context

**Implementation**:
- Context analysis from conversation history
- Mermaid code generation via LLM
- PNG rendering through Mermaid MCP server
- Interactive diagram modification

**Technical Flow**:
```python
# Diagram generation process
context = extract_conversation_context()
system_components = identify_components(context)
mermaid_code = generate_mermaid_diagram(system_components, diagram_type)
png_image = mermaid_mcp_server.render(mermaid_code)
store_diagram_artifacts(mermaid_code, png_image)
```

**Key Requirements**:
- Multiple diagram types (architecture, sequence, flowchart)
- Context-aware component identification
- High-quality PNG output
- Diagram modification capabilities

#### 4. Assessment System
**Purpose**: Comprehensive evaluation across system design competencies

**Framework**: 6-dimensional assessment
1. Requirements Analysis & Problem Understanding (20%)
2. System Architecture & High-Level Design (25%) 
3. Technical Deep Dive & Component Design (20%)
4. Scale & Performance Considerations (15%)
5. Reliability & Fault Tolerance (10%)
6. Communication & Thought Process (10%)

**Implementation**:
```python
# Assessment flow
interaction_context = gather_interaction_data()
assessment_prompt = create_assessment_prompt(interaction_context, rubrics)
evaluation = llm_judge.evaluate(assessment_prompt)
scores = parse_dimensional_scores(evaluation)
feedback = generate_detailed_feedback(scores, evaluation)
confidence = calculate_confidence_score(evaluation)
store_assessment(scores, feedback, confidence)
```

**Key Requirements**:
- Detailed scoring rubrics for each dimension
- Confidence scoring for assessment quality
- Human review triggers for low confidence
- Progress tracking over time

#### 5. Progress Analytics
**Purpose**: Visual progress tracking and personalized learning recommendations

**Components**:
- Timeline visualization across all dimensions
- Trend analysis and pattern recognition
- Personalized improvement recommendations
- Goal setting and achievement tracking

**Implementation**:
```javascript
// Progress dashboard data flow
const progressData = await fetchUserProgress(userId);
const timelineData = processTimelineData(progressData.assessments);
const trends = analyzeTrends(timelineData);
const recommendations = generateRecommendations(trends, userGoals);
const dashboard = renderProgressDashboard(timelineData, trends, recommendations);
```

### Development Workflow

#### Issue-Based Development
- **24 total issues** across 4 phases
- Each issue has specific acceptance criteria
- Test-driven development approach
- Sequential implementation with dependencies

#### Quality Gates
Before moving to next issue:
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] Deployed to staging and verified

#### Testing Strategy
```bash
# Testing pyramid
Unit Tests (70%) → Integration Tests (20%) → E2E Tests (10%)

# Test commands
npm test                    # Frontend unit tests
pytest                     # Backend unit tests
npm run test:integration    # API integration tests
npm run test:e2e           # End-to-end user flows
npm run test:performance   # Load and performance tests
```

### ADK Integration Details

#### Agent Architecture
```python
# Multi-agent system structure
root_agent = LlmAgent(
    name="system_design_tutor",
    model="gemini-2.0-flash",
    instruction="You are an expert system design tutor...",
    tools=[
        AgentTool(content_specialist),      # Course content
        AgentTool(whiteboard_specialist),   # Whiteboard analysis
        AgentTool(assessment_specialist),   # Performance evaluation
        whiteboard_analysis_tool,           # PNG analysis
        diagram_generator_tool,             # Mermaid generation
        assessment_tool                     # LLM judge
    ]
)
```

#### Session Management
```python
# Session and state configuration
session_service = VertexAiSessionService(...)  # Production
artifact_service = GcsArtifactService(...)     # For PNGs and diagrams
memory_service = VertexAiRagMemoryService(...)  # Course content

# State structure
session_state = {
    "user:skill_level": "intermediate",
    "user:current_chapter": "design_twitter",
    "user:assessment_history": [...],
    "app:active_whiteboard": "whiteboard_001.png",
    "app:learning_phase": "interview_simulation",
    "temp:last_user_question": "How to handle sharding?"
}
```

#### Custom Tools
```python
# Whiteboard analysis tool
@tool
async def analyze_whiteboard_design(
    png_filename: str,
    analysis_type: str,
    tool_context: ToolContext
) -> dict:
    """Analyze user's whiteboard design using multimodal LLM"""
    artifact = tool_context.load_artifact(png_filename)
    analysis = await multimodal_llm_analyze(artifact, context)
    return structured_feedback

# Diagram generation tool  
@tool
async def generate_system_diagram(
    system_description: str,
    diagram_type: str,
    tool_context: ToolContext
) -> dict:
    """Generate Mermaid diagram and render to PNG"""
    mermaid_code = await generate_mermaid(system_description, diagram_type)
    png_data = await mermaid_mcp_render(mermaid_code)
    return save_diagram_artifacts(mermaid_code, png_data, tool_context)
```

### Performance & Cost Considerations

#### Performance Targets
- **API Response Time**: <2 seconds
- **Whiteboard Analysis**: <1 second
- **System Uptime**: >99.5%
- **Concurrent Users**: 100+ supported
- **Test Coverage**: >90%

#### Cost Management
- **Estimated cost per session**: $0.20-0.80
- **Optimization strategies**:
  - Caching for expensive operations
  - Batch processing for multiple requests
  - Rate limiting by subscription tier
  - Efficient prompt engineering

#### Monitoring & Observability
```python
# Comet Opik integration
from opik import Opik

class OpikMonitoringCallbacks:
    def __init__(self):
        self.opik_client = Opik()
    
    async def after_agent_callback(self, context):
        self.opik_client.log_llm_call(
            trace_id=context.session.id,
            model=context.agent.model,
            input=context.request,
            output=context.response,
            metadata={
                "chapter": context.state.get("user:current_chapter"),
                "skill_level": context.state.get("user:skill_level")
            }
        )
```

### Security & Privacy

#### Data Protection
- PII detection and masking
- GDPR compliance workflows
- Audit logging for all data access
- Encryption at rest and in transit

#### Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Rate limiting by subscription tier
- Input validation and sanitization

#### Privacy Controls
```python
# Privacy callback implementation
class DataProtectionCallbacks:
    async def before_agent_callback(self, context):
        # Check user consent
        if not self.has_valid_consent(context.session.user_id):
            return privacy_notice_content
        
        # Sanitize PII
        sanitized_input = self.sanitize_user_input(context.request)
        context.request = sanitized_input
        
        # Check retention policies
        if self.should_delete_old_data(context.session):
            await self.cleanup_old_session_data(context.session)
```

### Deployment & Infrastructure

#### Development Environment
```bash
# Local development setup
git clone https://github.com/your-org/systemdesign-ai-platform
cd systemdesign-ai-platform

# Frontend setup
cd frontend
npm install
npm run dev

# Backend setup  
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Environment variables
cp .env.example .env
# Configure Google ADK, database, and API keys
```

#### Production Deployment
```bash
# Vercel deployment
vercel --prod

# Health checks
curl https://your-app.vercel.app/health
curl https://your-app.vercel.app/api/health

# Monitoring
# Comet Opik dashboard: https://www.comet.com/your-workspace
```

### Success Criteria

#### Technical Metrics
- All 24 issues completed successfully
- >90% test coverage maintained
- Performance targets met
- Zero critical security vulnerabilities

#### User Experience Metrics
- Complete learning session flow functional
- Real-time whiteboard feedback working
- Progress analytics displaying correctly
- Assessment system providing valuable feedback

#### Business Metrics
- Platform ready for beta user testing
- Cost per session within target range
- Monitoring and observability operational
- Documentation complete and up-to-date

This project context provides comprehensive information for Claude Code to understand the complete system architecture, business requirements, and implementation approach. Use this context to guide implementation decisions and ensure all features align with the overall product vision.