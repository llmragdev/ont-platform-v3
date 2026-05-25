"""
벡터DB 쿼리 캐싱 모듈.

캐시 전략:
- 쿼리 + 필터 기반으로 캐시 키 생성
- SHA256 해시로 키 정규화
- TTL 기반 자동 만료
- 메모리 기반 인메모리 캐시
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional


class VectorDBCache:
    """벡터DB 검색 결과 캐싱.

    Attributes:
        ttl_seconds: 캐시 TTL (초 단위)
        cache: 캐시 저장소 {key: (value, timestamp)}
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        """VectorDBCache 초기화.

        Args:
            ttl_seconds: Time-To-Live (기본값: 1시간)
        """
        self.cache: dict[str, tuple] = {}
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _get_cache_key(query: str, filters: Optional[dict] = None) -> str:
        """쿼리 + 필터 기반 캐시 키 생성.

        Args:
            query: 검색 쿼리
            filters: 검색 필터 (dict)

        Returns:
            SHA256 기반 캐시 키
        """
        filters_str = str(sorted(filters.items())) if filters else ""
        key_str = f"{query}:{filters_str}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        """캐시에서 값 조회.

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 (없으면 None)
        """
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                self.hits += 1
                return value
            else:
                # TTL 만료 시 삭제
                del self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: dict) -> None:
        """캐시에 값 저장.

        Args:
            key: 캐시 키
            value: 저장할 값 (dict)
        """
        self.cache[key] = (value, datetime.now())

    def clear(self) -> None:
        """전체 캐시 초기화."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> dict:
        """캐시 통계 반환.

        Returns:
            {
                "cache_size": 현재 캐시 항목 수,
                "ttl_seconds": TTL (초),
                "hits": 캐시 히트 수,
                "misses": 캐시 미스 수,
                "hit_rate": 히트율 (%)
            }
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0

        return {
            "cache_size": len(self.cache),
            "ttl_seconds": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
        }
