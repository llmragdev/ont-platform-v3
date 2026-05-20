import json
import sys

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def assert_success(response, label: str) -> dict:
    if response.status_code != 200:
        print(f"[FAIL] {label}: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)
    body = response.json()
    if body.get("status") != "success":
        print(f"[FAIL] {label}: status={body.get('status')}")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        sys.exit(1)
    print(f"[PASS] {label}")
    return body


def print_json(title: str, body: dict) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print(json.dumps(body, indent=2, ensure_ascii=False))


def test_health() -> None:
    response = client.get("/api/v1/health")
    body = assert_success(response, "health")
    print_json("1. Health Check", body)


def upload_document_smoke() -> str:
    content = (
        "2026년도 인사 규정 테스트 문서입니다. "
        "휴가 규정은 연 15일이며, 재택근무 지침은 부서장 승인 후 적용됩니다."
    ).encode("utf-8")
    files = {"file": ("2026_hr_policy.txt", content, "text/plain")}
    data = {
        "category_mid": "policy",
        "category_low": "hr",
    }
    response = client.post("/api/v1/documents/upload", files=files, data=data)
    body = assert_success(response, "document upload")
    data_body = body["data"]
    if data_body["pipeline_status"] != "completed":
        print(f"[FAIL] expected completed, got {data_body['pipeline_status']}")
        sys.exit(1)
    if data_body["assigned_vector_db"] != "vdb_policy_01":
        print(f"[FAIL] expected vdb_policy_01, got {data_body['assigned_vector_db']}")
        sys.exit(1)
    print_json("2. Document Upload", body)
    return data_body["doc_id"]


def check_document_list(doc_id: str) -> None:
    response = client.get("/api/v1/documents")
    body = assert_success(response, "document list")
    doc_ids = {item["doc_id"] for item in body["data"]}
    if doc_id not in doc_ids:
        print(f"[FAIL] uploaded doc_id not found in list: {doc_id}")
        sys.exit(1)
    print_json("3. Document List", body)


def test_document_upload() -> None:
    upload_document_smoke()


def test_document_list() -> None:
    doc_id = upload_document_smoke()
    check_document_list(doc_id)


def test_rag_search_normal() -> None:
    payload = {
        "query": "휴가 규정과 재택근무 지침을 알려줘",
        "top_k": 3,
        "debug_mode": False,
        "filters": {
            "category_mid": "policy",
        },
    }
    response = client.post("/api/v1/rag/search", json=payload)
    body = assert_success(response, "rag search normal")
    data_body = body["data"]
    if not data_body["used_chunks"]:
        print("[FAIL] expected used_chunks to be non-empty")
        sys.exit(1)
    if data_body["debug_info"] is not None:
        print("[FAIL] debug_info must be null when debug_mode=false")
        sys.exit(1)
    print_json("4. RAG Search - Normal Mode", body)


def test_rag_search_debug() -> None:
    payload = {
        "query": "휴가 규정과 재택근무 지침을 알려줘",
        "top_k": 3,
        "debug_mode": True,
        "filters": {
            "category_mid": "policy",
        },
    }
    response = client.post("/api/v1/rag/search", json=payload)
    body = assert_success(response, "rag search debug")
    data_body = body["data"]
    debug_info = data_body["debug_info"]
    if debug_info is None:
        print("[FAIL] debug_info must be present when debug_mode=true")
        sys.exit(1)
    if not debug_info["candidate_chunks"]:
        print("[FAIL] expected candidate_chunks to be non-empty")
        sys.exit(1)
    print_json("5. RAG Search - Debug Mode", body)


def run_tests() -> None:
    print("src_codex endpoint smoke tests")
    test_health()
    doc_id = upload_document_smoke()
    check_document_list(doc_id)
    test_rag_search_normal()
    test_rag_search_debug()
    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    run_tests()
