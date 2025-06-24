# Claude Code Configuration
## AI System Design Learning Platform

### Project Overview
This is an AI-powered learning platform that helps software engineers prepare for system design interviews through interactive AI tutoring, real-time whiteboard feedback, and comprehensive progress tracking.

### Tech Stack
- **Frontend**: NextJS 14+, TypeScript, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python), Google Agent Development Kit (ADK)
- **AI Framework**: Google ADK with Gemini 2.0 Flash
- **Database**: PostgreSQL (production), Redis (caching)
- **Deployment**: Vercel (frontend + serverless backend)
- **Monitoring**: Comet Opik for LLM observability

### Key Features
1. **Interactive AI Tutor**: Real-time conversation with expert-level AI agent
2. **Whiteboard Analysis**: PNG capture + multimodal LLM analysis for architecture feedback
3. **AI Diagram Generation**: Context-aware Mermaid diagram creation and rendering
4. **Assessment System**: 6-dimensional evaluation with detailed feedback
5. **Progress Analytics**: Timeline visualization and personalized recommendations
6. **Voice Integration**: Bidirectional audio streaming (future phase)

### Development Approach
- **Incremental Development**: Each phase builds upon previous functionality
- **Test-Driven**: Comprehensive testing at unit, integration, and E2E levels
- **GitHub Integration**: Issues-based development with clear milestones

### Current Development Phase
**Phase 1: Foundation & Core Setup (Issues #1-7)**
- Project setup and repository structure
- Vercel deployment pipeline
- Google ADK integration with basic agent
- Session management and state handling
- Basic UI with chat interface
- FastAPI backend with chat endpoints
- End-to-end integration testing

### Project Structure
```
systemdesign-ai-platform/
├── frontend/                 # NextJS application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Next.js pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── utils/           # Utility functions
│   │   └── types/           # TypeScript type definitions
│   ├── public/              # Static assets
│   └── package.json
├── backend/                  # FastAPI + ADK backend
│   ├── app/
│   │   ├── agents/          # ADK agent definitions
│   │   ├── api/             # FastAPI route handlers
│   │   ├── models/          # Pydantic models
│   │   ├── services/        # Business logic services
│   │   ├── tools/           # ADK custom tools
│   │   └── callbacks/       # ADK callbacks
│   ├── tests/               # Backend tests
│   └── requirements.txt
├── tests/                   # End-to-end tests
├── docs/                    # Documentation
├── .github/                 # GitHub workflows and templates
└── deployment/             # Deployment configurations
```

### Development Guidelines

#### Code Style
- **TypeScript**: Strict mode enabled, proper type definitions
- **Python**: Follow PEP 8, use type hints, docstrings for functions
- **Testing**: Write tests before implementation (TDD approach)
- **Documentation**: Update README and docs with each feature

#### Git Workflow
- **Branch naming**: `feature/issue-[number]-[description]`
- **Commit messages**: Follow conventional commits format
- **PR requirements**: Reference issue number, include tests, update docs

#### Testing Requirements
- **Unit Tests**: >90% code coverage required
- **Integration Tests**: Test all API endpoints and ADK integration
- **E2E Tests**: Complete user flow validation
- **Manual Testing**: UI/UX verification before issue completion

### Environment Variables
```bash
# Google ADK Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_API_KEY=your-api-key
GOOGLE_GENAI_USE_VERTEXAI=True

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379

# Vercel Configuration
VERCEL_TOKEN=your-vercel-token
NEXT_PUBLIC_API_URL=https://your-app.vercel.app/api

# Monitoring
OPIK_API_KEY=your-opik-key
OPIK_PROJECT_NAME=systemdesign-ai

# Security
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
```

### Implementation Priorities

#### Phase 1 (Current): Foundation
1. **Issue #1**: Project setup and repository structure
2. **Issue #2**: Vercel deployment pipeline setup
3. **Issue #3**: Google ADK basic setup and authentication
4. **Issue #4**: ADK session management and state
5. **Issue #5**: Basic frontend UI with chat interface
6. **Issue #6**: FastAPI backend with basic chat endpoint
7. **Issue #7**: End-to-end chat flow integration

#### Phase 2: Core Features
- Whiteboard implementation with PNG analysis
- LLM judge assessment system
- AI diagram generation with Mermaid
- Progress tracking backend

#### Phase 3: Integration & Polish
- Voice integration with Live API
- Progress dashboard frontend
- Complete feature integration

#### Phase 4: Production Ready
- Production deployment and monitoring
- Security implementation
- Performance optimization
- Comprehensive testing

### Key Implementation Notes

#### Google ADK Integration
- Use `InMemorySessionService` for development
- Implement custom tools for whiteboard analysis and diagram generation
- Set up callbacks for monitoring and cost tracking
- Follow ADK best practices for agent orchestration

#### Whiteboard Functionality
- Capture canvas as PNG (not shape recognition)
- Use multimodal LLM (GPT-4V/Claude 3.5 Sonnet) for analysis
- Store PNGs as ADK artifacts
- Optimize for cost and latency

#### Assessment System
- 6-dimensional scoring framework
- LLM judge with detailed rubrics
- Confidence scoring and human review triggers
- Progress timeline visualization

#### Performance Requirements
- API response time <2 seconds
- Whiteboard analysis <1 second latency
- >99.5% uptime
- Cost per session $0.20-0.80

### Testing Strategy

#### Unit Testing
```bash
# Frontend tests
cd frontend && npm test

# Backend tests  
cd backend && pytest --cov=app --cov-report=html
```

#### Integration Testing
```bash
# API endpoint testing
pytest tests/integration/

# ADK integration testing
pytest tests/adk/
```

#### End-to-End Testing
```bash
# Playwright E2E tests
npm run test:e2e
```

### Deployment Commands

#### Development
```bash
# Start frontend
cd frontend && npm run dev

# Start backend
cd backend && uvicorn app.main:app --reload

# Start both with concurrently
npm run dev:all
```

#### Production
```bash
# Deploy to Vercel
vercel --prod

# Health check
curl https://your-app.vercel.app/health
```

### Documentation References
- [Product Requirements Document](./docs/product_requirements_document.md)
- [ADK Implementation Plan](./docs/adk_implementation_plan_complete.md)
- [ADK Feature Mapping](./docs/adk_feature_mapping.md)
- [User Flows & Features](./docs/user_flow_features.md)
- [Go-to-Market Strategy](./docs/go_to_market_strategy.md)
- [Security & Monitoring Guide](./docs/adk_security_monitoring_guide.md)

### Support & Resources
- **ADK Documentation**: https://google.github.io/adk-docs/
- **Vercel Docs**: https://vercel.com/docs
- **NextJS Docs**: https://nextjs.org/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Shadcn UI**: https://ui.shadcn.com/