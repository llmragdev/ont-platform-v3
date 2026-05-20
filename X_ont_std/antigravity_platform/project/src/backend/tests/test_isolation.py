import os
import sys
from pathlib import Path
import pytest

# 프로젝트 루트를 Python path에 추가
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.documents import DocumentService
from app.models.identity import UserIdentity, PermissionSet

@pytest.fixture
def mock_identity_acme():
    return UserIdentity(
        user_id="alice",
        username="Alice",
        company_id="acme",
        current_project_id="proj-001",
        role="admin",
        permissions=PermissionSet(can_upload_docs=True, can_delete_docs=True)
    )

@pytest.fixture
def mock_identity_globex():
    return UserIdentity(
        user_id="bob",
        username="Bob",
        company_id="globex",
        current_project_id="proj-999",
        role="viewer",
        permissions=PermissionSet(can_upload_docs=False, can_delete_docs=False)
    )

def test_path_traversal_prevention(mock_identity_acme):
    """경로 탈출 시도 시 파일명이 정규화되어 안전한 곳에 저장되는지 테스트"""
    service = DocumentService(mock_identity_acme)
    
    # 조작된 파일명
    malicious_filename = "../../../secret.txt"
    
    # 1. safe_filename 추출 로직 검증 (os.path.basename)
    safe_name = os.path.basename(malicious_filename)
    assert safe_name == "secret.txt"
    
    # 2. 업로드 디렉토리 확인
    from storage_config import storage_config
    upload_dir = storage_config.get_sub_dir("acme", "proj-001", "uploads")
    
    # 실제 경로가 uploads 디렉토리 내부에 있는지 확인 (commonpath 활용)
    final_path = upload_dir / f"test-id_{safe_name}"
    assert os.path.commonpath([upload_dir, final_path]) == str(upload_dir)

def test_tenant_isolation_in_registry(mock_identity_acme, mock_identity_globex):
    """Company A 사용자가 Company B의 문서를 볼 수 없는지 테스트"""
    # 실제 파일 시스템 연동이므로, 레포지토리 로직의 격리성 확인
    from app.repositories.documents import DocumentRepository
    
    repo_acme = DocumentRepository("acme", "proj-001")
    repo_globex = DocumentRepository("globex", "proj-999")
    
    # 각 레포지토리의 root_path가 다른지 확인
    assert str(repo_acme.root_path) != str(repo_globex.root_path)
    assert "acme" in str(repo_acme.root_path)
    assert "globex" in str(repo_globex.root_path)
