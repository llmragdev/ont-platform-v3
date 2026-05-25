from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    code: str
    message: str


class ChunkMetadata(BaseModel):
    source_name: str
    source_url: str
    page_no: int | None = None
    doc_id: str
    category_large: str | None = None
    category_mid: str
    category_low: str | None = None
    chunk_type: str = "text"
    tenant_id: str
    org_id: str | None = None          # 조직 코드 (없으면 전사 공유 문서)
    dept_code: str | None = None       # org_id 앞 2자리 파생값
    vector_db_id: str = ""
    created_at: str | None = None      # ISO 8601
    tags: list[str] = []               # RDBMS/API 응답 전용 — Vector DB metadata에 저장 안 함


class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    similarity_score: float
    metadata: ChunkMetadata


class DebugInfo(BaseModel):
    execution_time_ms: int
    candidate_chunks: list[RetrievedChunk]
    metadata: dict | None = None  # 추가 디버그 정보 (캐시 상태 등)


class RagSearchFilter(BaseModel):
    category_mid: str | None = None
    vector_db_id: str | None = None


class RagSearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    limit: int | None = Field(default=None, ge=1, le=20)
    filters: RagSearchFilter | None = None
    debug_mode: bool = False


class RagSearchData(BaseModel):
    query: str
    answer: str
    used_chunks: list[RetrievedChunk]
    debug_info: DebugInfo | None = None


class RagSearchResponse(BaseModel):
    status: str
    data: RagSearchData | None = None
    error: ErrorDetail | None = None
    chunks: list[RetrievedChunk] = []
    total_chunks: int = 0


class DocumentUploadData(BaseModel):
    doc_id: str
    pipeline_status: str
    file_name: str
    assigned_vector_db: str
    version: int


class DocumentUploadResponse(BaseModel):
    status: str
    data: DocumentUploadData | None = None
    error: ErrorDetail | None = None
    doc_id: str | None = None


class DocumentRecord(BaseModel):
    doc_id: str
    tenant_id: str
    org_id: str | None = None
    file_name: str
    pipeline_status: str
    assigned_vector_db: str
    category_mid: str
    category_low: str | None
    version: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ListDocumentsResponse(BaseModel):
    status: str
    data: list[DocumentRecord]
    error: ErrorDetail | None = None
    documents: list[DocumentRecord] = []


class ExpandedQuery(BaseModel):
    query: str
    weight: float


class QueryExpansionRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class QueryExpansionResponse(BaseModel):
    status: str = "success"
    original_query: str
    expanded_queries: list[ExpandedQuery]
    error: ErrorDetail | None = None


class RerankRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    chunks: list[RetrievedChunk]


class RerankResponse(BaseModel):
    status: str = "success"
    chunks: list[RetrievedChunk]
    error: ErrorDetail | None = None


class BatchSearchRequest(BaseModel):
    queries: list[RagSearchRequest] = Field(min_length=1, max_length=20)


class BatchSearchResult(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    total_chunks: int


class BatchSearchResponse(BaseModel):
    status: str = "success"
    results: list[BatchSearchResult]
    processing_time_ms: int
    error: ErrorDetail | None = None


class DocumentUpdateRequest(BaseModel):
    category_mid: str | None = None
    category_low: str | None = None


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
    category_low: str | None
    vector_db_id: str


class CategoryResponse(BaseModel):
    status: str
    data: CategoryRecord | None = None
    error: ErrorDetail | None = None


class ListCategoriesResponse(BaseModel):
    status: str
    data: list[CategoryRecord]
    error: ErrorDetail | None = None


class HealthCheckItem(BaseModel):
    name: str
    status: str
    detail: str | None = None


class HealthCheckResponse(BaseModel):
    status: str
    checks: list[HealthCheckItem]
