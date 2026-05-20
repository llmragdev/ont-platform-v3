"""PDF 문서 업로드 + Chroma 벡터 검색 서비스.

- GoogleGenerativeAIEmbeddings (models/text-embedding-004) 로 임베딩
- Chroma 로컬 DB를 backend/vector_db/ 에 영속 저장
- 업로드된 파일은 backend/uploads/ 에 보관
- 문서 레지스트리는 vector_db/docs_registry.json 에 저장
- API 키가 없거나 문서가 없으면 빈 결과를 반환 (graceful degradation)
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import List

VECTOR_DB_DIR = Path(__file__).resolve().parent.parent / "vector_db"
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
REGISTRY_FILE = VECTOR_DB_DIR / "docs_registry.json"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")


class _GenAIEmbeddings:
    """google-genai SDK를 직접 사용하는 임베딩 클래스 (v1 stable API 사용).

    langchain-google-genai는 내부적으로 v1beta를 호출해 text-embedding-004가
    NOT_FOUND 오류를 낸다. google-genai SDK는 v1 stable을 사용하므로 정상 동작.
    """

    def __init__(self, api_key: str, model: str = "models/gemini-embedding-001") -> None:
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _embed_one(self, text: str) -> List[float]:
        result = self._client.models.embed_content(model=self._model, contents=text)
        return list(result.embeddings[0].values)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_one(text)


def _first_api_key() -> str | None:
    for label in ("GEMINI_API_KEY", "GEMINI_API_KEY1", "GEMINI_API_KEY2", "GEMINI_API_KEY3", "GEMINI_API_KEY4"):
        val = os.environ.get(label)
        if val:
            return val
    return None


class VectorSearchService:
    def __init__(self) -> None:
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self._api_key = _first_api_key()
        self._embeddings = None
        self._store = None
        self._registry: dict[str, dict] = self._load_registry()

    # ── persistence ────────────────────────────────────────────────────────

    def _load_registry(self) -> dict[str, dict]:
        if REGISTRY_FILE.exists():
            try:
                return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_registry(self) -> None:
        REGISTRY_FILE.write_text(json.dumps(self._registry, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── lazy init ──────────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return self._api_key is not None

    def _get_embeddings(self):
        if self._embeddings is None:
            if not self._api_key:
                raise RuntimeError("GEMINI_API_KEY not available for embeddings")
            self._embeddings = _GenAIEmbeddings(api_key=self._api_key, model=EMBEDDING_MODEL)
        return self._embeddings

    def _get_store(self):
        if self._store is None:
            from langchain_chroma import Chroma
            self._store = Chroma(
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=self._get_embeddings(),
            )
        return self._store

    # ── public API ─────────────────────────────────────────────────────────

    def ingest(self, file_path: str | Path, filename: str) -> dict:
        """PDF 파일을 로드해 청크 분할 후 Chroma에 임베딩 저장."""
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()
        splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(pages)
        for split in splits:
            split.metadata["doc_id"] = doc_id
            split.metadata["filename"] = filename

        store = self._get_store()
        store.add_documents(splits)

        info: dict = {
            "doc_id": doc_id,
            "filename": filename,
            "page_count": len(pages),
            "chunk_count": len(splits),
            "file_path": str(file_path),
        }
        self._registry[doc_id] = info
        self._save_registry()
        return info

    def search(self, query: str, k: int = 3) -> list[dict]:
        """유사 문서 청크 검색. API 키 없거나 오류 시 빈 리스트 반환."""
        if not self._registry or not self._api_key:
            return []
        try:
            store = self._get_store()
            results = store.similarity_search_with_score(query, k=k)
        except Exception:
            return []
        return [
            {
                "text": doc.page_content,
                "score": float(score),
                "doc_id": doc.metadata.get("doc_id", ""),
                "filename": doc.metadata.get("filename", ""),
                "page": doc.metadata.get("page", 0),
            }
            for doc, score in results
        ]

    def list_documents(self, company_id: str | None = None) -> list[dict]:
        """문서 목록 반환. company_id 지정 시 해당 테넌트 문서만 반환.

        company_id가 None이거나 "default"이면 전체 반환 (기존 호환).
        레지스트리에 company_id 필드가 없는 레코드는 "default"로 간주.
        """
        docs = list(self._registry.values())
        if not company_id or company_id == "default":
            return docs
        return [d for d in docs if d.get("company_id", "default") == company_id]

    def delete(self, doc_id: str) -> bool:
        try:
            store = self._get_store()
            existing = store.get(where={"doc_id": doc_id})
            if existing["ids"]:
                store.delete(ids=existing["ids"])
            info = self._registry.pop(doc_id, None)
            self._save_registry()
            if info:
                fp = Path(info.get("file_path", ""))
                if fp.exists():
                    fp.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def health(self) -> dict:
        return {
            "available": self.available,
            "document_count": len(self._registry),
            "embedding_model": EMBEDDING_MODEL,
        }
