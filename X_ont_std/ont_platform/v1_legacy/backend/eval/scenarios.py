"""학습 시나리오 5종 자동 검증.

README.md §4의 시나리오를 실제로 API에 던져서 기대 결과와 일치하는지 확인한다.
브라우저 클릭을 못 하는 환경(CI 등)에서 회귀 감지용으로 사용한다.

실행:
    cd backend && python -m eval.scenarios            # uvicorn 서버 필요
    cd backend && python -m eval.scenarios --json     # 결과를 eval/results-YYYYMMDD.json 로 저장
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


@dataclass
class ScenarioResult:
    name: str
    description: str
    passed: bool
    expected: dict
    actual: dict
    notes: list[str] = field(default_factory=list)


def _check(actual: Any, predicate, label: str, notes: list[str]) -> bool:
    try:
        ok = predicate(actual)
    except Exception as exc:
        notes.append(f"{label}: 예외 {exc!r}")
        return False
    if not ok:
        notes.append(f"{label}: 실패 (actual={actual!r})")
    return ok


def scenario_1_normal_approval(client: TestClient) -> ScenarioResult:
    """analyst 사용자가 O001(Submitted, Low risk, 3200원)을 승인."""
    notes: list[str] = []
    queue = client.get("/api/workflow/queue").json()["queue"]
    in_queue = next((row for row in queue if row["id"] == "O001"), None)
    pre_ok = _check(in_queue, lambda r: r is not None and "ApproveOrder" in r["available_actions"], "O001 큐에 ApproveOrder 존재", notes)

    response = client.post(
        "/api/workflow/execute",
        json={"action": "ApproveOrder", "order_id": "O001"},
    )
    body = response.json()
    status_ok = _check(response.status_code, lambda code: code == 200, "HTTP 200", notes)
    transition_ok = _check(
        body, lambda b: b["result"]["to_status"] == "Approved", "to_status == Approved", notes
    )

    # 상태 복구
    return ScenarioResult(
        name="정상 승인",
        description="analyst + O001 + ApproveOrder → Approved",
        passed=pre_ok and status_ok and transition_ok,
        expected={"http": 200, "to_status": "Approved", "available_actions_contains": "ApproveOrder"},
        actual={"http": response.status_code, "to_status": body.get("result", {}).get("to_status")},
        notes=notes,
    )


def scenario_2_high_risk_reject(client: TestClient) -> ScenarioResult:
    """analyst가 O003(Gamma Logistics, High risk)을 승인 시도 → 거부."""
    notes: list[str] = []
    response = client.post(
        "/api/workflow/execute",
        json={"action": "ApproveOrder", "order_id": "O003"},
    )
    body = response.json()
    http_ok = _check(response.status_code, lambda code: code == 409, "HTTP 409", notes)
    code_ok = _check(
        body, lambda b: b.get("error", {}).get("code") == "ACTION_NOT_ALLOWED", "error.code == ACTION_NOT_ALLOWED", notes
    )
    return ScenarioResult(
        name="고위험 거부",
        description="analyst + O003(High risk) + ApproveOrder → ACTION_NOT_ALLOWED",
        passed=http_ok and code_ok,
        expected={"http": 409, "error.code": "ACTION_NOT_ALLOWED"},
        actual={"http": response.status_code, "error": body.get("error", {})},
        notes=notes,
    )


def scenario_3_amount_threshold(client: TestClient) -> ScenarioResult:
    """O002(C002 Beta Retail, 8200원, ≥5000)는 analyst에게 ApproveOrder가 안 보이고 finance에게는 보임."""
    notes: list[str] = []
    analyst_queue = client.get("/api/workflow/queue", params={"user": "analyst"}).json()["queue"]
    analyst_o002 = next((row for row in analyst_queue if row["id"] == "O002"), None)
    # O002는 Busan이라 analyst region(Seoul/Incheon)에 없어서 큐에서 빠지거나 ApproveOrder가 없어야 함
    analyst_blocked = _check(
        analyst_o002,
        lambda r: r is None or "ApproveOrder" not in r["available_actions"],
        "analyst 큐에 O002 ApproveOrder 없음",
        notes,
    )

    finance_queue = client.get("/api/workflow/queue", params={"user": "finance"}).json()["queue"]
    finance_o002 = next((row for row in finance_queue if row["id"] == "O002"), None)
    finance_can = _check(
        finance_o002,
        lambda r: r is not None and "ApproveOrder" in r["available_actions"],
        "finance 큐에 O002 ApproveOrder 존재",
        notes,
    )

    return ScenarioResult(
        name="금액 임계 분기",
        description="O002(8200원) → analyst 불가 / finance 가능",
        passed=analyst_blocked and finance_can,
        expected={"analyst_can_approve_O002": False, "finance_can_approve_O002": True},
        actual={
            "analyst_o002": analyst_o002["available_actions"] if analyst_o002 else None,
            "finance_o002": finance_o002["available_actions"] if finance_o002 else None,
        },
        notes=notes,
    )


def scenario_4_region_filter(client: TestClient) -> ScenarioResult:
    """viewer(Seoul만 접근 가능)에게는 O002(Busan), O003(Incheon)이 보이지 않거나 액션이 없어야 한다."""
    notes: list[str] = []
    response = client.get("/api/objects/orders/O002/context", params={"user": "viewer"})
    forbidden = _check(response.status_code, lambda code: code == 403, "O002 viewer → 403", notes)
    err_code = _check(
        response.json(),
        lambda b: b.get("error", {}).get("code") == "FORBIDDEN",
        "error.code == FORBIDDEN",
        notes,
    )
    return ScenarioResult(
        name="지역 거부",
        description="viewer(Seoul) → O002(Busan) context 조회 시 403 FORBIDDEN",
        passed=forbidden and err_code,
        expected={"http": 403, "error.code": "FORBIDDEN"},
        actual={"http": response.status_code, "error": response.json().get("error", {})},
        notes=notes,
    )


def scenario_5_masking(client: TestClient) -> ScenarioResult:
    """viewer는 customer.risk_tier=Restricted, analyst는 contract_terms 마스킹."""
    notes: list[str] = []
    viewer_customers = client.get("/api/objects/customers", params={"user": "viewer"}).json()["customers"]
    target = next((c for c in viewer_customers if c["id"] == "C001"), None)
    viewer_ok = _check(
        target,
        lambda c: c is not None and c.get("risk_tier") == "Restricted",
        "viewer가 보는 C001.risk_tier == Restricted",
        notes,
    )

    analyst_customers = client.get("/api/objects/customers", params={"user": "analyst"}).json()["customers"]
    analyst_target = next((c for c in analyst_customers if c["id"] == "C001"), None)
    analyst_ok = _check(
        analyst_target,
        lambda c: c is not None and c.get("contract_terms", "").startswith("Custom discount rate:"),
        "analyst가 보는 C001.contract_terms 마스킹",
        notes,
    )

    finance_customers = client.get("/api/objects/customers", params={"user": "finance"}).json()["customers"]
    finance_target = next((c for c in finance_customers if c["id"] == "C001"), None)
    finance_clear = _check(
        finance_target,
        lambda c: c is not None and "discount 7%" in c.get("contract_terms", ""),
        "finance는 contract_terms 원본 노출",
        notes,
    )

    return ScenarioResult(
        name="속성 마스킹",
        description="viewer→Restricted / analyst→마스킹 / finance→원본",
        passed=viewer_ok and analyst_ok and finance_clear,
        expected={
            "viewer.risk_tier": "Restricted",
            "analyst.contract_terms_starts_with": "Custom discount rate:",
            "finance.contract_terms_contains": "discount 7%",
        },
        actual={
            "viewer.risk_tier": (target or {}).get("risk_tier"),
            "analyst.contract_terms": (analyst_target or {}).get("contract_terms"),
            "finance.contract_terms": (finance_target or {}).get("contract_terms"),
        },
        notes=notes,
    )


def run_all() -> list[ScenarioResult]:
    client = TestClient(app)
    return [
        scenario_1_normal_approval(client),
        scenario_2_high_risk_reject(client),
        scenario_3_amount_threshold(client),
        scenario_4_region_filter(client),
        scenario_5_masking(client),
    ]


def format_console(results: list[ScenarioResult]) -> str:
    lines: list[str] = []
    passed = 0
    for index, result in enumerate(results, start=1):
        mark = "PASS" if result.passed else "FAIL"
        passed += 1 if result.passed else 0
        lines.append(f"[{mark}] #{index} {result.name} — {result.description}")
        if not result.passed:
            for note in result.notes:
                lines.append(f"      ↳ {note}")
            lines.append(f"      expected={result.expected}")
            lines.append(f"      actual={result.actual}")
    lines.append("")
    lines.append(f"{passed}/{len(results)} passed")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="결과를 eval/results-YYYYMMDD.json 으로 저장")
    args = parser.parse_args(argv)

    results = run_all()
    print(format_console(results))

    if args.json:
        out_dir = Path(__file__).parent
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = out_dir / f"results-{stamp}.json"
        payload = [
            {
                "name": result.name,
                "description": result.description,
                "passed": result.passed,
                "expected": result.expected,
                "actual": result.actual,
                "notes": result.notes,
            }
            for result in results
        ]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n결과 저장: {path}")

    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
