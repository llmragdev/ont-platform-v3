from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, example="온톨로지 설계 원칙", description="임베딩할 텍스트")
    model: str | None = Field(None, example="models/gemini-embedding-001", description="모델명 (기본: settings.embed_model)")
    tenant_id: str = Field("default", example="default", description="테넌트 ID")
    company_id: str | None = Field(None, example="company_abc", description="조직 ID (선택)")

    @property
    def effective_tenant_id(self) -> str:
        return self.tenant_id if self.tenant_id != "default" else (self.company_id or "default")


class EmbedResponse(BaseModel):
    embedding: list[float]
    model: str
    dimension: int
    cached: bool = False


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, example="대한민국의 수도는?", description="생성할 프롬프트")
    model: str | None = Field(None, example="gemini-2.5-flash-lite", description="모델명 (기본: settings.llm_model)")
    max_tokens: int = Field(1024, example=1024, description="최대 토큰 수")
    tenant_id: str = Field("default", example="default", description="테넌트 ID")
    company_id: str | None = Field(None, example="company_abc", description="조직 ID (선택)")
    stream: bool = Field(False, example=False, description="스트리밍 여부")

    @property
    def effective_tenant_id(self) -> str:
        return self.tenant_id if self.tenant_id != "default" else (self.company_id or "default")


class GenerateResponse(BaseModel):
    answer: str
    model: str


class HealthItem(BaseModel):
    name: str
    status: str
    detail: str = ""


class HealthResponse(BaseModel):
    status: str
    checks: list[HealthItem]
