"""Priority 2.5 Week 2: Embedding Caching & Batching Service."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import List, Dict, Any, Optional

try:
    from langchain_core.embeddings import Embeddings
except ImportError:
    try:
        from langchain_community.embeddings import Embeddings
    except ImportError:
        class Embeddings:
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                raise NotImplementedError
            def embed_query(self, text: str) -> List[float]:
                raise NotImplementedError

logger = logging.getLogger(__name__)

class CachedEmbeddings(Embeddings):
    """LangChain Embeddings wrapper that caches embedding vectors to avoid duplicate API calls."""

    def __init__(
        self,
        base_embeddings: Embeddings,
        redis_url: Optional[str] = None,
        cache_name: str = "embedding_cache"
    ) -> None:
        self.base_embeddings = base_embeddings
        self.redis_url = redis_url
        self.cache_name = cache_name
        self.memory_cache: Dict[str, List[float]] = {}
        
        # Redis Connection Setup
        self.redis_client = None
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, socket_timeout=2.0)
                self.redis_client.ping()
                logger.info("Connected to Redis for embedding cache: %s", redis_url)
            except Exception as e:
                logger.warning("Failed to connect to Redis, falling back to In-Memory cache. Error: %s", e)
                self.redis_client = None

        # Statistics
        self.hits = 0
        self.misses = 0

    def _get_cache_key(self, text: str) -> str:
        """Generate a deterministic hash key for a given text."""
        hasher = hashlib.sha256(text.encode('utf-8'))
        return f"{self.cache_name}:{hasher.hexdigest()}"

    def _lookup_cache(self, text: str) -> Optional[List[float]]:
        """Look up the cache for the given text. Returns embedding vector or None."""
        key = self._get_cache_key(text)
        
        if self.redis_client:
            try:
                cached_val = self.redis_client.get(key)
                if cached_val:
                    self.hits += 1
                    return json.loads(cached_val)
            except Exception as e:
                logger.error("Redis read error: %s", e)
        
        if key in self.memory_cache:
            self.hits += 1
            return self.memory_cache[key]
            
        self.misses += 1
        return None

    def _write_cache(self, text: str, embedding: List[float]) -> None:
        """Write the embedding to cache."""
        key = self._get_cache_key(text)
        
        self.memory_cache[key] = embedding
        
        if self.redis_client:
            try:
                self.redis_client.set(key, json.dumps(embedding), ex=86400 * 7)  # TTL: 7 days
            except Exception as e:
                logger.error("Redis write error: %s", e)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents. Performs batching and caching optimization."""
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        for idx, text in enumerate(texts):
            cached_emb = self._lookup_cache(text)
            if cached_emb is not None:
                results[idx] = cached_emb
            else:
                uncached_indices.append(idx)
                uncached_texts.append(text)

        if uncached_texts:
            try:
                new_embeddings = self.base_embeddings.embed_documents(uncached_texts)
                for idx, emb in zip(uncached_indices, new_embeddings):
                    results[idx] = emb
                    self._write_cache(texts[idx], emb)
            except Exception as e:
                logger.error("Failed to generate embeddings via base model: %s", e)
                raise e

        return [r for r in results if r is not None]

    def embed_query(self, text: str) -> List[float]:
        """Embed a query text with caching."""
        cached_emb = self._lookup_cache(text)
        if cached_emb is not None:
            return cached_emb

        try:
            emb = self.base_embeddings.embed_query(text)
            self._write_cache(text, emb)
            return emb
        except Exception as e:
            logger.error("Failed to generate query embedding: %s", e)
            raise e

    def get_stats(self) -> Dict[str, Any]:
        """Get cache efficiency statistics."""
        total = self.hits + self.misses
        hit_ratio = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_ratio": hit_ratio,
            "memory_cache_size": len(self.memory_cache),
            "redis_connected": self.redis_client is not None
        }

    def clear_cache(self) -> None:
        """Clear memory cache. If Redis is connected, clear keys matching cache_name."""
        self.memory_cache.clear()
        if self.redis_client:
            try:
                keys = self.redis_client.keys(f"{self.cache_name}:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.error("Redis clear error: %s", e)
