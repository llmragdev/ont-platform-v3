from __future__ import annotations

import json

from pydantic import BaseModel

from app.core.config import settings
from app.services.embedding.base import EmbeddingService
from app.services.vector_db.base import VectorDbAdapter
from app.services.vector_db.local_json import LocalJsonVectorDbAdapter


class RoutingRule(BaseModel):
    vector_db_id: str
    target_category_mid: list[str]
    engine_type: str = "local_json"
    connection: dict = {}


class VectorDbRouter:
    """벡터 DB 라우터 — vector_db_id 우선, category_mid 폴백, JSON 설정 파일 기반.
    v1은 category만, Codex는 JSON 설정 기반. 이 구현은 두 방식을 모두 계승.
    """

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service
        self._rules: list[RoutingRule] | None = None

    @property
    def rules(self) -> list[RoutingRule]:
        if self._rules is None:
            self._rules = self._load_rules()
        return self._rules

    def resolve_vector_db_id(
        self,
        category_mid: str | None = None,
        vector_db_id: str | None = None,
    ) -> str:
        if vector_db_id:
            return vector_db_id
        if category_mid:
            for rule in self.rules:
                if category_mid in rule.target_category_mid:
                    return rule.vector_db_id
        return "vdb_default_01"

    def get_adapter(
        self,
        category_mid: str | None = None,
        vector_db_id: str | None = None,
    ) -> VectorDbAdapter:
        resolved_id = self.resolve_vector_db_id(category_mid, vector_db_id)
        rule = self._find_rule(resolved_id)
        engine = rule.engine_type if rule else "local_json"

        if engine == "chroma":
            from app.services.vector_db.chroma import ChromaAdapter
            conn = rule.connection if rule else {}
            return ChromaAdapter(
                vector_db_id=resolved_id,
                host=conn.get("host", "localhost"),
                port=conn.get("port", 8000),
                collection_name=conn.get("collection_name", resolved_id),
            )

        store_path = settings.vector_store_dir / f"{resolved_id}.json"
        return LocalJsonVectorDbAdapter(resolved_id, store_path, self.embedding_service)

    def _find_rule(self, vector_db_id: str) -> RoutingRule | None:
        for rule in self.rules:
            if rule.vector_db_id == vector_db_id:
                return rule
        return None

    def _load_rules(self) -> list[RoutingRule]:
        if not settings.routing_config_path.exists():
            return []
        try:
            data = json.loads(settings.routing_config_path.read_text(encoding="utf-8"))
            return [RoutingRule(**item) for item in data.get("routing_rules", [])]
        except (json.JSONDecodeError, Exception):
            return []
