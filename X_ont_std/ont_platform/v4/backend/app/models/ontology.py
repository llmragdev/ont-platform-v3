"""v3.0 Ontology models with Provenance support."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel


class OntologyProvenance(BaseModel):
    source_doc_id: str | None = None
    source_page: int | None = None
    source_chunk_id: str | None = None
    source_text: str | None = None
    confidence: float = 1.0
    extracted_by: str | None = None  # "llm" | "manual" | "import"


class OntologyEntityV3(BaseModel):
    id: str
    type: str
    name: str
    properties: dict = {}
    provenance: OntologyProvenance | None = None
    status: Literal["active", "review", "deprecated"] = "active"
    version: int = 1
    created_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "OntologyEntityV3":
        prov_raw = data.get("provenance")
        prov = OntologyProvenance(**prov_raw) if isinstance(prov_raw, dict) else None
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            name=data.get("name", ""),
            properties=data.get("properties", {}),
            provenance=prov,
            status=data.get("status", "active"),
            version=data.get("version", 1),
            created_by=data.get("created_by"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
