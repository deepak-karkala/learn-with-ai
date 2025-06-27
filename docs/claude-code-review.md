# Claude Code Review Integration

This project integrates Claude Code as a Unix-style utility for automated code review, following the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/common-workflows#use-claude-as-a-unix-style-utility).

## 🔧 Setup

### Prerequisites
- [Claude CLI](https://claude.ai/code) installed and authenticated
- Node.js 18+ (for frontend reviews)
- Python 3.11+ with uv (for backend reviews)

### Environment Setup
Make sure you have the `ANTHROPIC_API_KEY` environment variable set:
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

## 🚀 Usage

### Manual Code Review

#### Full Project Review
```bash
# Review both frontend and backend for general issues
./review-claude.sh full

# Security-focused review of both codebases  
./review-claude.sh security

# Performance review of both codebases
./review-claude.sh performance

# ADK-specific review (backend only)
./review-claude.sh adk
```

#### Frontend-Only Review
```bash
cd frontend

# General frontend review
npm run review:claude

# Security-focused frontend review
npm run review:claude:security

# Performance-focused frontend review  
npm run review:claude:performance
```

#### Backend-Only Review
```bash
cd backend

# General backend review
./review-claude.sh general

# Security-focused backend review
./review-claude.sh security

# Performance review
./review-claude.sh performance

# ADK-specific review
./review-claude.sh adk
```

### Automated GitHub Workflow

The project includes a GitHub Actions workflow (`.github/workflows/claude-code-review.yml`) that automatically runs Claude Code review on pull requests.

#### Setup for GitHub Actions
1. Add `ANTHROPIC_API_KEY` to your repository secrets:
   - Go to repository Settings → Secrets and variables → Actions
   - Add new secret: `ANTHROPIC_API_KEY`

2. The workflow will automatically:
   - Run on PRs to `main` or `develop` branches
   - Perform general, security, and ADK-specific reviews
   - Post results as PR comments
   - Upload review artifacts

## 📋 Review Types

### General Code Review
- **Frontend**: TypeScript errors, React best practices, performance issues, security vulnerabilities, code style
- **Backend**: Python syntax/type hints, FastAPI best practices, security, performance, PEP 8 compliance

### Security Review
- **Frontend**: XSS, CSRF, data exposure, authentication bypasses, input validation
- **Backend**: SQL injection, code injection, authentication bypasses, data exposure, secret leaks

### Performance Review
- **Frontend**: Unnecessary re-renders, bundle size issues, inefficient data fetching, memory leaks
- **Backend**: Inefficient database queries, blocking I/O, memory leaks, poor async/await usage

### ADK-Specific Review (Backend Only)
- Proper ADK patterns and best practices
- Session management implementation
- Streaming implementation correctness
- Error handling in ADK contexts
- Agent configuration validation

## 🛠 Customization

### Modifying Review Prompts

#### Frontend (package.json)
Edit the prompts in `frontend/package.json` under the `scripts` section:
```json
"review:claude": "claude -p 'Your custom prompt here'"
```

#### Backend (review-claude.sh)
Edit prompts in `backend/review-claude.sh`:
```bash
claude -p "Your custom prompt here"
```

### Adding New Review Types

#### Frontend
Add new scripts to `frontend/package.json`:
```json
"review:claude:accessibility": "claude -p 'Review for accessibility issues...'"
```

#### Backend
Add new cases to `backend/review-claude.sh`:
```bash
"accessibility")
    claude -p "Review for accessibility compliance..."
    ;;
```

## 📊 Output Format

Claude Code reviews return results in this format:
```
filename:line_number - issue description
```

Example:
```
src/components/Button.tsx:15 - Missing aria-label for accessibility
backend/app/services/adk_service.py:123 - Potential SQL injection vulnerability
```

## 🔍 Integration with Development Workflow

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
./review-claude.sh security
if [ $? -ne 0 ]; then
    echo "Security review failed. Please address issues before committing."
    exit 1
fi
```

### VS Code Integration
Add to `.vscode/tasks.json`:
```json
{
    "label": "Claude Security Review",
    "type": "shell", 
    "command": "./review-claude.sh security",
    "group": "test"
}
```

### CI/CD Integration
The GitHub workflow can be extended for different CI/CD systems by adapting the script calls and authentication methods.

## 🤖 Best Practices

1. **Run reviews early and often** - Catch issues before they reach production
2. **Customize prompts** - Tailor reviews to your specific project needs
3. **Combine with other tools** - Use alongside ESLint, flake8, security scanners
4. **Review the reviews** - Claude suggestions should be validated by developers
5. **Track patterns** - Look for recurring issues to improve development practices

## 🔐 Security Considerations

- Keep your `ANTHROPIC_API_KEY` secure and rotate regularly
- Review suggestions are sent to Claude AI - avoid reviewing files with secrets
- Use environment-specific configurations for sensitive repositories
- Consider running security-focused reviews more frequently than general reviews

## 📈 Monitoring and Metrics

Track the effectiveness of Claude Code reviews:
- Number of issues caught before production
- Time saved in manual code review
- Developer satisfaction with automated suggestions
- False positive rates for different review types

---

*For more information about Claude Code, visit the [official documentation](https://docs.anthropic.com/en/docs/claude-code).*