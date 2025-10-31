# Vercel Deployment Guide

This guide explains how to deploy the AI System Design Learning Platform on Vercel with separate frontend and backend services.

## Architecture Overview

The project has two separate Vercel deployments:

1. **Frontend** (Next.js) - User interface and client-side logic
2. **Backend** (FastAPI) - API server and agent services

## Prerequisites

- Vercel account (https://vercel.com)
- GitHub repository connected to Vercel
- Google API credentials (for ADK integration)
- Environment variables configured

## Deployment Setup

### Step 1: Deploy the Backend First

The backend must be deployed first so you have a stable URL for the frontend.

#### 1.1 Create Backend Project on Vercel

```bash
# In your project directory
vercel link
```

Select or create a new Vercel project for the backend.

#### 1.2 Configure Backend Environment Variables

Go to your Vercel project dashboard and add these environment variables:

```
GOOGLE_API_KEY=your-api-key
GOOGLE_GENAI_USE_VERTEXAI=False
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production
```

#### 1.3 Deploy Backend

```bash
# Navigate to backend directory
cd backend

# Deploy to production
vercel --prod
```

**Note the deployment URL**, e.g., `https://your-backend-project.vercel.app`

### Step 2: Deploy the Frontend

#### 2.1 Create Frontend Project on Vercel

```bash
cd frontend
vercel link
```

Select or create a new Vercel project for the frontend.

#### 2.2 Configure Frontend Environment Variables

Go to your Vercel project dashboard and add:

```
NEXT_PUBLIC_BACKEND_URL=https://your-backend-project.vercel.app
NEXT_PUBLIC_API_URL=https://your-backend-project.vercel.app/api
```

Replace `https://your-backend-project.vercel.app` with your actual backend URL from Step 1.3.

#### 2.3 Deploy Frontend

```bash
cd frontend

# Deploy to production
vercel --prod
```

## Configuration Files Explained

### Backend Configuration: `backend/vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb",
        "runtime": "python3.11"
      }
    }
  ],
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/app/main.py"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        },
        {
          "key": "Access-Control-Allow-Methods",
          "value": "GET, POST, PUT, DELETE, OPTIONS"
        }
      ]
    }
  ]
}
```

**Key Points:**
- Uses `@vercel/python` builder for FastAPI apps
- `rewrites` (not `routes`) is the correct configuration when using `headers`
- Includes CORS headers for cross-origin requests from the frontend
- Catches all routes and directs them to the FastAPI app

### Frontend Configuration: `frontend/vercel.json` & `next.config.js`

**vercel.json:**
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "${NEXT_PUBLIC_BACKEND_URL}/api/$1"
    }
  ]
}
```

**next.config.js:**
```javascript
async rewrites() {
  let backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  return [
    {
      source: '/api/:path*',
      destination: `${backendUrl}/api/:path*`,
    },
  ]
}
```

**Key Points:**
- Rewrites proxy `/api/*` requests to the backend
- Uses environment variable `NEXT_PUBLIC_BACKEND_URL` for dynamic configuration
- Supports both development (localhost:8000) and production URLs

## Troubleshooting

### Backend Returns 500 Errors

**Problem:** Backend endpoints return 500 Internal Server Error

**Solutions:**
1. Check environment variables in Vercel dashboard
   - `GOOGLE_API_KEY` must be set and valid
   - `GOOGLE_GENAI_USE_VERTEXAI` must be False for Google AI Studio
2. Check backend logs in Vercel dashboard
   - Go to project → Deployments → Recent deployment → Runtime Logs

### Frontend Can't Reach Backend

**Problem:** `NEXT_PUBLIC_BACKEND_URL` not accessible or 404 errors

**Solutions:**
1. Verify the backend URL is correct in frontend environment variables
2. Ensure backend is deployed and healthy:
   ```bash
   curl https://your-backend-url/health
   ```
3. Check CORS headers in backend `vercel.json`:
   - Should include `Access-Control-Allow-Origin: *`
4. In development, ensure frontend `next.config.js` has correct rewrite rules

### CORS Issues

**Problem:** Browser shows CORS errors

**Solution:** Verify backend headers in `vercel.json`:

```json
"headers": [
  {
    "source": "/(.*)",
    "headers": [
      {
        "key": "Access-Control-Allow-Origin",
        "value": "*"
      },
      {
        "key": "Access-Control-Allow-Methods",
        "value": "GET, POST, PUT, DELETE, OPTIONS"
      }
    ]
  }
]
```

### Cold Start Performance

**Problem:** First requests are slow (cold starts)

**Solution:** This is normal for serverless functions. To mitigate:
1. Monitor usage and consider upgrading Vercel plan
2. Use Vercel's "Prerender" feature for static pages
3. Optimize requirements.txt to reduce bundle size

## Development Workflow

### Local Development

Run both services locally:

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

Frontend defaults to `http://localhost:8000` for API calls.

### Staging Deployment

Use branch previews for testing:

1. Push changes to a feature branch
2. Vercel automatically creates preview deployments
3. Test thoroughly before merging to `main`

### Production Deployment

```bash
# Backend (from backend directory)
vercel --prod

# Frontend (from frontend directory)
vercel --prod
```

Or enable GitHub integration for automatic deployments on main branch.

## Cost Optimization

### Frontend (Next.js)
- **Free tier**: 100 GB bandwidth/month
- **Typical usage**: 1-5 GB/month for medium app

### Backend (FastAPI)
- **Free tier**: 100 GB data transfer/month, 1000 function executions
- **Cost**: $0.50 per million requests after free tier

### Recommendations
1. Use appropriate plan for expected usage
2. Monitor costs in Vercel dashboard
3. Optimize database queries
4. Compress API responses

## Security Checklist

- [ ] Set strong API keys in environment variables
- [ ] Enable HTTPS (automatic with Vercel)
- [ ] Configure CORS properly (test with curl)
- [ ] Validate all input data
- [ ] Use rate limiting on critical endpoints
- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies updated
- [ ] Use environment variables, never hardcode secrets

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Support](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment/vercel)
