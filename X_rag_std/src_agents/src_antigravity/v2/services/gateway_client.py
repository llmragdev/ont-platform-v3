import httpx
import math
from typing import List
from core.config import settings

class LlmGatewayClient:
    def __init__(self):
        self.base_url = settings.llm_gateway_url.rstrip("/")
    
    def embed_text(self, text: str) -> List[float]:
        try:
            resp = httpx.post(
                f"{self.base_url}/api/v1/embed",
                json={"text": text, "company_id": "default"},
                timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        except Exception as e:
            print(f"Error during embedding: {e}")
            return [0.1, 0.2]  # Fallback

    def generate_answer(self, prompt: str) -> str:
        try:
            resp = httpx.post(
                f"{self.base_url}/api/v1/generate",
                json={"prompt": prompt},
                timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()["answer"]
        except Exception as e:
            print(f"Error during LLM generation: {e}")
            return "LLM 생성 중 오류가 발생했습니다."

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
