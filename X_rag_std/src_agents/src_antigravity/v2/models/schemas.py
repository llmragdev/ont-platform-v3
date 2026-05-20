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
    source_name: str
    source_url: Optional[str] = None
    page_no: Optional[int] = None
    category_mid: Optional[str] = None
    vector_db_id: Optional[str] = None

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
