from __future__ import annotations

import json
import os
import shutil
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "ont_platform").exists())
V4_BACKEND = ROOT / "ont_platform" / "v4" / "backend"
RESULTS_DIR = ROOT / "validation" / "ont_platform_v4_eval" / "results" / "previous30"
QUERY_FILE = ROOT / "validation" / "comparison_team0_phase1" / "test_queries.json"
TARGET_DOC_DIR = Path("E:/ai_lab_SIT/target_doc")
V3_ENV = ROOT / "ont_platform" / "v3" / ".env"

COMPANY_ID = "codex_eval"
PROJECT_ID = "ont_platform_v4_pdf8"
HEADERS = {
    "X-User-ID": "codex-evaluator",
    "X-Company-ID": COMPANY_ID,
    "X-Project-ID": PROJECT_ID,
    "X-Role": "Admin",
}


GOLDEN_KEYWORDS = {
    "온톨로지란 무엇인가?": ["온톨로지", "지식", "개념", "관계", "명세"],
    "온톨로지와 지식그래프의 관계는?": ["온톨로지", "지식그래프", "의미", "관계", "시맨틱"],
    "온톨로지 매칭이란 무엇인가?": ["매칭", "이질성", "매핑", "유사도", "정렬"],
    "온톨로지 이질성 문제는?": ["이질성", "구문", "의미", "해결", "스키마"],
    "도메인 온톨로지 모델링 방법은?": ["모델링", "도메인", "구축", "설계", "단계"],
    "온톨로지 기반 의미 속성 판별이란?": ["의미", "속성", "판별", "감성", "텍스트"],
    "온톨로지 학습 기반 지식 그래프 구축 방법은?": ["학습", "지식그래프", "구축", "자동", "추출"],
    "RDF는 무엇인가?": ["RDF", "자원", "기술", "트리플", "주어"],
    "온톨로지 관리 및 유지보수 방법은?": ["관리", "유지보수", "갱신", "버전", "일관성"],
    "온톨로지의 평가 지표는?": ["평가", "지표", "품질", "일관성", "완전성"],
    "온톨로지 재사용 전략은?": ["재사용", "전략", "모듈", "가져오기", "표준"],
    "온톨로지 국제 표준은?": ["표준", "OWL", "W3C", "RDF", "국제"],
    "자연어처리(NLP)란?": ["자연어처리", "NLP", "텍스트", "언어", "이해"],
    "정적 언어모델과 생성형AI의 차이는?": ["정적", "생성형", "차이", "맥락", "확률"],
    "생성형AI의 발전 과정은?": ["생성형", "발전", "GPT", "트랜스포머", "모델"],
    "텍스트를 다시 쓰는 기술(Paraphrasing)이란?": ["다시", "Paraphrasing", "문장", "재작성", "의미"],
    "한국근대문인 데이터베이스 구축 방법은?": ["근대문인", "데이터베이스", "구축", "인물", "아카이브"],
    "실시간 문맥 인식 감성 분석이란?": ["문맥", "실시간", "감성", "분석", "모듈"],
    "감성 분석의 모듈형 아키텍처 설계란?": ["모듈", "아키텍처", "설계", "감성", "유연성"],
    "NLP에서의 감정 판별 기법은?": ["감정", "판별", "기법", "사전", "기계학습"],
    "언어모델의 문맥 이해 방식은?": ["문맥", "이해", "어텐션", "트랜스포머", "의미"],
    "대규모 언어모델의 학습 방식은?": ["대규모", "학습", "사전학습", "미세조정", "가중치"],
    "NLP의 주요 응용 분야는?": ["응용", "번역", "챗봇", "요약", "검색"],
    "자연어 이해와 생성의 차이는?": ["이해", "생성", "차이", "NLU", "NLG"],
    "국방 분야에서 온톨로지를 어떻게 활용하는가?": ["국방", "지휘통제", "데이터", "통합", "의사결정"],
    "국방 지휘통제 데이터 통합 방법은?": ["지휘통제", "데이터", "통합", "온톨로지", "상호운용성"],
    "온톨로지와 지식그래프를 국방에 적용하는 방법은?": ["국방", "온톨로지", "지식그래프", "적용", "체계"],
    "해외 온톨로지 현황은?": ["해외", "현황", "미국", "국방성", "NATO"],
    "한국군 온톨로지 개발 방안은?": ["한국군", "개발", "방안", "표준화", "국방"],
    "지식그래프 기반 국방 정보 통합은?": ["지식그래프", "국방", "정보", "통합", "상호운용"],
}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if " #" in value:
            value = value.split(" #", 1)[0].strip()
        if "  " in value:
            value = value.split("  ", 1)[0].strip()
        if key and value and key not in os.environ:
            os.environ[key] = value
    # The shared v3 .env may annotate GEMINI_API_KEY with Korean comments.
    # Prefer a clean numbered key if the default key is not the expected shape.
    default_key = os.environ.get("GEMINI_API_KEY", "")
    if len(default_key) > 45:
        for name in ("GEMINI_API_KEY1", "GEMINI_API_KEY2", "GEMINI_API_KEY3", "GEMINI_API_KEY4"):
            candidate = os.environ.get(name, "")
            if candidate.startswith("AIza") and len(candidate) <= 45:
                os.environ["GEMINI_API_KEY"] = candidate
                break


def load_queries() -> list[dict[str, str]]:
    data = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for category in ("ontology", "nlp", "defense"):
        for query in data[category]:
            rows.append({"category": category, "query": query})
    return rows


def target_pdfs() -> list[Path]:
    pdfs = sorted(p for p in TARGET_DOC_DIR.glob("*.pdf"))
    return pdfs


def clean_eval_storage() -> None:
    sys.path.insert(0, str(V4_BACKEND))
    from storage_config import get_project_root

    project_root = get_project_root(COMPANY_ID, PROJECT_ID)
    if project_root.exists():
        shutil.rmtree(project_root)


def create_client():
    sys.path.insert(0, str(V4_BACKEND))
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def upload_pdfs(client) -> list[dict[str, Any]]:
    uploads = []
    for pdf in target_pdfs():
        started = time.perf_counter()
        with pdf.open("rb") as fh:
            response = client.post(
                "/api/documents/upload",
                headers=HEADERS,
                files={"file": (pdf.name, fh, "application/pdf")},
                data={"shard_id": "default"},
                timeout=180,
            )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        item = {
            "filename": pdf.name,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        }
        try:
            item["response"] = response.json()
        except Exception:
            item["response"] = {"text": response.text[:500]}
        uploads.append(item)
        print(f"UPLOAD {len(uploads)}/8 {pdf.name} status={response.status_code} elapsed_ms={elapsed_ms}")
    return uploads


def normalize_relevance(raw_scores: list[float]) -> float:
    if not raw_scores:
        return 0.3
    # Chroma returns distance-like scores, so lower is better. This maps the
    # observed distance into a bounded relevance proxy for the legacy rubric.
    converted = [1.0 / (1.0 + max(0.0, s)) for s in raw_scores]
    avg = sum(converted) / len(converted)
    if avg >= 0.5:
        return 1.0
    if avg >= 0.4:
        return 0.8
    if avg >= 0.3:
        return 0.6
    return 0.4


def evaluate_query(query: str, answer: str, raw_scores: list[float]) -> dict[str, Any]:
    keywords = GOLDEN_KEYWORDS[query]
    keyword_ratio = sum(1 for kw in keywords if kw in answer) / len(keywords)
    answer_len = len(answer)
    if answer_len >= 300:
        completeness = 1.0
    elif answer_len >= 150:
        completeness = 0.7
    elif answer_len >= 50:
        completeness = 0.4
    else:
        completeness = 0.1
    relevance = normalize_relevance(raw_scores)
    score = keyword_ratio * 0.4 + completeness * 0.3 + relevance * 0.3
    return {
        "keyword_presence_ratio": round(keyword_ratio, 3),
        "answer_completeness": round(completeness, 3),
        "answer_relevance": round(relevance, 3),
        "accuracy_score": round(score, 4),
    }


def run_queries(client, queries: list[dict[str, str]]) -> list[dict[str, Any]]:
    results = []
    for idx, item in enumerate(queries, start=1):
        query = item["query"]
        started = time.perf_counter()
        try:
            response = client.post(
                "/api/hybrid/ask",
                headers=HEADERS,
                json={"question": query},
                timeout=180,
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            payload = response.json()
            status = "success" if response.status_code == 200 else "error"
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            payload = {"error": type(exc).__name__, "detail": str(exc)}
            status = "error"
            response = None

        vector_items = (
            payload.get("structured_data", {})
            .get("vector", {})
            .get("items", [])
            if isinstance(payload, dict)
            else []
        )
        raw_scores = [float(v.get("score", 0.0)) for v in vector_items if isinstance(v, dict)]
        answer = payload.get("answer", "") if isinstance(payload, dict) else ""
        evaluation = evaluate_query(query, answer, raw_scores)
        result = {
            "query": query,
            "category": item["category"],
            "status": status,
            "status_code": response.status_code if response is not None else None,
            "elapsed_ms": elapsed_ms,
            "answer": answer,
            "used_chunks": [
                {
                    "text": v.get("text", ""),
                    "raw_score": v.get("score"),
                    "doc_id": v.get("doc_id", ""),
                    "filename": v.get("filename", ""),
                    "page": v.get("page"),
                }
                for v in vector_items
                if isinstance(v, dict)
            ],
            "quality_metrics": payload.get("quality_metrics", {}) if isinstance(payload, dict) else {},
            "trace": payload.get("trace", []) if isinstance(payload, dict) else [],
            "evaluation": evaluation,
            "data": payload,
        }
        results.append(result)
        print(
            f"QUERY {idx}/{len(queries)} status={status} "
            f"score={evaluation['accuracy_score']:.4f} elapsed_ms={elapsed_ms} q={query}"
        )
    return results


def performance(results: list[dict[str, Any]]) -> dict[str, Any]:
    times = [r["elapsed_ms"] for r in results]
    success = [r for r in results if r["status"] == "success"]
    sorted_times = sorted(times)

    def percentile(p: float) -> float:
        if not sorted_times:
            return 0.0
        k = (len(sorted_times) - 1) * p
        lower = int(k)
        upper = min(lower + 1, len(sorted_times) - 1)
        if lower == upper:
            return sorted_times[lower]
        return sorted_times[lower] + (sorted_times[upper] - sorted_times[lower]) * (k - lower)

    return {
        "success_rate": round(len(success) / len(results), 4) if results else 0.0,
        "avg_response_time_ms": round(statistics.mean(times), 2) if times else 0.0,
        "min_response_time_ms": round(min(times), 2) if times else 0.0,
        "max_response_time_ms": round(max(times), 2) if times else 0.0,
        "p50_response_time_ms": round(percentile(0.50), 2),
        "p95_response_time_ms": round(percentile(0.95), 2),
        "p99_response_time_ms": round(percentile(0.99), 2),
    }


def accuracy(results: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [r["evaluation"]["accuracy_score"] for r in results]
    by_category = {}
    for category in ("ontology", "nlp", "defense"):
        cat_scores = [r["evaluation"]["accuracy_score"] for r in results if r["category"] == category]
        by_category[category] = round(sum(cat_scores) / len(cat_scores), 4) if cat_scores else 0.0
    return {
        "overall_accuracy": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "by_category": by_category,
        "queries": [
            {
                "query": r["query"],
                "category": r["category"],
                **r["evaluation"],
            }
            for r in results
        ],
    }


def write_summary(uploads, results, acc, perf) -> None:
    total_chunks = sum((u.get("response") or {}).get("chunk_count", 0) for u in uploads)
    llm_used = sum(1 for r in results if r.get("quality_metrics", {}).get("llm_used"))
    vector_hits = sum(r.get("quality_metrics", {}).get("vector_hits", 0) for r in results)
    content = f"""ont_platform v4 RAG Validation Metrics Summary
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Target: ont_platform v4 /api/hybrid/ask
Tenant: {COMPANY_ID}/{PROJECT_ID}
Total Documents: {len(uploads)} PDFs
Total Uploaded Chunks: {total_chunks}
Total Queries: {len(results)} standardized queries

Measured Performance:
- Overall Accuracy: {acc['overall_accuracy'] * 100:.2f}%
- API Success Rate: {perf['success_rate'] * 100:.1f}%
- Avg Response Time: {perf['avg_response_time_ms']} ms
- Min Response Time: {perf['min_response_time_ms']} ms
- Max Response Time: {perf['max_response_time_ms']} ms
- P50 Response Time: {perf['p50_response_time_ms']} ms
- P95 Response Time: {perf['p95_response_time_ms']} ms
- P99 Response Time: {perf['p99_response_time_ms']} ms

Category Accuracy:
- Ontology: {acc['by_category']['ontology'] * 100:.2f}%
- NLP & Generative AI: {acc['by_category']['nlp'] * 100:.2f}%
- Defense: {acc['by_category']['defense'] * 100:.2f}%

Execution Evidence:
- LLM Used Queries: {llm_used}/{len(results)}
- Total Vector Hits: {vector_hits}
- Evaluation Type: direct execution, not simulation
"""
    (RESULTS_DIR / "summary.txt").write_text(content, encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    load_env_file(V3_ENV)
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")):
        print("ERROR: GEMINI_API_KEY/GEMINI_API_KEY1 is not available; v4 vector evaluation cannot run.")
        return 2
    queries = load_queries()
    pdfs = target_pdfs()
    if len(pdfs) != 8:
        print(f"ERROR: expected 8 PDFs, found {len(pdfs)} in {TARGET_DOC_DIR}")
        return 2

    clean_eval_storage()
    client = create_client()
    uploads = upload_pdfs(client)
    total_chunks = sum((u.get("response") or {}).get("chunk_count", 0) for u in uploads)
    if total_chunks <= 0:
        print("ERROR: upload completed but no chunks were vectorized.")
        (RESULTS_DIR / "upload_results.json").write_text(json.dumps(uploads, ensure_ascii=False, indent=2), encoding="utf-8")
        return 3

    results = run_queries(client, queries)
    acc = accuracy(results)
    perf = performance(results)

    detailed = {
        "metadata": {
            "test_date": datetime.now().strftime("%Y-%m-%d"),
            "platform": "ont_platform_v4",
            "endpoint": "/api/hybrid/ask",
            "pdf_count": len(uploads),
            "query_count": len(results),
            "chunk_count": total_chunks,
            "tenant": {"company_id": COMPANY_ID, "project_id": PROJECT_ID},
            "evaluation_type": "direct_execution",
        },
        "results": {
            "accuracy": acc,
            "performance": perf,
            "by_query": acc["queries"],
        },
        "uploads": uploads,
    }

    (RESULTS_DIR / "upload_results.json").write_text(json.dumps(uploads, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / "test_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / "accuracy_report.json").write_text(json.dumps(acc, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / "performance_report.json").write_text(json.dumps(perf, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / "detailed_results.json").write_text(json.dumps(detailed, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(uploads, results, acc, perf)
    print(json.dumps({"accuracy": acc["overall_accuracy"], "performance": perf, "chunks": total_chunks}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
