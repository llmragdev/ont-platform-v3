from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from database import Base
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ==========================================
# 04. SQLAlchemy RDBMS Models (SQLite 용)
# ==========================================
class Company(Base):
    __tablename__ = "ca_company"
    company_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)

class User(Base):
    __tablename__ = "ca_user"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    company_id = Column(Integer, ForeignKey("ca_company.company_id"))

class Project(Base):
    __tablename__ = "wc_project"
    project_code = Column(String(6), primary_key=True, index=True) # 6자리 식별자
    project_name = Column(String(100), nullable=False)

class Category(Base):
    __tablename__ = "wc_category"
    category_id = Column(Integer, primary_key=True, index=True)
    category_mid = Column(String(50), nullable=False)
    category_low = Column(String(50))

class ProjectRagDoc(Base):
    __tablename__ = "wc_project_rag_doc"
    doc_id = Column(String(36), primary_key=True, index=True)
    project_code = Column(String(6), ForeignKey("wc_project.project_code"))
    file_name = Column(String(255), nullable=False)
    source_url = Column(String(512))
    pipeline_status = Column(String(20), default="pending") # pending, processing, completed, error
    assigned_vector_db = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

class DialogHistory(Base):
    __tablename__ = "wc_dialog_history"
    dialog_id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    answer = Column(Text)
    used_chunks_meta = Column(Text) # JSON 문자열 형태로 저장
    created_at = Column(DateTime, server_default=func.now())

# ==========================================
# 01 & 03. Pydantic Schemas (API 입출력용)
# ==========================================
class DocumentUploadResponseData(BaseModel):
    doc_id: str
    file_name: str
    pipeline_status: str
    assigned_vector_db: str

class DocumentUploadResponse(BaseModel):
    status: str
    data: DocumentUploadResponseData
    error: Optional[str] = None

class RagSearchFilter(BaseModel):
    category_mid: Optional[str] = None
    vector_db_id: Optional[str] = None

class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    debug_mode: bool = False
    filters: Optional[RagSearchFilter] = None

class ChunkMetadata(BaseModel):
    source_name: str
    source_url: str
    page_no: Optional[int] = None
    category_mid: str
    vector_db_id: str

class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: ChunkMetadata
    similarity_score: float

class DebugInfo(BaseModel):
    execution_time_ms: int
    candidate_chunks: List[RetrievedChunk]

class RagSearchData(BaseModel):
    query: str
    answer: str
    used_chunks: List[RetrievedChunk]
    debug_info: Optional[DebugInfo] = None

class RagSearchResponse(BaseModel):
    status: str
    data: RagSearchData
    error: Optional[str] = None
