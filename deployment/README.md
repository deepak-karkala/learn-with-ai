# Deployment Guide

## Vercel Deployment Strategies

This project supports multiple Vercel deployment strategies to handle the frontend/backend separation.

### Strategy 1: Monorepo Deployment (Recommended)

Deploy both frontend and backend from the same repository using the root `vercel.json`.

**Pros:**
- Single deployment pipeline
- Easier environment management
- Automatic API routing

**Cons:**
- More complex configuration
- Potential for larger deployments

**Setup:**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from project root
vercel

# Set environment variables
vercel env add GOOGLE_CLOUD_PROJECT
vercel env add GOOGLE_API_KEY
# ... add other environment variables
```

### Strategy 2: Separate Projects

Deploy frontend and backend as separate Vercel projects.

**Pros:**
- Independent deployments
- Simpler individual configurations
- Better separation of concerns

**Cons:**
- Need to manage CORS
- Two separate deployments
- API URL configuration required

**Frontend Setup:**
```bash
cd frontend
vercel
```

**Backend Setup:**
```bash
cd backend
vercel
```

### Strategy 3: Hybrid Approach

Frontend on Vercel, Backend elsewhere (Railway, Render, etc.)

**Pros:**
- More flexibility for backend hosting
- Better for complex backend requirements

**Cons:**
- Multiple hosting providers
- More complex deployment pipeline

## Recommended Deployment Flow

### For Development/Testing:
Use **Strategy 1 (Monorepo)** with the root `vercel.json`

### For Production:
Consider **Strategy 2 (Separate Projects)** for better isolation

## Environment Variables

### Frontend Environment Variables:
```bash
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
```

### Backend Environment Variables:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_API_KEY=your-api-key
DATABASE_URL=your-database-url
REDIS_URL=your-redis-url
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
```

## File Structure for Vercel

```
learn-with-ai/
├── vercel.json                 # Root config (Strategy 1)
├── frontend/
│   ├── vercel.json            # Frontend config (Strategy 2)
│   ├── package.json
│   └── ...
├── backend/
│   ├── vercel.json            # Backend config (Strategy 2)
│   ├── api/
│   │   └── index.py           # Vercel serverless entry point
│   ├── app/
│   │   └── main.py            # FastAPI app
│   └── ...
```

## Troubleshooting Common Issues

### 1. Build Failures in Monorepo
- Ensure build commands specify correct directories
- Check that install commands are in the right directory

### 2. API Routes Not Working
- Verify rewrite rules in `vercel.json`
- Check CORS configuration
- Ensure serverless function structure is correct

### 3. Environment Variables
- Use Vercel dashboard to set environment variables
- Prefix frontend env vars with `NEXT_PUBLIC_` for client-side access
- Use `@env_var_name` syntax in vercel.json for references

### 4. Python Dependencies
- Ensure `requirements.txt` or `pyproject.toml` is in correct location
- Verify Python runtime version matches your code

## Testing Deployments

### Local Testing with Vercel CLI:
```bash
# Test frontend
cd frontend
vercel dev

# Test backend  
cd backend
vercel dev

# Test full stack (from root)
vercel dev
```

### Preview Deployments:
Every PR automatically gets a preview deployment for testing.

### Production Deployment:
```bash
vercel --prod
```

## Performance Considerations

- **Cold Starts**: Serverless functions have cold start delays
- **Bundle Size**: Keep frontend bundles optimized
- **Database Connections**: Use connection pooling for databases
- **Caching**: Implement appropriate caching strategies

## Migration Path

If you encounter issues with the monorepo approach:

1. Start with Strategy 1 (Monorepo)
2. If issues arise, migrate to Strategy 2 (Separate projects)
3. Keep both configurations available for flexibility

The separate `vercel.json` files in `/frontend` and `/backend` directories provide fallback options.