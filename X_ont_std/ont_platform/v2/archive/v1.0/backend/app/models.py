from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class PropertyDefinition:
    name: str
    value_type: type
    required: bool = False
    # Phase 1 — 스키마 외부화로 추가된 메타데이터 (기본값이 있어 기존 호출자 무영향)
    sensitive: bool = False
    searchable: bool = False
    enum_values: list[str] | None = None

    @property
    def type_name(self) -> str:
        return getattr(self.value_type, "__name__", str(self.value_type))


@dataclass
class ObjectType:
    name: str
    properties: dict[str, PropertyDefinition] = field(default_factory=dict)
    # Phase 1 — 스키마 메타데이터
    display_name: str | None = None
    id_prefix: str | None = None
    icon: str | None = None

    def add_property(
        self,
        name: str,
        value_type: type,
        required: bool = False,
        *,
        sensitive: bool = False,
        searchable: bool = False,
        enum_values: list[str] | None = None,
    ) -> None:
        self.properties[name] = PropertyDefinition(
            name, value_type, required,
            sensitive=sensitive, searchable=searchable, enum_values=enum_values,
        )


@dataclass
class ObjectInstance:
    object_id: str
    object_type: ObjectType
    values: dict[str, Any]

    def validate(self) -> None:
        for property_name, definition in self.object_type.properties.items():
            if definition.required and property_name not in self.values:
                raise ValueError(f"Missing required property: {property_name}")
            if property_name in self.values and not isinstance(self.values[property_name], definition.value_type):
                raise TypeError(f"{property_name} must be {definition.type_name}")

    def get_status(self) -> str:
        return str(self.values["status"])

    def set_status(self, status: str) -> None:
        self.values["status"] = status


@dataclass
class RelationshipDefinition:
    name: str
    source_type: ObjectType
    target_type: ObjectType
    # Phase 1 — 스키마 메타데이터
    display_name: str | None = None
    reverse_display_name: str | None = None
    cardinality: str = "many_to_many"


@dataclass
class RelationshipInstance:
    relationship_type: RelationshipDefinition
    source_id: str
    target_id: str
    values: dict[str, Any] = field(default_factory=dict)
    # Phase 3 — 삭제 API를 위한 고유 ID
    rel_id: str = field(default_factory=lambda: f"rel-{uuid.uuid4().hex[:10]}")


@dataclass
class ActionDefinition:
    name: str
    object_type: ObjectType
    handler: Callable[[ObjectInstance, dict[str, Any]], dict[str, Any]]

    def execute(self, target: ObjectInstance, payload: dict[str, Any]) -> dict[str, Any]:
        if target.object_type.name != self.object_type.name:
            raise TypeError(f"{self.name} cannot run on {target.object_type.name}")
        return self.handler(target, payload)


@dataclass
class WorkflowTransition:
    name: str
    object_type: ObjectType
    from_status: str
    action_name: str
    to_status: str
    condition: Callable[[ObjectInstance, dict[str, Any]], bool] | None = None

    def can_execute(self, target: ObjectInstance, payload: dict[str, Any]) -> bool:
        if target.object_type.name != self.object_type.name:
            return False
        if target.get_status() != self.from_status:
            return False
        if self.condition is not None:
            return self.condition(target, payload)
        return True


@dataclass
class WorkflowEvent:
    object_id: str
    action_name: str
    from_status: str
    to_status: str
    actor: str
    payload: dict[str, Any]
    occurred_at: datetime = field(default_factory=datetime.utcnow)
