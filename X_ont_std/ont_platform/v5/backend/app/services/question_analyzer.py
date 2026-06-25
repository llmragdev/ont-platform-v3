"""Question analysis helpers for v5 routing and evidence policy."""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class QuestionAnalysis:
    question_category: str
    confidence: float
    no_answer_candidate: bool
    matched_terms: list[str]


class QuestionAnalyzer:
    """Small rule-based analyzer for the v5 MVP.

    This intentionally starts simple. Later phases can replace or augment it
    with ontology schema mapping and a lightweight classifier.
    """

    _CATEGORY_PATTERNS: dict[str, list[str]] = {
        "Snowflake": [
            r"\bSnowflake\b",
            "스노우플레이크",
            r"\branking_issue\b",
            "warehouse",
            "정형 테이블",
            "테이블과 PDF",
            "Snowflake RAG",
        ],
        "Ontology": [
            "온톨로지",
            "지식그래프",
            "지식 그래프",
            "클래스",
            "속성",
            "인스턴스",
            "상하위",
            "이질성",
            "매칭",
            "SimRank",
            "SCBOW",
        ],
        "Advanced RAG": [
            r"\bRAG\b",
            "검색증강생성",
            "검색 증강",
            "chunk",
            "청크",
            "rerank",
            "재랭킹",
            "BM25",
            "문맥",
            "QA 테스트",
        ],
        "NLP": [
            r"\bNLP\b",
            "자연어",
            "언어모델",
            "감성 분석",
            "문맥 인식",
        ],
        "Defense": [
            "국방",
            "지휘통제",
            "한국군",
            "무기체계",
            "작전",
        ],
    }

    def analyze(self, question: str) -> QuestionAnalysis:
        matches: list[tuple[str, str]] = []
        for category, patterns in self._CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question, flags=re.IGNORECASE):
                    matches.append((category, pattern))

        if not matches:
            return QuestionAnalysis(
                question_category="Unknown",
                confidence=0.25,
                no_answer_candidate=False,
                matched_terms=[],
            )

        counts: dict[str, int] = {}
        terms: dict[str, list[str]] = {}
        for category, term in matches:
            counts[category] = counts.get(category, 0) + 1
            terms.setdefault(category, []).append(term)

        category = max(counts, key=counts.get)
        confidence = min(0.95, 0.45 + 0.15 * counts[category])
        return QuestionAnalysis(
            question_category=category,
            confidence=round(confidence, 3),
            no_answer_candidate=category in {"Snowflake"},
            matched_terms=terms[category],
        )
