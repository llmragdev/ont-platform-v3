"""Evaluation script — measure QueryPlanner classification accuracy.

Usage:
    python run_eval.py [--dataset descriptive|filter|hybrid|all]

Output: accuracy per intent type + overall
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.models.tenant_context import TenantContext
from app.services.llm_client import LlmClient
from app.services.ontology import OntologyService
from app.services.query_planner import QueryPlannerService
from app.services.vector_search import VectorSearchService

_EVAL_DIR = Path(__file__).resolve().parent
_DATASETS = {
    "descriptive": _EVAL_DIR / "dataset_descriptive.jsonl",
    "filter": _EVAL_DIR / "dataset_filter.jsonl",
    "hybrid": _EVAL_DIR / "dataset_hybrid.jsonl",
}

_CTX = TenantContext(user_id="eval", company_id="eval", project_id="eval", role="Admin")


def load_dataset(path: Path) -> list[dict]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


def evaluate_dataset(name: str, path: Path, planner: QueryPlannerService) -> dict:
    items = load_dataset(path)
    if not items:
        return {"name": name, "total": 0, "correct": 0, "accuracy": 0.0, "errors": []}

    correct = 0
    errors = []
    for item in items:
        query = item["query"]
        expected = item["expected_intent"]
        try:
            plan = planner.classify_intent(query, _CTX)
            actual = plan.intent.value
        except Exception as exc:
            actual = f"ERROR: {exc}"

        if actual == expected:
            correct += 1
        else:
            errors.append({"query": query, "expected": expected, "actual": actual})

    accuracy = correct / len(items)
    return {"name": name, "total": len(items), "correct": correct, "accuracy": round(accuracy, 3), "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Evaluate QueryPlanner classification accuracy")
    parser.add_argument("--dataset", choices=["descriptive", "filter", "hybrid", "all"], default="all")
    parser.add_argument("--no-llm", action="store_true", help="Force heuristic only (disable LLM)")
    args = parser.parse_args()

    llm = LlmClient(api_key="DISABLED" if args.no_llm else None)
    ont_svc = OntologyService()
    vec_svc = VectorSearchService(embeddings=None)
    planner = QueryPlannerService(ontology_svc=ont_svc, vector_svc=vec_svc, llm_client=llm)

    datasets = _DATASETS if args.dataset == "all" else {args.dataset: _DATASETS[args.dataset]}

    total_all = correct_all = 0
    for name, path in datasets.items():
        if not path.exists():
            print(f"[SKIP] {name}: dataset file not found")
            continue
        result = evaluate_dataset(name, path, planner)
        print(f"\n[{name.upper()}] total={result['total']}  correct={result['correct']}  "
              f"accuracy={result['accuracy']:.1%}")
        if result["errors"]:
            for e in result["errors"][:5]:
                print(f"  WRONG: expected={e['expected']}  actual={e['actual']}")
                print(f"         query={e['query']!r}")
        total_all += result["total"]
        correct_all += result["correct"]

    if total_all > 0:
        print(f"\n{'='*50}")
        print(f"OVERALL: {correct_all}/{total_all} = {correct_all / total_all:.1%}")

    results_dir = _EVAL_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"eval_{ts}.json"
    out_path.write_text(json.dumps({"timestamp": ts, "total": total_all, "correct": correct_all,
                                    "accuracy": round(correct_all / total_all, 3) if total_all else 0},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
