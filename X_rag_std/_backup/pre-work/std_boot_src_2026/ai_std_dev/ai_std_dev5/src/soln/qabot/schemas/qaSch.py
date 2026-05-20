import os
from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel
from typing import List, Optional

class QaSettings(BaseSettings):
    # .env의 5장 전용 변수명 매핑 (하드코딩 제거)
    company_id: str = Field(default="abc", validation_alias="COMPANY_ID5")
    source_doc_dir: str = Field(default="F:/ai_std_dev/data/raw_documents", validation_alias="SOURCE_DOC_DIR5")
    db_base_path: str = Field(default="F:/ai_std_dev/data/ai_std_dev_r5", validation_alias="VECTOR_DB_BASE_PATH5")
    db_name: str = Field(default="hnix_standard_rag", validation_alias="VECTOR_DB_NAME5")
    core_url: str = Field(default="http://localhost:8010/api/v1/llm/generate", validation_alias="CORE_INFERENCE_URL5")

    class Config:
        env_file = "F:/ai_std_dev/.env"
        extra = "ignore"

    @property
    def full_db_path(self) -> str:
        return os.path.abspath(os.path.join(self.db_base_path, self.db_name))

# API 통신 규격
class QaRequest(BaseModel):
    question: str
    user_id: str = "guest"

class QaResponse(BaseModel):
    answer: str
    source_documents: Optional[List[str]] = []
    status: str = "success"

class IngestResponse(BaseModel):
    status: str
    message: str