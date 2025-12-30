# Vercel Preview Deployment Setup Guide

## 🔍 Current Setup Status

### ✅ **Already Configured**
- Staging deployment workflow (`.github/workflows/staging-deploy.yml`)
- Basic Vercel action configuration
- Root-level `vercel.json` with frontend/backend integration

### ❌ **Missing Components**
- Improved preview URL capture and sharing
- Environment-specific configurations
- Better GitHub integration for preview links

## 🔧 **Required GitHub Secrets**

Navigate to: **Repository Settings → Secrets and variables → Actions**

### **Required Secrets:**
```bash
VERCEL_TOKEN          # ✅ Should already exist
ORG_ID               # ✅ Should already exist  
PROJECT_ID           # ✅ Should already exist
GITHUB_TOKEN         # ✅ Auto-provided by GitHub
```

### **How to Get Missing Values:**

#### **1. Vercel Token** (if missing)
```bash
# Install Vercel CLI
npm i -g vercel

# Login and get token
vercel login
vercel tokens create "GitHub Actions Token"
```

#### **2. Organization ID** (if missing)
```bash
# In your project directory
vercel link
# Copy the orgId from .vercel/project.json
```

#### **3. Project ID** (if missing)
```bash
# In your project directory  
vercel link
# Copy the projectId from .vercel/project.json
```

## 🚀 **Enhanced Staging Workflow**

### **Updated `.github/workflows/staging-deploy.yml`:**

```yaml
name: Staging Deployment

on:
  push:
    branches: [ develop ]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    name: Deploy to Staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Deploy to Vercel Preview
      id: vercel-deploy
      uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        github-token: ${{ secrets.GITHUB_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        working-directory: ./frontend
        scope: ${{ secrets.ORG_ID }}
        # This creates a preview deployment (not production)
        vercel-args: '--confirm'
        # Optional: Custom alias for staging
        alias-domains: |
          staging-{{BRANCH}}.your-domain.com
    
    - name: Get Preview URL
      run: |
        echo "🚀 Preview Deployment Successful!"
        echo "🔗 Preview URL: ${{ steps.vercel-deploy.outputs.preview-url }}"
        echo "📋 Staging Environment Ready for Testing"
    
    - name: Comment with Preview URL
      uses: actions/github-script@v7
      with:
        script: |
          const previewUrl = '${{ steps.vercel-deploy.outputs.preview-url }}';
          const deploymentUrl = previewUrl || 'Check Vercel Dashboard';
          
          console.log(`## 🚀 Staging Deployment Successful!
          
          ### 🔗 Preview Environment
          **Preview URL:** ${deploymentUrl}
          
          ### 🧪 Testing Checklist
          - [ ] UI/UX verification
          - [ ] Feature functionality testing  
          - [ ] API integration testing
          - [ ] Performance validation
          - [ ] Mobile responsiveness
          
          ### 📱 Environment Details
          - **Branch:** develop
          - **Environment:** Staging/Preview
          - **Framework:** Next.js + FastAPI
          - **Deployment Time:** ${new Date().toISOString()}
          
          Ready for manual verification before merging to \`main\`! 🎯`);
```

## 🏗️ **Vercel Project Configuration**

### **1. Vercel Dashboard Settings**

Go to your Vercel project dashboard and configure:

#### **Environment Variables** (per environment)
```bash
# Production Environment
GOOGLE_API_KEY=your_prod_key
GOOGLE_GENAI_USE_VERTEXAI=FALSE
DEBUG=false
NODE_ENV=production

# Preview Environment (staging)
GOOGLE_API_KEY=your_staging_key
GOOGLE_GENAI_USE_VERTEXAI=FALSE  
DEBUG=true
NODE_ENV=preview
```

#### **Git Integration Settings**
```bash
Production Branch: main
Preview Deployments: ✅ Enabled
  - Deploy all branches: ✅ Enabled
  - Deploy only production branch: ❌ Disabled
```

### **2. Custom Domain Setup** (Optional)

If you want predictable staging URLs:

#### **In Vercel Dashboard:**
1. Go to **Project Settings → Domains**
2. Add custom domain: `staging.yourdomain.com`
3. Configure DNS records as instructed

#### **In GitHub Workflow:**
```yaml
alias-domains: |
  staging.yourdomain.com
  develop.yourdomain.com
```

## 📋 **Verification Steps**

### **Test the Setup:**

1. **Create a test branch:**
```bash
git checkout develop
git checkout -b test-staging-deploy
echo "Test staging" > test-file.txt
git add . && git commit -m "test: staging deployment"
git push origin test-staging-deploy
```

2. **Merge to develop:**
```bash
git checkout develop
git merge test-staging-deploy
git push origin develop
```

3. **Check GitHub Actions:**
- Go to **Actions** tab in GitHub
- Verify "Staging Deployment" workflow runs
- Check for preview URL in logs

4. **Verify Vercel Dashboard:**
- Check **Deployments** tab
- Confirm preview deployment exists
- Test the preview URL

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **1. Deployment Fails**
```bash
# Check GitHub Actions logs
# Verify all secrets are set correctly
# Ensure Vercel project is linked properly
```

#### **2. No Preview URL in Output**
```bash
# Add to workflow:
- name: Debug Vercel Output
  run: |
    echo "Vercel outputs: ${{ toJson(steps.vercel-deploy.outputs) }}"
```

#### **3. Environment Variables Not Loading**
```bash
# In Vercel Dashboard:
# Project → Settings → Environment Variables
# Ensure "Preview" environment is configured
```

### **4. Build Failures**
```bash
# Check vercel.json configuration
# Verify build commands work locally
# Check Node.js version compatibility
```

## 🎯 **Expected Results**

After proper setup, when you push to `develop`:

1. **GitHub Actions will:**
   - ✅ Trigger staging deployment workflow
   - ✅ Deploy to Vercel preview environment
   - ✅ Output preview URL in logs
   - ✅ Comment with staging details (if configured)

2. **Vercel will:**
   - ✅ Create preview deployment
   - ✅ Generate unique preview URL
   - ✅ Use preview environment variables
   - ✅ Deploy both frontend and backend

3. **You'll get:**
   - 🔗 **Unique preview URL** for testing
   - 🎭 **Isolated staging environment**
   - 🚀 **Fast deployment** (no redundant CI tests)
   - 📱 **Full stack preview** (frontend + backend)

## 🚀 **Next Steps**

1. **Verify GitHub secrets are set**
2. **Update staging-deploy.yml with enhanced configuration** ✅ (already done)
3. **Configure Vercel environment variables**
4. **Test with a sample deploy to develop**
5. **Verify preview URL generation works**

Once configured, your staging workflow will provide seamless preview deployments for manual testing before production! 🎉