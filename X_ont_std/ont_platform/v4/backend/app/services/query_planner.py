"""QueryPlannerService v3.0 — LLM-first classification with keyword fallback."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from app.models.query_intent import (
    ActionType, EngineType, IntentType,
    OntologyFilter, QueryAction, QueryPlan, QueryPlanV3, QueryResponse,
)
from app.models.tenant_context import TenantContext
from app.services.audit import append_audit_event
from app.services.hybrid_synthesizer import HybridSynthesizer
from app.services.llm_client import LlmClient
from app.services.ontology import OntologyService
from app.services.query_executor import OntologyQueryEngine
from app.services.vector_search import VectorSearchService
from app.services.evidence_gate import EvidenceGate

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_FILTER_KEYWORDS = [
    "목록", "모두", "전체", "해당", "있는", "리스트", "조회",
    "보여줘", "알려줘", "찾아줘", "검색", "뭐가", "뭔가", "필터", "조건", "속성",
]


def _load_prompt(name: str) -> str:
    p = _PROMPTS_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


class _NullVectorSearchService:
    def search(self, query: str, ctx: TenantContext, **_: Any) -> list[dict]:
        return []


class QueryPlannerService:
    def __init__(
        self,
        ontology_svc: OntologyService,
        vector_svc: VectorSearchService | None = None,
        llm_client: LlmClient | None = None,
    ) -> None:
        self.ontology_svc = ontology_svc
        self.ontology = ontology_svc
        self.vector_svc = vector_svc or _NullVectorSearchService()
        self._llm = llm_client or LlmClient()
        self.ontology_engine = OntologyQueryEngine(ontology_svc)
        self.synthesizer = HybridSynthesizer(llm=self._llm)
        self.evidence_gate = EvidenceGate()

    def classify_intent(self, query: str, ctx: TenantContext | None = None) -> QueryPlanV3:
        schema_context = self._schema_context(ctx) if ctx else {}

        # LLM-first classification
        intent = self._llm_classify(query)
        llm_classified = intent is not None
        if intent is None:
            intent = self._heuristic_classify(query)

        plan = QueryPlanV3(
            intent=intent,
            reasoning="LLM classification" if llm_classified else "Heuristic classification",
            steps=self._build_steps(query, intent, schema_context),
            schema_context=schema_context,
            ontology_filters=self._build_filters(query, intent, schema_context),
            needs_vector=(intent in {IntentType.DESCRIPTIVE, IntentType.HYBRID}),
            llm_classified=llm_classified,
        )
        if ctx:
            self._validate_plan_steps(plan)
            append_audit_event(ctx, "GENERATE_QUERY_PLAN", "query", "planner",
                               {"query": query, "intent": intent.value, "llm_classified": llm_classified})
        return plan

    def _llm_classify(self, query: str) -> IntentType | None:
        if not self._llm.enabled:
            return None
        template = _load_prompt("classifier.txt")
        if not template:
            return None
        prompt = template.replace("{query}", query)
        result = self._llm.classify(prompt)
        intent_str = result.get("intent", "")
        logger.info("[LLM] classify intent=%r reasoning=%r", intent_str, result.get("reasoning", ""))
        try:
            return IntentType(intent_str.lower())
        except ValueError:
            return None

    def _heuristic_classify(self, query: str) -> IntentType:
        query_lower = query.lower()
        if "하이브리드" in query_lower or "hybrid" in query_lower:
            return IntentType.HYBRID
        if ":" in query or "=" in query:
            return IntentType.FILTER
        if any(word in query_lower for word in ["찾아줘", "필터", "조건", "속성", "목록", "보여줘"]):
            return IntentType.FILTER
        return IntentType.DESCRIPTIVE

    def ask(self, query: str, ctx: TenantContext) -> QueryResponse:
        logger.info("[ASK] query=%r  user=%s  project=%s", query, ctx.user_id, ctx.project_id)
        plan = self.classify_intent(query, ctx)
        logger.info("[PLAN] intent=%s  steps=%d  llm_classified=%s",
                    plan.intent.value, len(plan.steps), plan.llm_classified)
        trace = ["planner: generated query plan", f"planner: intent={plan.intent.value}",
                 f"planner: llm_classified={plan.llm_classified}"]
        ontology_results: list[dict[str, Any]] = []
        vector_results: list[dict[str, Any]] = []

        for index, step in enumerate(plan.steps, start=1):
            logger.info("[STEP %d] engine=%s  action=%s  params=%s",
                        index, step.engine.value, step.action.value, step.params)
            trace.append(f"executor: step {index} {step.engine.value}.{step.action.value}")
            if step.engine == EngineType.ONTOLOGY:
                result = self.ontology_engine.execute(step, ctx, query)
                ontology_results.append(result)
                trace.extend(result.get("trace", []))
                logger.info("[ONTOLOGY] hits=%d", result.get("count", 0))
            elif step.engine == EngineType.VECTOR:
                top_k = int(step.params.get("top_k", 3))
                shard_id = step.params.get("shard_id")
                results = self.vector_svc.search(step.params.get("query", query), ctx,
                                                 k=top_k, shard_id=shard_id)
                vector_results.extend(results)
                logger.info("[VECTOR] top_k=%d  shard=%s  hits=%d", top_k, shard_id, len(results))
                for r in results[:3]:
                    logger.info("  └ score=%.3f  doc=%s  text=%.80s",
                                r.get("score", 0), r.get("doc_id", "?"), r.get("text", "")[:80])
                trace.append(f"vector.search: matched {len(results)} document result(s)")
            else:
                trace.append(f"executor: skipped unsupported engine {step.engine.value}")

        gate_res = self.evidence_gate.check_evidence(query, ontology_results, vector_results)
        if not gate_res["answer_allowed"]:
            logger.info("[EVIDENCE_GATE] Blocked query=%r reason=%s", query, gate_res["reason"])
            trace.append(f"evidence_gate: blocked answer due to {gate_res['reason']}")
            
            ontology_items = []
            for result in ontology_results:
                ontology_items.extend(result.get("items", []))
            ontology_sources = [self.synthesizer._ontology_source(item) for item in ontology_items]
            vector_sources = [self.synthesizer._vector_source(item) for item in vector_results]
            sources = ontology_sources + vector_sources
            
            response = QueryResponse(
                answer=gate_res["message"],
                intent=plan.intent,
                sources=sources,
                structured_data={
                    "ontology": {"count": len(ontology_items), "items": ontology_items, "results": ontology_results},
                    "vector": {"count": len(vector_results), "items": vector_results},
                },
                evidence=[],
                trace=trace,
                metadata={"plan": self.synthesizer._dump_model(plan), "question": query, "evidence_gate": gate_res},
                ontology_evidence=[],
                quality_metrics={
                    "llm_used": False,
                    "fallback_used": True,
                    "vector_hits": len(vector_results),
                    "ontology_hits": len(ontology_items),
                    "blocked_by_gate": True,
                    "gate_reason": gate_res["reason"]
                }
            )
        else:
            response = self.synthesizer.synthesize(query, plan, ontology_results, vector_results, trace)
            
        logger.info("[ANSWER] llm_used=%s  answer=%.120s",
                    response.quality_metrics.get("llm_used"),
                    (response.answer or "")[:120])
        append_audit_event(ctx, "COMPLETE_HYBRID_ASK", "query", "hybrid_ask", {
            "query": query, "intent": plan.intent.value,
            "ontology_count": response.structured_data.get("ontology", {}).get("count", 0),
            "vector_count": response.structured_data.get("vector", {}).get("count", 0),
            "llm_used": response.quality_metrics.get("llm_used", False),
        })
        return response

    def ask_forced_hybrid(self, query: str, ctx: TenantContext) -> QueryResponse:
        """Like ask() but forces HYBRID intent regardless of LLM classification.
        Used by the integration test runner so every case exercises both sources."""
        logger.info("[ASK-HYBRID] query=%r  user=%s  project=%s", query, ctx.user_id, ctx.project_id)
        schema_context = self._schema_context(ctx)
        plan = QueryPlanV3(
            intent=IntentType.HYBRID,
            reasoning="Forced hybrid (integration test)",
            steps=self._build_steps(query, IntentType.HYBRID, schema_context),
            schema_context=schema_context,
            ontology_filters=self._build_filters(query, IntentType.HYBRID, schema_context),
            needs_vector=True,
            llm_classified=False,
        )
        trace = ["planner: forced hybrid plan", "planner: intent=hybrid", "planner: llm_classified=False"]
        ontology_results: list[dict[str, Any]] = []
        vector_results: list[dict[str, Any]] = []

        for index, step in enumerate(plan.steps, start=1):
            logger.info("[STEP %d] engine=%s  action=%s", index, step.engine.value, step.action.value)
            trace.append(f"executor: step {index} {step.engine.value}.{step.action.value}")
            if step.engine == EngineType.ONTOLOGY:
                result = self.ontology_engine.execute(step, ctx, query)
                ontology_results.append(result)
                trace.extend(result.get("trace", []))
                logger.info("[ONTOLOGY] hits=%d", result.get("count", 0))
            elif step.engine == EngineType.VECTOR:
                top_k = int(step.params.get("top_k", 5))
                results = self.vector_svc.search(step.params.get("query", query), ctx, k=top_k)
                vector_results.extend(results)
                logger.info("[VECTOR] hits=%d", len(results))
                trace.append(f"vector.search: matched {len(results)} document result(s)")

        gate_res = self.evidence_gate.check_evidence(query, ontology_results, vector_results)
        if not gate_res["answer_allowed"]:
            logger.info("[EVIDENCE_GATE] Blocked query=%r reason=%s", query, gate_res["reason"])
            trace.append(f"evidence_gate: blocked answer due to {gate_res['reason']}")
            
            ontology_items = []
            for result in ontology_results:
                ontology_items.extend(result.get("items", []))
            ontology_sources = [self.synthesizer._ontology_source(item) for item in ontology_items]
            vector_sources = [self.synthesizer._vector_source(item) for item in vector_results]
            sources = ontology_sources + vector_sources
            
            response = QueryResponse(
                answer=gate_res["message"],
                intent=plan.intent,
                sources=sources,
                structured_data={
                    "ontology": {"count": len(ontology_items), "items": ontology_items, "results": ontology_results},
                    "vector": {"count": len(vector_results), "items": vector_results},
                },
                evidence=[],
                trace=trace,
                metadata={"plan": self.synthesizer._dump_model(plan), "question": query, "evidence_gate": gate_res},
                ontology_evidence=[],
                quality_metrics={
                    "llm_used": False,
                    "fallback_used": True,
                    "vector_hits": len(vector_results),
                    "ontology_hits": len(ontology_items),
                    "blocked_by_gate": True,
                    "gate_reason": gate_res["reason"]
                }
            )
        else:
            response = self.synthesizer.synthesize(query, plan, ontology_results, vector_results, trace)
            
        logger.info("[ANSWER] llm_used=%s  answer=%.120s",
                    response.quality_metrics.get("llm_used"), (response.answer or "")[:120])
        append_audit_event(ctx, "COMPLETE_HYBRID_ASK", "query", "hybrid_ask", {
            "query": query, "intent": "hybrid",
            "ontology_count": response.structured_data.get("ontology", {}).get("count", 0),
            "vector_count": response.structured_data.get("vector", {}).get("count", 0),
            "llm_used": response.quality_metrics.get("llm_used", False),
        })
        return response

    # ── Legacy compatibility ──────────────────────────────────────────────────

    def classify(self, question: str) -> dict:
        plan = self.classify_intent(question)
        params = plan.steps[0].params if plan.steps else {}
        return {
            "type": "filter" if plan.intent == IntentType.FILTER else "descriptive",
            "entities": [],
            "operation": "list" if plan.intent == IntentType.FILTER else "explain",
            "property_key": params.get("property_key"),
            "property_value": params.get("property_value"),
            "entity_type": params.get("entity_type"),
        }

    def execute(self, question: str, ctx: TenantContext, doc_ids: list[str] | None = None,
                override: dict | None = None) -> dict:
        classification = override if override else self.classify(question)
        intent_str = classification.get("type", "descriptive")
        if intent_str == "filter":
            entity_type = classification.get("entity_type")
            prop_key = classification.get("property_key")
            prop_val = classification.get("property_value")
            if prop_key and prop_val:
                results = self.ontology_svc.filter_by_property(ctx, entity_type, prop_key, prop_val, doc_ids)
            else:
                results = self.ontology_svc.find_by_name(ctx, question, doc_ids)
            return {"query_type": "filter", "results": results, "count": len(results),
                    "fallback": "name_search" if not (prop_key and prop_val) else None}
        return {"query_type": "descriptive", "answer": "Descriptive response via legacy execute.", "results": []}

    def _validate_plan_steps(self, plan: QueryPlanV3) -> bool:
        schema = plan.schema_context or {}
        entity_types = set(schema.get("entity_types", []))
        properties_by_type = schema.get("properties_by_type", {})
        for step in plan.steps:
            if step.engine != EngineType.ONTOLOGY:
                continue
            entity_type = step.params.get("entity_type")
            prop = step.params.get("property_key")
            if entity_type and entity_types and entity_type not in entity_types:
                raise ValueError(f"Unknown entity_type in query plan: {entity_type}")
            if prop and entity_type:
                allowed = set(properties_by_type.get(entity_type, []))
                if allowed and prop not in allowed:
                    raise ValueError(f"Unknown property for {entity_type}: {prop}")
        return True

    def _build_steps(self, query: str, intent: IntentType, schema_context: dict[str, Any]) -> list[QueryAction]:
        if intent in {IntentType.FILTER, IntentType.HYBRID}:
            steps = [QueryAction(engine=EngineType.ONTOLOGY, action=ActionType.FILTER,
                                 params=self._extract_filter_params(query, schema_context),
                                 description="Filter ontology entities using schema-recognized fields.")]
            if intent == IntentType.HYBRID:
                steps.append(QueryAction(engine=EngineType.VECTOR, action=ActionType.SEARCH,
                                         params={"query": query, "top_k": 5},
                                         description="Search vectorized documents for evidence."))
            return steps
        return [QueryAction(engine=EngineType.VECTOR, action=ActionType.SEARCH,
                            params={"query": query, "top_k": 5},
                            description="Search vectorized documents.")]

    def _build_filters(self, query: str, intent: IntentType, schema_context: dict) -> list[OntologyFilter]:
        if intent not in {IntentType.FILTER, IntentType.HYBRID}:
            return []
        params = self._extract_filter_params(query, schema_context)
        return [OntologyFilter(
            entity_type=params.get("entity_type"),
            property=params.get("property_key"),
            operator="eq",
            value=params.get("property_value"),
        )]

    def _schema_context(self, ctx: TenantContext | None) -> dict[str, Any]:
        if ctx is None:
            return {}
        schema = self.ontology_svc.get_schema(ctx)
        types, props = [], {}
        for group in ("builtin_entity_types", "domain_entity_types"):
            for item in schema.get(group, []):
                name = item.get("name")
                if name:
                    types.append(name)
                    props[name] = list(item.get("properties") or [])
        return {
            "entity_types": sorted(set(types)),
            "properties_by_type": props,
            "all_properties": sorted({p for values in props.values() for p in values}),
            "relation_types": [r.get("name") for r in schema.get("domain_relation_types", []) if r.get("name")],
        }

    def _extract_filter_params(self, query: str, schema_context: dict[str, Any]) -> dict[str, Any]:
        entity_type = None
        lower = query.lower()
        for candidate in schema_context.get("entity_types", []):
            if re.search(rf"\b{re.escape(candidate.lower())}\b", lower):
                entity_type = candidate
                break
        prop = val = None
        match = re.search(r"([A-Za-z_][\w.-]*)\s*[:=]\s*([^,;]+)", query)
        if match:
            prop = match.group(1)
            val = self._clean_value(match.group(2))
        return {"entity_type": entity_type, "property_key": prop, "property_value": val, "query": query}

    @staticmethod
    def _clean_value(value: str) -> str:
        value = value.strip()
        value = re.split(r"\s+(?:인|엔티티|항목|목록|찾아줘|보여줘)", value, maxsplit=1)[0]
        value = re.sub(r"(인|인\s*엔티티|엔티티|항목|목록|찾아줘|보여줘)$", "", value).strip()
        return value
