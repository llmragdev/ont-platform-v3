"""SQLAlchemy ORM models for ontology platform"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False, index=True)
    domain_id = Column(String, nullable=False, index=True)
    doc_id = Column(String, nullable=True)
    properties = Column(JSON, default={})
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Relationships
    outgoing_relations = relationship(
        "Relationship",
        foreign_keys="Relationship.from_entity_id",
        back_populates="from_entity"
    )
    incoming_relations = relationship(
        "Relationship",
        foreign_keys="Relationship.to_entity_id",
        back_populates="to_entity"
    )

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True)
    from_entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    to_entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    relation_type = Column(String, nullable=False, index=True)
    weight = Column(Float, default=1.0)
    properties = Column(JSON, default={})
    domain_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_entity = relationship(
        "Entity",
        foreign_keys=[from_entity_id],
        back_populates="outgoing_relations"
    )
    to_entity = relationship(
        "Entity",
        foreign_keys=[to_entity_id],
        back_populates="incoming_relations"
    )

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, nullable=True, index=True)
    domain_id = Column(String, nullable=True, index=True)
    operation = Column(String, nullable=False, index=True)
    old_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    actor = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        CheckConstraint("operation IN ('CREATE', 'UPDATE', 'DELETE', 'EXECUTE')", name="valid_operation"),
    )

class OntologyMetadata(Base):
    __tablename__ = "ontology_metadata"

    domain_id = Column(String, primary_key=True)
    entity_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    status = Column(String, default="active")
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActionExecution(Base):
    __tablename__ = "action_executions"

    id = Column(String, primary_key=True)
    action_id = Column(String, nullable=False, index=True)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    domain_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)  # PENDING, APPROVED, EXECUTED, FAILED
    requested_by = Column(String, nullable=False)
    executed_by = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, index=True)
    executed_at = Column(DateTime, nullable=True)

    entity = relationship("Entity", foreign_keys=[entity_id])

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'APPROVED', 'EXECUTED', 'FAILED')", name="valid_action_status"),
    )

class WriteBackQueue(Base):
    __tablename__ = "writeback_queue"

    id = Column(String, primary_key=True)
    action_execution_id = Column(String, ForeignKey("action_executions.id"), nullable=False, index=True)
    target_system = Column(String, nullable=False, index=True)  # SAP, ERP, JIRA
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False, index=True)  # PENDING, SENT, CONFIRMED, FAILED
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    action_execution = relationship("ActionExecution", foreign_keys=[action_execution_id])

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'SENT', 'CONFIRMED', 'FAILED')", name="valid_writeback_status"),
    )

class ChangeLog(Base):
    """액션 실행 이력 추적"""
    __tablename__ = "changelog"

    id = Column(String, primary_key=True)

    # Entity 정보
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    domain_id = Column(String, nullable=False, index=True)

    # Action 정보
    action_type = Column(String, nullable=False, index=True)
    actor = Column(String, nullable=False)
    source = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 상태 변화
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)

    # Write-back 추적
    sync_status = Column(String, default="PENDING", nullable=False, index=True)
    target_system = Column(String, nullable=True)
    sync_timestamp = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Relationships
    entity = relationship("Entity", foreign_keys=[entity_id])

    __table_args__ = (
        CheckConstraint("sync_status IN ('PENDING', 'SYNCED', 'FAILED')", name="valid_changelog_sync_status"),
    )


class EntityMetadata(Base):
    """엔티티 메타데이터 (Task 3-1)"""
    __tablename__ = "entity_metadata"

    entity_id = Column(String, ForeignKey("entities.id"), primary_key=True)
    created_by = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_by = Column(String, nullable=True, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String, default="active", nullable=False, index=True)  # active, archived, deprecated, deleted, draft

    # 추적 정보
    tags = Column(JSON, default=list)  # List[str]
    annotations = Column(JSON, default=dict)  # Dict[str, Any]

    # 품질 지표
    quality_score = Column(Float, nullable=True)  # 0.0 ~ 1.0
    completeness = Column(Float, nullable=True)   # 완성도
    accuracy = Column(Float, nullable=True)       # 정확성

    # 접근 제어
    owner_id = Column(String, nullable=True, index=True)
    shared_with = Column(JSON, default=list)  # List[str]
    access_level = Column(String, default="private", nullable=False)  # private, shared, public

    # Relationships
    entity = relationship("Entity", foreign_keys=[entity_id])
    transformations = relationship("Transformation", back_populates="entity", cascade="all, delete-orphan")
    lineages = relationship("LineageChain", back_populates="entity", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived', 'deprecated', 'deleted', 'draft')", name="valid_entity_status"),
        CheckConstraint("access_level IN ('private', 'shared', 'public')", name="valid_access_level"),
    )


class Transformation(Base):
    """데이터 변환 기록 (Task 3-1)"""
    __tablename__ = "transformations"

    id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("entity_metadata.entity_id"), nullable=False, index=True)
    transformation_type = Column(String, nullable=False, index=True)  # merge, split, enrich, normalize, validate, translate, aggregate
    description = Column(Text, nullable=False)
    performed_by = Column(String, nullable=False, index=True)
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 입출력 정보
    input_ids = Column(JSON, default=list)  # List[str]
    output_id = Column(String, nullable=False, index=True)

    # 파라미터 및 상태
    parameters = Column(JSON, default=dict)  # Dict[str, Any]
    status = Column(String, default="completed", nullable=False)  # completed, failed, pending

    # Relationships
    entity = relationship("EntityMetadata", back_populates="transformations", foreign_keys=[entity_id])

    __table_args__ = (
        CheckConstraint("transformation_type IN ('merge', 'split', 'enrich', 'normalize', 'validate', 'translate', 'aggregate')", name="valid_transformation_type"),
        CheckConstraint("status IN ('completed', 'failed', 'pending')", name="valid_transformation_status"),
    )


class LineageChain(Base):
    """데이터 혈통 추적 (Task 3-1)"""
    __tablename__ = "lineage_chains"

    id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("entity_metadata.entity_id"), nullable=False, index=True)

    # 출처 정보
    source_type = Column(String, nullable=False, index=True)  # user_input, import, derived, external_api, system_generated
    source_id = Column(String, nullable=True, index=True)     # 원본 엔티티/문서 ID

    # 임포트 정보
    source_name = Column(String, nullable=True)               # DBpedia, Wikidata, SAP 등
    source_url = Column(String, nullable=True)
    source_version = Column(String, nullable=True)            # 소스의 버전/시간
    original_format = Column(String, nullable=True)           # 원본 데이터 형식
    imported_at = Column(DateTime, nullable=True)

    # 혈통 연결
    direct_parent_ids = Column(JSON, default=list)  # List[str]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    entity = relationship("EntityMetadata", back_populates="lineages", foreign_keys=[entity_id])

    __table_args__ = (
        CheckConstraint("source_type IN ('user_input', 'import', 'derived', 'external_api', 'system_generated')", name="valid_source_type"),
    )
