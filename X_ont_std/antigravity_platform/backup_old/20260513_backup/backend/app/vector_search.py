import os
import shutil
from pathlib import Path
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 저장 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
CHROMA_DIR = BASE_DIR / "vector_db"

UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

class VectorSearchService:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # Fallback for evaluation environment
            api_key = os.environ.get("GEMINI_API_KEY1")
            
        if not api_key:
            # key가 없어도 초기화는 되도록 처리 (런타임 에러 방지)
            self.embeddings = None
            self.vector_store = None
            return
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        self.vector_store = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=self.embeddings,
            collection_name="antigravity_docs"
        )

    def ingest(self, file_path: Path, filename: str) -> dict:
        """PDF 파일을 로드하여 벡터 DB에 저장."""
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(pages)
        
        # 메타데이터 보강
        for i, chunk in enumerate(chunks):
            chunk.metadata["filename"] = filename
            chunk.metadata["doc_id"] = filename  # 간단하게 파일명을 ID로 사용
            chunk.metadata["page"] = chunk.metadata.get("page", 0)

        self.vector_store.add_documents(chunks)
        
        return {
            "filename": filename,
            "chunk_count": len(chunks),
            "page_count": len(pages)
        }

    def search(self, query: str, k: int = 4, doc_ids: Optional[List[str]] = None) -> List[dict]:
        """관련 청크 검색."""
        filter_dict = None
        if doc_ids:
            filter_dict = {"doc_id": {"$in": doc_ids}}
            
        results = self.vector_store.similarity_search_with_relevance_scores(
            query, k=k, filter=filter_dict
        )
        
        return [
            {
                "text": doc.page_content,
                "score": score,
                "filename": doc.metadata.get("filename"),
                "page": doc.metadata.get("page"),
                "doc_id": doc.metadata.get("doc_id")
            }
            for doc, score in results
        ]

    def list_documents(self) -> List[dict]:
        """업로드된 문서 목록 반환 (중복 제거)."""
        data = self.vector_store.get()
        metadatas = data.get("metadatas", [])
        
        docs = {}
        for meta in metadatas:
            doc_id = meta.get("doc_id")
            if doc_id and doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta.get("filename"),
                }
        return list(docs.values())

    def delete(self, doc_id: str) -> bool:
        """문서 삭제."""
        try:
            self.vector_store.delete(where={"doc_id": doc_id})
            # 파일도 삭제
            for f in UPLOAD_DIR.glob(f"{doc_id}*"):
                f.unlink()
            return True
        except Exception:
            return False

    def health(self) -> dict:
        try:
            count = self.vector_store._collection.count()
            return {"status": "ok", "total_chunks": count}
        except Exception as e:
            return {"status": "error", "message": str(e)}
