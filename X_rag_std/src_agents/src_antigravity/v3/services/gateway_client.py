import httpx
import math
from typing import List
from core.config import settings

class EmbeddingError(Exception):
    """임베딩 API 호출 실패 시 발생하는 예외"""
    pass

class LlmGatewayClient:
    def __init__(self):
        self.base_url = settings.llm_gateway_url.rstrip("/")
    
    def embed_text(self, text: str, tenant_id: str = "default") -> List[float]:
        """
        텍스트 임베딩을 위해 LLM Gateway를 호출합니다.
        v1.3 표준에 따라 fallback[0.1, 0.2]을 절대 사용하지 않습니다.
        """
        try:
            resp = httpx.post(
                f"{self.base_url}/api/v1/embed",
                json={"text": text, "tenant_id": tenant_id},
                timeout=10.0
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        except Exception as e:
            # 표준 2.6: 반드시 예외를 전파하여 파이프라인을 error 상태로 전환
            raise EmbeddingError(f"Gateway embedding failed: {str(e)}")

    def generate_answer(self, prompt: str, tenant_id: str = "default") -> str:
        """LLM 답변 생성을 위해 LLM Gateway를 호출합니다."""
        try:
            resp = httpx.post(
                f"{self.base_url}/api/v1/generate",
                json={"prompt": prompt, "tenant_id": tenant_id},
                timeout=30.0
            )
            resp.raise_for_status()
            return resp.json()["answer"]
        except Exception as e:
            raise RuntimeError(f"Gateway generation failed: {str(e)}")

    async def stream_answer(self, prompt: str, tenant_id: str = "default"):
        """
        LLM 답변을 스트리밍 방식으로 생성합니다. (Server-Sent Events 호환)
        """
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/v1/generate/stream",
                    json={"prompt": prompt, "tenant_id": tenant_id},
                    timeout=60.0
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line:
                            # Gateway가 "data: {token}" 형식으로 준다고 가정
                            yield line
        except Exception as e:
            yield f"data: [Error] {str(e)}"

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        # 차원이 맞지 않는 경우 방어 로직 (v2 버그 예방)
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
