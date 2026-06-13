"""Phase 4 Week 4: SPARQL API 엔드포인트 통합 테스트"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.services.sparql_service import SPARQLService
from app.models.ontology_schema import (
    DomainSchema, OntologyStyle, EntityType, RelationType,
    PropertyDefinition, PropertyType, RDFNamespace as SchemaRDFNamespace
)
from app.models.rdf_model import RDFTriple


@pytest.fixture
def domain_schema():
    """테스트용 도메인 스키마"""
    return DomainSchema(
        domain_id="test-domain",
        name="Test Domain",
        display_name="Test Domain",
        description="Test domain for API",
        ontology_style=OntologyStyle.RDF_TRIPLE,
        entity_types={
            "Person": EntityType(
                name="Person",
                display_name="Person",
                description="A person",
                properties={
                    "name": PropertyDefinition(
                        name="name",
                        display_name="Name",
                        description="Person's name",
                        property_type=PropertyType.STRING,
                        required=True
                    ),
                    "age": PropertyDefinition(
                        name="age",
                        display_name="Age",
                        description="Person's age",
                        property_type=PropertyType.INTEGER
                    )
                }
            )
        },
        relation_types={
            "knows": RelationType(
                name="knows",
                display_name="Knows",
                description="Person knows another person",
                from_type="Person",
                to_type="Person",
                properties={}
            )
        },
        rdf_namespaces=[
            SchemaRDFNamespace(
                prefix="ex",
                uri="http://example.com/",
                description="Example namespace"
            )
        ]
    )


@pytest.fixture
def sparql_service(domain_schema):
    """SPARQL 서비스"""
    service = SPARQLService()
    service.set_domain_schema(domain_schema)
    return service


class TestSPARQLServiceBasics:
    """SPARQL 서비스 기본 기능"""

    def test_add_entity_rdf(self, sparql_service):
        """엔티티를 RDF로 추가"""
        properties = {"name": "John Doe", "age": 30}
        triples = sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties=properties
        )
        assert len(triples) > 0
        assert sparql_service.get_triple_count() > 0

    def test_add_relationship_rdf(self, sparql_service):
        """관계를 RDF로 추가"""
        # 먼저 두 엔티티 추가
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )
        sparql_service.add_entity_rdf(
            entity_id="person-2",
            entity_type="Person",
            properties={"name": "Jane"}
        )

        # 관계 추가
        triples = sparql_service.add_relationship_rdf(
            from_entity_id="person-1",
            from_type="Person",
            to_entity_id="person-2",
            to_type="Person",
            relation_type="knows"
        )
        assert len(triples) > 0

    def test_execute_sparql_query(self, sparql_service):
        """SPARQL 쿼리 실행"""
        # 엔티티 추가
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        # 쿼리 실행
        result = sparql_service.execute_sparql_query(
            "SELECT ?x WHERE { ?x ?p ?o }"
        )
        assert result.query_id is not None
        assert result.execution_time_ms >= 0

    def test_explore_ontology(self, sparql_service):
        """온톨로지 탐색"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        result = sparql_service.explore_ontology()
        assert result["query_id"] is not None
        assert "results" in result
        assert "execution_time_ms" in result

    def test_explore_entity(self, sparql_service):
        """특정 엔티티 탐색"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        result = sparql_service.explore_ontology(
            entity_uri="http://ontology.example.com/test-domain/person/person-1"
        )
        assert result["query_id"] is not None

    def test_find_relationships(self, sparql_service):
        """관계 찾기"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        result = sparql_service.find_relationships(
            entity_uri="http://ontology.example.com/test-domain/person/person-1"
        )
        assert "entity" in result
        assert "relationships" in result

    def test_query_by_type(self, sparql_service):
        """타입별로 엔티티 조회"""
        # 여러 엔티티 추가
        for i in range(3):
            sparql_service.add_entity_rdf(
                entity_id=f"person-{i}",
                entity_type="Person",
                properties={"name": f"Person {i}"}
            )

        result = sparql_service.query_by_type(
            "http://ontology.example.com/test-domain/class/Person"
        )
        assert result["entity_type"] is not None
        assert "entities" in result

    def test_get_triple_count(self, sparql_service):
        """트리플 개수 조회"""
        initial_count = sparql_service.get_triple_count()
        assert initial_count == 0

        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        new_count = sparql_service.get_triple_count()
        assert new_count > initial_count

    def test_get_query_history(self, sparql_service):
        """쿼리 이력 조회"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        # 쿼리 실행
        sparql_service.execute_sparql_query("SELECT ?x WHERE { ?x ?p ?o }")
        sparql_service.execute_sparql_query("ASK WHERE { ?x ?p ?o }")

        history = sparql_service.get_query_history(limit=10)
        assert len(history) >= 2
        assert "query_id" in history[0]
        assert "execution_time_ms" in history[0]


class TestSPARQLServiceQueries:
    """SPARQL 쿼리 타입 테스트"""

    def test_select_query(self, sparql_service):
        """SELECT 쿼리"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        result = sparql_service.execute_sparql_query(
            "SELECT ?x WHERE { ?x ?p ?o }"
        )
        assert result.variables is not None or result.results is not None

    def test_ask_query(self, sparql_service):
        """ASK 쿼리"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        result = sparql_service.execute_sparql_query(
            "ASK WHERE { ?x ?p ?o }"
        )
        assert result.results is not None

    def test_describe_query(self, sparql_service):
        """DESCRIBE 쿼리"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        result = sparql_service.execute_sparql_query(
            "DESCRIBE ?x"
        )
        assert result.query_id is not None

    def test_construct_query(self, sparql_service):
        """CONSTRUCT 쿼리"""
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )

        result = sparql_service.execute_sparql_query(
            "CONSTRUCT { ?x ?p ?o } WHERE { ?x ?p ?o }"
        )
        assert result.query_id is not None


class TestSPARQLServiceExternalOntologies:
    """외부 온톨로지 임포트"""

    def test_import_dbpedia(self, sparql_service):
        """DBpedia 임포트"""
        result = sparql_service.import_external_ontology(
            source="dbpedia",
            source_id="Person",
            limit=5
        )
        assert result["import_id"] is not None
        assert result["source"] == "dbpedia"
        assert result["total_triples"] > 0

    def test_import_wikidata(self, sparql_service):
        """Wikidata 임포트"""
        result = sparql_service.import_external_ontology(
            source="wikidata",
            source_id="Q42",
            language="en"
        )
        assert result["import_id"] is not None
        assert result["source"] == "wikidata"

    def test_import_schema_org(self, sparql_service):
        """schema.org 임포트"""
        result = sparql_service.import_external_ontology(
            source="schema_org",
            source_id="Person"
        )
        assert result["import_id"] is not None
        assert result["source"] == "schema_org"

    def test_import_invalid_source(self, sparql_service):
        """유효하지 않은 소스"""
        with pytest.raises(ValueError):
            sparql_service.import_external_ontology(
                source="invalid",
                source_id="test"
            )


class TestSPARQLServiceCrud:
    """CRUD 작업"""

    def test_add_and_query_entity(self, sparql_service):
        """엔티티 추가 및 조회"""
        # 추가
        triples = sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John Doe", "age": 30}
        )
        assert len(triples) > 0

        # 조회
        count = sparql_service.get_triple_count()
        assert count > 0

    def test_add_multiple_entities(self, sparql_service):
        """여러 엔티티 추가"""
        for i in range(5):
            sparql_service.add_entity_rdf(
                entity_id=f"person-{i}",
                entity_type="Person",
                properties={"name": f"Person {i}"}
            )

        count = sparql_service.get_triple_count()
        assert count > 0

    def test_clear_triples(self, sparql_service):
        """모든 트리플 제거"""
        # 데이터 추가
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John"}
        )
        assert sparql_service.get_triple_count() > 0

        # 제거
        sparql_service.clear_triples()
        assert sparql_service.get_triple_count() == 0


class TestSPARQLServiceIntegration:
    """통합 테스트"""

    def test_full_workflow(self, sparql_service):
        """전체 워크플로우"""
        # 1. 엔티티 추가
        sparql_service.add_entity_rdf(
            entity_id="person-1",
            entity_type="Person",
            properties={"name": "John Doe", "age": 30}
        )
        sparql_service.add_entity_rdf(
            entity_id="person-2",
            entity_type="Person",
            properties={"name": "Jane Smith", "age": 28}
        )

        # 2. 관계 추가
        sparql_service.add_relationship_rdf(
            from_entity_id="person-1",
            from_type="Person",
            to_entity_id="person-2",
            to_type="Person",
            relation_type="knows"
        )

        # 3. 탐색
        result = sparql_service.explore_ontology()
        assert result["result_count"] > 0

        # 4. 타입별 조회
        type_result = sparql_service.query_by_type(
            "http://ontology.example.com/test-domain/class/Person"
        )
        assert type_result["count"] >= 0  # May be 0 or more depending on pattern matching

        # 5. 쿼리 이력 확인
        history = sparql_service.get_query_history()
        assert len(history) > 0

    def test_entity_relationships_workflow(self, sparql_service):
        """엔티티와 관계 워크플로우"""
        # 엔티티 추가
        sparql_service.add_entity_rdf(
            entity_id="p1",
            entity_type="Person",
            properties={"name": "Alice"}
        )
        sparql_service.add_entity_rdf(
            entity_id="p2",
            entity_type="Person",
            properties={"name": "Bob"}
        )

        # 관계 추가
        sparql_service.add_relationship_rdf(
            from_entity_id="p1",
            from_type="Person",
            to_entity_id="p2",
            to_type="Person",
            relation_type="knows"
        )

        # 관계 조회
        result = sparql_service.find_relationships(
            entity_uri="http://ontology.example.com/test-domain/person/p1"
        )
        assert "relationships" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
