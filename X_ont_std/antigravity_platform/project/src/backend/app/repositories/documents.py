import json
from typing import List, Dict, Any, Optional
from app.repositories.base import BaseRepository

class DocumentRepository(BaseRepository):
    """테넌트별 문서 메타데이터(Registry)를 관리하는 저장소"""

    REGISTRY_FILE = "documents_registry.json"

    def list_documents(self) -> List[Dict[str, Any]]:
        """테넌트 내 문서 목록 조회"""
        return self._load_json(self.REGISTRY_FILE)

    def register_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 문서를 레지스트리에 등록"""
        registry = self._load_json(self.REGISTRY_FILE)
        
        # 중복 체크 (파일명 기반 등, 필요 시 추가)
        
        registry.append(doc_data)
        self._save_json(self.REGISTRY_FILE, registry)
        return doc_data

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        registry = self._load_json(self.REGISTRY_FILE)
        for doc in registry:
            if doc["id"] == doc_id:
                return doc
        return None

    def delete_document(self, doc_id: str):
        """레지스트리에서 문서 제거 (물리 파일 삭제는 서비스에서 담당)"""
        registry = self._load_json(self.REGISTRY_FILE)
        registry = [doc for doc in registry if doc["id"] != doc_id]
        self._save_json(self.REGISTRY_FILE, registry)
