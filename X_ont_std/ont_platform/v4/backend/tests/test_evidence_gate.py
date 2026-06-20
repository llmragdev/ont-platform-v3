"""Unit tests for EvidenceGate service."""
import pytest
from app.services.evidence_gate import EvidenceGate, QuestionCategoryClassifier


def test_question_classifier():
    assert QuestionCategoryClassifier.classify("Snowflake RAG에서 어떤가요?") == "Snowflake"
    assert QuestionCategoryClassifier.classify("스노우플레이크 성능 분석") == "Snowflake"
    assert QuestionCategoryClassifier.classify("국방 지휘통제 DB") == "Defense"
    assert QuestionCategoryClassifier.classify("온톨로지와 지식그래프의 매칭 이질성") == "Ontology"
    assert QuestionCategoryClassifier.classify("RAG 임베딩 및 청크 검색") == "Advanced RAG"
    assert QuestionCategoryClassifier.classify("일반적인 일상 대화") == "Unknown"


def test_evidence_gate_category_mismatch():
    gate = EvidenceGate()
    # Snowflake query should be blocked regardless of retrieved sources
    res = gate.check_evidence(
        question="Snowflake RAG에서 어떤가요?",
        ontology_results=[],
        vector_results=[{"filename": "NLP - [07] NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf", "score": 0.5}]
    )
    assert res["answer_allowed"] is False
    assert res["reason"] == "category_mismatch"
    assert res["message"] == "해당 카테고리 문서와 관련이 없습니다."


def test_evidence_gate_no_evidence():
    gate = EvidenceGate()
    # Query with no retrieved docs and no ontology hits should be blocked
    res = gate.check_evidence(
        question="온톨로지 기반 질의응답은 무엇인가?",
        ontology_results=[{"items": []}],
        vector_results=[]
    )
    assert res["answer_allowed"] is False
    assert res["reason"] == "no_evidence"
    assert res["message"] == "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다."


def test_evidence_gate_low_relevance():
    gate = EvidenceGate(relevance_threshold=1.2)
    # Query with vector hits but poor scores (distance > 1.2) should be blocked
    res = gate.check_evidence(
        question="온톨로지 기반 질의응답은 무엇인가?",
        ontology_results=[{"items": []}],
        vector_results=[{"filename": "NLP - [07] NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf", "score": 1.4}]
    )
    assert res["answer_allowed"] is False
    assert res["reason"] == "low_relevance"
    assert res["message"] == "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다."


def test_evidence_gate_sufficient_evidence():
    gate = EvidenceGate(relevance_threshold=1.2)
    # Query with valid matching vector score should be allowed
    res = gate.check_evidence(
        question="온톨로지 기반 질의응답은 무엇인가?",
        ontology_results=[{"items": []}],
        vector_results=[{"filename": "NLP - [07] NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf", "score": 0.8}]
    )
    assert res["answer_allowed"] is True
    assert res["reason"] == "sufficient_evidence"
    assert res["message"] is None
