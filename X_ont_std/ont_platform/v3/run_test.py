#!/usr/bin/env python3
"""빠른 통합 테스트 실행 스크립트"""
import sys
import os
import time
from pathlib import Path

# 환경 변수 설정
os.environ["GEMINI_API_KEY"] = "AIzaSyAMt7L0OVBzarSLn-Tn-3RyNbaIKg4RKPA"
os.environ["LLM_MODEL_NAME"] = "gemini-2.5-flash-lite"

# sys.path 설정
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path.parent.parent))
sys.path.insert(0, str(backend_path))

# FastAPI 테스트 클라이언트
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("[TEST] Integration Test Running...")
print("=" * 60)

# 테스트 실행
response = client.post(
    "/api/integration-test/run",
    json={
        "project": "ai-voucher-2025",
        "company_id": "demo-co",
        "project_id": "proj-01"
    },
    timeout=180
)

print(f"HTTP Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()

    # 요약 출력
    summary = result.get("summary", {})
    print("\n[SUMMARY] Test Summary:")
    print("-" * 60)
    print(f"Total:     {summary.get('total')}")
    print(f"Passed:    {summary.get('passed')}")
    print(f"Failed:    {summary.get('failed')}")
    print(f"Pass Rate: {summary.get('pass_rate'):.1%}")
    print(f"Duration:  {summary.get('duration_sec'):.2f}s")

    # 소스별 상세
    print("\n[BY SOURCE]")
    print("-" * 60)
    for source, stats in summary.get("by_source", {}).items():
        rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
        print(f"{source:15} {stats['passed']:2}/{stats['total']:2} ({rate:5.1%})")

    # 실패한 케이스 나열
    cases = result.get("cases", [])
    failed_cases = [c for c in cases if not c.get("passed")]

    if failed_cases:
        print("\n[FAILED] Cases:")
        print("-" * 60)
        for case in failed_cases[:5]:  # 처음 5개만
            print(f"\n{case['id']}: {case['question'][:50]}...")
            print(f"  Expected: {case['expected_source']}")
            print(f"  Got:      {case['actual_source']}")
            print(f"  Source Matched: {case['source_matched']}")
            print(f"  Keyword Matched: {case['keyword_matched']}")

    # 테스트 파일 저장 경로
    print(f"\n[SAVED] Result:")
    print(f"   {result.get('run_id')}.json")

else:
    print(f"[ERROR] {response.text}")
    sys.exit(1)

print("\n[DONE] Test completed")
