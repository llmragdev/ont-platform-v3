import re


class TextChunker:
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
            if next_start <= start:
                next_start = boundary
            start = next_start

        return chunks
