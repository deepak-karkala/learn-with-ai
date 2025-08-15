"""
Google Cloud Storage service for storing artifacts, whiteboards, and session data.
"""

import base64
import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, BinaryIO, Any
from urllib.parse import urlparse

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound, GoogleCloudError
except ImportError:
    storage = None
    NotFound = Exception
    GoogleCloudError = Exception
try:
    from google.oauth2 import service_account
except ImportError:
    service_account = None

logger = logging.getLogger(__name__)


class StorageService:
    """Google Cloud Storage service for artifact management."""
    
    def __init__(self):
        self._client: Optional[Any] = None
        self._bucket: Optional[Any] = None
        self._bucket_name: Optional[str] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Google Cloud Storage client."""
        try:
            if storage is None:
                logger.warning("Google Cloud Storage not available, storage features will be disabled")
                return
                
            self._bucket_name = os.getenv("GCS_BUCKET_NAME")
            if not self._bucket_name:
                logger.warning("GCS_BUCKET_NAME not configured, storage features will be disabled")
                return
            
            # Initialize client with credentials
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            
            if credentials_path and os.path.exists(credentials_path):
                # Use service account credentials file
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                self._client = storage.Client(credentials=credentials, project=project_id)
            elif project_id:
                # Use default credentials (good for Cloud Run, App Engine, etc.)
                self._client = storage.Client(project=project_id)
            else:
                # Try default authentication
                self._client = storage.Client()
            
            # Get bucket reference
            self._bucket = self._client.bucket(self._bucket_name)
            
            # Test bucket access
            if self._bucket.exists():
                logger.info(f"Connected to GCS bucket: {self._bucket_name}")
            else:
                logger.error(f"GCS bucket {self._bucket_name} does not exist")
                self._client = None
                self._bucket = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage: {e}")
            self._client = None
            self._bucket = None
    
    def is_available(self) -> bool:
        """Check if Google Cloud Storage is available."""
        return self._client is not None and self._bucket is not None
    
    def _generate_file_path(
        self, 
        artifact_type: str, 
        user_id: str, 
        session_id: str,
        file_extension: str = ""
    ) -> str:
        """Generate a structured file path for artifacts."""
        # Create hierarchical structure: artifacts/{type}/{year}/{month}/{user_id}/{session_id}/{filename}
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        filename = f"{uuid.uuid4()}{file_extension}"
        
        return f"artifacts/{artifact_type}/{year}/{month}/{user_id}/{session_id}/{filename}"
    
    def _calculate_file_hash(self, data: Union[bytes, str]) -> str:
        """Calculate SHA-256 hash of file data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    # =============================================================================
    # File Upload Operations
    # =============================================================================
    
    def upload_file(
        self,
        data: Union[bytes, str, BinaryIO],
        artifact_type: str,
        user_id: str,
        session_id: str,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Cloud Storage.
        
        Returns:
            Dict with upload information including URL, path, and metadata
        """
        if not self.is_available():
            raise RuntimeError("Google Cloud Storage is not available")
        
        try:
            # Determine file extension
            file_extension = ""
            if filename:
                file_extension = os.path.splitext(filename)[1]
            elif content_type:
                if content_type.startswith("image/png"):
                    file_extension = ".png"
                elif content_type.startswith("image/jpeg"):
                    file_extension = ".jpg"
                elif content_type.startswith("application/json"):
                    file_extension = ".json"
            
            # Generate file path
            file_path = self._generate_file_path(artifact_type, user_id, session_id, file_extension)
            
            # Prepare data
            if isinstance(data, str):
                file_data = data.encode('utf-8')
            elif hasattr(data, 'read'):
                file_data = data.read()
            else:
                file_data = data
            
            # Calculate file hash for deduplication
            file_hash = self._calculate_file_hash(file_data)
            
            # Create blob
            blob = self._bucket.blob(file_path)
            
            # Set metadata
            blob_metadata = {
                "artifact_type": artifact_type,
                "user_id": user_id,
                "session_id": session_id,
                "file_hash": file_hash,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "original_filename": filename or ""
            }
            
            if metadata:
                blob_metadata.update(metadata)
            
            blob.metadata = blob_metadata
            
            # Set content type
            if content_type:
                blob.content_type = content_type
            
            # Upload file
            blob.upload_from_string(file_data, content_type=content_type)
            
            # Generate signed URL for access
            signed_url = blob.generate_signed_url(
                expiration=datetime.utcnow() + timedelta(hours=24),
                method="GET"
            )
            
            logger.info(f"File uploaded successfully: {file_path}")
            
            return {
                "success": True,
                "file_path": file_path,
                "public_url": f"gs://{self._bucket_name}/{file_path}",
                "signed_url": signed_url,
                "file_hash": file_hash,
                "file_size": len(file_data),
                "content_type": content_type,
                "metadata": blob_metadata
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_png_from_base64(
        self,
        base64_data: str,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Upload a PNG image from base64 data."""
        try:
            # Remove data URL prefix if present
            if base64_data.startswith("data:image/png;base64,"):
                base64_data = base64_data.split(",", 1)[1]
            
            # Decode base64 data
            png_data = base64.b64decode(base64_data)
            
            return self.upload_file(
                data=png_data,
                artifact_type="whiteboard",
                user_id=user_id,
                session_id=session_id,
                filename="whiteboard.png",
                content_type="image/png",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error uploading PNG from base64: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_json_data(
        self,
        json_data: Dict,
        artifact_type: str,
        user_id: str,
        session_id: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Upload JSON data as an artifact."""
        import json
        
        try:
            json_string = json.dumps(json_data, indent=2)
            
            return self.upload_file(
                data=json_string,
                artifact_type=artifact_type,
                user_id=user_id,
                session_id=session_id,
                filename=filename or f"{artifact_type}.json",
                content_type="application/json",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error uploading JSON data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =============================================================================
    # File Download Operations
    # =============================================================================
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """Download a file from Google Cloud Storage."""
        if not self.is_available():
            return None
        
        try:
            blob = self._bucket.blob(file_path)
            if not blob.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            return blob.download_as_bytes()
            
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            return None
    
    def download_as_text(self, file_path: str) -> Optional[str]:
        """Download a file as text."""
        data = self.download_file(file_path)
        if data:
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError as e:
                logger.error(f"Error decoding file as text: {e}")
                return None
        return None
    
    def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Google Cloud Storage."""
        if not self.is_available():
            return None
        
        try:
            blob = self._bucket.blob(file_path)
            if not blob.exists():
                return None
            
            # Reload to get fresh metadata
            blob.reload()
            
            return {
                "file_path": file_path,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "metadata": blob.metadata or {},
                "md5_hash": blob.md5_hash,
                "etag": blob.etag
            }
            
        except Exception as e:
            logger.error(f"Error getting file metadata {file_path}: {e}")
            return None
    
    def generate_signed_url(
        self, 
        file_path: str, 
        expiration_hours: int = 24,
        method: str = "GET"
    ) -> Optional[str]:
        """Generate a signed URL for file access."""
        if not self.is_available():
            return None
        
        try:
            blob = self._bucket.blob(file_path)
            
            signed_url = blob.generate_signed_url(
                expiration=datetime.utcnow() + timedelta(hours=expiration_hours),
                method=method
            )
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {file_path}: {e}")
            return None
    
    # =============================================================================
    # File Management Operations
    # =============================================================================
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Google Cloud Storage."""
        if not self.is_available():
            return False
        
        try:
            blob = self._bucket.blob(file_path)
            if blob.exists():
                blob.delete()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def list_files(
        self, 
        prefix: str = "", 
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List files in the bucket with optional prefix filter."""
        if not self.is_available():
            return []
        
        try:
            blobs = self._bucket.list_blobs(prefix=prefix, max_results=max_results)
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "created": blob.time_created.isoformat() if blob.time_created else None,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "metadata": blob.metadata or {}
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files with prefix {prefix}: {e}")
            return []
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """Copy a file within the bucket."""
        if not self.is_available():
            return False
        
        try:
            source_blob = self._bucket.blob(source_path)
            if not source_blob.exists():
                logger.error(f"Source file not found: {source_path}")
                return False
            
            destination_blob = self._bucket.blob(destination_path)
            destination_blob.rewrite(source_blob)
            
            logger.info(f"File copied from {source_path} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file from {source_path} to {destination_path}: {e}")
            return False
    
    # =============================================================================
    # Session Artifact Management
    # =============================================================================
    
    def store_session_artifacts(
        self,
        session_id: str,
        user_id: str,
        artifacts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store all session artifacts in a single operation."""
        results = {}
        
        try:
            # Store conversation history
            if "conversation_history" in artifacts:
                conv_result = self.upload_json_data(
                    json_data=artifacts["conversation_history"],
                    artifact_type="conversation",
                    user_id=user_id,
                    session_id=session_id,
                    filename="conversation_history.json"
                )
                results["conversation"] = conv_result
            
            # Store whiteboard PNGs
            if "whiteboards" in artifacts:
                whiteboard_results = []
                for i, whiteboard_data in enumerate(artifacts["whiteboards"]):
                    wb_result = self.upload_png_from_base64(
                        base64_data=whiteboard_data,
                        user_id=user_id,
                        session_id=session_id,
                        metadata={"whiteboard_index": str(i)}
                    )
                    whiteboard_results.append(wb_result)
                results["whiteboards"] = whiteboard_results
            
            # Store assessment results
            if "assessments" in artifacts:
                assess_result = self.upload_json_data(
                    json_data=artifacts["assessments"],
                    artifact_type="assessment",
                    user_id=user_id,
                    session_id=session_id,
                    filename="assessments.json"
                )
                results["assessments"] = assess_result
            
            # Store session state
            if "session_state" in artifacts:
                state_result = self.upload_json_data(
                    json_data=artifacts["session_state"],
                    artifact_type="session_state",
                    user_id=user_id,
                    session_id=session_id,
                    filename="session_state.json"
                )
                results["session_state"] = state_result
            
            return {
                "success": True,
                "session_id": session_id,
                "artifacts_stored": results
            }
            
        except Exception as e:
            logger.error(f"Error storing session artifacts: {e}")
            return {
                "success": False,
                "error": str(e),
                "partial_results": results
            }
    
    def retrieve_session_artifacts(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Retrieve all artifacts for a session."""
        try:
            # List all files for this session
            session_prefix = f"artifacts"
            session_files = []
            
            # Get all files and filter by session_id in metadata
            all_files = self.list_files(prefix=session_prefix)
            
            for file_info in all_files:
                file_metadata = self.get_file_metadata(file_info["name"])
                if (file_metadata and 
                    file_metadata.get("metadata", {}).get("session_id") == session_id and
                    file_metadata.get("metadata", {}).get("user_id") == user_id):
                    session_files.append(file_info["name"])
            
            # Download and categorize artifacts
            artifacts = {}
            
            for file_path in session_files:
                file_metadata = self.get_file_metadata(file_path)
                if not file_metadata:
                    continue
                
                artifact_type = file_metadata.get("metadata", {}).get("artifact_type", "unknown")
                
                if artifact_type == "conversation":
                    data = self.download_as_text(file_path)
                    if data:
                        import json
                        artifacts["conversation_history"] = json.loads(data)
                
                elif artifact_type == "whiteboard":
                    # Return signed URL for whiteboard images
                    signed_url = self.generate_signed_url(file_path)
                    if "whiteboards" not in artifacts:
                        artifacts["whiteboards"] = []
                    artifacts["whiteboards"].append({
                        "file_path": file_path,
                        "url": signed_url,
                        "metadata": file_metadata["metadata"]
                    })
                
                elif artifact_type == "assessment":
                    data = self.download_as_text(file_path)
                    if data:
                        import json
                        artifacts["assessments"] = json.loads(data)
                
                elif artifact_type == "session_state":
                    data = self.download_as_text(file_path)
                    if data:
                        import json
                        artifacts["session_state"] = json.loads(data)
            
            return {
                "success": True,
                "session_id": session_id,
                "artifacts": artifacts
            }
            
        except Exception as e:
            logger.error(f"Error retrieving session artifacts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =============================================================================
    # Cleanup Operations
    # =============================================================================
    
    def cleanup_old_artifacts(self, days_old: int = 90) -> Dict[str, Any]:
        """Clean up artifacts older than specified days."""
        if not self.is_available():
            return {"success": False, "error": "Storage not available"}
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_files = []
            total_size_freed = 0
            
            # List all artifacts
            artifacts = self.list_files(prefix="artifacts/")
            
            for file_info in artifacts:
                if file_info["created"]:
                    created_date = datetime.fromisoformat(file_info["created"].replace('Z', '+00:00'))
                    if created_date < cutoff_date:
                        if self.delete_file(file_info["name"]):
                            deleted_files.append(file_info["name"])
                            total_size_freed += file_info["size"] or 0
            
            return {
                "success": True,
                "deleted_files": len(deleted_files),
                "total_size_freed_bytes": total_size_freed,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old artifacts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        if not self.is_available():
            return {"available": False}
        
        try:
            # Get bucket-level stats
            total_files = 0
            total_size = 0
            artifact_types = {}
            
            files = self.list_files(prefix="artifacts/")
            
            for file_info in files:
                total_files += 1
                total_size += file_info["size"] or 0
                
                # Extract artifact type from path
                path_parts = file_info["name"].split("/")
                if len(path_parts) > 1:
                    artifact_type = path_parts[1]
                    artifact_types[artifact_type] = artifact_types.get(artifact_type, 0) + 1
            
            return {
                "available": True,
                "bucket_name": self._bucket_name,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "artifact_types": artifact_types
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "available": False,
                "error": str(e)
            }


# Global storage service instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get the global storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


def init_storage() -> None:
    """Initialize storage service."""
    global _storage_service
    _storage_service = StorageService()
    logger.info("Storage service initialized")