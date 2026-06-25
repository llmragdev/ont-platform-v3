"""EvidenceGate Service — checks query relevance, category matches, and grounding."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class QuestionCategoryClassifier:
    """Heuristic query classifier based on keyword mapping."""

    @staticmethod
    def classify(question: str) -> str:
        q_lower = question.lower()
        if any(term in q_lower for term in ["snowflake", "스노우플레이크", "스노우 플레이크", "ranking_issue"]):
            return "Snowflake"
        if any(term in q_lower for term in ["국방", "지휘통제", "한국군"]):
            return "Defense"
        if any(term in q_lower for term in ["온톨로지", "지식 그래프", "지식그래프", "지식지형", "rdf", "owl", "스키마", "매칭", "이질성"]):
            return "Ontology"
        if any(term in q_lower for term in ["rag", "임베딩", "벡터", "청크", "검색", "생성", "언어모델"]):
            return "Advanced RAG"
        return "Unknown"


def get_document_category(filename: str) -> str:
    """Maps retrieved document filename to its respective category."""
    if not filename:
        return "Unknown"
    
    ontology_docs = [
        "NLP - [03] 온톨로지이질성문제를해결하기위한온톨로지매칭방법-2024.pdf",
        "NLP - [07] NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf",
        "국방 - [01] 온톨로지와지식그래프를활용한국방지휘통제데이터통합방법연구-2025.pdf",
        "국방 - [02] 해외 온톨로지 현황과 한국군 온톨로지 개발방안_202306.pdf"
    ]
    for doc in ontology_docs:
        if doc in filename:
            return "Ontology"
            
    rag_docs = [
        "NLP - [06] 정적 언어모델부터 생성형AI까지, 텍스트를 다시 쓰는 기술에 대하여 - 2025.pdf",
        "NLP - [08] NLP - 한국근대문인 데이터베이스 구축 방법탐색-2025.pdf",
        "NLP - [09] NLP - 실시간 문맥 인식 감성 분석을 위한 모듈형 아키텍처 설계-2025.pdf"
    ]
    for doc in rag_docs:
        if doc in filename:
            return "Advanced RAG"
            
    return "Unknown"


class EvidenceGate:
    """Blocks answers for out-of-scope or ungrounded questions."""

    def __init__(self, relevance_threshold: float = 1.2) -> None:
        self.relevance_threshold = relevance_threshold

    def check_evidence(
        self,
        question: str,
        ontology_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        q_category = QuestionCategoryClassifier.classify(question)
        
        # 1. Category mismatch check for Snowflake (Out-of-Scope)
        if q_category == "Snowflake":
            logger.info("[EvidenceGate] Out-of-scope Snowflake query detected.")
            return {
                "answer_allowed": False,
                "reason": "category_mismatch",
                "message": "해당 카테고리 문서와 관련이 없습니다.",
                "confidence": 1.0,
                "question_category": q_category
            }

        # Collect categories of retrieved documents
        retrieved_categories = set()
        for res in vector_results:
            filename = res.get("filename", "")
            doc_cat = get_document_category(filename)
            if doc_cat != "Unknown":
                retrieved_categories.add(doc_cat)

        has_ontology_hits = any(len(res.get("items", [])) > 0 for res in ontology_results)
        if has_ontology_hits:
            retrieved_categories.add("Ontology")

        has_vector_hits = len(vector_results) > 0

        # 2. General no evidence check: if both sources are empty
        if not has_vector_hits and not has_ontology_hits:
            logger.info("[EvidenceGate] No vector or ontology hits retrieved.")
            return {
                "answer_allowed": False,
                "reason": "no_evidence",
                "message": "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다.",
                "confidence": 1.0,
                "question_category": q_category
            }

        # 3. Vector relevance threshold check
        # Chroma scores are distances where lower is better. A distance > 1.2 typically represents poor relevance.
        if has_vector_hits:
            scores = [res["score"] for res in vector_results if "score" in res]
            if scores:
                best_score = min(scores)
                if best_score > self.relevance_threshold:
                    logger.info(
                        "[EvidenceGate] Best score %.3f exceeds relevance threshold %.3f.",
                        best_score, self.relevance_threshold
                    )
                    return {
                        "answer_allowed": False,
                        "reason": "low_relevance",
                        "message": "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다.",
                        "confidence": 0.9,
                        "question_category": q_category
                    }

        return {
            "answer_allowed": True,
            "reason": "sufficient_evidence",
            "message": None,
            "confidence": 1.0,
            "question_category": q_category
        }
