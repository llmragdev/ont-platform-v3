from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class DataFlowNode(BaseModel):
    id: str
    label: str
    type: str  # "source" | "ingest" | "transform" | "retrieve" | "execute" | "writeback" | "persist" | "audit"
    description: str
    status: Optional[str] = "ready"  # "ready" | "running" | "success" | "failed" | "skipped"
    details: Optional[Dict[str, Any]] = None

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
