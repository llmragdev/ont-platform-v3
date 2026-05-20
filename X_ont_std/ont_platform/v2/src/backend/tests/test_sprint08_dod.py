"""Sprint 08 DoD Test — Query Planner & Repository Layer (D01~D05)."""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.query_intent import IntentType

client = TestClient(app)

# Test headers
CTX_HEADERS = {
    "X-User-Id": "test-user",
    "X-Company-Id": "company-s08",
    "X-Project-Id": "proj-s08",
    "X-Role": "Admin"
}


@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    """Create sample ontology and vector data for testing."""
    # 1. Create an ontology entity with specific property
    doc_id = "test-doc-s08"
    entity = {
        "name": "Antigravity Inc",
        "type": "ORGANIZATION",
        "properties": {"location": "Seoul", "status": "active"}
    }
    client.post(f"/api/ontology/{doc_id}/entities", json=entity, headers=CTX_HEADERS)
    
    # 2. Upload a dummy document for vector search (if needed)
    # For unit testing, we might mock vector search, but here we check the integration
    yield


def test_d01_repository_refactoring():
    """D01: OntologyService should use Repository (Verify data persists in correct location)."""
    # This is implicitly verified if other tests pass, 
    # but we can check if the file exists in the storage path.
    from storage_config import get_ontology_path
    p = get_ontology_path("company-s08", "proj-s08") / "test-doc-s08.json"
    assert p.exists()


def test_d00_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_d02_intent_classification_descriptive():
    """D02: Classify general question as descriptive."""
    resp = client.post("/api/hybrid/ask", json={"query": "What is Antigravity Inc?"}, headers=CTX_HEADERS)
    if resp.status_code != 200:
        print(f"\nDEBUG STATUS: {resp.status_code}")
        print(f"DEBUG BODY: {resp.text}")
        pytest.fail(f"Request failed with {resp.status_code}: {resp.text}")
    data = resp.json()
    assert data["intent"] == IntentType.DESCRIPTIVE


def test_d03_intent_classification_filter():
    """D03: Classify property-based question as filter."""
    # The heuristic looks for ":" or "=" or specific keywords
    resp = client.post("/api/hybrid/ask", json={"query": "location: Seoul인 엔티티 찾아줘"}, headers=CTX_HEADERS)
    if resp.status_code != 200:
        raise Exception(f"Request failed {resp.status_code}: {resp.text}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == IntentType.FILTER
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["name"] == "Antigravity Inc"


def test_d04_intent_classification_hybrid():
    """D04: Classify '하이브리드' keyword as hybrid."""
    resp = client.post("/api/hybrid/ask", json={"query": "하이브리드 검색 수행해줘"}, headers=CTX_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == IntentType.HYBRID


def test_d05_tenant_isolation_in_repository():
    """D05: Verify company-s08 data is not visible to company-other."""
    OTHER_HEADERS = CTX_HEADERS.copy()
    OTHER_HEADERS["X-Company-Id"] = "company-other"
    
    # Try to filter in another company
    resp = client.post("/api/hybrid/ask", json={"query": "location: Seoul인 엔티티 찾아줘"}, headers=OTHER_HEADERS)
    if resp.status_code != 200:
        print(f"\nDEBUG STATUS: {resp.status_code}")
        print(f"DEBUG BODY: {resp.text}")
    assert resp.status_code == 200
    data = resp.json()
    # Should not find the entity from company-s08
    assert len(data["sources"]) == 0
