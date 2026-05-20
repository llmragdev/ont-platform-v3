from __future__ import annotations

from pydantic import BaseModel, Field


class PropertyDef(BaseModel):
    name: str
    type: str
    required: bool = False
    searchable: bool = False
    sensitive: bool = False
    values: list[str] | None = None


class ObjectTypeDef(BaseModel):
    name: str
    display_name: str | None = None
    id_prefix: str | None = None
    properties: list[PropertyDef] = Field(default_factory=list)


class RelationshipTypeDef(BaseModel):
    name: str
    source_type: str
    target_type: str
    display_name: str | None = None
    reverse_display_name: str | None = None
    cardinality: str = "many_to_many"
    properties: list[PropertyDef] = Field(default_factory=list)


class ActionTypeDef(BaseModel):
    name: str
    target_type: str
    display_name: str | None = None
    description: str | None = None
    exposed_as_graph_node: bool = False


class OntologySchema(BaseModel):
    object_types: list[ObjectTypeDef]
    relationship_types: list[RelationshipTypeDef]
    action_types: list[ActionTypeDef] = Field(default_factory=list)


class RelationshipCreate(BaseModel):
    type: str
    source_id: str
    target_id: str
    properties: dict = Field(default_factory=dict)


class AskRequest(BaseModel):
    question: str
    object_id: str | None = None


class HybridAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    object_id: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


class OntologyObjectCreate(BaseModel):
    type: str
    values: dict = Field(default_factory=dict)
    company_id: str | None = None
    project_id: str | None = None


class OntologyObjectUpdate(BaseModel):
    values: dict | None = None
    status: str | None = None


class OntologyRelationshipCreate(BaseModel):
    type: str
    source_id: str
    target_id: str
    properties: dict = Field(default_factory=dict)
    company_id: str | None = None
    project_id: str | None = None
