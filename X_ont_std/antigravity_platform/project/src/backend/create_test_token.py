import sys
import os

# 현재 경로를 Python path에 추가하여 app 모듈을 불러올 수 있게 함
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.security import create_access_token

def generate_test_tokens():
    # 1. ACME 회사의 관리자 Alice (모든 권한)
    alice_data = {
        "sub": "user-001",
        "name": "Alice Admin",
        "company_id": "acme",
        "project_id": "proj-001",
        "role": "admin",
        "permissions": {
            "can_read": True,
            "can_edit_ontology": True,
            "can_upload_docs": True,
            "can_delete_docs": True,
            "can_manage_users": True
        },
        "project_ids": ["proj-001", "proj-002"]
    }
    alice_token = create_access_token(alice_data)

    # 2. Globex 회사의 뷰어 Bob (읽기 전용)
    bob_data = {
        "sub": "user-002",
        "name": "Bob Viewer",
        "company_id": "globex",
        "project_id": "proj-999",
        "role": "viewer",
        "permissions": {
            "can_read": True,
            "can_edit_ontology": False,
            "can_upload_docs": False
        },
        "project_ids": ["proj-999"]
    }
    bob_token = create_access_token(bob_data)

    print("-" * 50)
    print("TEST TOKENS GENERATED")
    print("-" * 50)
    print(f"ALICE (ACME Admin):\n{alice_token}\n")
    print(f"BOB (Globex Viewer):\n{bob_token}")
    print("-" * 50)
    print("Usage: curl -H 'Authorization: Bearer <TOKEN>' http://localhost:8000/api/v1/tenant/me")

if __name__ == "__main__":
    generate_test_tokens()
