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
