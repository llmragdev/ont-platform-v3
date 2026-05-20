import os
import shutil
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from app.models.identity import UserIdentity
from app.repositories.documents import DocumentRepository
from app.services.audit import AuditService
from storage_config import storage_config

class DocumentService:
    """실제 파일 저장 및 레지스트리 관리 (보안 강화 버전)"""

    ALLOWED_EXTENSIONS = {".pdf", ".json", ".txt", ".csv"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, identity: UserIdentity):
        self.identity = identity
        self.repo = DocumentRepository(identity.company_id, identity.current_project_id)
        self.audit = AuditService(identity)

    async def upload_document(self, file: UploadFile) -> Dict[str, Any]:
        """파일 검증 및 경로 탈출 방지가 적용된 업로드"""
        
        # 1. 파일 검증 (확장자 및 크기)
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        
        # Note: file.size is available in newer FastAPI/Starlette, fallback to seek if needed
        if file.size > self.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        doc_id = str(uuid4())
        
        # 2. 경로 탈출 방지 (os.path.basename 사용)
        safe_filename = os.path.basename(file.filename)
        upload_dir = storage_config.get_sub_dir(
            self.identity.company_id, 
            self.identity.current_project_id, 
            "uploads"
        )
        file_path = upload_dir / f"{doc_id}_{safe_filename}"
        
        # 3. 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 4. 메타데이터 생성
        doc_metadata = {
            "id": doc_id,
            "filename": safe_filename,
            "physical_path": str(file_path),
            "size_bytes": file.size,
            "status": "uploaded",
            "company_id": self.identity.company_id,
            "project_id": self.identity.current_project_id,
            "uploaded_by": self.identity.user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 5. 레지스트리 등록 및 로그
        self.repo.register_document(doc_metadata)
        self.audit.log_action("UPLOAD_DOCUMENT", doc_id, {"filename": safe_filename})
        
        return doc_metadata

    def delete_document(self, doc_id: str):
        """레지스트리와 물리 파일 동시 삭제"""
        doc = self.repo.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # 1. 물리 파일 삭제
        p_path = Path(doc["physical_path"])
        if p_path.exists():
            p_path.unlink()
            
        # 2. 레지스트리 제거
        self.repo.delete_document(doc_id)
        
        # 3. 로그 기록
        self.audit.log_action("DELETE_DOCUMENT", doc_id, {"filename": doc["filename"]})

    def get_all_documents(self) -> List[Dict[str, Any]]:
        return self.repo.list_documents()
