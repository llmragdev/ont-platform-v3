"""Phase 4 Week 2: 엔티티 메타데이터 및 감시 시스템"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """데이터 출처 타입"""
    USER_INPUT = "user_input"          # 사용자 직접 입력
    IMPORT = "import"                  # 파일/시스템에서 임포트
    DERIVED = "derived"                # 다른 데이터에서 파생
    EXTERNAL_API = "external_api"      # 외부 API 연동
    SYSTEM_GENERATED = "system_generated"  # 시스템 자동 생성


class TransformationType(str, Enum):
    """데이터 변환 타입"""
    MERGE = "merge"                    # 여러 엔티티 통합
    SPLIT = "split"                    # 엔티티 분할
    ENRICH = "enrich"                  # 정보 추가
    NORMALIZE = "normalize"            # 정규화
    VALIDATE = "validate"              # 검증 및 정정
    TRANSLATE = "translate"            # 언어/형식 변환
    AGGREGATE = "aggregate"            # 집계


class EntityStatus(str, Enum):
    """엔티티 상태"""
    ACTIVE = "active"                  # 활성
    ARCHIVED = "archived"              # 보관됨
    DEPRECATED = "deprecated"          # 사용 중단됨
    DELETED = "deleted"                # 삭제됨
    DRAFT = "draft"                    # 초안


class Transformation(BaseModel):
    """데이터 변환 기록"""
    transformation_id: str
    transformation_type: TransformationType
    description: str
    performed_by: str
    performed_at: datetime
    input_ids: List[str]               # 입력 엔티티 ID들
    output_id: str                     # 결과 엔티티 ID
    parameters: Dict[str, Any]         # 변환 파라미터
    status: str = "completed"          # completed, failed, pending


class ImportMetadata(BaseModel):
    """외부 소스 임포트 메타데이터"""
    source_type: DataSourceType
    source_name: str                   # 예: "DBpedia", "Wikidata", "SAP"
    source_id: str                     # 외부 시스템의 ID
    source_url: Optional[str] = None   # 소스 URL
    imported_at: datetime
    import_version: str                # 소스의 버전/시간
    original_format: str               # 원본 데이터 형식


class LineageInfo(BaseModel):
    """데이터 혈통(Lineage) 추적"""
    source_type: DataSourceType        # 데이터 출처
    source_id: Optional[str] = None    # 원본 엔티티/문서 ID
    transformations: List[Transformation] = []  # 변환 이력
    import_metadata: Optional[ImportMetadata] = None  # 임포트 정보
    direct_parent_ids: List[str] = []  # 직접 부모 엔티티들 (혈통 추적)


class EntityMetadata(BaseModel):
    """엔티티 메타데이터 (감시 시스템)"""
    entity_id: str
    created_by: str
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    version: int = 1                   # 엔티티 버전
    status: EntityStatus = EntityStatus.ACTIVE

    # 추적 정보
    lineage: Optional[LineageInfo] = None

    # 분류 및 검색
    tags: List[str] = []               # 분류용 태그
    annotations: Dict[str, Any] = Field(default_factory=dict)  # 자유형 메모

    # 품질 지표
    quality_score: Optional[float] = None  # 0.0 ~ 1.0, 데이터 품질
    completeness: Optional[float] = None   # 완성도
    accuracy: Optional[float] = None       # 정확성

    # 접근 제어
    owner_id: Optional[str] = None
    shared_with: List[str] = []        # 공유 대상자 ID들
    access_level: str = "private"      # private, shared, public


class EntityVersion(BaseModel):
    """엔티티 버전 관리"""
    entity_id: str
    version: int
    data: Dict[str, Any]               # 해당 버전의 완전한 데이터
    changed_fields: List[str]          # 변경된 필드들
    change_reason: str                 # 변경 사유
    changed_by: str
    changed_at: datetime
    is_current: bool = True

    # 메타정보
    checksum: Optional[str] = None     # 데이터 무결성 확인용


class AuditLogAction(str, Enum):
    """감사 로그 액션 타입"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    EXPORT = "export"
    IMPORT = "import"
    VIEW = "view"
    SHARE = "share"
    CHANGE_STATUS = "change_status"
    MERGE = "merge"


class AuditLog(BaseModel):
    """감사 로그 (완전한 추적)"""
    audit_id: str
    entity_id: str
    action: AuditLogAction

    # 변경 내용
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None

    # 수행 정보
    performed_by: str
    performed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # 문맥 정보
    reason: Optional[str] = None       # "사용자 요청", "자동 동기화" 등
    request_id: Optional[str] = None   # 요청 추적 ID

    # 결과
    success: bool = True
    error_message: Optional[str] = None


class AuditSummary(BaseModel):
    """감사 요약 (통계)"""
    entity_id: str
    total_changes: int
    last_change_at: datetime
    changes_by_action: Dict[str, int]  # action → count
    changes_by_user: Dict[str, int]    # user_id → count
    change_frequency: str              # "high", "medium", "low"


class DataQualityReport(BaseModel):
    """데이터 품질 리포트"""
    entity_id: str
    report_date: datetime
    generated_by: str

    # 품질 지표
    completeness: float                # 필수 필드 완성도 (%)
    accuracy: float                    # 데이터 정확성 (%)
    consistency: float                 # 일관성 (%)
    timeliness: float                  # 최신성 (%)

    # 문제점
    issues: List[Dict[str, Any]] = []  # {field, severity, description}
    recommendations: List[str] = []    # 개선 권고사항

    # 종합
    overall_score: float               # 0.0 ~ 1.0


class LineageQuery(BaseModel):
    """혈통 추적 쿼리"""
    entity_id: str
    direction: str = "both"            # "upstream" (입력), "downstream" (출력), "both"
    depth: int = 3                     # 추적 깊이
    include_transformations: bool = True
