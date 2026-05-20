import os
from pydantic import BaseModel

class Settings(BaseModel):
    llm_gateway_url: str = os.environ.get("LLM_GATEWAY_URL", "http://localhost:8010")
    vector_db_engine: str = os.environ.get("VECTOR_DB_ENGINE", "local_json")
    embedding_provider: str = os.environ.get("EMBEDDING_PROVIDER", "gemini_http")
    llm_provider: str = os.environ.get("LLM_PROVIDER", "gemini_http")

settings = Settings()
