from app.core.config import settings
from app.services.embeddings import HashEmbeddingService
from app.services.llm_client import SimpleLlmClient


def get_embedding_service():
    if settings.embedding_provider == "gemini_http":
        from app.services.gemini_http_embedding import GeminiHttpEmbeddingService

        return GeminiHttpEmbeddingService()
    return HashEmbeddingService()


def get_llm_client():
    if settings.llm_provider == "gemini_http":
        from app.services.gemini_http_llm import GeminiHttpLlmClient

        return GeminiHttpLlmClient()
    return SimpleLlmClient()
