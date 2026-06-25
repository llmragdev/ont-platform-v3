"""v5.3 answerability gate regression smoke.

Run from ont_platform/v5/backend:
    python test_gate.py
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
SESSION_ID = "test-gate"

CASES = [
    {
        "name": "Snowflake blocked in document_only",
        "query": "Snowflake 기반 RAG 평가에서 문서 저장소와 근거 페이지를 왜 함께 관리해야 하는가?",
        "mode": "document_only",
        "expected_status": "NO_ANSWER",
        "expected_confidence": 0.0,
        "expect_all_rag_filtered": True,
    },
    {
        "name": "DB schema survives in expert_mode",
        "query": "DB 스키마를 온톨로지로 변환할 때 어떤 절차가 필요한가?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
    },
    {
        "name": "Defense C2 survives in expert_mode",
        "query": "국방 지휘통제 통합 DB에서 상위 온톨로지가 필요한 이유는?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
    },
    {
        "name": "Ontology role survives in expert_mode",
        "query": "온톨로지 기반 질의응답에서 온톨로지는 어떤 역할을 하는가?",
        "mode": "expert_mode",
        "allowed_statuses": {"GENERAL_ONLY", "PARTIAL", "NORMAL"},
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

    if "expected_confidence" in case and confidence != case["expected_confidence"]:
        raise AssertionError(f"expected confidence {case['expected_confidence']}, got {confidence}")

    if case.get("expect_all_rag_filtered"):
        if not rag_sources:
            raise AssertionError("expected RAG sources to prove FILTERED handling")
        unfiltered = [
            source for source in rag_sources
            if source.get("_status") != "FILTERED" and source.get("used") is not False
        ]
        if unfiltered:
            raise AssertionError(f"expected all RAG sources filtered, got {len(unfiltered)} unfiltered")


async def main() -> int:
    print("=== v5.3 Answerability Gate Regression ===")
    failures: list[str] = []

    for case in CASES:
        result = await collect_stream(case["query"], case["mode"])
        complete = result["complete"]
        sources = result["sources"]
        v5_3 = complete.get("v5_3", {})
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
            f"status={v5_3.get('answer_status')} | "
            f"confidence={complete.get('confidence_score')} | "
            f"rag={len(rag_sources)} | filtered={filtered} | "
            f"answer_len={len(result['answer'])}"
        )

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nAll gate checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
