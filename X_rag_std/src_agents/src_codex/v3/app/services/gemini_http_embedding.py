import math

import httpx

from app.core.config import settings


class GeminiHttpEmbeddingService:
    """Embedding client for the central Gemini gateway.

    The RAG service only knows the gateway URL. Gemini API keys remain owned by
    the separate inference server.
    """

    def __init__(self) -> None:
        if not settings.llm_gateway_url:
            raise RuntimeError("LLM_GATEWAY_URL is required for gemini_http embeddings.")
        self.url = f"{settings.llm_gateway_url.rstrip('/')}/api/v1/embed"

    def embed_text(self, text: str, tenant_id: str) -> list[float]:
        response = httpx.post(
            self.url,
            json={"text": text, "tenant_id": tenant_id},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["embedding"]

    @staticmethod
    def cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)
