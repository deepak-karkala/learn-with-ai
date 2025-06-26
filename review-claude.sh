#!/bin/bash
# Claude Code review scripts for the entire project

case "$1" in
    "full")
        echo "🔍 Running full project review with Claude Code..."
        echo ""
        echo "📱 Frontend Review:"
        cd frontend && npm run review:claude
        echo ""
        echo "🐍 Backend Review:"
        cd ../backend && ./review-claude.sh general
        ;;
    "security")
        echo "🔒 Running security review with Claude Code..."
        echo ""
        echo "📱 Frontend Security:"
        cd frontend && npm run review:claude:security
        echo ""
        echo "🐍 Backend Security:"
        cd ../backend && ./review-claude.sh security
        ;;
    "performance")
        echo "⚡ Running performance review with Claude Code..."
        echo ""
        echo "📱 Frontend Performance:"
        cd frontend && npm run review:claude:performance
        echo ""
        echo "🐍 Backend Performance:"
        cd ../backend && ./review-claude.sh performance
        ;;
    "adk")
        echo "🤖 Running ADK-specific review with Claude Code..."
        cd backend && ./review-claude.sh adk
        ;;
    *)
        echo "Claude Code Review Helper"
        echo "========================"
        echo ""
        echo "Usage: $0 {full|security|performance|adk}"
        echo ""
        echo "Options:"
        echo "  full        - Review both frontend and backend for general issues"
        echo "  security    - Security-focused review of both codebases"
        echo "  performance - Performance review of both codebases"
        echo "  adk         - ADK-specific review (backend only)"
        echo ""
        echo "Examples:"
        echo "  ./review-claude.sh full        # Complete project review"
        echo "  ./review-claude.sh security    # Security audit"
        echo "  ./review-claude.sh adk         # ADK implementation review"
        echo ""
        echo "Individual component reviews:"
        echo "  cd frontend && npm run review:claude"
        echo "  cd backend && ./review-claude.sh general"
        exit 1
        ;;
esac