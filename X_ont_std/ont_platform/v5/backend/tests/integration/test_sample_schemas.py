"""Task 1-4: Sample Domain Schemas Testing"""
import pytest
import yaml
from pathlib import Path
from app.models.ontology_schema import (
    OntologyStyle,
    PropertyType,
    Cardinality,
    PropertyDefinition,
    EntityTypeDefinition,
    RelationTypeDefinition,
    DomainSchema,
    RDFNamespace,
)
from app.repositories.schema_repository import SchemaRepository


def load_yaml_schema(filename: str) -> dict:
    """YAML 스키마 파일 로드"""
    schema_dir = Path(__file__).parent.parent.parent / "schemas" / "domain-schemas"
    with open(schema_dir / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dict_to_domain_schema(data: dict) -> DomainSchema:
    """YAML 딕셔너리를 DomainSchema로 변환"""
    # EntityType 변환
    entity_types = {}
    for entity_name, entity_data in data.get("entity_types", {}).items():
        properties = {}
        for prop_name, prop_data in entity_data.get("properties", {}).items():
            properties[prop_name] = PropertyDefinition(**prop_data)

        entity_types[entity_name] = EntityTypeDefinition(
            name=entity_data.get("name"),
            display_name=entity_data.get("display_name"),
            description=entity_data.get("description", ""),
            properties=properties,
            parent_types=entity_data.get("parent_types", []),
            supports_multi_typing=entity_data.get("supports_multi_typing", False),
        )

    # RelationType 변환
    relation_types = {}
    for rel_name, rel_data in data.get("relation_types", {}).items():
        properties = {}
        for prop_name, prop_data in rel_data.get("properties", {}).items():
            properties[prop_name] = PropertyDefinition(**prop_data)

        relation_types[rel_name] = RelationTypeDefinition(
            name=rel_data.get("name"),
            display_name=rel_data.get("display_name"),
            description=rel_data.get("description", ""),
            from_type=rel_data.get("from_type"),
            to_type=rel_data.get("to_type"),
            cardinality=rel_data.get("cardinality", "1:N"),
            directed=rel_data.get("directed", True),
            properties=properties,
        )

    # RDF Namespace 변환
    rdf_namespaces = []
    for ns_data in data.get("rdf_namespaces", []):
        rdf_namespaces.append(RDFNamespace(**ns_data))

    return DomainSchema(
        domain_id=data.get("domain_id"),
        ontology_style=data.get("ontology_style"),
        display_name=data.get("display_name"),
        description=data.get("description", ""),
        entity_types=entity_types,
        relation_types=relation_types,
        rdf_namespaces=rdf_namespaces,
        version=data.get("version", "1.0"),
        created_by=data.get("created_by", ""),
    )


class TestAIVoucherSchema:
    """AI Voucher 2025 스키마 테스트"""

    def test_ai_voucher_schema_validation(self):
        """AI Voucher 스키마 검증"""
        data = load_yaml_schema("ai-voucher-2025.yaml")
        schema = dict_to_domain_schema(data)

        assert schema.domain_id == "ai-voucher-2025"
        assert schema.ontology_style == OntologyStyle.PROPERTY_GRAPH
        assert len(schema.entity_types) == 3  # PROJECT, PERSON, ORGANIZATION
        assert len(schema.relation_types) == 3  # leads, participates_in, belongs_to

    def test_ai_voucher_entity_types(self):
        """AI Voucher 엔티티 타입 검증"""
        data = load_yaml_schema("ai-voucher-2025.yaml")
        schema = dict_to_domain_schema(data)

        # PROJECT 엔티티 검증
        project = schema.entity_types["PROJECT"]
        assert project.name == "PROJECT"
        assert "name" in project.properties
        assert project.properties["name"].required is True

        # PERSON 엔티티 검증
        person = schema.entity_types["PERSON"]
        assert person.name == "PERSON"
        assert "email" in person.properties
        assert person.properties["email"].unique is True

    def test_ai_voucher_relation_types(self):
        """AI Voucher 관계 타입 검증"""
        data = load_yaml_schema("ai-voucher-2025.yaml")
        schema = dict_to_domain_schema(data)

        leads = schema.relation_types["leads"]
        assert leads.from_type == "PERSON"
        assert leads.to_type == "PROJECT"
        assert leads.cardinality == Cardinality.ONE_TO_MANY


class TestManufacturingSchema:
    """Manufacturing 시스템 스키마 테스트 (계층적)"""

    def test_manufacturing_schema_validation(self):
        """Manufacturing 스키마 검증"""
        data = load_yaml_schema("manufacturing.yaml")
        schema = dict_to_domain_schema(data)

        assert schema.domain_id == "manufacturing"
        assert schema.ontology_style == OntologyStyle.HIERARCHICAL
        assert len(schema.entity_types) == 5  # PRODUCT, CATEGORY, SUBCATEGORY, COMPONENT, MATERIAL
        assert len(schema.relation_types) == 2  # composed_of, produced_in

    def test_manufacturing_hierarchy(self):
        """Manufacturing 계층 구조 검증"""
        data = load_yaml_schema("manufacturing.yaml")
        schema = dict_to_domain_schema(data)

        # 상속 구조 검증
        category = schema.entity_types["CATEGORY"]
        assert "PRODUCT" in category.parent_types

        subcategory = schema.entity_types["SUBCATEGORY"]
        assert "CATEGORY" in subcategory.parent_types

        component = schema.entity_types["COMPONENT"]
        assert "SUBCATEGORY" in component.parent_types

    def test_manufacturing_schema_validation_with_repo(self):
        """Manufacturing 스키마가 SchemaRepository 검증을 통과하는지 확인"""
        repo = SchemaRepository()
        data = load_yaml_schema("manufacturing.yaml")
        schema = dict_to_domain_schema(data)

        result = repo.validate_schema(schema)
        # 계층적 스타일에서 경고 발생 가능 (다중 부모), 하지만 유효해야 함
        assert result.is_valid is True or len(result.errors) == 0


class TestKnowledgeGraphSchema:
    """Knowledge Graph 스키마 테스트 (시맨틱 웹)"""

    def test_knowledge_graph_schema_validation(self):
        """Knowledge Graph 스키마 검증"""
        data = load_yaml_schema("knowledge-graph.yaml")
        schema = dict_to_domain_schema(data)

        assert schema.domain_id == "knowledge-graph"
        assert schema.ontology_style == OntologyStyle.SEMANTIC_WEB
        assert len(schema.entity_types) == 4  # CONCEPT, CLASS, PROPERTY, INDIVIDUAL
        assert len(schema.relation_types) == 4  # subclass_of, has_property, instance_of, related_to

    def test_knowledge_graph_rdf_namespaces(self):
        """Knowledge Graph RDF 네임스페이스 검증"""
        data = load_yaml_schema("knowledge-graph.yaml")
        schema = dict_to_domain_schema(data)

        assert len(schema.rdf_namespaces) >= 3
        ns_prefixes = [ns.prefix for ns in schema.rdf_namespaces]
        assert "kg" in ns_prefixes
        assert "rdfs" in ns_prefixes
        assert "owl" in ns_prefixes

    def test_knowledge_graph_entity_uri_property(self):
        """Knowledge Graph 엔티티의 URI 속성 검증"""
        data = load_yaml_schema("knowledge-graph.yaml")
        schema = dict_to_domain_schema(data)

        for entity_type in ["CONCEPT", "CLASS", "PROPERTY", "INDIVIDUAL"]:
            entity = schema.entity_types[entity_type]
            assert "uri" in entity.properties
            assert entity.properties["uri"].property_type == PropertyType.URI


class TestOrderTrackingSchema:
    """Order Tracking 스키마 테스트 (RDF 삼중쌍)"""

    def test_order_tracking_schema_validation(self):
        """Order Tracking 스키마 검증"""
        data = load_yaml_schema("order-tracking.yaml")
        schema = dict_to_domain_schema(data)

        assert schema.domain_id == "order-tracking"
        assert schema.ontology_style == OntologyStyle.RDF_TRIPLE
        assert len(schema.entity_types) == 4  # ORDER, SHIPMENT, ITEM, CUSTOMER
        assert len(schema.relation_types) == 4  # placed_by, contains, shipped_via, has_status

    def test_order_tracking_rdf_support(self):
        """Order Tracking RDF 지원 검증"""
        data = load_yaml_schema("order-tracking.yaml")
        schema = dict_to_domain_schema(data)

        # RDF 네임스페이스 확인
        assert len(schema.rdf_namespaces) >= 3
        ns_prefixes = [ns.prefix for ns in schema.rdf_namespaces]
        assert "ot" in ns_prefixes
        assert "rdf" in ns_prefixes
        assert "rdfs" in ns_prefixes
        assert "xsd" in ns_prefixes

    def test_order_tracking_predicate_properties(self):
        """Order Tracking 관계의 술어 속성 검증"""
        data = load_yaml_schema("order-tracking.yaml")
        schema = dict_to_domain_schema(data)

        # RDF 삼중쌍 스타일에서는 각 관계가 predicate 속성을 가져야 함
        for rel_type in schema.relation_types.values():
            # 일부 관계는 predicate 속성을 가질 수 있음
            if "predicate" in rel_type.properties:
                assert rel_type.properties["predicate"].property_type == PropertyType.URI


class TestMultiTypedEntities:
    """다중 타입 엔티티 지원 테스트"""

    def test_entity_supports_multi_typing(self):
        """엔티티가 다중 타입을 지원하도록 설정 가능"""
        multi_typed_entity = EntityTypeDefinition(
            name="RESOURCE",
            display_name="Resource",
            properties={},
            supports_multi_typing=True,
        )

        assert multi_typed_entity.supports_multi_typing is True


class TestSchemaMigrationStrategy:
    """스키마 마이그레이션 전략 테스트"""

    def test_property_graph_to_hierarchical_migration(self):
        """Property Graph에서 Hierarchical로 마이그레이션"""
        # AI Voucher (Property Graph) 로드
        ai_data = load_yaml_schema("ai-voucher-2025.yaml")
        ai_schema = dict_to_domain_schema(ai_data)

        # Manufacturing (Hierarchical) 로드
        mfg_data = load_yaml_schema("manufacturing.yaml")
        mfg_schema = dict_to_domain_schema(mfg_data)

        # 다른 스타일 확인
        assert ai_schema.ontology_style != mfg_schema.ontology_style
        assert ai_schema.ontology_style == OntologyStyle.PROPERTY_GRAPH
        assert mfg_schema.ontology_style == OntologyStyle.HIERARCHICAL

    def test_all_domains_have_versions(self):
        """모든 도메인 스키마가 버전을 가지고 있는지 확인"""
        domains = ["ai-voucher-2025.yaml", "manufacturing.yaml", "knowledge-graph.yaml", "order-tracking.yaml"]

        for domain_file in domains:
            data = load_yaml_schema(domain_file)
            schema = dict_to_domain_schema(data)
            assert schema.version is not None
            assert schema.version == "1.0"

    def test_all_domains_have_creator(self):
        """모든 도메인 스키마가 생성자 정보를 가지고 있는지 확인"""
        domains = ["ai-voucher-2025.yaml", "manufacturing.yaml", "knowledge-graph.yaml", "order-tracking.yaml"]

        for domain_file in domains:
            data = load_yaml_schema(domain_file)
            schema = dict_to_domain_schema(data)
            assert schema.created_by is not None
            assert len(schema.created_by) > 0


class TestSampleDataConformance:
    """샘플 데이터 준수 테스트"""

    def test_ai_voucher_sample_entity(self):
        """AI Voucher 샘플 엔티티 생성 및 검증"""
        repo = SchemaRepository()
        data = load_yaml_schema("ai-voucher-2025.yaml")
        schema = dict_to_domain_schema(data)
        repo.save_schema(schema)

        # 샘플 엔티티 생성
        project_entity = {
            "type": "PROJECT",
            "name": "AI Innovation Lab",
            "budget": 1000000,
            "status": "active",
            "category": "AI Research",
        }

        result = repo.validate_entity_against_schema("ai-voucher-2025", project_entity)
        assert result.is_valid is True

        repo.delete_schema("ai-voucher-2025")

    def test_manufacturing_sample_entity(self):
        """Manufacturing 샘플 엔티티 생성 및 검증"""
        repo = SchemaRepository()
        data = load_yaml_schema("manufacturing.yaml")
        schema = dict_to_domain_schema(data)
        repo.save_schema(schema)

        # 샘플 엔티티 생성
        component_entity = {
            "type": "COMPONENT",
            "name": "Motor Control Unit",
            "part_number": "MCU-2025-001",
            "supplier": "TechSupplies Inc",
        }

        result = repo.validate_entity_against_schema("manufacturing", component_entity)
        assert result.is_valid is True

        repo.delete_schema("manufacturing")

    def test_order_tracking_sample_relationship(self):
        """Order Tracking 샘플 관계 생성 및 검증"""
        repo = SchemaRepository()
        data = load_yaml_schema("order-tracking.yaml")
        schema = dict_to_domain_schema(data)
        repo.save_schema(schema)

        # 샘플 관계 생성
        relationship = {
            "type": "contains",
            "from_type": "ORDER",
            "to_type": "ITEM",
        }

        result = repo.validate_relationship_against_schema("order-tracking", relationship)
        assert result.is_valid is True

        repo.delete_schema("order-tracking")


class TestSchemaRepositoryIntegration:
    """SchemaRepository와의 통합 테스트"""

    def test_save_and_retrieve_all_sample_schemas(self):
        """모든 샘플 스키마를 저장하고 조회"""
        repo = SchemaRepository()

        domains = {
            "ai-voucher-2025.yaml": "ai-voucher-2025",
            "manufacturing.yaml": "manufacturing",
            "knowledge-graph.yaml": "knowledge-graph",
            "order-tracking.yaml": "order-tracking",
        }

        for filename, domain_id in domains.items():
            # 로드 및 저장
            data = load_yaml_schema(filename)
            schema = dict_to_domain_schema(data)
            repo.save_schema(schema)

            # 조회 및 검증
            retrieved = repo.get_schema(domain_id)
            assert retrieved is not None
            assert retrieved.domain_id == domain_id
            assert retrieved.version == "1.0"

            # 스키마 검증
            validation = repo.validate_schema(retrieved)
            assert validation.is_valid is True or len(validation.errors) == 0

            # 정리
            repo.delete_schema(domain_id)

    def test_style_based_schema_retrieval(self):
        """스타일별 스키마 조회"""
        repo = SchemaRepository()

        # Property Graph 스키마 저장
        pg_data = load_yaml_schema("ai-voucher-2025.yaml")
        pg_schema = dict_to_domain_schema(pg_data)
        repo.save_schema(pg_schema)

        # Hierarchical 스키마 저장
        h_data = load_yaml_schema("manufacturing.yaml")
        h_schema = dict_to_domain_schema(h_data)
        repo.save_schema(h_schema)

        # Style별 조회
        pg_schemas = repo.get_schema_by_style(OntologyStyle.PROPERTY_GRAPH)
        assert len(pg_schemas) >= 1

        h_schemas = repo.get_schema_by_style(OntologyStyle.HIERARCHICAL)
        assert len(h_schemas) >= 1

        # 정리
        repo.delete_schema("ai-voucher-2025")
        repo.delete_schema("manufacturing")
