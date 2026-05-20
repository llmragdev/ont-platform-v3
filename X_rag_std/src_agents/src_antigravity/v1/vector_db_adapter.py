from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseVectorDbAdapter(ABC):
    @abstractmethod
    def add_documents(self, chunks: List[Dict[str, Any]], metadata: List[Dict[str, Any]]) -> bool:
        pass
        
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        pass

class ChromaAdapter(BaseVectorDbAdapter):
    def __init__(self, host: str, port: int, collection_name: str):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        
    def add_documents(self, chunks: List[Dict[str, Any]], metadata: List[Dict[str, Any]]) -> bool:
        # Dummy Implementation
        return True
        
    def search(self, query_vector: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        # Dummy Search Results matching ChunkMetadata schema
        return [
            {
                "chunk_id": "doc123#chunk1",
                "content": "이것은 ChromaDB에서 검색된 텍스트입니다.",
                "similarity_score": 0.95,
                "metadata": {
                    "source_name": "sample.pdf",
                    "source_url": "http://storage/sample.pdf",
                    "page_no": 1,
                    "category_mid": "IT",
                    "vector_db_id": "vdb_tech_01"
                }
            }
        ]

# Registry Configuration as per Detail 02
ROUTING_REGISTRY = {
    "vdb_policy_01": {
        "target_category_mid": ["규정", "지침", "매뉴얼"],
        "engine_type": "chroma",
        "connection": {"host": "chroma-policy", "port": 8000, "collection_name": "hr_policy_dim1536"}
    },
    "vdb_tech_01": {
        "target_category_mid": ["IT", "개발표준", "아키텍처"],
        "engine_type": "chroma",
        "connection": {"host": "chroma-tech", "port": 8000, "collection_name": "tech_docs_dim1536"}
    }
}

class VectorDbRouter:
    @staticmethod
    def get_adapter_by_category(category_mid: str) -> BaseVectorDbAdapter:
        for vdb_id, config in ROUTING_REGISTRY.items():
            if category_mid in config["target_category_mid"]:
                conn = config["connection"]
                return ChromaAdapter(conn["host"], conn["port"], conn["collection_name"])
        # Default fallback
        return ChromaAdapter("localhost", 8000, "default_collection")
