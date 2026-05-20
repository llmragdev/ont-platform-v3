from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.api.deps import get_current_identity, PermissionChecker
from app.models.identity import UserIdentity
from app.services.documents import DocumentService
from app.services.search import SearchService

router = APIRouter()

@router.get("")
async def list_documents(
    identity: UserIdentity = Depends(get_current_identity)
):
    service = DocumentService(identity)
    return service.get_all_documents()

@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    identity: UserIdentity = Depends(PermissionChecker("can_upload_docs"))
):
    service = DocumentService(identity)
    return await service.upload_document(file)

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    identity: UserIdentity = Depends(PermissionChecker("can_delete_docs"))
):
    """문서 삭제 (권한 필요)"""
    service = DocumentService(identity)
    service.delete_document(doc_id)
    return {"message": "Document deleted successfully"}

@router.get("/search")
async def search_documents(
    q: str,
    identity: UserIdentity = Depends(get_current_identity)
):
    """문서 검색 서비스 연동"""
    service = SearchService(identity)
    return await service.search(q)
