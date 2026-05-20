import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseModel):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    embed_model: str = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")
    llm_model: str = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash-lite")
    embed_cache_ttl: int = int(os.getenv("EMBED_CACHE_TTL", "3600"))
    embed_cache_max: int = int(os.getenv("EMBED_CACHE_MAX", "10000"))
    gemini_api_base: str = "https://generativelanguage.googleapis.com/v1beta"


settings = Settings()
