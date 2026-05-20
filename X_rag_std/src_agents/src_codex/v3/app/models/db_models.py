from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


class Company(Base):
    __tablename__ = "ca_company"

    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class OrganizationManagement(Base):
    __tablename__ = "ca_org_mgnt"

    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.tenant_id"), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    org_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(2), nullable=False)
    org_level: Mapped[int] = mapped_column(Integer, default=2)
    parent_org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)


class User(Base):
    __tablename__ = "ca_user"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.tenant_id"), nullable=False)
    org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="viewer")


class Project(Base):
    __tablename__ = "wc_project"

    project_code: Mapped[str] = mapped_column(String(6), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.tenant_id"), default="default")
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
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "org_id"], ["ca_org_mgnt.tenant_id", "ca_org_mgnt.org_id"]),
    )

    doc_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_code: Mapped[str] = mapped_column(String(6), default="000001")
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.tenant_id"), nullable=False)
    org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    pipeline_status: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_vector_db: Mapped[str] = mapped_column(String(128), nullable=False)
    category_mid: Mapped[str] = mapped_column(String(128), nullable=False)
    category_low: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class DialogHistory(Base):
    __tablename__ = "wc_dialog_history"

    dialog_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("ca_company.tenant_id"), nullable=False)
    org_id: Mapped[str | None] = mapped_column(String(8), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    used_chunks: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
