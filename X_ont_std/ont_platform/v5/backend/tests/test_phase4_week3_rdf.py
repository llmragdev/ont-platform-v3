"""Phase 4 Week 3: RDF 변환 및 외부 온톨로지 통합 테스트"""
import sys
from pathlib import Path
import json
import uuid
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from datetime import datetime
from app.models.rdf_model import (
    RDFTriple, RDFFormat, RDFNamespace, RDFGraph, RDFResource,
    RDFDataType, ExternalOntologySource, ImportResult, SPARQLQuery,
    SPARQLResult, OntologyAlignment, ConceptMapping
)
from app.models.ontology_schema import (
    DomainSchema, OntologyStyle, EntityType, RelationType, PropertyDefinition,
    PropertyType, RDFNamespace as SchemaRDFNamespace
)
from app.services.rdf_converter import RDFConverter
from app.services.ontology_importer import OntologyImporter
from app.services.sparql_engine import SPARQLEngine


@pytest.fixture
def domain_schema():
    """테스트용 도메인 스키마"""
    return DomainSchema(
        domain_id="test-domain",
        name="Test Domain",
        display_name="Test Domain",
        description="Test domain for RDF conversion",
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
                    ),
                    "email": PropertyDefinition(
                        name="email",
                        display_name="Email",
                        description="Person's email",
                        property_type=PropertyType.STRING
                    )
                }
            ),
            "Organization": EntityType(
                name="Organization",
                display_name="Organization",
                description="An organization",
                properties={
                    "name": PropertyDefinition(
                        name="name",
                        display_name="Name",
                        description="Organization name",
                        property_type=PropertyType.STRING,
                        required=True
                    ),
                    "founded_date": PropertyDefinition(
                        name="founded_date",
                        display_name="Founded Date",
                        description="Founded date",
                        property_type=PropertyType.DATETIME
                    )
                }
            )
        },
        relation_types={
            "works_at": RelationType(
                name="works_at",
                display_name="Works At",
                description="Person works at organization",
                from_type="Person",
                to_type="Organization",
                properties={
                    "start_date": PropertyDefinition(
                        name="start_date",
                        display_name="Start Date",
                        description="Start date",
                        property_type=PropertyType.DATETIME
                    )
                }
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
def rdf_converter(domain_schema):
    """RDF 변환기"""
    converter = RDFConverter()
    converter.set_domain_schema(domain_schema)
    return converter


@pytest.fixture
def sparql_engine():
    """SPARQL 엔진"""
    return SPARQLEngine()


@pytest.fixture
def ontology_importer():
    """온톨로지 임포터"""
    return OntologyImporter()


class TestRDFTripleModels:
    """RDF Triple 및 모델 클래스"""

    def test_create_rdf_triple(self):
        """RDF Triple 생성"""
        triple = RDFTriple(
            subject="http://example.com/person/1",
            predicate="http://www.w3.org/2000/01/rdf-schema#label",
            object="John Doe",
            object_type="literal"
        )
        assert triple.subject == "http://example.com/person/1"
        assert triple.object == "John Doe"
        assert triple.object_type == "literal"

    def test_rdf_triple_with_datatype(self):
        """데이터 타입이 있는 RDF Triple"""
        triple = RDFTriple(
            subject="http://example.com/person/1",
            predicate="http://example.com/age",
            object="30",
            object_type="literal",
            datatype=RDFDataType.INTEGER.value
        )
        assert triple.datatype == RDFDataType.INTEGER.value

    def test_rdf_namespace_creation(self):
        """RDF 네임스페이스 생성"""
        ns = RDFNamespace(
            prefix="foaf",
            uri="http://xmlns.com/foaf/0.1/",
            description="Friend of a Friend"
        )
        assert ns.prefix == "foaf"
        assert ns.uri == "http://xmlns.com/foaf/0.1/"


class TestRDFConverter:
    """RDF 변환기 테스트"""

    def test_entity_to_rdf_triples(self, rdf_converter):
        """엔티티를 RDF Triple로 변환"""
        properties = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="person-1",
            entity_type="Person",
            properties=properties
        )
        assert len(triples) > 0
        # rdf:type 트리플 확인
        type_triples = [t for t in triples if "rdf-syntax-ns#type" in t.predicate]
        assert len(type_triples) > 0

    def test_relation_to_rdf_triples(self, rdf_converter):
        """관계를 RDF Triple로 변환"""
        triples = rdf_converter.relation_to_rdf_triples(
            from_entity_id="person-1",
            from_type="Person",
            to_entity_id="org-1",
            to_type="Organization",
            relation_type="works_at",
            relation_props={"start_date": "2020-01-01"}
        )
        assert len(triples) > 0
        # 관계 트리플 확인
        rel_triples = [t for t in triples if "relation" in t.predicate]
        assert len(rel_triples) > 0

    def test_rdf_graph_creation(self, rdf_converter, domain_schema):
        """RDF 그래프 생성"""
        properties = {"name": "Test Entity", "age": 25}
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="test-1",
            entity_type="Person",
            properties=properties
        )
        graph = rdf_converter.create_rdf_graph(
            graph_uri="http://example.com/graph/1",
            entities_and_relations=triples
        )
        assert graph.graph_uri == "http://example.com/graph/1"
        assert len(graph.triples) > 0

    def test_serialize_to_turtle(self, rdf_converter, domain_schema):
        """Turtle 형식 직렬화"""
        properties = {"name": "Test Entity", "age": 25}
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="test-1",
            entity_type="Person",
            properties=properties
        )
        graph = rdf_converter.create_rdf_graph(
            graph_uri="http://example.com/graph/1",
            entities_and_relations=triples
        )
        turtle = rdf_converter.serialize_rdf(graph, RDFFormat.TURTLE)
        assert isinstance(turtle, str)
        assert "@prefix" in turtle
        assert len(turtle) > 0

    def test_serialize_to_json_ld(self, rdf_converter, domain_schema):
        """JSON-LD 형식 직렬화"""
        properties = {"name": "Test Entity", "age": 25}
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="test-1",
            entity_type="Person",
            properties=properties
        )
        graph = rdf_converter.create_rdf_graph(
            graph_uri="http://example.com/graph/1",
            entities_and_relations=triples
        )
        json_ld = rdf_converter.serialize_rdf(graph, RDFFormat.JSON_LD)
        assert isinstance(json_ld, str)
        data = json.loads(json_ld)
        assert "@context" in data
        assert "@graph" in data


class TestOntologyImporter:
    """온톨로지 임포터 테스트"""

    def test_import_dbpedia(self, ontology_importer):
        """DBpedia 임포트"""
        result = ontology_importer.import_dbpedia(
            entity_type="Person",
            limit=5
        )
        assert isinstance(result, ImportResult)
        assert result.source_type == ExternalOntologySource.DBPEDIA
        assert result.imported_triples > 0
        assert result.failed_count == 0

    def test_import_wikidata(self, ontology_importer):
        """Wikidata 임포트"""
        result = ontology_importer.import_wikidata(
            entity_id="Q42",
            language="en"
        )
        assert isinstance(result, ImportResult)
        assert result.source_type == ExternalOntologySource.WIKIDATA
        assert result.imported_triples > 0

    def test_import_schema_org(self, ontology_importer):
        """schema.org 임포트"""
        result = ontology_importer.import_schema_org(
            schema_type="Person"
        )
        assert isinstance(result, ImportResult)
        assert result.source_type == ExternalOntologySource.SCHEMA_ORG
        assert result.imported_triples > 0

    def test_import_rdf_file(self, ontology_importer):
        """RDF 파일 임포트"""
        # 임시 Turtle 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write("""
            @prefix ex: <http://example.com/> .
            ex:person1 ex:name "John Doe" .
            ex:person1 ex:age "30" .
            """)
            temp_file = f.name

        try:
            result = ontology_importer.import_rdf_file(
                file_path=temp_file,
                domain_id="test-domain",
                format="turtle"
            )
            assert isinstance(result, ImportResult)
            assert result.source_type == ExternalOntologySource.CUSTOM
            assert result.imported_triples > 0
        finally:
            Path(temp_file).unlink()

    def test_get_import_result(self, ontology_importer):
        """임포트 결과 조회"""
        result1 = ontology_importer.import_dbpedia(
            entity_type="Person",
            limit=5
        )
        result2 = ontology_importer.get_import_result(result1.import_id)
        assert result2 is not None
        assert result2.import_id == result1.import_id


class TestSPARQLEngine:
    """SPARQL 엔진 테스트"""

    def test_add_and_query_triples(self, sparql_engine):
        """트리플 추가 및 쿼리"""
        triples = [
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://www.w3.org/2000/01/rdf-schema#label",
                object="John Doe",
                object_type="literal"
            ),
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                object="http://example.com/Person",
                object_type="uri"
            )
        ]
        sparql_engine.add_triples(triples)
        assert sparql_engine.get_triple_count() == 2

    def test_select_query(self, sparql_engine):
        """SELECT 쿼리 실행"""
        triples = [
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://example.com/name",
                object="John",
                object_type="literal"
            ),
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                object="http://example.com/Person",
                object_type="uri"
            )
        ]
        sparql_engine.add_triples(triples)

        query = SPARQLQuery(
            query_string="""
            SELECT ?x WHERE {
                ?x http://example.com/name "John"
            }
            """,
            query_type="SELECT"
        )
        result = sparql_engine.execute_query(query)
        assert isinstance(result, SPARQLResult)
        assert result.result_count >= 0
        assert result.execution_time_ms >= 0

    def test_ask_query(self, sparql_engine):
        """ASK 쿼리 실행"""
        triples = [
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://example.com/name",
                object="John",
                object_type="literal"
            )
        ]
        sparql_engine.add_triples(triples)

        query = SPARQLQuery(
            query_string="""
            ASK WHERE {
                ?x http://example.com/name "John"
            }
            """,
            query_type="ASK"
        )
        result = sparql_engine.execute_query(query)
        assert len(result.results) > 0
        assert "boolean" in result.results[0]

    def test_describe_query(self, sparql_engine):
        """DESCRIBE 쿼리 실행"""
        triples = [
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://example.com/name",
                object="John",
                object_type="literal"
            ),
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://example.com/age",
                object="30",
                object_type="literal"
            )
        ]
        sparql_engine.add_triples(triples)

        query = SPARQLQuery(
            query_string="DESCRIBE ?x",
            query_type="DESCRIBE"
        )
        result = sparql_engine.execute_query(query)
        assert isinstance(result, SPARQLResult)

    def test_query_history(self, sparql_engine):
        """쿼리 이력 조회"""
        triples = [
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://example.com/name",
                object="John",
                object_type="literal"
            )
        ]
        sparql_engine.add_triples(triples)

        query = SPARQLQuery(
            query_string="SELECT ?x WHERE { ?x http://example.com/name \"John\" }",
            query_type="SELECT"
        )
        sparql_engine.execute_query(query)
        sparql_engine.execute_query(query)

        history = sparql_engine.get_query_history(limit=10)
        assert len(history) >= 2

    def test_query_with_limit_and_offset(self, sparql_engine):
        """LIMIT/OFFSET를 포함한 쿼리"""
        triples = [
            RDFTriple(
                subject=f"http://example.com/person/{i}",
                predicate="http://example.com/name",
                object=f"Person {i}",
                object_type="literal"
            )
            for i in range(10)
        ]
        sparql_engine.add_triples(triples)

        query = SPARQLQuery(
            query_string="SELECT ?x WHERE { ?x http://example.com/name ?name }",
            query_type="SELECT",
            limit=5,
            offset=2
        )
        result = sparql_engine.execute_query(query)
        assert result.result_count <= 5

    def test_construct_query(self, sparql_engine):
        """CONSTRUCT 쿼리 실행"""
        triples = [
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://example.com/name",
                object="John",
                object_type="literal"
            ),
            RDFTriple(
                subject="http://example.com/person/1",
                predicate="http://example.com/age",
                object="30",
                object_type="literal"
            )
        ]
        sparql_engine.add_triples(triples)

        query = SPARQLQuery(
            query_string="""
            CONSTRUCT {
                ?x http://example.com/name ?name
            }
            WHERE {
                ?x http://example.com/name ?name
            }
            """,
            query_type="CONSTRUCT"
        )
        result = sparql_engine.execute_query(query)
        assert isinstance(result, SPARQLResult)

    def test_query_error_handling(self, sparql_engine):
        """쿼리 에러 처리"""
        query = SPARQLQuery(
            query_string="INVALID QUERY",
            query_type="UNKNOWN"
        )
        result = sparql_engine.execute_query(query)
        assert result.result_count == 0 or len(result.results) > 0


class TestRDFConversionRoundTrip:
    """RDF 변환 왕복 테스트"""

    def test_entity_to_rdf_to_entity(self, rdf_converter):
        """엔티티 → RDF → 엔티티 변환"""
        original_properties = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }

        # 엔티티 → RDF
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="person-1",
            entity_type="Person",
            properties=original_properties
        )

        # RDF → 엔티티
        reconstructed = rdf_converter.rdf_triples_to_entity(
            triples=triples,
            entity_type="Person"
        )

        assert reconstructed.get("name") == original_properties["name"]


class TestMultiFormatSerialization:
    """다중 형식 직렬화 테스트"""

    def test_rdf_xml_serialization(self, rdf_converter, domain_schema):
        """RDF/XML 형식 직렬화"""
        properties = {"name": "Test Entity"}
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="test-1",
            entity_type="Person",
            properties=properties
        )
        graph = rdf_converter.create_rdf_graph(
            graph_uri="http://example.com/graph/1",
            entities_and_relations=triples
        )
        rdf_xml = rdf_converter.serialize_rdf(graph, RDFFormat.RDF_XML)
        assert isinstance(rdf_xml, str)
        assert "<?xml" in rdf_xml
        assert "rdf:RDF" in rdf_xml

    def test_n_triples_serialization(self, rdf_converter, domain_schema):
        """N-Triples 형식 직렬화"""
        properties = {"name": "Test Entity"}
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="test-1",
            entity_type="Person",
            properties=properties
        )
        graph = rdf_converter.create_rdf_graph(
            graph_uri="http://example.com/graph/1",
            entities_and_relations=triples
        )
        n_triples = rdf_converter.serialize_rdf(graph, RDFFormat.N_TRIPLES)
        assert isinstance(n_triples, str)
        assert len(n_triples) > 0
        assert "." in n_triples  # N-Triples ends with period


class TestIntegrationRDFAndSPARQL:
    """RDF 변환 및 SPARQL 통합 테스트"""

    def test_full_rdf_to_sparql_workflow(self, rdf_converter, sparql_engine, domain_schema):
        """전체 RDF → SPARQL 워크플로우"""
        # 1. 엔티티를 RDF로 변환
        properties = {"name": "John Doe", "age": 30}
        triples = rdf_converter.entity_to_rdf_triples(
            entity_id="person-1",
            entity_type="Person",
            properties=properties
        )

        # 2. SPARQL 엔진에 트리플 추가
        sparql_engine.add_triples(triples)

        # 3. SPARQL 쿼리 실행
        query = SPARQLQuery(
            query_string="SELECT ?x WHERE { ?x http://ontology.example.com/test-domain/property/name ?name }",
            query_type="SELECT"
        )
        result = sparql_engine.execute_query(query)

        assert isinstance(result, SPARQLResult)
        assert result.execution_time_ms >= 0
        assert len(result.variables) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
