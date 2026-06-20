import json
from pathlib import Path
from app.models.tenant_context import TenantContext
from app.services.data_flow_service import DataFlowService

def _ctx(company_id: str, project_id: str) -> TenantContext:
    return TenantContext(
        user_id="tester",
        company_id=company_id,
        project_id=project_id,
        role="Admin",
        permissions={},
    )

def test_scenario1_customer_question_run_mapping(tmp_path, monkeypatch):
    import storage_config
    monkeypatch.setattr(storage_config, "STORAGE_ROOT", tmp_path / "storage")

    # 1. Create fake workflow run JSON with 'succeeded' status
    company_id = "test-co"
    project_id = "proj-01"
    run_id = "run-12345"
    
    run_dir = tmp_path / "storage" / company_id / project_id / "workflow_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    run_data = {
        "run_id": run_id,
        "graph_id": "wfg-dummy",
        "status": "succeeded",
        "triggered_by": "tester",
        "started_at": "2026-06-14T09:10:00Z",
        "finished_at": "2026-06-14T09:10:10Z",
        "steps": [
            {
                "step_id": "step-1",
                "node_id": "request-input",
                "node_type": "request_input",
                "status": "succeeded",
                "started_at": "2026-06-14T09:10:00Z",
                "finished_at": "2026-06-14T09:10:01Z",
                "input": {"mode": "post"},
                "output": {"status": "open", "limit": 1},
                "error": None
            },
            {
                "step_id": "step-2",
                "node_id": "draft-response",
                "node_type": "draft_response",
                "status": "succeeded",
                "started_at": "2026-06-14T09:10:01Z",
                "finished_at": "2026-06-14T09:10:02Z",
                "input": {},
                "output": {"started": 1, "skipped": 0},
                "error": None
            },
            {
                "step_id": "step-3",
                "node_id": "post-comment",
                "node_type": "customer_mcp_comment_create",
                "status": "succeeded",
                "started_at": "2026-06-14T09:10:02Z",
                "finished_at": "2026-06-14T09:10:03Z",
                "input": {},
                "output": {
                    "status": "success",
                    "items": [
                        {
                            "draft": {
                                "question_id": "q-1",
                                "reply_message": "Hello from RAG",
                                "intent": "billing",
                                "confidence": 0.95
                            }
                        }
                    ]
                },
                "error": None
            },
            {
                "step_id": "step-4",
                "node_id": "audit-write",
                "node_type": "notify_user",
                "status": "succeeded",
                "started_at": "2026-06-14T09:10:03Z",
                "finished_at": "2026-06-14T09:10:04Z",
                "input": {},
                "output": {
                    "ontology_writeback": {
                        "status": "success",
                        "entities_upserted": 2
                    }
                },
                "error": None
            }
        ]
    }
    
    with open(run_dir / f"{run_id}.json", "w", encoding="utf-8") as f:
        json.dump(run_data, f)

    # 2. Execute DataFlowService
    ctx = _ctx(company_id, project_id)
    flow_info = DataFlowService.get_flow_with_run_status("scenario1-customer-question", run_id, ctx)

    # 3. Assertions
    assert flow_info["flow_id"] == "scenario1-customer-question"
    
    nodes_by_id = {node["id"]: node for node in flow_info["nodes"]}
    
    # Check that source is marked as success because run was succeeded
    assert nodes_by_id["n1-source"]["status"] == "success"
    
    # Check that mapped step statuses are standardized to 'success' (not 'succeeded')
    assert nodes_by_id["n2-ingest"]["status"] == "success"
    assert nodes_by_id["n5-execute"]["status"] == "success"
    assert nodes_by_id["n6-writeback"]["status"] == "success"
    assert nodes_by_id["n8-audit"]["status"] == "success"
    
    # Check input/output details mapping
    assert nodes_by_id["n2-ingest"]["details"]["inputs"] == {"mode": "post"}
    assert nodes_by_id["n2-ingest"]["details"]["outputs"] == {"status": "open", "limit": 1}

    # Check virtual node details extraction
    assert nodes_by_id["n3-transform"]["status"] == "success"
    assert nodes_by_id["n3-transform"]["details"]["outputs"]["intent"] == "billing"
    assert nodes_by_id["n3-transform"]["details"]["outputs"]["confidence"] == 0.95

    assert nodes_by_id["n4-retrieve"]["status"] == "success"
    assert nodes_by_id["n4-retrieve"]["details"]["inputs"]["intent"] == "billing"

    # Check custom persistent payload on n7-persist (extracts from audit-write ontology_writeback)
    assert nodes_by_id["n7-persist"]["status"] == "success"
    assert nodes_by_id["n7-persist"]["details"]["outputs"] == {"status": "success", "entities_upserted": 2}
