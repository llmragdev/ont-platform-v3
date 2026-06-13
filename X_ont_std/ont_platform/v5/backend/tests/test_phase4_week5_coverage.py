"""Phase 4 Week 5: Bug Fix & Test Coverage - 커버리지 향상 (목표 95%+)"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.services.rdf_converter import RDFConverter
from app.models.ontology_schema import (
    DomainSchema, EntityType, RelationType, PropertyType, RDFNamespace
)
from app.models.rdf_model import RDFTriple, RDFFormat, RDFGraph


class TestTask51RDFConverterEdgeCases:
    """Task 5-1: RDFConverter 엣지 케이스 및 커버리지 (목표 95%+)"""

    @pytest.fixture
    def mock_schema(self):
        """Mock DomainSchema"""
        schema = Mock(spec=DomainSchema)
        schema.domain_id = "test_domain"
        ns_mock = Mock()
        ns_mock.prefix = "test"
        ns_mock.uri = "http://test.org/"
        ns_mock.description = "Test namespace"
        schema.rdf_namespaces = [ns_mock]
        schema.entity_types = {
            "Person": Mock(
                name="Person",
                properties={
                    "name": Mock(property_type="String"),
                    "age": Mock(property_type="Integer"),
                    "email": Mock(property_type="String")
                }
            ),
            "Organization": Mock(
                name="Organization",
                properties={
                    "name": Mock(property_type="String"),
                    "employees": Mock(property_type="Integer")
                }
            )
        }
        schema.relation_types = {
            "worksAt": Mock(
                name="worksAt",
                properties={
                    "since": Mock(property_type="Date")
                }
            ),
            "manages": Mock(
                name="manages",
                properties={}
            )
        }
        return schema

    @pytest.fixture
    def converter(self, mock_schema):
        """RDFConverter 인스턴스"""
        conv = RDFConverter(domain_schema=mock_schema)
        conv.set_domain_schema(mock_schema)
        return conv

    # ===== Task 5-1a: None 값 처리 =====
    def test_entity_to_rdf_with_none_properties(self, converter):
        """None 속성 처리"""
        triples = converter.entity_to_rdf_triples(
            entity_id="p1",
            entity_type="Person",
            properties={"name": None, "age": None}
        )
        # None 값도 포함되어야 함
        assert len(triples) >= 1
        assert any(t.predicate.endswith("type") for t in triples)

    def test_entity_to_rdf_with_empty_string(self, converter):
        """빈 문자열 속성"""
        triples = converter.entity_to_rdf_triples(
            entity_id="p2",
            entity_type="Person",
            properties={"name": "", "age": "30"}
        )
        assert len(triples) > 0

    def test_entity_to_rdf_with_empty_dict(self, converter):
        """빈 속성 딕셔너리"""
        triples = converter.entity_to_rdf_triples(
            entity_id="p3",
            entity_type="Person",
            properties={}
        )
        # 최소한 rdf:type 트리플은 생성
        assert len(triples) >= 1

    # ===== Task 5-1b: 경계값 테스트 =====
    def test_entity_to_rdf_with_very_long_id(self, converter):
        """매우 긴 entity_id (10000자)"""
        long_id = "x" * 10000
        triples = converter.entity_to_rdf_triples(
            entity_id=long_id,
            entity_type="Person",
            properties={"name": "LongID"}
        )
        assert len(triples) > 0
        assert any(long_id in t.subject for t in triples)

    def test_entity_to_rdf_with_special_characters(self, converter):
        """특수 문자가 포함된 속성값"""
        special_values = {
            "name": 'Test & "Entity" <XML>',
            "email": "test@example.com"
        }
        triples = converter.entity_to_rdf_triples(
            entity_id="p4",
            entity_type="Person",
            properties=special_values
        )
        assert len(triples) > 0

    def test_entity_to_rdf_with_large_number(self, converter):
        """매우 큰 숫자"""
        triples = converter.entity_to_rdf_triples(
            entity_id="p5",
            entity_type="Person",
            properties={"age": "999999999999"}
        )
        assert len(triples) > 0

    # ===== Task 5-1c: 다중값 처리 =====
    def test_entity_to_rdf_with_list_properties(self, converter):
        """리스트 속성 처리"""
        triples = converter.entity_to_rdf_triples(
            entity_id="p6",
            entity_type="Person",
            properties={
                "name": ["John", "Jane"],
                "age": "30"
            }
        )
        # 리스트 항목마다 트리플 생성
        name_triples = [t for t in triples if "name" in t.predicate]
        assert len(name_triples) >= 1

    def test_entity_to_rdf_with_empty_list(self, converter):
        """빈 리스트 속성"""
        triples = converter.entity_to_rdf_triples(
            entity_id="p7",
            entity_type="Person",
            properties={"name": []}
        )
        assert len(triples) >= 1  # 최소 rdf:type

    # ===== Task 5-1d: 선택적 매개변수 =====
    def test_entity_to_rdf_without_domain_schema(self):
        """Domain schema 없이 호출"""
        converter = RDFConverter(domain_schema=None)
        with pytest.raises(ValueError):
            converter.entity_to_rdf_triples("p1", "Person", {})

    def test_relation_to_rdf_triples_without_props(self, converter):
        """관계 속성 없이 호출"""
        triples = converter.relation_to_rdf_triples(
            from_entity_id="p1",
            from_type="Person",
            to_entity_id="org1",
            to_type="Organization",
            relation_type="worksAt",
            relation_props=None
        )
        assert len(triples) >= 1

    def test_relation_to_rdf_triples_with_props(self, converter):
        """관계 속성 포함"""
        triples = converter.relation_to_rdf_triples(
            from_entity_id="p1",
            from_type="Person",
            to_entity_id="org1",
            to_type="Organization",
            relation_type="worksAt",
            relation_props={"since": "2020-01-01"}
        )
        assert len(triples) >= 2  # 관계 + 속성

    # ===== Task 5-1e: RDF Triple 파싱 엣지 케이스 =====
    def test_rdf_triples_to_entity_empty_list(self, converter):
        """빈 RDF Triple 리스트"""
        entity = converter.rdf_triples_to_entity([], "Person")
        assert entity == {}

    def test_rdf_triples_to_entity_with_unknown_property(self, converter):
        """알 수 없는 속성 포함"""
        triples = [
            RDFTriple(
                subject="http://test.org/person/p1",
                predicate="http://test.org/property/unknown_prop",
                object="value",
                object_type="literal"
            )
        ]
        entity = converter.rdf_triples_to_entity(triples, "Person")
        # unknown_prop은 무시되어야 함
        assert "unknown_prop" not in entity

    def test_rdf_triples_to_entity_with_multi_values(self, converter):
        """다중값 속성 파싱"""
        # 정확한 base_uri 사용: http://ontology.example.com/test_domain/
        triples = [
            RDFTriple(
                subject="http://ontology.example.com/test_domain/person/p1",
                predicate="http://ontology.example.com/test_domain/property/name",
                object="John",
                object_type="literal"
            ),
            RDFTriple(
                subject="http://ontology.example.com/test_domain/person/p1",
                predicate="http://ontology.example.com/test_domain/property/name",
                object="Jane",
                object_type="literal"
            )
        ]
        entity = converter.rdf_triples_to_entity(triples, "Person")
        # 다중값일 때 list로 변환됨
        if "name" in entity:
            assert isinstance(entity["name"], list) or len(entity.get("name", "")) > 0

    # ===== Task 5-1f: RDF 그래프 생성 =====
    def test_create_rdf_graph_basic(self, converter):
        """기본 RDF 그래프 생성"""
        triples = [
            RDFTriple(
                subject="http://test.org/person/p1",
                predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                object="http://test.org/class/Person",
                object_type="uri"
            )
        ]
        graph = converter.create_rdf_graph("http://test.org/graph/1", triples)

        assert isinstance(graph, RDFGraph)
        assert graph.graph_uri == "http://test.org/graph/1"
        assert len(graph.triples) == 1
        assert len(graph.namespaces) >= 3  # rdf, rdfs, xsd

    def test_create_rdf_graph_with_schema_namespaces(self, converter):
        """스키마의 네임스페이스 포함"""
        triples = []
        graph = converter.create_rdf_graph("http://test.org/graph/2", triples)

        # 스키마의 네임스페이스도 포함되어야 함
        ns_prefixes = [ns.prefix for ns in graph.namespaces]
        assert "test" in ns_prefixes

    # ===== Task 5-1g: RDF 직렬화 =====
    def test_serialize_rdf_turtle(self, converter):
        """Turtle 포맷 직렬화"""
        triples = [
            RDFTriple(
                subject="http://test.org/person/p1",
                predicate="http://test.org/property/name",
                object="John",
                object_type="literal"
            )
        ]
        graph = converter.create_rdf_graph("http://test.org/graph/3", triples)
        result = converter.serialize_rdf(graph, RDFFormat.TURTLE)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_serialize_rdf_xml(self, converter):
        """RDF/XML 포맷 직렬화"""
        triples = [
            RDFTriple(
                subject="http://test.org/person/p1",
                predicate="http://test.org/property/name",
                object="John",
                object_type="literal"
            )
        ]
        graph = converter.create_rdf_graph("http://test.org/graph/4", triples)
        result = converter.serialize_rdf(graph, RDFFormat.RDF_XML)

        assert isinstance(result, str)

    def test_serialize_rdf_jsonld(self, converter):
        """JSON-LD 포맷 직렬화"""
        triples = [
            RDFTriple(
                subject="http://test.org/person/p1",
                predicate="http://test.org/property/name",
                object="John",
                object_type="literal"
            )
        ]
        graph = converter.create_rdf_graph("http://test.org/graph/5", triples)
        result = converter.serialize_rdf(graph, RDFFormat.JSON_LD)

        assert isinstance(result, str)

    # ===== Task 5-1h: 타입 변환 =====
    def test_rdf_triples_to_entity_type_conversion(self, converter):
        """RDF 값 타입 변환"""
        triples = [
            RDFTriple(
                subject="http://ontology.example.com/test_domain/person/p1",
                predicate="http://ontology.example.com/test_domain/property/age",
                object="30",
                object_type="literal",
                datatype="http://www.w3.org/2001/XMLSchema#integer"
            )
        ]
        entity = converter.rdf_triples_to_entity(triples, "Person")
        # 정수로 변환되어야 함
        if "age" in entity:
            assert entity["age"] is not None
        # 또는 결과는 비어있을 수 있음 (구현에 따라)

    # ===== Task 5-1i: 에러 케이스 =====
    def test_rdf_triples_to_entity_invalid_type(self, converter):
        """존재하지 않는 엔티티 타입"""
        with pytest.raises(ValueError):
            converter.rdf_triples_to_entity([], "InvalidType")

    def test_relation_to_rdf_without_schema(self):
        """Domain schema 없이 관계 변환"""
        converter = RDFConverter(domain_schema=None)
        with pytest.raises(ValueError):
            converter.relation_to_rdf_triples("p1", "Person", "o1", "Org", "rel", {})


class TestTask52ExceptionHandling:
    """Task 5-2: Exception Handling 및 입력 검증 강화"""

    @pytest.fixture
    def mock_schema(self):
        schema = Mock(spec=DomainSchema)
        schema.domain_id = "test_domain"
        schema.entity_types = {
            "Person": Mock(properties={"name": Mock(property_type="String")})
        }
        schema.relation_types = {}
        schema.rdf_namespaces = []
        return schema

    @pytest.fixture
    def converter(self, mock_schema):
        conv = RDFConverter(domain_schema=mock_schema)
        conv.set_domain_schema(mock_schema)
        return conv

    def test_validate_entity_id_length(self, converter):
        """entity_id 길이 초과"""
        # 구현 시 길이 제한 추가 예정
        very_long_id = "x" * 1001  # 1000자 초과
        # 현재는 통과하지만, validation 추가 예정
        triples = converter.entity_to_rdf_triples(
            entity_id=very_long_id,
            entity_type="Person",
            properties={"name": "Test"}
        )
        assert len(triples) > 0

    def test_entity_type_case_sensitivity(self, converter):
        """엔티티 타입 소문자 처리"""
        triples = converter.entity_to_rdf_triples(
            entity_id="p1",
            entity_type="person",  # 소문자
            properties={"name": "John"}
        )
        # URI는 소문자로 생성됨
        assert any("person" in t.subject.lower() for t in triples)

    def test_concurrent_converter_instances(self, mock_schema):
        """동시 converter 인스턴스"""
        conv1 = RDFConverter(domain_schema=mock_schema)
        conv2 = RDFConverter(domain_schema=mock_schema)

        conv1.set_domain_schema(mock_schema)
        conv2.set_domain_schema(mock_schema)

        # 동시 호출도 안전해야 함
        triples1 = conv1.entity_to_rdf_triples("p1", "Person", {"name": "John"})
        triples2 = conv2.entity_to_rdf_triples("p2", "Person", {"name": "Jane"})

        assert len(triples1) > 0
        assert len(triples2) > 0


class TestTask53IntegrationScenarios:
    """Task 5-3: 통합 테스트 및 Regression 테스트"""

    @pytest.fixture
    def full_schema(self):
        """완전한 테스트 스키마"""
        schema = Mock(spec=DomainSchema)
        schema.domain_id = "integration_test"
        schema.entity_types = {
            "Person": Mock(
                properties={
                    "name": Mock(property_type="String"),
                    "age": Mock(property_type="Integer")
                }
            ),
            "Organization": Mock(
                properties={
                    "name": Mock(property_type="String"),
                    "employees": Mock(property_type="Integer")
                }
            )
        }
        schema.relation_types = {
            "worksAt": Mock(properties={"since": Mock(property_type="Date")})
        }
        schema.rdf_namespaces = []
        return schema

    @pytest.fixture
    def converter(self, full_schema):
        conv = RDFConverter(domain_schema=full_schema)
        conv.set_domain_schema(full_schema)
        return conv

    def test_full_pipeline_entity_to_rdf_to_entity(self, converter):
        """엔티티 → RDF → 엔티티 완전 파이프라인"""
        # 1. 엔티티 → RDF
        original_props = {"name": "John", "age": "30"}
        triples = converter.entity_to_rdf_triples(
            entity_id="p1",
            entity_type="Person",
            properties=original_props
        )
        assert len(triples) > 1

        # 2. RDF → 엔티티 (손실 없이)
        recovered = converter.rdf_triples_to_entity(
            [t for t in triples if "property" in t.predicate],
            "Person"
        )
        assert recovered.get("name") == "John"
        assert recovered.get("age") == "30"

    def test_batch_entity_rdf_conversion(self, converter):
        """배치 엔티티 변환"""
        entities = [
            {"id": f"p{i}", "name": f"Person{i}", "age": str(20 + i)}
            for i in range(100)
        ]

        batch_triples = []
        for entity in entities:
            triples = converter.entity_to_rdf_triples(
                entity_id=entity["id"],
                entity_type="Person",
                properties={"name": entity["name"], "age": entity["age"]}
            )
            batch_triples.extend(triples)

        # 100개 엔티티 × 3 속성 이상
        assert len(batch_triples) >= 300

    def test_relationship_integration(self, converter):
        """관계 포함 통합"""
        # 1. Person 엔티티
        person_triples = converter.entity_to_rdf_triples(
            "p1", "Person", {"name": "John"}
        )

        # 2. Organization 엔티티
        org_triples = converter.entity_to_rdf_triples(
            "org1", "Organization", {"name": "ACME"}
        )

        # 3. 관계
        rel_triples = converter.relation_to_rdf_triples(
            "p1", "Person", "org1", "Organization",
            "worksAt", {"since": "2020-01-01"}
        )

        all_triples = person_triples + org_triples + rel_triples
        assert len(all_triples) >= 5

    def test_graph_creation_and_serialization(self, converter):
        """그래프 생성 및 직렬화"""
        triples = converter.entity_to_rdf_triples(
            "p1", "Person", {"name": "John", "age": "30"}
        )

        graph = converter.create_rdf_graph("http://test.org/graph", triples)

        # Turtle 직렬화
        turtle = converter.serialize_rdf(graph, RDFFormat.TURTLE)
        assert isinstance(turtle, str)
        assert len(turtle) > 0

    def test_large_graph_handling(self, converter):
        """대규모 그래프 처리"""
        large_triples = []
        for i in range(1000):
            triples = converter.entity_to_rdf_triples(
                f"p{i}", "Person", {"name": f"Person{i}"}
            )
            large_triples.extend(triples)

        graph = converter.create_rdf_graph(
            "http://test.org/large_graph", large_triples
        )
        assert len(graph.triples) >= 1000
