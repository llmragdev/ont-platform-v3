import os
import io
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document
from sqlalchemy.orm import Session
from fastapi import UploadFile
from repositories.doc_repo import DocRepository
from services.vector_db import VectorDbRouter

class DocumentPipelineService:
    def __init__(self, db: Session):
        self.doc_repo = DocRepository(db)

    def process_upload(self, tenant_id: str, project_code: str, file: UploadFile, org_id: str = None):
        """
        RAG 파이프라인 실행: 저장 -> 실제 파싱 -> 표준 청킹 -> VectorDB 적재
        """
        # 1. RDBMS에 상태 pending으로 등록
        doc_record = self.doc_repo.create_doc(
            tenant_id=tenant_id,
            project_code=project_code,
            file_name=file.filename,
            org_id=org_id
        )
        
        doc_id = doc_record.doc_id
        self.doc_repo.update_status(doc_id, "processing")
        
        try:
            # 2. 파일 읽기 및 실제 텍스트 추출 (pypdf / python-docx)
            content = file.file.read()
            text_by_page = self._extract_text(file.filename, content)
            
            if not text_by_page:
                raise ValueError(f"Failed to extract text from {file.filename}")
                
            # 3. 표준 청킹 (700자 크기, 80자 중첩)
            chunks, metadata_list = self._create_standard_chunks(
                text_by_page, 
                doc_record
            )
                
            # 4. Vector DB에 적재
            adapter = VectorDbRouter.get_adapter(vector_db_id=doc_record.assigned_vector_db)
            adapter.add_documents(chunks, metadata_list)
            
            # 5. RDBMS 상태 업데이트 (완료)
            self.doc_repo.update_status(doc_id, "completed")
            
        except Exception as e:
            # 임베딩 fallback[0.1, 0.2] 금지 및 예외 기록
            self.doc_repo.update_status(doc_id, "error", error_message=str(e))
            raise e
            
        return doc_record

    def _extract_text(self, filename: str, content: bytes) -> List[Dict[str, Any]]:
        """페이지별 텍스트와 메타데이터 추출"""
        results = []
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".pdf":
            reader = PdfReader(io.BytesIO(content))
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    results.append({"page_no": i + 1, "text": text})
        elif ext == ".docx":
            doc = Document(io.BytesIO(content))
            full_text = "\n".join([para.text for para in doc.paragraphs])
            # Docx는 페이지 구분이 어려우므로 단일 페이지로 처리
            results.append({"page_no": 1, "text": full_text})
        else:
            # 텍스트 파일 등 기본 처리
            try:
                text = content.decode('utf-8')
                results.append({"page_no": 1, "text": text})
            except:
                results.append({"page_no": 1, "text": "Unreadable file format"})
                
        return results

    def _create_standard_chunks(self, text_by_page: List[Dict[str, Any]], doc_record: Any):
        """표준 설계 v1.3에 따른 청킹 및 메타데이터 생성"""
        chunk_size = 700
        chunk_overlap = 80
        
        final_chunks = []
        final_metadata = []
        
        for page in text_by_page:
            text = page["text"]
            page_no = page["page_no"]
            
            # 단순 슬라이딩 윈도우 기반 청킹 (RecursiveCharacterTextSplitter와 유사한 기초 구현)
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk = text[start:end]
                
                if chunk.strip():
                    final_chunks.append(chunk)
                    
                    # 표준 메타데이터 v1.3 준수
                    meta = {
                        "doc_id": doc_record.doc_id,
                        "tenant_id": doc_record.tenant_id,
                        "org_id": doc_record.org_id,
                        "dept_code": doc_record.dept_code,
                        "vector_db_id": doc_record.assigned_vector_db,
                        "source_name": doc_record.file_name,
                        "page_no": page_no,
                        "created_at": doc_record.created_at.isoformat()
                    }
                    final_metadata.append(meta)
                
                start += (chunk_size - chunk_overlap)
                if end >= len(text):
                    break
                    
        return final_chunks, final_metadata
