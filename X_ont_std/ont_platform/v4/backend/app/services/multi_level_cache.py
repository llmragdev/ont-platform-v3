import json
import hashlib
import logging
from functools import wraps
from typing import Any, Callable, List, Dict, Optional
from redis import Redis

logger = logging.getLogger(__name__)

class MultiLevelCache:
    """L1: 메모리 (로컬) → L2: Redis (공유) → L3: DB 계층적 캐시"""

    def __init__(self, redis_url: str, memory_limit: int = 1000):
        # 윈도우/테스트 환경에서 Redis 가 연결 실패하더라도 메모리로 fallback할 수 있게 예외처리 적용
        try:
            self.redis = Redis.from_url(redis_url, socket_timeout=2.0)
            self.redis.ping()
        except Exception as e:
            logger.warning("Failed to connect to Redis, MultiLevelCache running in memory-only fallback mode. Error: %s", e)
            self.redis = None

        self.memory_cache: Dict[str, Any] = {}
        self.memory_limit = memory_limit
        
        # 통계 카운터
        self.hits_l1 = 0
        self.hits_l2 = 0
        self.misses = 0

    def get(self, key: str) -> Any:
        """캐시 조회 (L1 -> L2 -> None)"""
        # L1: 로컬 메모리
        if key in self.memory_cache:
            self.hits_l1 += 1
            return self.memory_cache[key]

        # L2: Redis
        if self.redis:
            try:
                redis_value = self.redis.get(key)
                if redis_value:
                    self.hits_l2 += 1
                    value = json.loads(redis_value)
                    # L1에 복사
                    self._add_to_memory_cache(key, value)
                    return value
            except Exception as e:
                logger.error("Redis read error in MultiLevelCache: %s", e)

        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """캐시 저장 (L1 + L2)"""
        # L1: 메모리
        self._add_to_memory_cache(key, value)

        # L2: Redis
        if self.redis:
            try:
                self.redis.setex(
                    key,
                    ttl,
                    json.dumps(value, ensure_ascii=False)
                )
            except Exception as e:
                logger.error("Redis write error in MultiLevelCache: %s", e)

    def _add_to_memory_cache(self, key: str, value: Any):
        """메모리 캐시에 추가 및 용량 제어 (LRU/FIFO)"""
        if len(self.memory_cache) >= self.memory_limit:
            # 가장 오래된 항목 제거 (FIFO)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        self.memory_cache[key] = value

    def get_hit_rate(self) -> float:
        """전체 캐시 히트율 반환"""
        total = self.hits_l1 + self.hits_l2 + self.misses
        if total == 0:
            return 0.0
        return (self.hits_l1 + self.hits_l2) / total


def cached(cache: MultiLevelCache, ttl: int = 300):
    """비동기 함수 호출 결과 캐싱 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성 (함수명 + 인자 해싱)
            key_data = f"{args}:{kwargs}"
            cache_key = f"{func.__name__}:{hashlib.md5(key_data.encode()).hexdigest()}"

            # 캐시 조회
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 캐시 미스: 본래 비동기 함수 실행
            result = await func(*args, **kwargs)

            # 캐시 저장
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


class CacheInvalidationStrategy:
    """스마트 캐시 무효화 전략"""

    def __init__(self, redis: Redis):
        self.redis = redis

    def invalidate_by_pattern(self, pattern: str):
        """패턴 기반 Redis 캐시 무효화"""
        if not self.redis:
            return
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.error("Failed to invalidate cache by pattern: %s", e)

    def invalidate_on_entity_update(self, entity_id: str):
        """엔티티 업데이트 시 연계 캐시 무효화"""
        if not self.redis:
            return
        try:
            # 1. 해당 엔티티 관련 RDF 캐시 제거
            self.invalidate_by_pattern(f"rdf:{entity_id}:*")
            
            # 2. 해당 엔티티를 포함한 SPARQL 결과 제거
            self.invalidate_by_pattern(f"sparql:*{entity_id}*")
        except Exception as e:
            logger.error("Failed to invalidate cache on entity update: %s", e)

    def invalidate_ttl_based(self, key: str, ttl: int):
        """TTL 기반 만료 설정"""
        if self.redis:
            try:
                self.redis.expire(key, ttl)
            except Exception as e:
                logger.error("Failed to set TTL for key %s: %s", key, e)

    def warm_cache(self, queries: List[str], execute_func: Callable[[str], Any]):
        """자주 쓰이는 SPARQL 질의 결과 사전 적재 (Cache Warming)"""
        if not self.redis:
            return
        for query in queries:
            try:
                result = execute_func(query)
                cache_key = f"sparql:{hashlib.md5(query.encode()).hexdigest()}"
                self.redis.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False))
            except Exception as e:
                logger.error("Failed to warm cache for query: %s", e)
