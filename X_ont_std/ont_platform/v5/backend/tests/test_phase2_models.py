"""Phase 2 DoD tests — Provenance models, Repository pattern, QueryPlanValidator."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.ontology import OntologyEntityV3, OntologyProvenance
from app.models.query_intent import OntologyFilter, QueryPlanV3, IntentType
from app.repositories.base_interface import BaseRepositoryInterface
from app.repositories.json_repository import JsonOntologyRepository
from app.services.query_plan_validator import QueryPlanValidator, ValidationResult
from app.services.ontology import OntologyService


class TestOntologyProvenanceModel:
    def test_default_values(self):
        prov = OntologyProvenance()
        assert prov.confidence == 1.0
        assert prov.source_doc_id is None

    def test_entity_v3_from_dict_backward_compat(self):
        raw = {"id": "E001", "type": "PRODUCT", "name": "Snowflake", "properties": {}}
        entity = OntologyEntityV3.from_dict(raw)
        assert entity.id == "E001"
        assert entity.provenance is None
        assert entity.status == "active"
        assert entity.version == 1

    def test_entity_v3_with_provenance(self):
        raw = {
            "id": "E002", "type": "CONCEPT", "name": "RAG",
            "properties": {},
            "provenance": {"source_doc_id": "doc-001", "source_page": 3, "confidence": 0.92},
            "status": "active", "version": 2,
        }
        entity = OntologyEntityV3.from_dict(raw)
        assert entity.provenance is not None
        assert entity.provenance.source_doc_id == "doc-001"
        assert entity.provenance.confidence == 0.92
        assert entity.version == 2

    def test_entity_v3_optional_all_new_fields(self):
        entity = OntologyEntityV3(id="E003", type="PERSON", name="Alice")
        assert entity.provenance is None
        assert entity.status == "active"
        assert entity.created_by is None


class TestRepositoryInterface:
    def test_json_repo_is_abc_compliant(self):
        repo = JsonOntologyRepository()
        assert isinstance(repo, BaseRepositoryInterface)

    def test_abstract_methods_implemented(self):
        repo = JsonOntologyRepository()
        assert hasattr(repo, "get")
        assert hasattr(repo, "list")
        assert hasattr(repo, "save")
        assert hasattr(repo, "delete")


class TestQueryPlanV3Fields:
    def test_plan_v3_has_new_fields(self):
        plan = QueryPlanV3(intent=IntentType.FILTER, reasoning="test", steps=[])
        assert plan.ontology_filters == []
        assert plan.needs_vector is True
        assert plan.doc_ids is None
        assert plan.validated is False
        assert plan.llm_classified is False

    def test_ontology_filter_defaults(self):
        f = OntologyFilter(entity_type="Order")
        assert f.operator == "eq"
        assert f.property is None
        assert f.value is None

    def test_plan_inherits_query_plan(self):
        from app.models.query_intent import QueryPlan
        plan = QueryPlanV3(intent=IntentType.DESCRIPTIVE, reasoning="test", steps=[])
        assert isinstance(plan, QueryPlan)


class TestQueryPlanValidator:
    def test_valid_plan_passes(self):
        ont_svc = OntologyService()
        validator = QueryPlanValidator(ont_svc)
        from app.models.tenant_context import TenantContext
        ctx = TenantContext("u", "c", "p", "Admin")
        plan = QueryPlanV3(intent=IntentType.FILTER, reasoning="ok", steps=[],
                           ontology_filters=[OntologyFilter(entity_type="PRODUCT")])
        result = validator.validate(plan, ctx)
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_invalid_entity_type(self):
        ont_svc = OntologyService()
        validator = QueryPlanValidator(ont_svc)
        from app.models.tenant_context import TenantContext
        ctx = TenantContext("u", "c", "p", "Admin")
        plan = QueryPlanV3(intent=IntentType.FILTER, reasoning="test", steps=[],
                           ontology_filters=[OntologyFilter(entity_type="NONEXISTENT_TYPE_XYZ")])
        result = validator.validate(plan, ctx)
        assert result.valid is False
        assert any("NONEXISTENT_TYPE_XYZ" in e for e in result.errors)
