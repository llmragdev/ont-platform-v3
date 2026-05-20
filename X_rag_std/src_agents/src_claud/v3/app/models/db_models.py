from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Integer, SmallInteger, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "ca_company"

    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OrganizationManagement(Base):
    """조직 관리 — (tenant_id, org_id) 복합 PK.
    멀티테넌트에서 org_id는 테넌트별로 중복될 수 있으므로 복합키 필수.
    """
    __tablename__ = "ca_org_mgnt"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "parent_org_id"],
            ["ca_org_mgnt.tenant_id", "ca_org_mgnt.org_id"],
            name="fk_org_parent",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ca_company.tenant_id"), primary_key=True
    )
    org_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    org_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(2), nullable=False)
    org_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    parent_org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class User(Base):
    __tablename__ = "ca_user"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ca_company.tenant_id"), nullable=False
    )
    org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(64), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Project(Base):
    __tablename__ = "wc_project"

    project_code: Mapped[str] = mapped_column(String(6), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ca_company.tenant_id"), nullable=False
    )
    vector_db_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Category(Base):
    __tablename__ = "wc_category"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_code: Mapped[str] = mapped_column(
        String(6), ForeignKey("wc_project.project_code"), nullable=False
    )
    category_mid: Mapped[str] = mapped_column(String(128), nullable=False)
    category_low: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vector_db_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Intent(Base):
    __tablename__ = "wc_intent"

    intent_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_code: Mapped[str] = mapped_column(
        String(6), ForeignKey("wc_project.project_code"), nullable=False
    )
    intent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_mid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProjectRagDocument(Base):
    __tablename__ = "wc_project_rag_doc"

    doc_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_code: Mapped[str] = mapped_column(
        String(6), ForeignKey("wc_project.project_code"), default="000001"
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ca_company.tenant_id"), nullable=False
    )
    org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    category_mid: Mapped[str] = mapped_column(String(128), nullable=False)
    category_low: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pipeline_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    assigned_vector_db: Mapped[str] = mapped_column(String(128), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class DialogHistory(Base):
    __tablename__ = "wc_dialog_history"

    dialog_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ca_company.tenant_id"), nullable=False
    )
    org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    project_code: Mapped[str | None] = mapped_column(
        String(6), ForeignKey("wc_project.project_code"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    used_chunks: Mapped[str] = mapped_column(Text, nullable=False)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "sys_audit_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
