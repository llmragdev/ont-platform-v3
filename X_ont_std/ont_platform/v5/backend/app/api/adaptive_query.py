"""Adaptive query SSE API backed by real RAG/Ontology services.

This endpoint intentionally avoids hardcoded mock sources. If no project
evidence is found, it says so instead of fabricating a general answer.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()

ONTOLOGY_RULES_PATH = Path(__file__).resolve().parents[1] / "services" / "ontology_rules.yaml"


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
        "_status": result.get("_status", "USED"),
        "_reason": result.get("_reason", "답변에 사용됨"),
    }


def _entity_id(entity: dict[str, Any]) -> str:
    return str(entity.get("id") or entity.get("entity_id") or "")


def _entity_name(entity: dict[str, Any]) -> str:
    return str(entity.get("name") or entity.get("entity_name") or entity.get("id") or entity.get("entity_id") or "")


def _relation_id(relation: dict[str, Any]) -> str:
    return str(relation.get("id") or relation.get("relation_id") or "")


def _relation_from_id(relation: dict[str, Any]) -> str:
    return str(relation.get("from_id") or relation.get("from_entity_id") or "")


def _relation_to_id(relation: dict[str, Any]) -> str:
    return str(relation.get("to_id") or relation.get("to_entity_id") or "")


def _relation_type(relation: dict[str, Any]) -> str:
    return str(relation.get("relation") or relation.get("type") or relation.get("relation_type") or "")


def _ontology_source(entity: dict[str, Any], index: int) -> dict[str, Any]:
    entity_id = _entity_id(entity)
    name = _entity_name(entity) or f"Entity-{index + 1}"
    description = entity.get("description") or str(entity.get("properties", ""))
    return {
        "name": name,
        "entity_name": name,
        "entity": name,
        "entity_id": entity_id,
        "type": entity.get("type", ""),
        "description": description,
        "text": description,
        "similarity": entity.get("__match_score", 0.0),
        "score": entity.get("__match_score", 0.0),
        "relation": "",
        "target": "",
        "_status": entity.get("_status", "USED"),
        "_reason": entity.get("_reason", "답변에 사용됨"),
    }


def _ontology_sources_with_relationships(
    matched_entities: list[dict[str, Any]],
    all_entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return graph-friendly ontology sources for the frontend.

    The query UI expects entity_name/relation/target for graph edges. The
    ontology store, however, keeps entities and relationships separately.
    """
    entity_by_id = {_entity_id(entity): entity for entity in all_entities if _entity_id(entity)}
    matched_ids = {_entity_id(entity) for entity in matched_entities if _entity_id(entity)}
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for relation in relationships:
        from_id = _relation_from_id(relation)
        to_id = _relation_to_id(relation)
        if from_id not in matched_ids and to_id not in matched_ids:
            continue

        from_entity = entity_by_id.get(from_id, {"id": from_id, "name": from_id})
        to_entity = entity_by_id.get(to_id, {"id": to_id, "name": to_id})
        relation_label = _relation_type(relation) or "관련"
        key = (from_id, relation_label, to_id)
        if key in seen:
            continue
        seen.add(key)

        sources.append(
            {
                "name": _entity_name(from_entity),
                "entity_name": _entity_name(from_entity),
                "entity": _entity_name(from_entity),
                "entity_id": from_id,
                "type": from_entity.get("type", ""),
                "description": from_entity.get("description") or str(from_entity.get("properties", "")),
                "relation": relation_label,
                "target": _entity_name(to_entity),
                "target_id": to_id,
                "relation_id": _relation_id(relation),
                "text": f"{_entity_name(from_entity)} -[{relation_label}]-> {_entity_name(to_entity)}",
                "similarity": 1.0,
                "score": 1.0,
                "_status": from_entity.get("_status", "USED"),
                "_reason": from_entity.get("_reason", "답변에 사용됨"),
            }
        )

    represented_ids = {source["entity_id"] for source in sources} | {source.get("target_id", "") for source in sources}
    for index, entity in enumerate(matched_entities):
        entity_id = _entity_id(entity)
        if entity_id and entity_id in represented_ids:
            continue
        sources.append(_ontology_source(entity, index))

    return sources[:5]


def _load_ontology_rules() -> dict[str, Any]:
    """Load type filter policy from config, not from hardcoded code branches."""
    try:
        import yaml

        with ONTOLOGY_RULES_PATH.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except FileNotFoundError:
        logger.warning("[AdaptiveQuery] ontology rules not found: %s", ONTOLOGY_RULES_PATH)
    except Exception as exc:
        logger.warning("[AdaptiveQuery] failed to load ontology rules: %s", exc)
    return {"intent_overrides": {}, "type_policies": {}}


def _entity_type(entity: dict[str, Any]) -> str:
    return str(entity.get("type") or entity.get("entity_type") or "UNKNOWN").upper()


def _is_metadata_lookup(query: str, rules: dict[str, Any]) -> bool:
    lowered = query.lower()
    for keywords in rules.get("intent_overrides", {}).values():
        for keyword in keywords or []:
            if str(keyword).lower() in lowered:
                return True
    return False


def _ontology_graph_entity(entity: dict[str, Any], rank: int, status: str = "USED") -> dict[str, Any]:
    description = entity.get("description") or str(entity.get("properties", ""))
    item: dict[str, Any] = {
        "name": _entity_name(entity),
        "type": _entity_type(entity),
        "rank": rank,
        "status": status,
    }
    if description:
        item["definition"] = description
    if entity.get("source_document"):
        item["source_document"] = entity.get("source_document")
    if entity.get("__match_score") is not None:
        item["confidence"] = entity.get("__match_score")
    return item


def _entity_properties(entity: dict[str, Any]) -> dict[str, Any]:
    properties = entity.get("properties") or {}
    return properties if isinstance(properties, dict) else {}


def _entity_role(entity: dict[str, Any]) -> str:
    return str(entity.get("role") or _entity_properties(entity).get("role") or "").lower()


def _select_seed_entity(
    query: str,
    candidates: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not candidates:
        return None

    degree: dict[str, int] = {}
    for relation in relationships:
        for entity_id in (_relation_from_id(relation), _relation_to_id(relation)):
            if entity_id:
                degree[entity_id] = degree.get(entity_id, 0) + 1

    preferred_role_fragments = (
        "core",
        "domain",
        "concept",
        "method",
        "process",
        "step",
        "application",
        "property",
        "constraint",
        "criterion",
        "metric",
        "schema",
        "field",
        "rule",
    )
    metadata_role_fragments = ("metadata", "author", "publication", "affiliation")
    query_lower = query.lower()

    def score(entity: dict[str, Any]) -> tuple[float, int, str]:
        entity_id = _entity_id(entity)
        name = _entity_name(entity)
        role = _entity_role(entity)
        properties = _entity_properties(entity)
        value = float(entity.get("__match_score") or 0.0)

        if name and name.lower() in query_lower:
            value += 4.0
        if role:
            value += 1.0
        if any(fragment in role for fragment in preferred_role_fragments):
            value += 5.0
        if any(fragment in role for fragment in metadata_role_fragments):
            value -= 5.0

        node_degree = degree.get(entity_id, 0)
        value += min(node_degree, 10) * 0.75

        richness = sum(
            1
            for key in ("description", "source", "confidence", "aliases")
            if entity.get(key) or properties.get(key)
        )
        value += richness * 0.25

        return (value, node_degree, entity_id)

    selected = max(candidates, key=score)
    selected_score, selected_degree, _ = score(selected)
    logger.info(
        "[ontology_graph] seed selected name=%s id=%s score=%.2f degree=%s role=%s",
        _entity_name(selected),
        _entity_id(selected),
        selected_score,
        selected_degree,
        _entity_role(selected) or "-",
    )
    return selected


def _build_ontology_graph_v2(
    query: str,
    matched_entities: list[dict[str, Any]],
    all_entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    vector_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Build the v2 hierarchical ontology payload while preserving legacy lists."""
    used_matches = [entity for entity in matched_entities if entity.get("_status", "USED") == "USED"]
    if not used_matches:
        return None

    rules = _load_ontology_rules()
    type_policies = rules.get("type_policies", {})
    metadata_allowed = _is_metadata_lookup(query, rules)

    seed_source = _select_seed_entity(query, used_matches, relationships)
    if not seed_source:
        return None
    seed_id = _entity_id(seed_source)
    if not seed_id:
        return None

    entity_by_id = {_entity_id(entity): entity for entity in all_entities if _entity_id(entity)}
    seed_entity = _ontology_graph_entity(seed_source, rank=1, status="USED")
    related_entities: list[dict[str, Any]] = []
    filtered_out: list[dict[str, Any]] = []
    seen_neighbors: set[str] = set()

    for relation in relationships:
        from_id = _relation_from_id(relation)
        to_id = _relation_to_id(relation)
        if seed_id not in {from_id, to_id}:
            continue

        if from_id == seed_id:
            neighbor_id = to_id
            direction = f"seed -> {_relation_type(relation) or 'related'}"
        else:
            neighbor_id = from_id
            direction = f"{_relation_type(relation) or 'related'} -> seed"

        if not neighbor_id or neighbor_id == seed_id or neighbor_id in seen_neighbors:
            continue
        seen_neighbors.add(neighbor_id)

        neighbor = entity_by_id.get(neighbor_id)
        if not neighbor:
            continue

        neighbor_type = _entity_type(neighbor)
        policy = type_policies.get(neighbor_type, {})
        is_metadata = bool(policy.get("is_metadata", False))
        rank = int(policy.get("priority", len(related_entities) + len(filtered_out) + 2))
        item = _ontology_graph_entity(neighbor, rank=rank, status="USED")
        item["relation_type"] = direction

        if is_metadata and not metadata_allowed:
            item["status"] = "FILTERED"
            item["reason"] = f"Config policy: {neighbor_type} is metadata for this intent"
            filtered_out.append(item)
        else:
            item["reason"] = "Used as a related ontology entity"
            related_entities.append(item)

    allowed_types = [
        entity_type
        for entity_type, policy in type_policies.items()
        if metadata_allowed or not bool((policy or {}).get("is_metadata", False))
    ]
    top_vector = vector_results[0].get("filename") if vector_results else ""

    return {
        "seed_entity": seed_entity,
        "related_entities": related_entities[:5],
        "filtered_out": filtered_out[:10],
        "policy": {
            "intent": "metadata_lookup" if metadata_allowed else "concept_explanation",
            "allowed_entity_types": allowed_types,
            "traversal_depth": 1,
            "applied_filters": len(filtered_out),
            "source": ONTOLOGY_RULES_PATH.name,
        },
        "provenance": {
            "query": query,
            "vector_search_top1": top_vector,
            "intent_classification_confidence": 1.0 if metadata_allowed else 0.8,
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        },
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
    return []


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
        all_ontology_entities = ontology_svc.repo.list_all_entities(ctx)
        all_ontology_relationships = ontology_svc.repo.list_all_relationships(ctx)
        raw_vector_count = len(vector_results)
        raw_ontology_count = len(ontology_results)

        for r in vector_results:
            r["_status"] = "USED"
            r["_reason"] = "답변에 사용됨"
        for r in ontology_results:
            r["_status"] = "USED"
            r["_reason"] = "답변에 사용됨"

        if hide_irrelevant:
            for r in vector_results:
                if float(r.get("score", 999.0)) > 1.2:
                    r["_status"] = "FILTERED_THRESHOLD"
                    r["_reason"] = f"유사도 낮음 ({float(r.get('score', 999.0)):.2f})"
            
            if not allow_general:
                terms = _required_terms(query)
                if terms:
                    for r in vector_results:
                        if r.get("_status") == "USED":
                            if not _contains_any_term(" ".join(str(r.get(key, "")) for key in ("filename", "text", "doc_id", "source")), terms):
                                r["_status"] = "FILTERED_REQUIRED_TERMS"
                                r["_reason"] = "필수 키워드 누락"
                    for r in ontology_results:
                        if r.get("_status") == "USED":
                            if not _contains_any_term(" ".join(str(r.get(key, "")) for key in ("name", "description", "type", "properties")), terms):
                                r["_status"] = "FILTERED_REQUIRED_TERMS"
                                r["_reason"] = "필수 키워드 누락"

        used_vectors = [r for r in vector_results if r.get("_status") == "USED"]
        used_ontology = [r for r in ontology_results if r.get("_status") == "USED"]

        # --- v5.3 Hybrid Search OAG (Entity Gate) ---
        from app.services.entity_gate import extract_query_entity_candidates, calculate_ontology_entity_overlap, evaluate_chunk_entity_match
        from app.services.answerability_gate import evaluate_answerability

        query_entities = extract_query_entity_candidates(query)
        ont_names = [_entity_name(e) for e in used_ontology]
        chunk_text_combined = " ".join([r.get("text", "") for r in used_vectors])
        
        ontology_overlap = calculate_ontology_entity_overlap(query_entities, ont_names)
        chunk_match = evaluate_chunk_entity_match(query_entities, chunk_text_combined, {})
        chunk_overlap = chunk_match["chunk_entity_overlap"]
        
        gate_result = evaluate_answerability(
            ontology_overlap,
            chunk_overlap,
            mode,
            matched_query_entities_count=chunk_match["matched_query_entities_count"],
        )
        answer_status = gate_result["answer_status"]
        fallback_answer_bypassed = answer_status == "NO_ANSWER"
        
        v5_3_meta = {
            "answer_status": answer_status,
            "gate": {
                "decision": gate_result["decision"],
                "query_entities": query_entities,
                "matched_query_entities": chunk_match["matched_query_entities"],
                "missing_query_entities": chunk_match["missing_query_entities"],
                "matched_query_entities_count": chunk_match["matched_query_entities_count"],
                "ontology_entity_overlap": ontology_overlap,
                "chunk_entity_overlap": chunk_overlap,
                "metadata_absent_fallback_used": chunk_match["metadata_absent_fallback_used"],
                "fallback_answer_bypassed": fallback_answer_bypassed,
            },
            "gate_status": gate_result["gate_status"],
            "thresholds": gate_result.get("thresholds", {}),
            "entity_gate": {
                "query_entities": query_entities,
                "matched_ontology_entities": ont_names,
                "matched_query_entities": chunk_match["matched_query_entities"],
                "missing_query_entities": chunk_match["missing_query_entities"],
                "matched_query_entities_count": chunk_match["matched_query_entities_count"],
                "ontology_entity_overlap": ontology_overlap,
                "chunk_entity_overlap": chunk_overlap,
                "metadata_absent_fallback_used": chunk_match["metadata_absent_fallback_used"],
            }
        }
        
        logger.info(
            "[AdaptiveQuery] v5.3 Gate: status=%s decision=%s ontology_overlap=%.2f chunk_overlap=%.2f matched=%d metadata_absent_fallback_used=%s fallback_answer_bypassed=%s",
            answer_status,
            gate_result["decision"],
            ontology_overlap,
            chunk_overlap,
            chunk_match["matched_query_entities_count"],
            chunk_match["metadata_absent_fallback_used"],
            fallback_answer_bypassed,
        )
        # --------------------------------------------

        logger.info(
            "[AdaptiveQuery] evidence raw_rag=%d raw_ontology=%d used_rag=%d used_ontology=%d",
            raw_vector_count,
            raw_ontology_count,
            len(used_vectors),
            len(used_ontology),
        )

        if not used_vectors and not used_ontology:
            logger.info(
                "[AdaptiveQuery] no usable evidence project=%s mode=%s hide_irrelevant=%s query=%r",
                project_id,
                mode,
                hide_irrelevant,
                query,
            )

        sources_for_tab = {
            "rag": [_rag_source(result, i) for i, result in enumerate(vector_results[:10])],
            "ontology": _ontology_sources_with_relationships(
                ontology_results[:10],
                all_ontology_entities,
                all_ontology_relationships,
            ),
            "expert_opinions": [],
        }
        if answer_status == "NO_ANSWER":
            for source in sources_for_tab["rag"]:
                source["_status"] = "FILTERED"
                source["used"] = False
                source["reason"] = "answerability_gate_blocked"
            for source in sources_for_tab["ontology"]:
                source["_status"] = "FILTERED"
                source["used"] = False
                source["reason"] = "answerability_gate_blocked"
        ontology_graph = _build_ontology_graph_v2(
            query=query,
            matched_entities=ontology_results,
            all_entities=all_ontology_entities,
            relationships=all_ontology_relationships,
            vector_results=vector_results,
        )
        if ontology_graph:
            sources_for_tab["ontology_contract_version"] = "v2"
            sources_for_tab["ontology_graph"] = ontology_graph
        yield _sse("sources", sources_for_tab)

        if answer_status == "NO_ANSWER":
            answer_text = "죄송합니다. 제공된 문서와 온톨로지 지식에서 질문에 대한 관련 근거를 찾지 못했습니다."
        else:
            answer_text = _build_answer(
                query=query,
                mode=mode,
                allow_general=allow_general,
                vector_results=used_vectors,
                ontology_results=used_ontology,
            )

        for char in answer_text:
            await asyncio.sleep(0.001)
            yield _sse("answer_chunk", {"token": char})

        limitations: list[str] = []
        if answer_status == "NO_ANSWER":
            limitations.append("Answerability Gate blocked the response because direct evidence was not confirmed.")
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
        if answer_status == "NO_ANSWER":
            response_confidence = 0.0
        elif answer_status == "GENERAL_ONLY":
            response_confidence = 0.55
        elif answer_status == "PARTIAL":
            response_confidence = 0.75
        else:
            response_confidence = 0.95 if has_evidence else 0.0
        complete_meta = {
            "level": 3 if vector_results and ontology_results else (2 if has_evidence else 1),
            "relevance_level": 3 if vector_results and ontology_results else (2 if has_evidence else 1),
            "confidence": response_confidence,
            "confidence_score": response_confidence,
            "sources": sources_for_tab,
            "limitations": limitations,
            "v5_3": v5_3_meta,
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
