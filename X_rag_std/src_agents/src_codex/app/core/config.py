import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_root: Path = Path(__file__).resolve().parents[2]
    storage_root: Path = Path(__file__).resolve().parents[2] / "storage"
    raw_documents_dir: Path = Path(__file__).resolve().parents[2] / "storage" / "raw_documents"
    processed_dir: Path = Path(__file__).resolve().parents[2] / "storage" / "processed"
    vector_store_dir: Path = Path(__file__).resolve().parents[2] / "storage" / "vector_store"
    db_path: Path = Path(__file__).resolve().parents[2] / "storage" / "metadata.db"
    routing_config_path: Path = Path(__file__).resolve().parents[2] / "storage" / "vector_routing.json"
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "hash")
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_gateway_url: str = os.getenv("LLM_GATEWAY_URL", "")
    vector_db_engine: str = os.getenv("VECTOR_DB_ENGINE", "local_json")
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8001"))

    @property
    def database_url(self) -> str:
        default_url = f"sqlite:///{self.db_path.as_posix()}"
        return os.getenv("DATABASE_URL", default_url)


settings = Settings()


DEFAULT_ROUTING_CONFIG = {
    "routing_rules": [
        {
            "vector_db_id": "vdb_policy_01",
            "target_category_mid": ["규정", "지침", "매뉴얼", "policy"],
            "engine_type": "local_json",
            "connection": {"collection_name": "policy_docs_dim64"},
        },
        {
            "vector_db_id": "vdb_tech_01",
            "target_category_mid": ["IT", "개발표준", "아키텍처", "tech"],
            "engine_type": "local_json",
            "connection": {"collection_name": "tech_docs_dim64"},
        },
        {
            "vector_db_id": "vdb_default_01",
            "target_category_mid": ["default", "일반"],
            "engine_type": "local_json",
            "connection": {"collection_name": "default_docs_dim64"},
        },
    ]
}


def ensure_runtime_dirs() -> None:
    for path in (
        settings.storage_root,
        settings.raw_documents_dir,
        settings.processed_dir,
        settings.vector_store_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)

    if not settings.routing_config_path.exists():
        import json

        settings.routing_config_path.write_text(
            json.dumps(DEFAULT_ROUTING_CONFIG, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
