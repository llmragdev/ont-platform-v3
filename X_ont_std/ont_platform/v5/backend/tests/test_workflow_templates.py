from pathlib import Path

from app.models.tenant_context import TenantContext
from app.services.workflow_template_service import WorkflowTemplateService


def _ctx(company_id: str, project_id: str) -> TenantContext:
    return TenantContext(
        user_id="tester",
        company_id=company_id,
        project_id=project_id,
        role="Admin",
        permissions={},
    )


def test_clone_system_template_is_project_scoped(tmp_path, monkeypatch):
    import storage_config

    monkeypatch.setattr(storage_config, "STORAGE_ROOT", tmp_path / "storage")

    svc = WorkflowTemplateService()
    graph_a = svc.clone_template(_ctx("acme", "support"), "service-request-auto-reply", name="Auto Reply A")
    graph_b = svc.clone_template(_ctx("globex", "support"), "service-request-auto-reply", name="Auto Reply B")

    assert graph_a["id"] != graph_b["id"]
    assert graph_a["tenant_scope"] == {"company_id": "acme", "project_id": "support"}
    assert graph_b["tenant_scope"] == {"company_id": "globex", "project_id": "support"}
    assert graph_a["runtime"]["executor"] == "scenario1.customer_question_auto_reply"

    assert (tmp_path / "storage" / "acme" / "support" / "workflow_graphs.json").exists()
    assert (tmp_path / "storage" / "globex" / "support" / "workflow_graphs.json").exists()


def test_factory_repeated_fault_template_is_available():
    svc = WorkflowTemplateService()

    template = svc.get_template("factory-repeated-fault-response")

    assert template["runtime"]["executor"] == "factory.repeated_fault_response"
    assert template["scenario_id"] == "factory-repeated-fault"
    assert any(node["id"] == "recurrence-check" for node in template["nodes"])
    assert any(node["id"] == "maintenance-task" for node in template["nodes"])


def test_project_graph_clone_preserves_runtime_metadata(tmp_path, monkeypatch):
    import storage_config

    monkeypatch.setattr(storage_config, "STORAGE_ROOT", tmp_path / "storage")

    ctx = _ctx("default", "proj-default")
    template_svc = WorkflowTemplateService()
    graph = template_svc.clone_template(ctx, "service-request-auto-reply", name="Auto Reply")
    cloned = template_svc.graph_svc.clone_graph(ctx, graph["id"], name="Auto Reply Copy")

    assert cloned["id"] != graph["id"]
    assert cloned["name"] == "Auto Reply Copy"
    assert cloned["runtime"] == graph["runtime"]
    assert cloned["source"]["cloned_from"] == graph["id"]
