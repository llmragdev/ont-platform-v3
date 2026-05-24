"""Phase 4 Week 4: SPARQL API 서비스 (Priority 1: TripleStore 통합)"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from app.models.rdf_model import (
    SPARQLQuery, SPARQLResult, RDFTriple, ExternalOntologySource
)
from app.services.sparql_engine import SPARQLEngine
from app.services.rdf_converter import RDFConverter
from app.services.ontology_importer import OntologyImporter
from app.models.ontology_schema import DomainSchema
from storage_config import STORAGE_ROOT


class SPARQLService:
    """SPARQL 쿼리 서비스 (TripleStore 기반 영속성)"""

    def __init__(self, domain_id: str = "default"):
        # Priority 1: TripleStore 저장 경로
        store_path = STORAGE_ROOT / "ontology" / f"{domain_id}_triples.jsonl"
        self.engine = SPARQLEngine(store_path=store_path)
        self.converter = RDFConverter()
        self.importer = OntologyImporter()
        self.domain_schema: Optional[DomainSchema] = None
        self.domain_id = domain_id

        # 서버 시작 시 기존 트리플 로드
        self.engine.load_triples()

    def set_domain_schema(self, schema: DomainSchema) -> None:
        """도메인 스키마 설정"""
        self.domain_schema = schema
        self.converter.set_domain_schema(schema)

    def execute_sparql_query(self, query_string: str) -> SPARQLResult:
        """SPARQL 쿼리 실행"""
        query = SPARQLQuery(
            query_string=query_string,
            query_type=self._detect_query_type(query_string)
        )
        return self.engine.execute_query(query)

    def add_entity_rdf(
        self, entity_id: str, entity_type: str, properties: Dict[str, Any]
    ) -> List[RDFTriple]:
        """엔티티를 RDF로 변환 후 추가"""
        if not self.domain_schema:
            raise ValueError("Domain schema must be set first")

        triples = self.converter.entity_to_rdf_triples(
            entity_id=entity_id,
            entity_type=entity_type,
            properties=properties
        )
        self.engine.add_triples(triples)
        self.engine.save_triples()  # Priority 1: 자동 저장
        return triples

    def add_relationship_rdf(
        self,
        from_entity_id: str,
        from_type: str,
        to_entity_id: str,
        to_type: str,
        relation_type: str,
        relation_props: Optional[Dict[str, Any]] = None
    ) -> List[RDFTriple]:
        """관계를 RDF로 변환 후 추가"""
        if not self.domain_schema:
            raise ValueError("Domain schema must be set first")

        triples = self.converter.relation_to_rdf_triples(
            from_entity_id=from_entity_id,
            from_type=from_type,
            to_entity_id=to_entity_id,
            to_type=to_type,
            relation_type=relation_type,
            relation_props=relation_props
        )
        self.engine.add_triples(triples)
        self.engine.save_triples()  # Priority 1: 자동 저장
        return triples

    def explore_ontology(self, entity_uri: Optional[str] = None) -> Dict[str, Any]:
        """온톨로지 탐색 (엔티티 또는 전체)"""
        if entity_uri:
            # 특정 엔티티에 대한 DESCRIBE 쿼리
            query_string = f"DESCRIBE {entity_uri}"
        else:
            # 모든 엔티티 조회
            query_string = "SELECT ?x WHERE { ?x ?p ?o }"

        result = self.execute_sparql_query(query_string)
        return {
            "query_id": result.query_id,
            "results": result.results,
            "result_count": result.result_count,
            "execution_time_ms": result.execution_time_ms
        }

    def find_relationships(self, entity_uri: str) -> Dict[str, Any]:
        """엔티티의 관계 찾기"""
        query_string = f"""
        SELECT ?predicate ?object WHERE {{
            {entity_uri} ?predicate ?object
        }}
        """
        result = self.execute_sparql_query(query_string)
        return {
            "entity": entity_uri,
            "relationships": result.results,
            "count": result.result_count
        }

    def query_by_type(self, entity_type: str) -> Dict[str, Any]:
        """타입별로 엔티티 조회"""
        query_string = f"""
        SELECT ?x WHERE {{
            ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{entity_type}>
        }}
        """
        result = self.execute_sparql_query(query_string)
        return {
            "entity_type": entity_type,
            "entities": result.results,
            "count": result.result_count
        }

    def import_external_ontology(
        self, source: str, source_id: str, **kwargs
    ) -> Dict[str, Any]:
        """외부 온톨로지 임포트"""
        if source == "dbpedia":
            result = self.importer.import_dbpedia(
                entity_type=source_id,
                limit=kwargs.get("limit", 100)
            )
        elif source == "wikidata":
            result = self.importer.import_wikidata(
                entity_id=source_id,
                language=kwargs.get("language", "en")
            )
        elif source == "schema_org":
            result = self.importer.import_schema_org(source_id)
        else:
            raise ValueError(f"Unsupported source: {source}")

        # RDF로 변환해서 엔진에 추가 (시뮬레이션)
        return {
            "import_id": result.import_id,
            "source": source,
            "source_id": source_id,
            "total_triples": result.total_triples,
            "imported_entities": result.imported_entities,
            "imported_triples": result.imported_triples,
            "status": "success" if result.failed_count == 0 else "partial"
        }

    def get_query_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """쿼리 이력 조회"""
        history = self.engine.get_query_history(limit=limit)
        return [
            {
                "query_id": h.query_id,
                "variables": h.variables,
                "result_count": h.result_count,
                "execution_time_ms": h.execution_time_ms,
                "timestamp": h.query_timestamp.isoformat()
            }
            for h in history
        ]

    def get_triple_count(self) -> int:
        """전체 트리플 개수"""
        return self.engine.get_triple_count()

    def clear_triples(self) -> None:
        """모든 트리플 제거"""
        self.engine.clear_triples()

    def _detect_query_type(self, query_string: str) -> str:
        """쿼리 타입 감지"""
        upper_query = query_string.upper().strip()
        if upper_query.startswith("SELECT"):
            return "SELECT"
        elif upper_query.startswith("CONSTRUCT"):
            return "CONSTRUCT"
        elif upper_query.startswith("DESCRIBE"):
            return "DESCRIBE"
        elif upper_query.startswith("ASK"):
            return "ASK"
        return "UNKNOWN"
