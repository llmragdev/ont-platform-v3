from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel


class ColumnSpec(BaseModel):
    name: str
    type: str
    description: str


class CatalogTableResponse(BaseModel):
    table_name: str
    layer: str  # BRONZE, SILVER, GOLD
    description: str
    columns: List[ColumnSpec]


class QueryExecuteRequest(BaseModel):
    query: str


class QueryExecuteResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    execution_time_ms: float
    error: Optional[str] = None
