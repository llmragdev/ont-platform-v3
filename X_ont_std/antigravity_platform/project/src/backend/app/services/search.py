from typing import List, Dict, Any, Optional
from app.models.identity import UserIdentity
from app.repositories.documents import DocumentRepository

class SearchResult(Dict):
    """검색 결과 객체 표준화"""
    doc_id: str
    filename: str
    score: float
    text_snippet: str
    metadata: Dict[str, Any]

class SearchService:
    """테넌트 격리가 보장된 하이브리드 검색 서비스 (RAG의 핵심)"""

    def __init__(self, identity: UserIdentity):
        self.identity = identity
        self.doc_repo = DocumentRepository(identity.company_id, identity.current_project_id)

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        문서 검색 실행. 
        현재는 기초 단계로 레지스트리 내 파일명/메타데이터 검색을 수행하며,
        향후 BM25 및 Vector Search 엔진이 이곳에 플러그인됨.
        """
        all_docs = self.doc_repo.list_documents()
        
        # 기초적인 키워드 필터링 (임시)
        results = []
        for doc in all_docs:
            if query.lower() in doc["filename"].lower():
                results.append({
                    "doc_id": doc["id"],
                    "filename": doc["filename"],
                    "score": 1.0,
                    "text_snippet": f"Found in filename: {doc['filename']}",
                    "metadata": {"status": doc["status"]}
                })
        
        return results[:top_k]

    async def get_document_context(self, doc_id: str) -> Optional[str]:
        """특정 문서의 텍스트 컨텍스트 추출 (LLM 전달용)"""
        doc = self.doc_repo.get_document(doc_id)
        if not doc:
            return None
            
        # 실제 구현 시에는 physical_path에서 텍스트를 읽어와야 함
        # 현재는 placeholder 반환
        return f"Full text content of {doc['filename']} would be loaded here."
