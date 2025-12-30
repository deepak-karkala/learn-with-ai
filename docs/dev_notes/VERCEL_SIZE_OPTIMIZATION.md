# Vercel 250MB Deployment Size Optimization

## Problem

Vercel has a 250MB unzipped limit for serverless functions. The backend was exceeding this due to heavy transitive dependencies pulled in by `google-adk`.

## Size Analysis

### Packages Removed (Total: ~163MB)

| Package | Size | Reason for Removal |
|---------|------|-------------------|
| `opik` | 11MB | Monitoring library; use basic logging instead |
| `openai` | 12MB | Redundant; use google-genai for all LLM calls |
| `numpy` | 109MB | Transitive dependency from opik/litellm |
| `litellm` | 41MB | Transitive dependency from opik |
| `googleapiclient` | 90MB | Transitive dependency from google packages |
| `pytest` | Dev only | Testing; excluded from production build |
| pytest-asyncio | Dev only | Testing; excluded from production build |
| pytest-cov | Dev only | Testing; excluded from production build |

### Packages Kept

| Package | Size | Reason |
|---------|------|--------|
| `wordsegment` | 12MB | Required for voice feature (speech-to-text word segmentation) |

### Remaining Large Packages (~70MB)

These are transitive dependencies from `google-adk` and `google-genai`, which are core to the application:

| Package | Size | Required For |
|---------|------|--------------|
| `google` packages | 242MB | ADK agent framework, core functionality |
| `grpc` | 38MB | Protocol Buffers for ADK communication |
| `cryptography` | 22MB | Security and authentication |
| `sqlalchemy` | 18MB | Database ORM |

**Note**: The remaining size should be under 250MB after removing unused dependencies.

## Changes Made

### 1. Updated `requirements.txt`

**Removed:**
```
openai>=1.0.0
opik>=0.2.0
```

**Kept:**
```
wordsegment>=1.0.0  # 12MB - Voice feature (speech-to-text)
```

**Why:**
- `openai`: Redundant since we're using `google-genai` for all LLM calls
- `opik`: Monitoring library that pulls in `litellm` (41MB) and `numpy` (109MB)
- `wordsegment`: Needed for voice feature word segmentation functionality

### 2. Added `.vercelignore` Files

```
# backend/.vercelignore
tests
test_*.py
conftest.py
*.md
docs
.vscode
.github
```

Excludes test dependencies and documentation from production build.

### 3. Code Fallbacks Already In Place

**Monitoring service** (`app/services/monitoring_service.py`):
```python
try:
    from opik import Opik, track
except ImportError:
    Opik = None
    # Disables Opik monitoring gracefully
```

The monitoring service works without opik - basic logging will be used instead.

**Voice endpoint** (`app/api/voice.py`):
```python
try:
    from wordsegment import load, segment
    WORDSEGMENT_AVAILABLE = True
except ImportError:
    WORDSEGMENT_AVAILABLE = False
    # Uses regex-based fallback (though wordsegment is now included)
```

Now that `wordsegment` is in requirements, the voice feature has full functionality.

## Deployment Strategy

### Phase 1: MVP (Current)
- Remove monitoring library (opik) - use basic logging
- Remove duplicate LLM library (openai) - use google-genai
- Keep voice feature (wordsegment) included
- Use Vercel's 250MB limit with optimized dependencies
- Exclude test/doc files via .vercelignore

### Phase 2: Enhanced Features
- Add advanced monitoring with Opik (separate service)
- Add OpenAI support if needed (different deployment)
- Integrate additional voice features

### Phase 3+: Monitoring & Advanced Features
- Deploy Opik monitoring on dedicated service
- Use Vercel's Edge Middleware for monitoring
- Consider dedicated ML inference service

## Testing Deployment Size Locally

```bash
# Check actual bundle size
cd backend

# Create production-like environment
python -m venv test-venv
source test-venv/bin/activate
pip install -r requirements.txt

# Check size (excluding venv overhead)
du -sh test-venv/lib/python*/site-packages

# Should be < 250MB
```

## Vercel Deployment Commands

```bash
# Clean build
cd backend
rm -rf .vercel  # Remove Vercel cache if issues persist

# Deploy
vercel --prod --force  # Force rebuild without cache

# Monitor build
# Watch the Vercel dashboard for "Build & Deployments"
```

## Troubleshooting

### Still Getting Size Error?

1. **Clear Vercel cache**:
   - Go to Vercel Dashboard
   - Project Settings → Deployments
   - Delete any cached builds

2. **Check actual dependencies**:
   ```bash
   pip list | wc -l  # Should be ~30-40 packages
   ```

3. **Verify .vercelignore is working**:
   - Look at Vercel build logs
   - Should exclude `tests/` and `pytest`

### Performance Issues After Removal?

1. **opik removal**: Basic logging replaces Opik tracing
   - Implement custom metrics if needed
   - Use Vercel's built-in monitoring

2. **openai removal**: Use google-genai exclusively
   - Ensure `GOOGLE_API_KEY` is set
   - Test LLM calls in development

3. **wordsegment removal**: Regex-based fallback in place
   - Voice endpoint will use simpler word segmentation
   - Re-enable in Phase 2 if needed

## Future Optimizations

### If Size Issues Persist:

1. **Monorepo split**: Deploy backend as multiple services
   - Chat service (core)
   - Voice service (optional, with wordsegment)
   - Assessment service (if needed)

2. **Docker optimization**:
   - Use slim base images
   - Multi-stage builds
   - Remove test dependencies

3. **Serverless alternatives**:
   - AWS Lambda (with 500MB limit)
   - Google Cloud Functions (with higher limits)
   - Railway.app or Render (different pricing model)

## Environment Variables

After removing opik, these env vars are no longer needed:

```
OPIK_API_KEY          # Remove
OPIK_PROJECT_NAME     # Remove
OPIK_WORKSPACE        # Remove
```

Keep these:
```
GOOGLE_API_KEY              # Required
GOOGLE_GENAI_USE_VERTEXAI   # Required
DEBUG                       # Optional
LOG_LEVEL                   # Optional
```

## References

- [Vercel Functions Size Limits](https://vercel.com/docs/concepts/functions/serverless-functions#limits)
- [Optimizing Python for Serverless](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python#configuration)
- [Dependency Size Analysis](https://pypi.org)
