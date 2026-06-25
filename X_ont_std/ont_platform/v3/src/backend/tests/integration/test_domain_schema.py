"""Task 1-2: DomainSchema + EntityTypeDefinition + RelationTypeDefinition Tests"""
import pytest
from datetime import datetime
from app.models.ontology_schema import (
    OntologyStyle,
    PropertyType,
    Cardinality,
    PropertyDefinition,
    SchemaConstraint,
    EntityTypeDefinition,
    RelationTypeDefinition,
    DomainSchema,
)


class TestEntityTypeDefinitionInheritance:
    """엔티티 타입 상속 지원 검증"""

    def test_entity_type_with_inheritance(self):
        """엔티티 타입이 parent_types를 지원하는지 검증"""
        # 부모 엔티티 타입
        base_entity = EntityTypeDefinition(
            name="ENTITY",
            display_name="Base Entity",
            properties={
                "id": PropertyDefinition(
                    name="id",
                    display_name="ID",
                    property_type=PropertyType.STRING,
                    required=True,
                ),
            },
        )

        # 자식 엔티티 타입
        project_entity = EntityTypeDefinition(
            name="PROJECT",
            display_name="Project",
            properties={
                "name": PropertyDefinition(
                    name="name",
                    display_name="Project Name",
                    property_type=PropertyType.STRING,
                    required=True,
                ),
            },
            parent_types=["ENTITY"],  # ENTITY를 상속
        )

        assert project_entity.name == "PROJECT"
        assert project_entity.parent_types == ["ENTITY"]
        assert "name" in project_entity.properties

    def test_entity_type_multi_inheritance(self):
        """엔티티 타입이 다중 상속을 지원하는지 검증"""
        entity = EntityTypeDefinition(
            name="MANAGER",
            display_name="Manager",
            properties={},
            parent_types=["PERSON", "STAFF"],  # 다중 상속
        )

        assert len(entity.parent_types) == 2
        assert "PERSON" in entity.parent_types
        assert "STAFF" in entity.parent_types


class TestEntityTypeMetadataFields:
    """메타필드 자동 포함 검증"""

    def test_entity_type_default_metadata_fields(self):
        """메타필드가 기본값으로 설정되는지 검증"""
        entity = EntityTypeDefinition(
            name="PERSON",
            display_name="Person",
            properties={},
        )

        assert "created_by" in entity.metadata_fields
        assert "created_at" in entity.metadata_fields
        assert "updated_by" in entity.metadata_fields
        assert "updated_at" in entity.metadata_fields
        assert "version" in entity.metadata_fields

    def test_entity_type_custom_metadata_fields(self):
        """메타필드를 사용자 정의할 수 있는지 검증"""
        custom_fields = ["created_by", "created_at", "approved_by"]
        entity = EntityTypeDefinition(
            name="DOCUMENT",
            display_name="Document",
            properties={},
            metadata_fields=custom_fields,
        )

        assert entity.metadata_fields == custom_fields
        assert len(entity.metadata_fields) == 3


class TestRelationTypeCardinality:
    """관계 카디널리티 검증"""

    def test_relation_type_cardinality_1_1(self):
        """1:1 관계 검증"""
        rel = RelationTypeDefinition(
            name="manages",
            display_name="Manages",
            from_type="PERSON",
            to_type="DEPARTMENT",
            cardinality=Cardinality.ONE_TO_ONE,
        )

        assert rel.cardinality == Cardinality.ONE_TO_ONE
        assert rel.from_type == "PERSON"
        assert rel.to_type == "DEPARTMENT"

    def test_relation_type_cardinality_1_n(self):
        """1:N 관계 검증"""
        rel = RelationTypeDefinition(
            name="leads",
            display_name="Leads",
            from_type="PERSON",
            to_type="PROJECT",
            cardinality=Cardinality.ONE_TO_MANY,
        )

        assert rel.cardinality == Cardinality.ONE_TO_MANY

    def test_relation_type_cardinality_n_m(self):
        """N:M 관계 검증"""
        rel = RelationTypeDefinition(
            name="participates_in",
            display_name="Participates In",
            from_type="PERSON",
            to_type="PROJECT",
            cardinality=Cardinality.MANY_TO_MANY,
        )

        assert rel.cardinality == Cardinality.MANY_TO_MANY


class TestDomainSchemaValidation:
    """도메인 스키마 검증"""

    def test_domain_schema_entity_validation(self):
        """도메인 내 엔티티 타입 검증"""
        schema = DomainSchema(
            domain_id="test-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Test Domain",
            entity_types={
                "PROJECT": EntityTypeDefinition(
                    name="PROJECT",
                    display_name="Project",
                    properties={
                        "name": PropertyDefinition(
                            name="name",
                            display_name="Project Name",
                            property_type=PropertyType.STRING,
                            required=True,
                        ),
                    },
                ),
                "PERSON": EntityTypeDefinition(
                    name="PERSON",
                    display_name="Person",
                    properties={
                        "email": PropertyDefinition(
                            name="email",
                            display_name="Email",
                            property_type=PropertyType.STRING,
                            required=True,
                            unique=True,
                        ),
                    },
                ),
            },
            relation_types={},
        )

        assert "PROJECT" in schema.entity_types
        assert "PERSON" in schema.entity_types
        assert len(schema.entity_types) == 2

    def test_domain_schema_relation_validation(self):
        """도메인 내 관계 타입 검증"""
        schema = DomainSchema(
            domain_id="test-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Test Domain",
            entity_types={
                "PERSON": EntityTypeDefinition(
                    name="PERSON",
                    display_name="Person",
                    properties={},
                ),
                "PROJECT": EntityTypeDefinition(
                    name="PROJECT",
                    display_name="Project",
                    properties={},
                ),
            },
            relation_types={
                "leads": RelationTypeDefinition(
                    name="leads",
                    display_name="Leads",
                    from_type="PERSON",
                    to_type="PROJECT",
                    cardinality=Cardinality.ONE_TO_MANY,
                ),
            },
        )

        assert "leads" in schema.relation_types
        rel = schema.relation_types["leads"]
        assert rel.from_type == "PERSON"
        assert rel.to_type == "PROJECT"


class TestDomainSchemaVersioning:
    """스키마 버전 관리"""

    def test_domain_schema_versioning(self):
        """스키마 버전 관리 기능 검증"""
        schema = DomainSchema(
            domain_id="test-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Test Domain",
            entity_types={},
            relation_types={},
            version="2.0",
            created_by="test_user",
            created_at=datetime(2026, 5, 25, 10, 0, 0),
        )

        assert schema.version == "2.0"
        assert schema.created_by == "test_user"
        assert schema.created_at.year == 2026


class TestDomainSchemaStyleSpecific:
    """스타일별 스키마 구성"""

    def test_domain_schema_property_graph_style(self):
        """Property Graph 스타일 스키마 검증"""
        schema = DomainSchema(
            domain_id="property-graph-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Property Graph Domain",
            entity_types={
                "NODE": EntityTypeDefinition(
                    name="NODE",
                    display_name="Node",
                    properties={
                        "label": PropertyDefinition(
                            name="label",
                            display_name="Label",
                            property_type=PropertyType.STRING,
                        ),
                    },
                ),
            },
            relation_types={},
        )

        assert schema.ontology_style == OntologyStyle.PROPERTY_GRAPH

    def test_domain_schema_hierarchical_style(self):
        """Hierarchical 스타일 스키마 검증"""
        schema = DomainSchema(
            domain_id="hierarchical-domain",
            ontology_style=OntologyStyle.HIERARCHICAL,
            display_name="Hierarchical Domain",
            entity_types={
                "CATEGORY": EntityTypeDefinition(
                    name="CATEGORY",
                    display_name="Category",
                    properties={},
                    parent_types=["CATEGORY"],  # 계층 구조 지원
                ),
            },
            relation_types={},
        )

        assert schema.ontology_style == OntologyStyle.HIERARCHICAL


class TestDomainSchemaConstraints:
    """스키마 레벨 제약 조건"""

    def test_domain_schema_constraints(self):
        """스키마 레벨 제약 조건 검증"""
        constraints = [
            SchemaConstraint(
                constraint_type="cardinality",
                description="Each PERSON can lead at most 10 PROJECTs",
                condition={"max_targets": 10},
            ),
            SchemaConstraint(
                constraint_type="temporal",
                description="Project deadline must be in the future",
                condition={"type": "future_date"},
            ),
        ]

        schema = DomainSchema(
            domain_id="constrained-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Constrained Domain",
            entity_types={},
            relation_types={},
            constraints=constraints,
        )

        assert len(schema.constraints) == 2
        assert schema.constraints[0].constraint_type == "cardinality"
        assert schema.constraints[1].constraint_type == "temporal"


class TestEntityTypeMultiTyping:
    """다중 타입 지원 검증"""

    def test_entity_type_supports_multi_typing(self):
        """엔티티가 다중 타입을 지원할 수 있는지 검증"""
        entity = EntityTypeDefinition(
            name="RESOURCE",
            display_name="Resource",
            properties={},
            supports_multi_typing=True,
        )

        assert entity.supports_multi_typing is True

    def test_entity_type_style_specific_config(self):
        """스타일별 설정이 저장되는지 검증"""
        config = {
            "rdf_class": "http://example.org/Resource",
            "required_properties": ["id", "name"],
        }
        entity = EntityTypeDefinition(
            name="RESOURCE",
            display_name="Resource",
            properties={},
            style_specific_config=config,
        )

        assert entity.style_specific_config == config
        assert "rdf_class" in entity.style_specific_config


class TestRelationTypeProperties:
    """관계 속성 검증"""

    def test_relation_type_with_properties(self):
        """관계가 속성을 가질 수 있는지 검증"""
        rel = RelationTypeDefinition(
            name="employs",
            display_name="Employs",
            from_type="ORGANIZATION",
            to_type="PERSON",
            cardinality=Cardinality.ONE_TO_MANY,
            properties={
                "start_date": PropertyDefinition(
                    name="start_date",
                    display_name="Start Date",
                    property_type=PropertyType.DATETIME,
                ),
                "role": PropertyDefinition(
                    name="role",
                    display_name="Role",
                    property_type=PropertyType.STRING,
                ),
            },
        )

        assert "start_date" in rel.properties
        assert "role" in rel.properties
        assert len(rel.properties) == 2


class TestRelationTypeConstraints:
    """관계 제약 조건 검증"""

    def test_relation_type_with_constraints(self):
        """관계가 제약 조건을 가질 수 있는지 검증"""
        constraints = [
            SchemaConstraint(
                constraint_type="referential",
                description="Both entities must exist",
                condition={"type": "foreign_key"},
            ),
        ]

        rel = RelationTypeDefinition(
            name="references",
            display_name="References",
            from_type="TABLE_A",
            to_type="TABLE_B",
            constraints=constraints,
        )

        assert len(rel.constraints) == 1
        assert rel.constraints[0].constraint_type == "referential"


class TestCompleteSchemaIntegration:
    """완전한 스키마 통합 검증"""

    def test_complete_domain_schema_ai_voucher(self):
        """AI Voucher 도메인 전체 스키마 검증"""
        schema = DomainSchema(
            domain_id="ai-voucher-2025",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="AI Voucher 2025",
            description="AI 바우처 프로젝트 관리 시스템",
            entity_types={
                "PROJECT": EntityTypeDefinition(
                    name="PROJECT",
                    display_name="Project",
                    properties={
                        "name": PropertyDefinition(
                            name="name",
                            display_name="Project Name",
                            property_type=PropertyType.STRING,
                            required=True,
                            indexed=True,
                        ),
                        "budget": PropertyDefinition(
                            name="budget",
                            display_name="Budget",
                            property_type=PropertyType.INTEGER,
                        ),
                        "deadline": PropertyDefinition(
                            name="deadline",
                            display_name="Deadline",
                            property_type=PropertyType.DATETIME,
                        ),
                    },
                ),
                "PERSON": EntityTypeDefinition(
                    name="PERSON",
                    display_name="Person",
                    properties={
                        "email": PropertyDefinition(
                            name="email",
                            display_name="Email",
                            property_type=PropertyType.STRING,
                            required=True,
                            unique=True,
                        ),
                    },
                ),
            },
            relation_types={
                "leads": RelationTypeDefinition(
                    name="leads",
                    display_name="Leads",
                    from_type="PERSON",
                    to_type="PROJECT",
                    cardinality=Cardinality.ONE_TO_MANY,
                    properties={
                        "start_date": PropertyDefinition(
                            name="start_date",
                            display_name="Start Date",
                            property_type=PropertyType.DATETIME,
                        ),
                    },
                ),
            },
            version="1.0",
            created_by="admin",
        )

        assert schema.domain_id == "ai-voucher-2025"
        assert len(schema.entity_types) == 2
        assert len(schema.relation_types) == 1
        assert schema.version == "1.0"
        assert schema.created_by == "admin"
