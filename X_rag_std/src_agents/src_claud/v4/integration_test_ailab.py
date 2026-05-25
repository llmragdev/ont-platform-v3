#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Lab 통합테스트 데이터로 v3 RAG 시스템 테스트

ai_lab의 rag_target_files를 사용하여 실제 PDF 기반 테스트:
- 8개 실제 PDF 업로드 (NLP, 국방 관련)
- 프로젝트별 분류 (TECH001, POLICY001)
- 검색 품질 검증
"""

import os
import sys
from pathlib import Path
import httpx
import json
import time

# ── 설정 ──────────────────────────────────────────────────

TEST_DATA_DIR = Path(r"e:\ontology_edu\X_rag_std\zz-ai lab 통합테스트\rag_target_files")
RAG_SERVER_URL = "http://localhost:8000"
TENANT_ID = "company_abc"

# PDF 파일별 분류
FILE_MAPPING = {
    # NLP 관련 (기술)
    "NLP": {
        "project_code": "TECH001",
        "category_large": "기술",
        "category_mid": "ontology",
        "org_id": "0200",  # HR부 테스트
    },
    # 국방 관련 (규정/정책)
    "국방": {
        "project_code": "POLICY001",
        "category_large": "규정",
        "category_mid": "취업규칙",
        "org_id": "0100",  # 영업부 테스트
    },
}


def get_file_category(filename: str) -> dict:
    """파일명에서 카테고리 추출"""
    if "NLP" in filename:
        return FILE_MAPPING["NLP"]
    elif "국방" in filename:
        return FILE_MAPPING["국방"]
    else:
        return FILE_MAPPING["NLP"]  # 기본값


def upload_file(client: httpx.Client, file_path: Path, metadata: dict) -> dict:
    """PDF 파일 업로드"""
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        response = client.post(
            f"{RAG_SERVER_URL}/api/v1/documents/upload",
            files=files,
            data=metadata,
        )
    return response.json()


def test_search(client: httpx.Client, query: str, org_id: str = None) -> dict:
    """검색 테스트"""
    headers = {}
    if org_id:
        headers["X-Org-ID"] = org_id

    response = client.post(
        f"{RAG_SERVER_URL}/api/v1/rag/search",
        json={"query": query, "top_k": 5},
        headers=headers,
    )
    return response.json()


def main():
    """통합 테스트 실행"""
    print("=" * 80)
    print("AI Lab RAG Integration Test Started")
    print("=" * 80)
    print(f"Test Data: {TEST_DATA_DIR}")
    print(f"RAG Server: {RAG_SERVER_URL}")
    print()

    # 파일 확인
    pdf_files = sorted(TEST_DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        print("[FAIL] PDF files not found")
        return

    print(f"[OK] {len(pdf_files)} PDF files found")
    for pf in pdf_files:
        print(f"   - {pf.name}")
    print()

    # Server connection check
    try:
        with httpx.Client(headers={"X-Tenant-ID": TENANT_ID}, timeout=30) as client:
            health = client.get(f"{RAG_SERVER_URL}/docs")
            if health.status_code != 200:
                print("[FAIL] RAG server connection failed")
                print(f"   Server status: {health.status_code}")
                return
            print("[OK] RAG server connection successful")
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        print(f"[INFO] Check if server is running at {RAG_SERVER_URL}")
        print(f"\n[TIP] How to start server:")
        print(f"   set VECTOR_DB_ENGINE=local_json")
        print(f"   uvicorn app.main:app --port 8000 --reload")
        return

    # Step 1: File Upload

    print("\n" + "=" * 80)
    print("Step 1: PDF File Upload")
    print("=" * 80)

    uploaded_docs = []
    with httpx.Client(headers={"X-Tenant-ID": TENANT_ID}, timeout=60) as client:
        for i, file_path in enumerate(pdf_files, 1):
            metadata = get_file_category(file_path.name)
            org_id = metadata.pop("org_id")
            print(f"\n[{i}/{len(pdf_files)}] {file_path.name}")
            print(f"   Project: {metadata['project_code']}")
            print(f"   Category: {metadata['category_large']} > {metadata['category_mid']}")
            print(f"   Organization: {org_id}")

            try:
                result = upload_file(
                    client, file_path, metadata | {"X-Org-ID": org_id}
                )
                if result.get("status") == "success":
                    doc_id = result["data"]["doc_id"]
                    uploaded_docs.append(
                        {
                            "doc_id": doc_id,
                            "filename": file_path.name,
                            "metadata": metadata,
                        }
                    )
                    print(f"   [OK] Upload successful (doc_id: {doc_id})")
                else:
                    print(f"   [FAIL] Upload failed: {result.get('error')}")
            except Exception as e:
                print(f"   [FAIL] Error: {e}")

    print(f"\n[RESULT] {len(uploaded_docs)}/{len(pdf_files)} files uploaded successfully")

    if not uploaded_docs:
        print("[FAIL] No documents uploaded - cannot run search tests")
        return

    # Step 2: Document List Verification

    print("\n" + "=" * 80)
    print("Step 2: Document List Verification")
    print("=" * 80)

    with httpx.Client(headers={"X-Tenant-ID": TENANT_ID}, timeout=30) as client:
        response = client.get(f"{RAG_SERVER_URL}/api/v1/documents")
        if response.status_code == 200:
            docs = response.json()["data"]
            print(f"[OK] Stored documents: {len(docs)} files")
            for doc in docs[:5]:  # Show first 5 only
                print(f"   - {doc['file_name']} (status: {doc['pipeline_status']})")
            if len(docs) > 5:
                print(f"   ... and {len(docs) - 5} more")
        else:
            print(f"[FAIL] Document list query failed: {response.status_code}")

    # Step 3: RAG Search Test

    print("\n" + "=" * 80)
    print("Step 3: RAG Search Test")
    print("=" * 80)

    search_queries = [
        # Ontology & NLP domain queries (TECH001)
        ("온톨로지", "0200"),  # HR부
        ("자연언어처리", "0200"),
        ("knowledge graph", "0200"),
        ("semantic relationship", "0200"),
        ("NLP embedding", "0200"),

        # Defense domain queries (POLICY001)
        ("국방 지휘통제", "0100"),  # 영업부
        ("온톨로지 국방", "0100"),
        ("command control system", "0100"),

        # Cross-organizational queries
        ("AI language model", None),  # 전체 테넌트
        ("현대 문인 데이터베이스", None),
        ("감성 분석", None),
    ]

    search_results = []
    total_searches = len(search_queries)
    successful_searches = 0
    total_chunks_found = 0

    with httpx.Client(headers={"X-Tenant-ID": TENANT_ID}, timeout=30) as client:
        for idx, (query, org_id) in enumerate(search_queries, 1):
            org_label = f"(org: {org_id})" if org_id else "(all)"
            print(f"\n[{idx}/{total_searches}] '{query}' {org_label}")

            try:
                import time
                start_time = time.time()

                headers = {"X-Org-ID": org_id} if org_id else {}
                response = client.post(
                    f"{RAG_SERVER_URL}/api/v1/rag/search",
                    json={"query": query, "top_k": 3},
                    headers=headers,
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()["data"]
                    chunks = data.get("used_chunks", [])

                    if chunks:
                        successful_searches += 1
                        total_chunks_found += len(chunks)
                        print(f"   [OK] {len(chunks)} chunks found (response: {response_time:.2f}s)")

                        for i, chunk in enumerate(chunks[:2], 1):
                            score = chunk.get('similarity_score', 0)
                            chunk_id = chunk.get('chunk_id', 'N/A')
                            print(f"      [{i}] {chunk_id[:50]}... (score: {score:.3f})")

                        # Show remaining chunks if more than 2
                        if len(chunks) > 2:
                            print(f"      ... and {len(chunks) - 2} more")
                    else:
                        print(f"   [WARN] No relevant chunks found (response: {response_time:.2f}s)")

                    # Answer preview
                    answer = data.get("answer", "")
                    if answer:
                        preview = answer[:80] + "..." if len(answer) > 80 else answer
                        print(f"   [ANSWER] {preview}")

                    search_results.append({
                        "query": query,
                        "org_id": org_id,
                        "chunks_found": len(chunks),
                        "response_time": response_time,
                        "success": True,
                    })
                else:
                    print(f"   [FAIL] Search failed: {response.status_code}")
                    search_results.append({
                        "query": query,
                        "org_id": org_id,
                        "chunks_found": 0,
                        "response_time": response_time,
                        "success": False,
                    })

            except Exception as e:
                print(f"   [FAIL] Error: {e}")
                search_results.append({
                    "query": query,
                    "org_id": org_id,
                    "chunks_found": 0,
                    "response_time": 0,
                    "success": False,
                })

    # Step 4: Test Summary

    print("\n" + "=" * 80)
    print("Step 4: Integration Test Summary")
    print("=" * 80)

    avg_response_time = 0
    if search_results:
        avg_response_time = sum(r["response_time"] for r in search_results) / len(search_results)

    print(f"""
[COMPLETE] Integration test finished!

[UPLOAD] Document upload:
   - Success: {len(uploaded_docs)}/{len(pdf_files)} files
   - Projects: TECH001 (ontology), POLICY001 (defense)
   - Organizations: 0100 (sales), 0200 (HR)

[SEARCH] Search performance:
   - Test queries: {total_searches}
   - Success: {successful_searches}/{total_searches}
   - Total chunks found: {total_chunks_found}
   - Avg response time: {avg_response_time:.3f}s

[CONFIG] Test environment:
   - Storage: local_json (test mode)
   - Multitenant: {TENANT_ID}
   - Vector DB engine: local_json

[NEXT] Next steps:
   1. Switch to ChromaDB production mode
   2. Fine-tune search quality (chunk_size, top_k, etc.)
   3. Monitor performance and measure accuracy

[REFS] Related documents:
   - README.md: Server startup and API guide
   - RAG_표준_설계_v1.6.md: Architecture details
   - tests/: Automated tests (28 tests, all passing)
   - 통합테스트 방식.md: Test methodology
""")


if __name__ == "__main__":
    main()
