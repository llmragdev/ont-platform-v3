from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PropertySchema(BaseModel):
    name: str
    type: str
    required: bool = False
    sensitive: bool = False


class ObjectTypeSchema(BaseModel):
    id: str
    display_name: str
    icon: str
    properties: List[PropertySchema]


class RelationshipTypeSchema(BaseModel):
    id: str
    display_name: str
    source_type: str
    target_type: str


class OntologySchema(BaseModel):
    object_types: List[ObjectTypeSchema]
    relationship_types: List[RelationshipTypeSchema]


class ObjectInstance(BaseModel):
    id: str
    type: str
    values: Dict[str, Any]


class RelationshipInstance(BaseModel):
    type: str
    source_id: str
    target_id: str
    values: Dict[str, Any] = Field(default_factory=dict)


class OntologyEngine:
    def __init__(self, schema_path: str | Path):
        self.schema_path = Path(schema_path)
        self.schema: OntologySchema = self._load_schema()
        self.objects: Dict[str, ObjectInstance] = {}
        self.relationships: List[RelationshipInstance] = []

    def _load_schema(self) -> OntologySchema:
        with open(self.schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return OntologySchema(**data)

    def register_object(self, obj: ObjectInstance):
        # 유효성 검사 (스키마에 정의된 타입인지 확인)
        type_ids = [ot.id for ot in self.schema.object_types]
        if obj.type not in type_ids:
            raise ValueError(f"Unknown object type: {obj.type}")
        self.objects[obj.id] = obj

    def link(self, rel_type_id: str, source_id: str, target_id: str, values: Dict[str, Any] = None):
        # 유효성 검사
        rel_type = next((rt for rt in self.schema.relationship_types if rt.id == rel_type_id), None)
        if not rel_type:
            raise ValueError(f"Unknown relationship type: {rel_type_id}")
        
        source = self.objects.get(source_id)
        target = self.objects.get(target_id)
        
        if not source or not target:
            raise ValueError("Source or Target object not found")
            
        if source.type != rel_type.source_type or target.type != rel_type.target_type:
            raise ValueError(f"Relationship type mismatch: {source.type} -> {target.type}")
            
        rel = RelationshipInstance(
            type=rel_type_id,
            source_id=source_id,
            target_id=target_id,
            values=values or {}
        )
        self.relationships.append(rel)

    def find_related(self, object_id: str, rel_type_id: Optional[str] = None) -> List[ObjectInstance]:
        """특정 객체와 연결된 모든 객체를 찾음 (그래프 탐색의 기초)"""
        results = []
        for rel in self.relationships:
            if rel.source_id == object_id:
                if rel_type_id is None or rel.type == rel_type_id:
                    results.append(self.objects[rel.target_id])
            elif rel.target_id == object_id:
                 if rel_type_id is None or rel.type == rel_type_id:
                    results.append(self.objects[rel.source_id])
        return results

    def get_object_with_context(self, object_id: str) -> Dict[str, Any]:
        """객체와 그 주변부(1-hop) 관계 데이터를 패키징함"""
        obj = self.objects.get(object_id)
        if not obj:
            return {}
            
        related = self.find_related(object_id)
        return {
            "object": obj.dict(),
            "related_objects": [r.dict() for r in related],
            "schema_info": next((ot for ot in self.schema.object_types if ot.id == obj.type), None)
        }
