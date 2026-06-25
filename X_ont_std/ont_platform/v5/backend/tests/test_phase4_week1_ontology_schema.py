"""Phase 4 Week 1: 온톨로지 스타일 및 스키마 통합 테스트"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from datetime import datetime
from app.models.ontology_schema import (
    OntologyStyle, PropertyType, Cardinality, PropertyDefinition,
    EntityType, RelationType, DomainSchema, RDFNamespace, SchemaConstraint
)
from app.repositories.schema_repository import SchemaRepository


@pytest.fixture
def schema_repo():
    """스키마 저장소"""
    repo = SchemaRepository()
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    yield repo
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


class TestOntologyStyle:
    """온톨로지 스타일 정의"""

    def test_style_enum_values(self):
        """스타일 Enum 정의 검증"""
        assert OntologyStyle.DOCUMENT.value == "document"
        assert OntologyStyle.RDF_TRIPLE.value == "rdf_triple"
        assert OntologyStyle.PROPERTY_GRAPH.value == "property_graph"
        assert OntologyStyle.SEMANTIC_WEB.value == "semantic_web"
        assert OntologyStyle.HIERARCHICAL.value == "hierarchical"
        assert OntologyStyle.MULTI_TYPED.value == "multi_typed"

    def test_property_types(self):
        """속성 타입 정의 검증"""
        assert PropertyType.STRING.value == "string"
        assert PropertyType.INTEGER.value == "integer"
        assert PropertyType.URI.value == "uri"
        assert PropertyType.JSON.value == "json"

    def test_cardinality_types(self):
        """카디널리티 정의 검증"""
        assert Cardinality.ONE_TO_ONE.value == "1:1"
        assert Cardinality.ONE_TO_MANY.value == "1:N"
        assert Cardinality.MANY_TO_MANY.value == "N:M"


class TestEntityTypeDefinition:
    """엔티티 타입 정의"""

    def test_create_entity_type(self):
        """엔티티 타입 생성"""
        entity_type = EntityType(
            name="PROJECT",
            display_name="프로젝트",
            description="AI 바우처 프로젝트",
            properties={
                "name": PropertyDefinition(
                    name="name",
                    display_name="프로젝트명",
                    property_type=PropertyType.STRING,
                    required=True
                ),
                "budget": PropertyDefinition(
                    name="budget",
                    display_name="예산",
                    property_type=PropertyType.INTEGER,
                    required=True
                )
            },
            parent_types=[],
            color="#FF6B6B"
        )

        assert entity_type.name == "PROJECT"
        assert "name" in entity_type.properties
        assert entity_type.properties["name"].required is True

    def test_entity_type_inheritance(self):
        """엔티티 타입 상속"""
        parent_type = EntityType(
            name="Entity",
            display_name="기본 엔티티",
            properties={}
        )

        child_type = EntityType(
            name="PROJECT",
            display_name="프로젝트",
            properties={},
            parent_types=["Entity"]
        )

        assert "Entity" in child_type.parent_types

    def test_entity_type_metadata_fields(self):
        """엔티티 타입 메타데이터 필드"""
        entity_type = EntityType(
            name="DOCUMENT",
            display_name="문서",
            properties={}
        )

        assert "created_by" in entity_type.metadata_fields
        assert "version" in entity_type.metadata_fields


class TestRelationTypeDefinition:
    """관계 타입 정의"""

    def test_create_relation_type(self):
        """관계 타입 생성"""
        rel_type = RelationType(
            name="manages",
            display_name="관리",
            from_type="PERSON",
            to_type="PROJECT",
            cardinality=Cardinality.ONE_TO_MANY,
            directed=True
        )

        assert rel_type.name == "manages"
        assert rel_type.from_type == "PERSON"
        assert rel_type.cardinality == Cardinality.ONE_TO_MANY

    def test_relation_with_properties(self):
        """관계 속성 정의"""
        rel_type = RelationType(
            name="employs",
            display_name="고용",
            from_type="ORGANIZATION",
            to_type="PERSON",
            properties={
                "start_date": PropertyDefinition(
                    name="start_date",
                    display_name="시작일",
                    property_type=PropertyType.DATETIME,
                    required=True
                ),
                "role": PropertyDefinition(
                    name="role",
                    display_name="직책",
                    property_type=PropertyType.STRING,
                    required=True
                )
            }
        )

        assert len(rel_type.properties) == 2
        assert "role" in rel_type.properties


class TestDomainSchemaCreation:
    """도메인 스키마 생성"""

    def test_create_property_graph_schema(self):
        """Property Graph 스타일 스키마 생성"""
        schema = DomainSchema(
            domain_id="ai-voucher-2025",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="AI 바우처 시스템",
            description="복잡한 다중 주체 관계 모델",
            entity_types={
                "PROJECT": EntityType(
                    name="PROJECT",
                    display_name="프로젝트",
                    properties={
                        "name": PropertyDefinition(
                            name="name",
                            display_name="이름",
                            property_type=PropertyType.STRING
                        )
                    }
                ),
                "PERSON": EntityType(
                    name="PERSON",
                    display_name="사람",
                    properties={}
                )
            },
            relation_types={
                "manages": RelationType(
                    name="manages",
                    display_name="관리",
                    from_type="PERSON",
                    to_type="PROJECT"
                )
            }
        )

        assert schema.ontology_style == OntologyStyle.PROPERTY_GRAPH
        assert "PROJECT" in schema.entity_types
        assert "manages" in schema.relation_types

    def test_create_hierarchical_schema(self):
        """계층적 스타일 스키마"""
        schema = DomainSchema(
            domain_id="org-structure",
            ontology_style=OntologyStyle.HIERARCHICAL,
            display_name="조직 구조",
            entity_types={
                "ORGANIZATION": EntityType(
                    name="ORGANIZATION",
                    display_name="조직",
                    properties={}
                ),
                "DEPARTMENT": EntityType(
                    name="DEPARTMENT",
                    display_name="부서",
                    properties={},
                    parent_types=["ORGANIZATION"]
                ),
                "TEAM": EntityType(
                    name="TEAM",
                    display_name="팀",
                    properties={},
                    parent_types=["DEPARTMENT"]
                )
            },
            relation_types={}
        )

        assert schema.ontology_style == OntologyStyle.HIERARCHICAL
        assert "DEPARTMENT" in schema.entity_types
        assert "ORGANIZATION" in schema.entity_types["DEPARTMENT"].parent_types

    def test_create_semantic_web_schema(self):
        """시맨틱 웹 스타일 스키마"""
        schema = DomainSchema(
            domain_id="knowledge-graph",
            ontology_style=OntologyStyle.SEMANTIC_WEB,
            display_name="지식 그래프",
            entity_types={},
            relation_types={},
            rdf_namespaces=[
                RDFNamespace(
                    prefix="kg",
                    uri="http://example.com/ontology/knowledge-graph#",
                    description="지식 그래프 네임스페이스"
                )
            ]
        )

        assert len(schema.rdf_namespaces) == 1
        assert schema.rdf_namespaces[0].prefix == "kg"


class TestSchemaRepository:
    """스키마 저장소 CRUD"""

    def test_save_and_get_schema(self, schema_repo):
        """스키마 저장 및 조회"""
        schema = DomainSchema(
            domain_id="test-domain",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="테스트 도메인",
            entity_types={
                "TEST": EntityType(
                    name="TEST",
                    display_name="테스트",
                    properties={}
                )
            },
            relation_types={}
        )

        schema_repo.save_schema(schema)
        retrieved = schema_repo.get_schema("test-domain")

        assert retrieved is not None
        assert retrieved.domain_id == "test-domain"
        assert retrieved.ontology_style == OntologyStyle.DOCUMENT

    def test_schema_exists(self, schema_repo):
        """스키마 존재 여부"""
        schema = DomainSchema(
            domain_id="existing-domain",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="기존 도메인",
            entity_types={},
            relation_types={}
        )

        assert not schema_repo.schema_exists("existing-domain")
        schema_repo.save_schema(schema)
        assert schema_repo.schema_exists("existing-domain")

    def test_list_domains(self, schema_repo):
        """모든 도메인 조회"""
        domains = ["domain-1", "domain-2", "domain-3"]
        for domain_id in domains:
            schema = DomainSchema(
                domain_id=domain_id,
                ontology_style=OntologyStyle.DOCUMENT,
                display_name=f"도메인 {domain_id}",
                entity_types={},
                relation_types={}
            )
            schema_repo.save_schema(schema)

        listed = schema_repo.list_domains()
        assert len(listed) == 3
        assert all(d in listed for d in domains)

    def test_delete_schema(self, schema_repo):
        """스키마 삭제"""
        schema = DomainSchema(
            domain_id="delete-me",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="삭제 대상",
            entity_types={},
            relation_types={}
        )

        schema_repo.save_schema(schema)
        assert schema_repo.schema_exists("delete-me")

        success = schema_repo.delete_schema("delete-me")
        assert success is True
        assert not schema_repo.schema_exists("delete-me")

    def test_get_schema_by_style(self, schema_repo):
        """스타일별 스키마 조회"""
        # Property Graph 스키마
        pg_schema = DomainSchema(
            domain_id="finance",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="금융",
            entity_types={},
            relation_types={}
        )

        # Hierarchical 스키마
        hier_schema = DomainSchema(
            domain_id="org",
            ontology_style=OntologyStyle.HIERARCHICAL,
            display_name="조직",
            entity_types={},
            relation_types={}
        )

        schema_repo.save_schema(pg_schema)
        schema_repo.save_schema(hier_schema)

        pg_schemas = schema_repo.get_schema_by_style(OntologyStyle.PROPERTY_GRAPH)
        hier_schemas = schema_repo.get_schema_by_style(OntologyStyle.HIERARCHICAL)

        assert len(pg_schemas) == 1
        assert len(hier_schemas) == 1
        assert pg_schemas[0].domain_id == "finance"
        assert hier_schemas[0].domain_id == "org"


class TestSchemaValidation:
    """스키마 검증"""

    def test_validate_valid_schema(self, schema_repo):
        """유효한 스키마 검증"""
        schema = DomainSchema(
            domain_id="valid-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="유효한 도메인",
            entity_types={
                "PROJECT": EntityType(
                    name="PROJECT",
                    display_name="프로젝트",
                    properties={}
                )
            },
            relation_types={
                "has": RelationType(
                    name="has",
                    display_name="포함",
                    from_type="PROJECT",
                    to_type="PROJECT"
                )
            }
        )

        result = schema_repo.validate_schema(schema)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_schema_missing_entity_types(self, schema_repo):
        """엔티티 타입 누락 검증"""
        schema = DomainSchema(
            domain_id="invalid-domain",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="잘못된 도메인",
            entity_types={},
            relation_types={}
        )

        result = schema_repo.validate_schema(schema)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_relation_type_mismatch(self, schema_repo):
        """관계 타입 불일치 검증"""
        schema = DomainSchema(
            domain_id="mismatch-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="불일치 도메인",
            entity_types={
                "PROJECT": EntityType(
                    name="PROJECT",
                    display_name="프로젝트",
                    properties={}
                )
            },
            relation_types={
                "manages": RelationType(
                    name="manages",
                    display_name="관리",
                    from_type="PERSON",  # 존재하지 않음
                    to_type="PROJECT"
                )
            }
        )

        result = schema_repo.validate_schema(schema)
        assert result.is_valid is False
        assert any("PERSON" in error for error in result.errors)


class TestSchemaCloning:
    """스키마 복제"""

    def test_clone_schema(self, schema_repo):
        """스키마 복제"""
        source_schema = DomainSchema(
            domain_id="source-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="원본 도메인",
            entity_types={
                "ENTITY": EntityType(
                    name="ENTITY",
                    display_name="엔티티",
                    properties={}
                )
            },
            relation_types={},
            tags=["important"]
        )

        schema_repo.save_schema(source_schema)

        # 복제
        cloned = schema_repo.clone_schema("source-domain", "cloned-domain", "admin")

        assert cloned is not None
        assert cloned.domain_id == "cloned-domain"
        assert cloned.ontology_style == source_schema.ontology_style
        assert "ENTITY" in cloned.entity_types
        assert "important" in cloned.tags


class TestSchemaVersioning:
    """스키마 버전 관리"""

    def test_update_schema_version(self, schema_repo):
        """스키마 버전 업데이트"""
        schema = DomainSchema(
            domain_id="versioned-domain",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="버전 관리 도메인",
            version="1.0",
            entity_types={},
            relation_types={}
        )

        schema_repo.save_schema(schema)

        # 버전 업데이트
        updated = schema_repo.update_schema_version("versioned-domain", "2.0", "admin")

        assert updated is not None
        assert updated.version == "2.0"
        assert updated.updated_by == "admin"

    def test_list_schema_versions(self, schema_repo):
        """스키마 버전 이력"""
        schema = DomainSchema(
            domain_id="version-history",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="버전 이력",
            entity_types={},
            relation_types={}
        )

        schema_repo.save_schema(schema)
        versions = schema_repo.list_schema_versions("version-history")

        assert len(versions) > 0
        assert versions[0]["version"] == "1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
