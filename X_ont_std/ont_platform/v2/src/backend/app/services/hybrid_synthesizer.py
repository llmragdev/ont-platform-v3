"""Combine ontology and vector results into a cited QueryResponse."""
from __future__ import annotations

from typing import Any

from app.models.query_intent import IntentType, QueryPlan, QueryResponse


class HybridSynthesizer:
    def synthesize(
        self,
        question: str,
        plan: QueryPlan,
        ontology_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        trace: list[str],
    ) -> QueryResponse:
        ontology_items = []
        for result in ontology_results:
            ontology_items.extend(result.get("items", []))

        ontology_sources = [self._ontology_source(item) for item in ontology_items]
        vector_sources = [self._vector_source(item) for item in vector_results]
        sources = ontology_sources + vector_sources
        evidence = [src for src in sources if src.get("citation")]

        answer = self._answer(plan.intent, len(ontology_items), len(vector_results), evidence)
        structured_data = {
            "ontology": {
                "count": len(ontology_items),
                "items": ontology_items,
                "results": ontology_results,
            },
            "vector": {
                "count": len(vector_results),
                "items": vector_results,
            },
        }

        return QueryResponse(
            answer=answer,
            intent=plan.intent,
            sources=sources,
            structured_data=structured_data,
            evidence=evidence,
            trace=trace,
            metadata={"plan": self._dump_model(plan), "question": question},
        )

    @staticmethod
    def _answer(intent: IntentType, ontology_count: int, vector_count: int, evidence: list[dict]) -> str:
        citation_text = ""
        if evidence:
            citation_text = " Citations: " + ", ".join(e["citation"] for e in evidence[:3]) + "."
        if intent == IntentType.FILTER:
            return f"Found {ontology_count} ontology item(s).{citation_text}"
        if intent == IntentType.HYBRID:
            return f"Found {ontology_count} ontology item(s) and {vector_count} document result(s).{citation_text}"
        return f"Found {vector_count} document result(s).{citation_text}"

    @staticmethod
    def _ontology_source(item: dict[str, Any]) -> dict[str, Any]:
        doc_id = item.get("doc_id") or item.get("__doc_id") or ""
        item_id = item.get("id", "")
        citation = f"ontology:{doc_id}:{item_id}" if doc_id or item_id else "ontology"
        return {
            "source_type": "ontology",
            "citation": citation,
            "id": item_id,
            "doc_id": doc_id,
            "name": item.get("name"),
            "type": item.get("type"),
            "data": item,
        }

    @staticmethod
    def _vector_source(item: dict[str, Any]) -> dict[str, Any]:
        doc_id = item.get("doc_id", "")
        page = item.get("page", 0)
        citation = f"document:{doc_id}:p{page}" if doc_id else "document"
        return {
            "source_type": "vector",
            "citation": citation,
            "doc_id": doc_id,
            "filename": item.get("filename", ""),
            "page": page,
            "score": item.get("score"),
            "text": item.get("text", ""),
            "data": item,
        }

    @staticmethod
    def _dump_model(model: Any) -> dict:
        if hasattr(model, "model_dump"):
            return model.model_dump(mode="json")
        return model.dict()
