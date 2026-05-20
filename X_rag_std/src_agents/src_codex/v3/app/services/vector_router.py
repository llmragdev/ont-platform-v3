import json
from dataclasses import dataclass

from app.core.config import settings
from app.core.errors import VectorDbConnectionError
from app.services.embeddings import HashEmbeddingService
from app.services.vector_adapters import (
    BaseVectorDbAdapter,
    ChromaVectorDbAdapter,
    LocalJsonVectorDbAdapter,
)


@dataclass(frozen=True)
class RoutingRule:
    vector_db_id: str
    target_category_mid: list[str]
    engine_type: str
    connection: dict


class VectorDbRouter:
    def __init__(self, embedding_service: HashEmbeddingService) -> None:
        self.embedding_service = embedding_service
        self.rules = self._load_rules()

    def resolve_vector_db_id(
        self,
        category_mid: str | None = None,
        vector_db_id: str | None = None,
    ) -> str:
        if vector_db_id:
            return vector_db_id
        category = category_mid or "default"
        for rule in self.rules:
            if category in rule.target_category_mid:
                return rule.vector_db_id
        return "vdb_default_01"

    def get_adapter(
        self,
        category_mid: str | None = None,
        vector_db_id: str | None = None,
    ) -> BaseVectorDbAdapter:
        resolved_id = self.resolve_vector_db_id(category_mid, vector_db_id)
        rule = self._find_rule(resolved_id)
        engine_type = settings.vector_db_engine
        if engine_type == "local_json":
            engine_type = rule.engine_type

        if engine_type == "chroma":
            collection_name = rule.connection.get("collection_name", resolved_id)
            return ChromaVectorDbAdapter(
                vector_db_id=resolved_id,
                host=rule.connection.get("host", settings.chroma_host),
                port=rule.connection.get("port", settings.chroma_port),
                collection_name=collection_name,
                embedding_service=self.embedding_service,
            )

        if engine_type != "local_json":
            raise VectorDbConnectionError(f"Unsupported engine_type: {engine_type}")
        store_path = settings.vector_store_dir / f"{resolved_id}.json"
        return LocalJsonVectorDbAdapter(resolved_id, store_path, self.embedding_service)

    def _load_rules(self) -> list[RoutingRule]:
        config = json.loads(settings.routing_config_path.read_text(encoding="utf-8"))
        return [RoutingRule(**item) for item in config.get("routing_rules", [])]

    def _find_rule(self, vector_db_id: str) -> RoutingRule:
        for rule in self.rules:
            if rule.vector_db_id == vector_db_id:
                return rule
        return RoutingRule(
            vector_db_id=vector_db_id,
            target_category_mid=[],
            engine_type="local_json",
            connection={"collection_name": vector_db_id},
        )
