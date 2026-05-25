"""Phase 4 Week 2: 메타데이터 및 감시 시스템 통합 테스트"""
import sys
from pathlib import Path
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from datetime import datetime, timedelta
from app.models.entity_metadata import (
    EntityMetadata, EntityStatus, LineageInfo, DataSourceType,
    Transformation, TransformationType, ImportMetadata, AuditLog,
    AuditLogAction, EntityVersion
)
from app.repositories.audit_repository import AuditRepository
from app.services.lineage_service import LineageService


@pytest.fixture
def audit_repo():
    """감시 저장소"""
    repo = AuditRepository()
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    yield repo
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


@pytest.fixture
def lineage_service():
    """혈통 추적 서비스"""
    repo = AuditRepository()
    import shutil
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)
    repo.base_path.mkdir(parents=True, exist_ok=True)
    service = LineageService(repo)
    yield service
    if repo.base_path.exists():
        shutil.rmtree(repo.base_path)


class TestEntityMetadata:
    """엔티티 메타데이터"""

    def test_create_entity_metadata(self):
        """엔티티 메타데이터 생성"""
        metadata = EntityMetadata(
            entity_id="E001",
            created_by="user@company.com",
            created_at=datetime.utcnow(),
            version=1,
            status=EntityStatus.ACTIVE,
            tags=["important", "finance"],
            quality_score=0.95
        )

        assert metadata.entity_id == "E001"
        assert metadata.status == EntityStatus.ACTIVE
        assert "important" in metadata.tags

    def test_entity_metadata_with_lineage(self):
        """혈통이 포함된 메타데이터"""
        lineage = LineageInfo(
            source_type=DataSourceType.USER_INPUT,
            source_id="user-input-1"
        )

        metadata = EntityMetadata(
            entity_id="E002",
            created_by="admin@company.com",
            created_at=datetime.utcnow(),
            lineage=lineage
        )

        assert metadata.lineage is not None
        assert metadata.lineage.source_type == DataSourceType.USER_INPUT


class TestAuditLog:
    """감시 로그"""

    def test_create_audit_log(self):
        """감시 로그 생성"""
        log = AuditLog(
            audit_id="audit-001",
            entity_id="E001",
            action=AuditLogAction.CREATE,
            new_value={"name": "New Entity"},
            performed_by="user@company.com",
            performed_at=datetime.utcnow()
        )

        assert log.action == AuditLogAction.CREATE
        assert log.success is True

    def test_audit_log_with_failure(self):
        """실패한 감시 로그"""
        log = AuditLog(
            audit_id="audit-fail",
            entity_id="E001",
            action=AuditLogAction.UPDATE,
            old_value={"status": "active"},
            new_value={"status": "inactive"},
            performed_by="user@company.com",
            performed_at=datetime.utcnow(),
            success=False,
            error_message="Permission denied"
        )

        assert log.success is False
        assert "Permission" in log.error_message


class TestAuditRepository:
    """감시 저장소"""

    def test_log_action(self, audit_repo):
        """액션 기록"""
        log = AuditLog(
            audit_id="audit-log-001",
            entity_id="E001",
            action=AuditLogAction.CREATE,
            new_value={"name": "Entity 1"},
            performed_by="user@company.com",
            performed_at=datetime.utcnow()
        )

        audit_repo.log_action(log)

        # 조회
        logs = audit_repo.get_audit_logs("E001")
        assert len(logs) == 1
        assert logs[0].audit_id == "audit-log-001"

    def test_get_audit_logs(self, audit_repo):
        """감시 로그 조회"""
        for i in range(5):
            log = AuditLog(
                audit_id=f"audit-{i}",
                entity_id="E001",
                action=AuditLogAction.UPDATE,
                performed_by="user@company.com",
                performed_at=datetime.utcnow()
            )
            audit_repo.log_action(log)

        logs = audit_repo.get_audit_logs("E001")
        assert len(logs) == 5

    def test_get_logs_by_action(self, audit_repo):
        """액션별 로그 조회"""
        # CREATE 로그
        create_log = AuditLog(
            audit_id="create-log",
            entity_id="E001",
            action=AuditLogAction.CREATE,
            performed_by="user@company.com",
            performed_at=datetime.utcnow()
        )
        audit_repo.log_action(create_log)

        # UPDATE 로그 (2개)
        for i in range(2):
            update_log = AuditLog(
                audit_id=f"update-{i}",
                entity_id="E001",
                action=AuditLogAction.UPDATE,
                performed_by="user@company.com",
                performed_at=datetime.utcnow()
            )
            audit_repo.log_action(update_log)

        creates = audit_repo.get_logs_by_action("E001", AuditLogAction.CREATE)
        updates = audit_repo.get_logs_by_action("E001", AuditLogAction.UPDATE)

        assert len(creates) == 1
        assert len(updates) == 2

    def test_save_and_get_version(self, audit_repo):
        """버전 저장 및 조회"""
        version = EntityVersion(
            entity_id="E001",
            version=1,
            data={"name": "Entity 1", "status": "active"},
            changed_fields=["name", "status"],
            change_reason="Initial creation",
            changed_by="admin",
            changed_at=datetime.utcnow()
        )

        audit_repo.save_version(version)

        versions = audit_repo.get_versions("E001")
        assert len(versions) == 1
        assert versions[0].version == 1

    def test_get_current_version(self, audit_repo):
        """현재 버전 조회"""
        v1 = EntityVersion(
            entity_id="E001",
            version=1,
            data={"value": 1},
            changed_fields=["value"],
            change_reason="V1",
            changed_by="user",
            changed_at=datetime.utcnow(),
            is_current=False
        )
        v2 = EntityVersion(
            entity_id="E001",
            version=2,
            data={"value": 2},
            changed_fields=["value"],
            change_reason="V2",
            changed_by="user",
            changed_at=datetime.utcnow(),
            is_current=True
        )

        audit_repo.save_version(v1)
        audit_repo.save_version(v2)

        current = audit_repo.get_current_version("E001")
        assert current is not None
        assert current.version == 2

    def test_get_audit_summary(self, audit_repo):
        """감시 요약"""
        # 여러 액션 기록
        actions = [
            AuditLogAction.CREATE,
            AuditLogAction.UPDATE,
            AuditLogAction.UPDATE,
            AuditLogAction.DELETE
        ]

        for i, action in enumerate(actions):
            log = AuditLog(
                audit_id=f"summary-{i}",
                entity_id="E001",
                action=action,
                performed_by="user@company.com" if i % 2 == 0 else "admin@company.com",
                performed_at=datetime.utcnow()
            )
            audit_repo.log_action(log)

        summary = audit_repo.get_audit_summary("E001")
        assert summary is not None
        assert summary.total_changes == 4
        assert summary.changes_by_action[AuditLogAction.UPDATE.value] == 2

    def test_get_logs_in_timerange(self, audit_repo):
        """시간 범위 내 로그 조회"""
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        # 과거 로그
        old_log = AuditLog(
            audit_id="old",
            entity_id="E001",
            action=AuditLogAction.CREATE,
            performed_by="user",
            performed_at=past
        )
        # 현재 로그
        new_log = AuditLog(
            audit_id="new",
            entity_id="E001",
            action=AuditLogAction.UPDATE,
            performed_by="user",
            performed_at=now
        )

        audit_repo.log_action(old_log)
        audit_repo.log_action(new_log)

        # 현재 시간 근처만 조회
        logs = audit_repo.get_logs_in_timerange("E001", now - timedelta(minutes=5), now + timedelta(minutes=5))
        assert len(logs) == 1
        assert logs[0].audit_id == "new"

    def test_compare_versions(self, audit_repo):
        """버전 비교"""
        v1 = EntityVersion(
            entity_id="E001",
            version=1,
            data={"name": "Old", "status": "active"},
            changed_fields=["name", "status"],
            change_reason="V1",
            changed_by="user",
            changed_at=datetime.utcnow()
        )
        v2 = EntityVersion(
            entity_id="E001",
            version=2,
            data={"name": "New", "status": "inactive"},
            changed_fields=["name"],
            change_reason="V2",
            changed_by="user",
            changed_at=datetime.utcnow()
        )

        audit_repo.save_version(v1)
        audit_repo.save_version(v2)

        comparison = audit_repo.compare_versions("E001", 1, 2)
        assert "changes" in comparison
        assert "name" in comparison["changes"]
        assert comparison["changes"]["name"]["old"] == "Old"
        assert comparison["changes"]["name"]["new"] == "New"


class TestLineageInfo:
    """혈통 정보"""

    def test_create_lineage_from_user_input(self):
        """사용자 입력 혈통"""
        lineage = LineageInfo(
            source_type=DataSourceType.USER_INPUT,
            source_id="user-123"
        )

        assert lineage.source_type == DataSourceType.USER_INPUT

    def test_lineage_with_transformations(self):
        """변환이 포함된 혈통"""
        transform = Transformation(
            transformation_id="t-001",
            transformation_type=TransformationType.ENRICH,
            description="Added external data",
            performed_by="system",
            performed_at=datetime.utcnow(),
            input_ids=["E001", "E002"],
            output_id="E003",
            parameters={"enrichment_source": "API"}
        )

        lineage = LineageInfo(
            source_type=DataSourceType.DERIVED,
            transformations=[transform]
        )

        assert len(lineage.transformations) == 1
        assert lineage.transformations[0].transformation_type == TransformationType.ENRICH

    def test_lineage_with_import(self):
        """임포트 혈통"""
        import_meta = ImportMetadata(
            source_type=DataSourceType.IMPORT,
            source_name="DBpedia",
            source_id="http://dbpedia.org/resource/Company",
            imported_at=datetime.utcnow(),
            import_version="2026-05-20",
            original_format="RDF"
        )

        lineage = LineageInfo(
            source_type=DataSourceType.EXTERNAL_API,
            import_metadata=import_meta
        )

        assert lineage.import_metadata is not None
        assert lineage.import_metadata.source_name == "DBpedia"


class TestLineageService:
    """혈통 추적 서비스"""

    def test_record_and_get_lineage(self, lineage_service):
        """혈통 기록 및 조회"""
        lineage = LineageInfo(
            source_type=DataSourceType.USER_INPUT,
            source_id="user-input-1"
        )

        lineage_service.record_lineage("E001", lineage)
        retrieved = lineage_service.get_lineage("E001")

        assert retrieved is not None
        assert retrieved.source_type == DataSourceType.USER_INPUT

    def test_trace_upstream(self, lineage_service):
        """상류 추적"""
        # E1 → (변환) → E2 → (변환) → E3
        t1 = Transformation(
            transformation_id="t1",
            transformation_type=TransformationType.ENRICH,
            description="T1",
            performed_by="user",
            performed_at=datetime.utcnow(),
            input_ids=["E1"],
            output_id="E2",
            parameters={}
        )

        lineage2 = LineageInfo(
            source_type=DataSourceType.DERIVED,
            transformations=[t1],
            direct_parent_ids=["E1"]
        )
        lineage_service.record_lineage("E2", lineage2)

        graph = lineage_service.trace_upstream("E2")
        assert "E2" in graph.nodes or len(graph.edges) > 0

    def test_get_most_transformed_entities(self, lineage_service):
        """가장 많이 변환된 엔티티"""
        for i in range(3):
            transform = Transformation(
                transformation_id=f"t{i}",
                transformation_type=TransformationType.MERGE,
                description=f"Transform {i}",
                performed_by="user",
                performed_at=datetime.utcnow(),
                input_ids=["input"],
                output_id="E1",
                parameters={}
            )

            lineage = LineageInfo(
                source_type=DataSourceType.DERIVED,
                transformations=[transform]
            )
            lineage_service.record_lineage("E1", lineage)

        transformed = lineage_service.get_most_transformed_entities(limit=10)
        assert len(transformed) > 0
        assert transformed[0]["entity_id"] == "E1"
        assert transformed[0]["transformation_count"] == 1

    def test_get_data_sources_summary(self, lineage_service):
        """데이터 원천 요약"""
        lineage_service.record_lineage(
            "E1",
            LineageInfo(source_type=DataSourceType.USER_INPUT)
        )
        lineage_service.record_lineage(
            "E2",
            LineageInfo(source_type=DataSourceType.IMPORT)
        )
        lineage_service.record_lineage(
            "E3",
            LineageInfo(source_type=DataSourceType.USER_INPUT)
        )

        summary = lineage_service.get_data_sources_summary()
        assert DataSourceType.USER_INPUT.value in summary
        assert summary[DataSourceType.USER_INPUT.value]["count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
