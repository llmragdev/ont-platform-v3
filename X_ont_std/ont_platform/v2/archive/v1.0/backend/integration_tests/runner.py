"""시나리오 실행 + 채점 엔진.

각 시나리오를 POST /api/hybrid/ask 로 실행하고
100점 기준으로 채점한 결과 dict 목록을 반환한다.
"""
from __future__ import annotations

import time
from typing import Any

import requests

from .config import (
    BASE_URL,
    DEFAULT_USER,
    HEADERS,
    LATENCY_OK_MS,
    PASS_THRESHOLD,
    SCORE_ANSWER_OK,
    SCORE_DATA_COND,
    SCORE_LATENCY,
    SCORE_TYPE_MATCH,
)
from .scenarios import SCENARIOS, Scenario


# ── 채점 헬퍼 ──────────────────────────────────────────────────────────────────

def _score_type_match(resp: dict, expected: str) -> tuple[int, str]:
    actual = resp.get("query_type", "")
    if actual == expected:
        return SCORE_TYPE_MATCH, f"query_type={actual} ✓"
    return 0, f"query_type={actual} (기대: {expected})"


def _score_answer(resp: dict) -> tuple[int, str]:
    ans = resp.get("answer", "")
    if ans and len(ans) >= 100:
        return SCORE_ANSWER_OK, f"answer {len(ans)}자 ✓"
    if ans and len(ans) >= 30:
        return SCORE_ANSWER_OK // 2, f"answer {len(ans)}자 (짧음)"
    return 0, f"answer 없음 또는 너무 짧음 ({len(ans)}자)"


def _score_latency(elapsed_ms: float) -> tuple[int, str]:
    if elapsed_ms < LATENCY_OK_MS:
        return SCORE_LATENCY, f"{elapsed_ms:.0f}ms < {LATENCY_OK_MS}ms ✓"
    return 0, f"{elapsed_ms:.0f}ms ≥ {LATENCY_OK_MS}ms (초과)"


# ── 단일 시나리오 실행 ─────────────────────────────────────────────────────────

def run_scenario(scenario: Scenario) -> dict[str, Any]:
    """시나리오 하나를 실행하고 채점 결과 dict를 반환."""
    payload: dict[str, Any] = {"question": scenario["question"]}
    if scenario.get("doc_ids") is not None:
        payload["doc_ids"] = scenario["doc_ids"]

    url = f"{BASE_URL}/api/hybrid/ask?user={DEFAULT_USER}"
    error: str | None = None
    resp_data: dict = {}
    elapsed_ms: float = 0.0

    try:
        t0 = time.perf_counter()
        http_resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        if http_resp.status_code == 200:
            resp_data = http_resp.json()
        else:
            error = f"HTTP {http_resp.status_code}: {http_resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        error = "서버에 연결할 수 없음 (ConnectionError)"
    except requests.exceptions.Timeout:
        elapsed_ms = 30_000
        error = "요청 타임아웃 (30s)"
    except Exception as exc:  # noqa: BLE001
        error = f"예외: {exc}"

    # 채점
    scores: dict[str, tuple[int, str]] = {}

    if error:
        scores["type_match"] = (0, f"오류: {error}")
        scores["answer"]     = (0, "오류로 인해 미평가")
        scores["data_cond"]  = (0, "오류로 인해 미평가")
        scores["latency"]    = (0, "오류로 인해 미평가")
        total = 0
        data_pass = False
        data_reason = "오류"
    else:
        scores["type_match"] = _score_type_match(resp_data, scenario["expected_type"])
        scores["answer"]     = _score_answer(resp_data)

        check_fn = scenario.get("check")
        if check_fn:
            try:
                data_pass, data_reason = check_fn(resp_data)
            except Exception as exc:  # noqa: BLE001
                data_pass, data_reason = False, f"check 예외: {exc}"
        else:
            data_pass, data_reason = True, "check 없음"

        scores["data_cond"] = (SCORE_DATA_COND if data_pass else 0, data_reason)
        scores["latency"]   = _score_latency(elapsed_ms)
        total = sum(v for v, _ in scores.values())

    passed = total >= PASS_THRESHOLD

    return {
        "id":             scenario["id"],
        "question":       scenario["question"],
        "expected_type":  scenario["expected_type"],
        "tags":           scenario.get("tags", []),
        "description":    scenario.get("description", ""),
        "elapsed_ms":     elapsed_ms,
        "error":          error,
        "response":       resp_data,
        "scores":         {k: {"points": v, "reason": r} for k, (v, r) in scores.items()},
        "total":          total,
        "passed":         passed,
    }


# ── 전체 실행 ──────────────────────────────────────────────────────────────────

def run_all(
    scenario_ids: list[str] | None = None,
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """시나리오 목록 전체(또는 일부)를 실행하고 결과 리스트 반환."""
    targets = (
        [s for s in SCENARIOS if s["id"] in scenario_ids]
        if scenario_ids
        else SCENARIOS
    )

    results: list[dict[str, Any]] = []
    for i, scenario in enumerate(targets, 1):
        if verbose:
            print(f"[{i:02d}/{len(targets)}] {scenario['id']} — {scenario['question'][:50]}...")

        result = run_scenario(scenario)
        results.append(result)

        if verbose:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"       {status}  {result['total']:3d}pt  "
                  f"type={result['scores']['type_match']['points']}/"
                  f"ans={result['scores']['answer']['points']}/"
                  f"data={result['scores']['data_cond']['points']}/"
                  f"lat={result['scores']['latency']['points']}  "
                  f"{result['elapsed_ms']:.0f}ms")
            if result["error"]:
                print(f"       ⚠ {result['error']}")

    if verbose:
        pass_count = sum(1 for r in results if r["passed"])
        avg_score  = sum(r["total"] for r in results) / len(results) if results else 0
        print(f"\n{'─'*60}")
        print(f"결과: {pass_count}/{len(results)} PASS  |  평균 점수: {avg_score:.1f}pt")

    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """결과 목록에서 요약 통계를 계산."""
    if not results:
        return {}

    total_count  = len(results)
    pass_count   = sum(1 for r in results if r["passed"])
    fail_count   = total_count - pass_count
    avg_score    = sum(r["total"] for r in results) / total_count
    avg_latency  = sum(r["elapsed_ms"] for r in results) / total_count
    error_count  = sum(1 for r in results if r["error"])

    by_type: dict[str, dict] = {}
    for r in results:
        t = r["expected_type"]
        if t not in by_type:
            by_type[t] = {"total": 0, "pass": 0}
        by_type[t]["total"] += 1
        if r["passed"]:
            by_type[t]["pass"] += 1

    return {
        "total":       total_count,
        "pass":        pass_count,
        "fail":        fail_count,
        "pass_rate":   round(pass_count / total_count * 100, 1),
        "avg_score":   round(avg_score, 1),
        "avg_latency": round(avg_latency, 0),
        "errors":      error_count,
        "by_type":     by_type,
    }
