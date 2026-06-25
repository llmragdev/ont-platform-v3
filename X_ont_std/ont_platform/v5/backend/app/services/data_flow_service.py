import json
import os
from pathlib import Path
from typing import Dict, Any, List
from app.models.tenant_context import TenantContext
from storage_config import get_ontology_path, get_workflow_runs_path
from app.models.data_flow import DataFlowDefinition, DataFlowNode, DataFlowEdge

class DataFlowService:
    @staticmethod
    def get_flow_with_run_status(flow_id: str, workflow_run_id: str, ctx: TenantContext) -> Dict[str, Any]:
        """
        정적 데이터 흐름 설정에 특정 워크플로우 실행(run)의 상태 및 결과를 매핑하여 반환합니다.
        """
        # 1. 정적 데이터 흐름 설정 로드
        config_dir = Path(__file__).resolve().parent.parent / "config" / "data_flows"
        filepath = config_dir / f"{flow_id}.json"
        if not filepath.exists():
            filepath = config_dir / f"{flow_id.replace('-', '_')}.json"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data flow configuration not found: {flow_id}")
            
        with open(filepath, "r", encoding="utf-8") as f:
            flow_data = json.load(f)

        # 2. 워크플로우 실행 데이터 파일 읽기
        runs_dir = get_workflow_runs_path(ctx.company_id, ctx.project_id)
        run_file = runs_dir / f"{workflow_run_id}.json"
        
        if not run_file.exists():
            # 실행 데이터 파일이 없으면 정적 흐름만 반환
            return flow_data

        with open(run_file, "r", encoding="utf-8") as f:
            run_data = json.load(f)

        # 3. 워크플로우 실행 결과 매핑 (노드 맵)
        step_runs = run_data.get("steps", []) or run_data.get("step_runs", [])
        
        # 1단계: 노드별 실행 상태 파악
        run_steps_by_node_id = {}
        for step in step_runs:
            node_id = step.get("node_id") or step.get("id")
            if node_id:
                run_steps_by_node_id[node_id] = step

        # 4. 전체 실행 상태 판별
        overall_status = run_data.get("status", "pending")
        if isinstance(overall_status, str):
            overall_status = overall_status.lower()
        else:
            overall_status = getattr(overall_status, "value", "pending").lower()
        
        is_run_completed = overall_status in ("completed", "succeeded", "success")

        # 5. 고객사 댓글 자동 등록(scenario1) 추가 정보 추출용 데이터 구성
        draft_data = {}
        if "post-comment" in run_steps_by_node_id:
            pc_step = run_steps_by_node_id["post-comment"]
            pc_output = pc_step.get("output", {}) or {}
            items = pc_output.get("items", [])
            if items and isinstance(items, list) and isinstance(items[0], dict):
                draft_data = items[0].get("draft") or {}

        # 6. 정적 노드에 동적 상태 및 입출력 데이터 바인딩
        for node in flow_data.get("nodes", []):
            node_type = node.get("type")
            node_id = node.get("id")
            
            # 시나리오 노드와 실제 워크플로우 노드 매핑 정의
            mapped_step = None
            
            # 시나리오1: 고객사 문의 자동댓글 매핑 규칙
            if flow_id == "scenario1-customer-question":
                mapping_rules = {
                    "n2-ingest": ["request-input", "question-normalize", "input"],
                    "n3-transform": ["intent-classify", "request-classify", "classify"],
                    "n4-retrieve": ["knowledge-lookup", "evidence-gate", "rag-ontology-lookup", "rag-lookup"],
                    "n5-execute": ["draft-response"],
                    "n6-writeback": ["post-comment", "customer-comment-create", "mcp-comment"],
                    "n7-persist": ["audit-write", "ontology-write"],
                    "n8-audit": ["audit-write"]
                }
                candidates = mapping_rules.get(node_id, [])
                for c in candidates:
                    if c in run_steps_by_node_id:
                        mapped_step = run_steps_by_node_id[c]
                        break
            
            # 시나리오2: 공장 자동화 정비지시 매핑 규칙
            elif flow_id == "scenario2-factory-fault":
                mapping_rules = {
                    "n2-ingest": ["request-input", "input"],
                    "n3-transform": ["category-classify", "request-classify", "classify"],
                    "n4-map": ["asset-map"],
                    "n5-check": ["recurrence-check", "fault-recurrence-check"],
                    "n6-execute": ["draft-response", "maintenance-create"],
                    "n7-writeback": ["notify-teams", "maintenance-task", "quality-link", "factory-maintenance-create", "factory-comment", "mcp-writeback"],
                    "n8-persist": ["ontology-write"],
                    "n9-audit": ["ontology-write", "audit-write"]
                }
                candidates = mapping_rules.get(node_id, [])
                for c in candidates:
                    if c in run_steps_by_node_id:
                        mapped_step = run_steps_by_node_id[c]
                        break

            # 매핑된 워크플로우 단계가 존재하는 경우 상태 및 입출력 주입
            if mapped_step:
                status = mapped_step.get("status", "ready")
                if isinstance(status, str):
                    status = status.lower()
                else:
                    status = getattr(status, "value", "ready").lower()

                # StepStatus 표준화 (completed/succeeded/success -> success, failed/error -> failed)
                if status in ("completed", "succeeded", "success"):
                    node["status"] = "success"
                elif status in ("failed", "error"):
                    node["status"] = "failed"
                elif status == "running":
                    node["status"] = "running"
                elif status == "skipped":
                    node["status"] = "skipped"
                else:
                    node["status"] = status
                
                # 입출력 데이터 표준 키 매핑 (input/inputs/input_summary 등 지원)
                node_input = mapped_step.get("input") or mapped_step.get("inputs") or mapped_step.get("input_summary") or {}
                node_output = mapped_step.get("output") or mapped_step.get("outputs") or mapped_step.get("output_summary") or {}
                
                # 특수한 노드 유형별 페이로드 커스터마이징
                if flow_id == "scenario1-customer-question" and node_id == "n7-persist":
                    # n7-persist는 audit-write의 ontology_writeback 정보를 output으로 활용
                    node_output = node_output.get("ontology_writeback") or node_output

                node["details"] = {
                    "inputs": node_input,
                    "outputs": node_output,
                    "error": mapped_step.get("error"),
                    "started_at": mapped_step.get("started_at"),
                    "completed_at": mapped_step.get("completed_at") or mapped_step.get("finished_at"),
                    "execution_time_ms": mapped_step.get("execution_time_ms")
                }
            else:
                # 매핑된 단계가 없지만 전체 워크플로우 상태가 완료된 경우
                # 데이터 흐름의 시작점(source) 등은 간접적으로 'success' 처리
                if node_type == "source":
                    node["status"] = "success" if is_run_completed else "ready"
                elif is_run_completed:
                    node["status"] = "success"
                    # scenario1의 가상 노드들에 대한 모의 데이터 주입
                    if flow_id == "scenario1-customer-question":
                        if node_id == "n3-transform":
                            node["details"] = {
                                "inputs": {"question_id": draft_data.get("question_id") or "q-d94ce8ed"},
                                "outputs": {"intent": draft_data.get("intent") or "filter", "confidence": draft_data.get("confidence") or 0.5}
                            }
                        elif node_id == "n4-retrieve":
                            node["details"] = {
                                "inputs": {"intent": draft_data.get("intent") or "filter"},
                                "outputs": {"retrieved_manuals": ["account_security_manual.md"], "kb_source": "ontology"}
                            }
                else:
                    node["status"] = "ready"

        return flow_data
