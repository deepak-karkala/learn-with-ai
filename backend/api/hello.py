from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers based on environment"""
        # In production, only allow specific origins
        allowed_origins = [
            'https://frontend-lua5my5jr-dkarkala01-gmailcoms-projects.vercel.app',
            'http://localhost:3000'  # For local development
        ]
        
        origin = self.headers.get('Origin', '')
        if origin in allowed_origins:
            self.send_header('Access-Control-Allow-Origin', origin)
        
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        
        response = {
            "message": "AI System Design Learning Platform API",
            "status": "healthy",
            "version": "0.1.0"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
        return