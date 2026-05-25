"""
캐시된 임베딩 서비스.

기존 임베딩 서비스를 래핑하여 캐싱 기능 추가.
"""

import numpy as np

from app.core.embedding_cache import EmbeddingCache
from app.services.embedding.base import EmbeddingService


class CachedEmbeddingService(EmbeddingService):
    """임베딩 캐싱을 지원하는 EmbeddingService 래퍼.

    Args:
        base_service: 기본 임베딩 서비스
        cache: EmbeddingCache 인스턴스
    """

    def __init__(self, base_service: EmbeddingService, cache: EmbeddingCache | None = None) -> None:
        """CachedEmbeddingService 초기화.

        Args:
            base_service: 실제 임베딩을 수행할 기본 서비스
            cache: 캐시 인스턴스 (None이면 자동 생성)
        """
        self._base_service = base_service
        self._cache = cache or EmbeddingCache()

    def embed_text(self, text: str, tenant_id: str = "") -> list[float]:
        """텍스트를 임베딩.

        캐시에서 먼저 확인 후, 없으면 기본 서비스 호출.

        Args:
            text: 임베딩할 텍스트
            tenant_id: 테넌트 ID

        Returns:
            임베딩 벡터 (list[float])
        """
        # 캐시 확인
        cached_embedding = self._cache.get(text)
        if cached_embedding is not None:
            return cached_embedding.tolist()

        # 캐시 미스: 기본 서비스 호출
        embedding = self._base_service.embed_text(text, tenant_id)

        # numpy 배열로 변환하여 캐시에 저장
        embedding_array = np.array(embedding, dtype=np.float32)
        self._cache.set(text, embedding_array)

        return embedding

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """코사인 유사도 계산.

        캐시와 무관하게 기본 서비스의 구현을 사용.

        Args:
            a: 벡터 a
            b: 벡터 b

        Returns:
            코사인 유사도 (-1 ~ 1)
        """
        return self._base_service.cosine_similarity(a, b)

    def get_cache_stats(self) -> dict:
        """캐시 통계 반환.

        Returns:
            캐시 통계 딕셔너리
        """
        return self._cache.stats()
