from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Company(Base):
    __tablename__ = "ca_company"
    company_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)

class User(Base):
    __tablename__ = "ca_user"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("ca_company.company_id"))

class Project(Base):
    __tablename__ = "wc_project"
    project_code: Mapped[str] = mapped_column(String(6), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(100), nullable=False)

class Category(Base):
    __tablename__ = "wc_category"
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_mid: Mapped[str] = mapped_column(String(50), nullable=False)
    category_low: Mapped[str | None] = mapped_column(String(50), nullable=True)

class ProjectRagDoc(Base):
    __tablename__ = "wc_project_rag_doc"
    doc_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_code: Mapped[str | None] = mapped_column(String(6), ForeignKey("wc_project.project_code"), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pipeline_status: Mapped[str] = mapped_column(String(20), default="pending")
    assigned_vector_db: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DialogHistory(Base):
    __tablename__ = "wc_dialog_history"
    dialog_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    used_chunks_meta: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON String
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
