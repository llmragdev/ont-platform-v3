from app.core import config as config_module
from app.models.schemas import ChunkMetadata, RetrievedChunk
from app.services.gemini_http_embedding import GeminiHttpEmbeddingService
from app.services.gemini_http_llm import GeminiHttpLlmClient


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


def test_gemini_embedding_uses_gateway_without_api_key(monkeypatch):
    requests = []
    monkeypatch.setattr(config_module.settings, "llm_gateway_url", "http://gateway:8010")

    def fake_post(url, json, timeout):
        requests.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse({"embedding": [0.1, 0.2, 0.3]})

    monkeypatch.setattr("app.services.gemini_http_embedding.httpx.post", fake_post)

    service = GeminiHttpEmbeddingService()
    assert service.embed_text("hello", company_id="company_a") == [0.1, 0.2, 0.3]
    assert requests == [
        {
            "url": "http://gateway:8010/api/v1/embed",
            "json": {"text": "hello", "company_id": "company_a"},
            "timeout": 30.0,
        }
    ]


def test_gemini_llm_uses_gateway_without_api_key(monkeypatch):
    requests = []
    monkeypatch.setattr(config_module.settings, "llm_gateway_url", "http://gateway:8010")

    def fake_post(url, json, timeout):
        requests.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse({"answer": "ok"})

    monkeypatch.setattr("app.services.gemini_http_llm.httpx.post", fake_post)

    client = GeminiHttpLlmClient()
    chunk = RetrievedChunk(
        chunk_id="doc_1#chunk0",
        content="source text",
        metadata=ChunkMetadata(
            source_name="doc.txt",
            source_url="/tmp/doc.txt",
            category_mid="policy",
            vector_db_id="vdb_policy_01",
            doc_id="doc_1",
            company_id="company_a",
        ),
        similarity_score=0.9,
    )
    assert client.generate_answer("question", [chunk], company_id="company_a") == "ok"
    assert requests[0]["url"] == "http://gateway:8010/api/v1/generate"
    assert requests[0]["json"]["company_id"] == "company_a"
    assert "source text" in requests[0]["json"]["prompt"]
