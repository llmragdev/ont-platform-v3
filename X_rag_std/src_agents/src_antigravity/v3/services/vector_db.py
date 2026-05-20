import os
import json
from typing import List, Dict, Any, Optional
from services.gateway_client import LlmGatewayClient

class BaseVectorDbAdapter:
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        raise NotImplementedError
    
    def search(self, query_vector: List[float], tenant_id: str, org_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def delete_by_doc_id(self, doc_id: str, tenant_id: str):
        raise NotImplementedError

class LocalJsonVectorDbAdapter(BaseVectorDbAdapter):
    def __init__(self, vector_db_id: str):
        self.vector_db_id = vector_db_id
        self.storage_path = f"storage/{vector_db_id}.json"
        os.makedirs("storage", exist_ok=True)
        self.gateway = LlmGatewayClient()

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        data = self._load_data()
        
        for text, meta in zip(texts, metadatas):
            embedding = self.gateway.embed_text(text, tenant_id=meta.get("tenant_id", "default"))
            data.append({
                "content": text,
                "metadata": meta,
                "embedding": embedding
            })
            
        self._save_data(data)

    def search(self, query_vector: List[float], tenant_id: str, org_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        data = self._load_data()
        results = []
        
        # dept_code 추출 (부서 단위 검색용)
        dept_code = org_id[:2] if org_id and len(org_id) >= 2 else None

        for item in data:
            meta = item["metadata"]
            
            # 1. 테넌트 격리 (필수)
            if meta.get("tenant_id") != tenant_id:
                continue
                
            # 2. 계층 검색 정책 (OR 로직) 반영 v1.3
            # (org_id 일치) OR (org_id가 None인 전사 공유 문서)
            # 혹은 부서 검색일 경우 (dept_code 일치) OR (org_id가 None)
            
            match = False
            if not org_id:
                # 전사 검색
                match = True
            elif org_id.endswith("00"):
                # 부서 검색 (예: 0100)
                if meta.get("dept_code") == dept_code or meta.get("org_id") is None:
                    match = True
            else:
                # 팀 검색 (예: 0102)
                if meta.get("org_id") == org_id or meta.get("org_id") is None:
                    match = True
            
            if not match:
                continue

            score = self.gateway.cosine_similarity(query_vector, item["embedding"])
            results.append({
                "content": item["content"],
                "metadata": meta,
                "score": score
            })
            
        # 점수 순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_by_doc_id(self, doc_id: str, tenant_id: str):
        data = self._load_data()
        # 해당 doc_id와 tenant_id가 일치하는 청크 제외
        new_data = [
            item for item in data 
            if not (item["metadata"].get("doc_id") == doc_id and item["metadata"].get("tenant_id") == tenant_id)
        ]
        if len(new_data) < len(data):
            self._save_data(new_data)
            return True
        return False

    def _load_data(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_data(self, data: List[Dict[str, Any]]):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

class VectorDbRouter:
    @staticmethod
    def get_adapter(vector_db_id: str = None) -> BaseVectorDbAdapter:
        # 실무에서는 routing.json 기반으로 인스턴스화
        db_id = vector_db_id or "vdb_default_01"
        return LocalJsonVectorDbAdapter(db_id)
