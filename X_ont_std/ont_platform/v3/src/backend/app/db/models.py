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
