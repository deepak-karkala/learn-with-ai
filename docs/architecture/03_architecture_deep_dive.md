# Part 3: Architecture Deep Dive

## Table of Contents
1. [Frontend Architecture](#frontend-architecture)
2. [Backend Architecture](#backend-architecture)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)

---

## Frontend Architecture

### NextJS 14 Architecture Overview

The frontend uses NextJS 14 with the App Router pattern, TypeScript strict mode, and Tailwind CSS for styling.

#### **App Structure**

```
/frontend/
├── app/                          # NextJS App Router
│   ├── page.tsx                 # Landing page (/)
│   ├── layout.tsx               # Root layout
│   ├── chat/
│   │   ├── page.tsx            # Chat interface (/chat)
│   │   └── layout.tsx          # Chat-specific layout
│   ├── chapters/
│   │   ├── page.tsx            # Chapter selection (/chapters)
│   │   ├── [id]/
│   │   │   └── page.tsx        # Individual chapter (/chapters/[id])
│   │   └── layout.tsx          # Chapter layout
│   ├── progress/
│   │   ├── page.tsx            # Progress dashboard (/progress)
│   │   └── layout.tsx          # Progress layout
│   ├── dev/
│   │   └── page.tsx            # Development utilities (/dev)
│   └── api/                     # API routes (if any)
│
├── components/                   # React components (~5,500 LOC)
│   ├── LearnInterface.tsx        # Main container
│   ├── ChatInterface.tsx         # Chat (850 LOC)
│   ├── WhiteboardCanvas.tsx      # Whiteboard (845 LOC) ⚠️
│   ├── VoiceInterface.tsx        # Voice (620 LOC)
│   ├── AssessmentPanel.tsx       # Assessment (480 LOC)
│   ├── ProgressDashboard.tsx     # Progress (520 LOC)
│   └── ui/                      # Shadcn UI components
│       ├── button.tsx
│       ├── input.tsx
│       ├── card.tsx
│       └── ... (12+ UI components)
│
├── hooks/                        # Custom React hooks
│   ├── useChat.ts              # Chat state hook
│   ├── useWhiteboard.ts        # Whiteboard state
│   ├── useAssessment.ts        # Assessment state
│   ├── useProgress.ts          # Progress state
│   └── useSession.ts           # Session management
│
├── utils/                        # Utility functions
│   ├── api.ts                  # API client
│   ├── formatting.ts           # Text/date formatting
│   ├── canvas.ts               # Canvas utilities
│   └── validation.ts           # Input validation
│
├── types/                        # TypeScript interfaces
│   ├── chat.ts
│   ├── assessment.ts
│   ├── whiteboard.ts
│   ├── progress.ts
│   └── index.ts                # Central type exports
│
├── public/                       # Static assets
│   ├── images/
│   ├── icons/
│   └── ...
│
├── styles/                       # Global styles
│   ├── globals.css             # Global Tailwind CSS
│   └── ...
│
├── next.config.ts              # NextJS configuration
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.ts          # Tailwind CSS configuration
├── package.json                # Dependencies
└── .env.local                  # Local environment variables
```

### State Management Architecture

**Pattern**: Combination of React hooks + API client (no Redux/Zustand)

```typescript
// hooks/useChat.ts
export function useChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: content, session_id: sessionId })
      })
      // Handle response...
    } catch (err) {
      setError(err as Error)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  return { messages, isLoading, error, sendMessage }
}
```

**Advantages**:
- ✅ Minimal bundle size
- ✅ No extra dependencies
- ✅ Direct API integration
- ✅ Server-side state possible with NextJS

**Disadvantages**:
- ⚠️ State prop-drilling for deeply nested components
- ⚠️ No built-in dev tools
- ⚠️ Prop drilling for shared state

### Component Communication Pattern

```mermaid
graph TB
    Page["Page Component<br/>/chat/page.tsx"]
    LearnInterface["LearnInterface<br/>(Container)"]
    ChatInterface["ChatInterface"]
    Whiteboard["WhiteboardCanvas"]
    Assessment["AssessmentPanel"]
    Progress["ProgressDashboard"]

    Page -->|Props| LearnInterface
    LearnInterface -->|Props| ChatInterface
    LearnInterface -->|Props| Whiteboard
    LearnInterface -->|Props| Assessment
    LearnInterface -->|Props| Progress

    ChatInterface -.->|Callback| LearnInterface
    Whiteboard -.->|Callback| LearnInterface
    Assessment -.->|Callback| LearnInterface
    Progress -.->|Callback| LearnInterface
```

### Data Flow: Props + Callbacks

```typescript
// Page passes session context
<LearnInterface sessionId={sessionId} chapterId={chapterId} />

// LearnInterface distributes to children
<ChatInterface
  sessionId={sessionId}
  onMessageSent={handleMessageSent}
  onAssessmentRequest={handleAssessmentRequest}
/>

// Child components call callbacks to update parent state
const handleSendMessage = useCallback((message: Message) => {
  setMessages([...messages, message])
}, [messages])
```

### Routing & Navigation

**NextJS App Router Benefits**:
- ✅ File-based routing (simpler than Remix)
- ✅ Nested routing with shared layouts
- ✅ Dynamic routes with [id] pattern
- ✅ Built-in code splitting

**Route Structure**:
```
/                    → Landing page
/chat                → Chat learning interface
/chapters            → Chapter selection
/chapters/[id]       → Individual chapter
/progress            → Progress dashboard
/dev                 → Development utilities
```

**Navigation Implementation**:
```typescript
import { useRouter } from 'next/navigation'

// In component
const router = useRouter()
router.push('/chat')  // Navigate to chat
router.back()         // Go back
```

### Styling Architecture

**Tech Stack**: Tailwind CSS + Shadcn UI

**Configuration** ([tailwind.config.ts](./../../frontend/tailwind.config.ts)):
```typescript
export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors
      },
      spacing: {
        // Custom spacing
      }
    }
  },
  plugins: []
}
```

**Utility-First Approach**:
```jsx
// Instead of writing CSS, compose Tailwind classes
<div className="flex gap-4 p-4 bg-white rounded-lg shadow-md">
  <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
    Click me
  </button>
</div>
```

**Component Styling** (Shadcn UI):
```jsx
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

// Pre-styled components with variants
<Button variant="destructive" size="lg" />
<Card className="p-6">Content</Card>
```

**Responsive Design**:
```jsx
// Mobile-first responsive utilities
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <Card key={item.id}>{item}</Card>)}
</div>
```

### API Client Integration

**API Client** ([frontend/utils/api.ts](./../../frontend/utils/api.ts)):
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api'

export const apiClient = {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    })
    if (!response.ok) throw new Error('Chat failed')
    return response.json()
  },

  async uploadWhiteboard(image: string, sessionId: string) {
    const response = await fetch(`${API_BASE}/whiteboard/upload`, {
      method: 'POST',
      body: JSON.stringify({ image_data: image, session_id: sessionId })
    })
    return response.json()
  },

  // ... other endpoints
}
```

**Error Handling**:
```typescript
try {
  const result = await apiClient.chat(request)
} catch (error) {
  console.error('API Error:', error)
  // Display user-friendly error
  setError(getErrorMessage(error))
}
```

### Performance Optimization

**Code Splitting**:
- NextJS auto-splits code per route
- Dynamic imports for heavy components:
```typescript
const WhiteboardCanvas = dynamic(
  () => import('./WhiteboardCanvas'),
  { loading: () => <Skeleton /> }
)
```

**Image Optimization**:
```jsx
import Image from 'next/image'

<Image
  src="/diagram.png"
  alt="Architecture"
  width={800}
  height={600}
  priority // For above-fold images
/>
```

**Lazy Loading**:
```typescript
// Lazy load assessment panel
const AssessmentPanel = lazy(() => import('./AssessmentPanel'))

<Suspense fallback={<LoadingSpinner />}>
  <AssessmentPanel />
</Suspense>
```

---

## Backend Architecture

### FastAPI Architecture Overview

The backend uses FastAPI with async/await, SQLAlchemy ORM, and layered service architecture.

#### **Layered Architecture**

```mermaid
graph TB
    Client["API Clients<br/>(Frontend, Mobile)"]

    subgraph API["API Layer"]
        Routes["FastAPI Routes<br/>(app/api/*.py)"]
        Middleware["Middleware Stack<br/>(Security, Monitoring)"]
    end

    subgraph Services["Service Layer"]
        ChatSvc["Chat Service<br/>(ADK Integration)"]
        WBSvc["Whiteboard Service<br/>(Vision Analysis)"]
        AssessSvc["Assessment Service<br/>(LLM Judge)"]
        ProgressSvc["Progress Service<br/>(Analytics)"]
        DiagramSvc["Diagram Service<br/>(Mermaid MCP)"]
        MonitorSvc["Monitoring Service<br/>(Observability)"]
    end

    subgraph Data["Data Layer"]
        Database["PostgreSQL<br/>(Sessions, Assessments)"]
        Cache["Redis<br/>(Caching, Rate Limits)"]
    end

    subgraph External["External APIs"]
        Gemini["Gemini API<br/>(via ADK)"]
        GPT["OpenAI API<br/>(Vision, Judge)"]
        Opik["Comet Opik<br/>(Monitoring)"]
    end

    Client -->|HTTP| Middleware
    Middleware -->|Route| Routes
    Routes -->|Call| Services
    Services -->|Query| Data
    Services -->|Track| Opik
    Services -->|API Call| Gemini
    Services -->|API Call| GPT
```

### Backend Directory Structure

```
/backend/
├── app/
│   ├── main.py                      # FastAPI app initialization (180 LOC)
│   │
│   ├── api/                         # Route handlers (8 routers)
│   │   ├── chat.py                 # POST /api/chat
│   │   ├── sessions.py             # Session management routes
│   │   ├── assessment.py           # Assessment endpoints
│   │   ├── whiteboard.py           # Whiteboard upload/analyze
│   │   ├── diagrams.py             # Diagram generation
│   │   ├── progress.py             # Progress tracking
│   │   ├── voice.py                # Voice interface (WIP)
│   │   ├── monitoring.py           # Monitoring endpoints
│   │   ├── content.py              # Content management
│   │   ├── auth.py                 # Authentication (disabled)
│   │   ├── performance.py          # Performance metrics
│   │   └── __init__.py             # Router initialization
│   │
│   ├── services/                    # Business logic (17,761 LOC total)
│   │   ├── adk_service.py          # ADK agent orchestration (450 LOC)
│   │   ├── whiteboard_service.py   # Vision analysis (380 LOC)
│   │   ├── assessment_service.py   # LLM judge (420 LOC)
│   │   ├── progress_service.py     # Analytics & trends (350 LOC)
│   │   ├── diagram_service.py      # Mermaid generation (300 LOC)
│   │   ├── session_service.py      # Session management (280 LOC)
│   │   ├── monitoring_service.py   # Metrics & monitoring (320 LOC)
│   │   ├── logging_service.py      # Structured logging (180 LOC)
│   │   ├── analytics_service.py    # User analytics (250 LOC)
│   │   ├── alerting_service.py     # Alert management (180 LOC)
│   │   ├── security_service.py     # Security validation (220 LOC)
│   │   └── cache_service.py        # Redis caching (200 LOC)
│   │
│   ├── models/                      # Pydantic validation models
│   │   ├── chat.py                 # Chat request/response
│   │   ├── assessment.py           # Assessment models
│   │   ├── whiteboard.py           # Whiteboard models
│   │   ├── progress.py             # Progress models
│   │   ├── diagram.py              # Diagram models
│   │   ├── session.py              # Session models
│   │   ├── common.py               # Shared models
│   │   └── __init__.py
│   │
│   ├── database/                    # Data access layer
│   │   ├── __init__.py             # Database setup
│   │   ├── models.py               # SQLAlchemy models (200 LOC)
│   │   ├── migrations/             # Alembic migrations (prepared)
│   │   └── seeds.py                # Database seeds
│   │
│   ├── middleware/                  # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── security.py             # Security headers (100 LOC)
│   │   ├── performance.py          # Request timing (120 LOC)
│   │   ├── monitoring.py           # Opik integration (90 LOC)
│   │   └── rate_limit.py           # Rate limiting (140 LOC)
│   │
│   ├── tools/                       # ADK custom tools
│   │   ├── __init__.py
│   │   ├── content_tool.py         # Course content access
│   │   ├── whiteboard_tool.py      # Whiteboard analysis
│   │   ├── assessment_tool.py      # Performance evaluation
│   │   └── diagram_tool.py         # Diagram generation
│   │
│   └── callbacks/                   # ADK callbacks
│       ├── __init__.py
│       ├── state_callback.py       # State tracking
│       └── event_callback.py       # Event handling
│
├── tests/                           # Test suite (270+ tests)
│   ├── test_main.py                # API tests
│   ├── test_adk_service.py
│   ├── test_assessment.py
│   ├── test_whiteboard.py
│   ├── test_diagrams.py
│   ├── test_progress_service.py
│   ├── test_voice_api.py
│   ├── test_load_performance.py
│   ├── test_session_persistence.py
│   ├── security/
│   │   ├── test_auth_service.py
│   │   ├── test_security_service.py
│   │   ├── test_security_integration.py
│   │   └── test_security_config.py
│   └── conftest.py                 # Pytest fixtures
│
├── scripts/
│   ├── test_dashboard.py           # Test reporting
│   ├── load_test.py                # Load testing
│   └── health_check.py             # Health monitoring
│
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── vercel.json                      # Vercel deployment
├── pytest.ini                       # Pytest configuration
└── .env.example                     # Environment template
```

### FastAPI Application Initialization

**[app/main.py](./../../backend/app/main.py)** (180 LOC)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.monitoring import MonitoringMiddleware
from app.api import (
    chat, sessions, assessment, whiteboard,
    diagrams, progress, voice, monitoring
)

# Initialize FastAPI app
app = FastAPI(
    title="Learn With AI Backend",
    description="AI-powered system design learning platform",
    version="1.0.0"
)

# Middleware stack (order matters)
# 1. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://learn-with-ai.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 3. Performance tracking
app.add_middleware(PerformanceMiddleware)

# 4. Monitoring (Opik integration)
app.add_middleware(MonitoringMiddleware)

# 5. Rate limiting
app.add_middleware(RateLimitMiddleware, rate_limit=10, window_seconds=60)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(assessment.router, prefix="/api", tags=["assessment"])
app.include_router(whiteboard.router, prefix="/api", tags=["whiteboard"])
app.include_router(diagrams.router, prefix="/api", tags=["diagrams"])
app.include_router(progress.router, prefix="/api", tags=["progress"])
app.include_router(voice.router, prefix="/api", tags=["voice"])
app.include_router(monitoring.router, prefix="/api", tags=["monitoring"])

# Health checks
@app.get("/")
async def root():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/health")
async def api_health():
    # Check all services
    return {
        "status": "healthy",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "gemini_api": "available",
            "openai_api": "available"
        }
    }
```

### Middleware Stack

**Order & Purpose**:

1. **SecurityHeadersMiddleware** - Add security headers
   ```python
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   X-XSS-Protection: 1; mode=block
   ```

2. **CORSMiddleware** - Handle cross-origin requests
   - Allow frontend origin only
   - Allow credentials
   - Allow all methods

3. **PerformanceMiddleware** - Track request timing
   - Request processing time
   - Database query time
   - External API latency

4. **MonitoringMiddleware** - Opik integration
   - Track all requests
   - Monitor error rates
   - Cost tracking

5. **RateLimitMiddleware** - Rate limiting
   - 10 requests/min per IP
   - Redis-backed (production)
   - In-memory (development)

### Service Layer Architecture

**ADK Service** ([services/adk_service.py](./../../backend/app/services/adk_service.py)) - 450 LOC

```python
class ADKService:
    """Google ADK agent orchestration for conversation"""

    def __init__(self):
        self.client = adk.Client(api_key=settings.GOOGLE_API_KEY)
        self.runner = adk.InMemoryRunner()
        self.session_service = SessionService()

    async def chat(
        self,
        message: str,
        session_id: str,
        context: dict = None
    ) -> ChatResponse:
        """Process chat message via ADK agent"""

        # Prepare request
        session = await self.session_service.get_or_create(session_id)

        # Build ADK request with conversation history
        request = adk.Request(
            text=message,
            system_instruction="You are an expert system design tutor...",
            history=session.conversation_history,
            tools=[
                self._create_content_tool(),
                self._create_whiteboard_tool(),
                self._create_assessment_tool(),
                self._create_diagram_tool()
            ]
        )

        # Stream response
        response_text = ""
        artifacts = []

        async with self.runner.request(request) as stream:
            async for event in stream:
                if event.server_content.model_update:
                    # Streaming text update
                    response_text += event.text

                if event.server_content.tool_call:
                    # Handle tool calling
                    artifacts.extend(await self._handle_tool_call(event))

                if event.server_content.turn_complete:
                    break

        # Track in monitoring
        await self._track_call(message, response_text)

        # Save to session
        await self.session_service.add_message(
            session_id, "assistant", response_text
        )

        return ChatResponse(
            message_id=str(uuid4()),
            content=response_text,
            role="assistant",
            artifacts=artifacts
        )
```

**Whiteboard Service** ([services/whiteboard_service.py](./../../backend/app/services/whiteboard_service.py)) - 380 LOC

```python
class WhiteboardService:
    """Multimodal analysis of whiteboard drawings"""

    async def analyze(
        self,
        artifact_id: str,
        analysis_type: str = "feedback"
    ) -> WhiteboardAnalysisResponse:
        """Analyze PNG using GPT-4V"""

        # Load artifact
        artifact = await self._load_artifact(artifact_id)

        # Prepare vision request
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{artifact.image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": self._get_analysis_prompt(analysis_type)
                        }
                    ]
                }
            ],
            max_tokens=2000
        )

        # Parse structured response
        analysis = self._parse_response(response.choices[0].message.content)

        # Track cost
        await self._track_vision_cost(response)

        return analysis

    def _get_analysis_prompt(self, analysis_type: str) -> str:
        """Get analysis prompt based on type"""
        if analysis_type == "feedback":
            return """Analyze this system design diagram and provide:
            1. Identified components
            2. Architecture patterns
            3. Feedback on design
            4. Suggestions for improvement

            Return as JSON."""
```

**Assessment Service** ([services/assessment_service.py](./../../backend/app/services/assessment_service.py)) - 420 LOC

```python
class AssessmentService:
    """6-dimensional LLM-based assessment"""

    async def evaluate(
        self,
        session_id: str,
        user_id: str
    ) -> AssessmentResponse:
        """Comprehensive 6-dimensional evaluation"""

        # Gather context
        session = await self._get_session(session_id)
        context = await self._build_assessment_context(session)

        # Create evaluation prompt
        prompt = self._create_evaluation_prompt(context)

        # Call LLM judge
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-1106-preview",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )

        # Parse dimension scores
        scores = self._parse_dimension_scores(
            response.choices[0].message.content
        )

        # Calculate overall score
        overall = sum(s.score for s in scores.values()) / len(scores)
        confidence = self._calculate_confidence(scores)

        # Generate recommendations
        recommendations = self._generate_recommendations(scores)

        # Store assessment
        assessment = await self._save_assessment({
            "session_id": session_id,
            "user_id": user_id,
            "dimension_scores": scores,
            "overall_score": overall,
            "confidence_score": confidence,
            "recommendations": recommendations
        })

        # Track cost
        await self._track_judge_cost(response)

        return AssessmentResponse(
            assessment_id=assessment.id,
            dimension_scores=scores,
            overall_score=overall,
            confidence_score=confidence,
            recommendations=recommendations
        )

    def _create_evaluation_prompt(self, context: dict) -> str:
        """Create rubric-based evaluation prompt"""
        return f"""
        You are an expert technical interviewer.

        Evaluate this system design response on 6 dimensions:
        1. Requirements Analysis (understanding of problem scope)
        2. System Architecture (design of components)
        3. Technical Deep Dive (implementation details)
        4. Scale & Performance (handling of scale)
        5. Reliability & Fault Tolerance (robustness)
        6. Communication & Thought Process (clarity)

        Conversation:
        {context['conversation']}

        Whiteboard (if any):
        {context['whiteboard_description']}

        For each dimension:
        - Score 1-5
        - Specific feedback
        - Suggestions for improvement

        Return as JSON.
        """
```

### Asynchronous Processing

**Async/Await Pattern**:

```python
# FastAPI routes use async
@router.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Async endpoint for chat"""

    # Async service calls
    response = await adk_service.chat(
        message=request.message,
        session_id=request.session_id
    )

    # Async database operations
    await db.sessions.save(session_id, response)

    return response
```

**Benefits**:
- ✅ Non-blocking I/O
- ✅ Handle many concurrent requests
- ✅ Better resource utilization
- ✅ Natural streaming support

### Error Handling Strategy

**Layered Error Handling**:

```python
# 1. Request validation (Pydantic)
@router.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # Pydantic validates request automatically
    # Returns 422 if invalid
    pass

# 2. Service-level error handling
async def chat(self, request: ChatRequest):
    try:
        result = await self.adk_service.process(request)
        return result
    except OpenAIError as e:
        logger.error(f"OpenAI error: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

# 3. Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id")
            }
        }
    )
```

### Connection Management

**Database Connections**:
```python
# Connection pooling
DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Session management
async def get_db_session():
    async with AsyncSession(engine) as session:
        yield session
```

**Redis Connections**:
```python
# Redis connection pool
redis_client = redis.from_url(
    "redis://localhost:6379",
    max_connections=10,
    decode_responses=True
)
```

---

## Project Structure

### Directory Layout Philosophy

**Principle**: Separation of concerns with clear layer boundaries

```
📦 learn-with-ai (Monorepo)
├── 📁 frontend/           # NextJS 14 application (~5,870 LOC)
├── 📁 backend/            # FastAPI + Google ADK (~17,761 LOC)
├── 📁 content/            # Learning content
├── 📁 tests/              # E2E test suite
├── 📁 docs/               # Documentation
├── 📁 deployment/         # Deployment configs
└── 📁 .github/            # GitHub workflows
    └── workflows/
        ├── ci.yml         # Fast PR checks
        ├── feature-ci.yml # Feature branch testing
        └── ... (13 more)
```

### Frontend Organization

**Principle**: Atomic component design with hooks

```
components/
├── LearnInterface.tsx      # Container
├── ChatInterface.tsx       # Feature component
├── WhiteboardCanvas.tsx    # Feature component
├── AssessmentPanel.tsx     # Feature component
├── ProgressDashboard.tsx   # Feature component
└── ui/                     # Atoms
    ├── button.tsx
    ├── input.tsx
    ├── card.tsx
    └── ... (12+)

hooks/
├── useChat.ts             # Chat state hook
├── useSession.ts          # Session management
└── ... (custom hooks)

types/
├── chat.ts
├── assessment.ts
├── whiteboard.ts
└── index.ts               # Central exports
```

**Component Size Distribution**:
- LearnInterface: 120 LOC (small)
- ChatInterface: 850 LOC (medium) ✅
- WhiteboardCanvas: 845 LOC (large) ⚠️ Refactor
- AssessmentPanel: 480 LOC (medium) ✅
- ProgressDashboard: 520 LOC (medium) ✅
- UI components: 50-150 LOC each ✅

### Backend Organization

**Principle**: Layered architecture with clear data flow

```
api/                       # Request handlers
├── chat.py              # Route → Service
├── assessment.py        # Validation + Service call
└── ...

services/                  # Business logic
├── adk_service.py       # Orchestration
├── assessment_service.py # Domain logic
└── ...

models/                    # Pydantic validation
├── chat.py              # Request/Response models
├── assessment.py        # Validation schemas
└── ...

database/                  # Data access
├── models.py            # SQLAlchemy ORM
├── __init__.py          # Connection setup
└── migrations/          # Alembic migrations
```

**Data Flow**:
```
Request → Route Handler (api/chat.py)
  ↓
Validation (models/chat.py - Pydantic)
  ↓
Service Layer (services/adk_service.py)
  ↓
Database/External APIs (database/ + API clients)
  ↓
Response
```

### Configuration Management

**Environment-Based Configuration**:

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Google APIs
    GOOGLE_API_KEY: str
    GOOGLE_CLOUD_PROJECT: str

    # OpenAI
    OPENAI_API_KEY: str
    MULTIMODAL_MODEL: str = "gpt-4o"
    ASSESSMENT_MODEL: str = "gpt-4-1106-preview"

    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Monitoring
    OPIK_API_KEY: str
    OPIK_PROJECT_NAME: str = "systemdesign-ai"

    # Security
    JWT_SECRET: str
    ENCRYPTION_KEY: str

    # Deployment
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Usage in Services**:
```python
from app.config import settings

client = adk.Client(api_key=settings.GOOGLE_API_KEY)
```

---

## Development Workflow

### Local Development Setup

**Prerequisites**:
- Node.js 18+ (frontend)
- Python 3.11+ (backend)
- PostgreSQL (optional, in-memory by default)
- Redis (optional, in-memory by default)

**Frontend Setup**:
```bash
cd frontend
npm install
npm run dev      # Start dev server at localhost:3000
npm test         # Run unit tests
npm run test:e2e # Run E2E tests
```

**Backend Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload  # Start at localhost:8000
pytest                                    # Run tests
```

**Full Stack**:
```bash
npm run dev:all  # Starts both frontend and backend
```

### Testing Strategy

**Test Organization** (270+ tests):

```
Backend Tests:
├── Unit Tests (160+)
│   ├── test_adk_service.py
│   ├── test_assessment.py
│   ├── test_whiteboard.py
│   └── ... (service unit tests)
│
├── Integration Tests (70+)
│   ├── test_assessment_e2e.py
│   ├── test_adk_session_integration.py
│   └── ... (service integration tests)
│
├── Security Tests (20+)
│   ├── test_auth_service.py
│   ├── test_security_service.py
│   └── test_security_integration.py
│
└── Performance Tests (20+)
    ├── test_load_performance.py
    └── test_regression_critical_paths.py

Frontend Tests:
├── Unit Tests (40+)
│   └── __tests__/*.test.tsx
│
└── E2E Tests (20+)
    └── tests-e2e/*.spec.ts (Playwright)
```

**Running Tests**:
```bash
# Backend - All tests
cd backend && pytest --cov=app --cov-report=html

# Backend - Specific suite
pytest tests/test_assessment.py        # Single file
pytest tests/ -k "assessment"          # By keyword
pytest tests/security/                 # By directory

# Frontend - Unit tests
cd frontend && npm test

# Frontend - E2E tests
npm run test:e2e

# Full suite with report
python run_comprehensive_tests.py --generate-report
```

**Test Dashboard**:
```bash
cd backend
python scripts/test_dashboard.py
# Opens HTML dashboard at localhost:8000/dashboard
```

### Code Quality Tools

**Linting & Formatting**:

**Backend**:
```bash
# Check style
flake8 app/ tests/

# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/ --strict
```

**Frontend**:
```bash
# Linting
npx eslint src/ --fix

# Formatting
npx prettier --write src/
```

**Pre-commit Hooks** (recommended):
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Runs on every commit:
# - Black formatting
# - Flake8 linting
# - isort import sorting
# - mypy type checking
```

### Version Control Workflow

**Branch Strategy**: GitFlow

```
main (production)
├── develop (staging)
│   └── feature/issue-[number]-[description]
│       └── Merge → develop → main
```

**Commit Messages** (Conventional Commits):

```
feat: add whiteboard canvas component

The component provides drawing tools including
pen, eraser, and shape tools with undo/redo.

Fixes #45

fix: resolve memory leaks in canvas listeners

Remove event listeners on component unmount
to prevent memory leaks in long-running sessions.

docs: update architecture documentation

Add detailed backend service layer documentation
with code examples and data flow diagrams.

test: add assessment service unit tests

Cover 95% of assessment_service.py with unit
and integration tests.

perf: optimize whiteboard rendering

chore: update dependencies
```

### CI/CD Pipelines

**GitHub Actions Workflows**:

**1. PR Checks** (ci.yml - Fast)
```yaml
- npm install + lint + test (frontend)
- pip install + pytest + mypy (backend)
- TypeScript compilation
- Build verification
```

**2. Feature Branches** (feature-ci.yml - Comprehensive)
```yaml
- Full test suite
- Coverage reporting (target >90%)
- Security audit
- Build optimization check
```

**3. Comprehensive Testing** (comprehensive-testing.yml)
```yaml
- Test matrix (Python 3.9-3.11, Node 18-20)
- Integration tests
- E2E tests
- Performance benchmarks
- Security scanning
```

### Debugging & Development Tools

**Backend Debugging**:
```python
# FastAPI interactive API docs
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc

# Debugging with print
from app.services.logging_service import logger
logger.debug(f"Value: {value}")

# Database inspection
from app.database import db
async with db.session() as session:
    result = await session.execute(...)
```

**Frontend Debugging**:
```typescript
// Console logging
console.log('Debug:', value)

// React DevTools browser extension
// Redux DevTools (if using Redux in future)

// Network inspection
// Chrome DevTools → Network tab → /api/chat
```

**Performance Profiling**:
```bash
# Backend
# 1. Enable profiling
# 2. Run with cProfile
python -m cProfile -o output.prof -m uvicorn app.main:app

# 3. Analyze with snakeviz
snakeviz output.prof

# Frontend
# Chrome DevTools → Performance tab → Record
```

### Deployment Process

**Development** → **Staging** → **Production**

```
Local Development
  ↓
Feature Branch (GitHub PR)
  ↓ (CI checks run)
Code Review
  ↓ (Merge to develop)
Staging Deployment
  ↓ (Manual testing)
Production Deployment
  ↓ (Vercel automatic)
Monitoring & Observability
```

**Deployment Command**:
```bash
# Deploy to production (from main branch)
./deploy-production.sh

# Steps:
# 1. Environment validation
# 2. Backend tests
# 3. Frontend tests
# 4. TypeScript compilation
# 5. Security audit
# 6. Build verification
# 7. Vercel deployment
# 8. Health check validation
# 9. Database migrations
# 10. Post-deployment monitoring
```

---

## Summary

**Frontend Architecture**:
- ✅ NextJS 14 with App Router
- ✅ Tailwind CSS + Shadcn UI
- ✅ Hooks-based state management
- ✅ Async API client integration

**Backend Architecture**:
- ✅ FastAPI with async/await
- ✅ Layered service architecture
- ✅ Comprehensive middleware stack
- ✅ Google ADK integration

**Development Workflow**:
- ✅ 270+ comprehensive tests
- ✅ CI/CD with GitHub Actions
- ✅ Code quality tools (linting, formatting)
- ✅ Clear branching strategy
- ✅ Type safety (TypeScript + Python type hints)

**Next Steps**: See [Part 4 - Operations & Production](./04_operations_production.md) for deployment, security, and monitoring details.

