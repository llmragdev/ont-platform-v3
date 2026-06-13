"""Priority 2.5 Week 4: Redis & In-Memory Query Result Cache Service."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

class QueryCacheService:
    """Caching service for storing query results. Supports Redis and memory fallback."""

    def __init__(self, redis_url: Optional[str] = None, cache_name: str = "query_cache"):
        self.redis_url = redis_url
        self.cache_name = cache_name
        self.memory_cache: Dict[str, str] = {}
        
        # Redis Connection Setup
        self.redis_client = None
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, socket_timeout=2.0)
                self.redis_client.ping()
                logger.info("Connected to Redis for query result cache: %s", redis_url)
            except Exception as e:
                logger.warning("Failed to connect to Redis for query cache, falling back to In-Memory. Error: %s", e)
                self.redis_client = None

        self.hits = 0
        self.misses = 0

    def _get_cache_key(self, query: str, tenant_domain: str) -> str:
        """Create a unique cache key based on query string and tenant domain boundary."""
        hasher = hashlib.sha256(f"{tenant_domain}:{query}".encode('utf-8'))
        return f"{self.cache_name}:{hasher.hexdigest()}"

    def get_query(self, query: str, tenant_domain: str) -> Optional[Any]:
        """Retrieve cached query result if valid."""
        key = self._get_cache_key(query, tenant_domain)
        
        if self.redis_client:
            try:
                cached_val = self.redis_client.get(key)
                if cached_val:
                    self.hits += 1
                    return json.loads(cached_val)
            except Exception as e:
                logger.error("Redis read error in cache service: %s", e)
        
        if key in self.memory_cache:
            self.hits += 1
            return json.loads(self.memory_cache[key])
            
        self.misses += 1
        return None

    def set_query(self, query: str, tenant_domain: str, result: Any, ttl_seconds: int = 300) -> None:
        """Cache query result with specified TTL."""
        key = self._get_cache_key(query, tenant_domain)
        serialized = json.dumps(result, ensure_ascii=False)
        
        self.memory_cache[key] = serialized
        
        if self.redis_client:
            try:
                self.redis_client.set(key, serialized, ex=ttl_seconds)
            except Exception as e:
                logger.error("Redis write error in cache service: %s", e)

    def invalidate_by_domain(self, tenant_domain: str) -> None:
        """Invalidate all cache entries associated with a tenant domain."""
        if self.redis_client:
            try:
                keys = self.redis_client.keys(f"{self.cache_name}:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.error("Redis invalidation error: %s", e)
                
        self.memory_cache.clear()
        logger.info("Cache invalidated for domain: %s", tenant_domain)

    def get_stats(self) -> Dict[str, Any]:
        """Return cache hit/miss ratio metrics."""
        total = self.hits + self.misses
        hit_ratio = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_ratio": hit_ratio,
            "memory_cache_entries": len(self.memory_cache),
            "redis_connected": self.redis_client is not None
        }

# Alias for compatibility with tests
CacheService = QueryCacheService

