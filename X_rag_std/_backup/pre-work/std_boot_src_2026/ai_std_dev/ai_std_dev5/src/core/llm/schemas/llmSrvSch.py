from pydantic import BaseModel
from typing import Optional

class LlmRequest(BaseModel):
    engine_type: int = 1  # 1: Gemini, 2: OpenAI (Default 1)
    prompt: str
    context: Optional[str] = None
    persona: Optional[str] = "Professional AI Assistant"

class LlmResponse(BaseModel):
    status: str
    result: str
    model: str
    engine: str