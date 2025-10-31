# Railway Quick Start Guide

## Critical: Environment Variables Must Be Set First!

**Before deploying**, you MUST set these environment variables in Railway, or the app will crash on startup:

### Required Environment Variables

Go to Railway Dashboard → Your Project → Variables → Add the following:

```
GOOGLE_API_KEY=your-actual-google-api-key-here
```

**How to get your Google API Key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Paste it in Railway Variables

### Optional (Recommended) Environment Variables

```
GOOGLE_GENAI_USE_VERTEXAI=False
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## Deployment Steps

### 1. Set Environment Variables (Critical!)

❌ **DO NOT deploy without setting `GOOGLE_API_KEY` first!**

The app will crash immediately if this is missing.

### 2. Deploy to Railway

**Option A: From GitHub** (Recommended)

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Add Railway configuration"
   git push
   ```

2. In Railway:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway auto-deploys

**Option B: Railway CLI**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### 3. Monitor Deployment

Watch the logs in Railway dashboard:

**Build Phase** (~1-2 minutes):
```
Successfully installed fastapi google-adk google-genai ...
```

**Startup Phase** (~30-60 seconds):
```
INFO: Starting production services initialization...
INFO: Production services initialized successfully
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:XXXX
```

**Healthcheck** (~10-20 seconds):
```
Starting Healthcheck
Attempt #1 succeeded with status 200
```

### 4. Get Your Railway URL

Once deployed, Railway provides a URL like:
```
https://systemdesign-ai-backend-production.up.railway.app
```

Copy this URL - you'll use it for your frontend.

### 5. Test the Deployment

```bash
# Test root endpoint
curl https://your-app-production.up.railway.app/

# Test health endpoint
curl https://your-app-production.up.railway.app/health

# Test API health
curl https://your-app-production.up.railway.app/api/health
```

Expected responses:
```json
// Root endpoint
{"message": "AI System Design Learning Platform API"}

// Health endpoint
{"status": "healthy", "message": "API is running successfully", "version": "0.1.0"}

// API health endpoint
{"status": "healthy", "api_version": "0.1.0", "services": {...}}
```

---

## Troubleshooting

### Issue: "Service Unavailable" during healthcheck

**Symptom**:
```
Attempt #1 failed with service unavailable
1/1 replicas never became healthy!
```

**Causes & Solutions**:

#### 1. Missing `GOOGLE_API_KEY` ⚠️ MOST COMMON

**Check**: Look in deploy logs for:
```
KeyError: 'GOOGLE_API_KEY'
RuntimeError: Service initialization failed
```

**Fix**: Add `GOOGLE_API_KEY` in Railway Variables, then redeploy.

#### 2. Invalid API Key

**Check**: Deploy logs show:
```
google.auth.exceptions.RefreshError
Invalid API key
```

**Fix**: Get a new API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

#### 3. App Crashes During Startup

**Check Deploy Logs for**:
- `ImportError` - Missing dependencies (shouldn't happen, build succeeded)
- `ModuleNotFoundError` - Python can't find modules
- `ConnectionError` - Can't connect to external services

**Debug**:
```bash
# Check Railway logs
Railway Dashboard → Deployments → Latest → View Logs

# Filter for errors
Look for "ERROR" or "CRITICAL" or "Failed"
```

#### 4. Port Issues

**Check**: App logs show:
```
Address already in use
OSError: [Errno 48] Address already in use
```

**Fix**: Railway automatically sets `$PORT`. Ensure `railway.toml` uses `$PORT` (already configured).

---

## Complete Environment Variable List

### Required
```
GOOGLE_API_KEY=<your-key>        # ⚠️ CRITICAL - App won't start without this
```

### Recommended
```
GOOGLE_GENAI_USE_VERTEXAI=False  # Use Google AI Studio (not Vertex AI)
ENVIRONMENT=production           # Set environment
DEBUG=False                      # Disable debug mode
LOG_LEVEL=INFO                   # Logging verbosity
```

### Optional (Not needed for basic functionality)
```
DATABASE_URL=<connection-string> # Only if using PostgreSQL
REDIS_URL=<connection-string>    # Only if using Redis
```

---

## Railway Dashboard Navigation

1. **View Logs**: Project → Deployments → Latest Deployment → "View Logs"
2. **Environment Variables**: Project → Variables → Add Variable
3. **Metrics**: Project → Metrics (CPU, Memory, Network)
4. **Settings**: Project → Settings (change name, region, etc.)

---

## Cost & Limits

### Free Tier
- $5 credit per month
- 512MB RAM
- Shared CPU
- 100GB bandwidth

### Hobby Plan ($5/month)
- $5 credit + pay for usage
- 8GB RAM
- Dedicated CPU
- 100GB bandwidth

**Estimated monthly cost for this backend**: $5-10/month

---

## Next Step: Connect Frontend

Once backend is deployed and healthy:

1. **Copy Railway URL**:
   ```
   https://your-app-production.up.railway.app
   ```

2. **Update Frontend (Vercel)**:
   - Go to Vercel Dashboard → Frontend Project → Settings → Environment Variables
   - Add:
     ```
     NEXT_PUBLIC_BACKEND_URL=https://your-app-production.up.railway.app
     NEXT_PUBLIC_API_URL=https://your-app-production.up.railway.app/api
     ```

3. **Redeploy Frontend**:
   ```bash
   cd frontend
   vercel --prod
   ```

4. **Test End-to-End**:
   - Open your frontend URL
   - Try the chat feature
   - Should connect to Railway backend!

---

## Getting Help

1. **Check Deploy Logs First** - 90% of issues are visible in logs
2. **Railway Discord**: https://discord.gg/railway
3. **Railway Docs**: https://docs.railway.app
4. **Troubleshooting Guide**: [RAILWAY_TROUBLESHOOTING.md](./RAILWAY_TROUBLESHOOTING.md)

---

## Summary Checklist

- [ ] Set `GOOGLE_API_KEY` in Railway Variables
- [ ] Push code to GitHub
- [ ] Deploy from GitHub in Railway
- [ ] Monitor deployment logs
- [ ] Wait for "Healthcheck succeeded"
- [ ] Copy Railway URL
- [ ] Update frontend environment variables
- [ ] Deploy frontend
- [ ] Test end-to-end

**Total time**: ~5-10 minutes
