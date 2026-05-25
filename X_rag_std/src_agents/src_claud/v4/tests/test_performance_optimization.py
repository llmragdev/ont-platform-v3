"""
성능 최적화 테스트.

Task 1: PDF 추출 개선 (normalize_text)
Task 2: 청킹 품질 (MIN_CHUNK_SIZE)
Task 3: 벡터DB 캐싱
Task 4: 임베딩 캐시
"""

import io
import numpy as np
import pytest

from app.services.pipeline.extractor import FileExtractor
from app.services.pipeline.chunker import SemanticChunker, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE
from app.core.cache import VectorDBCache
from app.core.embedding_cache import EmbeddingCache


# ──────────────────────────────────────────────────────────────────
# Task 1: PDF 추출 개선 (normalize_text)
# ──────────────────────────────────────────────────────────────────

class TestNormalizeText:
    """텍스트 정규화 테스트."""

    def test_normalize_single_newlines_to_space(self) -> None:
        """단일 줄바꿈을 스페이스로 변환."""
        text = "Line 1\nLine 2\nLine 3"
        result = FileExtractor._normalize_text(text)
        assert "\n" not in result or "\n\n" in result
        assert "Line 1 Line 2 Line 3" in result.replace("\n\n", " ")

    def test_preserve_paragraph_breaks(self) -> None:
        """문단 구분자 \\n\\n 유지."""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        result = FileExtractor._normalize_text(text)
        assert "\n\n" in result
        assert result.count("\n\n") == 2

    def test_normalize_multiple_spaces(self) -> None:
        """다중 공백을 단일 공백으로."""
        text = "Word1    Word2     Word3"
        result = FileExtractor._normalize_text(text)
        assert "    " not in result
        assert result.count("  ") == 0

    def test_pdf_text_with_line_wrapping(self) -> None:
        """PDF 줄 래핑 시뮬레이션."""
        pdf_text = """This is a long sentence that is
wrapped across multiple
lines in the PDF."""
        result = FileExtractor._normalize_text(pdf_text)
        assert "wrapped across multiple lines" in result
        assert result.startswith("This is a long sentence that is wrapped")

    def test_empty_text(self) -> None:
        """빈 텍스트 처리."""
        assert FileExtractor._normalize_text("") == ""
        assert FileExtractor._normalize_text("   ") == ""

    def test_complex_formatting(self) -> None:
        """복잡한 서식 처리."""
        text = """Title\n\n
First paragraph with\nmultiple\nline breaks.\n\n
Second paragraph."""
        result = FileExtractor._normalize_text(text)
        # \n\n은 유지, \n은 스페이스로
        assert "Title" in result
        assert "First paragraph with multiple line breaks." in result


# ──────────────────────────────────────────────────────────────────
# Task 2: 청킹 품질 (MIN_CHUNK_SIZE)
# ──────────────────────────────────────────────────────────────────

class TestChunkerMinSize:
    """최소 크기 필터링 테스트."""

    def test_all_chunks_above_min_size(self) -> None:
        """모든 청크가 MIN_CHUNK_SIZE 이상."""
        long_text = "This is a long chunk. " * 20  # 약 400자
        chunker = SemanticChunker()
        chunks = chunker.split_text(long_text)

        for chunk in chunks:
            assert len(chunk) >= MIN_CHUNK_SIZE, f"Chunk too small: {len(chunk)} < {MIN_CHUNK_SIZE}"

    def test_small_chunks_merged(self) -> None:
        """너무 작은 청크는 병합."""
        # 짧은 문단들
        text = "Short para.\n\nShort para.\n\nShort para.\n\n" + "Long paragraph. " * 50
        chunker = SemanticChunker()
        chunks = chunker.split_text(text)

        # 모든 청크가 MIN_CHUNK_SIZE 이상
        assert all(len(c) >= MIN_CHUNK_SIZE for c in chunks), \
            f"Some chunks are too small: {[len(c) for c in chunks]}"

    def test_chunks_below_max_size(self) -> None:
        """모든 청크가 MAX_CHUNK_SIZE 이하."""
        text = "Very long text. " * 100  # 약 1600자
        chunker = SemanticChunker()
        chunks = chunker.split_text(text)

        for chunk in chunks:
            assert len(chunk) <= MAX_CHUNK_SIZE, f"Chunk too large: {len(chunk)} > {MAX_CHUNK_SIZE}"

    def test_empty_text(self) -> None:
        """빈 텍스트 처리."""
        chunker = SemanticChunker()
        assert chunker.split_text("") == []
        assert chunker.split_text("   ") == []

    def test_minimum_quality_chunk(self) -> None:
        """최소 크기 청크 생성."""
        # 정확히 MIN_CHUNK_SIZE 크기의 텍스트
        text = "A" * MIN_CHUNK_SIZE
        chunker = SemanticChunker()
        chunks = chunker.split_text(text)

        assert len(chunks) >= 1
        assert len(chunks[0]) >= MIN_CHUNK_SIZE

    def test_chunk_count_reduction(self) -> None:
        """필터링으로 청크 수 감소."""
        # 많은 짧은 문단들
        text = "\n\n".join(["Short para." for _ in range(100)])
        chunker = SemanticChunker()
        chunks = chunker.split_text(text)

        # 100개 문단이 훨씬 적은 청크로 병합되어야 함
        assert len(chunks) < 50, f"Too many chunks: {len(chunks)}"

    def test_korean_text_chunking(self) -> None:
        """한국어 텍스트 청킹."""
        korean_text = """
온톨로지는 지식을 체계적으로 표현하는 방식입니다.
이는 의미론적 웹 구축에 중요한 역할을 합니다.
자연언어 처리 기술과 함께 사용되어 지식 그래프를 만들 수 있습니다.

본 문서는 온톨로지 설계 가이드입니다.
여러 조직의 요구사항을 반영하여 작성되었습니다.
프로젝트별로 커스터마이징할 수 있습니다.
"""
        chunker = SemanticChunker()
        chunks = chunker.split_text(korean_text)

        assert len(chunks) > 0
        assert all(len(c) >= MIN_CHUNK_SIZE for c in chunks)


# ──────────────────────────────────────────────────────────────────
# Task 3: 벡터DB 캐싱
# ──────────────────────────────────────────────────────────────────

class TestVectorDBCache:
    """벡터DB 캐시 테스트."""

    def test_cache_hit(self) -> None:
        """캐시 히트 확인."""
        cache = VectorDBCache()
        query = "test query"
        result = {"chunks": [{"id": "1", "content": "test"}]}

        cache.set(cache._get_cache_key(query), result)
        cached = cache.get(cache._get_cache_key(query))

        assert cached is not None
        assert cached == result

    def test_cache_miss(self) -> None:
        """캐시 미스 확인."""
        cache = VectorDBCache()
        key = cache._get_cache_key("nonexistent query")
        result = cache.get(key)

        assert result is None

    def test_cache_ttl_expiration(self) -> None:
        """TTL 만료 확인."""
        import time
        from datetime import datetime, timedelta

        cache = VectorDBCache(ttl_seconds=1)
        query = "test query"
        result = {"chunks": []}

        cache.set(cache._get_cache_key(query), result)
        time.sleep(1.1)  # TTL 초과

        cached = cache.get(cache._get_cache_key(query))
        assert cached is None

    def test_cache_statistics(self) -> None:
        """캐시 통계 확인."""
        cache = VectorDBCache()
        query = "test"
        key = cache._get_cache_key(query)
        result = {"data": "value"}

        cache.set(key, result)
        cache.get(key)  # 히트
        cache.get(cache._get_cache_key("other"))  # 미스

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0

    def test_cache_clear(self) -> None:
        """캐시 초기화."""
        cache = VectorDBCache()
        key = cache._get_cache_key("query")
        cache.set(key, {"data": "value"})

        assert cache.get(key) is not None

        cache.clear()
        assert cache.get(key) is None
        assert cache.stats()["cache_size"] == 0

    def test_cache_key_generation(self) -> None:
        """캐시 키 생성 일관성."""
        cache = VectorDBCache()
        query = "test query"
        filters = {"category": "IT", "limit": 5}

        key1 = cache._get_cache_key(query, filters)
        key2 = cache._get_cache_key(query, filters)

        assert key1 == key2  # 동일 입력 → 동일 키

    def test_cache_with_filters(self) -> None:
        """필터 포함 캐싱."""
        cache = VectorDBCache()
        query = "test"
        filters1 = {"category": "IT"}
        filters2 = {"category": "HR"}

        key1 = cache._get_cache_key(query, filters1)
        key2 = cache._get_cache_key(query, filters2)

        assert key1 != key2  # 다른 필터 → 다른 키


# ──────────────────────────────────────────────────────────────────
# Task 5: 임베딩 캐시
# ──────────────────────────────────────────────────────────────────

class TestEmbeddingCache:
    """임베딩 캐시 테스트."""

    def test_memory_cache_store_and_retrieve(self, tmp_path) -> None:
        """메모리 캐시 저장 및 조회."""
        cache = EmbeddingCache(cache_dir=str(tmp_path))
        text = "test embedding text"
        embedding = np.random.rand(768).astype(np.float32)

        cache.set(text, embedding)
        retrieved = cache.get(text)

        assert retrieved is not None
        assert np.allclose(retrieved, embedding)

    def test_disk_cache_persistence(self, tmp_path) -> None:
        """디스크 캐시 영속성."""
        cache1 = EmbeddingCache(cache_dir=str(tmp_path))
        text = "persistent embedding"
        embedding = np.random.rand(768).astype(np.float32)

        cache1.set(text, embedding)

        # 새 캐시 인스턴스로 같은 디렉토리 사용
        cache2 = EmbeddingCache(cache_dir=str(tmp_path))
        retrieved = cache2.get(text)

        assert retrieved is not None
        assert np.allclose(retrieved, embedding)

    def test_memory_overflow_handling(self, tmp_path) -> None:
        """메모리 오버플로우 처리."""
        cache = EmbeddingCache(cache_dir=str(tmp_path), max_memory_items=5)

        # 5개 이상 저장
        for i in range(10):
            text = f"text_{i}"
            embedding = np.random.rand(768).astype(np.float32)
            cache.set(text, embedding)

        stats = cache.stats()
        # 메모리 캐시는 최대 5개 유지
        assert stats["memory_items"] <= 5
        # 디스크 캐시는 모두 저장
        assert stats["disk_items"] == 10

    def test_embedding_cache_statistics(self, tmp_path) -> None:
        """임베딩 캐시 통계."""
        cache = EmbeddingCache(cache_dir=str(tmp_path))
        text = "test text"
        embedding = np.random.rand(768).astype(np.float32)

        cache.set(text, embedding)
        cache.get(text)  # 히트
        cache.get("nonexistent")  # 미스

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0
        assert stats["memory_items"] == 1
        assert stats["disk_items"] == 1

    def test_cache_clear(self, tmp_path) -> None:
        """캐시 초기화."""
        cache = EmbeddingCache(cache_dir=str(tmp_path))
        text = "test"
        embedding = np.random.rand(768).astype(np.float32)

        cache.set(text, embedding)
        cache.clear()

        stats = cache.stats()
        assert stats["memory_items"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_memory_size_calculation(self, tmp_path) -> None:
        """메모리 사용량 계산."""
        cache = EmbeddingCache(cache_dir=str(tmp_path))

        # float32 벡터: 768 * 4 = 3072 bytes ≈ 0.003 MB
        embeddings = []
        for i in range(10):
            text = f"text_{i}"
            embedding = np.random.rand(768).astype(np.float32)
            embeddings.append(embedding)
            cache.set(text, embedding)

        stats = cache.stats()
        # 대략적인 메모리 크기 검증
        assert stats["memory_size_mb"] > 0
        assert stats["memory_size_mb"] < 1  # 10 * 3KB ≈ 30KB

    def test_hash_key_consistency(self, tmp_path) -> None:
        """해시 키 일관성."""
        cache = EmbeddingCache(cache_dir=str(tmp_path))
        text = "consistent text"

        key1 = cache._get_key(text)
        key2 = cache._get_key(text)

        assert key1 == key2
