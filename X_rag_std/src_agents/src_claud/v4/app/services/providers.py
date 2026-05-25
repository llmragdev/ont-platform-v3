"""DRY factory — embedding / LLM / chunker 인스턴스 생성 중앙화."""
from app.core.config import settings
from app.services.embedding.base import EmbeddingService
from app.services.llm.base import LlmClientBase
from app.services.pipeline.chunker import ChunkerBase, FixedSizeChunker, SemanticChunker


def get_embedding_service() -> EmbeddingService:
    if settings.embedding_provider == "gemini_http":
        from app.services.embedding.gemini_http_embedding import GeminiHttpEmbeddingService
        return GeminiHttpEmbeddingService()
    if settings.embedding_provider == "claude":
        from app.services.embedding.claude_embedding import ClaudeEmbeddingService
        return ClaudeEmbeddingService()
    from app.services.embedding.hash_embedding import HashEmbeddingService
    return HashEmbeddingService()


def get_llm_client() -> LlmClientBase:
    if settings.llm_provider == "gemini_http":
        from app.services.llm.gemini_http_llm import GeminiHttpLlmClient
        return GeminiHttpLlmClient()
    if settings.llm_provider == "claude":
        from app.services.llm.claude_llm import ClaudeLlmClient
        return ClaudeLlmClient()
    from app.services.llm.mock_llm import MockLlmClient
    return MockLlmClient()


def get_chunker() -> ChunkerBase:
    if settings.chunker_type == "fixed":
        return FixedSizeChunker()
    return SemanticChunker()
