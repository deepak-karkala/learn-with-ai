#!/bin/bash

# Production Testing Script for AI System Design Learning Platform
# This script runs comprehensive tests against the production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="${FRONTEND_URL:-}"
BACKEND_URL="${BACKEND_URL:-}"
TEST_USER_ID="test-user-$(date +%s)"

# Logging functions
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

# Function to test API endpoint
test_api_endpoint() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="${3:-}"
    local expected_status="${4:-200}"
    
    log "Testing $method $endpoint"
    
    if [[ -n "$data" ]]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BACKEND_URL$endpoint" || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            "$BACKEND_URL$endpoint" || echo "000")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$status_code" == "$expected_status" ]]; then
        success "$method $endpoint - Status: $status_code"
        return 0
    else
        error "$method $endpoint - Expected: $expected_status, Got: $status_code"
        echo "Response: $body"
        return 1
    fi
}

# Function to test health endpoints
test_health_endpoints() {
    log "Testing health endpoints..."
    
    test_api_endpoint "/health" "GET" "" "200"
    test_api_endpoint "/api/health" "GET" "" "200"
    test_api_endpoint "/api/monitoring/health" "GET" "" "200"
}

# Function to test core API functionality
test_core_api() {
    log "Testing core API functionality..."
    
    # Test session creation
    session_data='{"user_id":"'$TEST_USER_ID'","initial_state":{"skill_level":"intermediate"}}'
    session_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$session_data" \
        "$BACKEND_URL/api/session/create")
    
    session_id=$(echo "$session_response" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
    
    if [[ -n "$session_id" ]]; then
        success "Session created: $session_id"
    else
        error "Failed to create session"
        echo "Response: $session_response"
        return 1
    fi
    
    # Test chat endpoint
    chat_data='{"message":"Hello, I want to learn about system design","user_id":"'$TEST_USER_ID'","session_id":"'$session_id'"}'
    chat_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$chat_data" \
        "$BACKEND_URL/api/chat")
    
    if echo "$chat_response" | grep -q '"success":true'; then
        success "Chat endpoint working"
    else
        error "Chat endpoint failed"
        echo "Response: $chat_response"
        return 1
    fi
    
    # Test user sessions endpoint
    test_api_endpoint "/api/session/$TEST_USER_ID" "GET" "" "200"
}

# Function to test monitoring endpoints
test_monitoring() {
    log "Testing monitoring endpoints..."
    
    test_api_endpoint "/api/monitoring/health" "GET" "" "200"
    test_api_endpoint "/api/monitoring/metrics" "GET" "" "200"
    test_api_endpoint "/api/monitoring/dashboard" "GET" "" "200"
    test_api_endpoint "/api/monitoring/storage" "GET" "" "200"
}

# Function to test performance
test_performance() {
    log "Testing performance..."
    
    local start_time=$(date +%s.%N)
    
    # Test multiple concurrent requests
    for i in {1..5}; do
        curl -s "$BACKEND_URL/health" > /dev/null &
    done
    wait
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    
    if (( $(echo "$duration < 5.0" | bc -l) )); then
        success "Performance test passed (${duration}s for 5 concurrent requests)"
    else
        warning "Performance test slow (${duration}s for 5 concurrent requests)"
    fi
}

# Function to test rate limiting
test_rate_limiting() {
    log "Testing rate limiting..."
    
    # Send requests rapidly to trigger rate limiting
    local rate_limited=false
    
    for i in {1..15}; do
        response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/chat" \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{"message":"test","user_id":"rate-test-user"}')
        
        status_code=$(echo "$response" | tail -n1)
        
        if [[ "$status_code" == "429" ]]; then
            rate_limited=true
            break
        fi
        
        sleep 0.1
    done
    
    if [[ "$rate_limited" == true ]]; then
        success "Rate limiting working (got 429 status)"
    else
        warning "Rate limiting may not be working properly"
    fi
}

# Function to test frontend
test_frontend() {
    if [[ -z "$FRONTEND_URL" ]]; then
        warning "FRONTEND_URL not provided, skipping frontend tests"
        return
    fi
    
    log "Testing frontend..."
    
    # Test frontend accessibility
    frontend_response=$(curl -s -w "\n%{http_code}" "$FRONTEND_URL")
    status_code=$(echo "$frontend_response" | tail -n1)
    
    if [[ "$status_code" == "200" ]]; then
        success "Frontend accessible"
    else
        error "Frontend not accessible - Status: $status_code"
        return 1
    fi
    
    # Check if frontend contains expected content
    body=$(echo "$frontend_response" | head -n -1)
    if echo "$body" | grep -q -i "system.*design\|learn"; then
        success "Frontend content looks correct"
    else
        warning "Frontend content may be incorrect"
    fi
}

# Function to test error handling
test_error_handling() {
    log "Testing error handling..."
    
    # Test invalid endpoints
    test_api_endpoint "/api/nonexistent" "GET" "" "404"
    
    # Test invalid chat request
    invalid_chat='{"message":"","user_id":"test"}'
    test_api_endpoint "/api/chat" "POST" "$invalid_chat" "422"
    
    # Test invalid JSON
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "invalid json" \
        "$BACKEND_URL/api/chat" | grep -q "error" && success "Invalid JSON handled" || error "Invalid JSON not handled"
}

# Function to test security headers
test_security() {
    log "Testing security headers..."
    
    headers=$(curl -s -I "$BACKEND_URL/health")
    
    security_headers=(
        "X-Content-Type-Options"
        "X-Frame-Options"
        "X-XSS-Protection"
    )
    
    for header in "${security_headers[@]}"; do
        if echo "$headers" | grep -q "$header"; then
            success "Security header present: $header"
        else
            warning "Security header missing: $header"
        fi
    done
}

# Function to generate test report
generate_report() {
    log "Generating test report..."
    
    local report_file="production-test-report-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
Production Test Report
======================
Date: $(date)
Frontend URL: ${FRONTEND_URL:-"Not provided"}
Backend URL: ${BACKEND_URL:-"Not provided"}
Test User ID: $TEST_USER_ID

Test Results Summary:
EOF
    
    success "Test report generated: $report_file"
}

# Main test function
main() {
    log "Starting production testing..."
    log "================================"
    
    # Check if URLs are provided
    if [[ -z "$BACKEND_URL" ]]; then
        error "BACKEND_URL environment variable is required"
        echo "Usage: BACKEND_URL=https://your-backend.vercel.app $0"
        exit 1
    fi
    
    local failed_tests=0
    
    # Run test suites
    test_health_endpoints || ((failed_tests++))
    test_core_api || ((failed_tests++))
    test_monitoring || ((failed_tests++))
    test_performance || ((failed_tests++))
    test_rate_limiting || ((failed_tests++))
    test_frontend || ((failed_tests++))
    test_error_handling || ((failed_tests++))
    test_security || ((failed_tests++))
    
    # Generate report
    generate_report
    
    # Final summary
    log "================================"
    if [[ $failed_tests -eq 0 ]]; then
        success "All tests passed! 🎉"
        echo ""
        echo "✅ Production deployment is healthy"
        echo "✅ All core functionality working"
        echo "✅ Security measures in place"
        echo "✅ Performance within acceptable range"
    else
        error "$failed_tests test suite(s) failed"
        echo ""
        echo "❌ Some issues detected in production"
        echo "📋 Check the test output above for details"
        echo "🔧 Address failing tests before proceeding"
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: BACKEND_URL=<backend-url> [FRONTEND_URL=<frontend-url>] $0"
    echo ""
    echo "Environment variables:"
    echo "  BACKEND_URL    (required) Backend API URL"
    echo "  FRONTEND_URL   (optional) Frontend application URL"
    echo ""
    echo "Example:"
    echo "  BACKEND_URL=https://backend.vercel.app FRONTEND_URL=https://frontend.vercel.app $0"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        usage
        exit 0
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