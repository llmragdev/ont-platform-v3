import json
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from main import app


PDF_PATH = Path(
    r"E:\ontology_edu\ont_platform\docs\ref_data\01_raw\2025년 AI바우처 사업설명회 발표자료.pdf"
)

client = TestClient(app)
TEST_VECTOR_DB_ID = f"vdb_ai_voucher_test_{uuid.uuid4().hex[:8]}"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def assert_success(response, label: str) -> dict:
    if response.status_code != 200:
        print(response.text)
        fail(f"{label}: HTTP {response.status_code}")
    body = response.json()
    if body.get("status") != "success":
        print(json.dumps(body, indent=2, ensure_ascii=False))
        fail(f"{label}: status={body.get('status')}")
    print(f"[PASS] {label}")
    return body


def print_summary(title: str, body: dict) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print(json.dumps(body, indent=2, ensure_ascii=False)[:4000])


def upload_pdf() -> str:
    if not PDF_PATH.exists():
        fail(f"PDF not found: {PDF_PATH}")

    with PDF_PATH.open("rb") as file_obj:
        files = {
            "file": (
                PDF_PATH.name,
                file_obj,
                "application/pdf",
            )
        }
        data = {
            "category_mid": "policy",
            "category_low": "ai_voucher_2025",
            "vector_db_id": TEST_VECTOR_DB_ID,
        }
        response = client.post("/api/v1/documents/upload", files=files, data=data)

    body = assert_success(response, "AI voucher PDF upload")
    data_body = body["data"]
    if data_body["pipeline_status"] != "completed":
        fail(f"expected completed, got {data_body['pipeline_status']}")
    if data_body["assigned_vector_db"] != TEST_VECTOR_DB_ID:
        fail(f"expected {TEST_VECTOR_DB_ID}, got {data_body['assigned_vector_db']}")
    print_summary("1. AI Voucher PDF Upload", body)
    return data_body["doc_id"]


def search_pdf(question: str, debug_mode: bool) -> dict:
    payload = {
        "query": question,
        "top_k": 5,
        "debug_mode": debug_mode,
        "filters": {
            "category_mid": "policy",
            "vector_db_id": TEST_VECTOR_DB_ID,
        },
    }
    response = client.post("/api/v1/rag/search", json=payload)
    body = assert_success(response, f"AI voucher search debug={debug_mode}")
    data_body = body["data"]
    if not data_body["used_chunks"]:
        fail("expected used_chunks to be non-empty")
    if debug_mode and not data_body["debug_info"]:
        fail("debug_info must be present when debug_mode=true")
    if not debug_mode and data_body["debug_info"] is not None:
        fail("debug_info must be null when debug_mode=false")
    return body


def assert_pdf_source(body: dict, doc_id: str) -> None:
    used_chunks = body["data"]["used_chunks"]
    if not any(chunk["metadata"].get("doc_id") == doc_id for chunk in used_chunks):
        fail(f"expected at least one used chunk from uploaded PDF doc_id={doc_id}")
    if not any(PDF_PATH.name in chunk["metadata"].get("source_name", "") for chunk in used_chunks):
        fail("expected source_name to reference the AI voucher PDF")


def run_tests() -> None:
    print("src_codex AI voucher PDF integration test")
    doc_id = upload_pdf()

    normal = search_pdf("2025년 AI바우처 사업의 예산과 과제 수를 알려줘", debug_mode=False)
    assert_pdf_source(normal, doc_id)
    print_summary("2. AI Voucher Search - Normal Mode", normal)

    debug = search_pdf("공급기업 Pool 신규 등록 절차를 설명해줘", debug_mode=True)
    assert_pdf_source(debug, doc_id)
    candidates = debug["data"]["debug_info"]["candidate_chunks"]
    if not candidates:
        fail("expected candidate_chunks to be non-empty")
    print_summary("3. AI Voucher Search - Debug Mode", debug)

    print("\nAI VOUCHER PDF TESTS PASSED")


if __name__ == "__main__":
    run_tests()
