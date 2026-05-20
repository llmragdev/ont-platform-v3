from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    error_code: str
    message: str


class RagSearchFilter(BaseModel):
    category_mid: str | None = None
    vector_db_id: str | None = None


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    debug_mode: bool = False
    filters: RagSearchFilter | None = None


class ChunkMetadata(BaseModel):
    source_name: str
    source_url: str
    page_no: int | None = None
    category_mid: str
    vector_db_id: str
    doc_id: str | None = None
    tenant_id: str
    org_id: str | None = None
    dept_code: str | None = None
    category_low: str | None = None
    chunk_type: str = "text"
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: ChunkMetadata
    similarity_score: float


class DebugInfo(BaseModel):
    execution_time_ms: int
    candidate_chunks: list[RetrievedChunk]


class RagSearchData(BaseModel):
    query: str
    answer: str
    used_chunks: list[RetrievedChunk]
    debug_info: DebugInfo | None = None


class RagSearchResponse(BaseModel):
    status: str
    data: RagSearchData | None
    error: ErrorDetail | None = None


class DocumentUploadData(BaseModel):
    doc_id: str
    file_name: str
    pipeline_status: str
    assigned_vector_db: str


class DocumentUploadResponse(BaseModel):
    status: str
    data: DocumentUploadData | None
    error: ErrorDetail | None = None


class DocumentRecordResponse(BaseModel):
    doc_id: str
    project_code: str = "default"
    tenant_id: str
    org_id: str | None = None
    file_name: str
    source_url: str
    pipeline_status: str
    assigned_vector_db: str
    category_mid: str
    category_low: str | None = None
    error_message: str | None = None
    version: int
    created_at: str
    updated_at: str


class ListDocumentsResponse(BaseModel):
    status: str
    data: list[DocumentRecordResponse]
    error: ErrorDetail | None = None


class ApiSuccessResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any] | None = None
    error: ErrorDetail | None = None


class ProjectCreateRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=255)
    vector_db_id: str = Field(min_length=1, max_length=128)
    project_code: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$")


class ProjectRecord(BaseModel):
    project_code: str
    project_name: str
    vector_db_id: str


class ProjectResponse(BaseModel):
    status: str
    data: ProjectRecord | None = None
    error: ErrorDetail | None = None


class ListProjectsResponse(BaseModel):
    status: str
    data: list[ProjectRecord]
    error: ErrorDetail | None = None


class CategoryCreateRequest(BaseModel):
    category_mid: str = Field(min_length=1, max_length=128)
    vector_db_id: str = Field(min_length=1, max_length=128)
    category_low: str | None = Field(default=None, max_length=128)


class CategoryRecord(BaseModel):
    category_id: int
    category_mid: str
    category_low: str | None = None
    vector_db_id: str


class CategoryResponse(BaseModel):
    status: str
    data: CategoryRecord | None = None
    error: ErrorDetail | None = None


class ListCategoriesResponse(BaseModel):
    status: str
    data: list[CategoryRecord]
    error: ErrorDetail | None = None
