from __future__ import annotations

from backend.app_context import AppContext
from backend.errors import AppError


TESTS = [
    {
        "id": "Q1",
        "question": "C001 고객의 O001 주문을 승인해도 될까?",
        "user": "analyst",
        "expected_status": "ANSWERED",
        "expected_document": "D001",
    },
    {
        "id": "Q2",
        "question": "C002 고객의 O002 주문은 왜 재무 승인이 필요해?",
        "user": "finance",
        "expected_status": "ANSWERED",
        "expected_document": "D001",
    },
    {
        "id": "Q3",
        "question": "O999 주문 상태를 알려줘.",
        "user": "analyst",
        "expected_status": "OBJECT_NOT_FOUND",
    },
    {
        "id": "Q4",
        "question": "C001 고객과 O002 주문은 연결되어 있어?",
        "user": "finance",
        "expected_status": "RELATION_MISMATCH",
    },
    {
        "id": "Q5",
        "question": "고위험 고객 주문을 자동 승인해도 돼? C003 O003",
        "user": "analyst",
        "expected_status": "ANSWERED",
        "expected_no_action": "ApproveOrder",
    },
]


def main() -> None:
    app = AppContext()
    passed = 0
    rows = []
    for test in TESTS:
        try:
            result = app.ask(test["question"], test["user"])
            status = "ANSWERED"
            docs = [item["document_id"] for item in result["evidence"]]
            actions = result["available_actions"]
        except AppError as error:
            status = error.code
            docs = []
            actions = []

        ok = status == test["expected_status"]
        if ok and test.get("expected_document"):
            ok = test["expected_document"] in docs
        if ok and test.get("expected_no_action"):
            ok = test["expected_no_action"] not in actions
        passed += 1 if ok else 0
        rows.append((test["id"], status, "PASS" if ok else "FAIL", docs, actions))

    print("=== RAG / Ontology Evaluation ===")
    for row in rows:
        print(f"{row[0]} status={row[1]} result={row[2]} docs={row[3]} actions={row[4]}")
    print(f"\nScore: {passed}/{len(TESTS)}")


if __name__ == "__main__":
    main()

