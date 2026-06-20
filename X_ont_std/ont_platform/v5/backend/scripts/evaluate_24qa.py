from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_PROJECT_ID = "proj-deafe1fe"
DEFAULT_API_BASE = "http://127.0.0.1:8001"
DEFAULT_OUTPUT = Path("eval_results_24qa.json")


DEFAULT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "ONT-01",
        "category": "Ontology",
        "text": "온톨로지 기반 질의응답에서 온톨로지는 어떤 역할을 하는가?",
        "expected": "개념 분류, 관계 모델링, 기계 판독 가능성, 의미 통합, Class/Property/Instance, 의미 검색과 추론, 상호운용성을 설명한다.",
    },
    {"id": "ONT-02", "category": "Ontology", "text": "온톨로지와 지식그래프의 차이는 무엇인가?", "expected": ""},
    {"id": "ONT-03", "category": "Ontology", "text": "Class, Property, Instance는 온톨로지에서 어떻게 사용되는가?", "expected": ""},
    {"id": "ONT-04", "category": "Ontology", "text": "온톨로지가 의미 기반 검색을 가능하게 하는 이유는 무엇인가?", "expected": ""},
    {"id": "ONT-05", "category": "Ontology", "text": "온톨로지에서 관계 모델링이 중요한 이유는 무엇인가?", "expected": ""},
    {"id": "ONT-06", "category": "Ontology", "text": "온톨로지 기반 추론은 어떤 방식으로 이루어지는가?", "expected": ""},
    {"id": "ONT-07", "category": "Ontology", "text": "온톨로지가 시스템 간 상호운용성에 기여하는 방식은 무엇인가?", "expected": ""},
    {"id": "ONT-08", "category": "Ontology", "text": "온톨로지 품질을 검증할 때 확인해야 할 요소는 무엇인가?", "expected": ""},
    {"id": "RAG-01", "category": "Advanced RAG", "text": "RAG에서 검색 근거의 품질이 답변 정확도에 미치는 영향은 무엇인가?", "expected": ""},
    {"id": "RAG-02", "category": "Advanced RAG", "text": "벡터 검색과 키워드 검색은 어떻게 다른가?", "expected": ""},
    {"id": "RAG-03", "category": "Advanced RAG", "text": "하이브리드 검색이 필요한 이유는 무엇인가?", "expected": ""},
    {"id": "RAG-04", "category": "Advanced RAG", "text": "RAG에서 임계값 설정이 중요한 이유는 무엇인가?", "expected": ""},
    {"id": "RAG-05", "category": "Advanced RAG", "text": "재랭킹은 RAG 결과를 어떻게 개선하는가?", "expected": ""},
    {"id": "RAG-06", "category": "Advanced RAG", "text": "문서 청킹 전략이 검색 정확도에 미치는 영향은 무엇인가?", "expected": ""},
    {"id": "RAG-07", "category": "Advanced RAG", "text": "근거 없는 답변을 줄이기 위한 방법은 무엇인가?", "expected": ""},
    {"id": "RAG-08", "category": "Advanced RAG", "text": "RAG 평가에서 출처 검증이 중요한 이유는 무엇인가?", "expected": ""},
    {"id": "SNOW-01", "category": "Snowflake", "text": "Snowflake Cortex AI의 주요 역할은 무엇인가?", "expected": ""},
    {"id": "SNOW-02", "category": "Snowflake", "text": "Snowflake 데이터 웨어하우스와 온톨로지 플랫폼은 어떻게 연계될 수 있는가?", "expected": ""},
    {"id": "SNOW-03", "category": "Snowflake", "text": "메달리온 아키텍처에서 Bronze, Silver, Gold 계층은 무엇을 의미하는가?", "expected": ""},
    {"id": "SNOW-04", "category": "Snowflake", "text": "Snowflake 기반 분석에서 스키마 메타데이터가 중요한 이유는 무엇인가?", "expected": ""},
    {"id": "SNOW-05", "category": "Snowflake", "text": "Cortex AI와 RAG 기반 질의응답의 차이는 무엇인가?", "expected": ""},
    {"id": "SNOW-06", "category": "Snowflake", "text": "데이터 카탈로그와 온톨로지는 어떤 관계를 가질 수 있는가?", "expected": ""},
    {"id": "SNOW-07", "category": "Snowflake", "text": "Snowflake 연동이 없을 때 질의응답 시스템은 어떻게 응답해야 하는가?", "expected": ""},
    {"id": "SNOW-08", "category": "Snowflake", "text": "기업 데이터 분석에서 의미 계층을 두는 이유는 무엇인가?", "expected": ""},
]


def load_questions(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return DEFAULT_QUESTIONS
    if not path.exists():
        raise FileNotFoundError(f"Question file not found: {path}")

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("questions", [])
        return [normalize_question(item, idx + 1) for idx, item in enumerate(data)]

    if path.suffix.lower() in {".csv", ".tsv"}:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return [normalize_question(row, idx + 1) for idx, row in enumerate(reader)]

    raise ValueError("Supported question formats: .json, .csv, .tsv")


def normalize_question(item: dict[str, Any], fallback_id: int) -> dict[str, Any]:
    text = item.get("text") or item.get("question") or item.get("질문") or ""
    if not text:
        raise ValueError(f"Question text is empty at row {fallback_id}")
    return {
        "id": item.get("id") or item.get("question_id") or f"Q{fallback_id:02d}",
        "category": item.get("category") or item.get("카테고리") or "Uncategorized",
        "text": text,
        "expected": item.get("expected") or item.get("answer") or item.get("예상답변") or "",
    }


def parse_sse(raw_text: str) -> dict[str, Any]:
    answer_parts: list[str] = []
    sources: dict[str, Any] = {"rag": [], "ontology": [], "expert_opinions": []}
    complete: dict[str, Any] = {}
    events: list[dict[str, Any]] = []

    event_name: str | None = None
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal event_name, data_lines, sources, complete
        if not event_name:
            data_lines = []
            return
        payload_text = "\n".join(data_lines)
        try:
            payload = json.loads(payload_text) if payload_text else None
        except json.JSONDecodeError:
            payload = payload_text
        events.append({"event": event_name, "data": payload})
        if event_name == "answer_chunk" and isinstance(payload, dict):
            answer_parts.append(str(payload.get("token", "")))
        elif event_name == "sources" and isinstance(payload, dict):
            sources = payload
        elif event_name == "complete" and isinstance(payload, dict):
            complete = payload
        event_name = None
        data_lines = []

    for line in raw_text.splitlines():
        if not line:
            flush()
            continue
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())
    flush()

    return {
        "answer": "".join(answer_parts),
        "sources": sources,
        "complete": complete,
        "events": events,
    }


def call_query_api(api_base: str, project_id: str, question: str, mode: str, timeout: int) -> dict[str, Any]:
    query = urlencode({"query": question, "mode": mode})
    url = f"{api_base.rstrip('/')}/api/v1/projects/{project_id}/query/stream?{query}"
    req = Request(url, headers={"Accept": "text/event-stream"})
    started = time.perf_counter()
    with urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        status = getattr(response, "status", 200)
    parsed = parse_sse(raw)
    parsed["http_status"] = status
    parsed["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
    parsed["raw_length"] = len(raw)
    return parsed


def evaluate_all_questions(args: argparse.Namespace) -> list[dict[str, Any]]:
    questions = load_questions(args.questions)
    results: list[dict[str, Any]] = []

    for idx, question in enumerate(questions, start=1):
        print(f"[{idx}/{len(questions)}] {question['id']} {question['text'][:60]}")
        try:
            parsed = call_query_api(args.api_base, args.project_id, question["text"], args.mode, args.timeout)
            sources = parsed["sources"]
            complete = parsed["complete"]
            results.append(
                {
                    "question_id": question["id"],
                    "category": question["category"],
                    "question": question["text"],
                    "expected": question["expected"],
                    "actual": parsed["answer"],
                    "http_status": parsed["http_status"],
                    "elapsed_ms": parsed["elapsed_ms"],
                    "sources_count": {
                        "rag": len(sources.get("rag", [])),
                        "ontology": len(sources.get("ontology", [])),
                        "expert": len(sources.get("expert_opinions", [])),
                    },
                    "coverage_check": complete.get("coverage_check"),
                    "confidence_score": complete.get("confidence_score"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "question_id": question["id"],
                    "category": question["category"],
                    "question": question["text"],
                    "expected": question["expected"],
                    "actual": "",
                    "error": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    return results


def write_results(path: Path, results: list[dict[str, Any]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "api_base": args.api_base,
            "project_id": args.project_id,
            "mode": args.mode,
            "question_count": len(results),
        },
        "results": results,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate 24 QA questions against the v5 SSE query API.")
    parser.add_argument("--api-base", default=os.getenv("EVAL_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--project-id", default=os.getenv("EVAL_PROJECT_ID", DEFAULT_PROJECT_ID))
    parser.add_argument("--mode", default=os.getenv("EVAL_MODE", "expert_mode"))
    parser.add_argument("--questions", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=45)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    results = evaluate_all_questions(args)
    write_results(args.output, results, args)
    failed = sum(1 for item in results if item.get("error"))
    print(f"Saved: {args.output}")
    print(f"Completed: {len(results) - failed}/{len(results)}")
    if failed:
        print(f"Failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
