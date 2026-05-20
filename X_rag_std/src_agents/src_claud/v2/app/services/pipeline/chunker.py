import re
from abc import ABC, abstractmethod


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
    """

    def __init__(self, max_size: int = 700, chunk_overlap: int = 80) -> None:
        self.max_size = max_size
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
        return result
