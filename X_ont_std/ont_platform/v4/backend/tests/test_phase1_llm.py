"""Phase 1 DoD tests — LlmClient + HybridSynthesizer + QueryPlanner LLM classification."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.llm_client import LlmClient
from app.services.hybrid_synthesizer import HybridSynthesizer
from app.services.query_planner import QueryPlannerService
from app.services.ontology import OntologyService
from app.services.vector_search import VectorSearchService
from app.models.query_intent import IntentType
from app.models.tenant_context import TenantContext

_CTX = TenantContext(user_id="test", company_id="test", project_id="test-proj", role="Admin")


class TestLlmClient:
    def test_disabled_when_no_api_key(self):
        client = LlmClient(api_key=None)
        # If no GEMINI_API_KEY env var, should be disabled
        import os
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")):
            assert client.enabled is False

    def test_generate_returns_none_when_disabled(self):
        client = LlmClient(api_key="INVALID_KEY_FOR_TEST")
        # Will fail to init, so enabled=False
        if not client.enabled:
            result = client.generate("test prompt")
            assert result is None

    def test_classify_returns_empty_dict_when_disabled(self):
        client = LlmClient(api_key=None)
        import os
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")):
            result = client.classify("test prompt")
            assert result == {}


class TestHybridSynthesizer:
    def test_fallback_answer_no_llm(self):
        synth = HybridSynthesizer(llm=LlmClient(api_key=None))
        from app.models.query_intent import QueryPlan
        plan = QueryPlan(intent=IntentType.DESCRIPTIVE, reasoning="test", steps=[])

        import os
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")):
            response = synth.synthesize("test?", plan, [], [], [])
            assert response.quality_metrics["llm_used"] is False
            assert response.quality_metrics["fallback_used"] is True

    def test_quality_metrics_included(self):
        synth = HybridSynthesizer(llm=LlmClient(api_key=None))
        from app.models.query_intent import QueryPlan
        plan = QueryPlan(intent=IntentType.FILTER, reasoning="test", steps=[])
        response = synth.synthesize("test?", plan, [], [], [])
        assert "llm_used" in response.quality_metrics
        assert "fallback_used" in response.quality_metrics
        assert "vector_hits" in response.quality_metrics
        assert "ontology_hits" in response.quality_metrics

    def test_ontology_evidence_populated(self):
        synth = HybridSynthesizer(llm=LlmClient(api_key=None))
        from app.models.query_intent import QueryPlan
        plan = QueryPlan(intent=IntentType.FILTER, reasoning="test", steps=[])
        ont_results = [{"items": [{"id": "E001", "type": "PRODUCT", "name": "Snowflake", "properties": {}}]}]
        response = synth.synthesize("snowflake?", plan, ont_results, [], [])
        assert len(response.ontology_evidence) == 1
        assert response.ontology_evidence[0]["label"] == "Snowflake"


class TestQueryPlannerLlmClassification:
    def setup_method(self):
        self.ont_svc = OntologyService()
        self.vec_svc = VectorSearchService(embeddings=None)
        self.planner = QueryPlannerService(
            ontology_svc=self.ont_svc,
            vector_svc=self.vec_svc,
            llm_client=LlmClient(api_key=None),
        )

    def test_heuristic_descriptive(self):
        plan = self.planner.classify_intent("Snowflake의 장점은?")
        assert plan.intent == IntentType.DESCRIPTIVE

    def test_heuristic_filter_colon(self):
        plan = self.planner.classify_intent("status: Submitted")
        assert plan.intent == IntentType.FILTER

    def test_heuristic_hybrid_keyword(self):
        plan = self.planner.classify_intent("하이브리드로 찾아줘")
        assert plan.intent == IntentType.HYBRID

    def test_llm_classified_flag_false_without_key(self):
        import os
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")):
            plan = self.planner.classify_intent("test query")
            assert plan.llm_classified is False

    def test_plan_has_v3_fields(self):
        plan = self.planner.classify_intent("status: Submitted")
        assert hasattr(plan, "ontology_filters")
        assert hasattr(plan, "needs_vector")
        assert hasattr(plan, "llm_classified")
