from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List

class Base(DeclarativeBase):
    pass

class Tenant(Base):
    __tablename__ = "ca_tenant"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class OrgMgnt(Base):
    __tablename__ = "ca_org_mgnt"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(20), primary_key=True) # {DD}{TT}
    org_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_org_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["ca_tenant.tenant_id"]),
    )

class User(Base):
    __tablename__ = "ca_user"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    org_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["ca_tenant.tenant_id"]),
        # Note: In a real system, we might want FK to OrgMgnt too
    )

class Project(Base):
    __tablename__ = "wc_project"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vector_db_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["ca_tenant.tenant_id"]),
    )

class Category(Base):
    __tablename__ = "wc_category"
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category_mid: Mapped[str] = mapped_column(String(50), nullable=False)
    category_low: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vector_db_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["ca_tenant.tenant_id"]),
    )

class ProjectRagDoc(Base):
    __tablename__ = "wc_project_rag_doc"
    doc_id: Mapped[str] = mapped_column(String(36), primary_key=True) # UUID
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    project_code: Mapped[str] = mapped_column(String(10), nullable=False)
    org_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    dept_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    pipeline_status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    assigned_vector_db: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "project_code"], ["wc_project.tenant_id", "wc_project.project_code"]),
    )

class DialogHistory(Base):
    __tablename__ = "wc_dialog_history"
    dialog_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    used_chunks_meta: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON String
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["ca_tenant.tenant_id"]),
    )
