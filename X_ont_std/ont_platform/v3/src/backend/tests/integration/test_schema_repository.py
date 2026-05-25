"""Task 1-3: SchemaRepository CRUD + Validation Tests"""
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from app.models.ontology_schema import (
    OntologyStyle,
    PropertyType,
    Cardinality,
    PropertyDefinition,
    SchemaConstraint,
    EntityTypeDefinition,
    RelationTypeDefinition,
    DomainSchema,
    RDFNamespace,
)
from app.repositories.schema_repository import SchemaRepository


@pytest.fixture
def schema_repo():
    """테스트용 SchemaRepository"""
    repo = SchemaRepository()
    yield repo
    # 테스트 후 생성된 스키마 삭제
    for domain_id in repo.list_domains():
        repo.delete_schema(domain_id)


@pytest.fixture
def sample_schema():
    """샘플 스키마"""
    return DomainSchema(
        domain_id="test-domain",
        ontology_style=OntologyStyle.PROPERTY_GRAPH,
        display_name="Test Domain",
        description="테스트용 도메인",
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
        relation_types={
            "leads": RelationTypeDefinition(
                name="leads",
                display_name="Leads",
                from_type="PERSON",
                to_type="PROJECT",
                cardinality=Cardinality.ONE_TO_MANY,
            ),
        },
        version="1.0",
        created_by="test_user",
    )


class TestSchemaCRUD:
    """Create, Read, Update, Delete 테스트"""

    def test_schema_create(self, schema_repo, sample_schema):
        """스키마 생성"""
        schema_repo.save_schema(sample_schema)
        assert schema_repo.schema_exists("test-domain")

    def test_schema_read(self, schema_repo, sample_schema):
        """스키마 읽기"""
        schema_repo.save_schema(sample_schema)
        retrieved = schema_repo.get_schema("test-domain")
        assert retrieved is not None
        assert retrieved.domain_id == "test-domain"
        assert len(retrieved.entity_types) == 2

    def test_schema_update(self, schema_repo, sample_schema):
        """스키마 업데이트"""
        schema_repo.save_schema(sample_schema)

        # 업데이트
        updated_schema = schema_repo.get_schema("test-domain")
        updated_schema.version = "2.0"
        updated_schema.updated_by = "updater"
        schema_repo.save_schema(updated_schema)

        # 확인
        retrieved = schema_repo.get_schema("test-domain")
        assert retrieved.version == "2.0"
        assert retrieved.updated_by == "updater"

    def test_schema_delete(self, schema_repo, sample_schema):
        """스키마 삭제"""
        schema_repo.save_schema(sample_schema)
        assert schema_repo.schema_exists("test-domain")

        deleted = schema_repo.delete_schema("test-domain")
        assert deleted is True
        assert not schema_repo.schema_exists("test-domain")

    def test_schema_delete_nonexistent(self, schema_repo):
        """존재하지 않는 스키마 삭제"""
        deleted = schema_repo.delete_schema("nonexistent")
        assert deleted is False


class TestSchemaRetrieval:
    """스키마 조회 테스트"""

    def test_schema_retrieval_by_domain(self, schema_repo):
        """도메인별 스키마 조회"""
        schema1 = DomainSchema(
            domain_id="domain-1",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Domain 1",
            entity_types={"ENTITY": EntityTypeDefinition(name="ENTITY", display_name="Entity", properties={})},
            relation_types={},
        )
        schema2 = DomainSchema(
            domain_id="domain-2",
            ontology_style=OntologyStyle.HIERARCHICAL,
            display_name="Domain 2",
            entity_types={"CATEGORY": EntityTypeDefinition(name="CATEGORY", display_name="Category", properties={})},
            relation_types={},
        )

        schema_repo.save_schema(schema1)
        schema_repo.save_schema(schema2)

        retrieved1 = schema_repo.get_schema("domain-1")
        retrieved2 = schema_repo.get_schema("domain-2")

        assert retrieved1.domain_id == "domain-1"
        assert retrieved2.domain_id == "domain-2"

    def test_schema_retrieval_by_style(self, schema_repo):
        """스타일별 스키마 조회"""
        # Property Graph 스타일 스키마
        pg_schema = DomainSchema(
            domain_id="pg-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Property Graph Domain",
            entity_types={"NODE": EntityTypeDefinition(name="NODE", display_name="Node", properties={})},
            relation_types={},
        )

        # Hierarchical 스타일 스키마
        h_schema = DomainSchema(
            domain_id="h-domain",
            ontology_style=OntologyStyle.HIERARCHICAL,
            display_name="Hierarchical Domain",
            entity_types={"CATEGORY": EntityTypeDefinition(name="CATEGORY", display_name="Category", properties={})},
            relation_types={},
        )

        schema_repo.save_schema(pg_schema)
        schema_repo.save_schema(h_schema)

        # Property Graph 스타일 스키마 조회
        pg_schemas = schema_repo.get_schema_by_style(OntologyStyle.PROPERTY_GRAPH)
        assert len(pg_schemas) == 1
        assert pg_schemas[0].domain_id == "pg-domain"

        # Hierarchical 스타일 스키마 조회
        h_schemas = schema_repo.get_schema_by_style(OntologyStyle.HIERARCHICAL)
        assert len(h_schemas) == 1
        assert h_schemas[0].domain_id == "h-domain"


class TestEntityValidation:
    """엔티티 검증 테스트"""

    def test_entity_validation_passes(self, schema_repo, sample_schema):
        """엔티티 검증 통과"""
        schema_repo.save_schema(sample_schema)

        # 유효한 엔티티
        entity = {
            "type": "PROJECT",
            "name": "My Project",
        }

        result = schema_repo.validate_entity_against_schema("test-domain", entity)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_entity_validation_fails_missing_required(self, schema_repo, sample_schema):
        """엔티티 검증 실패 - 필수 속성 없음"""
        schema_repo.save_schema(sample_schema)

        # 필수 속성 missing
        entity = {
            "type": "PROJECT",
            # "name" 필드가 없음
        }

        result = schema_repo.validate_entity_against_schema("test-domain", entity)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("필수 속성" in error for error in result.errors)

    def test_entity_validation_fails_invalid_type(self, schema_repo, sample_schema):
        """엔티티 검증 실패 - 유효하지 않은 타입"""
        schema_repo.save_schema(sample_schema)

        # 유효하지 않은 타입
        entity = {
            "type": "INVALID_TYPE",
            "name": "My Project",
        }

        result = schema_repo.validate_entity_against_schema("test-domain", entity)
        assert result.is_valid is False
        assert any("존재하지 않습니다" in error for error in result.errors)

    def test_entity_validation_invalid_domain(self, schema_repo):
        """엔티티 검증 - 유효하지 않은 도메인"""
        entity = {"type": "PROJECT"}
        result = schema_repo.validate_entity_against_schema("nonexistent-domain", entity)
        assert result.is_valid is False


class TestRelationshipValidation:
    """관계 검증 테스트"""

    def test_relationship_validation_passes(self, schema_repo, sample_schema):
        """관계 검증 통과"""
        schema_repo.save_schema(sample_schema)

        # 유효한 관계
        relationship = {
            "type": "leads",
            "from_type": "PERSON",
            "to_type": "PROJECT",
        }

        result = schema_repo.validate_relationship_against_schema("test-domain", relationship)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_relationship_validation_fails_invalid_from_type(self, schema_repo, sample_schema):
        """관계 검증 실패 - 유효하지 않은 from_type"""
        schema_repo.save_schema(sample_schema)

        # 유효하지 않은 from_type
        relationship = {
            "type": "leads",
            "from_type": "INVALID_TYPE",
            "to_type": "PROJECT",
        }

        result = schema_repo.validate_relationship_against_schema("test-domain", relationship)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_relationship_validation_fails_invalid_relation_type(self, schema_repo, sample_schema):
        """관계 검증 실패 - 유효하지 않은 관계 타입"""
        schema_repo.save_schema(sample_schema)

        # 유효하지 않은 관계 타입
        relationship = {
            "type": "invalid_relation",
            "from_type": "PERSON",
            "to_type": "PROJECT",
        }

        result = schema_repo.validate_relationship_against_schema("test-domain", relationship)
        assert result.is_valid is False


class TestSchemaConflictsDetection:
    """스키마 충돌 감지"""

    def test_schema_validation_detects_missing_entity_type(self, schema_repo):
        """스키마 검증 - 누락된 엔티티 타입 감지"""
        # 관계가 참조하는 엔티티 타입이 없음
        schema = DomainSchema(
            domain_id="conflict-domain",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Conflict Domain",
            entity_types={
                "PERSON": EntityTypeDefinition(name="PERSON", display_name="Person", properties={}),
            },
            relation_types={
                "leads": RelationTypeDefinition(
                    name="leads",
                    display_name="Leads",
                    from_type="PERSON",
                    to_type="PROJECT",  # PROJECT가 entity_types에 없음
                    cardinality=Cardinality.ONE_TO_MANY,
                ),
            },
        )

        result = schema_repo.validate_schema(schema)
        assert result.is_valid is False
        assert any("존재하지 않습니다" in error for error in result.errors)

    def test_schema_validation_detects_missing_parent_type(self, schema_repo):
        """스키마 검증 - 누락된 부모 타입 감지"""
        schema = DomainSchema(
            domain_id="inheritance-conflict",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Inheritance Conflict",
            entity_types={
                "PERSON": EntityTypeDefinition(
                    name="PERSON",
                    display_name="Person",
                    properties={},
                    parent_types=["NONEXISTENT"],  # 부모 타입이 없음
                ),
            },
            relation_types={},
        )

        result = schema_repo.validate_schema(schema)
        assert result.is_valid is False


class TestSchemaVersionTracking:
    """버전 추적 테스트"""

    def test_schema_version_tracking(self, schema_repo, sample_schema):
        """스키마 버전 추적"""
        schema_repo.save_schema(sample_schema)

        # 버전 업데이트
        updated = schema_repo.update_schema_version("test-domain", "2.0", "updater_user")
        assert updated is not None
        assert updated.version == "2.0"
        assert updated.updated_by == "updater_user"

        # 저장 확인
        retrieved = schema_repo.get_schema("test-domain")
        assert retrieved.version == "2.0"

    def test_schema_version_list(self, schema_repo, sample_schema):
        """스키마 버전 이력 조회"""
        schema_repo.save_schema(sample_schema)

        versions = schema_repo.list_schema_versions("test-domain")
        assert len(versions) >= 1
        assert versions[0]["version"] == "1.0"

    def test_schema_version_nonexistent(self, schema_repo):
        """존재하지 않는 스키마 버전"""
        versions = schema_repo.list_schema_versions("nonexistent")
        assert len(versions) == 0


class TestSchemaRepositoryIntegration:
    """SchemaRepository 통합 테스트"""

    def test_complete_workflow(self, schema_repo):
        """완전한 워크플로우"""
        # 1. 스키마 생성
        schema = DomainSchema(
            domain_id="workflow-test",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="Workflow Test",
            entity_types={
                "TASK": EntityTypeDefinition(
                    name="TASK",
                    display_name="Task",
                    properties={
                        "title": PropertyDefinition(
                            name="title",
                            display_name="Title",
                            property_type=PropertyType.STRING,
                            required=True,
                        ),
                    },
                ),
                "USER": EntityTypeDefinition(
                    name="USER",
                    display_name="User",
                    properties={
                        "username": PropertyDefinition(
                            name="username",
                            display_name="Username",
                            property_type=PropertyType.STRING,
                            required=True,
                            unique=True,
                        ),
                    },
                ),
            },
            relation_types={
                "assigned_to": RelationTypeDefinition(
                    name="assigned_to",
                    display_name="Assigned To",
                    from_type="TASK",
                    to_type="USER",
                    cardinality=Cardinality.MANY_TO_ONE,
                ),
            },
        )

        # 2. 스키마 저장
        schema_repo.save_schema(schema)
        assert schema_repo.schema_exists("workflow-test")

        # 3. 스키마 검증
        validation = schema_repo.validate_schema(schema)
        assert validation.is_valid is True

        # 4. 엔티티 검증
        task_entity = {"type": "TASK", "title": "Important Task"}
        entity_validation = schema_repo.validate_entity_against_schema("workflow-test", task_entity)
        assert entity_validation.is_valid is True

        # 5. 관계 검증
        relationship = {"type": "assigned_to", "from_type": "TASK", "to_type": "USER"}
        rel_validation = schema_repo.validate_relationship_against_schema("workflow-test", relationship)
        assert rel_validation.is_valid is True

        # 6. 버전 업데이트
        updated = schema_repo.update_schema_version("workflow-test", "1.1", "upgrader")
        assert updated.version == "1.1"

        # 7. 스키마 조회
        retrieved = schema_repo.get_schema("workflow-test")
        assert retrieved.version == "1.1"

        # 8. 스키마 삭제
        deleted = schema_repo.delete_schema("workflow-test")
        assert deleted is True
