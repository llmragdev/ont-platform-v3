import os
import json
import uuid
from typing import List, Dict, Any
from services.gateway_client import LlmGatewayClient

class LocalJsonVectorDbAdapter:
    """
    하드코딩을 피하기 위해 로컬 JSON 파일을 VectorDB처럼 사용하는 어댑터.
    """
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
        os.makedirs(self.storage_dir, exist_ok=True)
        self.db_path = os.path.join(self.storage_dir, f"{self.collection_name}.json")
        
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_db(self) -> List[Dict[str, Any]]:
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_db(self, data: List[Dict[str, Any]]):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_documents(self, chunks: List[str], metadata_list: List[Dict[str, Any]]) -> bool:
        db_data = self._read_db()
        gateway = LlmGatewayClient()
        for chunk, meta in zip(chunks, metadata_list):
            embedding = gateway.embed_text(chunk)
            record = {
                "chunk_id": str(uuid.uuid4()),
                "content": chunk,
                "metadata": meta,
                "vector": embedding
            }
            db_data.append(record)
        self._write_db(db_data)
        return True

    def search(self, query_vector: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        db_data = self._read_db()
        results = []
        for record in db_data:
            # 카테고리 필터 매칭
            if filters and "category_mid" in filters:
                if record["metadata"].get("category_mid") != filters["category_mid"]:
                    continue
            
            # 검색 결과 구성 (유사도 계산)
            sim = LlmGatewayClient.cosine_similarity(query_vector, record["vector"])
            res = {
                "chunk_id": record["chunk_id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "similarity_score": sim
            }
            results.append(res)
        
        # 유사도 순 정렬
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

class VectorDbRouter:
    @staticmethod
    def get_adapter(category_mid: str = None, vector_db_id: str = None) -> LocalJsonVectorDbAdapter:
        # vector_db_id가 1순위, 없으면 category_mid 기반 2순위 할당
        target_db_id = vector_db_id
        if not target_db_id:
            target_db_id = f"vdb_{category_mid}_01" if category_mid else "vdb_default_01"
            
        return LocalJsonVectorDbAdapter(collection_name=target_db_id)
