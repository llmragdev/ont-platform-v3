import math

import httpx

from app.core.config import settings
from app.services.embedding.base import EmbeddingService


class GeminiHttpEmbeddingService(EmbeddingService):
    """LLM Gateway를 통한 Gemini 임베딩 — RAG ↔ LLM 서버 분리 구조."""

    def __init__(self) -> None:
        if not settings.llm_gateway_url:
            raise RuntimeError("LLM_GATEWAY_URL 이 설정되지 않았습니다.")
        self._url = f"{settings.llm_gateway_url.rstrip('/')}/api/v1/embed"

    def embed_text(self, text: str, tenant_id: str = "") -> list[float]:
        resp = httpx.post(
            self._url,
            json={"text": text, "tenant_id": tenant_id},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
