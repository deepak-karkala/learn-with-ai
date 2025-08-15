import json
import os
import time
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers based on environment"""
        # In production, only allow specific origins
        allowed_origins = [
            "https://frontend-lua5my5jr-dkarkala01-gmailcoms-projects.vercel.app",
            "https://learn-with-ai.vercel.app",  # Production frontend domain
            "http://localhost:3000",  # For local development
        ]

        origin = self.headers.get("Origin", "")
        if origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)

        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Credentials", "true")

    def _check_service_health(self):
        """Check the health of various services"""
        services = {}
        
        # Check FastAPI/Backend
        services["api"] = "running"
        
        # Check Google ADK configuration
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if google_api_key or google_cloud_project:
            services["google_adk"] = "configured"
        else:
            services["google_adk"] = "not_configured"
        
        # Check OpenAI configuration
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            services["openai"] = "configured"
        else:
            services["openai"] = "not_configured"
            
        # Check Database configuration
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            services["database"] = "configured"
        else:
            services["database"] = "not_configured"
            
        # Check Redis configuration
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            services["redis"] = "configured"
        else:
            services["redis"] = "not_configured"
            
        # Check Google Cloud Storage
        gcs_bucket = os.getenv("GCS_BUCKET_NAME")
        if gcs_bucket:
            services["cloud_storage"] = "configured"
        else:
            services["cloud_storage"] = "not_configured"
            
        return services

    def do_GET(self):
        start_time = time.time()
        
        try:
            services = self._check_service_health()
            
            # Determine overall health status
            critical_services = ["api", "google_adk"]
            health_status = "healthy"
            
            for service in critical_services:
                if services.get(service) not in ["running", "configured"]:
                    health_status = "degraded"
                    break
            
            response = {
                "status": health_status,
                "message": "Production API Health Check",
                "version": "1.0.0",
                "timestamp": int(time.time()),
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "services": services,
                "uptime": "healthy"
            }
            
            status_code = 200 if health_status == "healthy" else 503
            
        except Exception as e:
            response = {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "version": "1.0.0",
                "timestamp": int(time.time()),
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "services": {},
                "uptime": "error"
            }
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
        return
