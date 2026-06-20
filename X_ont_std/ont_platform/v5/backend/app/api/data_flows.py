from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import json
import os
from pathlib import Path
from app.models.tenant_context import TenantContext
from app.dependencies import get_tenant_context
from app.models.data_flow import DataFlowDefinition
from app.services.data_flow_service import DataFlowService

router = APIRouter(prefix="/api/data-flows", tags=["Data Flow Lineage"])
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "data_flows"

@router.get("", response_model=List[Dict[str, str]])
def list_data_flows(ctx: TenantContext = Depends(get_tenant_context)):
    """등록된 모든 데이터 흐름 리스트 반환"""
    flows = []
    if not CONFIG_DIR.exists():
        return flows
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(".json"):
            with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                flows.append({
                    "flow_id": data["flow_id"],
                    "name": data["name"],
                    "scenario_id": data["scenario_id"],
                    "description": data["description"]
                })
    return flows

@router.get("/{flow_id}", response_model=DataFlowDefinition)
def get_data_flow_definition(flow_id: str, ctx: TenantContext = Depends(get_tenant_context)):
    """특정 데이터 흐름의 노드/엣지 정의 조회"""
    filepath = CONFIG_DIR / f"{flow_id}.json"
    if not filepath.exists():
        filepath = CONFIG_DIR / f"{flow_id.replace('-', '_')}.json"
        
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"데이터 흐름 설정을 찾을 수 없습니다: {flow_id}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data

@router.get("/{flow_id}/runs/{workflow_run_id}", response_model=DataFlowDefinition)
def get_data_flow_run(flow_id: str, workflow_run_id: str, ctx: TenantContext = Depends(get_tenant_context)):
    """실행 이력 데이터와 결합된 동적 데이터 흐름 상태 조회"""
    try:
        flow_run = DataFlowService.get_flow_with_run_status(flow_id, workflow_run_id, ctx)
        return flow_run
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="데이터 흐름 설정을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
