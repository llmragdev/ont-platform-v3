"""Evidence gate for v5 grounded/no-answer policy."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any

from app.models.query_intent import SearchMode
from app.services.question_analyzer import QuestionAnalysis


@dataclass(frozen=True)
class EvidenceGateResult:
    answer_allowed: bool
    reason: str
    policy: str
    message: str
    confidence: float
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AnswerPolicyStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(__file__).resolve().parents[3] / "config" / "answer_policies.jsonl"
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rules: list[dict[str, Any]] = []
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rules.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rules

    def match(self, question: str, category: str) -> dict[str, Any] | None:
        for rule in self.rules:
            rule_category = rule.get("category")
            if rule_category and rule_category != category:
                continue
            pattern = rule.get("question_pattern")
            if pattern and not re.search(pattern, question, flags=re.IGNORECASE):
                continue
            return rule
        return None


class EvidenceGate:
    CATEGORY_IRRELEVANT = "질문은 해당 카테고리 문서와 관련이 없습니다."
    NO_DIRECT_EVIDENCE = "제공된 문서에서 질문에 대한 직접적인 근거를 찾지 못했습니다."

    _DOC_CATEGORY_HINTS: dict[str, list[str]] = {
        "Snowflake": ["snowflake", "스노우플레이크"],
        "Ontology": ["온톨로지", "ontology", "지식그래프", "knowledge graph"],
        "Advanced RAG": ["rag", "검색증강", "qa", "bm25"],
        "NLP": ["nlp", "자연어", "언어모델", "감성"],
        "Defense": ["국방", "지휘통제", "한국군", "defense"],
    }

    def __init__(
        self,
        policy_store: AnswerPolicyStore | None = None,
        *,
        vector_distance_threshold: float = 1.2,
    ) -> None:
        self.policy_store = policy_store or AnswerPolicyStore()
        self.vector_distance_threshold = vector_distance_threshold

    def check_evidence(
        self,
        *,
        question: str,
        analysis: QuestionAnalysis,
        search_mode: SearchMode,
        ontology_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
    ) -> EvidenceGateResult:
        policy_rule = self.policy_store.match(question, analysis.question_category)
        if policy_rule and policy_rule.get("policy") == "category_irrelevant":
            if not self._has_direct_category_evidence(analysis.question_category, vector_results):
                return self._blocked(
                    reason="explicit_policy_category_irrelevant",
                    policy="category_irrelevant",
                    message=policy_rule.get("target_response") or self.CATEGORY_IRRELEVANT,
                    confidence=0.98,
                    details={"rule": policy_rule, "analysis": asdict(analysis)},
                )

        if analysis.question_category == "Snowflake" and not self._has_direct_category_evidence("Snowflake", vector_results):
            return self._blocked(
                reason="category_mismatch",
                policy="category_irrelevant",
                message=self.CATEGORY_IRRELEVANT,
                confidence=max(0.9, analysis.confidence),
                details={"analysis": asdict(analysis), "retrieved_categories": self._retrieved_categories(vector_results)},
            )

        if search_mode == SearchMode.ONTOLOGY_ONLY:
            ontology_count = self._ontology_count(ontology_results)
            if ontology_count == 0:
                return self._blocked("no_ontology_evidence", "no_direct_evidence", self.NO_DIRECT_EVIDENCE, 0.75, {})
            return self._allowed("ontology_evidence", {"ontology_count": ontology_count})

        if search_mode == SearchMode.VECTOR_ONLY:
            if not vector_results:
                return self._blocked("no_vector_evidence", "no_direct_evidence", self.NO_DIRECT_EVIDENCE, 0.75, {})
            if self._best_vector_distance(vector_results) > self.vector_distance_threshold:
                return self._blocked(
                    "low_vector_relevance",
                    "no_direct_evidence",
                    self.NO_DIRECT_EVIDENCE,
                    0.7,
                    {"best_score": self._best_vector_distance(vector_results), "threshold": self.vector_distance_threshold},
                )
            return self._allowed("vector_evidence", {"best_score": self._best_vector_distance(vector_results)})

        ontology_count = self._ontology_count(ontology_results)
        best_score = self._best_vector_distance(vector_results)
        has_vector = bool(vector_results) and best_score <= self.vector_distance_threshold
        if ontology_count == 0 and not has_vector:
            return self._blocked(
                "no_direct_evidence",
                "no_direct_evidence",
                self.NO_DIRECT_EVIDENCE,
                0.7,
                {"ontology_count": ontology_count, "best_score": best_score},
            )
        return self._allowed("evidence_found", {"ontology_count": ontology_count, "best_score": best_score})

    def _blocked(self, reason: str, policy: str, message: str, confidence: float, details: dict[str, Any]) -> EvidenceGateResult:
        return EvidenceGateResult(False, reason, policy, message, confidence, details)

    def _allowed(self, reason: str, details: dict[str, Any]) -> EvidenceGateResult:
        return EvidenceGateResult(True, reason, "answer_allowed", "", 0.8, details)

    @staticmethod
    def _ontology_count(ontology_results: list[dict[str, Any]]) -> int:
        return sum(int(result.get("count", len(result.get("items", [])))) for result in ontology_results)

    @staticmethod
    def _best_vector_distance(vector_results: list[dict[str, Any]]) -> float:
        if not vector_results:
            return float("inf")
        scores = [float(item.get("score", float("inf"))) for item in vector_results]
        return min(scores)

    def _has_direct_category_evidence(self, category: str, vector_results: list[dict[str, Any]]) -> bool:
        return category in self._retrieved_categories(vector_results)

    def _retrieved_categories(self, vector_results: list[dict[str, Any]]) -> list[str]:
        categories: set[str] = set()
        for item in vector_results:
            explicit = item.get("category") or item.get("metadata", {}).get("category") if isinstance(item.get("metadata"), dict) else None
            if explicit:
                categories.add(str(explicit))
                continue
            haystack = " ".join(
                str(item.get(key, ""))
                for key in ("filename", "doc_id", "source", "text")
            ).lower()
            for category, hints in self._DOC_CATEGORY_HINTS.items():
                if any(hint.lower() in haystack for hint in hints):
                    categories.add(category)
        return sorted(categories)
