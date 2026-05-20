"""RAG/Policy 자동 품질 평가 (#4).

평가 데이터셋: ``backend/eval/cases.json``
실행:
    cd backend
    python evaluate.py                       # 콘솔 표 + 요약
    python evaluate.py --json                # eval/results-YYYYMMDD-HHMMSS.json 저장도 함께

측정 지표:
    1. detection_ok        — 질문에서 기대 객체ID를 추출했는지
    2. precision_at_3      — 검색 evidence가 기대 문서를 포함하는 비율
    3. action_match        — 기대 액션 포함/제외 조건 충족 여부
    4. error_match         — 도메인 오류 케이스가 정확한 코드로 거부됐는지
    5. latency_ms          — 응답 시간
    6. llm_provider        — gemini vs rule-based (폴백률 측정)

요약:
    overall_pass_rate, latency p50/p95, gemini_rate, fallback_warning_rate
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from fastapi.testclient import TestClient

from app.main import app

EVAL_DIR = Path(__file__).resolve().parent / "eval"
CASES_PATH = EVAL_DIR / "cases.json"


@dataclass
class CaseResult:
    case_id: str
    question: str
    user: str
    passed: bool
    detection_ok: bool | None
    precision_at_3: float | None
    action_match: bool | None
    error_match: bool | None
    latency_ms: int | None
    llm_provider: str | None
    warning: str | None
    detected_objects: list[str] = field(default_factory=list)
    evidence_doc_ids: list[str] = field(default_factory=list)
    available_actions: list[str] = field(default_factory=list)
    error_code: str | None = None
    notes: list[str] = field(default_factory=list)


def _percentile(values: list[int], q: float) -> int:
    """간단 백분위 (q in [0,1])."""
    if not values:
        return 0
    sorted_values = sorted(values)
    index = max(0, min(len(sorted_values) - 1, int(round(q * (len(sorted_values) - 1)))))
    return sorted_values[index]


def _evaluate_case(client: TestClient, case: dict[str, Any]) -> CaseResult:
    expected = case["expected"]
    response = client.post(
        "/api/ask",
        params={"user": case["user"]},
        json={"question": case["question"]},
    )
    payload = response.json()

    # 오류 케이스 분기
    if "expect_error_code" in expected:
        actual_code = (
            payload.get("error", {}).get("code") if response.status_code >= 400 else None
        )
        error_ok = actual_code == expected["expect_error_code"]
        return CaseResult(
            case_id=case["id"],
            question=case["question"],
            user=case["user"],
            passed=error_ok,
            detection_ok=None,
            precision_at_3=None,
            action_match=None,
            error_match=error_ok,
            latency_ms=None,
            llm_provider=None,
            warning=None,
            error_code=actual_code,
            notes=[]
            if error_ok
            else [f"expected error_code={expected['expect_error_code']}, got={actual_code}"],
        )

    # 정상 응답 케이스
    notes: list[str] = []
    if response.status_code != 200:
        notes.append(f"unexpected HTTP {response.status_code}: {payload}")
        return CaseResult(
            case_id=case["id"],
            question=case["question"],
            user=case["user"],
            passed=False,
            detection_ok=False,
            precision_at_3=0.0,
            action_match=False,
            error_match=None,
            latency_ms=None,
            llm_provider=None,
            warning=None,
            error_code=payload.get("error", {}).get("code"),
            notes=notes,
        )

    detected = payload.get("detected_objects", []) or []
    evidence_ids = [item["document_id"] for item in payload.get("evidence", [])]
    actions = payload.get("available_actions", []) or []

    detection_ok = True
    for required in expected.get("detected_objects_contains", []):
        if required not in detected:
            detection_ok = False
            notes.append(f"detection: {required} not in {detected}")

    precision_at_3: float | None = None
    if "evidence_doc_ids_contains" in expected:
        required_docs = expected["evidence_doc_ids_contains"]
        top3 = evidence_ids[:3]
        hits = sum(1 for doc in required_docs if doc in top3)
        denom = min(len(required_docs), 3) or 1
        precision_at_3 = round(hits / denom, 3)
        if precision_at_3 < 1.0:
            missing = [doc for doc in required_docs if doc not in top3]
            notes.append(f"precision@3={precision_at_3}, missing={missing}, got={top3}")
    if "evidence_doc_ids_excludes" in expected:
        for forbidden in expected["evidence_doc_ids_excludes"]:
            if forbidden in evidence_ids:
                notes.append(f"forbidden doc {forbidden} appeared in evidence={evidence_ids}")
                precision_at_3 = 0.0 if precision_at_3 is None else min(precision_at_3, 0.0)

    action_match: bool | None = None
    if "available_actions_contains" in expected:
        action_match = all(a in actions for a in expected["available_actions_contains"])
        if not action_match:
            notes.append(f"actions: expected⊇{expected['available_actions_contains']}, got={actions}")
    if "available_actions_excludes" in expected:
        excluded_present = [a for a in expected["available_actions_excludes"] if a in actions]
        if excluded_present:
            action_match = False
            notes.append(f"actions: should_exclude={excluded_present} but present in {actions}")
        elif action_match is None:
            action_match = True

    metrics_pass = [
        detection_ok if "detected_objects_contains" in expected else None,
        precision_at_3 == 1.0 if precision_at_3 is not None else None,
        action_match,
    ]
    metrics_evaluated = [m for m in metrics_pass if m is not None]
    overall = bool(metrics_evaluated) and all(metrics_evaluated)

    return CaseResult(
        case_id=case["id"],
        question=case["question"],
        user=case["user"],
        passed=overall,
        detection_ok=detection_ok if "detected_objects_contains" in expected else None,
        precision_at_3=precision_at_3,
        action_match=action_match,
        error_match=None,
        latency_ms=payload.get("latency_ms"),
        llm_provider=payload.get("llm_provider"),
        warning=payload.get("warning"),
        detected_objects=detected,
        evidence_doc_ids=evidence_ids,
        available_actions=actions,
        notes=notes,
    )


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["cases"]


def run() -> tuple[list[CaseResult], dict[str, Any]]:
    client = TestClient(app)
    results = [_evaluate_case(client, case) for case in load_cases()]

    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    precision_values = [r.precision_at_3 for r in results if r.precision_at_3 is not None]
    gemini_count = sum(1 for r in results if r.llm_provider == "gemini")
    rule_count = sum(1 for r in results if r.llm_provider == "rule-based")
    warning_count = sum(1 for r in results if r.warning)

    summary: dict[str, Any] = {
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "pass_rate": round(sum(1 for r in results if r.passed) / max(len(results), 1), 3),
        "mean_precision_at_3": round(sum(precision_values) / max(len(precision_values), 1), 3)
        if precision_values
        else None,
        "latency_ms_p50": _percentile(latencies, 0.5) if latencies else None,
        "latency_ms_p95": _percentile(latencies, 0.95) if latencies else None,
        "latency_ms_median": median(latencies) if latencies else None,
        "gemini_calls": gemini_count,
        "rule_based_calls": rule_count,
        "fallback_warning_count": warning_count,
        "gemini_success_rate": round(gemini_count / max(gemini_count + rule_count, 1), 3),
    }
    return results, summary


def format_console(results: list[CaseResult], summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"{'CASE':<35} {'USER':<10} {'PASS':<6} {'p@3':<6} {'lat(ms)':<8} {'LLM':<12}")
    lines.append("-" * 80)
    for r in results:
        lines.append(
            f"{r.case_id:<35} {r.user:<10} "
            f"{'PASS' if r.passed else 'FAIL':<6} "
            f"{r.precision_at_3 if r.precision_at_3 is not None else '-':<6} "
            f"{r.latency_ms if r.latency_ms is not None else '-':<8} "
            f"{r.llm_provider or '-':<12}"
        )
        if not r.passed and r.notes:
            for note in r.notes:
                lines.append(f"    {note}")
        if r.warning:
            lines.append(f"    WARN: {r.warning[:120]}")
    lines.append("-" * 80)
    lines.append("Summary:")
    for key, value in summary.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RAG/Policy 자동 평가")
    parser.add_argument("--json", action="store_true", help="결과를 eval/results-YYYYMMDD.json 으로 저장")
    args = parser.parse_args(argv)

    results, summary = run()
    print(format_console(results, summary))

    if args.json:
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = EVAL_DIR / f"evaluate-{stamp}.json"
        payload = {
            "generated_at": stamp,
            "summary": summary,
            "results": [
                {
                    "case_id": r.case_id,
                    "question": r.question,
                    "user": r.user,
                    "passed": r.passed,
                    "detection_ok": r.detection_ok,
                    "precision_at_3": r.precision_at_3,
                    "action_match": r.action_match,
                    "error_match": r.error_match,
                    "latency_ms": r.latency_ms,
                    "llm_provider": r.llm_provider,
                    "warning": r.warning,
                    "detected_objects": r.detected_objects,
                    "evidence_doc_ids": r.evidence_doc_ids,
                    "available_actions": r.available_actions,
                    "error_code": r.error_code,
                    "notes": r.notes,
                }
                for r in results
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n결과 저장: {path}")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
