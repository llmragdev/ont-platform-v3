"""Integration tests for hybrid (keyword metadata + vector) search performance and quality."""
from __future__ import annotations

import sys
import tempfile
import shutil
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.vector_search import VectorSearchService
from app.models.tenant_context import TenantContext
from app.services.embedding_service import CachedEmbeddings
from tests.test_embedding_perf import MockEmbeddings

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma


class TestVectorSearchAndHybrid:
    """Test vector database indexing, shard routing, and hybrid retrieval accuracy."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Create temp directory for shard vector db
        self.temp_dir = Path(tempfile.mkdtemp())
        self.company_id = "test_company"
        self.project_id = "test_project"
        self.shard_id = "shard_1"
        
        # Mock TenantContext
        self.ctx = TenantContext(
            user_id="test_user",
            company_id=self.company_id,
            project_id=self.project_id,
            role="Admin",
            permissions={}
        )

        # Mock embeddings and cached wrapper
        self.base_embeddings = MockEmbeddings(vector_dim=128, latency_sec=0.0)
        self.embeddings = CachedEmbeddings(self.base_embeddings)
        self.search_service = VectorSearchService(self.embeddings)

        yield

        # Teardown: clean up files
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _prepare_sample_data(self, store_path: Path):
        """Prepare sample documents in Chroma store."""
        docs = [
            ("doc_1", "Project Alpha approval process and checklist", {"entity_type": "Project", "doc_id": "d1"}),
            ("doc_2", "Project Beta financial budget report", {"entity_type": "Financial", "doc_id": "d2"}),
            ("doc_3", "Shipbuilding block assembly safety manual", {"entity_type": "Manual", "doc_id": "d3"}),
            ("doc_4", "Project Alpha engineering design specification", {"entity_type": "Project", "doc_id": "d4"}),
            ("doc_5", "SAP integration interface schema for payments", {"entity_type": "System", "doc_id": "d5"}),
        ]
        
        texts = [d[1] for d in docs]
        metadatas = [
            {"doc_id": d[2]["doc_id"], "entity_type": d[2]["entity_type"], "filename": f"{d[0]}.txt"}
            for d in docs
        ]
        ids = [d[0] for d in docs]

        Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            ids=ids,
            persist_directory=str(store_path)
        )

    def test_vector_search_execution(self, monkeypatch):
        """Verify vector search returns correct score rankings and metadata."""
        shard_path = self.temp_dir / self.company_id / self.project_id / self.shard_id
        shard_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._prepare_sample_data(shard_path)

        import storage_config
        monkeypatch.setattr(storage_config, "list_shard_paths", lambda c, p: [shard_path])
        monkeypatch.setattr(storage_config, "get_vector_db_path", lambda c, p, s: shard_path)

        results = self.search_service.search("Project Alpha", self.ctx, k=2)

        assert len(results) == 2
        assert "text" in results[0]
        assert "score" in results[0]
        assert "doc_id" in results[0]
        assert "shard_id" in results[0]
        assert "Alpha" in results[0]["text"]

    def test_hybrid_search_logic(self, monkeypatch):
        """Verify hybrid metadata pre-filtering combined with vector search quality."""
        shard_path = self.temp_dir / self.company_id / self.project_id / self.shard_id
        shard_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._prepare_sample_data(shard_path)

        import storage_config
        monkeypatch.setattr(storage_config, "list_shard_paths", lambda c, p: [shard_path])
        monkeypatch.setattr(storage_config, "get_vector_db_path", lambda c, p, s: shard_path)

        store = Chroma(persist_directory=str(shard_path), embedding_function=self.embeddings)
        hits = store.similarity_search_with_score(
            "budget",
            k=3,
            filter={"entity_type": "Financial"}
        )

        assert len(hits) > 0
        doc, score = hits[0]
        assert "Beta" in doc.page_content
        assert doc.metadata["entity_type"] == "Financial"

        project_hits = store.similarity_search_with_score(
            "Alpha",
            k=5,
            filter={"entity_type": "Project"}
        )
        assert len(project_hits) == 2
        for doc, _ in project_hits:
            assert "Alpha" in doc.page_content
            assert doc.metadata["entity_type"] == "Project"
