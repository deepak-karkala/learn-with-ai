# Railway Deployment Troubleshooting

## Common Issues and Solutions

### Issue 1: Healthcheck Timeout (Service Unavailable)

**Error**:
```
Attempt #1 failed with service unavailable
1/1 replicas never became healthy!
Healthcheck failed!
```

**Cause**: The app takes longer than the default 30s to start due to:
- Loading Google ADK dependencies
- Initializing multiple services on startup
- Large dependency tree

**Solutions**:

#### Solution A: Increased Healthcheck Timeout (Applied)

The `railway.toml` has been updated with:
```toml
[deploy]
healthcheckTimeout = 100  # Increased from 30s to 100s
```

This gives the app more time to initialize all Google ADK services.

#### Solution B: Check Environment Variables

Ensure these are set in Railway dashboard → Variables:

```
GOOGLE_API_KEY=your-actual-api-key
GOOGLE_GENAI_USE_VERTEXAI=False
ENVIRONMENT=production
```

Missing `GOOGLE_API_KEY` will cause initialization to fail.

#### Solution C: Monitor Startup Logs

In Railway dashboard:
1. Go to your project
2. Click "Deployments"
3. Click the failed deployment
4. Check "Deploy Logs" for errors

Look for:
- `ImportError` - Missing dependencies
- `Connection refused` - Port issues
- `Failed to initialize` - Service initialization errors

---

### Issue 2: Port Binding Issues

**Error**: `Address already in use` or connection refused

**Solution**: Railway automatically sets the `$PORT` environment variable. Ensure your start command uses it:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

This is already configured in `Procfile` and `railway.toml`.

---

### Issue 3: Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'google'`

**Cause**: `requirements.txt` not found or incorrectly formatted

**Solution**:
1. Ensure `requirements.txt` is in the root of your backend directory
2. Check Railway build logs to confirm packages were installed
3. Verify no syntax errors in `requirements.txt`

---

### Issue 4: Memory Limit Exceeded

**Error**: `Out of memory` or `Killed`

**Cause**: Google ADK dependencies are very large (337MB), might exceed Railway's default memory limit

**Solutions**:

#### A. Upgrade Railway Plan (if on free tier)
- Free tier: 512MB RAM
- Hobby plan ($5/month): 8GB RAM

#### B. Optimize Memory Usage

Add to `railway.toml`:
```toml
[deploy]
numReplicas = 1
restartPolicyType = "ON_FAILURE"
```

#### C. Check Current Memory Usage

In Railway dashboard → Metrics, monitor:
- Memory usage
- CPU usage

---

### Issue 5: Build Succeeds But App Crashes

**Symptoms**: Build completes, but app crashes immediately after starting

**Debug Steps**:

1. **Check Deploy Logs**:
   ```
   Railway Dashboard → Deployments → Latest → Deploy Logs
   ```
   Look for Python tracebacks or errors.

2. **Common Errors**:

   **Missing Environment Variables**:
   ```python
   KeyError: 'GOOGLE_API_KEY'
   ```
   → Add `GOOGLE_API_KEY` in Railway Variables

   **Import Errors**:
   ```python
   ImportError: cannot import name 'ADKService'
   ```
   → Check that `app/` directory structure is correct

   **Database Connection**:
   ```python
   sqlalchemy.exc.OperationalError: could not connect
   ```
   → Either add `DATABASE_URL` or ensure code skips DB if not set

3. **Test Locally**:
   ```bash
   # Simulate Railway environment
   export PORT=8000
   export ENVIRONMENT=production
   export GOOGLE_API_KEY=your-key

   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

---

## Monitoring Your Railway Deployment

### View Logs

Real-time logs in Railway dashboard:
```
Railway Dashboard → Your Project → View Logs
```

Filter by:
- `stdout` - Application output
- `stderr` - Error messages
- `build` - Build process logs

### Check Health

Once deployed, test the health endpoint:

```bash
curl https://your-app-production.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "API is running successfully",
  "version": "0.1.0"
}
```

### Monitor Performance

Railway provides built-in metrics:
- **CPU Usage**: Should be < 80%
- **Memory Usage**: Should be < 80% of allocated
- **Response Time**: Monitor /health endpoint

---

## Alternative: If Railway Continues to Fail

If you continue to experience issues with Railway, consider these alternatives:

### Option 1: Google Cloud Run (Recommended for Google ADK)

Since you're using Google ADK, Cloud Run is a natural fit:

```bash
# Install Google Cloud CLI
brew install google-cloud-sdk  # macOS

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy
cd backend
gcloud run deploy systemdesign-ai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your-key,ENVIRONMENT=production
```

**Benefits**:
- Native Google Cloud integration
- No memory limits
- Pay per request
- Free tier: 2M requests/month

**Cost**: ~$0-5/month for typical usage

### Option 2: Render

```yaml
# render.yaml
services:
  - type: web
    name: systemdesign-ai-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
      - key: ENVIRONMENT
        value: production
```

**Cost**: Free tier (with limitations), paid from $7/month

---

## Configuration Files Reference

### railway.toml
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 75"
healthcheckPath = "/health"
healthcheckTimeout = 100  # Increased for slow Google ADK startup
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
ENVIRONMENT = "production"
```

### Procfile
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 75 --log-level info
```

---

## Getting Help

1. **Railway Community**:
   - Discord: https://discord.gg/railway
   - Docs: https://docs.railway.app

2. **Check Build/Deploy Logs**:
   - Always check logs first before asking for help
   - Include full error messages when seeking support

3. **Test Locally First**:
   - Ensure app runs locally with production settings
   - Verify all environment variables are set correctly
