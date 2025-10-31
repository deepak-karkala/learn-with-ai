# Quick Deployment Checklist

## Current Deployment Issues - FIXED

### ✅ Fixed Issues

1. **Hardcoded Backend URL** - Previously frontend had URL: `https://backend-nlrqcn4zl-dkarkala01-gmailcoms-projects.vercel.app`
   - **Status**: Fixed ✅
   - **Change**: Now uses environment variable `NEXT_PUBLIC_BACKEND_URL`
   - **File**: `frontend/vercel.json` & `frontend/next.config.js`

2. **Backend Routing Configuration** - Used conflicting `routes` with `headers`
   - **Status**: Fixed ✅
   - **Change**: Changed to `rewrites` configuration (works properly with `headers`)
   - **File**: `backend/vercel.json`

3. **Missing CORS Headers** - Backend was missing `Access-Control-Allow-Origin`
   - **Status**: Fixed ✅
   - **Change**: Added comprehensive CORS headers to backend
   - **File**: `backend/vercel.json`

4. **Deployment Size Exceeded 250MB Limit** - Backend bundle was too large
   - **Status**: Fixed ✅
   - **Changes**:
     - Removed `opik` (11MB) - Use basic logging instead
     - Removed `openai` (12MB) - Use google-genai exclusively
     - Kept `wordsegment` (12MB) - Needed for voice feature
     - Excluded test dependencies from build via `.vercelignore`
   - **Files**: `requirements.txt`, `backend/.vercelignore`, `frontend/.vercelignore`
   - **Details**: See [docs/VERCEL_SIZE_OPTIMIZATION.md](docs/VERCEL_SIZE_OPTIMIZATION.md)

5. **Editable Install Error on Vercel** - `pyproject.toml` caused package install issues
   - **Status**: Fixed ✅
   - **Changes**:
     - Excluded `pyproject.toml` from Vercel deployment
     - Excluded `uv.lock` from Vercel deployment
     - Vercel now uses `requirements.txt` exclusively
   - **Files**: `backend/.vercelignore`

6. **Google ADK Exceeds Vercel 250MB Limit** - Core dependency too large
   - **Status**: ⚠️ **Vercel Incompatible**
   - **Issue**: `google-adk` + dependencies = ~337MB (87MB over limit)
   - **Solution**: Deploy backend to Railway instead of Vercel
   - **Why Railway**:
     - No size limits
     - Docker-based deployment
     - Free tier ($5 credit/month)
     - Easy GitHub integration
   - **Files**: `backend/railway.toml`, `backend/Procfile`
   - **Details**: See [docs/DEPLOYMENT_ALTERNATIVES.md](docs/DEPLOYMENT_ALTERNATIVES.md)

---

## ⚠️ IMPORTANT: Backend Cannot Deploy to Vercel

**The backend with Google ADK is too large for Vercel's 250MB serverless limit.**

### Recommended Deployment Strategy

**Frontend**: Vercel (stays as is)
**Backend**: Railway (new platform)

This is the best approach for your stack!

## How to Deploy with Railway + Vercel

### Step 1: Deploy Backend to Railway

#### A. Create Railway Account

1. Go to [https://railway.app](https://railway.app)
2. Sign in with GitHub

#### B. Deploy from GitHub

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Select the `backend` directory (if monorepo) or root
5. Railway auto-detects Python and deploys

#### C. Set Environment Variables in Railway

In Railway dashboard → Variables:

```
GOOGLE_API_KEY=<your-google-api-key>
GOOGLE_GENAI_USE_VERTEXAI=False
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production
```

Click "Add" for each variable.

#### D. Get Railway URL

Railway will provide a URL like:
```
https://systemdesign-ai-backend-production.up.railway.app
```

Copy this URL - you'll need it for the frontend.

#### E. Test Backend

```bash
curl https://your-app-production.up.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "message": "API is running successfully"
}
```

### Step 2: Deploy Frontend to Vercel

#### A. Set Frontend Environment Variables in Vercel

1. In Vercel Dashboard → Frontend Project → Settings → Environment Variables
2. Add/Update these variables:

```
NEXT_PUBLIC_BACKEND_URL=<your-backend-url>
NEXT_PUBLIC_API_URL=<your-backend-url>/api
```

**Use your Railway URL**:
```
NEXT_PUBLIC_BACKEND_URL=https://your-app-production.up.railway.app
NEXT_PUBLIC_API_URL=https://your-app-production.up.railway.app/api
```

3. Click "Save"

#### B. Deploy Frontend

```bash
cd frontend
vercel --prod
```

Frontend will now connect to your Railway backend!

---

## Verify Deployment

### Test Backend Health

```bash
curl https://your-backend-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "API is running successfully",
  "version": "0.1.0"
}
```

### Test Backend API Health

```bash
curl https://your-backend-url/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "api_version": "0.1.0",
  "services": {...}
}
```

### Test Chat Endpoint

```bash
curl -X POST https://your-backend-url/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "user_id": "test-user"
  }'
```

Should return a response (not 503 or 500 error).

### Test Frontend

1. Open your frontend URL in browser
2. Check browser console (F12) for errors
3. Try the chat feature
4. Verify that messages are being sent to the backend

---

## Common Issues & Quick Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Frontend shows "API unavailable" | Backend URL is wrong or backend is down | Check `NEXT_PUBLIC_BACKEND_URL` in Vercel settings |
| Backend returns 503 | Services not initialized | Check that `GOOGLE_API_KEY` is set in backend env vars |
| Backend returns 500 | Missing dependencies or config | Check Vercel deployment logs for errors |
| Slow performance | Cold starts on serverless | Normal for free tier; first request takes 5-10 seconds |
| CORS errors | Backend headers misconfigured | Verify `Access-Control-Allow-Origin` in backend `vercel.json` |

---

## Files Changed

The following files were updated to fix deployment issues:

1. **`backend/vercel.json`** - Fixed routing and added CORS headers
2. **`frontend/vercel.json`** - Made backend URL dynamic via environment variable
3. **`frontend/next.config.js`** - Updated to read backend URL from environment
4. **`docs/VERCEL_DEPLOYMENT_GUIDE.md`** - New comprehensive deployment guide

---

## Next Steps

1. Update environment variables in Vercel
2. Run deployments (backend first, then frontend)
3. Test health endpoints
4. Test chat functionality
5. Monitor logs for any errors

**For detailed information**, see [VERCEL_DEPLOYMENT_GUIDE.md](docs/VERCEL_DEPLOYMENT_GUIDE.md)
