import re
from abc import ABC, abstractmethod

# 최소/최대 청크 크기
MIN_CHUNK_SIZE = 150  # 최소 150자
MAX_CHUNK_SIZE = 1000  # 최대 1000자


class ChunkerBase(ABC):
    @abstractmethod
    def split_text(self, text: str) -> list[str]: ...


class FixedSizeChunker(ChunkerBase):
    """700자 고정 크기, 80자 오버랩, 문장 경계 탐색.
    Codex TextChunker와 동일 로직을 ABC 위에 재구현.
    """

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 80) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return []
        if len(cleaned) <= self.chunk_size:
            return [cleaned]

        chunks: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(start + self.chunk_size, len(cleaned))
            boundary = cleaned.rfind(".", start, end)
            if boundary <= start + self.chunk_size // 2:
                boundary = cleaned.rfind(" ", start, end)
            if boundary <= start:
                boundary = end

            chunk = cleaned[start:boundary].strip()
            if chunk:
                chunks.append(chunk)

            if boundary >= len(cleaned):
                break
            next_start = max(boundary - self.chunk_overlap, start + 1)
            start = next_start if next_start > start else boundary

        return chunks


class SemanticChunker(ChunkerBase):
    """문단(\\n\\n) 단위 우선 분할 → 초과 시 FixedSizeChunker로 재분할.
    한국어 문단 구조를 존중해 의미 단위 청크를 우선 생성.
    최소 크기 필터링을 적용해 너무 작은 청크를 제거하거나 병합.
    """

    def __init__(self, max_size: int = 700, chunk_overlap: int = 80, min_size: int = MIN_CHUNK_SIZE) -> None:
        self.max_size = max_size
        self.min_size = min_size
        self._fallback = FixedSizeChunker(max_size, chunk_overlap)

    def split_text(self, text: str) -> list[str]:
        if not text.strip():
            return []
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        result: list[str] = []
        for para in paragraphs:
            if len(para) <= self.max_size:
                result.append(para)
            else:
                result.extend(self._fallback.split_text(para))

        # 최소 크기 필터링 + 병합
        return self._filter_and_merge_chunks(result)

    def _filter_and_merge_chunks(self, chunks: list[str]) -> list[str]:
        """
        너무 작은 청크를 제거하거나 인접한 청크와 병합.

        Args:
            chunks: 원본 청크 리스트

        Returns:
            필터링된 청크 리스트
        """
        if not chunks:
            return []

        filtered: list[str] = []
        buffer = ""

        for chunk in chunks:
            if len(chunk) >= self.min_size:
                # 현재 청크가 충분히 크면
                if buffer:
                    # 버퍼가 있다면 버퍼 + 현재 청크 병합
                    merged = buffer + " " + chunk
                    if len(merged) <= self.max_size:
                        filtered.append(merged)
                    else:
                        filtered.append(buffer)
                        filtered.append(chunk)
                    buffer = ""
                else:
                    filtered.append(chunk)
            else:
                # 현재 청크가 너무 작으면 버퍼에 누적
                if buffer:
                    buffer += " " + chunk
                else:
                    buffer = chunk

        # 남은 버퍼 처리
        if buffer and len(buffer) >= self.min_size:
            filtered.append(buffer)
        elif buffer and filtered:
            # 버퍼가 너무 작으면 마지막 청크에 병합
            last_chunk = filtered[-1]
            merged = last_chunk + " " + buffer
            if len(merged) <= self.max_size:
                filtered[-1] = merged
            # 아니면 버퍼 폐기 (너무 작으므로)

        # 최종 검증: 모든 청크가 MIN_CHUNK_SIZE 이상이고 MAX_CHUNK_SIZE 이하
        return [c for c in filtered if self.min_size <= len(c) <= self.max_size]
