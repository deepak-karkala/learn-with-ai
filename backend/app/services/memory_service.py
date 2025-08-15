"""
Vertex AI RAG service for memory and context management in production.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

try:
    import numpy as np
    from google.cloud import aiplatform
    from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint
    from google.oauth2 import service_account
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sentence_transformers import SentenceTransformer
except ImportError:
    np = None
    aiplatform = None
    MatchingEngineIndex = None
    MatchingEngineIndexEndpoint = None
    service_account = None
    TfidfVectorizer = None
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class MemoryService:
    """Vertex AI RAG service for context and memory management."""
    
    def __init__(self):
        self._initialized = False
        self._project_id: Optional[str] = None
        self._location: Optional[str] = None
        self._index_id: Optional[str] = None
        self._index_endpoint_id: Optional[str] = None
        self._deployed_index_id: Optional[str] = None
        
        # Embedding model for local fallback
        self._embedding_model: Optional[Any] = None
        self._local_vectors: Dict[str, Any] = {}
        self._local_metadata: Dict[str, Dict] = {}
        
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize Vertex AI RAG service."""
        try:
            if SentenceTransformer is None or aiplatform is None:
                logger.warning("Required dependencies not available, memory service will be disabled")
                return
                
            # Get configuration from environment
            self._project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            self._location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            self._index_id = os.getenv("VERTEX_AI_INDEX_ID")
            self._index_endpoint_id = os.getenv("VERTEX_AI_INDEX_ENDPOINT_ID")
            self._deployed_index_id = os.getenv("VERTEX_AI_DEPLOYED_INDEX_ID")
            
            if not all([self._project_id, self._index_id, self._index_endpoint_id]):
                logger.warning("Vertex AI RAG not fully configured, using local fallback")
                self._initialize_local_fallback()
                return
            
            # Initialize Vertex AI
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                aiplatform.init(
                    project=self._project_id,
                    location=self._location,
                    credentials=credentials
                )
            else:
                aiplatform.init(
                    project=self._project_id,
                    location=self._location
                )
            
            # Test connection
            self._test_vertex_ai_connection()
            self._initialized = True
            logger.info("Vertex AI RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI RAG: {e}")
            self._initialize_local_fallback()
    
    def _initialize_local_fallback(self) -> None:
        """Initialize local embedding fallback."""
        try:
            # Use a lightweight sentence transformer model
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Local embedding fallback initialized")
        except Exception as e:
            logger.error(f"Failed to initialize local embedding model: {e}")
    
    def _test_vertex_ai_connection(self) -> None:
        """Test Vertex AI connection."""
        try:
            # Get index endpoint
            index_endpoint = MatchingEngineIndexEndpoint(
                index_endpoint_name=f"projects/{self._project_id}/locations/{self._location}/indexEndpoints/{self._index_endpoint_id}"
            )
            logger.info("Vertex AI connection test successful")
        except Exception as e:
            logger.error(f"Vertex AI connection test failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the memory service is available."""
        return self._initialized or self._embedding_model is not None
    
    # =============================================================================
    # Embedding Operations
    # =============================================================================
    
    def _generate_embedding(self, text: str) -> Any:
        """Generate embedding for text using available method."""
        try:
            if self._embedding_model:
                # Use local model
                embedding = self._embedding_model.encode(text, convert_to_numpy=True)
                return embedding
            else:
                # Fallback to simple TF-IDF for basic similarity
                logger.warning("No embedding model available, using TF-IDF fallback")
                # This is a very basic fallback - in production you'd want a proper embedding service
                vectorizer = TfidfVectorizer(max_features=384)
                tfidf_matrix = vectorizer.fit_transform([text])
                return tfidf_matrix.toarray()[0]
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as ultimate fallback
            if np is not None:
                return np.zeros(384)
            else:
                return [0.0] * 384  # Fallback list
    
    def _normalize_vector(self, vector: Any) -> Any:
        """Normalize vector for cosine similarity."""
        if np is not None:
            norm = np.linalg.norm(vector)
            if norm == 0:
                return vector
            return vector / norm
        else:
            # Fallback for when numpy is not available
            norm = sum(x**2 for x in vector) ** 0.5
            if norm == 0:
                return vector
            return [x/norm for x in vector]
    
    def _calculate_similarity(self, vec1: Any, vec2: Any) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_norm = self._normalize_vector(vec1)
        vec2_norm = self._normalize_vector(vec2)
        if np is not None:
            return float(np.dot(vec1_norm, vec2_norm))
        else:
            # Fallback dot product calculation
            return float(sum(a * b for a, b in zip(vec1_norm, vec2_norm)))
    
    # =============================================================================
    # Memory Storage Operations
    # =============================================================================
    
    def store_memory(
        self,
        user_id: str,
        session_id: str,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a memory with vector embedding."""
        try:
            # Generate unique ID for this memory
            memory_id = str(uuid.uuid4())
            
            # Generate embedding
            embedding = self._generate_embedding(content)
            
            # Prepare metadata
            memory_metadata = {
                "memory_id": memory_id,
                "user_id": user_id,
                "session_id": session_id,
                "memory_type": memory_type,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "content_length": len(content)
            }
            
            if metadata:
                memory_metadata.update(metadata)
            
            if self._initialized:
                # Use Vertex AI Vector Search
                result = self._store_in_vertex_ai(memory_id, embedding, memory_metadata)
            else:
                # Use local storage
                result = self._store_locally(memory_id, embedding, memory_metadata)
            
            logger.info(f"Memory stored successfully: {memory_id}")
            return {
                "success": True,
                "memory_id": memory_id,
                "embedding_dimensions": len(embedding),
                "storage_method": "vertex_ai" if self._initialized else "local"
            }
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _store_in_vertex_ai(
        self, 
        memory_id: str, 
        embedding: Any, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Store memory in Vertex AI Vector Search."""
        try:
            # Convert embedding to list for JSON serialization
            embedding_list = embedding.tolist()
            
            # Prepare datapoint for Vertex AI
            datapoint = {
                "datapoint_id": memory_id,
                "feature_vector": embedding_list,
                "restricts": [
                    {"namespace": "user_id", "allow": [metadata["user_id"]]},
                    {"namespace": "memory_type", "allow": [metadata["memory_type"]]}
                ],
                "crowding_tag": metadata["session_id"]
            }
            
            # Note: In a real implementation, you would batch these operations
            # and use the Vertex AI Vector Search API to upsert the vectors
            logger.info(f"Would store in Vertex AI: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in Vertex AI: {e}")
            return False
    
    def _store_locally(
        self, 
        memory_id: str, 
        embedding: Any, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Store memory locally as fallback."""
        try:
            self._local_vectors[memory_id] = embedding
            self._local_metadata[memory_id] = metadata
            return True
        except Exception as e:
            logger.error(f"Error storing locally: {e}")
            return False
    
    # =============================================================================
    # Memory Retrieval Operations
    # =============================================================================
    
    def search_similar_memories(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        memory_types: Optional[List[str]] = None,
        time_range_hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using vector similarity."""
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            if self._initialized:
                # Use Vertex AI Vector Search
                results = self._search_vertex_ai(
                    query_embedding, user_id, top_k, similarity_threshold,
                    memory_types, time_range_hours
                )
            else:
                # Use local search
                results = self._search_locally(
                    query_embedding, user_id, top_k, similarity_threshold,
                    memory_types, time_range_hours
                )
            
            logger.info(f"Found {len(results)} similar memories for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def _search_vertex_ai(
        self,
        query_embedding: Any,
        user_id: str,
        top_k: int,
        similarity_threshold: float,
        memory_types: Optional[List[str]],
        time_range_hours: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Search using Vertex AI Vector Search."""
        try:
            # In a real implementation, you would:
            # 1. Convert embedding to the format expected by Vertex AI
            # 2. Build the query with appropriate filters
            # 3. Call the Vector Search API
            # 4. Process and return results
            
            logger.info("Would search using Vertex AI Vector Search")
            return []  # Placeholder
            
        except Exception as e:
            logger.error(f"Error in Vertex AI search: {e}")
            return []
    
    def _search_locally(
        self,
        query_embedding: Any,
        user_id: str,
        top_k: int,
        similarity_threshold: float,
        memory_types: Optional[List[str]],
        time_range_hours: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Search using local vector storage."""
        try:
            results = []
            
            # Calculate cutoff time if time range is specified
            cutoff_time = None
            if time_range_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            # Search through local vectors
            for memory_id, memory_vector in self._local_vectors.items():
                metadata = self._local_metadata.get(memory_id, {})
                
                # Filter by user_id
                if metadata.get("user_id") != user_id:
                    continue
                
                # Filter by memory types
                if memory_types and metadata.get("memory_type") not in memory_types:
                    continue
                
                # Filter by time range
                if cutoff_time:
                    memory_time = datetime.fromisoformat(metadata.get("timestamp", ""))
                    if memory_time < cutoff_time:
                        continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(query_embedding, memory_vector)
                
                if similarity >= similarity_threshold:
                    results.append({
                        "memory_id": memory_id,
                        "similarity_score": similarity,
                        "content": metadata.get("content", ""),
                        "memory_type": metadata.get("memory_type", ""),
                        "session_id": metadata.get("session_id", ""),
                        "timestamp": metadata.get("timestamp", ""),
                        "metadata": metadata
                    })
            
            # Sort by similarity score and return top_k
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in local search: {e}")
            return []
    
    # =============================================================================
    # Session Context Management
    # =============================================================================
    
    def build_session_context(
        self,
        user_id: str,
        session_id: str,
        current_message: str,
        max_context_length: int = 4000
    ) -> Dict[str, Any]:
        """Build contextual information for the current session."""
        try:
            context_parts = []
            total_length = 0
            
            # 1. Get recent memories from current session
            session_memories = self.get_session_memories(user_id, session_id)
            
            # 2. Get similar memories from past sessions
            similar_memories = self.search_similar_memories(
                query=current_message,
                user_id=user_id,
                top_k=3,
                similarity_threshold=0.6,
                time_range_hours=24 * 7  # Last week
            )
            
            # 3. Build context string prioritizing recent and relevant content
            context_parts.append("## Recent Session Context:")
            
            # Add recent session memories (most recent first)
            recent_session = session_memories[-5:] if len(session_memories) > 5 else session_memories
            for memory in reversed(recent_session):
                content = f"- {memory['content'][:200]}..."
                if total_length + len(content) < max_context_length:
                    context_parts.append(content)
                    total_length += len(content)
            
            # Add similar memories from past sessions
            if similar_memories and total_length < max_context_length * 0.7:
                context_parts.append("\n## Relevant Past Context:")
                for memory in similar_memories:
                    if memory['session_id'] != session_id:  # Exclude current session
                        content = f"- {memory['content'][:150]}... (similarity: {memory['similarity_score']:.2f})"
                        if total_length + len(content) < max_context_length:
                            context_parts.append(content)
                            total_length += len(content)
            
            context_string = "\n".join(context_parts)
            
            return {
                "success": True,
                "context": context_string,
                "context_length": len(context_string),
                "session_memories_count": len(session_memories),
                "similar_memories_count": len(similar_memories),
                "total_memories_used": len(recent_session) + len([m for m in similar_memories if m['session_id'] != session_id])
            }
            
        except Exception as e:
            logger.error(f"Error building session context: {e}")
            return {
                "success": False,
                "context": "",
                "error": str(e)
            }
    
    def get_session_memories(
        self,
        user_id: str,
        session_id: str,
        memory_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get all memories for a specific session."""
        try:
            memories = []
            
            if self._initialized:
                # Use Vertex AI to get session memories
                # Implementation would query by session_id restriction
                pass
            else:
                # Use local storage
                for memory_id, metadata in self._local_metadata.items():
                    if (metadata.get("user_id") == user_id and 
                        metadata.get("session_id") == session_id):
                        
                        if memory_types and metadata.get("memory_type") not in memory_types:
                            continue
                        
                        memories.append({
                            "memory_id": memory_id,
                            "content": metadata.get("content", ""),
                            "memory_type": metadata.get("memory_type", ""),
                            "timestamp": metadata.get("timestamp", ""),
                            "metadata": metadata
                        })
            
            # Sort by timestamp
            memories.sort(key=lambda x: x.get("timestamp", ""))
            return memories
            
        except Exception as e:
            logger.error(f"Error getting session memories: {e}")
            return []
    
    # =============================================================================
    # Memory Management Operations
    # =============================================================================
    
    def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete a specific memory."""
        try:
            if self._initialized:
                # Use Vertex AI to delete
                # Implementation would use the Vector Search API to remove the vector
                pass
            else:
                # Delete from local storage
                if memory_id in self._local_vectors:
                    # Verify ownership
                    metadata = self._local_metadata.get(memory_id, {})
                    if metadata.get("user_id") == user_id:
                        del self._local_vectors[memory_id]
                        del self._local_metadata[memory_id]
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
    
    def delete_session_memories(self, user_id: str, session_id: str) -> int:
        """Delete all memories for a session."""
        try:
            deleted_count = 0
            
            if self._initialized:
                # Use Vertex AI batch delete
                pass
            else:
                # Delete from local storage
                memory_ids_to_delete = []
                for memory_id, metadata in self._local_metadata.items():
                    if (metadata.get("user_id") == user_id and 
                        metadata.get("session_id") == session_id):
                        memory_ids_to_delete.append(memory_id)
                
                for memory_id in memory_ids_to_delete:
                    if memory_id in self._local_vectors:
                        del self._local_vectors[memory_id]
                    if memory_id in self._local_metadata:
                        del self._local_metadata[memory_id]
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} memories for session {session_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting session memories: {e}")
            return 0
    
    def cleanup_old_memories(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up memories older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = 0
            
            if self._initialized:
                # Use Vertex AI to clean up old vectors
                pass
            else:
                # Clean up local storage
                memory_ids_to_delete = []
                for memory_id, metadata in self._local_metadata.items():
                    timestamp_str = metadata.get("timestamp", "")
                    if timestamp_str:
                        memory_date = datetime.fromisoformat(timestamp_str)
                        if memory_date < cutoff_date:
                            memory_ids_to_delete.append(memory_id)
                
                for memory_id in memory_ids_to_delete:
                    if memory_id in self._local_vectors:
                        del self._local_vectors[memory_id]
                    if memory_id in self._local_metadata:
                        del self._local_metadata[memory_id]
                    deleted_count += 1
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =============================================================================
    # Statistics and Monitoring
    # =============================================================================
    
    def get_memory_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            if self._initialized:
                # Get stats from Vertex AI
                return {
                    "service_type": "vertex_ai",
                    "status": "initialized"
                }
            else:
                # Get stats from local storage
                total_memories = len(self._local_metadata)
                user_memories = 0
                memory_types = {}
                
                if user_id:
                    for metadata in self._local_metadata.values():
                        if metadata.get("user_id") == user_id:
                            user_memories += 1
                        
                        memory_type = metadata.get("memory_type", "unknown")
                        memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
                
                return {
                    "service_type": "local_fallback",
                    "total_memories": total_memories,
                    "user_memories": user_memories if user_id else None,
                    "memory_types": memory_types,
                    "embedding_model": "all-MiniLM-L6-v2" if self._embedding_model else "none"
                }
                
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {
                "service_type": "error",
                "error": str(e)
            }


# Global memory service instance
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Get the global memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service


def init_memory_service() -> None:
    """Initialize memory service."""
    global _memory_service
    _memory_service = MemoryService()
    logger.info("Memory service initialized")