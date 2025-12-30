# Deployment Alternatives for Google ADK Backend

## The Problem

The backend with `google-adk` and `google-genai` exceeds Vercel's 250MB unzipped serverless function limit, even after aggressive dependency optimization.

### Size Breakdown

| Component | Unzipped Size | Notes |
|-----------|---------------|-------|
| `google` packages | ~242MB | Core ADK functionality |
| `grpc` | ~38MB | Protocol Buffers communication |
| `cryptography` | ~22MB | Security |
| FastAPI + deps | ~15MB | Web framework |
| Other packages | ~20MB | Utilities |
| **Total** | **~337MB** | **Exceeds 250MB limit** |

### What We've Tried

✅ Removed `opik` (11MB + 150MB transitive deps)
✅ Removed `openai` (12MB)
✅ Removed non-essential packages (redis, sqlalchemy, aiohttp, etc.)
✅ Excluded test dependencies
✅ Minimal requirements.txt

**Result**: Still ~337MB unzipped (87MB over limit)

## Recommended Solutions

### Option 1: Deploy Backend to Railway or Render ⭐ **RECOMMENDED**

**Why**: These platforms don't have the 250MB serverless limit.

#### Railway Deployment

**Pros**:
- No 250MB limit
- Docker-based deployment
- Free tier: $5/month credit
- Easy setup with GitHub integration
- Built-in PostgreSQL/Redis addons

**Setup**:
```bash
# 1. Create railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

**Steps**:
1. Push code to GitHub
2. Create Railway account
3. Connect GitHub repo
4. Deploy automatically
5. Update frontend `NEXT_PUBLIC_BACKEND_URL` to Railway URL

**Cost**: Free tier ($5 credit/month), then ~$5-10/month

#### Render Deployment

**Pros**:
- No 250MB limit
- Free tier available
- Docker support
- Auto-deploy from GitHub

**Setup**:
```yaml
# render.yaml
services:
  - type: web
    name: systemdesign-ai-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
```

**Cost**: Free tier (limited), paid from $7/month

---

### Option 2: Split Backend into Multiple Vercel Functions

**Concept**: Deploy different parts as separate serverless functions.

**Functions**:
1. **Core API** (chat, session) - Google ADK - Deploy to Railway
2. **Static APIs** (health, content) - Deploy to Vercel
3. **Frontend** - Remain on Vercel

**Pros**:
- Keep frontend on Vercel
- Only move heavy ADK backend

**Cons**:
- More complex architecture
- Multiple deployments

**Not recommended** - Option 1 is simpler.

---

### Option 3: Use Vercel Docker Deployment (Pro Plan Only)

If you have Vercel Pro plan, you can deploy Docker containers without the 250MB limit.

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**vercel.json**:
```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "docker"
    }
  }
}
```

**Cost**: Vercel Pro: $20/month per user

---

### Option 4: Google Cloud Run (Native Google Platform)

**Why**: Since you're using Google ADK, Cloud Run integrates perfectly.

**Pros**:
- No size limits
- Pay per use
- Native Google Cloud integration
- Docker-based
- Free tier: 2M requests/month

**Setup**:
```bash
# Build and deploy
gcloud run deploy systemdesign-ai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Cost**: Free tier, then ~$0.40 per million requests

---

## Comparison Table

| Platform | Size Limit | Free Tier | Docker | Complexity | Monthly Cost |
|----------|------------|-----------|--------|------------|--------------|
| **Railway** | None | $5 credit | ✅ | Low | $5-10 |
| **Render** | None | Limited | ✅ | Low | $0-7 |
| **Vercel Pro** | None (Docker) | No | ✅ | Low | $20 |
| **Cloud Run** | None | 2M req/mo | ✅ | Medium | $0-5 |
| **Vercel Serverless** | 250MB | ✅ | ❌ | Low | $0 |

---

## Our Recommendation: Railway ⭐

**Why Railway**:
1. **Easiest migration** - Minimal code changes
2. **No size limits** - Google ADK fits perfectly
3. **Affordable** - $5-10/month
4. **Great DX** - Auto-deploy from GitHub
5. **Scalable** - Can add Redis/PostgreSQL easily

### Migration Steps

#### 1. Create `railway.toml`

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

#### 2. Create `Procfile` (optional)

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 3. Push to GitHub

```bash
git add railway.toml Procfile
git commit -m "Add Railway configuration"
git push
```

#### 4. Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and deploys

#### 5. Set Environment Variables

In Railway dashboard:
```
GOOGLE_API_KEY=your-api-key
GOOGLE_GENAI_USE_VERTEXAI=False
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production
```

#### 6. Get Railway URL

Railway provides: `https://your-app-production.up.railway.app`

#### 7. Update Frontend

In Vercel (frontend):
```
NEXT_PUBLIC_BACKEND_URL=https://your-app-production.up.railway.app
```

Redeploy frontend.

#### 8. Test

```bash
curl https://your-app-production.up.railway.app/health
```

---

## Alternative: Keep Frontend on Vercel, Backend on Railway

**Architecture**:
```
Frontend (Vercel)  →  Backend (Railway)
Next.js                 FastAPI + Google ADK
```

**Benefits**:
- ✅ Best of both worlds
- ✅ Frontend CDN performance (Vercel)
- ✅ Backend no size limits (Railway)
- ✅ Affordable (~$10/month total)
- ✅ Easy to maintain

**This is our recommended approach!**

---

## Next Steps

1. **Create Railway account** at [railway.app](https://railway.app)
2. **Add `railway.toml`** to your backend directory (see above)
3. **Deploy** by connecting GitHub repo
4. **Update frontend env vars** with Railway URL
5. **Redeploy frontend** on Vercel

---

## Questions?

See these resources:
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Vercel Docker Docs](https://vercel.com/docs/functions/serverless-functions/runtimes/docker)
