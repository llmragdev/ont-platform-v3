"""Priority 1-2: SQLite Index Performance Tests"""
import sys
import time
import uuid
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.ontology_index import OntologyIndex


class TestOntologyIndexPerformance:
    """Performance tests for index vs full scan"""

    def test_index_creation(self):
        """Test index creation"""
        unique_id = str(uuid.uuid4())[:8]
        index = OntologyIndex(f"test_company_{unique_id}", f"test_project_{unique_id}")
        stats = index.get_index_stats()
        assert stats["total_entities"] == 0
        assert stats["total_relationships"] == 0

    def test_batch_index_1k_entities(self):
        """Test indexing 1K entities"""
        unique_id = str(uuid.uuid4())[:8]
        index = OntologyIndex(f"test_1k_{unique_id}", f"test_{unique_id}")
        index.clear_index()

        entities = [
            {
                "entity_id": f"entity_{i}",
                "type": f"Type_{i % 10}",
                "name": f"Entity {i}",
                "properties": {"value": i, "category": f"cat_{i % 5}"}
            }
            for i in range(1000)
        ]

        start = time.time()
        index.index_entities_batch(entities, "doc_1")
        duration = time.time() - start

        stats = index.get_index_stats()
        assert stats["total_entities"] == 1000
        assert duration < 1.0, f"Indexing 1K entities took {duration}s (should be < 1s)"

    def test_batch_index_10k_entities(self):
        """Test indexing 10K entities"""
        index = OntologyIndex(f"test_10k_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        entities = [
            {
                "entity_id": f"entity_{i}",
                "type": f"Type_{i % 20}",
                "name": f"Entity {i}",
                "properties": {"value": i, "category": f"cat_{i % 10}"}
            }
            for i in range(10000)
        ]

        start = time.time()
        index.index_entities_batch(entities, "doc_1")
        duration = time.time() - start

        stats = index.get_index_stats()
        assert stats["total_entities"] == 10000
        assert duration < 5.0, f"Indexing 10K entities took {duration}s (should be < 5s)"

    def test_query_by_type_1k(self):
        """Test querying 1K indexed entities by type"""
        index = OntologyIndex(f"query_1k_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        entities = [
            {
                "entity_id": f"entity_{i}",
                "type": f"Type_{i % 10}",
                "name": f"Entity {i}",
            }
            for i in range(1000)
        ]
        index.index_entities_batch(entities, "doc_1")

        # Query
        start = time.time()
        results = index.query_entities(entity_type="Type_0")
        duration = time.time() - start

        assert len(results) == 100  # 1000 / 10 types
        assert duration < 0.1, f"Query took {duration}s (should be < 0.1s)"

    def test_query_by_type_10k(self):
        """Test querying 10K indexed entities by type"""
        index = OntologyIndex(f"query_10k_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        entities = [
            {
                "entity_id": f"entity_{i}",
                "type": f"Type_{i % 20}",
                "name": f"Entity {i}",
            }
            for i in range(10000)
        ]
        index.index_entities_batch(entities, "doc_1")

        # Query
        start = time.time()
        results = index.query_entities(entity_type="Type_0")
        duration = time.time() - start

        assert len(results) == 500  # 10000 / 20 types
        assert duration < 0.1, f"Query took {duration}s (should be < 0.1s)"

    def test_relationships_batch_1k(self):
        """Test indexing 1K relationships"""
        index = OntologyIndex(f"rel_1k_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        relations = [
            {
                "relation_id": f"rel_{i}",
                "from_entity_id": f"entity_{i}",
                "to_entity_id": f"entity_{(i + 1) % 1000}",
                "type": f"RelType_{i % 5}",
                "properties": {"weight": i}
            }
            for i in range(1000)
        ]

        start = time.time()
        index.index_relationships_batch(relations, "doc_1")
        duration = time.time() - start

        stats = index.get_index_stats()
        assert stats["total_relationships"] == 1000
        assert duration < 1.0, f"Indexing 1K relationships took {duration}s"

    def test_query_relationships_1k(self):
        """Test querying relationships by type"""
        index = OntologyIndex(f"query_rel_1k_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        relations = [
            {
                "relation_id": f"rel_{i}",
                "from_entity_id": f"entity_{i}",
                "to_entity_id": f"entity_{(i + 1) % 1000}",
                "type": f"RelType_{i % 5}",
            }
            for i in range(1000)
        ]
        index.index_relationships_batch(relations, "doc_1")

        start = time.time()
        results = index.query_relationships(relation_type="RelType_0")
        duration = time.time() - start

        assert len(results) == 200  # 1000 / 5 types
        assert duration < 0.1, f"Query took {duration}s"

    def test_count_entities(self):
        """Test counting entities by type"""
        index = OntologyIndex(f"count_test_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        entities = [
            {
                "entity_id": f"entity_{i}",
                "type": f"Type_{i % 3}",
                "name": f"Entity {i}",
            }
            for i in range(300)
        ]
        index.index_entities_batch(entities, "doc_1")

        count = index.count_entities("Type_0")
        assert count == 100

        total = index.count_entities()
        assert total == 300

    def test_delete_doc_index(self):
        """Test deleting all entities for a document"""
        index = OntologyIndex(f"delete_test_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        entities = [
            {
                "entity_id": f"entity_{i}",
                "type": "TestType",
            }
            for i in range(100)
        ]
        index.index_entities_batch(entities, "doc_1")

        assert index.count_entities() == 100

        index.delete_doc_index("doc_1")
        assert index.count_entities() == 0

    def test_multi_document_index(self):
        """Test indexing entities from multiple documents"""
        index = OntologyIndex(f"multi_doc_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        # Index from 5 documents
        for doc_id in range(5):
            entities = [
                {
                    "entity_id": f"entity_{doc_id}_{i}",
                    "type": f"Type_{i % 3}",
                }
                for i in range(200)
            ]
            index.index_entities_batch(entities, f"doc_{doc_id}")

        stats = index.get_index_stats()
        assert stats["total_entities"] == 1000
        assert stats["documents"] == 5

    def test_index_stats(self):
        """Test index statistics"""
        index = OntologyIndex(f"stats_test_{str(uuid.uuid4())[:8]}", f"test_{str(uuid.uuid4())[:8]}")
        index.clear_index()

        entities = [{"entity_id": f"e_{i}", "type": "Test"} for i in range(100)]
        index.index_entities_batch(entities, "doc_1")

        relations = [
            {
                "relation_id": f"r_{i}",
                "from_entity_id": f"e_{i}",
                "to_entity_id": f"e_{(i + 1) % 100}",
                "type": "TestRel"
            }
            for i in range(100)
        ]
        index.index_relationships_batch(relations, "doc_1")

        stats = index.get_index_stats()
        assert stats["total_entities"] == 100
        assert stats["total_relationships"] == 100
        assert stats["documents"] == 1
        assert "db_path" in stats
        assert "db_size_mb" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
