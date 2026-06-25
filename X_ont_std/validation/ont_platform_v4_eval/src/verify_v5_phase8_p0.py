from __future__ import annotations

import sys
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "ont_platform").exists())
V5_BACKEND = ROOT / "ont_platform" / "v5" / "backend"


def main() -> None:
    sys.path.insert(0, str(V5_BACKEND))
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    headers = {
        "X-User-ID": "phase8-p0-verifier",
        "X-Company-ID": "phase8",
        "X-Project-ID": "p0-empty-project",
        "X-Role": "Admin",
    }

    routes = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v5/hybrid/ask" in routes, "v5 endpoint is not registered"

    snowflake = client.post(
        "/api/v5/hybrid/ask",
        headers=headers,
        json={
            "question": "ranking_issue는 Snowflake RAG 평가에서 어떤 경우로 기록해야 하는가?",
            "search_mode": "auto",
        },
    )
    assert snowflake.status_code == 200, snowflake.text
    snowflake_data = snowflake.json()
    assert snowflake_data["answer"] == "질문은 해당 카테고리 문서와 관련이 없습니다."
    assert snowflake_data["quality_metrics"]["llm_used"] is False
    assert snowflake_data["quality_metrics"]["no_answer"] is True

    route_cases = [
        ("ontology_only", "VECTOR"),
        ("vector_only", "ONTOLOGY"),
    ]
    for mode, forbidden_trace in route_cases:
        response = client.post(
            "/api/v5/hybrid/ask",
            headers=headers,
            json={
                "question": "온톨로지 기반 질의응답에서 온톨로지는 어떤 역할을 하는가?",
                "search_mode": mode,
            },
        )
        assert response.status_code == 200, response.text
        trace = response.json().get("trace", [])
        assert not any(forbidden_trace in item for item in trace), f"{mode} trace contains {forbidden_trace}: {trace}"

    print("PHASE8 v5 P0 verification passed")


if __name__ == "__main__":
    main()
