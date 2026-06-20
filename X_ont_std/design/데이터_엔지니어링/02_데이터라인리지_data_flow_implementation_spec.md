# 🛠️ 데이터 워크플로우 / 라인리지 상세 구현 명세서

본 문서는 `01_데이터워크플로우_라인리지_화면_설계서.md`에 기재된 데이터 흐름(Data Flow) 및 계보(Lineage) 화면을 백엔드에 통합하기 위한 **JSON 정의 스키마, Pydantic 모델, 그리고 FastAPI 서비스 로직**을 기술합니다.

---

## 1. 🗂️ 정적 데이터 흐름 설정 파일 설계 (JSON)

시나리오별 데이터 흐름의 정적 노드와 엣지를 정의하는 설정 스펙입니다.

### 1.1 고객사 문의 자동댓글 흐름
`backend/app/config/data_flows/scenario1_customer_question.json`

```json
{
  "flow_id": "scenario1-customer-question",
  "scenario_id": "scenario1",
  "name": "고객사 문의 자동댓글 데이터 흐름",
  "description": "고객사 게시판 문의 접수부터 AI 답변 생성 및 MCP 댓글 등록, 온톨로지 저장까지의 흐름",
  "nodes": [
    { "id": "n1-source", "label": "고객사 게시판", "type": "source", "description": "고객이 문의를 등록하는 외부 게시판 시스템 (포트 8090)" },
    { "id": "n2-ingest", "label": "이벤트 수신", "type": "ingest", "description": "Webhook 또는 Batch를 통해 문의 이벤트를 온톨로지 플랫폼으로 수집" },
    { "id": "n3-transform", "label": "문의 분류", "type": "transform", "description": "LLM을 활용해 문의 유형(비밀번호, 주문, 기타)을 자동 분류" },
    { "id": "n4-retrieve", "label": "RAG 근거 조회", "type": "retrieve", "description": "회사 내부 매뉴얼 및 온톨로지 지식 DB에서 연관 답변 검색" },
    { "id": "n5-execute", "label": "답변 생성", "type": "execute", "description": "수집된 근거를 결합하여 고객 맞춤형 답변 초안 작성" },
    { "id": "n6-writeback", "label": "customer_mcp 댓글 등록", "type": "writeback", "description": "고객사 MCP 중계 계층(포트 8080)을 통해 외부 게시판에 댓글 작성" },
    { "id": "n7-persist", "label": "온톨로지 관계 저장", "type": "persist", "description": "ServiceRequest - has_reply - AutoReply 관계를 온톨로지에 영구 적재" },
    { "id": "n8-audit", "label": "감사 로그 기록", "type": "audit", "description": "누가 어떤 실행을 통해 무엇을 변경했는지 시스템 감사 로그에 기록" }
  ],
  "edges": [
    { "source": "n1-source", "target": "n2-ingest" },
    { "source": "n2-ingest", "target": "n3-transform" },
    { "source": "n3-transform", "target": "n4-retrieve" },
    { "source": "n4-retrieve", "target": "n5-execute" },
    { "source": "n5-execute", "target": "n6-writeback" },
    { "source": "n6-writeback", "target": "n7-persist" },
    { "source": "n7-persist", "target": "n8-audit" }
  ]
}
```

---

## 2. 🔌 백엔드 Pydantic 및 API 라우터 설계 (FastAPI)

설정 파일을 읽고 프론트엔드에 ReactFlow에 적합한 데이터 구조로 던져주기 위한 설계입니다.

```python
# backend/app/models/data_flow.py
from pydantic import BaseModel
from typing import List, Dict, Optional

class DataFlowNode(BaseModel):
    id: str
    label: str
    type: str  # "source" | "ingest" | "transform" | "retrieve" | "execute" | "writeback" | "persist" | "audit"
    description: str
    status: Optional[str] = "ready"  # "ready" | "running" | "success" | "failed" | "skipped"

class DataFlowEdge(BaseModel):
    source: str
    target: str

class DataFlowDefinition(BaseModel):
    flow_id: str
    scenario_id: str
    name: str
    description: str
    nodes: List[DataFlowNode]
    edges: List[DataFlowEdge]

# backend/app/api/data_flows.py
from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter(prefix="/data-flows", tags=["Data Flow Lineage"])
CONFIG_DIR = "backend/app/config/data_flows"

@router.get("", response_model=List[Dict[str, str]])
def list_data_flows():
    """등록된 모든 데이터 흐름 리스트 반환"""
    flows = []
    if not os.path.exists(CONFIG_DIR):
        return flows
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(CONFIG_DIR, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
                flows.append({
                    "flow_id": data["flow_id"],
                    "name": data["name"],
                    "scenario_id": data["scenario_id"]
                })
    return flows

@router.get("/{flow_id}", response_model=DataFlowDefinition)
def get_data_flow_definition(flow_id: str):
    """특정 데이터 흐름의 노드/엣지 정의 조회"""
    filepath = os.path.join(CONFIG_DIR, f"{flow_id}.json")
    # 예외적으로 대시(-)와 언더바(_) 혼용 처리
    if not os.path.exists(filepath):
        filepath = os.path.join(CONFIG_DIR, f"{flow_id.replace('-', '_')}.json")
        
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="데이터 흐름 설정을 찾을 수 없습니다.")
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data
```

---

## 3. ⚙️ 동적 실행 상태 매핑 로직 (Service)

워크플로우 실행 이력(`WorkflowExecution`)과 감사 로그를 대조하여, 데이터 흐름 각 단계의 성공/실패 상태(`status`)와 세부 입출력 데이터를 바인딩해 주는 서비스 함수 설계입니다.

```python
# backend/app/services/data_flow_service.py
import json
import os
from typing import Dict, Any
from app.models.data_flow import DataFlowDefinition

class DataFlowService:
    @staticmethod
    def get_flow_with_run_status(flow_id: str, workflow_run_id: str) -> Dict[str, Any]:
        """
        정적 데이터 흐름 정의에 동적 실행 상태(runs)를 주입합니다.
        """
        # 1. 정적 설정 로드
        filepath = f"backend/app/config/data_flows/{flow_id}.json"
        if not os.path.exists(filepath):
            raise FileNotFoundError("Flow configuration not found.")
            
        with open(filepath, "r", encoding="utf-8") as f:
            flow_data = json.load(f)

        # 2. 실행 이력 데이터 로드 (실제 DB 또는 storage/ 파일 조회)
        run_data = DataFlowService._fetch_workflow_run_data(workflow_run_id)
        if not run_data:
            return flow_data  # 실행 이력이 없으면 기본 정적 흐름만 반환

        # 3. 노드별 실행 상태 및 입출력 매핑
        node_status_map = DataFlowService._map_steps_to_run_nodes(flow_data["nodes"], run_data)
        
        # 4. 정적 노드 데이터 갱신
        for node in flow_data["nodes"]:
            node_id = node["id"]
            if node_id in node_status_map:
                node["status"] = node_status_map[node_id]["status"]
                node["details"] = node_status_map[node_id].get("details")

        return flow_data

    @staticmethod
    def _fetch_workflow_run_data(run_id: str) -> Dict[str, Any]:
        # 프로젝트의 기존 storage 조회 로직 활용
        # 예: storage/demo-co/proj-01/workflow_runs/{run_id}.json
        return {}  # Mock 리턴 (구현 시 파일 및 DB 파싱 모듈 추가)

    @staticmethod
    def _map_steps_to_run_nodes(nodes: list, run_data: Dict[str, Any]) -> Dict[str, Dict]:
        # 워크플로우 노드별 결과 상태를 바탕으로 데이터 흐름 노드 상태 매핑
        # 예: "n3-transform" (Transform 노드) -> workflow_run의 "Intent Classify" 노드 결과 파싱
        status_map = {}
        # ... 파싱 로직 구현 ...
        return status_map
```
