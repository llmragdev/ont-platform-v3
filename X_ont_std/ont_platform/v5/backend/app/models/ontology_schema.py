"""Phase 4 Week 1: 온톨로지 스타일 및 스키마 확장"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OntologyStyle(str, Enum):
    """온톨로지 데이터 모델 스타일"""
    DOCUMENT = "document"                # JSON 문서 기반 (현재)
    RDF_TRIPLE = "rdf_triple"            # RDF 삼중쌍 (Linked Data)
    PROPERTY_GRAPH = "property_graph"    # Property Graph (Neo4j 스타일)
    SEMANTIC_WEB = "semantic_web"        # 시맨틱 웹 (OWL, URI)
    HIERARCHICAL = "hierarchical"        # 계층적 구조 (Tree)
    MULTI_TYPED = "multi_typed"          # 다중 타입 (한 엔티티 여러 타입)


class PropertyType(str, Enum):
    """속성의 데이터 타입"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    URI = "uri"
    LIST = "list"


class Cardinality(str, Enum):
    """관계의 카디널리티"""
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"
    MANY_TO_MANY = "N:M"


class PropertyDefinition(BaseModel):
    """속성 정의"""
    name: str
    display_name: str
    property_type: PropertyType
    description: str = ""
    required: bool = False
    unique: bool = False
    indexed: bool = False
    default_value: Optional[Any] = None
    constraints: List[Dict[str, Any]] = []  # min, max, pattern, etc.


class SchemaConstraint(BaseModel):
    """스키마 제약 조건"""
    constraint_type: str  # "cardinality", "temporal", "referential"
    description: str
    condition: Dict[str, Any]  # 제약 조건 상세


class RelationTypeDefinition(BaseModel):
    """관계 타입 정의"""
    name: str                                       # e.g., "leads"
    display_name: str
    description: str = ""
    from_type: str                                  # 출발 엔티티 타입
    to_type: str                                    # 도착 엔티티 타입
    cardinality: Cardinality = Cardinality.ONE_TO_MANY
    directed: bool = True
    properties: Dict[str, PropertyDefinition] = Field(default_factory=dict)
    constraints: List[SchemaConstraint] = Field(default_factory=list)
    is_inheritance: bool = False                    # 상속 관계 여부


class EntityTypeDefinition(BaseModel):
    """엔티티 타입 정의"""
    name: str                                       # e.g., "PROJECT"
    display_name: str
    description: str = ""
    properties: Dict[str, PropertyDefinition]
    parent_types: List[str] = Field(default_factory=list)  # 상속 지원 (다중 상속 가능)
    metadata_fields: List[str] = Field(default_factory=lambda: [
        "created_by", "created_at", "updated_by", "updated_at", "version"
    ])
    supports_multi_typing: bool = False             # 다중 타입 지원 여부
    style_specific_config: Optional[Dict[str, Any]] = None  # 스타일별 설정


# 하위호환성을 위한 별칭
EntityType = EntityTypeDefinition
RelationType = RelationTypeDefinition


class RDFNamespace(BaseModel):
    """RDF 네임스페이스 정의"""
    prefix: str  # e.g., "avoucher"
    uri: str     # e.g., "http://nipa.go.kr/ontology/ai-voucher-2025#"
    description: str = ""


class DomainSchema(BaseModel):
    """도메인별 온톨로지 스키마 정의"""
    domain_id: str
    ontology_style: OntologyStyle
    display_name: str
    description: str = ""

    # 구조
    entity_types: Dict[str, EntityTypeDefinition]       # entity_name → EntityTypeDefinition
    relation_types: Dict[str, RelationTypeDefinition]   # relation_name → RelationTypeDefinition
    constraints: List[SchemaConstraint] = Field(default_factory=list)

    # RDF 지원
    rdf_namespaces: List[RDFNamespace] = Field(default_factory=list)

    # 메타정보
    version: str = "1.0"
    created_by: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    # 추가 설정
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StyleMigrationPlan(BaseModel):
    """온톨로지 스타일 마이그레이션 계획"""
    domain_id: str
    from_style: OntologyStyle
    to_style: OntologyStyle
    migration_rules: List[Dict[str, Any]]  # 변환 규칙
    estimated_entity_count: int
    estimated_duration_seconds: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, in_progress, completed, failed


class SchemaValidationResult(BaseModel):
    """스키마 검증 결과"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
