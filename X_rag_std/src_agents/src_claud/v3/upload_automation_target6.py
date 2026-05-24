#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Lab target_doc 6개 NLP PDF 업로드 전용 통합테스트.

전제:
- 벡터화/검색 검증은 사전 준비 또는 별도 단계로 수행한다.
- 이 스크립트는 v3 RAG 서버에 6개 파일이 정상 업로드되는지 확인한다.

서버 기동 예:
    cd E:\\ontology_edu\\X_rag_std\\src_agents\\src_claud\\v3
    set VECTOR_DB_ENGINE=local_json
    uvicorn app.main:app --port 8000 --reload

실행:
    python integration_upload_target6.py
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx


TARGET_DOC_DIR = Path(r"E:\ai_lab_SIT\target_doc")
RAG_SERVER_URL = "http://localhost:8000"
TENANT_ID = "company_abc"
ORG_ID = "0200"

TARGET_PATTERNS = [
    "*03]*.pdf",  # NLP - [03] ...
    "*06]*.pdf",  # NLP - [06] ...
    "*07]*.pdf",  # NLP - [07] ...
    "*08]*.pdf",  # NLP - [08] ...
    "*09]*.pdf",  # NLP - [09] ...
    "*온톨로지 기반의 의미 속성*.pdf",
]

UPLOAD_FORM = {
    "project_code": "TECH001",
    "category_mid": "ontology",
    "category_low": "ai_lab_nlp",
    "vector_db_id": "vdb_ontology_01",
}


def resolve_target_files() -> list[Path]:
    files: list[Path] = []
    for pattern in TARGET_PATTERNS:
        matches = sorted(TARGET_DOC_DIR.glob(pattern))
        if not matches:
            print(f"[WARN] 파일 패턴 없음: {pattern}")
            continue
        files.append(matches[0])
    return files


def check_server(client: httpx.Client) -> bool:
    try:
        response = client.get(
            f"{RAG_SERVER_URL}/api/v1/health",
            headers={"X-Tenant-ID": TENANT_ID},
        )
    except Exception as exc:
        print(f"[FAIL] RAG 서버 연결 실패: {exc}")
        return False

    if response.status_code != 200:
        print(f"[FAIL] Health check 실패: {response.status_code}")
        print(response.text[:500])
        return False

    print("[OK] RAG 서버 연결 확인")
    return True


def upload_file(client: httpx.Client, file_path: Path) -> dict:
    with file_path.open("rb") as file:
        response = client.post(
            f"{RAG_SERVER_URL}/api/v1/documents/upload",
            headers={
                "X-Tenant-ID": TENANT_ID,
                "X-Org-ID": ORG_ID,
            },
            files={"file": (file_path.name, file, "application/pdf")},
            data=UPLOAD_FORM,
        )

    try:
        result = response.json()
    except json.JSONDecodeError:
        result = {
            "status": "error",
            "error": response.text,
        }
    result["_http_status"] = response.status_code
    return result


def list_documents(client: httpx.Client) -> list[dict]:
    response = client.get(
        f"{RAG_SERVER_URL}/api/v1/documents",
        headers={"X-Tenant-ID": TENANT_ID},
    )
    if response.status_code != 200:
        print(f"[WARN] 문서 목록 조회 실패: {response.status_code}")
        print(response.text[:500])
        return []
    payload = response.json()
    return payload.get("data", [])


def main() -> None:
    print("=" * 80)
    print("AI Lab target_doc 6개 PDF 업로드 전용 통합테스트")
    print("=" * 80)
    print(f"대상 폴더: {TARGET_DOC_DIR}")
    print(f"RAG 서버: {RAG_SERVER_URL}")
    print(f"Tenant: {TENANT_ID}")
    print(f"Org: {ORG_ID}")
    print(f"Upload form: {UPLOAD_FORM}")

    pdf_files = resolve_target_files()
    if len(pdf_files) != 6:
        print(f"[FAIL] 대상 파일 수가 6개가 아닙니다: {len(pdf_files)}개")
        for file_path in pdf_files:
            print(f"  - {file_path.name}")
        return

    print("\n[대상 파일]")
    for file_path in pdf_files:
        print(f"  - {file_path.name}")

    with httpx.Client(timeout=120) as client:
        if not check_server(client):
            print("\n[TIP] 서버 기동 예:")
            print(r"  cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3")
            print("  set VECTOR_DB_ENGINE=local_json")
            print("  uvicorn app.main:app --port 8000 --reload")
            return

        print("\n[STEP 1] 파일 업로드")
        uploaded_docs: list[dict] = []
        for index, file_path in enumerate(pdf_files, 1):
            print(f"\n[{index}/6] {file_path.name}")
            result = upload_file(client, file_path)
            if result.get("status") == "success":
                data = result.get("data") or {}
                uploaded_docs.append(
                    {
                        "doc_id": data.get("doc_id"),
                        "file_name": data.get("file_name"),
                        "pipeline_status": data.get("pipeline_status"),
                        "assigned_vector_db": data.get("assigned_vector_db"),
                    }
                )
                print(
                    "  [OK] "
                    f"doc_id={data.get('doc_id')} "
                    f"status={data.get('pipeline_status')} "
                    f"vector_db={data.get('assigned_vector_db')}"
                )
            else:
                print(f"  [FAIL] http={result.get('_http_status')}")
                print(json.dumps(result, ensure_ascii=False, indent=2)[:1200])

        print("\n[STEP 2] 문서 목록 확인")
        documents = list_documents(client)
        target_names = {file_path.name for file_path in pdf_files}
        matched = [
            doc for doc in documents
            if doc.get("file_name") in target_names
        ]
        print(f"  전체 저장 문서 수: {len(documents)}")
        print(f"  이번 대상 파일 매칭 수: {len(matched)}/6")
        for doc in matched:
            print(
                "  - "
                f"{doc.get('file_name')} "
                f"status={doc.get('pipeline_status')} "
                f"vector_db={doc.get('assigned_vector_db')}"
            )

    print("\n[SUMMARY]")
    print(f"업로드 성공: {len(uploaded_docs)}/6")
    print("검색/정확도 테스트는 본 스크립트에서 수행하지 않습니다.")
    print("벡터화 준비 후 QA 플랫폼의 team0_local_rag 또는 별도 검색 테스트로 검증하세요.")


if __name__ == "__main__":
    main()
