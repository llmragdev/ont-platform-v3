"""HybridSynthesizer v3.0 — LLM-powered answer synthesis with fallback."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models.query_intent import IntentType, QueryPlan, QueryResponse
from app.services.llm_client import LlmClient

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    p = _PROMPTS_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


class HybridSynthesizer:
    def __init__(self, llm: LlmClient | None = None) -> None:
        self._llm = llm or LlmClient()

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

        llm_used = False
        if self._llm.enabled:
            answer = self._llm_answer(question, ontology_items, vector_results)
            if answer:
                llm_used = True
            else:
                answer = self._fallback_answer(plan.intent, len(ontology_items), len(vector_results), evidence)
        else:
            answer = self._fallback_answer(plan.intent, len(ontology_items), len(vector_results), evidence)

        ontology_evidence = self._build_ontology_evidence(ontology_items)
        quality_metrics = {
            "llm_used": llm_used,
            "fallback_used": not llm_used,
            "vector_hits": len(vector_results),
            "ontology_hits": len(ontology_items),
        }

        structured_data = {
            "ontology": {"count": len(ontology_items), "items": ontology_items, "results": ontology_results},
            "vector": {"count": len(vector_results), "items": vector_results},
        }

        return QueryResponse(
            answer=answer,
            intent=plan.intent,
            sources=sources,
            structured_data=structured_data,
            evidence=evidence,
            trace=trace,
            metadata={"plan": self._dump_model(plan), "question": question},
            ontology_evidence=ontology_evidence,
            quality_metrics=quality_metrics,
        )

    def _llm_answer(
        self,
        question: str,
        ontology_items: list[dict],
        vector_results: list[dict],
    ) -> str | None:
        template = _load_prompt("synthesizer.txt")
        if not template:
            return None

        ont_lines = "\n".join(
            f"- [{e.get('type','?')}] {e.get('name','?')}: {e.get('properties', {})}"
            for e in ontology_items[:10]
        ) or "없음"

        vec_lines = "\n".join(
            f"- (score={r.get('score',0):.2f}) {r.get('text','')[:200]}"
            for r in vector_results[:5]
        ) or "없음"

        prompt = (template
                  .replace("{question}", question)
                  .replace("{ontology_count}", str(len(ontology_items)))
                  .replace("{ontology_items}", ont_lines)
                  .replace("{vector_count}", str(len(vector_results)))
                  .replace("{vector_chunks}", vec_lines))
        return self._llm.generate(prompt)

    @staticmethod
    def _fallback_answer(intent: IntentType, ontology_count: int, vector_count: int, evidence: list[dict]) -> str:
        citation_text = ""
        if evidence:
            citation_text = " Citations: " + ", ".join(e["citation"] for e in evidence[:3]) + "."
        if intent == IntentType.FILTER:
            return f"Found {ontology_count} ontology item(s).{citation_text}"
        if intent == IntentType.HYBRID:
            return f"Found {ontology_count} ontology item(s) and {vector_count} document result(s).{citation_text}"
        return f"Found {vector_count} document result(s).{citation_text}"

    @staticmethod
    def _build_ontology_evidence(items: list[dict]) -> list[dict]:
        evidence = []
        for item in items:
            prov = item.get("provenance") or {}
            evidence.append({
                "node_id": item.get("id", ""),
                "node_type": item.get("type", ""),
                "label": item.get("name", ""),
                "source_doc_id": prov.get("source_doc_id") if isinstance(prov, dict) else None,
                "source_page": prov.get("source_page") if isinstance(prov, dict) else None,
                "confidence": prov.get("confidence", 1.0) if isinstance(prov, dict) else 1.0,
            })
        return evidence

    @staticmethod
    def _ontology_source(item: dict[str, Any]) -> dict[str, Any]:
        doc_id = item.get("doc_id") or item.get("__doc_id") or ""
        item_id = item.get("id", "")
        citation = f"ontology:{doc_id}:{item_id}" if doc_id or item_id else "ontology"
        return {"source_type": "ontology", "citation": citation, "id": item_id,
                "doc_id": doc_id, "name": item.get("name"), "type": item.get("type"), "data": item}

    @staticmethod
    def _vector_source(item: dict[str, Any]) -> dict[str, Any]:
        doc_id = item.get("doc_id", "")
        page = item.get("page", 0)
        citation = f"document:{doc_id}:p{page}" if doc_id else "document"
        return {"source_type": "vector", "citation": citation, "doc_id": doc_id,
                "filename": item.get("filename", ""), "page": page,
                "score": item.get("score"), "text": item.get("text", ""), "data": item}

    @staticmethod
    def _dump_model(model: Any) -> dict:
        if hasattr(model, "model_dump"):
            return model.model_dump(mode="json")
        return model.dict()
