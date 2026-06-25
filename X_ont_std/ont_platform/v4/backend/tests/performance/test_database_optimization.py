import time
import pytest
from app.db.models import Entity, ImportedEntity, EntityMapping
from app.services.performance_monitor import PerformanceMonitor

class TestDatabaseQueryOptimization:
    """DB 쿼리 성능 검증"""

    @pytest.fixture(autouse=True)
    def setup_database_data(self, db_session):
        """벤치마크 수행 전 대용량(테스트 규모)의 데이터를 DB 세션에 삽입"""
        # 1. 1000개의 엔티티 삽입
        entities = []
        imported_entities = []
        mappings = []

        for i in range(1000):
            entity_id = f'entity-{i:04d}'
            entity = Entity(
                id=entity_id,
                entity_type='Person' if i % 2 == 0 else 'Organization',
                domain_id='test-domain',
                properties={'name': f'Entity Name {i}', 'index': i}
            )
            entities.append(entity)

            # 2. ImportedEntity 생성 (외부 매핑 1K개 시뮬레이션)
            external_uri = f'http://example.org/{i}'
            imported = ImportedEntity(
                entity_id=entity_id,
                external_uri=external_uri,
                source='dbpedia' if i % 2 == 0 else 'wikidata'
            )
            imported_entities.append(imported)

            # 3. EntityMapping 생성
            mapping = EntityMapping(
                internal_entity_id=entity_id,
                external_entity_id=external_uri,
                external_source='dbpedia' if i % 2 == 0 else 'wikidata',
                confidence=0.5 + (i % 50) / 100.0
            )
            mappings.append(mapping)

        # Bulk save
        db_session.add_all(entities)
        db_session.add_all(imported_entities)
        db_session.add_all(mappings)
        db_session.commit()

    def test_entity_lookup_performance(self, db_session):
        """단건 엔티티 조회 성능 (<10ms)"""
        entity_id = 'entity-0500'
        
        start = time.time()
        entity = db_session.query(Entity).filter_by(id=entity_id).first()
        elapsed = (time.time() - start) * 1000
        
        # 성능 모니터 기록
        PerformanceMonitor.record_db_query('entities', 'LOOKUP', elapsed)
        
        assert elapsed < 10, f"Entity lookup too slow: {elapsed:.2f}ms"
        assert entity is not None
        assert entity.id == entity_id

    def test_batch_entity_lookup_performance(self, db_session):
        """배치 엔티티 조회 (<50ms for 100 items)"""
        entity_ids = [f'entity-{i:04d}' for i in range(100, 200)]
        
        start = time.time()
        entities = db_session.query(Entity).filter(
            Entity.id.in_(entity_ids)
        ).all()
        elapsed = (time.time() - start) * 1000
        
        PerformanceMonitor.record_db_query('entities', 'BATCH_LOOKUP', elapsed)
        
        assert elapsed < 50, f"Batch entity lookup too slow: {elapsed:.2f}ms"
        assert len(entities) == 100

    def test_external_uri_deduplication_performance(self, db_session):
        """중복 제거 조회 성능 (<100ms for 1K URIs)"""
        external_uris = [f'http://example.org/{i}' for i in range(1000)]
        
        start = time.time()
        mappings = db_session.query(EntityMapping).filter(
            EntityMapping.external_entity_id.in_(external_uris)
        ).all()
        elapsed = (time.time() - start) * 1000
        
        PerformanceMonitor.record_db_query('entity_mappings', 'DEDUPLICATION', elapsed)
        
        assert elapsed < 100, f"Deduplication lookup too slow: {elapsed:.2f}ms"
        assert len(mappings) == 1000

    def test_import_history_query_performance(self, db_session):
        """임포트 이력 조회 (<50ms)"""
        source = 'dbpedia'
        
        start = time.time()
        imports = db_session.query(ImportedEntity).filter_by(
            source=source
        ).order_by(ImportedEntity.import_timestamp.desc()).limit(100).all()
        elapsed = (time.time() - start) * 1000
        
        PerformanceMonitor.record_db_query('imported_entities', 'HISTORY_QUERY', elapsed)
        
        assert elapsed < 50, f"Import history query too slow: {elapsed:.2f}ms"
        assert len(imports) == 100
