"""
Vercel serverless function entry point for FastAPI app.
This file adapts our FastAPI application to work with Vercel's serverless functions.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path so we can import our modules
current_dir = Path(__file__).parent
app_dir = current_dir.parent / "app"
sys.path.insert(0, str(app_dir))

# Import the FastAPI app
from main import app

# Export the app for Vercel
# Vercel will automatically handle ASGI applications
handler = app
