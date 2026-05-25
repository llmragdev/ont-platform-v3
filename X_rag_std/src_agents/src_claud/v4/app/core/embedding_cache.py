"""
임베딩 캐시 모듈 (메모리 + 디스크).

캐시 전략:
- 자주 사용되는 임베딩을 메모리에 캐시
- 덜 사용되는 임베딩을 디스크에 저장
- SHA256 기반 캐시 키
- LRU 방식으로 메모리 오버플로우 관리
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np


class EmbeddingCache:
    """자주 사용되는 임베딩 캐싱 (메모리 + 디스크).

    Attributes:
        cache_dir: 디스크 캐시 디렉토리
        memory_cache: 인메모리 캐시 {key: embedding}
        max_memory_items: 메모리 캐시 최대 항목 수
        stats: 캐시 통계 {hits, misses, evictions}
    """

    def __init__(self, cache_dir: str = "./storage/embedding_cache", max_memory_items: int = 10000) -> None:
        """EmbeddingCache 초기화.

        Args:
            cache_dir: 디스크 캐시 디렉토리 (기본값: ./storage/embedding_cache)
            max_memory_items: 메모리 캐시 최대 항목 수 (기본값: 10000)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 인메모리 캐시
        self.memory_cache: dict[str, np.ndarray] = {}
        self.max_memory_items = max_memory_items

        # 통계
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    @staticmethod
    def _get_key(text: str) -> str:
        """SHA256 기반 캐시 키 생성.

        Args:
            text: 임베딩 대상 텍스트

        Returns:
            SHA256 해시 키
        """
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[np.ndarray]:
        """캐시에서 임베딩 조회.

        1단계: 메모리 캐시 확인
        2단계: 디스크 캐시 확인 후 메모리로 로드
        3단계: 캐시 미스

        Args:
            text: 조회할 텍스트

        Returns:
            임베딩 벡터 (캐시 미스 시 None)
        """
        key = self._get_key(text)

        # 1단계: 메모리 캐시 확인
        if key in self.memory_cache:
            self.hits += 1
            return self.memory_cache[key]

        # 2단계: 디스크 캐시 확인
        disk_path = self.cache_dir / f"{key}.npy"
        if disk_path.exists():
            try:
                embedding = np.load(disk_path)
                # 디스크에서 읽은 것을 메모리로 로드 (용량이 있으면)
                if len(self.memory_cache) < self.max_memory_items:
                    self.memory_cache[key] = embedding
                self.hits += 1
                return embedding
            except Exception as e:
                print(f"Warning: Failed to load embedding from disk: {e}")
                return None

        # 3단계: 캐시 미스
        self.misses += 1
        return None

    def set(self, text: str, embedding: np.ndarray) -> None:
        """임베딩을 캐시에 저장.

        1단계: 메모리 캐시에 저장
        2단계: 용량이 초과되면 오래된 항목 제거
        3단계: 디스크 캐시에도 저장

        Args:
            text: 임베딩 대상 텍스트
            embedding: 임베딩 벡터
        """
        key = self._get_key(text)

        # 메모리 캐시에 저장
        self.memory_cache[key] = embedding

        # 메모리 오버플로우 관리
        if len(self.memory_cache) > self.max_memory_items:
            # 가장 오래된 항목 제거 (FIFO 방식)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
            self.evictions += 1

        # 디스크 캐시에도 저장
        try:
            disk_path = self.cache_dir / f"{key}.npy"
            np.save(disk_path, embedding)
        except Exception as e:
            print(f"Warning: Failed to save embedding to disk: {e}")

    def clear(self) -> None:
        """전체 캐시 초기화."""
        self.memory_cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def clear_disk_cache(self) -> None:
        """디스크 캐시만 초기화."""
        try:
            for npy_file in self.cache_dir.glob("*.npy"):
                npy_file.unlink()
        except Exception as e:
            print(f"Warning: Failed to clear disk cache: {e}")

    def stats(self) -> dict:
        """캐시 통계 반환.

        Returns:
            {
                "memory_items": 메모리 캐시 항목 수,
                "disk_items": 디스크 캐시 항목 수,
                "memory_size_mb": 메모리 사용량 (MB),
                "hits": 캐시 히트 수,
                "misses": 캐시 미스 수,
                "hit_rate": 히트율 (%),
                "evictions": 제거된 항목 수,
            }
        """
        disk_items = len(list(self.cache_dir.glob("*.npy")))
        memory_items = len(self.memory_cache)
        memory_size_mb = sum(
            v.nbytes for v in self.memory_cache.values()
        ) / (1024 * 1024)

        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0

        return {
            "memory_items": memory_items,
            "disk_items": disk_items,
            "memory_size_mb": round(memory_size_mb, 2),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "evictions": self.evictions,
        }
