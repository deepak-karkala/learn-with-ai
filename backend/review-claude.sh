#!/bin/bash
# Claude Code review scripts for Python/FastAPI backend

case "$1" in
    "general")
        claude -p "You are a code reviewer for a Python/FastAPI project. Review the git diff vs main branch and report any issues related to: 1) Python syntax/type hints, 2) FastAPI best practices, 3) Security vulnerabilities, 4) Performance issues, 5) Code style (PEP 8). Format: filename:line - issue description. Be concise and actionable."
        ;;
    "security")
        claude -p "You are a security-focused code reviewer for Python/FastAPI. Analyze the git diff vs main for: SQL injection, code injection, authentication bypasses, data exposure, input validation, secret leaks. Report filename:line - security issue. Only report actual security concerns."
        ;;
    "performance")
        claude -p "You are a performance-focused code reviewer for Python/FastAPI. Analyze git diff vs main for: inefficient database queries, blocking I/O, memory leaks, unnecessary computations, poor async/await usage. Report filename:line - performance issue."
        ;;
    "adk")
        claude -p "You are a code reviewer specialized in Google ADK (Agent Development Kit). Review the git diff vs main for: proper ADK patterns, session management, streaming implementation, error handling, agent configuration. Report filename:line - ADK-specific issue."
        ;;
    *)
        echo "Usage: $0 {general|security|performance|adk}"
        echo ""
        echo "Examples:"
        echo "  ./review-claude.sh general     - General code review"
        echo "  ./review-claude.sh security    - Security-focused review"
        echo "  ./review-claude.sh performance - Performance review"
        echo "  ./review-claude.sh adk         - ADK-specific review"
        exit 1
        ;;
esac