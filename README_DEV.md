# Learn With AI

AI-powered learning platform for system design interviews with interactive AI tutoring, real-time whiteboard feedback, and comprehensive progress tracking.

## 🚀 Status: Production-Ready CI/CD
Comprehensive workflow suite with enterprise-grade testing and deployment automation.

## 🤖 Automated Code Review

This project includes Claude Code integration for automated code review on pull requests and local development.

### Quick Review Commands
```bash
# Complete project review
./review-claude.sh full

# Security audit  
./review-claude.sh security

# ADK-specific review
./review-claude.sh adk
```

See [docs/claude-code-review.md](./docs/claude-code-review.md) for detailed documentation.

## 🔄 Development Workflow

This project follows a comprehensive CI/CD workflow with automated testing, code review, and deployment. Here's the complete process from feature development to production:

### 📋 Workflow Overview

```
Feature Branch → Pull Request → Code Review → Staging → Production
     ↓              ↓              ↓           ↓          ↓
  Local Dev    → CI Tests     → Claude      → Preview   → Main
                 + Linting      Review        Deploy     Deploy
```

### 🚀 Step-by-Step Process

#### 1. **Feature Development** (Local)
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/issue-X-description

# Make your changes...
# Run local tests and reviews before committing
./review-claude.sh security  # Quick security check
npm test                     # Run tests locally
```

#### 2. **Commit & Push** 
```bash
# Commit changes
git add .
git commit -m "feat: implement feature X for issue #Y"
git push origin feature/issue-X-description
```

#### 3. **Pull Request Creation**
When you push to a feature branch and create a PR to `main`, the following are **automatically triggered**:

##### 🔍 **Continuous Integration** (`.github/workflows/ci.yml`)
- **Frontend CI**:
  - Node.js 18 setup
  - Dependencies installation (`npm ci`)
  - ESLint linting (`npm run lint`)
  - Jest tests (`npm test`)
  - Production build (`npm run build`)

- **Backend CI**:
  - Python 3.11 setup with uv package manager
  - Virtual environment creation and sync
  - Code linting (flake8, black, isort)
  - Pytest test suite with coverage
  - MyPy type checking

##### 🤖 **Claude Code Review** (`.github/workflows/claude-code-review.yml`)
- **General Review**: TypeScript, React patterns, Python syntax, FastAPI best practices
- **Security Review**: XSS, CSRF, SQL injection, authentication issues, secret exposure
- **ADK-Specific Review**: Streaming patterns, session management, agent configuration
- **Results**: Posted as PR comments with actionable feedback

##### 💬 **Interactive Claude** (`.github/workflows/claude.yml`)
- Responds to `@claude` mentions in PR comments
- Can answer questions about code changes
- Provides on-demand code analysis and suggestions

#### 4. **Code Review Process**
- **Automated**: CI tests must pass ✅
- **Automated**: Claude Code Review provides feedback 🤖
- **Manual**: Team members review and approve 👥
- **Interactive**: Use `@claude` for specific questions

#### 5. **Merge to Develop** (Optional Staging)
```bash
# If using develop branch for staging
git checkout develop
git merge feature/issue-X-description
git push origin develop
```

##### 🚀 **Staging Deployment** (`.github/workflows/staging-deploy.yml`)
When code is pushed to `develop` branch:
- **Direct Vercel staging deployment** (no redundant CI tests)
- Staging environment available for manual testing
- Preview URL generated for stakeholder review
- Focus on integration and UI/UX verification

#### 6. **Production Deployment**
```bash
# Merge develop to main (or feature branch directly to main)
git checkout main
git merge develop  # or merge PR in GitHub UI
git push origin main
```

##### 🌟 **Production Deployment**
When code is merged to `main`:
- Full CI test suite runs
- **Automatic Vercel production deployment**
- Production environment updated
- Health checks verified

### 🔧 **Required Setup**

#### Repository Secrets (GitHub Settings → Secrets)
```bash
ANTHROPIC_API_KEY     # For Claude Code Review
VERCEL_TOKEN          # For Vercel deployments  
ORG_ID               # Vercel organization ID
PROJECT_ID           # Vercel project ID
```

#### Branch Protection Rules (Recommended)
```bash
main:
  - Require PR reviews (1+ approvals)
  - Require status checks (CI tests)
  - Require up-to-date branches
  - Restrict pushes to main

develop:
  - Require status checks (CI tests)
  - Allow fast-forward merges
```

### 🛡️ **Quality Gates**

#### ✅ **Before Merge** (Required)
- [ ] All CI tests pass (frontend + backend)
- [ ] Code coverage maintained (>90%)
- [ ] Claude Code Review feedback addressed
- [ ] Manual code review approved
- [ ] No linting or type errors

#### 🔍 **Staging Verification** (Manual)
- [ ] Preview deployment successful
- [ ] Feature works as expected
- [ ] No UI/UX regressions
- [ ] API endpoints functional
- [ ] Performance acceptable

#### 🚀 **Production Readiness**
- [ ] Staging tests passed
- [ ] Security review clean
- [ ] Database migrations ready (if any)
- [ ] Monitoring alerts configured

### 🔄 **Common Workflows**

#### **Hotfix Process**
```bash
# For urgent production fixes
git checkout main
git checkout -b hotfix/critical-fix
# Make minimal changes
# Create PR to main (bypasses develop)
# Deploy immediately after approval
```

#### **Release Process**
```bash
# Create release branch from develop
git checkout -b release/v1.2.0
# Final testing and bug fixes
# Merge to main and develop
# Tag release: git tag v1.2.0
```

#### **Feature Flag Deployment**
```bash
# Deploy features behind flags
# Test in production with limited users
# Gradually roll out feature
# Remove flag after full deployment
```

### 📊 **Monitoring & Alerts**

#### **Deployment Status**
- Vercel deployment status in PR comments
- Health check endpoints monitored
- Error tracking with alerts

#### **Code Quality Metrics**
- Test coverage reports in PRs
- Claude Code Review trends
- Performance impact analysis

### 🆘 **Troubleshooting**

#### **CI Failures**
```bash
# Check logs in GitHub Actions tab
# Run tests locally: npm test / pytest
# Verify linting: npm run lint / flake8
# Check build: npm run build
```

#### **Deployment Issues**
```bash
# Check Vercel dashboard
# Verify environment variables
# Review deployment logs
# Test API endpoints manually
```

#### **Claude Review Issues**
```bash
# Verify ANTHROPIC_API_KEY secret
# Check quota limits
# Review custom prompts
# Manual review as fallback
```

---

## 📚 Documentation

Comprehensive project documentation is available in the [`docs/`](./docs/) directory:

- **[Development Workflow](./docs/development-workflow.md)** - Complete CI/CD process guide
- **[Claude Code Review](./docs/claude-code-review.md)** - Automated code review setup
- **[Vercel Preview Setup](./docs/vercel-preview-setup.md)** - Staging deployment configuration
- **[Documentation Index](./docs/README.md)** - Complete documentation directory

---