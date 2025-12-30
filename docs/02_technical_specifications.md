# Part 2: Technical Specifications

## Table of Contents
1. [Data Models](#data-models)
2. [API Specification](#api-specification)
3. [Components](#components)
4. [External APIs](#external-apis)
5. [Core Workflows](#core-workflows)
6. [Database Schema](#database-schema)

---

## Data Models

### Backend Pydantic Models

All backend data validation and serialization uses Pydantic v2 models, located in [/backend/app/models/](./../../backend/app/models/).

#### **Chat Models** ([backend/app/models/chat.py](./../../backend/app/models/chat.py))

```python
# Request for chat endpoint
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    chapter_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}
    include_diagram: bool = False

    model_config = ConfigDict(str_strip_whitespace=True)

# Response from chat endpoint
class ChatResponse(BaseModel):
    message_id: str
    content: str
    role: Literal["user", "assistant"]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    artifacts: List[Artifact] = []
    streaming: bool = False
```

#### **Assessment Models** ([backend/app/models/assessment.py](./../../backend/app/models/assessment.py))

```python
# 6-dimensional assessment framework
class AssessmentDimension(str, Enum):
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    SYSTEM_ARCHITECTURE = "system_architecture"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    SCALE_PERFORMANCE = "scale_performance"
    RELIABILITY_FAULT_TOLERANCE = "reliability_fault_tolerance"
    COMMUNICATION_THOUGHT_PROCESS = "communication_thought_process"

# Individual dimension evaluation
class DimensionScore(BaseModel):
    dimension: AssessmentDimension
    score: float  # 1-5 scale
    max_score: int = 5
    feedback: str
    examples: List[str] = []
    suggestions: List[str] = []

# Comprehensive assessment response
class AssessmentResponse(BaseModel):
    assessment_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    dimension_scores: Dict[str, DimensionScore]
    overall_score: float
    confidence_score: float  # 0-1 scale
    detailed_feedback: str
    recommendations: List[str]
    comparison_to_previous: Optional[Dict[str, float]] = None
    cost_estimate: float
    tokens_used: Dict[str, int]
```

#### **Whiteboard Models** ([backend/app/models/whiteboard.py](./../../backend/app/models/whiteboard.py))

```python
# PNG upload request
class PNGUploadRequest(BaseModel):
    image_data: str  # base64 encoded PNG
    session_id: str
    description: Optional[str] = None

    @field_validator('image_data')
    @classmethod
    def validate_png(cls, v):
        # Validate PNG header and size
        if not v.startswith('iVBORw0KGgoAAAA'):  # PNG magic bytes
            raise ValueError("Invalid PNG file")
        if len(v) > 5_000_000:  # 5MB limit
            raise ValueError("File too large")
        return v

# PNG analysis request
class WhiteboardAnalysisRequest(BaseModel):
    artifact_id: str
    analysis_type: Literal["components", "feedback", "suggestions"] = "feedback"
    focus_areas: List[str] = []

# Analysis response with structured feedback
class WhiteboardAnalysisResponse(BaseModel):
    analysis_id: str
    artifact_id: str
    components_identified: List[str]
    architecture_patterns: List[str]
    feedback: Dict[str, str]
    suggestions: List[str]
    strengths: List[str]
    improvements_needed: List[str]
    cost_estimate: float
    model_used: str
```

#### **Diagram Models** ([backend/app/models/diagram.py](./../../backend/app/models/diagram.py))

```python
# Diagram type enumeration
class DiagramType(str, Enum):
    ARCHITECTURE = "architecture"
    SEQUENCE = "sequence"
    COMPONENT = "component"
    CLASS = "class"

# Diagram generation request
class DiagramGenerationRequest(BaseModel):
    title: str
    description: str
    diagram_type: DiagramType
    context: Dict[str, Any]
    session_id: Optional[str] = None
    style: Optional[str] = "default"

# Diagram generation response
class DiagramGenerationResponse(BaseModel):
    diagram_id: str
    mermaid_code: str
    png_base64: str
    title: str
    description: str
    diagram_type: DiagramType
    dimensions: Dict[str, int]  # width, height
    artifact_id: Optional[str] = None
    cost_estimate: float
```

#### **Progress Models** ([backend/app/models/progress.py](./../../backend/app/models/progress.py))

```python
# Progress statistics
class ProgressStatistics(BaseModel):
    total_sessions: int
    total_assessments: int
    average_score: float
    strongest_dimension: AssessmentDimension
    weakest_dimension: AssessmentDimension
    improvement_rate: float  # percent per week
    total_duration: int  # seconds

# Trend analysis
class TrendAnalysis(BaseModel):
    dimension: AssessmentDimension
    scores_over_time: List[Tuple[datetime, float]]
    trend_direction: Literal["improving", "declining", "stable"]
    confidence: float

# Personalized recommendations
class RecommendationsList(BaseModel):
    recommendations: List[str]
    priority_dimension: AssessmentDimension
    suggested_topics: List[str]
    estimated_improvement_time: int  # hours
```

#### **Session Models** ([backend/app/models/session.py](./../../backend/app/models/session.py))

```python
class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class LearningSession(BaseModel):
    session_id: str
    user_id: str
    chapter_id: str
    status: SessionStatus
    created_at: datetime
    last_updated: datetime
    total_duration_seconds: int
    message_count: int
    whiteboard_interactions: int
    assessments_count: int
    conversation_history: List[ChatMessage] = []
    session_state: Dict[str, Any] = {}
```

---

### Frontend TypeScript Interfaces

Key interfaces defined in [/frontend/types/](./../../frontend/types/) and component files.

#### **Message Interface**

```typescript
// ChatInterface.tsx
interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  type?: 'text' | 'voice' | 'image'
  metadata?: {
    topic?: string
    difficulty?: 'beginner' | 'intermediate' | 'advanced'
    assessment?: Record<string, number>
    artifacts?: Artifact[]
  }
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  sessionId: string
  chapterId?: string
  error?: Error
}
```

#### **Assessment Interface**

```typescript
// From API response models
interface DimensionScore {
  dimension: string
  score: number
  maxScore: number
  feedback: string
  examples: string[]
  suggestions: string[]
}

interface AssessmentResult {
  assessmentId: string
  dimensionScores: Record<string, DimensionScore>
  overallScore: number
  confidenceScore: number
  recommendations: string[]
  timestamp: Date
}
```

#### **Whiteboard Interface**

```typescript
// WhiteboardCanvas.tsx
interface DrawingState {
  isDrawing: boolean
  currentTool: 'pen' | 'eraser' | 'rectangle' | 'circle' | 'line'
  currentColor: string
  brushSize: number
  canvasHistory: ImageData[]
}

interface AnalysisResult {
  analysisId: string
  componentsIdentified: string[]
  architecturePatterns: string[]
  feedback: Record<string, string>
  suggestions: string[]
  strengths: string[]
  improvementsNeeded: string[]
}
```

---

## API Specification

### Overview

The backend exposes 30+ RESTful API endpoints organized into 8 routers. All endpoints return JSON responses with consistent error handling.

**Base URL**: `https://learn-with-ai.vercel.app/api` (production)

**Authentication**: Currently disabled (critical security gap)

**Rate Limiting**: 10 requests/minute per IP address

### Health & Status Endpoints

#### `GET /` - Root Endpoint

```
Description: Basic health check
Method: GET
Response Code: 200 OK

Response:
{
  "status": "ok",
  "timestamp": "2024-10-28T10:30:00Z",
  "version": "1.0.0"
}
```

#### `GET /health` - Simple Health Check

```
Description: Service health status
Method: GET
Response Code: 200 OK

Response:
{
  "status": "healthy",
  "service": "learn-with-ai-backend"
}
```

#### `GET /api/health` - Detailed Health Check

```
Description: Comprehensive system health with all services
Method: GET
Response Code: 200 OK

Response:
{
  "status": "healthy",
  "timestamp": "2024-10-28T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "gemini_api": "available",
    "openai_api": "available"
  },
  "metrics": {
    "uptime_seconds": 3600,
    "memory_usage_mb": 256
  }
}
```

### Chat Endpoints

#### `POST /api/chat` - Main Chat Endpoint

```
Description: Send message to AI tutor and receive streaming response
Method: POST
Rate Limit: 10 req/min
Authentication: Not required (disabled)

Request:
{
  "message": "How do I design a distributed cache?",
  "session_id": "session_123",
  "chapter_id": "chapter_5",
  "context": {
    "difficulty": "intermediate"
  },
  "include_diagram": true
}

Response (200 OK):
{
  "message_id": "msg_456",
  "content": "To design a distributed cache...",
  "role": "assistant",
  "timestamp": "2024-10-28T10:30:00Z",
  "metadata": {
    "topic": "distributed-systems",
    "tokens_used": {"input": 150, "output": 320}
  },
  "artifacts": [],
  "streaming": false
}

Error Responses:
- 400: Invalid message format
- 429: Rate limit exceeded
- 500: Internal server error
```

### Session Management Endpoints

#### `POST /api/session/create` - Create Learning Session

```
Description: Create new learning session
Method: POST

Request:
{
  "user_id": "user_123",
  "chapter_id": "chapter_5"
}

Response (201 Created):
{
  "session_id": "session_789",
  "user_id": "user_123",
  "chapter_id": "chapter_5",
  "status": "active",
  "created_at": "2024-10-28T10:30:00Z"
}
```

#### `GET /api/session/{user_id}` - Get All User Sessions

```
Description: Retrieve all learning sessions for a user
Method: GET
Parameters:
  - user_id (path): UUID of user

Response (200 OK):
{
  "sessions": [
    {
      "session_id": "session_789",
      "chapter_id": "chapter_5",
      "status": "active",
      "created_at": "2024-10-28T10:30:00Z",
      "message_count": 15,
      "total_duration_seconds": 1800
    }
  ],
  "total": 1
}
```

#### `GET /api/sessions/{user_id}/{session_id}` - Get Session Details

```
Description: Retrieve complete session details with conversation history
Method: GET
Parameters:
  - user_id (path): UUID of user
  - session_id (path): UUID of session

Response (200 OK):
{
  "session_id": "session_789",
  "user_id": "user_123",
  "chapter_id": "chapter_5",
  "status": "active",
  "created_at": "2024-10-28T10:30:00Z",
  "conversation_history": [
    {
      "role": "user",
      "content": "How do I...",
      "timestamp": "2024-10-28T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "You can...",
      "timestamp": "2024-10-28T10:30:30Z"
    }
  ],
  "session_state": {}
}
```

### Whiteboard Endpoints

#### `POST /api/whiteboard/upload` - Upload Whiteboard PNG

```
Description: Upload whiteboard drawing as PNG
Method: POST
Content-Type: application/json

Request:
{
  "image_data": "iVBORw0KGgoAAAA...",  // base64 PNG
  "session_id": "session_789",
  "description": "System design for user service"
}

Response (201 Created):
{
  "artifact_id": "artifact_234",
  "session_id": "session_789",
  "type": "whiteboard_png",
  "storage_url": "gs://bucket/artifacts/artifact_234.png",
  "size_bytes": 45000,
  "uploaded_at": "2024-10-28T10:30:00Z"
}

Error Responses:
- 400: Invalid PNG format or too large
- 413: Payload too large (>5MB)
```

#### `POST /api/whiteboard/analyze` - Analyze Whiteboard

```
Description: Use GPT-4V to analyze whiteboard PNG and provide feedback
Method: POST

Request:
{
  "artifact_id": "artifact_234",
  "analysis_type": "feedback",
  "focus_areas": ["scalability", "fault-tolerance"]
}

Response (200 OK):
{
  "analysis_id": "analysis_567",
  "artifact_id": "artifact_234",
  "components_identified": [
    "Load Balancer",
    "Cache Layer",
    "Database Shard"
  ],
  "architecture_patterns": [
    "Load Balancing",
    "Caching",
    "Database Sharding"
  ],
  "feedback": {
    "scalability": "Good use of sharding, but missing...",
    "reliability": "Add replication for fault tolerance"
  },
  "suggestions": [
    "Consider adding circuit breakers",
    "Implement distributed tracing"
  ],
  "cost_estimate": 0.015
}
```

### Assessment Endpoints

#### `POST /api/assessment/evaluate` - Evaluate Performance

```
Description: Request comprehensive 6-dimensional assessment
Method: POST

Request:
{
  "session_id": "session_789",
  "user_id": "user_123",
  "include_whiteboard": true,
  "include_conversation": true
}

Response (200 OK):
{
  "assessment_id": "assessment_890",
  "session_id": "session_789",
  "timestamp": "2024-10-28T10:30:00Z",
  "dimension_scores": {
    "requirements_analysis": {
      "dimension": "requirements_analysis",
      "score": 4.2,
      "max_score": 5,
      "feedback": "Clear understanding of requirements...",
      "suggestions": ["Ask more clarifying questions"]
    },
    "system_architecture": {
      "score": 3.8,
      "feedback": "...",
      "suggestions": ["Consider more patterns"]
    },
    // ... 4 more dimensions
  },
  "overall_score": 3.95,
  "confidence_score": 0.87,
  "recommendations": [
    "Work on scaling strategies",
    "Study failure recovery patterns"
  ]
}
```

#### `GET /api/assessment/history/{user_id}` - Assessment History

```
Description: Get all assessments for a user
Method: GET
Parameters:
  - user_id (path): UUID of user
  - limit (query): Max results (default 20)
  - offset (query): Results offset (default 0)

Response (200 OK):
{
  "assessments": [
    {
      "assessment_id": "assessment_890",
      "session_id": "session_789",
      "timestamp": "2024-10-28T10:30:00Z",
      "overall_score": 3.95,
      "dimension_scores": {...}
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/assessment/summary/{user_id}` - Assessment Summary

```
Description: Get aggregate assessment statistics
Method: GET
Parameters:
  - user_id (path): UUID of user

Response (200 OK):
{
  "total_assessments": 5,
  "average_score": 3.75,
  "strongest_dimension": "requirements_analysis",
  "weakest_dimension": "communication_thought_process",
  "improvement_rate": 0.15,  // 15% per week
  "trends": {
    "requirements_analysis": {
      "trend_direction": "improving",
      "scores_over_time": [
        ["2024-10-10T10:30:00Z", 3.2],
        ["2024-10-17T10:30:00Z", 3.8],
        ["2024-10-24T10:30:00Z", 4.2]
      ]
    }
  }
}
```

#### `GET /api/assessment/{assessment_id}` - Get Assessment Details

```
Description: Retrieve specific assessment with all details
Method: GET
Parameters:
  - assessment_id (path): UUID of assessment

Response (200 OK):
{
  "assessment_id": "assessment_890",
  "session_id": "session_789",
  "timestamp": "2024-10-28T10:30:00Z",
  "dimension_scores": {...},
  "overall_score": 3.95,
  "confidence_score": 0.87,
  "detailed_feedback": "Your requirements analysis was excellent...",
  "recommendations": [...]
}
```

#### `DELETE /api/assessment/{assessment_id}` - Delete Assessment

```
Description: Remove assessment from system
Method: DELETE
Parameters:
  - assessment_id (path): UUID of assessment

Response (204 No Content):
// No body

Error Responses:
- 404: Assessment not found
```

### Diagram Generation Endpoints

#### `POST /api/diagrams/generate` - Generate System Diagram

```
Description: Generate Mermaid diagram based on context
Method: POST

Request:
{
  "title": "User Service Architecture",
  "description": "Multi-region, fault-tolerant user service",
  "diagram_type": "architecture",
  "context": {
    "components": ["Load Balancer", "API Servers", "Database"],
    "patterns": ["Replication", "Sharding"],
    "constraints": ["Low latency", "High availability"]
  }
}

Response (200 OK):
{
  "diagram_id": "diagram_123",
  "mermaid_code": "graph TD\n  A[Load Balancer] --> B[API]\n  B --> C[DB]",
  "png_base64": "iVBORw0KGgoAAAA...",
  "title": "User Service Architecture",
  "dimensions": {
    "width": 800,
    "height": 600
  },
  "artifact_id": "artifact_567",
  "cost_estimate": 0.02
}
```

### Progress Tracking Endpoints

#### `GET /api/progress/statistics/{user_id}` - Progress Statistics

```
Description: Get learning progress statistics
Method: GET
Parameters:
  - user_id (path): UUID of user

Response (200 OK):
{
  "total_sessions": 12,
  "total_assessments": 8,
  "average_score": 3.75,
  "strongest_dimension": "requirements_analysis",
  "weakest_dimension": "communication",
  "improvement_rate": 0.15
}
```

#### `GET /api/progress/trends/{user_id}` - Progress Trends

```
Description: Get trend analysis for each dimension
Method: GET
Parameters:
  - user_id (path): UUID of user

Response (200 OK):
{
  "trends": {
    "requirements_analysis": {
      "trend_direction": "improving",
      "scores_over_time": [...],
      "confidence": 0.92
    }
  }
}
```

#### `GET /api/progress/recommendations/{user_id}` - Get Recommendations

```
Description: Get personalized learning recommendations
Method: GET
Parameters:
  - user_id (path): UUID of user

Response (200 OK):
{
  "recommendations": [
    "Focus on scaling strategies",
    "Study failure recovery patterns"
  ],
  "priority_dimension": "scale_performance",
  "suggested_topics": ["Database Scaling", "Caching", "CDN"],
  "estimated_improvement_time": 10
}
```

### Monitoring Endpoints

#### `GET /api/monitoring/metrics` - System Metrics

```
Description: Get current system performance metrics
Method: GET

Response (200 OK):
{
  "cpu_usage_percent": 35.2,
  "memory_usage_mb": 256,
  "active_requests": 5,
  "average_response_time_ms": 145,
  "error_rate_percent": 0.5,
  "timestamp": "2024-10-28T10:30:00Z"
}
```

### Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "message",
      "issue": "String too long"
    },
    "request_id": "req_123456",
    "timestamp": "2024-10-28T10:30:00Z"
  }
}
```

**Common Error Codes**:
- `VALIDATION_ERROR` (400) - Invalid input
- `RATE_LIMITED` (429) - Too many requests
- `NOT_FOUND` (404) - Resource not found
- `CONFLICT` (409) - Resource conflict
- `INTERNAL_ERROR` (500) - Server error

---

## Components

### Frontend React Components

All components located in [/frontend/components/](./../../frontend/components/).

#### **ChatInterface Component** (850 LOC)
[ChatInterface.tsx](./../../frontend/components/ChatInterface.tsx)

**Purpose**: Main chat interface for real-time conversation with AI tutor

**Key Features**:
- Real-time message streaming
- Markdown rendering with syntax highlighting
- Voice transcript integration
- Chapter-specific content suggestions
- Message history display
- Loading states and error handling
- Typing indicators

**Props**:
```typescript
interface ChatInterfaceProps {
  sessionId: string
  chapterId?: string
  onMessageSent?: (message: Message) => void
  onAssessmentRequest?: () => void
}
```

**State Management**:
- Local state: messages, currentInput, isLoading
- External API calls: `/api/chat` endpoint

**Performance Considerations**:
- Message virtualization for long conversations
- Debounced input handling
- Lazy-loaded markdown rendering

#### **WhiteboardCanvas Component** (845 LOC) ⚠️ Needs Refactoring

[WhiteboardCanvas.tsx](./../../frontend/components/WhiteboardCanvas.tsx)

**Purpose**: HTML5 Canvas drawing interface for system design sketches

**Key Features**:
- Freehand drawing with adjustable brush size
- Shape tools (rectangle, circle, line)
- Eraser tool
- Color picker
- Undo/redo history
- Clear canvas
- PNG export
- Grid overlay option

**Drawing Tools**:
```typescript
type DrawingTool = 'pen' | 'eraser' | 'rectangle' | 'circle' | 'line'
```

**State Management**:
- Canvas drawing state
- Tool and color selection
- History stack for undo/redo

**Performance Issues** ⚠️:
- 845 lines in single file (needs splitting)
- Memory leaks in event listeners
- No canvas optimization for large drawings
- Could be refactored into:
  - `<CanvasRenderer />` - Canvas rendering
  - `<DrawingToolbar />` - Tool selection
  - `<DrawingHistory />` - Undo/redo management

#### **VoiceInterface Component** (620 LOC)

[VoiceInterface.tsx](./../../frontend/components/VoiceInterface.tsx)

**Purpose**: Bidirectional audio streaming for voice conversations

**Key Features**:
- Microphone input capture
- Real-time transcription
- Audio response playback
- Voice activity detection
- Audio level visualization
- Recording controls
- Transcript history

**Status**: ⚠️ Implemented but not production-ready
- Requires LiveRequestQueue connection
- Currently disabled in frontend

#### **AssessmentPanel Component** (480 LOC)

[AssessmentPanel.tsx](./../../frontend/components/AssessmentPanel.tsx)

**Purpose**: Display comprehensive assessment results

**Key Features**:
- 6-dimensional score visualization
- Radar chart for score distribution
- Detailed feedback per dimension
- Comparison to previous assessments
- Progress timeline
- Actionable recommendations
- Export assessment button

**Visualization**:
- Radial/radar chart for dimension scores
- Color-coded scoring (red < 2, yellow 2-3, green > 3)
- Trend indicators (↑↓→)

#### **ProgressDashboard Component** (520 LOC)

[ProgressDashboard.tsx](./../../frontend/components/ProgressDashboard.tsx)

**Purpose**: Overall learning progress visualization

**Key Features**:
- Timeline of all assessments
- Trend charts per dimension
- Overall score progression
- Achievement badges
- Goal setting interface
- Export progress data
- Recommendation list

**Charts**:
- Line charts for score trends
- Bar charts for dimension comparison
- Area charts for overall progress

#### **LearnInterface Component**

[LearnInterface.tsx](./../../frontend/components/LearnInterface.tsx)

**Purpose**: Container component integrating all learning features

**Key Features**:
- Session management
- Layout orchestration
- Feature toggling
- State synchronization
- Error boundary
- Loading states

**Integrated Components**:
- ChatInterface
- WhiteboardCanvas
- AssessmentPanel
- ProgressDashboard
- VoiceInterface

### UI Components (Shadcn/Radix)

Reusable UI primitives from Shadcn UI collection:

- `<Button />` - Clickable button with variants
- `<Input />` - Text input field
- `<Textarea />` - Multi-line text input
- `<Card />` - Card container with sections
- `<Tabs />` - Tabbed interface
- `<Slider />` - Range slider
- `<ScrollArea />` - Scrollable container
- `<Separator />` - Divider line
- `<Avatar />` - User avatar display
- `<Badge />` - Label/tag component
- `<Dialog />` - Modal dialog
- `<Select />` - Dropdown selection
- `<Tooltip />` - Hover tooltips

All styled with Tailwind CSS utility classes.

---

## External APIs

### Google ADK (Agent Development Kit)

**Service**: [backend/app/services/adk_service.py](./../../backend/app/services/adk_service.py)

**Configuration**:
```python
ADK_MODEL = "gemini-2.0-flash-exp"
ADK_STREAMING_TIMEOUT = 30  # seconds
ADK_MAX_EVENTS = 100
ADK_CONNECTION_POOL = 10
```

**Key Integration Points**:

1. **LLM Configuration**
   - Model: Gemini 2.0 Flash
   - Streaming enabled for real-time responses
   - Automatic tool calling

2. **Tool Integration** (Custom ADK Tools)
   - Content Specialist Tool: Access learning content
   - Whiteboard Specialist Tool: Analyze drawings
   - Assessment Specialist Tool: Evaluate performance
   - Diagram Generator Tool: Create Mermaid diagrams

3. **Session Management**
   - InMemorySessionService for development
   - Session persistence with conversation history
   - State tracking per session

4. **Streaming**
   ```python
   async with runner.request(request) as response:
       async for event in response:
           # Process streaming events
           if event.server_content.model_update:
               # Model thinking/reasoning
           if event.server_content.turn_complete:
               # Complete response
   ```

**Cost Tracking**:
- Input tokens: ~$0.075/1M
- Output tokens: ~$0.30/1M
- Tracked via Comet Opik

### OpenAI API Integration

**Services**:
- Whiteboard Analysis: [backend/app/services/whiteboard_service.py](./../../backend/app/services/whiteboard_service.py)
- Assessment: [backend/app/services/assessment_service.py](./../../backend/app/services/assessment_service.py)

#### **Vision API (GPT-4o)**

**Purpose**: Multimodal analysis of whiteboard PNGs

**Configuration**:
```python
MULTIMODAL_MODEL = "gpt-4o"
VISION_API_MAX_TOKENS = 2000
```

**Request Example**:
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"}
                },
                {
                    "type": "text",
                    "text": "Analyze this system design diagram..."
                }
            ]
        }
    ],
    max_tokens=2000,
    temperature=0.7
)
```

**Cost**:
- Input: $0.005/1K tokens
- Image: $0.015 per image

#### **Assessment API (GPT-4 Turbo)**

**Purpose**: LLM judge for 6-dimensional assessment

**Configuration**:
```python
ASSESSMENT_MODEL = "gpt-4-1106-preview"
ASSESSMENT_MAX_TOKENS = 2000
```

**Evaluation Prompt Structure**:
```
You are an expert technical interviewer evaluating a system design interview response.

Evaluate the following dimensions on a 1-5 scale:
1. Requirements Analysis - Understanding of problem scope
2. System Architecture - Design of system components
3. Technical Deep Dive - Implementation details
4. Scale & Performance - Handling of scale and optimization
5. Reliability & Fault Tolerance - System robustness
6. Communication & Thought Process - Clarity of explanation

For each dimension, provide:
- Score (1-5)
- Detailed feedback
- Specific suggestions for improvement
```

**Cost**:
- Input: ~$0.01/1K tokens
- Output: ~$0.03/1K tokens

### Mermaid MCP Server

**Service**: [backend/app/services/diagram_service.py](./../../backend/app/services/diagram_service.py)

**Status**: ⚠️ Partially integrated

**Configuration**:
```python
MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=['-y', '@peng-shawn/mermaid-mcp-server']
        )
    ),
    tool_filter=['generate']
)
```

**Flow**:
1. Generate Mermaid code via Gemini
2. Render PNG via MCP server
3. Store as artifact
4. Return base64 to frontend

**Issues**:
- MCP connection sometimes unstable
- Resource cleanup incomplete
- Fallback to text-only needed

### Database Services

#### **PostgreSQL**

**Connection**: [backend/app/database/__init__.py](./../../backend/app/database/__init__.py)

**Configuration**:
```python
DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
pool_size = 10
max_overflow = 20
pool_pre_ping = True  # Verify connections before use
```

**Tables**:
- `users` - User accounts and preferences
- `learning_sessions` - Active/completed sessions
- `assessments` - Assessment results
- `artifacts` - Whiteboard PNGs and diagrams
- `conversation_history` - Message logs

#### **Redis**

**Purpose**: Caching, rate limiting, session storage

**Configuration**:
```python
REDIS_URL = "redis://localhost:6379"
REDIS_MAX_CONNECTIONS = 10
```

**Usage**:
- Rate limiting: Key = IP + endpoint
- Session cache: Key = session_id
- Message cache: Key = conversation_{session_id}

---

## Core Workflows

### 1. Chat Conversation Workflow

```mermaid
sequenceDiagram
    User->>Frontend: Send message
    Frontend->>API: POST /api/chat
    API->>ADKService: process_chat()
    ADKService->>ADK: InMemoryRunner.run()
    ADK->>Gemini: Stream completion request
    Gemini-->>ADK: Streaming tokens
    ADK->>ADK: Tool calling?
    opt Tool Calling
        ADK->>DiagramService: generate_diagram()
        DiagramService->>Gemini: Create Mermaid code
        DiagramService->>MCPServer: Render PNG
        MCPServer-->>DiagramService: PNG binary
    end
    ADK-->>ADKService: Completion event
    ADKService->>Opik: Track LLM call
    ADKService->>Frontend: Stream response
    Frontend->>User: Display message + artifacts

    Note over API,Gemini: Real-time streaming
```

**Latency Breakdown**:
- Request processing: 10-20ms
- Gemini first token: 500-800ms
- Streaming response: 1-3 seconds
- Diagram generation: +2-3 seconds

### 2. Whiteboard Analysis Workflow

```mermaid
sequenceDiagram
    User->>Canvas: Draw diagram
    User->>Frontend: Capture & analyze
    Frontend->>API: POST /api/whiteboard/upload
    API->>Storage: Save PNG artifact
    Frontend->>API: POST /api/whiteboard/analyze
    API->>WhiteboardService: analyze()
    WhiteboardService->>GPT4V: Vision analysis
    GPT4V-->>WhiteboardService: Structured feedback
    WhiteboardService->>Opik: Track vision call
    WhiteboardService->>Frontend: Return analysis
    Frontend->>User: Display feedback
```

**Component Detection**:
- Load balancers, caches, databases
- Replication and sharding patterns
- Message queues and microservices

**Analysis Time**: 1-2 seconds (including API latency)

### 3. Assessment Workflow

```mermaid
sequenceDiagram
    User->>Frontend: Request assessment
    Frontend->>API: POST /api/assessment/evaluate
    API->>AssessmentService: evaluate()
    AssessmentService->>AssessmentService: Gather context
    AssessmentService->>GPT4Turbo: LLM judge evaluation
    GPT4Turbo->>GPT4Turbo: Score 6 dimensions
    GPT4Turbo-->>AssessmentService: Scored response
    AssessmentService->>Database: Store assessment
    AssessmentService->>Opik: Track judge call
    AssessmentService->>Frontend: Return results
    Frontend->>User: Display assessment
```

**Context Gathered**:
1. Conversation history (last 10 messages)
2. Whiteboard drawings (if any)
3. System diagram (if generated)
4. Previous assessment scores
5. Chapter/topic context

**Scoring Logic**:
- Each dimension scored 1-5
- Confidence score based on clarity of answers
- Recommendations based on weakest dimensions

### 4. Progress Tracking Workflow

```mermaid
sequenceDiagram
    Frontend->>API: GET /api/assessment/history
    API->>Database: Query assessments
    Database-->>API: Assessment records
    API->>ProgressService: calculate_statistics()
    ProgressService->>ProgressService: Compute trends
    ProgressService-->>API: Statistics object
    API->>Frontend: Return progress data
    Frontend->>User: Render dashboard
```

**Calculations**:
- Average scores per dimension
- Improvement rate (linear regression)
- Trend direction (improving/declining/stable)
- Recommended focus areas

---

## Database Schema

### SQLAlchemy Models

All models located in [/backend/app/database/models.py](./../../backend/app/database/models.py)

#### **Users Table**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    skill_level VARCHAR(50),  -- beginner, intermediate, advanced
    preferences JSONB,  -- {theme, notifications, language}
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### **Learning Sessions Table**

```sql
CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chapter_id VARCHAR(100) NOT NULL,
    status VARCHAR(50),  -- active, paused, completed, archived
    conversation_history JSONB,  -- [{role, content, timestamp}, ...]
    session_state JSONB,  -- {current_topic, subtopic_progress, ...}
    total_duration_seconds INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    whiteboard_interactions INTEGER DEFAULT 0,
    assessment_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_sessions_user_id ON learning_sessions(user_id);
CREATE INDEX idx_sessions_chapter_id ON learning_sessions(chapter_id);
CREATE INDEX idx_sessions_status ON learning_sessions(status);
```

**conversation_history Schema**:
```json
[
  {
    "message_id": "msg_123",
    "role": "user",
    "content": "How do I...",
    "timestamp": "2024-10-28T10:30:00Z",
    "type": "text"
  },
  {
    "message_id": "msg_124",
    "role": "assistant",
    "content": "You can...",
    "timestamp": "2024-10-28T10:30:30Z",
    "type": "text",
    "artifacts": ["artifact_123"]
  }
]
```

#### **Assessments Table**

```sql
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES learning_sessions(id) ON DELETE CASCADE,
    dimension_scores JSONB NOT NULL,  -- {requirement_analysis: {score, feedback, ...}, ...}
    overall_score DECIMAL(3,2),  -- 1.0-5.0
    confidence_score DECIMAL(3,2),  -- 0.0-1.0
    detailed_feedback TEXT,
    recommendations JSONB,  -- [recommendation_1, recommendation_2, ...]
    cost_estimate DECIMAL(10,6),
    tokens_used JSONB,  -- {input: 150, output: 320}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_assessments_user_id ON assessments(user_id);
CREATE INDEX idx_assessments_session_id ON assessments(session_id);
CREATE INDEX idx_assessments_created_at ON assessments(created_at);
```

**dimension_scores Schema**:
```json
{
  "requirements_analysis": {
    "score": 4.2,
    "max_score": 5,
    "feedback": "Clear understanding of requirements...",
    "examples": ["Good question about scale", "..."],
    "suggestions": ["Ask about edge cases"]
  },
  "system_architecture": {
    "score": 3.8,
    "feedback": "...",
    "examples": ["..."],
    "suggestions": ["..."]
  },
  // ... 4 more dimensions
}
```

#### **Artifacts Table**

```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES learning_sessions(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- whiteboard_png, diagram_mermaid, etc.
    storage_url VARCHAR(500),
    metadata JSONB,  -- {width, height, color_palette, ...}
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_artifacts_session_id ON artifacts(session_id);
CREATE INDEX idx_artifacts_type ON artifacts(type);
CREATE INDEX idx_artifacts_created_at ON artifacts(created_at);
```

### Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ LEARNING_SESSIONS : has
    USERS ||--o{ ASSESSMENTS : creates
    LEARNING_SESSIONS ||--o{ ASSESSMENTS : produces
    LEARNING_SESSIONS ||--o{ ARTIFACTS : contains

    USERS {
        uuid id
        string email
        string name
        string skill_level
        jsonb preferences
        timestamp created_at
    }

    LEARNING_SESSIONS {
        uuid id
        uuid user_id
        string chapter_id
        string status
        jsonb conversation_history
        jsonb session_state
        int total_duration_seconds
        int message_count
        timestamp created_at
    }

    ASSESSMENTS {
        uuid id
        uuid user_id
        uuid session_id
        jsonb dimension_scores
        decimal overall_score
        decimal confidence_score
        text detailed_feedback
        timestamp created_at
    }

    ARTIFACTS {
        uuid id
        uuid session_id
        string type
        string storage_url
        jsonb metadata
        timestamp created_at
    }
```

### Database Constraints & Indexes

**Primary Keys**:
- All tables use UUID primary keys (gen_random_uuid())

**Foreign Keys**:
- learning_sessions.user_id → users.id (CASCADE delete)
- assessments.user_id → users.id (CASCADE delete)
- assessments.session_id → learning_sessions.id (CASCADE delete)
- artifacts.session_id → learning_sessions.id (CASCADE delete)

**Indexes** (for query performance):
- users(email) - Fast email lookup
- learning_sessions(user_id) - User's sessions
- learning_sessions(status) - Active sessions
- assessments(user_id, created_at) - User assessment history
- assessments(session_id) - Session assessments
- artifacts(session_id, type) - Session artifacts

**Partitioning** (recommended for scale):
```sql
-- Partition assessments by created_at (monthly)
CREATE TABLE assessments_2024_10 PARTITION OF assessments
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');
```

### Data Retention & Archiving

**Current Policy**:
- Active sessions: No limit
- Completed sessions: Archived after 90 days
- Assessments: Permanently stored
- Artifacts: Deleted with session

**Recommended Policy**:
- Soft delete with deleted_at timestamp
- Archive old sessions to separate storage
- Export assessments before deletion
- Implement GDPR compliance

---

## Summary

This technical specification provides:

1. ✅ **Data Models** - All Pydantic models with validation
2. ✅ **API Specification** - 30+ endpoints with examples
3. ✅ **Components** - React component architecture
4. ✅ **External APIs** - Google ADK, OpenAI, Mermaid MCP
5. ✅ **Core Workflows** - Chat, whiteboard, assessment, progress
6. ✅ **Database Schema** - Complete SQLAlchemy models

**Next Steps**: See [Part 3 - Architecture Deep Dive](./03_architecture_deep_dive.md) for detailed system implementation patterns.

