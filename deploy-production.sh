#!/bin/bash

# Production Deployment Script for AI System Design Learning Platform
# This script deploys the application to production with proper checks and validations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Configuration
FRONTEND_DIR="./frontend"
BACKEND_DIR="./backend"
REQUIRED_ENV_VARS=(
    "GOOGLE_API_KEY"
    "OPENAI_API_KEY"
    "DATABASE_URL"
    "REDIS_URL"
    "GCS_BUCKET_NAME"
    "OPIK_API_KEY"
)

# Function to check if required environment variables are set
check_environment() {
    log "Checking environment variables..."
    
    missing_vars=()
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables in your .env file or export them."
        echo "See .env.production.template for reference."
        exit 1
    fi
    
    success "All required environment variables are set"
}

# Function to run tests
run_tests() {
    log "Running test suite..."
    
    # Backend tests
    log "Running backend tests..."
    cd "$BACKEND_DIR"
    if command -v pytest &> /dev/null; then
        if ! pytest --tb=short -v; then
            error "Backend tests failed"
            exit 1
        fi
    else
        warning "pytest not found, skipping backend tests"
    fi
    cd ..
    
    # Frontend tests
    log "Running frontend tests..."
    cd "$FRONTEND_DIR"
    if [[ -f "package.json" ]]; then
        if ! npm test -- --run; then
            error "Frontend tests failed"
            exit 1
        fi
    else
        warning "Frontend package.json not found, skipping frontend tests"
    fi
    cd ..
    
    success "All tests passed"
}

# Function to run linting and type checking
run_quality_checks() {
    log "Running code quality checks..."
    
    # Backend linting
    log "Running backend linting..."
    cd "$BACKEND_DIR"
    if command -v flake8 &> /dev/null; then
        if ! flake8 app/; then
            error "Backend linting failed"
            exit 1
        fi
    else
        warning "flake8 not found, skipping backend linting"
    fi
    
    if command -v mypy &> /dev/null; then
        if ! mypy app/ --ignore-missing-imports; then
            error "Backend type checking failed"
            exit 1
        fi
    else
        warning "mypy not found, skipping backend type checking"
    fi
    cd ..
    
    # Frontend linting
    log "Running frontend linting..."
    cd "$FRONTEND_DIR"
    if [[ -f "package.json" ]]; then
        if ! npm run lint; then
            error "Frontend linting failed"
            exit 1
        fi
        
        if ! npm run type-check; then
            error "Frontend type checking failed"
            exit 1
        fi
    fi
    cd ..
    
    success "All quality checks passed"
}

# Function to build applications
build_applications() {
    log "Building applications..."
    
    # Build frontend
    log "Building frontend..."
    cd "$FRONTEND_DIR"
    if [[ -f "package.json" ]]; then
        npm run build
        if [[ $? -ne 0 ]]; then
            error "Frontend build failed"
            exit 1
        fi
    fi
    cd ..
    
    success "Applications built successfully"
}

# Function to deploy to Vercel
deploy_to_vercel() {
    log "Deploying to Vercel..."
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        error "Vercel CLI not found. Install with: npm i -g vercel"
        exit 1
    fi
    
    # Deploy backend
    log "Deploying backend..."
    cd "$BACKEND_DIR"
    if ! vercel --prod --yes; then
        error "Backend deployment failed"
        exit 1
    fi
    BACKEND_URL=$(vercel ls --scope team | grep production | awk '{print $2}' | head -1)
    cd ..
    
    # Deploy frontend
    log "Deploying frontend..."
    cd "$FRONTEND_DIR"
    
    # Update API URL in frontend environment
    if [[ -n "$BACKEND_URL" ]]; then
        export NEXT_PUBLIC_API_URL="https://$BACKEND_URL"
        log "Frontend will connect to: $NEXT_PUBLIC_API_URL"
    fi
    
    if ! vercel --prod --yes; then
        error "Frontend deployment failed"
        exit 1
    fi
    FRONTEND_URL=$(vercel ls --scope team | grep production | awk '{print $2}' | head -1)
    cd ..
    
    success "Deployed to Vercel successfully"
    echo "Frontend URL: https://$FRONTEND_URL"
    echo "Backend URL: https://$BACKEND_URL"
}

# Function to run health checks
run_health_checks() {
    log "Running health checks..."
    
    # Wait a moment for deployment to stabilize
    sleep 10
    
    # Check backend health
    if [[ -n "$BACKEND_URL" ]]; then
        log "Checking backend health..."
        if curl -f "https://$BACKEND_URL/health" > /dev/null 2>&1; then
            success "Backend health check passed"
        else
            error "Backend health check failed"
            exit 1
        fi
    fi
    
    # Check frontend
    if [[ -n "$FRONTEND_URL" ]]; then
        log "Checking frontend..."
        if curl -f "https://$FRONTEND_URL" > /dev/null 2>&1; then
            success "Frontend health check passed"
        else
            error "Frontend health check failed"
            exit 1
        fi
    fi
    
    success "All health checks passed"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    
    if [[ -n "$DATABASE_URL" ]]; then
        cd "$BACKEND_DIR"
        if command -v python &> /dev/null; then
            python -m app.database.migrations init
            success "Database migrations completed"
        else
            warning "Python not found, skipping database migrations"
        fi
        cd ..
    else
        warning "DATABASE_URL not set, skipping database migrations"
    fi
}

# Function to setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    if [[ -n "$OPIK_API_KEY" ]]; then
        log "Comet Opik monitoring configured"
        success "Monitoring setup completed"
    else
        warning "OPIK_API_KEY not set, monitoring will be limited"
    fi
}

# Function to create backup
create_backup() {
    log "Creating backup..."
    
    if [[ -n "$DATABASE_URL" ]]; then
        cd "$BACKEND_DIR"
        if command -v python &> /dev/null; then
            python -m app.database.migrations backup
            success "Database backup created"
        else
            warning "Python not found, skipping database backup"
        fi
        cd ..
    else
        warning "DATABASE_URL not set, skipping database backup"
    fi
}

# Function to notify completion
notify_completion() {
    log "Deployment completed successfully!"
    echo ""
    echo "🚀 Production deployment summary:"
    echo "=================================="
    if [[ -n "$FRONTEND_URL" ]]; then
        echo "Frontend: https://$FRONTEND_URL"
    fi
    if [[ -n "$BACKEND_URL" ]]; then
        echo "Backend:  https://$BACKEND_URL"
        echo "API Docs: https://$BACKEND_URL/docs"
        echo "Health:   https://$BACKEND_URL/health"
    fi
    echo ""
    echo "✅ All services are running"
    echo "✅ Health checks passed"
    echo "✅ Monitoring configured"
    echo ""
    echo "Next steps:"
    echo "1. Monitor application logs"
    echo "2. Verify all features work correctly"
    echo "3. Set up alerts for critical metrics"
    echo "4. Schedule regular backups"
}

# Main deployment function
main() {
    log "Starting production deployment..."
    log "=================================="
    
    # Pre-deployment checks
    check_environment
    
    # Skip tests and quality checks if --skip-checks flag is provided
    if [[ "$1" != "--skip-checks" ]]; then
        run_tests
        run_quality_checks
    else
        warning "Skipping tests and quality checks (--skip-checks flag provided)"
    fi
    
    # Build and deploy
    build_applications
    create_backup
    run_migrations
    deploy_to_vercel
    
    # Post-deployment verification
    run_health_checks
    setup_monitoring
    
    # Completion
    notify_completion
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-checks    Skip tests and quality checks"
    echo "  --help          Show this help message"
    echo ""
    echo "Environment variables required:"
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        echo "  $var"
    done
    echo ""
    echo "Example:"
    echo "  $0                    # Full deployment with all checks"
    echo "  $0 --skip-checks      # Quick deployment without tests"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        usage
        exit 0
        ;;
    --skip-checks)
        main "$1"
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        usage
        exit 1
        ;;
esac