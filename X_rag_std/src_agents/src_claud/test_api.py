"""
실서버 통합 테스트 — 실제 HTTP 호출 (RESTful API)

사전 조건: 서버가 기동되어 있어야 함
  v1: uvicorn app.main:app --port 8000  (v1/ 폴더에서)
  v2: LLM Gateway + RAG 서버 기동 후 (v2/README.md 참조)

실행:
  pytest test_api.py -v
  pytest test_api.py -v -s              # 응답 시간 출력
  BASE_URL=http://192.168.0.10:8000 pytest test_api.py -v
"""
import os
import time
from pathlib import Path

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
COMPANY_ID = "test_company"
HEADERS = {"X-Company-ID": COMPANY_ID}

SAMPLE_TEXT = "RAG 테스트 문서입니다. 온톨로지 교육 시스템에서 학습 방법을 안내합니다.".encode("utf-8")

PDF_PATH = Path(
    r"E:\ontology_edu\X_rag_std\_backup\pre-work\std_boot_src_2026"
    r"\ai_std_dev\data\01_raw\2025년 AI바우처 사업설명회 발표자료.pdf"
)


# ── 서버 기동 여부 확인 ──────────────────────────────────────────
def _server_running() -> bool:
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


skip_if_down = pytest.mark.skipif(
    not _server_running(),
    reason=f"서버 미기동 — {BASE_URL} 에 서버를 먼저 실행하세요",
)

skip_if_no_pdf = pytest.mark.skipif(
    not PDF_PATH.exists(),
    reason=f"PDF 파일 없음 — {PDF_PATH}",
)


# ── 헬퍼 ────────────────────────────────────────────────────────
def _elapsed(start: float) -> str:
    return f"{(time.time() - start) * 1000:.0f}ms"


# ── 헬스 체크 ──────────────────────────────────────────────────
@skip_if_down
def test_health():
    t = time.time()
    r = httpx.get(f"{BASE_URL}/api/v1/health", headers=HEADERS)
    print(f"\n  [health] {_elapsed(t)}")
    assert r.status_code == 200
    assert r.json()["status"] in ("ok", "degraded")


# ── 문서 기본 테스트 ────────────────────────────────────────────
@skip_if_down
def test_upload_and_pipeline(tmp_path):
    doc_file = tmp_path / "sample.txt"
    doc_file.write_bytes(SAMPLE_TEXT)

    t = time.time()
    with open(doc_file, "rb") as f:
        r = httpx.post(
            f"{BASE_URL}/api/v1/documents/upload",
            headers=HEADERS,
            files={"file": ("sample.txt", f, "text/plain")},
            data={"category_mid": "ontology"},
            timeout=30.0,
        )
    print(f"\n  [upload] {_elapsed(t)}")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    assert body["data"]["pipeline_status"] == "completed"
    assert body["data"]["doc_id"]

    return body["data"]["doc_id"]


@skip_if_down
def test_list_documents():
    t = time.time()
    r = httpx.get(f"{BASE_URL}/api/v1/documents", headers=HEADERS, timeout=10.0)
    print(f"\n  [list] {_elapsed(t)}")
    assert r.status_code == 200
    assert r.json()["status"] == "success"


@skip_if_down
def test_upload_search_delete(tmp_path):
    # 1. 업로드
    doc_file = tmp_path / "rag_test.txt"
    doc_file.write_text("온톨로지 교육 시스템의 학습 방법을 안내합니다.", encoding="utf-8")

    with open(doc_file, "rb") as f:
        up = httpx.post(
            f"{BASE_URL}/api/v1/documents/upload",
            headers=HEADERS,
            files={"file": ("rag_test.txt", f, "text/plain")},
            data={"category_mid": "ontology"},
            timeout=30.0,
        )
    assert up.status_code == 200, up.text
    doc_id = up.json()["data"]["doc_id"]
    print(f"\n  [upload] doc_id={doc_id}")

    # 2. 검색
    t = time.time()
    sr = httpx.post(
        f"{BASE_URL}/api/v1/rag/search",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"query": "학습 방법", "top_k": 3, "debug_mode": True},
        timeout=30.0,
    )
    print(f"  [search] {_elapsed(t)}")
    assert sr.status_code == 200, sr.text
    body = sr.json()
    assert body["status"] == "success"
    assert body["data"]["answer"]

    # 3. 삭제
    t = time.time()
    dr = httpx.delete(
        f"{BASE_URL}/api/v1/documents/{doc_id}",
        headers=HEADERS,
        timeout=10.0,
    )
    print(f"  [delete] {_elapsed(t)}")
    assert dr.status_code == 200
    assert dr.json()["data"]["deleted"] is True


@skip_if_down
def test_search_response_time():
    """응답 시간 기준선 측정 — 500ms 이내."""
    t = time.time()
    r = httpx.post(
        f"{BASE_URL}/api/v1/rag/search",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"query": "테스트", "top_k": 3},
        timeout=10.0,
    )
    elapsed = (time.time() - t) * 1000
    print(f"\n  [search latency] {elapsed:.0f}ms")
    assert r.status_code == 200
    assert elapsed < 500, f"응답 시간 초과: {elapsed:.0f}ms"


# ── 프로젝트 관리 테스트 ────────────────────────────────────────
@skip_if_down
def test_project_lifecycle(tmp_path):
    """프로젝트 생성 → 문서 업로드 → 검색 → 프로젝트 삭제(cascade)."""
    # 1. 프로젝트 생성
    t = time.time()
    pr = httpx.post(
        f"{BASE_URL}/api/v1/projects",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"project_name": "테스트 프로젝트", "vector_db_id": "vdb_test_01"},
        timeout=10.0,
    )
    print(f"\n  [create project] {_elapsed(t)}")
    assert pr.status_code == 201, pr.text
    project_code = pr.json()["data"]["project_code"]
    print(f"  project_code={project_code}")

    # 2. 프로젝트에 문서 업로드
    doc_file = tmp_path / "project_doc.txt"
    doc_file.write_text("AI 바우처 사업은 중소기업 AI 도입을 지원합니다.", encoding="utf-8")

    with open(doc_file, "rb") as f:
        up = httpx.post(
            f"{BASE_URL}/api/v1/documents/upload",
            headers=HEADERS,
            files={"file": ("project_doc.txt", f, "text/plain")},
            data={"category_mid": "ontology", "project_code": project_code},
            timeout=30.0,
        )
    assert up.status_code == 200, up.text
    doc_id = up.json()["data"]["doc_id"]
    print(f"  [upload to project] doc_id={doc_id}")

    # 3. 프로젝트 조회
    get_r = httpx.get(f"{BASE_URL}/api/v1/projects/{project_code}", headers=HEADERS)
    assert get_r.status_code == 200
    assert get_r.json()["data"]["project_code"] == project_code

    # 4. 프로젝트 목록 확인
    list_r = httpx.get(f"{BASE_URL}/api/v1/projects", headers=HEADERS)
    assert list_r.status_code == 200
    codes = [p["project_code"] for p in list_r.json()["data"]]
    assert project_code in codes

    # 5. 프로젝트 삭제 (문서 cascade 포함)
    t = time.time()
    dr = httpx.delete(f"{BASE_URL}/api/v1/projects/{project_code}", headers=HEADERS, timeout=15.0)
    print(f"  [delete project] {_elapsed(t)}")
    assert dr.status_code == 200
    assert dr.json()["data"]["deleted"] is True

    # 6. 문서도 삭제됐는지 확인
    doc_r = httpx.delete(f"{BASE_URL}/api/v1/documents/{doc_id}", headers=HEADERS)
    assert doc_r.status_code == 404, "프로젝트 삭제 시 문서도 함께 삭제되어야 함"


# ── 카테고리 관리 테스트 ────────────────────────────────────────
@skip_if_down
def test_category_lifecycle():
    """카테고리 생성 → 목록 조회 → 삭제."""
    # 1. 생성
    cr = httpx.post(
        f"{BASE_URL}/api/v1/categories",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"category_mid": "AI바우처", "vector_db_id": "vdb_ai_01"},
        timeout=10.0,
    )
    assert cr.status_code == 201, cr.text
    cat_id = cr.json()["data"]["category_id"]
    print(f"\n  [create category] category_id={cat_id}")

    # 2. 목록 조회
    lr = httpx.get(f"{BASE_URL}/api/v1/categories", headers=HEADERS)
    assert lr.status_code == 200
    ids = [c["category_id"] for c in lr.json()["data"]]
    assert cat_id in ids

    # 3. 삭제
    dr = httpx.delete(f"{BASE_URL}/api/v1/categories/{cat_id}", headers=HEADERS)
    assert dr.status_code == 200
    assert dr.json()["data"]["deleted"] is True


# ── PDF 업로드 테스트 ───────────────────────────────────────────
@skip_if_down
@skip_if_no_pdf
def test_pdf_upload_search_delete():
    """실제 PDF 파일(AI바우처 발표자료) 업로드 → 검색 → 삭제."""
    # 1. PDF 업로드
    t = time.time()
    with open(PDF_PATH, "rb") as f:
        up = httpx.post(
            f"{BASE_URL}/api/v1/documents/upload",
            headers=HEADERS,
            files={"file": (PDF_PATH.name, f, "application/pdf")},
            data={"category_mid": "AI바우처"},
            timeout=120.0,
        )
    print(f"\n  [PDF upload] {_elapsed(t)}")
    assert up.status_code == 200, up.text
    body = up.json()
    assert body["status"] == "success"
    doc_id = body["data"]["doc_id"]
    print(f"  doc_id={doc_id}, status={body['data']['pipeline_status']}")

    # 2. 검색
    t = time.time()
    sr = httpx.post(
        f"{BASE_URL}/api/v1/rag/search",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"query": "AI 바우처 지원 대상", "top_k": 5, "debug_mode": True},
        timeout=60.0,
    )
    print(f"  [PDF search] {_elapsed(t)}")
    assert sr.status_code == 200, sr.text
    result = sr.json()
    assert result["status"] == "success"
    print(f"  answer preview: {result['data']['answer'][:200]}")
    if result["data"].get("debug_info"):
        chunks = result["data"]["debug_info"]["candidate_chunks"]
        print(f"  retrieved {len(chunks)} chunks")

    # 3. 삭제
    dr = httpx.delete(f"{BASE_URL}/api/v1/documents/{doc_id}", headers=HEADERS, timeout=10.0)
    assert dr.status_code == 200
    assert dr.json()["data"]["deleted"] is True
    print(f"  [PDF delete] done")
