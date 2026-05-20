from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1)
    model: str | None = None          # None → settings.embed_model
    tenant_id: str = "default"
    company_id: str | None = None     # legacy compatibility

    @property
    def effective_tenant_id(self) -> str:
        return self.tenant_id if self.tenant_id != "default" else (self.company_id or "default")


class EmbedResponse(BaseModel):
    embedding: list[float]
    model: str
    dimension: int
    cached: bool = False


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str | None = None          # None → settings.llm_model
    max_tokens: int = 1024
    tenant_id: str = "default"
    company_id: str | None = None     # legacy compatibility
    stream: bool = False

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
