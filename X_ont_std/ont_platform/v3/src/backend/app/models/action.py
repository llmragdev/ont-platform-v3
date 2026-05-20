"""Phase 3: ActionDefinition 모델 — 비즈니스 액션 정의"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict


class ConditionOperator(str, Enum):
    """조건 평가 연산자"""
    NOT_NULL = "not_null"
    EQUALS = "equals"
    GTE = "gte"
    LTE = "lte"
    GT = "gt"
    LT = "lt"
    EXISTS = "exists"


class Condition(BaseModel):
    """단일 조건"""
    field: str                          # e.g., "properties.budget"
    operator: ConditionOperator
    value: int | str | bool | None = None
    message: str = "조건을 만족하지 않습니다"
    and_condition: Condition | None = None  # 복합 조건 (AND)


class PropertyChange(BaseModel):
    """속성 변경 규칙"""
    field: str                          # e.g., "properties.approved_by"
    value: str | int | bool            # 템플릿 가능: "{{ user_id }}", "{{ timestamp }}"


class SideEffect(BaseModel):
    """부수 효과"""
    type: str                           # changelog, write_back, notification, audit
    target_system: str | None = None    # e.g., "SAP"
    recipients: list[str] | None = None  # e.g., ["applicant", "manager"]


class ConditionalPermission(BaseModel):
    """조건부 권한"""
    condition: Condition
    allowed_roles: list[str]
    description: str | None = None


class ActionDefinition(BaseModel):
    """액션 정의 — workflow.json에서 로드됨"""
    model_config = ConfigDict(use_enum_values=True)

    id: str                                      # approve_project
    display_name: str                           # 과제 승인
    entity_type: str                            # PROJECT
    from_statuses: list[str]                    # [UnderReview]
    to_status: str | None                       # Approved
    preconditions: list[Condition] = []
    allowed_roles: list[str] = []
    conditional_permissions: list[ConditionalPermission] = []
    property_changes: list[PropertyChange] = []
    required_fields: list[str] = []
    side_effects: list[SideEffect] = []

    def __init__(self, **data):
        """workflow.json 딕셔너리에서 생성"""
        # Condition 객체 변환
        if "preconditions" in data:
            data["preconditions"] = [
                Condition(**c) if isinstance(c, dict) else c
                for c in data.get("preconditions", [])
            ]

        # ConditionalPermission 객체 변환
        if "conditional_permissions" in data:
            data["conditional_permissions"] = [
                ConditionalPermission(**cp) if isinstance(cp, dict) else cp
                for cp in data.get("conditional_permissions", [])
            ]

        # PropertyChange 객체 변환
        if "property_changes" in data:
            data["property_changes"] = [
                PropertyChange(**pc) if isinstance(pc, dict) else pc
                for pc in data.get("property_changes", [])
            ]

        # SideEffect 객체 변환
        if "side_effects" in data:
            data["side_effects"] = [
                SideEffect(**se) if isinstance(se, dict) else se
                for se in data.get("side_effects", [])
            ]

        super().__init__(**data)

    def has_preconditions(self) -> bool:
        """전제 조건이 있는지 확인"""
        return len(self.preconditions) > 0

    def has_conditional_permissions(self) -> bool:
        """조건부 권한이 있는지 확인"""
        return len(self.conditional_permissions) > 0

    def requires_approval(self) -> bool:
        """승인이 필요한 액션인지"""
        return "Approve" in self.id or "approve" in self.id.lower()


class ActionRequest(BaseModel):
    """액션 실행 요청"""
    doc_id: str
    entity_id: str
    action: str                          # 액션 ID (e.g., "approve_project")
    domain_id: str = "ai-voucher-2025"
    params: dict = {}                    # 필수 필드 값 전달 (e.g., {"rejection_reason": "..."})


class ActionResponse(BaseModel):
    """액션 실행 응답"""
    entity_id: str
    action: str
    from_status: str | None
    to_status: str | None
    approved_by: str | None = None
    approved_at: str | None = None
    message: str = "액션이 성공적으로 실행되었습니다"
