"""신규 기능 통합 테스트.

테스트 범위:
  - ontology_store: CRUD 전 계층
  - ontology_query_engine: filter / compare / calculate / find_by_category / search_relations
  - query_classifier: 폴백(API 없을 때 descriptive 반환)
  - /api/ontology/mgmt/schema GET/POST/DELETE
  - /api/ontology/{doc_id}/entities GET/POST/PUT/DELETE
  - /api/ontology/{doc_id}/relationships GET/POST/DELETE
  - /api/ontology/{doc_id}/graph GET
  - /api/ontology GET (목록)
  - /api/hybrid/ask POST (LLM 없이 rule-based 폴백)
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

# ── 공통 픽스처 ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_ontology_db(tmp_path, monkeypatch):
    """테스트마다 격리된 ontology_db 디렉터리 사용."""
    from app import ontology_store
    monkeypatch.setattr(ontology_store, "ONTOLOGY_DB_DIR", tmp_path)
    monkeypatch.setattr(ontology_store, "REGISTRY_FILE", tmp_path / "ontology_registry.json")
    monkeypatch.setattr(ontology_store, "SCHEMA_FILE", tmp_path / "domain_config.json")
    yield


@pytest.fixture()
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture()
def sample_ontology(tmp_path):
    """테스트용 온톨로지 데이터 미리 삽입."""
    from app import ontology_store
    data = {
        "doc_id": "test_doc",
        "filename": "test.pdf",
        "entities": [
            {"id": "E001", "type": "PRODUCT", "name": "Virtual Warehouse",
             "properties": {"과금방식": "초단위", "계층": "컴퓨팅"}},
            {"id": "E002", "type": "PRODUCT", "name": "Snowpipe",
             "properties": {"과금방식": "Serverless", "계층": "Cloud Services"}},
            {"id": "E003", "type": "PERSON",  "name": "Benoit Dageville",
             "properties": {"역할": "창립자", "소속": "Oracle 출신"}},
            {"id": "E004", "type": "METRIC",  "name": "전체 고객수",
             "properties": {"value": "8537", "unit": "개", "period": "FY2023"}},
            {"id": "E005", "type": "METRIC",  "name": "$1M 이상 고객수",
             "properties": {"value": "330", "unit": "개", "period": "FY2023"}},
            {"id": "E006", "type": "ORGANIZATION", "name": "Snowflake",
             "properties": {"설립": "2012", "상장": "NYSE"}},
        ],
        "relationships": [
            {"id": "R001", "from_id": "E003", "relation": "창립자_of", "to_id": "E006"},
            {"id": "R002", "from_id": "E001", "relation": "속한_계층", "to_id": "E002"},
        ],
    }
    ontology_store.save_ontology("test_doc", data)
    return data


# ── ontology_store 단위 테스트 ─────────────────────────────────────────────────

class TestOntologyStore:
    def test_save_and_load(self):
        from app import ontology_store
        ontology_store.save_ontology("doc1", {"doc_id": "doc1", "entities": [], "relationships": []})
        loaded = ontology_store.load_ontology("doc1")
        assert loaded is not None
        assert loaded["doc_id"] == "doc1"

    def test_list_ontologies(self):
        from app import ontology_store
        ontology_store.save_ontology("doc1", {"doc_id": "doc1", "entities": [{"id": "E1", "type": "PERSON", "name": "A", "properties": {}}], "relationships": []})
        ontology_store.save_ontology("doc2", {"doc_id": "doc2", "entities": [], "relationships": []})
        lst = ontology_store.list_ontologies()
        ids = {d["doc_id"] for d in lst}
        assert {"doc1", "doc2"} == ids

    def test_delete_ontology(self):
        from app import ontology_store
        ontology_store.save_ontology("doc1", {"doc_id": "doc1", "entities": [], "relationships": []})
        assert ontology_store.delete_ontology("doc1") is True
        assert ontology_store.load_ontology("doc1") is None

    def test_upsert_entity_new(self):
        from app import ontology_store
        ontology_store.save_ontology("d", {"doc_id": "d", "entities": [], "relationships": []})
        e = ontology_store.upsert_entity("d", {"id": "E1", "type": "PERSON", "name": "Alice", "properties": {}})
        assert e["id"] == "E1"
        data = ontology_store.load_ontology("d")
        assert len(data["entities"]) == 1

    def test_upsert_entity_update(self):
        from app import ontology_store
        ontology_store.save_ontology("d", {"doc_id": "d", "entities": [{"id": "E1", "type": "PERSON", "name": "Alice", "properties": {}}], "relationships": []})
        ontology_store.upsert_entity("d", {"id": "E1", "type": "PERSON", "name": "Bob", "properties": {}})
        data = ontology_store.load_ontology("d")
        assert data["entities"][0]["name"] == "Bob"
        assert len(data["entities"]) == 1

    def test_delete_entity_cascades_relationships(self):
        from app import ontology_store
        ontology_store.save_ontology("d", {
            "doc_id": "d",
            "entities": [
                {"id": "E1", "type": "PERSON", "name": "A", "properties": {}},
                {"id": "E2", "type": "PERSON", "name": "B", "properties": {}},
            ],
            "relationships": [{"id": "R1", "from_id": "E1", "relation": "KNOWS", "to_id": "E2"}],
        })
        ontology_store.delete_entity("d", "E1")
        data = ontology_store.load_ontology("d")
        assert len(data["entities"]) == 1
        assert len(data["relationships"]) == 0

    def test_schema_builtin_types(self):
        from app import ontology_store
        schema = ontology_store.get_schema()
        names = {t["name"] for t in schema["entity_types"]}
        for expected in ("PERSON", "ORGANIZATION", "PRODUCT", "METRIC", "CONCEPT", "CATEGORY", "EVENT", "LOCATION"):
            assert expected in names

    def test_add_and_delete_entity_type(self):
        from app import ontology_store
        ontology_store.add_entity_type({"name": "CONTRACT", "description": "계약서", "properties": []})
        schema = ontology_store.get_schema()
        assert any(t["name"] == "CONTRACT" for t in schema["entity_types"])
        ontology_store.delete_entity_type("CONTRACT")
        schema2 = ontology_store.get_schema()
        assert all(t["name"] != "CONTRACT" for t in schema2["entity_types"])

    def test_delete_builtin_type_returns_false(self):
        from app import ontology_store
        assert ontology_store.delete_entity_type("PERSON") is False

    def test_get_graph(self, sample_ontology):
        from app import ontology_store
        graph = ontology_store.get_graph("test_doc")
        assert len(graph["nodes"]) == 6
        assert len(graph["edges"]) == 2


# ── ontology_query_engine 단위 테스트 ─────────────────────────────────────────

class TestOntologyQueryEngine:
    def test_filter_by_property(self, sample_ontology):
        from app import ontology_query_engine
        results = ontology_query_engine.filter_by_property("PRODUCT", "과금방식", "Serverless")
        assert len(results) == 1
        assert results[0]["name"] == "Snowpipe"

    def test_filter_by_property_fuzzy(self, sample_ontology):
        from app import ontology_query_engine
        results = ontology_query_engine.filter_by_property("PRODUCT", "과금방식", "serverless")  # 소문자
        assert len(results) >= 1

    def test_filter_empty_result(self, sample_ontology):
        from app import ontology_query_engine
        results = ontology_query_engine.filter_by_property("PRODUCT", "과금방식", "없는값123")
        assert results == []

    def test_compare_entities(self, sample_ontology):
        from app import ontology_query_engine
        result = ontology_query_engine.compare_entities(["Virtual Warehouse", "Snowpipe"])
        assert "headers" in result
        assert "rows" in result
        assert len(result["rows"]) == 2

    def test_compare_entities_common_keys(self, sample_ontology):
        from app import ontology_query_engine
        result = ontology_query_engine.compare_entities(["Virtual Warehouse", "Snowpipe"])
        # 둘 다 과금방식과 계층 속성을 가짐
        assert "과금방식" in result["headers"] or "계층" in result["headers"]

    def test_calculate_sum(self, sample_ontology):
        from app import ontology_query_engine
        result = ontology_query_engine.calculate(["전체 고객수", "$1M 이상 고객수"], "sum")
        assert result["result"] == pytest.approx(8867.0)

    def test_calculate_ratio(self, sample_ontology):
        from app import ontology_query_engine
        result = ontology_query_engine.calculate(["$1M 이상 고객수", "전체 고객수"], "ratio")
        assert result["result"] == pytest.approx(330 / 8537, rel=1e-3)

    def test_calculate_no_match(self, sample_ontology):
        from app import ontology_query_engine
        result = ontology_query_engine.calculate(["없는지표XYZ"], "sum")
        assert "error" in result

    def test_find_by_category(self, sample_ontology):
        from app import ontology_query_engine
        results = ontology_query_engine.find_by_category("PRODUCT", "Serverless")
        assert any(r["name"] == "Snowpipe" for r in results)

    def test_search_relations(self, sample_ontology):
        from app import ontology_query_engine
        results = ontology_query_engine.search_relations("Benoit Dageville")
        assert len(results) >= 1
        assert any(r["relation"] == "창립자_of" for r in results)

    def test_search_relations_no_match(self, sample_ontology):
        from app import ontology_query_engine
        results = ontology_query_engine.search_relations("존재하지않는이름XYZ")
        assert results == []


# ── query_classifier 단위 테스트 ──────────────────────────────────────────────

class TestQueryClassifier:
    def test_fallback_when_no_api_key(self, monkeypatch):
        """API 키 없을 때 descriptive 폴백."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY1", raising=False)
        from app import query_classifier
        result = query_classifier.classify("테스트 질문")
        assert result["type"] == "descriptive"
        assert "entities" in result
        assert "operation" in result


# ── API 엔드포인트 통합 테스트 ────────────────────────────────────────────────

class TestOntologyMgmtSchemaAPI:
    def test_get_schema(self, client):
        r = client.get("/api/ontology/mgmt/schema")
        assert r.status_code == 200
        body = r.json()
        assert "entity_types" in body
        assert "relation_types" in body
        types = {t["name"] for t in body["entity_types"]}
        assert "PERSON" in types and "METRIC" in types

    def test_add_and_delete_entity_type(self, client):
        r = client.post("/api/ontology/mgmt/schema/entity-types",
                        json={"name": "CONTRACT", "description": "계약", "properties": ["value"]})
        assert r.status_code == 200
        assert r.json()["name"] == "CONTRACT"

        r2 = client.delete("/api/ontology/mgmt/schema/entity-types/CONTRACT")
        assert r2.status_code == 200

        r3 = client.get("/api/ontology/mgmt/schema")
        names = {t["name"] for t in r3.json()["entity_types"]}
        assert "CONTRACT" not in names

    def test_delete_builtin_type_404(self, client):
        r = client.delete("/api/ontology/mgmt/schema/entity-types/PERSON")
        assert r.status_code == 404

    def test_add_and_delete_relation_type(self, client):
        r = client.post("/api/ontology/mgmt/schema/relation-types",
                        json={"name": "OWNS", "from_type": "PERSON", "to_type": "PRODUCT"})
        assert r.status_code == 200
        assert r.json()["name"] == "OWNS"

        r2 = client.delete("/api/ontology/mgmt/schema/relation-types/OWNS")
        assert r2.status_code == 200


class TestOntologyEntityAPI:
    def test_entities_list(self, client, sample_ontology):
        r = client.get("/api/ontology/test_doc/entities")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 6

    def test_entities_filter_by_type(self, client, sample_ontology):
        r = client.get("/api/ontology/test_doc/entities", params={"entity_type": "PRODUCT"})
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_entity_create(self, client):
        from app import ontology_store
        ontology_store.save_ontology("doc_new", {"doc_id": "doc_new", "entities": [], "relationships": []})
        r = client.post("/api/ontology/doc_new/entities",
                        json={"type": "PERSON", "name": "Test Person", "properties": {"role": "tester"}})
        assert r.status_code == 200
        assert r.json()["name"] == "Test Person"

    def test_entity_update(self, client, sample_ontology):
        r = client.put("/api/ontology/test_doc/entities/E001",
                       json={"name": "Virtual Warehouse Updated"})
        assert r.status_code == 200
        assert r.json()["name"] == "Virtual Warehouse Updated"

    def test_entity_delete(self, client, sample_ontology):
        r = client.delete("/api/ontology/test_doc/entities/E003")
        assert r.status_code == 200
        r2 = client.get("/api/ontology/test_doc/entities")
        assert r2.json()["total"] == 5

    def test_entity_not_found(self, client, sample_ontology):
        r = client.delete("/api/ontology/test_doc/entities/ENOTEXIST")
        assert r.status_code == 404

    def test_doc_not_found(self, client):
        r = client.get("/api/ontology/no_such_doc/entities")
        assert r.status_code == 404


class TestOntologyRelationshipAPI:
    def test_relationships_list(self, client, sample_ontology):
        r = client.get("/api/ontology/test_doc/relationships")
        assert r.status_code == 200
        assert len(r.json()["relationships"]) == 2

    def test_relationship_create(self, client, sample_ontology):
        r = client.post("/api/ontology/test_doc/relationships",
                        json={"from_id": "E001", "relation": "USED_BY", "to_id": "E006"})
        assert r.status_code == 200
        rel = r.json()
        assert rel["relation"] == "USED_BY"
        assert "id" in rel

    def test_relationship_delete(self, client, sample_ontology):
        r = client.delete("/api/ontology/test_doc/relationships/R001")
        assert r.status_code == 200
        r2 = client.get("/api/ontology/test_doc/relationships")
        assert len(r2.json()["relationships"]) == 1

    def test_relationship_not_found(self, client, sample_ontology):
        r = client.delete("/api/ontology/test_doc/relationships/RNOTEXIST")
        assert r.status_code == 404


class TestOntologyGraphAPI:
    def test_graph_shape(self, client, sample_ontology):
        r = client.get("/api/ontology/test_doc/graph")
        assert r.status_code == 200
        body = r.json()
        assert len(body["nodes"]) == 6
        assert len(body["edges"]) == 2

    def test_graph_node_fields(self, client, sample_ontology):
        r = client.get("/api/ontology/test_doc/graph")
        node = r.json()["nodes"][0]
        assert "id" in node and "label" in node and "type" in node

    def test_graph_not_found(self, client):
        r = client.get("/api/ontology/no_such_doc/graph")
        assert r.status_code == 404


class TestOntologyListAPI:
    def test_list_empty(self, client):
        r = client.get("/api/ontology")
        assert r.status_code == 200
        assert r.json()["ontologies"] == []

    def test_list_after_save(self, client, sample_ontology):
        r = client.get("/api/ontology")
        assert r.status_code == 200
        assert len(r.json()["ontologies"]) == 1
        assert r.json()["ontologies"][0]["doc_id"] == "test_doc"


class TestHybridAskAPI:
    def test_hybrid_ask_no_ontology(self, client):
        """온톨로지/문서 없을 때도 200 반환 (폴백 답변)."""
        r = client.post("/api/hybrid/ask", json={"question": "Snowflake란 무엇인가요?"})
        assert r.status_code == 200
        body = r.json()
        assert "answer" in body
        assert "query_type" in body
        assert "classification" in body
        assert "ontology_result" in body
        assert "steps" in body

    def test_hybrid_ask_with_ontology(self, client, sample_ontology):
        """온톨로지 있을 때 filter 유형 감지 → 구조형 결과 포함 가능."""
        r = client.post("/api/hybrid/ask",
                        json={"question": "Serverless 과금 기능은?", "doc_ids": ["test_doc"]})
        assert r.status_code == 200
        body = r.json()
        assert body["query_type"] in ("filter", "compare", "calculate", "hybrid", "descriptive")

    def test_hybrid_ask_doc_ids_filter(self, client, sample_ontology):
        """doc_ids 지정 시 해당 문서만 검색."""
        r = client.post("/api/hybrid/ask",
                        json={"question": "고객수 합계는?", "doc_ids": ["test_doc"]})
        assert r.status_code == 200
        assert r.json()["query_type"] in ("calculate", "filter", "descriptive", "hybrid")
