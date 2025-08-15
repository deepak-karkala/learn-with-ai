"""
Redis service for caching and rate limiting in production.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

try:
    import redis
    from redis.exceptions import ConnectionError, TimeoutError, RedisError
except ImportError:
    redis = None
    ConnectionError = Exception
    TimeoutError = Exception
    RedisError = Exception

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching, rate limiting, and session storage."""
    
    def __init__(self):
        self._client: Optional[Any] = None  # Use Any instead of redis.Redis when redis might be None
        self._connection_pool: Optional[Any] = None
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Initialize Redis connection with production settings."""
        if redis is None:
            logger.warning("Redis package not available, Redis features will be disabled")
            return
            
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning("REDIS_URL not configured, Redis features will be disabled")
            return
        
        try:
            # Parse connection parameters
            max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
            retry_on_timeout = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
            socket_keepalive = os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true"
            
            # Create connection pool
            self._connection_pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                retry_on_timeout=retry_on_timeout,
                socket_keepalive=socket_keepalive,
                socket_keepalive_options={},
                health_check_interval=30,
                decode_responses=True
            )
            
            # Create Redis client
            self._client = redis.Redis(
                connection_pool=self._connection_pool,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self._client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None
            self._connection_pool = None
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        
        try:
            self._client.ping()
            return True
        except Exception:
            return False
    
    def get_client(self) -> Optional[Any]:
        """Get Redis client instance."""
        return self._client
    
    # =============================================================================
    # Caching Operations
    # =============================================================================
    
    def set_cache(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set a value in cache with optional TTL."""
        if not self._client:
            return False
        
        try:
            serialized_value = json.dumps(value)
            if ttl_seconds:
                return self._client.setex(key, ttl_seconds, serialized_value)
            else:
                return self._client.set(key, serialized_value)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self._client:
            return None
        
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self._client:
            return False
        
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def cache_exists(self, key: str) -> bool:
        """Check if a cache key exists."""
        if not self._client:
            return False
        
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def set_cache_hash(self, key: str, field: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set a field in a hash with optional TTL."""
        if not self._client:
            return False
        
        try:
            serialized_value = json.dumps(value)
            result = self._client.hset(key, field, serialized_value)
            
            if ttl_seconds:
                self._client.expire(key, ttl_seconds)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting hash {key}.{field}: {e}")
            return False
    
    def get_cache_hash(self, key: str, field: str) -> Optional[Any]:
        """Get a field from a hash."""
        if not self._client:
            return None
        
        try:
            value = self._client.hget(key, field)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting hash {key}.{field}: {e}")
            return None
    
    def get_all_cache_hash(self, key: str) -> Dict[str, Any]:
        """Get all fields from a hash."""
        if not self._client:
            return {}
        
        try:
            hash_data = self._client.hgetall(key)
            return {field: json.loads(value) for field, value in hash_data.items()}
        except Exception as e:
            logger.error(f"Error getting all hash {key}: {e}")
            return {}
    
    # =============================================================================
    # Rate Limiting
    # =============================================================================
    
    def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int,
        identifier: str = "default"
    ) -> Dict[str, Any]:
        """
        Check if a request is within rate limits using sliding window algorithm.
        
        Returns:
            Dict with keys: allowed (bool), remaining (int), reset_time (int)
        """
        if not self._client:
            # If Redis is not available, allow all requests
            return {
                "allowed": True,
                "remaining": limit,
                "reset_time": int(time.time() + window_seconds),
                "redis_available": False
            }
        
        try:
            rate_limit_key = f"rate_limit:{key}:{identifier}"
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = self._client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(rate_limit_key)
            
            # Add current request
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            
            # Set expiry for the key
            pipe.expire(rate_limit_key, window_seconds + 10)
            
            results = pipe.execute()
            
            current_count = results[1] + 1  # +1 for the request we just added
            
            allowed = current_count <= limit
            remaining = max(0, limit - current_count)
            reset_time = int(current_time + window_seconds)
            
            if not allowed:
                # Remove the request we just added since it's not allowed
                self._client.zrem(rate_limit_key, str(current_time))
            
            return {
                "allowed": allowed,
                "remaining": remaining,
                "reset_time": reset_time,
                "current_count": current_count,
                "redis_available": True
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {key}: {e}")
            # On error, allow the request but log the issue
            return {
                "allowed": True,
                "remaining": limit,
                "reset_time": int(time.time() + window_seconds),
                "redis_available": False,
                "error": str(e)
            }
    
    def reset_rate_limit(self, key: str, identifier: str = "default") -> bool:
        """Reset rate limit for a specific key and identifier."""
        if not self._client:
            return False
        
        try:
            rate_limit_key = f"rate_limit:{key}:{identifier}"
            return bool(self._client.delete(rate_limit_key))
        except Exception as e:
            logger.error(f"Error resetting rate limit for {key}: {e}")
            return False
    
    # =============================================================================
    # Session Storage
    # =============================================================================
    
    def store_session(
        self, 
        session_id: str, 
        session_data: Dict[str, Any],
        ttl_seconds: int = 3600
    ) -> bool:
        """Store session data with TTL."""
        if not self._client:
            return False
        
        session_key = f"session:{session_id}"
        return self.set_cache(session_key, session_data, ttl_seconds)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        if not self._client:
            return None
        
        session_key = f"session:{session_id}"
        return self.get_cache(session_key)
    
    def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any],
        ttl_seconds: int = 3600
    ) -> bool:
        """Update specific fields in session data."""
        if not self._client:
            return False
        
        session_data = self.get_session(session_id)
        if session_data is None:
            session_data = {}
        
        session_data.update(updates)
        return self.store_session(session_id, session_data, ttl_seconds)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session data."""
        if not self._client:
            return False
        
        session_key = f"session:{session_id}"
        return self.delete_cache(session_key)
    
    # =============================================================================
    # Analytics and Metrics
    # =============================================================================
    
    def increment_counter(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter and return the new value."""
        if not self._client:
            return None
        
        try:
            return self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing counter {key}: {e}")
            return None
    
    def track_api_usage(
        self, 
        endpoint: str, 
        user_id: str, 
        response_time_ms: float,
        status_code: int
    ) -> None:
        """Track API usage metrics."""
        if not self._client:
            return
        
        try:
            date_key = datetime.now().strftime("%Y-%m-%d")
            hour_key = datetime.now().strftime("%Y-%m-%d:%H")
            
            # Track daily metrics
            daily_key = f"api_usage:daily:{date_key}"
            self._client.hincrby(daily_key, f"{endpoint}:count", 1)
            self._client.hincrby(daily_key, f"{endpoint}:total_time", int(response_time_ms))
            self._client.hincrby(daily_key, f"status:{status_code}", 1)
            self._client.expire(daily_key, 86400 * 7)  # Keep for 7 days
            
            # Track hourly metrics
            hourly_key = f"api_usage:hourly:{hour_key}"
            self._client.hincrby(hourly_key, f"{endpoint}:count", 1)
            self._client.hincrby(hourly_key, f"{endpoint}:total_time", int(response_time_ms))
            self._client.expire(hourly_key, 86400)  # Keep for 24 hours
            
            # Track user-specific metrics
            user_key = f"user_usage:{user_id}:{date_key}"
            self._client.hincrby(user_key, "total_requests", 1)
            self._client.hincrby(user_key, "total_time", int(response_time_ms))
            self._client.expire(user_key, 86400 * 30)  # Keep for 30 days
            
        except Exception as e:
            logger.error(f"Error tracking API usage: {e}")
    
    def get_api_metrics(self, date: str) -> Dict[str, Any]:
        """Get API metrics for a specific date."""
        if not self._client:
            return {}
        
        try:
            daily_key = f"api_usage:daily:{date}"
            return self.get_all_cache_hash(daily_key)
        except Exception as e:
            logger.error(f"Error getting API metrics: {e}")
            return {}
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def flush_cache(self, pattern: Optional[str] = None) -> bool:
        """Flush cache keys matching a pattern."""
        if not self._client:
            return False
        
        try:
            if pattern:
                keys = self._client.keys(pattern)
                if keys:
                    return bool(self._client.delete(*keys))
            else:
                return bool(self._client.flushdb())
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get Redis connection information."""
        if not self._client:
            return {"status": "disconnected"}
        
        try:
            info = self._client.info()
            return {
                "status": "connected",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses")
            }
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {"status": "error", "error": str(e)}


# Global Redis service instance
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Get the global Redis service instance."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service


def init_redis() -> None:
    """Initialize Redis service."""
    global _redis_service
    _redis_service = RedisService()
    logger.info("Redis service initialized")


# Context manager for Redis transactions
class RedisTransaction:
    """Context manager for Redis transactions."""
    
    def __init__(self, redis_client: Any):
        self.client = redis_client
        self.pipeline = None
    
    def __enter__(self):
        self.pipeline = self.client.pipeline(transaction=True)
        return self.pipeline
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                self.pipeline.execute()
            except Exception as e:
                logger.error(f"Redis transaction failed: {e}")
                raise
        else:
            # Transaction failed, pipeline will be discarded
            logger.error(f"Redis transaction aborted due to exception: {exc_val}")