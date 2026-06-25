"""Priority 1-3: OntologyRepository + Index Integration Tests"""
import sys
import json
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.tenant_context import TenantContext
from app.repositories.ontology import OntologyRepository


class TestOntologyRepositoryIntegration:
    """Test Repository with Index backend"""

    @pytest.fixture
    def repo(self):
        return OntologyRepository()

    @pytest.fixture
    def ctx(self):
        # Use unique company/project per test to avoid index cache issues
        unique_id = str(uuid.uuid4())[:8]
        return TenantContext(
            user_id="test_user",
            company_id=f"test_company_{unique_id}",
            project_id=f"test_project_{unique_id}",
            role="Admin",
            permissions={}
        )

    def test_save_and_list_entities(self, repo, ctx):
        """Test saving and listing entities"""
        doc_data = {
            "doc_id": "doc_1",
            "entities": [
                {"entity_id": "e1", "type": "Person", "name": "Alice", "properties": {"age": 30}},
                {"entity_id": "e2", "type": "Person", "name": "Bob", "properties": {"age": 25}},
                {"entity_id": "e3", "type": "Organization", "name": "Corp A", "properties": {"size": "large"}},
            ],
            "relationships": []
        }

        repo.save_document("doc_1", doc_data, ctx)
        entities = repo.list_all_entities(ctx)

        assert len(entities) == 3
        assert all(e.get("doc_id") == "doc_1" for e in entities)

    def test_find_entities_by_type_indexed(self, repo, ctx):
        """Test finding entities by type using index"""
        doc_data = {
            "doc_id": "doc_2",
            "entities": [
                {"entity_id": "p1", "type": "Person", "name": "Alice"},
                {"entity_id": "p2", "type": "Person", "name": "Bob"},
                {"entity_id": "o1", "type": "Organization", "name": "Corp"},
            ],
            "relationships": []
        }

        repo.save_document("doc_2", doc_data, ctx)
        persons = repo.find_entities_by_type("Person", ctx)

        assert len(persons) == 2
        assert all(e.get("type") == "Person" for e in persons)

    def test_find_entities_by_property(self, repo, ctx):
        """Test finding entities by property"""
        doc_data = {
            "doc_id": "doc_3",
            "entities": [
                {"entity_id": "e1", "type": "Person", "properties": {"dept": "Engineering"}},
                {"entity_id": "e2", "type": "Person", "properties": {"dept": "Sales"}},
                {"entity_id": "e3", "type": "Person", "properties": {"dept": "Engineering"}},
            ],
            "relationships": []
        }

        repo.save_document("doc_3", doc_data, ctx)
        eng_staff = repo.find_entities_by_property("dept", "Engineering", ctx)

        assert len(eng_staff) == 2

    def test_save_and_list_relationships(self, repo, ctx):
        """Test saving and listing relationships"""
        doc_data = {
            "doc_id": "doc_4",
            "entities": [
                {"entity_id": "p1", "type": "Person"},
                {"entity_id": "o1", "type": "Organization"},
            ],
            "relationships": [
                {
                    "relation_id": "r1",
                    "from_entity_id": "p1",
                    "to_entity_id": "o1",
                    "type": "WorksAt",
                    "properties": {"since": 2020}
                },
            ]
        }

        repo.save_document("doc_4", doc_data, ctx)
        rels = repo.list_all_relationships(ctx)

        assert len(rels) == 1
        assert rels[0].get("type") == "WorksAt"

    def test_multi_document_index(self, repo, ctx):
        """Test indexing across multiple documents"""
        for i in range(3):
            doc_data = {
                "doc_id": f"doc_{i}",
                "entities": [
                    {"entity_id": f"e_{i}_1", "type": "Person", "name": f"Person {i}"},
                    {"entity_id": f"e_{i}_2", "type": "Organization", "name": f"Org {i}"},
                ],
                "relationships": []
            }
            repo.save_document(f"doc_{i}", doc_data, ctx)

        entities = repo.list_all_entities(ctx)
        assert len(entities) == 6  # 3 docs * 2 entities

        persons = repo.find_entities_by_type("Person", ctx)
        assert len(persons) == 3

    def test_list_entities_with_doc_filter(self, repo, ctx):
        """Test listing entities with doc_ids filter"""
        # Create 2 documents
        repo.save_document("doc_A", {
            "doc_id": "doc_A",
            "entities": [
                {"entity_id": "eA1", "type": "Person"},
                {"entity_id": "eA2", "type": "Person"},
            ],
            "relationships": []
        }, ctx)

        repo.save_document("doc_B", {
            "doc_id": "doc_B",
            "entities": [
                {"entity_id": "eB1", "type": "Organization"},
            ],
            "relationships": []
        }, ctx)

        # Query only doc_A
        entities = repo.list_all_entities(ctx, doc_ids=["doc_A"])
        assert len(entities) == 2
        assert all(e.get("doc_id") == "doc_A" for e in entities)

    def test_index_stats(self, repo, ctx):
        """Test that index tracks statistics"""
        doc_data = {
            "doc_id": "doc_stats",
            "entities": [
                {"entity_id": f"e{i}", "type": f"Type_{i % 3}"}
                for i in range(100)
            ],
            "relationships": [
                {
                    "relation_id": f"r{i}",
                    "from_entity_id": f"e{i}",
                    "to_entity_id": f"e{(i + 1) % 100}",
                    "type": "LinksTo"
                }
                for i in range(100)
            ]
        }

        repo.save_document("doc_stats", doc_data, ctx)
        index = repo._get_index(ctx)
        stats = index.get_index_stats()

        assert stats["total_entities"] == 100
        assert stats["total_relationships"] == 100
        assert stats["documents"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
