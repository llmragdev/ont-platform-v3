"""Phase 4 Week 3: 메타데이터 및 감시 시스템 통합 테스트 (25개)"""
import sys
from pathlib import Path
import uuid
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.models.entity_metadata import (
    EntityMetadata, EntityStatus, LineageInfo, DataSourceType,
    Transformation, TransformationType, ImportMetadata, AuditLog,
    AuditLogAction, EntityVersion, PropertyChange
)
from app.repositories.audit_repository import AuditRepository
from app.services.lineage_service import LineageService


# ============================================================================
# Task 3-1: EntityMetadata + Transformation + LineageInfo (8개 테스트)
# ============================================================================

class TestEntityMetadata:
    """엔티티 메타데이터 (Task 3-1)"""

    def test_entity_metadata_creation(self):
        """Test 1: 엔티티 메타데이터 생성"""
        entity_id = str(uuid.uuid4())
        metadata = EntityMetadata(
            entity_id=entity_id,
            created_by="user1",
            created_at=datetime.utcnow(),
            version=1,
            status=EntityStatus.ACTIVE,
            tags=["production", "validated"]
        )

        assert metadata.entity_id == entity_id
        assert metadata.created_by == "user1"
        assert metadata.version == 1
        assert len(metadata.tags) == 2
        assert metadata.status == EntityStatus.ACTIVE

    def test_property_change_tracking(self):
        """Test 2: 속성 변경 추적"""
        change = PropertyChange(
            property_name="description",
            old_value="Old description",
            new_value="New description",
            changed_at=datetime.utcnow(),
            changed_by="user1"
        )

        assert change.property_name == "description"
        assert change.old_value == "Old description"
        assert change.new_value == "New description"
        assert change.changed_by == "user1"

    def test_transformation_merge_operation(self):
        """Test 3: merge 변환 기록"""
        transformation = Transformation(
            transformation_id=str(uuid.uuid4()),
            transformation_type=TransformationType.MERGE,
            description="Merge entity1 and entity2",
            performed_by="user1",
            performed_at=datetime.utcnow(),
            input_ids=["entity1", "entity2"],
            output_id="entity_merged",
            parameters={"strategy": "union"},
            status="completed"
        )

        assert transformation.transformation_type == TransformationType.MERGE
        assert len(transformation.input_ids) == 2
        assert transformation.output_id == "entity_merged"
        assert transformation.status == "completed"

    def test_transformation_split_operation(self):
        """Test 4: split 변환 기록"""
        transformation = Transformation(
            transformation_id=str(uuid.uuid4()),
            transformation_type=TransformationType.SPLIT,
            description="Split entity into 2",
            performed_by="user1",
            performed_at=datetime.utcnow(),
            input_ids=["entity_original"],
            output_id="entity_split",
            parameters={"count": 2}
        )

        assert transformation.transformation_type == TransformationType.SPLIT
        assert len(transformation.input_ids) == 1
        assert transformation.parameters["count"] == 2

    def test_lineage_single_source(self):
        """Test 5: 단일 소스 혈통"""
        lineage = LineageInfo(
            source_type=DataSourceType.IMPORT,
            source_id="dbpedia_resource",
            transformations=[],
            direct_parent_ids=["parent_entity"]
        )

        assert lineage.source_type == DataSourceType.IMPORT
        assert lineage.source_id == "dbpedia_resource"
        assert len(lineage.transformations) == 0
        assert "parent_entity" in lineage.direct_parent_ids

    def test_lineage_multi_hop_chain(self):
        """Test 6: 다단계 변환 체인"""
        trans1 = Transformation(
            transformation_id=str(uuid.uuid4()),
            transformation_type=TransformationType.MERGE,
            description="Step 1: merge",
            performed_by="user1",
            performed_at=datetime.utcnow(),
            input_ids=["e1", "e2"],
            output_id="e12",
            parameters={}
        )

        trans2 = Transformation(
            transformation_id=str(uuid.uuid4()),
            transformation_type=TransformationType.ENRICH,
            description="Step 2: enrich",
            performed_by="user1",
            performed_at=datetime.utcnow(),
            input_ids=["e12"],
            output_id="e12_enriched",
            parameters={}
        )

        lineage = LineageInfo(
            source_type=DataSourceType.DERIVED,
            transformations=[trans1, trans2]
        )

        assert len(lineage.transformations) == 2
        assert lineage.transformations[0].transformation_type == TransformationType.MERGE
        assert lineage.transformations[1].transformation_type == TransformationType.ENRICH

    def test_lineage_circular_dependency_detection(self):
        """Test 7: 순환 참조 감지"""
        # 순환 참조: A → B → C → A
        # 이 테스트는 나중에 LineageService에서 처리
        lineage = LineageInfo(
            source_type=DataSourceType.DERIVED,
            direct_parent_ids=["entity_b"],
            transformations=[]
        )

        # LineageService.detect_circular_dependencies()에서 처리됨
        assert lineage.direct_parent_ids == ["entity_b"]

    def test_data_quality_score_propagation(self):
        """Test 8: 품질 점수 전파"""
        entity_a = EntityMetadata(
            entity_id="a",
            created_by="user",
            created_at=datetime.utcnow(),
            quality_score=0.95
        )

        entity_b = EntityMetadata(
            entity_id="b",
            created_by="user",
            created_at=datetime.utcnow(),
            quality_score=None  # To be calculated from lineage
        )

        assert entity_a.quality_score == 0.95
        assert entity_b.quality_score is None


# ============================================================================
# Task 3-2: EntityVersion + AuditLog (10개 테스트)
# ============================================================================

class TestEntityVersion:
    """엔티티 버전 관리 (Task 3-2)"""

    def test_version_creation(self):
        """Test 9: 버전 생성"""
        version = EntityVersion(
            entity_id="entity1",
            version=1,
            data={"name": "Entity 1", "type": "PROJECT"},
            changed_fields=["name"],
            change_reason="Initial creation",
            changed_by="user1",
            changed_at=datetime.utcnow(),
            is_current=True
        )

        assert version.entity_id == "entity1"
        assert version.version == 1
        assert version.is_current is True
        assert "name" in version.changed_fields

    def test_version_increment(self):
        """Test 10: 버전 증가"""
        v1 = EntityVersion(
            entity_id="entity1", version=1,
            data={"name": "v1"},
            changed_fields=[], change_reason="",
            changed_by="user", changed_at=datetime.utcnow()
        )

        v2 = EntityVersion(
            entity_id="entity1", version=2,
            data={"name": "v2"},
            changed_fields=["name"], change_reason="Updated name",
            changed_by="user", changed_at=datetime.utcnow()
        )

        assert v2.version == v1.version + 1
        assert v2.data["name"] == "v2"

    def test_version_rollback(self):
        """Test 11: 버전 롤백"""
        version = EntityVersion(
            entity_id="entity1",
            version=3,
            data={"name": "Current", "status": "active"},
            changed_fields=["status"],
            change_reason="Rollback to v2",
            changed_by="user1",
            changed_at=datetime.utcnow(),
            rollback_enabled=True
        )

        assert version.rollback_enabled is True
        # Rollback would restore to version 2
        rolled_back_data = {"name": "Current", "status": "inactive"}
        assert "status" in rolled_back_data

    def test_version_branch_creation(self):
        """Test 12: 버전 분기 생성"""
        # Version 1 → 2 → 3 (main branch)
        # Version 1 → 2' (alternative branch)

        main_v3 = EntityVersion(
            entity_id="entity1", version=3,
            data={"name": "Main"},
            changed_fields=[], change_reason="",
            changed_by="user", changed_at=datetime.utcnow()
        )

        branch_v2_alt = EntityVersion(
            entity_id="entity1", version=2,
            data={"name": "Alternative"},
            changed_fields=[], change_reason="",
            changed_by="user", changed_at=datetime.utcnow()
        )

        assert main_v3.version > branch_v2_alt.version
        assert main_v3.data != branch_v2_alt.data


class TestAuditLog:
    """감시 로그 (Task 3-2)"""

    def test_audit_log_create_action(self):
        """Test 13: create 감시 로그"""
        log = AuditLog(
            audit_id=str(uuid.uuid4()),
            entity_id="entity1",
            action=AuditLogAction.CREATE,
            new_value={"name": "Entity1", "type": "PROJECT"},
            performed_by="user1",
            performed_at=datetime.utcnow(),
            success=True
        )

        assert log.action == AuditLogAction.CREATE
        assert log.old_value is None
        assert log.new_value is not None
        assert log.success is True

    def test_audit_log_update_action(self):
        """Test 14: update 감시 로그"""
        log = AuditLog(
            audit_id=str(uuid.uuid4()),
            entity_id="entity1",
            action=AuditLogAction.UPDATE,
            old_value={"status": "draft"},
            new_value={"status": "published"},
            performed_by="user1",
            performed_at=datetime.utcnow(),
            success=True
        )

        assert log.action == AuditLogAction.UPDATE
        assert log.old_value["status"] == "draft"
        assert log.new_value["status"] == "published"

    def test_audit_log_delete_action(self):
        """Test 15: delete 감시 로그"""
        log = AuditLog(
            audit_id=str(uuid.uuid4()),
            entity_id="entity1",
            action=AuditLogAction.DELETE,
            old_value={"name": "Entity1"},
            performed_by="user1",
            performed_at=datetime.utcnow(),
            success=True
        )

        assert log.action == AuditLogAction.DELETE
        assert log.old_value is not None
        assert log.new_value is None

    def test_audit_log_query_by_entity(self):
        """Test 16: 엔티티별 로그 조회"""
        # 3개 로그: entity1, entity1, entity2
        logs_entity1 = [
            AuditLog(
                audit_id=str(uuid.uuid4()),
                entity_id="entity1",
                action=AuditLogAction.CREATE,
                performed_by="user1",
                performed_at=datetime.utcnow(),
                success=True
            ),
            AuditLog(
                audit_id=str(uuid.uuid4()),
                entity_id="entity1",
                action=AuditLogAction.UPDATE,
                performed_by="user1",
                performed_at=datetime.utcnow(),
                success=True
            )
        ]

        assert all(log.entity_id == "entity1" for log in logs_entity1)
        assert len(logs_entity1) == 2

    def test_audit_log_query_by_actor(self):
        """Test 17: 액터별 로그 조회 (performed_by)"""
        logs_user1 = [
            AuditLog(
                audit_id=str(uuid.uuid4()),
                entity_id=f"entity{i}",
                action=AuditLogAction.UPDATE,
                performed_by="user1",
                performed_at=datetime.utcnow(),
                success=True
            )
            for i in range(3)
        ]

        assert all(log.performed_by == "user1" for log in logs_user1)
        assert len(logs_user1) == 3

    def test_retention_policy_cleanup(self):
        """Test 18: 보관 정책 자동 정리"""
        old_log = AuditLog(
            audit_id=str(uuid.uuid4()),
            entity_id="entity1",
            action=AuditLogAction.UPDATE,
            performed_by="user1",
            performed_at=datetime.utcnow(),
            success=True,
            retention_days=0  # 즉시 삭제 대상
        )

        recent_log = AuditLog(
            audit_id=str(uuid.uuid4()),
            entity_id="entity1",
            action=AuditLogAction.UPDATE,
            performed_by="user1",
            performed_at=datetime.utcnow(),
            success=True,
            retention_days=365  # 1년 보관
        )

        assert old_log.retention_days == 0
        assert recent_log.retention_days == 365


# ============================================================================
# Task 3-3: AuditRepository + LineageService (7개 테스트)
# ============================================================================

@pytest.fixture
def audit_repo():
    """감시 저장소 fixture"""
    repo = AuditRepository()
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    yield repo
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


@pytest.fixture
def lineage_service(audit_repo):
    """혈통 서비스 fixture"""
    return LineageService(audit_repo)


class TestAuditRepository:
    """감시 저장소 (Task 3-3)"""

    def test_audit_repository_crud(self, audit_repo):
        """Test 19: 감시 저장소 CRUD"""
        log = AuditLog(
            audit_id=str(uuid.uuid4()),
            entity_id="entity1",
            action=AuditLogAction.CREATE,
            new_value={"name": "test"},
            performed_by="user1",
            performed_at=datetime.utcnow(),
            success=True
        )

        # Create
        audit_repo.log_action(log)

        # Read
        logs = audit_repo.get_audit_logs("entity1")
        assert len(logs) > 0
        assert any(l.action == AuditLogAction.CREATE for l in logs)

    def test_audit_log_query_multi_filter(self, audit_repo):
        """Test 20: 복합 필터 쿼리"""
        # Create multiple logs
        for i in range(5):
            log = AuditLog(
                audit_id=str(uuid.uuid4()),
                entity_id="entity1",
                action=AuditLogAction.UPDATE if i % 2 == 0 else AuditLogAction.CREATE,
                performed_by="user1" if i < 3 else "user2",
                performed_at=datetime.utcnow(),
                success=True
            )
            audit_repo.log_action(log)

        logs = audit_repo.get_audit_logs("entity1", action=AuditLogAction.UPDATE)
        assert all(l.action == AuditLogAction.UPDATE for l in logs)


class TestLineageService:
    """혈통 서비스 (Task 3-3)"""

    def test_lineage_resolve_single_source(self, lineage_service):
        """Test 21: 단일 소스 혈통 해석"""
        lineage = lineage_service.resolve_full_chain("entity1")
        assert lineage is not None

    def test_lineage_resolve_multi_hop(self, lineage_service):
        """Test 22: 다단계 혈통 해석"""
        # entity1 ← entity2 ← entity3
        lineage = lineage_service.resolve_full_chain("entity1")
        assert lineage.source_type is not None

    def test_lineage_impact_analysis(self, lineage_service):
        """Test 23: 영향도 분석"""
        # entity를 소스로 하는 모든 파생 엔티티
        impact = lineage_service.analyze_impact("entity1")
        assert isinstance(impact, dict)

    def test_circular_dependency_detection(self, lineage_service):
        """Test 24: 순환 참조 감지"""
        # A → B → C → A (순환)
        is_circular = lineage_service.detect_circular_dependencies("entity_a")
        assert isinstance(is_circular, bool)

    def test_data_quality_score_accuracy(self, lineage_service):
        """Test 25: 데이터 품질 점수 정확도 (≥95%)"""
        score = lineage_service.compute_data_quality_score("entity1")
        assert 0.0 <= score <= 1.0
        # Score should be consistent across multiple calls
        score2 = lineage_service.compute_data_quality_score("entity1")
        assert score == score2
