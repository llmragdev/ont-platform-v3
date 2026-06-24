"""v5.3 answerability gate expanded smoke.

Run from ont_platform/v5/backend:
    python test_gate_expanded.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from app.api.adaptive_query import generate_stream


PROJECT_ID = "proj-deafe1fe"
SESSION_ID = "test-gate-expanded"

CASES = [
    {
        "name": "Snowflake evidence-page trap",
        "query": "Snowflake 기반 RAG 평가에서 문서 저장소와 근거 페이지를 왜 함께 관리해야 하는가?",
        "mode": "document_only",
        "expected_status": "NO_ANSWER",
        "expect_all_rag_filtered": True,
    },
    {
        "name": "Snowflake script trap",
        "query": "Snowflake 기반 RAG 평가를 위한 스크립트 작성 방법을 알려줘",
        "mode": "document_only",
        "expected_status": "NO_ANSWER",
        "expect_all_rag_filtered": True,
    },
    {
        "name": "Kafka unrelated trap",
        "query": "Kafka 스트리밍 파이프라인의 exactly-once 설정 절차는?",
        "mode": "document_only",
        "expected_status": "NO_ANSWER",
    },
    {
        "name": "Kubernetes unrelated trap",
        "query": "Kubernetes HPA를 GPU 사용률 기준으로 설정하는 방법은?",
        "mode": "document_only",
        "expected_status": "NO_ANSWER",
    },
    {
        "name": "DB schema procedure",
        "query": "DB 스키마를 온톨로지로 변환할 때 어떤 절차가 필요한가?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
    },
    {
        "name": "Defense C2 upper ontology",
        "query": "국방 지휘통제 통합 DB에서 상위 온톨로지가 필요한 이유는?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
    },
    {
        "name": "Ontology role in QA",
        "query": "온톨로지 기반 질의응답에서 온톨로지는 어떤 역할을 하는가?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
    },
    {
        "name": "Military ontology purpose",
        "query": "군 온톨로지는 어떤 목적으로 활용될 수 있는가?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
    },
    {
        "name": "Knowledge graph relation",
        "query": "온톨로지와 지식그래프는 어떤 관계가 있는가?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
    },
    {
        "name": "Document with limits schema",
        "query": "DB 스키마를 온톨로지로 변환할 때 문서에서 확인되는 절차와 한계는?",
        "mode": "document_with_limits",
        "allowed_statuses": {"PARTIAL", "NORMAL", "NO_ANSWER"},
    },
    {
        "name": "Document with limits C2",
        "query": "국방 지휘통제 통합 DB에서 상위 온톨로지가 필요한 이유 중 문서로 확인되는 내용은?",
        "mode": "document_with_limits",
        "allowed_statuses": {"PARTIAL", "NORMAL", "NO_ANSWER"},
    },
    {
        "name": "Document with limits ontology role",
        "query": "온톨로지 기반 질의응답에서 온톨로지 역할 중 문서 근거가 있는 부분은?",
        "mode": "document_with_limits",
        "allowed_statuses": {"PARTIAL", "NORMAL", "NO_ANSWER"},
    },
]


async def collect_stream(query: str, mode: str) -> dict[str, Any]:
    answer = ""
    sources = None
    complete = None

    async for sse in generate_stream(
        project_id=PROJECT_ID,
        session_id=SESSION_ID,
        query=query,
        mode=mode,
    ):
        if not sse.startswith("event: "):
            continue

        event_line, data_line = sse.strip().split("\n", 1)
        event = event_line.removeprefix("event: ").strip()
        payload = json.loads(data_line.removeprefix("data: ").strip())

        if event == "answer_chunk":
            answer += payload.get("token", "")
        elif event == "sources":
            sources = payload
        elif event == "complete":
            complete = payload

    return {
        "answer": answer,
        "sources": sources or {},
        "complete": complete or {},
    }


def assert_case(case: dict[str, Any], result: dict[str, Any]) -> None:
    complete = result["complete"]
    sources = result["sources"]
    v5_3 = complete.get("v5_3")
    if not v5_3:
        raise AssertionError("complete payload does not include v5_3")

    status = v5_3.get("answer_status")
    confidence = complete.get("confidence_score")
    rag_sources = sources.get("rag", [])

    expected_status = case.get("expected_status")
    if expected_status and status != expected_status:
        raise AssertionError(f"expected status {expected_status}, got {status}")

    allowed_statuses = case.get("allowed_statuses")
    if allowed_statuses and status not in allowed_statuses:
        raise AssertionError(f"expected status in {sorted(allowed_statuses)}, got {status}")

    if status == "NO_ANSWER" and confidence != 0.0:
        raise AssertionError(f"NO_ANSWER must have confidence 0.0, got {confidence}")

    if status == "GENERAL_ONLY" and confidence > 0.6:
        raise AssertionError(f"GENERAL_ONLY confidence must stay conservative, got {confidence}")

    if case.get("expect_all_rag_filtered") and rag_sources:
        unfiltered = [
            source for source in rag_sources
            if source.get("_status") != "FILTERED" and source.get("used") is not False
        ]
        if unfiltered:
            raise AssertionError(f"expected all RAG sources filtered, got {len(unfiltered)} unfiltered")


async def main() -> int:
    print("=== v5.3 Expanded Gate Smoke ===")
    failures: list[str] = []
    status_counts: dict[str, int] = {}

    for case in CASES:
        result = await collect_stream(case["query"], case["mode"])
        complete = result["complete"]
        sources = result["sources"]
        v5_3 = complete.get("v5_3", {})
        status = v5_3.get("answer_status", "MISSING")
        status_counts[status] = status_counts.get(status, 0) + 1
        rag_sources = sources.get("rag", [])
        filtered = sum(
            1 for source in rag_sources
            if source.get("_status") == "FILTERED" or source.get("used") is False
        )

        try:
            assert_case(case, result)
            outcome = "PASS"
        except AssertionError as exc:
            outcome = "FAIL"
            failures.append(f"{case['name']}: {exc}")

        print(
            f"{outcome} | {case['name']} | mode={case['mode']} | "
            f"status={status} | confidence={complete.get('confidence_score')} | "
            f"rag={len(rag_sources)} | filtered={filtered} | answer_len={len(result['answer'])}"
        )

    print(f"\nStatus counts: {status_counts}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nExpanded gate smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
