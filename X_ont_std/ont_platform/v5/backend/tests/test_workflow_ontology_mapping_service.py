import json

from app.models.tenant_context import TenantContext
from app.services.workflow_ontology_mapping_service import WorkflowOntologyMappingService


def _ctx(company_id: str = "demo-co", project_id: str = "proj-01") -> TenantContext:
    return TenantContext(
        user_id="tester",
        company_id=company_id,
        project_id=project_id,
        role="Admin",
        permissions={},
    )


def test_lists_scenario1_workflow_ontology_mapping():
    svc = WorkflowOntologyMappingService()

    mappings = svc.list_mappings()

    mapping = next(item for item in mappings if item["mapping_id"] == "scenario1.customer_question_auto_reply.v1")
    assert mapping["workflow_template_id"] == "service-request-auto-reply"
    assert mapping["ontology_document"]["doc_id"] == "service-requests"
    assert any(item["name"] == "ServiceRequest" for item in mapping["entity_types"])
    assert any(item["name"] == "handled_by" for item in mapping["relation_types"])


def test_lists_factory_repeated_fault_mapping():
    svc = WorkflowOntologyMappingService()

    mapping = svc.get_mapping("factory.repeated_fault_response.v1")

    assert mapping["workflow_template_id"] == "factory-repeated-fault-response"
    assert mapping["ontology_document"]["doc_id"] == "factory-repeated-faults"
    assert any(item["name"] == "Factory" for item in mapping["entity_types"])
    assert any(item["name"] == "FaultEvent" for item in mapping["entity_types"])
    assert any(item["name"] == "creates" for item in mapping["relation_types"])


def test_install_schema_merges_mapping_types_into_project_schema(tmp_path, monkeypatch):
    import storage_config

    monkeypatch.setattr(storage_config, "STORAGE_ROOT", tmp_path / "storage")
    ctx = _ctx()
    svc = WorkflowOntologyMappingService()

    result = svc.install_schema(ctx, "scenario1.customer_question_auto_reply.v1")

    assert result["status"] == "installed"
    schema_path = tmp_path / "storage" / "demo-co" / "proj-01" / "ontology" / "domain_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert any(item["name"] == "ServiceRequest" for item in schema["entity_types"])
    assert any(item["name"] == "posted_as" for item in schema["relation_types"])
    assert schema["installed_workflow_mappings"][0]["mapping_id"] == "scenario1.customer_question_auto_reply.v1"


def test_install_factory_schema_merges_manufacturing_types(tmp_path, monkeypatch):
    import storage_config

    monkeypatch.setattr(storage_config, "STORAGE_ROOT", tmp_path / "storage")
    ctx = _ctx()
    svc = WorkflowOntologyMappingService()

    result = svc.install_schema(ctx, "factory.repeated_fault_response.v1")

    assert result["status"] == "installed"
    schema_path = tmp_path / "storage" / "demo-co" / "proj-01" / "ontology" / "domain_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert any(item["name"] == "Equipment" for item in schema["entity_types"])
    assert any(item["name"] == "MaintenanceTask" for item in schema["entity_types"])
    assert any(item["name"] == "possibly_caused_by" for item in schema["relation_types"])
