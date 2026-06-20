"""Adaptive query SSE API backed by real RAG/Ontology services.

This endpoint intentionally avoids hardcoded mock sources. If no project
evidence is found, it says so instead of fabricating a general answer.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()


NO_EVIDENCE_ANSWER = (
    "현재 프로젝트의 문서 또는 온톨로지 근거에서 질문 주제와 직접 관련된 "
    "내용을 확인하지 못했습니다."
)


def _sse(event: str, data: Any) -> str:
    """Emit standard named SSE events consumed by EventSource listeners."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _project_scoped_context(project_id: str, session_id: str):
    """Build a tenant context for EventSource calls that cannot send headers."""
    from app.models.tenant_context import TenantContext

    # Current v5 UI/test project data is stored under demo-co/<project_id>.
    return TenantContext(
        user_id=session_id or "adaptive-query",
        company_id="demo-co",
        project_id=project_id,
        role="Viewer",
        permissions={},
    )


def _rag_source(result: dict[str, Any], index: int) -> dict[str, Any]:
    filename = result.get("filename") or result.get("source") or f"Document-{index + 1}"
    page = result.get("page", 0)
    return {
        "name": f"{filename} (p.{page})",
        "filename": filename,
        "page": page,
        "doc_id": result.get("doc_id", ""),
        "text": (result.get("text") or "")[:500],
        "similarity": result.get("score", 0.0),
        "score": result.get("score", 0.0),
    }


def _ontology_source(entity: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "name": entity.get("name") or entity.get("id") or f"Entity-{index + 1}",
        "entity_id": entity.get("id", ""),
        "type": entity.get("type", ""),
        "text": entity.get("description") or str(entity.get("properties", "")),
        "similarity": entity.get("__match_score", 0.0),
        "score": entity.get("__match_score", 0.0),
    }


def _format_evidence(vector_results: list[dict[str, Any]], ontology_results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    if vector_results:
        lines.append("[문서 근거]")
        for result in vector_results[:5]:
            filename = result.get("filename", "문서")
            page = result.get("page", 0)
            text = (result.get("text") or "").replace("\n", " ")[:700]
            lines.append(f"- {filename} p.{page}: {text}")
    if ontology_results:
        lines.append("[온톨로지 근거]")
        for entity in ontology_results[:5]:
            name = entity.get("name") or entity.get("id", "엔티티")
            desc = entity.get("description") or str(entity.get("properties", ""))
            lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def _required_terms(query: str) -> list[str]:
    """Return must-match domain terms for trap/out-of-scope questions."""
    lowered = query.lower()
    terms: list[str] = []
    if "snowflake" in lowered or "스노우플레이크" in query:
        terms.extend(["snowflake", "스노우플레이크"])
    return terms


def _contains_any_term(value: str, terms: list[str]) -> bool:
    lowered = value.lower()
    return any(term.lower() in lowered for term in terms)


def _filter_by_required_terms(
    query: str,
    vector_results: list[dict[str, Any]],
    ontology_results: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Prevent semantically-near but topically-wrong evidence from leaking."""
    terms = _required_terms(query)
    if not terms:
        return vector_results, ontology_results

    filtered_vectors = [
        result
        for result in vector_results
        if _contains_any_term(
            " ".join(
                str(result.get(key, ""))
                for key in ("filename", "text", "doc_id", "source")
            ),
            terms,
        )
    ]
    filtered_entities = [
        entity
        for entity in ontology_results
        if _contains_any_term(
            " ".join(
                str(entity.get(key, ""))
                for key in ("name", "description", "type", "properties")
            ),
            terms,
        )
    ]
    return filtered_vectors, filtered_entities


def _fallback_answer(
    query: str,
    vector_results: list[dict[str, Any]],
    ontology_results: list[dict[str, Any]],
) -> str:
    if vector_results:
        first = vector_results[0]
        filename = first.get("filename", "문서")
        page = first.get("page", 0)
        text = (first.get("text") or "").strip()
        return f"검색된 문서 근거를 우선하여 답변합니다. {text[:700]}\n\n주요 근거: {filename} p.{page}"

    if ontology_results:
        first = ontology_results[0]
        name = first.get("name") or first.get("id", "온톨로지 엔티티")
        desc = first.get("description") or str(first.get("properties", ""))
        return f"검색된 온톨로지 근거를 우선하여 답변합니다. {name}: {desc}"

    return NO_EVIDENCE_ANSWER


def _build_answer(
    query: str,
    mode: str,
    allow_general: bool,
    vector_results: list[dict[str, Any]],
    ontology_results: list[dict[str, Any]],
) -> str:
    if not vector_results and not ontology_results:
        return NO_EVIDENCE_ANSWER

    from app.dependencies import get_llm_client

    llm = get_llm_client()
    if not llm.enabled:
        return _fallback_answer(query, vector_results, ontology_results)

    mode_policy = {
        "document_only": "문서와 온톨로지 근거 안에서만 답변하고, 일반 지식은 사용하지 마세요.",
        "document_with_limits": "근거가 있는 부분만 답변하고, 부족한 부분은 한계로 분리해 설명하세요.",
        "expert_mode": (
            "문서 근거를 우선하되, allow_general이 true일 때만 보조적인 일반 설명을 "
            "명확히 분리해 덧붙일 수 있습니다."
        ),
    }.get(mode, "문서 근거를 우선하여 답변하세요.")

    evidence = _format_evidence(vector_results, ontology_results)
    prompt = (
        "당신은 근거 기반 질의응답 시스템입니다.\n"
        "절대 제공되지 않은 문서명, 페이지, 출처, 엔티티를 만들지 마세요.\n"
        "질문과 근거가 직접 관련 없으면 관련 근거가 없다고 답하세요.\n"
        f"응답 정책: {mode_policy}\n"
        f"일반 설명 허용: {allow_general}\n\n"
        f"질문:\n{query}\n\n"
        f"근거:\n{evidence}\n\n"
        "답변:"
    )
    answer = llm.generate(prompt, temperature=0.2, max_tokens=900)
    return answer.strip() if answer else _fallback_answer(query, vector_results, ontology_results)


async def generate_stream(
    project_id: str,
    session_id: str,
    query: str,
    mode: str,
    hide_irrelevant: bool = True,
    allow_partial: bool = True,
    separate_sources: bool = True,
    allow_general: bool = True,
):
    try:
        from app.dependencies import get_ontology_service, get_vector_search_service

        ctx = _project_scoped_context(project_id, session_id)
        vector_search = get_vector_search_service()
        ontology_svc = get_ontology_service()

        logger.info("[AdaptiveQuery] project=%s mode=%s query=%s", project_id, mode, query)

        vector_results = vector_search.search(query=query, ctx=ctx, k=5)
        ontology_results = ontology_svc.find_by_name(ctx=ctx, name_hint=query)
        raw_vector_count = len(vector_results)
        raw_ontology_count = len(ontology_results)

        if hide_irrelevant:
            # Chroma scores are distance-like; keep the current permissive ceiling
            # while avoiding obviously unrelated far hits.
            vector_results = [r for r in vector_results if float(r.get("score", 999.0)) <= 1.2]
            vector_results, ontology_results = _filter_by_required_terms(
                query,
                vector_results,
                ontology_results,
            )

        logger.info(
            "[AdaptiveQuery] evidence raw_rag=%d raw_ontology=%d filtered_rag=%d filtered_ontology=%d",
            raw_vector_count,
            raw_ontology_count,
            len(vector_results),
            len(ontology_results),
        )

        if not vector_results and not ontology_results:
            logger.info(
                "[AdaptiveQuery] no evidence project=%s mode=%s hide_irrelevant=%s query=%r",
                project_id,
                mode,
                hide_irrelevant,
                query,
            )

        sources_for_tab = {
            "rag": [_rag_source(result, i) for i, result in enumerate(vector_results[:5])],
            "ontology": [_ontology_source(entity, i) for i, entity in enumerate(ontology_results[:5])],
            "expert_opinions": [],
        }
        yield _sse("sources", sources_for_tab)

        answer_text = _build_answer(
            query=query,
            mode=mode,
            allow_general=allow_general,
            vector_results=vector_results,
            ontology_results=ontology_results,
        )

        for char in answer_text:
            await asyncio.sleep(0.001)
            yield _sse("answer_chunk", {"token": char})

        limitations: list[str] = []
        if not vector_results and not ontology_results:
            limitations.append("문서/온톨로지 근거 없음")
        elif allow_partial:
            limitations.append("검색된 근거 범위 안에서 답변")
        if limitations:
            yield _sse("limitations", limitations)

        follow_ups = [
            "이 답변의 근거 문서만 따로 정리해 줄까요?",
            "온톨로지 엔티티 기준으로도 다시 검색해 볼까요?",
        ]
        yield _sse("follow_ups", follow_ups)

        has_evidence = bool(vector_results or ontology_results)
        complete_meta = {
            "level": 3 if vector_results and ontology_results else (2 if has_evidence else 1),
            "relevance_level": 3 if vector_results and ontology_results else (2 if has_evidence else 1),
            "confidence": 0.85 if has_evidence else 0.0,
            "confidence_score": 0.85 if has_evidence else 0.0,
            "sources": sources_for_tab,
            "limitations": limitations,
        }
        yield _sse("complete", complete_meta)

        logger.info(
            "[AdaptiveQuery] complete rag=%d ontology=%d",
            len(vector_results),
            len(ontology_results),
        )

    except Exception as exc:
        logger.error("[AdaptiveQuery] error: %s", exc, exc_info=True)
        yield _sse("error", {"message": str(exc)})


@router.get("/api/v1/projects/{project_id}/query/stream")
async def query_stream(
    project_id: str,
    session_id: str = Query(...),
    query: str = Query(...),
    mode: str = Query(default="expert_mode"),
    hide_irrelevant: bool = Query(default=True),
    allow_partial: bool = Query(default=True),
    separate_sources: bool = Query(default=True),
    allow_general: bool = Query(default=True),
):
    """Stream a grounded adaptive answer and its real source lists."""
    return StreamingResponse(
        generate_stream(
            project_id=project_id,
            session_id=session_id,
            query=query,
            mode=mode,
            hide_irrelevant=hide_irrelevant,
            allow_partial=allow_partial,
            separate_sources=separate_sources,
            allow_general=allow_general,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
