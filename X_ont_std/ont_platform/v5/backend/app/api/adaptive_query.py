"""
Adaptive Query API with SSE streaming
v5 RAG + Ontology hybrid system

Fixed (2026-06-20):
- Removed hardcoded unrelated general explanations
- Removed source file/page listing from answer body
- Fixed confidence/level metadata mapping
- Added document chunk sentence extraction for answer synthesis
- Separated concerns: RAG sources via SSE, answer body via synthesis
- Use mock data for testing
"""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


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
    """
    Generate answer via SSE with proper document grounding (Mock Version).

    Modes:
    - document_only: Only document-based answers, no general knowledge
    - document_with_limits: Document + caveats about limits
    - expert_mode: Document + general knowledge integration

    Separated concerns:
    - RAG sources → sources event (displayed in RAG tab)
    - Answer body → token events (constructed from document chunks)
    - Limitations → limitations event
    """

    try:
        # Mock RAG results (질문별로 다른 응답)
        if "Class" in query or "Property" in query:
            rag_chunks = [
                {"source": "NLP - [03] OWL 온톨로지 설계 가이드 - 2025.pdf", "page": 15, "text": "Class는 OWL에서 개념을 정의하는 기본 요소이고, Property는 클래스 간의 관계와 속성을 표현합니다."},
                {"source": "온톨로지 기초 - [01] Class vs Property - 2025.pdf", "page": 3, "text": "Class는 개념의 정의이며, Property는 개념의 특성을 나타내는 속성입니다."},
            ]
            ontology_entities = [
                {"entity_id": "class_def", "name": "Class", "definition": "개념을 정의하는 기본 단위"},
                {"entity_id": "property_def", "name": "Property", "definition": "개념의 속성과 관계를 정의"},
            ]
        elif "매칭 성능" in query or "지표" in query:
            rag_chunks = [
                {"source": "RAG 성능 평가 - [04] 성능 지표 분석 - 2025.pdf", "page": 22, "text": "매칭 성능은 Precision, Recall, F1-Score 등의 지표로 평가합니다."},
                {"source": "온톨로지 평가 - [02] 정확도 측정 - 2025.pdf", "page": 8, "text": "온톨로지 매칭 성능은 의미 유사도, 구조적 유사도, 통합 스코어로 측정됩니다."},
            ]
            ontology_entities = [
                {"entity_id": "precision", "name": "Precision", "definition": "검색 결과의 정확성"},
                {"entity_id": "recall", "name": "Recall", "definition": "검색 완전성"},
            ]
        elif "Snowflake" in query or "응답 시간" in query:
            rag_chunks = [
                {"source": "Snowflake QA - [05] 성능 최적화 - 2025.pdf", "page": 34, "text": "Snowflake 환경에서는 응답 시간과 운영 제약(비용, 병렬화)을 함께 고려하여 쿼리를 최적화해야 합니다."},
                {"source": "데이터 웨어하우스 운영 - [03] 비용-성능 트레이드오프 - 2025.pdf", "page": 11, "text": "빠른 응답과 저비용 운영은 상충관계이므로 SLA에 맞는 균형점을 찾아야 합니다."},
            ]
            ontology_entities = [
                {"entity_id": "latency", "name": "응답시간", "definition": "쿼리 처리 시간"},
                {"entity_id": "cost", "name": "운영비용", "definition": "데이터 처리 비용"},
            ]
        else:
            # Default
            rag_chunks = [
                {"source": "일반 - [00] 온톨로지 개요 - 2025.pdf", "page": 1, "text": "온톨로지는 지식 표현과 추론의 기본 구조입니다."},
            ]
            ontology_entities = []

        # 근거 판정
        has_rag_evidence = len(rag_chunks) > 0
        has_ontology_evidence = len(ontology_entities) > 0 and allow_general

        # RAG 출처 이벤트 (RAG 탭에서 표시)
        sources_for_tab = {
            "rag": [
                {
                    "name": chunk.get("source", f"Document-{i}"),
                    "text": chunk.get("text", "")[:100],
                    "similarity": 0.75,
                }
                for i, chunk in enumerate(rag_chunks[:5])
            ],
            "ontology": [
                {
                    "name": entity.get("name", f"Entity-{i}"),
                    "text": entity.get("definition", ""),
                    "similarity": 0.8,
                }
                for i, entity in enumerate(ontology_entities[:3])
            ] if has_ontology_evidence else [],
            "expert_opinions": [],
        }

        yield f"data: {json.dumps({'event': 'sources', 'data': sources_for_tab})}\n\n"

        # 답변 생성
        answer_text = ""

        if not has_rag_evidence:
            # 근거 없음: 일반 설명 생성 안 함
            answer_text = "현재 업로드되었거나 검색된 문서 근거에서 질문 주제 관련 내용을 확인하지 못했습니다."
        else:
            # 근거 있음: RAG 청크에서 답변 구성
            answer_text = rag_chunks[0].get("text", "")

            # 온톨로지 정보 추가 (expert_mode인 경우)
            if has_ontology_evidence and mode == "expert_mode":
                entity_names = [e.get("name", "") for e in ontology_entities[:3]]
                if entity_names:
                    answer_text += f"\n\n관련 개념: {', '.join(entity_names)}"

        # 토큰별 전송 (답변 본문)
        for char in answer_text:
            await asyncio.sleep(0.001)
            yield f"data: {json.dumps({'event': 'answer_chunk', 'data': {'token': char}})}\n\n"

        # 한계점 정보
        limitations = []
        if not has_rag_evidence:
            limitations.append("문서 근거 없음")
        if allow_partial and has_rag_evidence:
            limitations.append("부분 답변 포함")

        if limitations:
            yield f"data: {json.dumps({'event': 'limitations', 'data': limitations})}\n\n"

        # 후속 질문 제안
        follow_ups = [
            "더 자세한 정보를 원하시나요?",
            "다른 관점에서의 설명이 필요하신가요?",
        ]
        yield f"data: {json.dumps({'event': 'follow_ups', 'data': follow_ups})}\n\n"

        # 완료 이벤트 (메타 정보)
        confidence_score = 0.85 if has_rag_evidence else 0.25
        coverage_level = 3 if has_rag_evidence and has_ontology_evidence else (2 if has_rag_evidence else 1)

        complete_meta = {
            "level": coverage_level,
            "relevance_level": coverage_level,
            "confidence": confidence_score,
            "confidence_score": confidence_score,
            "sources": {
                "rag": [c.get("source", "") for c in rag_chunks],
                "ontology": [e.get("name", "") for e in ontology_entities] if has_ontology_evidence else [],
            },
            "limitations": limitations,
        }

        yield f"data: {json.dumps({'event': 'complete', 'data': complete_meta})}\n\n"

    except Exception as e:
        logger.error(f"Error in generate_stream: {str(e)}")
        error_response = {"event": "error", "data": {"message": str(e)}}
        yield f"data: {json.dumps(error_response)}\n\n"


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
    """
    Adaptive Query Streaming Endpoint (Mock Version for Testing)

    Returns Server-Sent Events (SSE) stream with:
    - answer_chunk: Individual tokens of the answer
    - sources: RAG/Ontology sources (for RAG tab display)
    - limitations: Coverage limitations
    - follow_ups: Suggested follow-up questions
    - complete: Final metadata (confidence, coverage level)
    - error: Error messages
    """
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
