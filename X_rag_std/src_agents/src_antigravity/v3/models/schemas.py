from pydantic import BaseModel
from typing import Optional, List

class DocumentUploadResponseData(BaseModel):
    doc_id: str
    file_name: str
    pipeline_status: str
    assigned_vector_db: Optional[str] = None

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
    doc_id: str
    tenant_id: str
    org_id: Optional[str] = None
    dept_code: Optional[str] = None
    vector_db_id: str
    source_name: str
    source_url: Optional[str] = None
    page_no: int
    created_at: str

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

# --- Meta Schemas ---

class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    vector_db_id: Optional[str] = None

class ProjectResponse(BaseModel):
    tenant_id: str
    project_code: str
    project_name: str
    vector_db_id: Optional[str] = None

class CategoryCreate(BaseModel):
    category_mid: str
    category_low: Optional[str] = None
    vector_db_id: Optional[str] = None

class CategoryResponse(BaseModel):
    category_id: int
    tenant_id: str
    category_mid: str
    category_low: Optional[str] = None
    vector_db_id: Optional[str] = None
