# JSONL → PostgreSQL 마이그레이션 스크립트

> **목적**: JSONL 파일 기반 트리플 스토어를 PostgreSQL로 무중단 마이그레이션  
> **작성일**: 2026-05-24  
> **상태**: 📋 설계, 🔴 구현 대기  
> **예상 데이터**: 현재 ~10K 트리플 → 목표 1M  

---

## 1. 마이그레이션 전략

### 1.1 3단계 마이그레이션

```
Phase A: 데이터 동기화 (1주)
├─ PostgreSQL 클러스터 구성
├─ JSONL → PostgreSQL 초기 로드
├─ 쓰기는 여전히 JSONL (메인 저장소)
├─ 읽기는 양쪽 검증
└─ 상태: Dual-Read

Phase B: 쓰기 전환 (3일)
├─ 신규 쓰기 → PostgreSQL로 우선
├─ 기존 데이터 배경 마이그레이션
├─ 읽기 마스터 → PostgreSQL 전환
└─ 상태: PostgreSQL Primary

Phase C: 정리 (1주)
├─ JSONL 백업 아카이브
├─ 코드에서 TripleStore 제거
├─ 최종 검증
└─ 상태: PostgreSQL Only
```

### 1.2 시간표

```
05-27 (월): Phase A 시작
└─ PostgreSQL 스키마 생성
└─ 초기 데이터 로드 (10K)

05-28 ~ 05-30 (화~목): 데이터 동기화
└─ 검증 쿼리 실행
└─ 성능 벤치마크

05-31 (금): Phase A 검증
└─ 읽기 일치도 검증 (예: 100개 쿼리 결과 비교)

06-01 (토): Phase B 시작
└─ 쓰기 로직 PostgreSQL 리다이렉트

06-02 ~ 06-03 (일~월): 배경 마이그레이션
└─ 기존 JSONL 데이터 비동기 복사

06-04 (화): Phase B 검증
└─ 읽기/쓰기 모두 PostgreSQL 동작 확인

06-05 (수): Phase C 시작
└─ JSONL 백업
└─ 코드 정리

06-06 (목): 최종 검증
└─ 성능 벤치마크
└─ 감사 추적 완성
```

---

## 2. Phase A: 초기 로드

### 2.1 PostgreSQL 환경 구성

```bash
#!/bin/bash
# scripts/setup_postgres.sh

# 1. Docker로 PostgreSQL 실행
docker-compose -f docker-compose.dev.yml up -d

# 2. 데이터베이스 생성
psql -U postgres -c "CREATE DATABASE ontology_db;"

# 3. 스키마 로드
psql -U postgres -d ontology_db < docs/schema.sql

# 4. 확인
psql -U postgres -d ontology_db -c "\dt"
# 출력: entities, relationships, audit_log, ontology_metadata
```

### 2.2 JSONL → PostgreSQL 초기 로드

```python
# scripts/migrate_jsonl_to_postgres.py

import json
import psycopg2
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONLMigrator:
    """JSONL 파일 → PostgreSQL 마이그레이션"""
    
    def __init__(self, jsonl_path: str, db_url: str):
        self.jsonl_path = Path(jsonl_path)
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()
        self.stats = {
            'entities_inserted': 0,
            'relationships_inserted': 0,
            'errors': 0
        }
    
    def migrate_all(self):
        """전체 마이그레이션 실행"""
        try:
            logger.info(f"마이그레이션 시작: {self.jsonl_path}")
            
            # 1. 메타데이터 읽기
            metadata = self._load_metadata()
            
            # 2. 트리플 처리
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                        
                        if data['type'] == 'metadata':
                            # 메타데이터는 스킵
                            continue
                        
                        elif data['type'] == 'triple':
                            self._process_triple(data['data'])
                        
                        if line_num % 1000 == 0:
                            logger.info(f"처리 완료: {line_num} 줄")
                            self.conn.commit()  # 주기적 커밋
                    
                    except Exception as e:
                        logger.error(f"줄 {line_num} 오류: {e}")
                        self.stats['errors'] += 1
                        continue
            
            # 3. 최종 커밋
            self.conn.commit()
            
            # 4. 통계 갱신
            self._update_metadata(metadata)
            
            logger.info(f"마이그레이션 완료: {self.stats}")
        
        finally:
            self.cursor.close()
            self.conn.close()
    
    def _load_metadata(self) -> dict:
        """메타데이터 추출"""
        with open(self.jsonl_path, 'r') as f:
            first_line = f.readline()
            data = json.loads(first_line)
            if data['type'] == 'metadata':
                return data['data']
        return {}
    
    def _process_triple(self, triple: dict):
        """단일 트리플 처리"""
        subject = triple.get('subject')
        predicate = triple.get('predicate')
        obj = triple.get('object')
        
        # 1. 주어 추출 (엔티티)
        self._ensure_entity(subject)
        
        # 2. 관계 확인
        if self._is_relationship(predicate):
            # 목적어도 엔티티여야 함
            self._ensure_entity(obj)
            self._insert_relationship(subject, predicate, obj)
        else:
            # 속성 추가
            self._add_property(subject, predicate, obj)
    
    def _ensure_entity(self, entity_id: str):
        """엔티티 존재 확인, 없으면 생성"""
        self.cursor.execute(
            "SELECT id FROM entities WHERE id = %s",
            (entity_id,)
        )
        
        if self.cursor.fetchone() is None:
            # 새로운 엔티티 생성
            self.cursor.execute(
                """INSERT INTO entities 
                (id, entity_type, domain_id, properties)
                VALUES (%s, %s, %s, %s)""",
                (entity_id, 'Unknown', 'migration', '{}')
            )
            self.stats['entities_inserted'] += 1
    
    def _is_relationship(self, predicate: str) -> bool:
        """술어가 관계인지 판단"""
        # 기본 제공 타입 술어는 관계 아님
        non_relationships = [
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
            'http://example.org/name',
            'http://example.org/age',
        ]
        return predicate not in non_relationships
    
    def _insert_relationship(self, from_id: str, rel_type: str, to_id: str):
        """관계 삽입"""
        rel_id = f"{from_id}_{rel_type}_{to_id}"
        
        try:
            self.cursor.execute(
                """INSERT INTO relationships 
                (id, from_entity_id, to_entity_id, relation_type, domain_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING""",
                (rel_id, from_id, to_id, rel_type, 'migration')
            )
            self.stats['relationships_inserted'] += 1
        except Exception as e:
            logger.warning(f"관계 삽입 실패 ({rel_id}): {e}")
    
    def _add_property(self, entity_id: str, predicate: str, value: str):
        """엔티티에 속성 추가"""
        # 술어에서 키 추출
        key = predicate.split('/')[-1].lower()
        
        self.cursor.execute(
            """UPDATE entities 
            SET properties = properties || %s
            WHERE id = %s""",
            (json.dumps({key: value}), entity_id)
        )
    
    def _update_metadata(self, original_metadata: dict):
        """메타데이터 갱신"""
        # 엔티티 수 계산
        self.cursor.execute("SELECT COUNT(*) FROM entities WHERE domain_id = 'migration'")
        entity_count = self.cursor.fetchone()[0]
        
        # 관계 수 계산
        self.cursor.execute("SELECT COUNT(*) FROM relationships WHERE domain_id = 'migration'")
        relationship_count = self.cursor.fetchone()[0]
        
        # 메타데이터 삽입
        domain_id = original_metadata.get('domain_id', 'ontology_v1')
        self.cursor.execute(
            """INSERT INTO ontology_metadata 
            (domain_id, entity_count, relationship_count, last_updated)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (domain_id) DO UPDATE
            SET entity_count = EXCLUDED.entity_count,
                relationship_count = EXCLUDED.relationship_count,
                last_updated = EXCLUDED.last_updated""",
            (domain_id, entity_count, relationship_count, datetime.now())
        )
        
        self.conn.commit()
        logger.info(f"메타데이터 갱신: {entity_count} entities, {relationship_count} relationships")

# 실행
if __name__ == '__main__':
    migrator = JSONLMigrator(
        jsonl_path='data/ontology.jsonl',
        db_url='postgresql://postgres:password@localhost:5432/ontology_db'
    )
    migrator.migrate_all()
```

### 2.3 데이터 검증

```python
# scripts/validate_migration.py

import json
import psycopg2
from pathlib import Path

def validate_migration(jsonl_path: str, db_url: str):
    """JSONL과 PostgreSQL 데이터 일치도 검증"""
    
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # 1. 엔티티 수 비교
    with open(jsonl_path, 'r') as f:
        jsonl_entities = sum(1 for line in f if json.loads(line)['type'] == 'triple')
    
    cursor.execute("SELECT COUNT(*) FROM entities WHERE domain_id = 'migration'")
    pg_entities = cursor.fetchone()[0]
    
    print(f"엔티티 수: JSONL={jsonl_entities}, PostgreSQL={pg_entities}")
    
    # 2. 샘플 쿼리 비교
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE domain_id = 'migration'")
    pg_relationships = cursor.fetchone()[0]
    
    print(f"관계 수: PostgreSQL={pg_relationships}")
    
    # 3. 세부 검증
    cursor.execute("""
        SELECT entity_type, COUNT(*) 
        FROM entities 
        WHERE domain_id = 'migration'
        GROUP BY entity_type
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    
    print("상위 5개 엔티티 타입:")
    for entity_type, count in cursor.fetchall():
        print(f"  {entity_type}: {count}")
    
    cursor.close()
    conn.close()
```

---

## 3. Phase B: 쓰기 전환

### 3.1 애플리케이션 코드 수정

```python
# app/services/ontology_service.py (Before)

class OntologyService:
    def __init__(self):
        self.triple_store = TripleStore(Path("data/ontology.jsonl"))
    
    def add_entity(self, entity_id, entity_type, properties):
        """JSONL에만 저장"""
        self.triple_store.add_triple(entity_id, 'rdf:type', entity_type)
        for key, value in properties.items():
            self.triple_store.add_triple(entity_id, f'ex:{key}', value)

# app/services/ontology_service.py (After)

from app.db.models import Entity, Relationship
from sqlalchemy.orm import Session

class OntologyService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def add_entity(self, entity_id: str, entity_type: str, properties: dict):
        """PostgreSQL에 저장"""
        entity = Entity(
            id=entity_id,
            entity_type=entity_type,
            domain_id='ontology_v1',
            properties=properties
        )
        self.db.add(entity)
        self.db.commit()
    
    def add_relationship(self, from_id: str, to_id: str, rel_type: str):
        """PostgreSQL에 저장"""
        relationship = Relationship(
            id=f"{from_id}_{rel_type}_{to_id}",
            from_entity_id=from_id,
            to_entity_id=to_id,
            relation_type=rel_type,
            domain_id='ontology_v1'
        )
        self.db.add(relationship)
        self.db.commit()
```

### 3.2 쓰기 리다이렉트 (애플리케이션 수준)

```python
# app/repositories/ontology.py (듀얼 쓰기 패턴)

class OntologyRepository:
    def __init__(self, db_session: Session, jsonl_path: Optional[Path] = None):
        self.db = db_session
        self.jsonl_path = jsonl_path  # None이면 PostgreSQL만 사용
        self.use_dual_write = jsonl_path is not None
    
    def save_entity(self, entity: Entity):
        """PostgreSQL에 쓰기"""
        self.db.add(entity)
        self.db.commit()
        
        # 선택: JSONL도 쓰기 (검증용)
        if self.use_dual_write:
            self._write_to_jsonl(entity)
    
    def _write_to_jsonl(self, entity: Entity):
        """JSONL에 쓰기 (배경)"""
        try:
            with open(self.jsonl_path, 'a') as f:
                data = {
                    'type': 'triple',
                    'data': {
                        'subject': entity.id,
                        'predicate': 'rdf:type',
                        'object': entity.entity_type
                    }
                }
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.warning(f"JSONL 쓰기 실패 (무시): {e}")

# 환경 변수로 제어
# ON_MIGRATE=true  → Dual-write
# ON_MIGRATE=false → PostgreSQL only
```

---

## 4. Phase C: 정리

### 4.1 JSONL 아카이브

```bash
#!/bin/bash
# scripts/archive_jsonl.sh

DATE=$(date +%Y%m%d)

# 1. 백업 생성
cp data/ontology.jsonl backups/ontology_${DATE}.jsonl

# 2. 압축
gzip backups/ontology_${DATE}.jsonl
# 결과: ontology_20260605.jsonl.gz (~100MB → ~10MB)

# 3. 확인
ls -lh backups/ontology_*.jsonl.gz
```

### 4.2 코드에서 TripleStore 제거

```python
# Before: app/services/sparql_service.py
from app.services.triple_store import TripleStore

class SPARQLService:
    def __init__(self, domain_id: str):
        self.store = TripleStore(...)  # ← 제거할 부분

# After: SPARQLService는 PostgreSQL만 사용
from app.db.models import Entity, Relationship
from sqlalchemy import select

class SPARQLService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def query(self, sparql_query: str):
        """PostgreSQL 백엔드 쿼리"""
        # SPARQL→SQL 번역기 사용
        sql = self.translator.translate(sparql_query)
        return self.db.execute(sql)
```

### 4.3 최종 검증

```bash
#!/bin/bash
# scripts/final_validation.sh

# 1. PostgreSQL 성능 벤치마크
pytest tests/performance/test_scale_validation.py -v

# 2. API 엔드포인트 테스트
pytest tests/integration/test_api_endpoints.py -v

# 3. SPARQL 호환성 테스트
pytest tests/integration/test_sparql_queries.py -v

# 4. 감사 로그 검증
psql -d ontology_db -c "SELECT COUNT(*) FROM audit_log;"

# 결과가 모두 성공이면 마이그레이션 완료
```

---

## 5. 롤백 계획

### 5.1 긴급 롤백 (Phase B 중)

```bash
#!/bin/bash
# scripts/rollback_phase_b.sh

# 1. 애플리케이션 설정 되돌리기
export ON_MIGRATE=false  # JSONL 기본값으로

# 2. 애플리케이션 재시작
systemctl restart ontology-api

# 3. PostgreSQL 데이터는 유지 (다시 마이그레이션 시 재사용)

# 4. 확인
curl http://localhost:8001/health
```

### 5.2 전체 롤백 (Phase A 중)

```bash
#!/bin/bash
# scripts/rollback_phase_a.sh

# 1. 새 데이터 삭제
psql -d ontology_db << EOF
DROP TABLE IF EXISTS relationships CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS ontology_metadata CASCADE;
EOF

# 2. JSONL 복구
cp backups/ontology_before_migration.jsonl.bak data/ontology.jsonl

# 3. 애플리케이션 재시작
systemctl restart ontology-api
```

---

## 6. 모니터링

### 6.1 마이그레이션 진행상황 추적

```sql
-- 마이그레이션 상태
SELECT 
    (SELECT COUNT(*) FROM entities WHERE domain_id = 'migration') as entities_migrated,
    (SELECT COUNT(*) FROM relationships WHERE domain_id = 'migration') as relationships_migrated,
    (SELECT COUNT(*) FROM audit_log) as changes_tracked;
```

### 6.2 성능 비교

```python
# scripts/benchmark_comparison.py

import time
from datetime import datetime

def benchmark():
    queries = [
        "SELECT ?x WHERE { ?x a ex:Person }",
        "SELECT ?p ?c WHERE { ?p ex:works_at ?c }",
        # ... 50개 쿼리
    ]
    
    results = {
        'jsonl_times': [],
        'postgres_times': []
    }
    
    for query in queries:
        # JSONL 성능 (Phase A)
        start = time.time()
        # results_jsonl = triple_store.query(query)
        results['jsonl_times'].append(time.time() - start)
        
        # PostgreSQL 성능 (Phase B)
        start = time.time()
        # results_pg = db.query(translated_sql)
        results['postgres_times'].append(time.time() - start)
    
    # 성능 비교
    jsonl_avg = sum(results['jsonl_times']) / len(results['jsonl_times'])
    pg_avg = sum(results['postgres_times']) / len(results['postgres_times'])
    
    print(f"평균 쿼리 시간")
    print(f"  JSONL: {jsonl_avg:.3f}ms")
    print(f"  PostgreSQL: {pg_avg:.3f}ms")
    print(f"  개선율: {jsonl_avg / pg_avg:.1f}배")
```

---

## 7. 체크리스트

### Phase A
- [ ] PostgreSQL 스키마 생성 (entities, relationships, audit_log)
- [ ] JSONL 초기 로드 (10K 트리플)
- [ ] 데이터 일치도 검증 (100% 일치)
- [ ] 읽기 쿼리 검증 (50개 샘플 쿼리)
- [ ] 성능 벤치마크 기준선 수립

### Phase B
- [ ] 애플리케이션 코드 수정 (JSONL → PostgreSQL)
- [ ] Dual-write 구현 (검증용)
- [ ] 배경 마이그레이션 실행 (24시간)
- [ ] 쓰기 일치도 검증
- [ ] 읽기/쓰기 모두 PostgreSQL 동작 확인

### Phase C
- [ ] JSONL 백업 (압축)
- [ ] 코드에서 TripleStore 제거
- [ ] 최종 성능 벤치마크 (개선율 확인)
- [ ] 감사 로그 완성도 검증
- [ ] 운영 가이드 작성

---

## 8. 자동화 스크립트 목록

| 스크립트 | 용도 | 실행 시점 |
|---------|------|---------|
| `setup_postgres.sh` | PostgreSQL 환경 | Phase A 시작 |
| `migrate_jsonl_to_postgres.py` | 초기 로드 | Phase A |
| `validate_migration.py` | 데이터 검증 | Phase A 완료 후 |
| `benchmark_comparison.py` | 성능 비교 | Phase B 완료 후 |
| `archive_jsonl.sh` | JSONL 아카이브 | Phase C |
| `rollback_phase_a.sh` | 긴급 롤백 | Phase A 중 오류 |
| `rollback_phase_b.sh` | Phase B 롤백 | Phase B 중 오류 |
| `final_validation.sh` | 최종 검증 | Phase C 완료 |

---

## 9. 예상 문제 및 해결책

| 문제 | 원인 | 해결책 |
|------|------|--------|
| **외래 키 제약** | 관계가 존재하지 않는 엔티티 참조 | 먼저 모든 엔티티 로드, 관계는 나중에 |
| **메모리 부족** | 대규모 JSONL 파일 | Batch 처리 (1000줄씩) |
| **중복 키** | 같은 ID로 여러 트리플 | `ON CONFLICT ... DO NOTHING` |
| **타입 불일치** | JSONL의 모호한 타입 | 모든 값을 문자열로 로드, 필요시 캐스팅 |
| **성능 저하** | 인덱스 미생성 상태 로드 | 로드 후 `REINDEX TABLE` 실행 |

---

## 10. 성공 기준

```
✅ Phase A 완료:
- JSONL 100% 데이터 PostgreSQL 로드
- 50개 샘플 쿼리 결과 100% 일치
- 성능 벤치마크 기준선 수립

✅ Phase B 완료:
- 신규 쓰기 PostgreSQL 저장 확인
- 기존 데이터 배경 마이그레이션 완료
- 읽기/쓰기 모두 PostgreSQL에서 동작

✅ Phase C 완료:
- JSONL 아카이브 (압축)
- TripleStore 코드 제거
- 성능 개선율 ≥ 10배 확인
- 감사 로그 완성도 100%
- 운영 문서 완성
```

---

**관련 문서**: 
- POSTGRES_MIGRATION_ROADMAP.md (일정)
- SCHEMA_DESIGN.md (DDL)
- SPARQL_TRANSLATOR_DESIGN.md (쿼리 변환)
