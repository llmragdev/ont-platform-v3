from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "ca_company"

    company_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OrganizationManagement(Base):
    __tablename__ = "ca_org_mgnt"

    org_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.company_id"), nullable=False)
    org_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_org_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class User(Base):
    __tablename__ = "ca_user"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.company_id"), nullable=False)
    org_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("ca_org_mgnt.org_id"), nullable=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="viewer")


class Project(Base):
    __tablename__ = "wc_project"

    project_code: Mapped[str] = mapped_column(String(6), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vector_db_id: Mapped[str] = mapped_column(String(128), nullable=False)


class Category(Base):
    __tablename__ = "wc_category"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_mid: Mapped[str] = mapped_column(String(128), nullable=False)
    category_low: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vector_db_id: Mapped[str] = mapped_column(String(128), nullable=False)


class Intent(Base):
    __tablename__ = "wc_intent"

    intent_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intent_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProjectRagDocument(Base):
    __tablename__ = "wc_project_rag_doc"

    doc_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_code: Mapped[str] = mapped_column(String(6), ForeignKey("wc_project.project_code"), default="000001")
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    pipeline_status: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_vector_db: Mapped[str] = mapped_column(String(128), nullable=False)
    category_mid: Mapped[str] = mapped_column(String(128), nullable=False)
    category_low: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DialogHistory(Base):
    __tablename__ = "wc_dialog_history"

    dialog_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    used_chunks: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "sys_audit_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
