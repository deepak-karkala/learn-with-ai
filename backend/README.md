# AI System Design Learning Platform - Backend

FastAPI backend with Google ADK integration for the AI System Design Learning Platform.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Installing uv

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

## Setup

1. **Initialize the project with uv:**
   ```bash
   cd backend
   uv sync
   ```

2. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.template .env
   # Edit .env with your actual values
   ```

## Development

### Running the server

**Option 1: Using uv run (recommended)**
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2: Using the project script**
```bash
uv run dev
```

**Option 3: Traditional way (after activating venv)**
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_main.py
```

### Code Quality

```bash
# Format code
uv run black app/

# Sort imports
uv run isort app/

# Lint code
uv run flake8 app/

# Type checking
uv run mypy app/

# Run all quality checks
uv run black app/ && uv run isort app/ && uv run flake8 app/ && uv run mypy app/
```

### Adding Dependencies

```bash
# Add production dependency
uv add fastapi

# Add development dependency
uv add --dev pytest

# Add with version constraint
uv add "fastapi>=0.104.1"
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── agents/              # ADK agent definitions
│   ├── api/                 # FastAPI route handlers
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic services
│   ├── tools/               # ADK custom tools
│   └── callbacks/           # ADK callbacks
├── tests/                   # Test files
├── pyproject.toml          # Project configuration and dependencies
├── .env.template           # Environment variables template
└── README.md               # This file
```

## Environment Variables

Key environment variables (see `.env.template`):

```bash
# Google ADK Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_API_KEY=your-api-key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
JWT_SECRET=your-jwt-secret-here
```

## Deployment

The backend is designed to deploy on Vercel as serverless functions.

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're in the virtual environment
   ```bash
   source .venv/bin/activate
   ```

2. **Dependencies not found**: Sync dependencies
   ```bash
   uv sync
   ```

3. **Port already in use**: Change the port
   ```bash
   uv run uvicorn app.main:app --reload --port 8001
   ```

### Development Tips

- Use `uv run` prefix for all commands to ensure proper environment
- Keep dependencies in `pyproject.toml` updated
- Run tests before committing changes
- Use type hints for better code quality