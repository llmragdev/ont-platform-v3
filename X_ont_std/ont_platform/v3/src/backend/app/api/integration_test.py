"""Integration Test Runner API — v3.0
Runs QA dataset cases against hybridAsk and evaluates pass/fail.

Source matching semantics (contribution-based, not exclusive):
  ontology    → ontology_hits > 0  (vector may also be present)
  vector      → vector_hits > 0    (ontology may also be present)
  hybrid      → both > 0
  no_evidence → both == 0

Keyword matching:
  match_mode "any" → any expected_keyword found in answer → pass
  match_mode "all" → all expected_keywords must be in answer → pass
  expect_no_answer=True → forbidden_keywords must NOT appear → pass
  expect_no_evidence=True → acknowledgment_keywords must appear → pass
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_query_planner_service, get_tenant_context
from app.models.tenant_context import TenantContext
from app.services.query_planner import QueryPlannerService
from storage_config import get_project_root

router = APIRouter(prefix="/api/integration-test", tags=["integration-test"])

_BACKEND = Path(__file__).resolve().parent.parent.parent
TEST_DATA_ROOT = _BACKEND / "test_data"


# ── helpers ───────────────────────────────────────────────────────────────────

def _test_runs_dir(ctx: TenantContext, project: str) -> Path:
    d = get_project_root(ctx.company_id, ctx.project_id) / "test_runs" / project
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_qa_dataset(project: str) -> dict:
    p = TEST_DATA_ROOT / project / "qa_dataset.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"QA 데이터셋 없음: {project}")
    return json.loads(p.read_text(encoding="utf-8"))


def _detect_source(quality_metrics: dict) -> str:
    """Categorize which sources contributed to the answer."""
    ont = quality_metrics.get("ontology_hits", 0)
    vec = quality_metrics.get("vector_hits", 0)
    if ont > 0 and vec > 0:
        return "hybrid"
    if ont > 0:
        return "ontology"
    if vec > 0:
        return "vector"
    return "no_evidence"


def _source_matches(actual: str, expected: str) -> bool:
    """Contribution-based matching — expected source must be present, not exclusive."""
    if expected == "no_evidence":
        return actual == "no_evidence"
    if expected == "ontology":
        # ontology contributed — actual is "ontology" or "hybrid"
        return actual in ("ontology", "hybrid")
    if expected == "vector":
        # vector contributed — actual is "vector" or "hybrid"
        return actual in ("vector", "hybrid")
    if expected == "hybrid":
        return actual == "hybrid"
    return actual == expected


def _check_keywords(answer: str, case: dict) -> bool:
    lower = answer.lower()

    # Hallucination guard: forbidden keywords must NOT appear
    if case.get("expect_no_answer"):
        forbidden = case.get("forbidden_keywords", [])
        if not forbidden:
            return True
        return not any(kw.lower() in lower for kw in forbidden)

    # No-evidence acknowledgment check
    if case.get("expect_no_evidence"):
        ack_kws = case.get("acknowledgment_keywords", [])
        if not ack_kws:
            return True
        return any(kw.lower() in lower for kw in ack_kws)

    keywords = case.get("expected_keywords", [])
    if not keywords:
        return True

    mode = case.get("match_mode", "any")
    if mode == "all":
        return all(kw.lower() in lower for kw in keywords)
    return any(kw.lower() in lower for kw in keywords)


def _evaluate_case(case: dict, response_dict: dict, duration_ms: int) -> dict:
    qm = response_dict.get("quality_metrics") or {}
    answer = response_dict.get("answer", "")

    actual_source = _detect_source(qm)
    source_matched = _source_matches(actual_source, case["expected_source"])
    keyword_matched = _check_keywords(answer, case)
    passed = source_matched and keyword_matched

    ontology_evidence = response_dict.get("ontology_evidence") or []
    vector_sources = [
        s for s in (response_dict.get("sources") or [])
        if s.get("source_type") == "vector"
    ]

    evidence = []
    for oe in ontology_evidence[:3]:
        evidence.append({
            "type": "ontology",
            "entity": oe.get("label", ""),
            "entity_type": oe.get("node_type", ""),
        })
    for vs in vector_sources[:2]:
        evidence.append({
            "type": "vector",
            "doc_id": vs.get("doc_id", ""),
            "score": vs.get("score"),
            "text": (vs.get("text") or "")[:100],
        })

    return {
        "id": case["id"],
        "tags": case.get("tags", []),
        "question": case["question"],
        "expected_source": case["expected_source"],
        "expected_keywords": case.get("expected_keywords", []),
        "match_mode": case.get("match_mode", "any"),
        "actual_source": actual_source,
        "actual_answer": answer,
        "ontology_hits": qm.get("ontology_hits", 0),
        "vector_hits": qm.get("vector_hits", 0),
        "llm_used": qm.get("llm_used", False),
        "source_matched": source_matched,
        "keyword_matched": keyword_matched,
        "passed": passed,
        "evidence": evidence,
        "duration_ms": duration_ms,
        "note": case.get("note", case.get("_note", "")),
    }


def _make_summary(cases: list[dict], duration_sec: float, project: str, run_id: str) -> dict:
    total = len(cases)
    passed = sum(1 for c in cases if c["passed"])
    by_source: dict[str, dict] = {}
    for c in cases:
        src = c["expected_source"]
        if src not in by_source:
            by_source[src] = {"total": 0, "passed": 0}
        by_source[src]["total"] += 1
        if c["passed"]:
            by_source[src]["passed"] += 1

    return {
        "run_id": run_id,
        "project": project,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "duration_sec": round(duration_sec, 2),
            "by_source": by_source,
        },
        "cases": cases,
    }


# ── request model ─────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    project: str
    company_id: str | None = None
    project_id: str | None = None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/run")
def run_integration_test(
    body: RunRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    svc: QueryPlannerService = Depends(get_query_planner_service),
):
    dataset = _load_qa_dataset(body.project)
    cases_def = dataset.get("cases", [])
    if not cases_def:
        raise HTTPException(status_code=400, detail="QA 케이스가 없습니다.")

    # Override TenantContext with request body values if provided
    if body.company_id or body.project_id:
        ctx = TenantContext(
            user_id=ctx.user_id,
            company_id=body.company_id or ctx.company_id,
            project_id=body.project_id or ctx.project_id,
            role=ctx.role,
            permissions=ctx.permissions,
        )

    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    t_start = time.time()
    evaluated: list[dict] = []

    for case in cases_def:
        t_case = time.time()
        try:
            response = svc.ask_forced_hybrid(case["question"], ctx)
            res_dict: dict[str, Any] = (
                response.model_dump(mode="json")
                if hasattr(response, "model_dump")
                else response.dict()
            )
        except Exception as exc:
            res_dict = {
                "answer": f"[ERROR] {exc}",
                "quality_metrics": {},
                "ontology_evidence": [],
                "sources": [],
            }
        duration_ms = int((time.time() - t_case) * 1000)
        evaluated.append(_evaluate_case(case, res_dict, duration_ms))

    total_sec = time.time() - t_start
    result = _make_summary(evaluated, total_sec, body.project, run_id)

    runs_dir = _test_runs_dir(ctx, body.project)
    (runs_dir / f"{run_id}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return result


@router.get("/projects")
def list_test_projects(ctx: TenantContext = Depends(get_tenant_context)):
    projects = []
    for p in TEST_DATA_ROOT.iterdir():
        if not p.is_dir():
            continue
        qa_file = p / "qa_dataset.json"
        if not qa_file.exists():
            continue
        runs_dir = get_project_root(ctx.company_id, ctx.project_id) / "test_runs" / p.name
        run_files = sorted(runs_dir.glob("run-*.json"), reverse=True) if runs_dir.exists() else []
        last_run = None
        last_pass_rate = None
        if run_files:
            try:
                last = json.loads(run_files[0].read_text(encoding="utf-8"))
                last_run = last.get("summary", {}).get("timestamp") or last.get("timestamp")
                last_pass_rate = last.get("summary", {}).get("pass_rate")
            except Exception:
                pass
        projects.append({
            "project": p.name,
            "run_count": len(run_files),
            "last_run": last_run,
            "last_pass_rate": last_pass_rate,
        })
    return projects


@router.get("/{project}/runs")
def list_runs(project: str, ctx: TenantContext = Depends(get_tenant_context)):
    runs_dir = get_project_root(ctx.company_id, ctx.project_id) / "test_runs" / project
    if not runs_dir.exists():
        return {"project": project, "runs": []}
    run_files = sorted(runs_dir.glob("run-*.json"), reverse=True)
    runs = []
    for f in run_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            s = data.get("summary", {})
            runs.append({
                "run_id": data.get("run_id", f.stem),
                "timestamp": s.get("timestamp") or data.get("timestamp", ""),
                "total": s.get("total", 0),
                "passed": s.get("passed", 0),
                "pass_rate": s.get("pass_rate", 0.0),
                "duration_sec": s.get("duration_sec", 0.0),
            })
        except Exception:
            continue
    return {"project": project, "runs": runs}


@router.get("/{project}/runs/{run_id}")
def get_run(project: str, run_id: str, ctx: TenantContext = Depends(get_tenant_context)):
    runs_dir = get_project_root(ctx.company_id, ctx.project_id) / "test_runs" / project
    run_file = runs_dir / f"{run_id}.json"
    if not run_file.exists():
        raise HTTPException(status_code=404, detail=f"실행 결과 없음: {run_id}")
    return json.loads(run_file.read_text(encoding="utf-8"))
