from app.models.tenant_context import TenantContext
from app.services.factory_ontology_writer import FACTORY_DOC_ID, FactoryOntologyWriter
from app.services.workflow_ontology_writer import SERVICE_REQUEST_DOC_ID, WorkflowOntologyWriter


def test_workflow_ontology_writer_upserts_service_request_trace(tmp_path, monkeypatch):
    import storage_config

    monkeypatch.setattr(storage_config, "STORAGE_ROOT", tmp_path / "storage")
    ctx = TenantContext(
        user_id="tester",
        company_id="demo-co",
        project_id="proj-01",
        role="Admin",
        permissions={},
    )
    graph = {
        "id": "wfg-test",
        "name": "서비스 요청 자동댓글",
        "runtime": {"executor": "scenario1.customer_question_auto_reply"},
    }
    batch_result = {
        "status": "success",
        "checked": 1,
        "started": 1,
        "skipped": 0,
        "errors": 0,
        "items": [
            {
                "event_id": "batch-q-001-abc",
                "request_id": "req-001",
                "draft": {
                    "question_id": "q-001",
                    "reply_message": "안녕하세요. 문의를 확인했습니다.",
                    "confidence": 0.8,
                    "created_at": "2026-06-13T00:00:00Z",
                },
                "mcp": {
                    "status": "success",
                    "audit_id": "audit-001",
                    "result": {
                        "external_comment_id": "comment-001",
                        "external_thread_id": "q-001",
                        "url": "http://localhost:8090/posts/q-001#comment-comment-001",
                    },
                },
            }
        ],
    }

    summary = WorkflowOntologyWriter().write_scenario1_batch_result(
        ctx=ctx,
        graph=graph,
        run_id="run-001",
        run_started_at="2026-06-13T00:00:00Z",
        run_finished_at="2026-06-13T00:00:10Z",
        mode="post",
        batch_result=batch_result,
    )

    assert summary["doc_id"] == SERVICE_REQUEST_DOC_ID
    doc_path = tmp_path / "storage" / "demo-co" / "proj-01" / "ontology" / "service-requests.json"
    assert doc_path.exists()
    text = doc_path.read_text(encoding="utf-8")
    assert "ServiceRequest" in text
    assert "WorkflowExecution" in text
    assert "AutoReply" in text
    assert "ExternalComment" in text
    assert "scenario1.customer_question_auto_reply.v1" in text
    assert "handled_by" in text
    assert "posted_as" in text


def test_factory_ontology_writer_upserts_repeated_fault_trace(tmp_path, monkeypatch):
    import storage_config

    monkeypatch.setattr(storage_config, "STORAGE_ROOT", tmp_path / "storage")
    ctx = TenantContext(
        user_id="tester",
        company_id="demo-co",
        project_id="proj-01",
        role="Admin",
        permissions={},
    )

    summary = FactoryOntologyWriter().write_event_result(
        ctx=ctx,
        event={
            "factory_event_id": "fe-001",
            "category": "equipment_fault",
            "factory_name": "세종 배터리팩 공장",
            "line_name": "3번 조립 라인",
            "process_step": "배터리 탭 용접",
            "equipment_name": "탭 용접기 3호기",
            "fault_message": "용접 압력 낮음",
            "severity": "high",
            "occurred_at": "2026-06-13T10:00:00Z",
            "title": "탭 용접기 압력 낮음 반복",
            "content": "10시와 11시에 같은 압력 저하가 발생했습니다.",
            "reporter": "현장 관리인",
        },
        request_id="req-001",
        mode="post",
        repeated=True,
        response_result={"external_response_id": "resp-001"},
        maintenance_result={"external_task_id": "mt-001"},
        workflow_run_id="run-001",
    )

    assert summary["doc_id"] == FACTORY_DOC_ID
    doc_path = tmp_path / "storage" / "demo-co" / "proj-01" / "ontology" / "factory-repeated-faults.json"
    assert doc_path.exists()
    text = doc_path.read_text(encoding="utf-8")
    assert "Factory" in text
    assert "ProductionLine" in text
    assert "Equipment" in text
    assert "FaultEvent" in text
    assert "MaintenanceTask" in text
    assert "factory.repeated_fault_response.v1" in text
    assert "reports" in text
    assert "creates" in text
