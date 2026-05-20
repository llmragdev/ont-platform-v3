from __future__ import annotations

from backend.app_context import AppContext


def main() -> None:
    app = AppContext()
    question = "C001 고객의 O001 주문을 승인해도 될까?"
    result = app.ask(question, "analyst")

    print("=== Question ===")
    print(question)
    print("\n=== Detected Objects ===")
    print(result["detected_objects"])
    print("\n=== Ontology Context ===")
    print(result["context"])
    print("\n=== Evidence ===")
    for item in result["evidence"]:
        print(f"{item['document_id']} {item['title']} score={item['score']}")
    print("\n=== RAG Prompt ===")
    print(result["prompt"])
    print("\n=== Answer ===")
    print(result["answer"])
    print("\n=== Workflow Action ===")
    user = app.user("analyst")
    print(app.workflow.execute(user, "ApproveOrder", "O001", {"comment": "Approved from CLI demo"}))
    print("\n=== Audit Events ===")
    for event in app.audit.list_events():
        print(event)


if __name__ == "__main__":
    main()

