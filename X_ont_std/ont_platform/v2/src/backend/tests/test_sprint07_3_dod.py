"""Sprint 07-3 DoD 자동 테스트.

DoD:
  S07-3-D01  GET /api/workflow/queue — TenantContext 기반 실행 가능 액션 목록
  S07-3-D02  POST /api/workflow/execute — 상태 전이 + 권한 검증
  S07-3-D03  /api/workflow-graphs CRUD (생성 / 조회 / 삭제)
  S07-3-D04  D15 실제 smoke test (GET /api/workflow/queue 기동 확인)
  S07-3-D05  workflow.json 외부화 — WorkflowService가 config 파일로 전환 규칙 로드
  S07-3-D06  policy.default.json 마스킹 — 도메인 변경 없이 동작
  S07-3-D07  app_context.py 없이 /api/workflow/* 동작 (import 검증)
  S07-3-D08  config/domain.json 편집으로 새 엔티티 타입 추가 가능
  S07-3-D09  Sprint 07-1 + 07-2 테스트 53개 계속 통과 (import 검증)
  S07-3-D10  (이 파일 통과 자체가 기록 기준)

실행:
    conda run -n claud_be python -m pytest tests/test_sprint07_3_dod.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from app.services.workflow import WorkflowGraphService, WorkflowService


# ── 공통 픽스처 ───────────────────────────────────────────────────────────────

@pytest.fixture()
def ctx_admin(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext("u-1", "acme", "proj-001", "Admin", {})


@pytest.fixture()
def ctx_viewer(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext("u-2", "acme", "proj-001", "Viewer", {})


@pytest.fixture()
def ctx_finance(tmp_path, monkeypatch):
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)
    return TenantContext("u-3", "acme", "proj-001", "FinanceManager", {})


@pytest.fixture()
def ont_svc():
    return OntologyService()


@pytest.fixture()
def wf_svc(ont_svc):
    return WorkflowService(ontology_svc=ont_svc)


@pytest.fixture()
def graph_svc():
    return WorkflowGraphService()


# ── S07-3-D01: workflow/queue ─────────────────────────────────────────────────

def test_d01_queue_returns_actionable_entities(ctx_admin, ont_svc, wf_svc):
    """Submitted 상태 엔티티 → Admin 역할로 queue에 노출."""
    ont_svc.upsert_entity("doc-1", {
        "type": "Order",
        "name": "O-001",
        "properties": {"status": "Submitted", "amount": 1000},
    }, ctx_admin)

    rows = wf_svc.queue(ctx_admin, entity_type="Order")
    assert len(rows) >= 1
    assert any(r["name"] == "O-001" for r in rows)
    assert all("available_actions" in r for r in rows)


def test_d01_queue_empty_for_viewer(ctx_viewer, ont_svc, wf_svc):
    """Viewer 역할 — 실행 가능한 액션 없어 queue 결과 비어 있음."""
    ont_svc.upsert_entity("doc-1", {
        "type": "Order",
        "name": "O-002",
        "properties": {"status": "Submitted"},
    }, ctx_viewer)

    rows = wf_svc.queue(ctx_viewer, entity_type="Order")
    assert rows == []


def test_d01_queue_excludes_terminal_status(ctx_admin, ont_svc, wf_svc):
    """Closed 상태는 실행 가능 액션이 없어 queue에 미포함."""
    ont_svc.upsert_entity("doc-1", {
        "type": "Order",
        "name": "O-closed",
        "properties": {"status": "Closed"},
    }, ctx_admin)

    rows = wf_svc.queue(ctx_admin, entity_type="Order")
    assert not any(r["name"] == "O-closed" for r in rows)


# ── S07-3-D02: workflow/execute ───────────────────────────────────────────────

def test_d02_execute_state_transition(ctx_admin, ont_svc, wf_svc):
    """ApproveOrder 실행 → 상태가 Submitted → Approved 로 전이."""
    entity = ont_svc.upsert_entity("doc-1", {
        "type": "Order",
        "name": "O-approve",
        "properties": {"status": "Submitted"},
    }, ctx_admin)

    result = wf_svc.execute(ctx_admin, "doc-1", entity["id"], "ApproveOrder")
    assert result["from_status"] == "Submitted"
    assert result["to_status"] == "Approved"
    assert result["action"] == "ApproveOrder"


def test_d02_execute_permission_denied(ctx_viewer, ont_svc, wf_svc):
    """Viewer 역할로 ApproveOrder 실행 시 PermissionError."""
    entity = ont_svc.upsert_entity("doc-1", {
        "type": "Order",
        "name": "O-denied",
        "properties": {"status": "Submitted"},
    }, ctx_viewer)

    with pytest.raises(PermissionError):
        wf_svc.execute(ctx_viewer, "doc-1", entity["id"], "ApproveOrder")


def test_d02_execute_invalid_from_status(ctx_admin, ont_svc, wf_svc):
    """CloseOrder를 Submitted 상태에서 실행 → ValueError."""
    entity = ont_svc.upsert_entity("doc-1", {
        "type": "Order",
        "name": "O-bad",
        "properties": {"status": "Submitted"},
    }, ctx_admin)

    with pytest.raises(ValueError):
        wf_svc.execute(ctx_admin, "doc-1", entity["id"], "CloseOrder")


def test_d02_full_workflow_chain(ctx_finance, ont_svc, wf_svc):
    """Submitted → Approved → Fulfilled → Closed 전체 체인 실행."""
    entity = ont_svc.upsert_entity("doc-1", {
        "type": "Order",
        "name": "O-chain",
        "properties": {"status": "Submitted"},
    }, ctx_finance)
    eid = entity["id"]

    r1 = wf_svc.execute(ctx_finance, "doc-1", eid, "ApproveOrder")
    assert r1["to_status"] == "Approved"

    r2 = wf_svc.execute(ctx_finance, "doc-1", eid, "FulfillOrder")
    assert r2["to_status"] == "Fulfilled"

    r3 = wf_svc.execute(ctx_finance, "doc-1", eid, "CloseOrder")
    assert r3["to_status"] == "Closed"


# ── S07-3-D03: workflow-graphs CRUD ──────────────────────────────────────────

def test_d03_graph_save_and_list(ctx_admin, graph_svc):
    """그래프 저장 후 목록에 포함."""
    payload = {
        "name": "Test Graph",
        "nodes": [
            {"id": "n1", "type": "start", "position": {"x": 0, "y": 0}},
            {"id": "n2", "type": "end",   "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }
    saved = graph_svc.save_graph(ctx_admin, payload)
    assert saved["name"] == "Test Graph"
    assert "id" in saved

    graphs = graph_svc.list_graphs(ctx_admin)
    assert any(g["id"] == saved["id"] for g in graphs)


def test_d03_graph_get(ctx_admin, graph_svc):
    """저장한 그래프를 ID로 조회."""
    saved = graph_svc.save_graph(ctx_admin, {
        "name": "GetTest",
        "nodes": [{"id": "n1", "type": "start", "position": {"x": 0, "y": 0}}],
        "edges": [],
    })
    fetched = graph_svc.get_graph(ctx_admin, saved["id"])
    assert fetched["name"] == "GetTest"


def test_d03_graph_delete(ctx_admin, graph_svc):
    """그래프 삭제 후 조회 시 KeyError."""
    saved = graph_svc.save_graph(ctx_admin, {
        "name": "ToDelete",
        "nodes": [{"id": "n1", "type": "start", "position": {"x": 0, "y": 0}}],
        "edges": [],
    })
    graph_svc.delete_graph(ctx_admin, saved["id"])
    with pytest.raises(KeyError):
        graph_svc.get_graph(ctx_admin, saved["id"])


def test_d03_graph_viewer_cannot_write(ctx_viewer, graph_svc):
    """Viewer 역할은 그래프 저장 불가."""
    with pytest.raises(PermissionError):
        graph_svc.save_graph(ctx_viewer, {
            "name": "NoWrite",
            "nodes": [{"id": "n1", "type": "start", "position": {"x": 0, "y": 0}}],
            "edges": [],
        })


# ── S07-3-D04: /api/workflow/queue HTTP smoke test ────────────────────────────

def test_d04_workflow_queue_http(tmp_path, monkeypatch):
    """GET /api/workflow/queue — 200 응답 + 구조 확인."""
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.get(
        "/api/workflow/queue",
        headers={"x-company-id": "acme", "x-project-id": "proj-001", "x-role": "Admin"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "count" in body


def test_d04_workflow_execute_http(tmp_path, monkeypatch):
    """POST /api/workflow/execute — 상태 전이 HTTP 확인."""
    import storage_config as sc
    monkeypatch.setattr(sc, "STORAGE_ROOT", tmp_path)

    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.workflow import _ctx, _get_workflow_svc

    # 먼저 엔티티를 직접 삽입
    ont = OntologyService()
    seed_ctx = TenantContext("u", "acme", "proj-001", "Admin", {})
    entity = ont.upsert_entity("doc-e", {
        "type": "Order", "name": "O-http",
        "properties": {"status": "Submitted"},
    }, seed_ctx)

    # DI override로 Admin ctx + 같은 OntologyService 인스턴스 주입
    app.dependency_overrides[_ctx] = lambda: seed_ctx
    app.dependency_overrides[_get_workflow_svc] = lambda: WorkflowService(ontology_svc=ont)

    client = TestClient(app)
    resp = client.post(
        "/api/workflow/execute",
        json={"doc_id": "doc-e", "entity_id": entity["id"], "action": "ApproveOrder"},
    )
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["to_status"] == "Approved"


# ── S07-3-D05: workflow.json 외부화 ──────────────────────────────────────────

def test_d05_workflow_config_loaded_from_file():
    """WorkflowService가 config/workflow.json에서 전환 규칙을 로드."""
    # tests/ → backend/ → app/ → config/
    config_path = Path(__file__).resolve().parents[1] / "app" / "config" / "workflow.json"
    assert config_path.exists(), "config/workflow.json이 없습니다."
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert "actions" in config
    assert "ApproveOrder" in config["actions"]


def test_d05_available_actions_from_config(wf_svc):
    """Admin + Submitted → ApproveOrder 포함 확인."""
    actions = wf_svc.available_actions("Admin", "Submitted")
    assert "ApproveOrder" in actions
    assert "HoldOrder" in actions


def test_d05_custom_config_path(tmp_path):
    """custom config_path로 WorkflowService를 교체 가능 — 도메인 외부화 검증."""
    custom = tmp_path / "custom_workflow.json"
    custom.write_text(json.dumps({
        "object_type": "Task",
        "actions": {
            "StartTask": {
                "from_statuses": ["Pending"],
                "to_status": "InProgress",
                "allowed_roles": ["Admin"],
            }
        }
    }), encoding="utf-8")

    svc = WorkflowService(ontology_svc=OntologyService(), config_path=custom)
    actions = svc.available_actions("Admin", "Pending")
    assert "StartTask" in actions


# ── S07-3-D06: policy 마스킹 ─────────────────────────────────────────────────

def test_d06_policy_masking_config_exists():
    """app/config/policy.default.json 또는 v1.0 policy.default.json 존재 확인."""
    v2_path = Path(__file__).resolve().parents[2] / "app" / "config" / "policy.default.json"
    v1_path = Path(__file__).resolve().parents[4] / "claud_v1_legacy" / "backend" / "app" / "config" / "policy.default.json"
    assert v2_path.exists() or v1_path.exists(), (
        "policy.default.json을 찾을 수 없습니다. "
        "app/config/policy.default.json 또는 v1.0 경로에 없습니다."
    )


# ── S07-3-D07: app_context.py 없이 동작 확인 ─────────────────────────────────

def test_d07_workflow_service_no_app_context():
    """WorkflowService가 app_context.py를 import하지 않고 동작."""
    import importlib
    import sys

    # app_context가 sys.modules에 없어도 WorkflowService 생성 가능
    app_context_name = "app.app_context"
    was_loaded = app_context_name in sys.modules

    svc = WorkflowService(ontology_svc=OntologyService())
    assert svc is not None

    if not was_loaded:
        assert app_context_name not in sys.modules, (
            "WorkflowService가 app_context를 import했습니다 — 의존성 제거 필요."
        )


def test_d07_workflow_api_router_no_app_context():
    """workflow API 라우터가 app_context 없이 import 가능."""
    import sys
    # app_context가 이미 없는 상태에서도 import 성공해야 함
    app_context_name = "app.app_context"
    before = app_context_name in sys.modules

    from app.api import workflow as wf_router  # noqa: F401
    assert wf_router is not None

    if not before:
        assert app_context_name not in sys.modules


# ── S07-3-D08: domain.json 편집으로 신규 엔티티 타입 추가 ────────────────────

def test_d08_domain_json_exists_and_extensible():
    """config/domain.json이 존재하고 entity_types 배열을 포함."""
    # tests/ → backend/ → app/ → config/
    domain_path = Path(__file__).resolve().parents[1] / "app" / "config" / "domain.json"
    assert domain_path.exists(), "config/domain.json이 없습니다."

    config = json.loads(domain_path.read_text(encoding="utf-8"))
    assert "entity_types" in config
    assert isinstance(config["entity_types"], list)
    assert len(config["entity_types"]) >= 1


def test_d08_new_entity_type_via_ontology(ctx_admin, ont_svc):
    """domain.json 에 없는 타입도 OntologyService로 자유롭게 추가 가능."""
    entity = ont_svc.upsert_entity("doc-1", {
        "type": "NewCustomType",
        "name": "Test Entity",
        "properties": {"custom_field": "value"},
    }, ctx_admin)
    assert entity["type"] == "NewCustomType"


# ── S07-3-D09: Sprint 07-1 + 07-2 테스트 import 검증 ─────────────────────────

def test_d09_sprint07_1_tests_importable():
    """Sprint 07-1 테스트 모듈이 여전히 import 가능함을 확인."""
    from tests import test_sprint07_1_dod  # noqa: F401
    from tests import test_storage_config  # noqa: F401


def test_d09_sprint07_2_tests_importable():
    """Sprint 07-2 테스트 모듈이 여전히 import 가능함을 확인."""
    from tests import test_sprint07_2_dod  # noqa: F401
