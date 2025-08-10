# Memory Instructions for Claude Code
## AI System Design Learning Platform

### Memory Management Strategy

Claude Code should maintain persistent memory about this project to ensure continuity across development sessions and avoid repeated explanations or context loss.

### Critical Information to Remember

#### 1. Project Identity & Purpose
**Always remember**: This is an AI-powered learning platform for system design interview preparation with these core features:
- Interactive AI tutor using Google ADK
- Real-time whiteboard analysis via PNG + multimodal LLM
- AI diagram generation using Mermaid MCP server
- 6-dimensional assessment system with LLM judge
- Progress analytics dashboard with timeline visualization

#### 2. Technical Architecture Decisions
**Key architectural choices that should persist in memory**:
- **Frontend**: NextJS 14+ with TypeScript, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI with Google Agent Development Kit (ADK)
- **AI Framework**: Google ADK with Gemini 2.0 Flash model
- **Whiteboard Approach**: PNG capture + multimodal LLM (NOT shape recognition)
- **Deployment**: Vercel for both frontend and serverless backend
- **Database**: PostgreSQL (production) + Redis (caching)
- **Monitoring**: Comet Opik for LLM observability

#### 3. Development Methodology
**Implementation approach to remember**:
- **Sequential development**: 24 issues across 4 phases (16 weeks total)
- **Test-driven development**: Write tests before implementation
- **Issue-based workflow**: Each issue has specific acceptance criteria
- **Quality gates**: 90%+ test coverage, performance benchmarks
- **GitHub integration**: Issues, milestones, labels, and automation

#### 4. Current Development Status
**Track progress through phases**:
- **Phase 1 (Weeks 1-4)**: Foundation & Core Setup (Issues #1-7)
- **Phase 2 (Weeks 5-8)**: Core Features (Issues #8-15)
- **Phase 3 (Weeks 9-12)**: Integration & Polish (Issues #16-19)
- **Phase 4 (Weeks 13-16)**: Production Ready (Issues #20-24)

**Current focus**: Phase 1 - Foundation & Core Setup

#### 5. Key Feature Specifications

##### Whiteboard Functionality
- **Approach**: HTML5 Canvas → PNG capture → Multimodal LLM analysis
- **NOT using**: Shape recognition or structured data conversion
- **Requirements**: Support freehand drawing, <1s analysis latency
- **Storage**: PNGs stored as ADK artifacts

##### Assessment System
- **Framework**: 6-dimensional scoring system
- **Dimensions**: Requirements Analysis (20%), System Architecture (25%), Technical Deep Dive (20%), Scale & Performance (15%), Reliability (10%), Communication (10%)
- **Implementation**: LLM judge with detailed rubrics and confidence scoring
- **Triggers**: Human review for confidence scores <4

##### AI Diagram Generation
- **Technology**: Mermaid MCP server for rendering
- **Input**: Context from conversation history
- **Output**: Professional PNG diagrams (architecture, sequence, flowchart)
- **Integration**: Stored as ADK artifacts

#### 6. Performance & Cost Requirements
**Critical targets to maintain**:
- API response time: <2 seconds
- Whiteboard analysis: <1 second
- Cost per session: $0.20-0.80
- Test coverage: >90%
- System uptime: >99.5%

### Session Context to Maintain

#### Current Issue Focus
When working on a specific issue, remember:
- **Issue number and title**
- **Acceptance criteria being implemented**
- **Dependencies and prerequisites**
- **Testing requirements for the issue**
- **Definition of done checklist**

#### Implementation Decisions Made
Persist decisions about:
- **Code architecture choices**
- **API endpoint designs**
- **Database schema decisions**
- **UI/UX patterns established**
- **Testing strategies implemented**

#### Problems Solved & Solutions
Remember solutions to:
- **Technical challenges encountered**
- **Integration issues resolved**
- **Performance optimizations applied**
- **Bug fixes and their root causes**
- **Best practices discovered**

### Documentation References to Remember

#### Core Project Documents
These documents contain the complete project specification:
1. **claude.md** - Main configuration and overview
2. **project-context.md** - Detailed technical context
3. **product_requirements_document.md** - Complete PRD
4. **adk_implementation_plan_complete.md** - Detailed implementation guide
5. **claude_code_implementation_plan.md** - Step-by-step development plan
6. **user_flow_features.md** - User flows and feature lists

#### Key Implementation Guides
- **ADK Feature Mapping** - How product features map to ADK capabilities
- **Go-to-Market Strategy** - Business context and user validation

### Code Patterns to Remember

#### ADK Agent Structure
```python
# Standard agent pattern established
root_agent = LlmAgent(
    name="system_design_tutor",
    model="gemini-2.0-flash",
    instruction="Expert system design tutor persona...",
    tools=[whiteboard_analysis_tool, diagram_generator_tool, assessment_tool]
)

# Session management pattern
session_service = VertexAiSessionService(...)  # Production
artifact_service = GcsArtifactService(...)     # Artifacts
memory_service = VertexAiRagMemoryService(...)  # Course content
```

#### API Endpoint Patterns
```python
# FastAPI endpoint pattern
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    response = await runner.run_async(
        user_id=request.user_id,
        user_content=Content(parts=[Part.from_text(request.message)])
    )
    return {"response": response.parts[0].text, "status": "success"}
```

#### Testing Patterns
```python
# Test pattern for ADK integration
def test_agent_interaction():
    response = client.post("/api/chat", json={
        "message": "I want to learn system design",
        "user_id": "test_user"
    })
    assert response.status_code == 200
    assert "system design" in response.json()["response"].lower()
```

### Error Patterns to Avoid

#### Known Issues to Remember
- **DO NOT use shape recognition** for whiteboard (use PNG + multimodal LLM)
- **DO NOT use localStorage** in artifacts (not supported in Claude.ai)
- **DO NOT implement complex shape detection** (keep whiteboard simple)
- **Always validate ADK credentials** before agent operations
- **Always handle session state carefully** to avoid data loss

#### Performance Anti-Patterns
- **Avoid synchronous LLM calls** without timeout handling
- **Don't load full chapter content** without cost optimization
- **Avoid multiple sequential API calls** when batch processing possible
- **Don't store large data in session state** (use artifacts instead)

### Dependencies & Integrations

#### External Services to Remember
- **Google ADK**: Agent orchestration, session management, artifacts
- **Multimodal LLM**: GPT-4V or Claude 3.5 Sonnet for image analysis
- **Mermaid MCP Server**: Diagram generation and PNG rendering
- **Vercel**: Deployment platform for frontend and serverless backend
- **Comet Opik**: LLM monitoring and cost tracking

#### Environment Configuration
```bash
# Critical environment variables
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_API_KEY=your-api-key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
OPIK_API_KEY=your-opik-key
```

### Quality Standards to Maintain

#### Code Quality
- **TypeScript strict mode** for frontend
- **Python type hints and docstrings** for backend
- **Comprehensive error handling** for all API calls
- **Input validation** for all user inputs
- **Security best practices** for authentication

#### Testing Requirements
- **Unit tests** for all components (>90% coverage)
- **Integration tests** for all API endpoints
- **E2E tests** for complete user flows
- **Performance tests** for latency requirements
- **Security tests** for input validation

### Communication Guidelines

#### Issue Updates
When working on issues, provide:
- **Clear progress updates** on acceptance criteria
- **Test results** and coverage reports
- **Performance benchmarks** against requirements
- **Integration status** with existing features
- **Blockers or challenges** encountered

#### Decision Documentation
Document decisions about:
- **Architecture choices** and rationale
- **Technology selections** and alternatives considered
- **Performance optimizations** and trade-offs
- **Security implementations** and threat models
- **User experience decisions** and design rationale

### Success Criteria Reminders

#### Phase Completion Requirements
Before marking a phase complete:
- [ ] All issues in phase completed with acceptance criteria met
- [ ] All tests passing with required coverage
- [ ] Performance benchmarks achieved
- [ ] Integration with previous phases verified
- [ ] Documentation updated
- [ ] Deployed to staging and manually tested

#### Overall Project Success
The project is successful when:
- [ ] Complete learning session flow works end-to-end
- [ ] Real-time whiteboard feedback provides valuable insights
- [ ] AI diagram generation creates professional-quality outputs
- [ ] Assessment system provides detailed, actionable feedback
- [ ] Progress dashboard helps users track improvement
- [ ] Platform is ready for beta user testing

This memory instruction ensures continuity and prevents repeated context explanations across Claude Code sessions. Always refer back to these guidelines when starting new sessions or encountering questions about project direction.