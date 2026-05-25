# PostgreSQL 스키마 설계

> **목적**: ont_platform v3의 데이터베이스 스키마 상세 정의  
> **데이터베이스**: PostgreSQL 14+  
> **작성일**: 2026-05-24  
> **상태**: 📋 설계 완료, 🔴 구현 대기  

---

## 1. 스키마 개요

### 1.1 핵심 테이블

```
┌─────────────────────────────────┐
│ entities (핵심)                 │
├─────────────────────────────────┤
│ id: VARCHAR(255) PRIMARY KEY    │
│ entity_type: VARCHAR(100)       │
│ domain_id: VARCHAR(100)         │
│ doc_id: VARCHAR(255)            │
│ properties: JSONB               │
│ version: INT                    │
│ created_at, updated_at: TS      │
└─────────────────────────────────┘
         ↓ (FK)
┌─────────────────────────────────┐
│ relationships (관계)            │
├─────────────────────────────────┤
│ id: VARCHAR(255) PRIMARY KEY    │
│ from_entity_id: FK              │
│ to_entity_id: FK                │
│ relation_type: VARCHAR(100)     │
│ properties: JSONB               │
│ version: INT                    │
│ created_at, updated_at: TS      │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ audit_log (감시)                │
├─────────────────────────────────┤
│ id: SERIAL PRIMARY KEY          │
│ domain_id: VARCHAR(100)         │
│ operation: VARCHAR(50)          │
│ entity_id: VARCHAR(255)         │
│ old_state: JSONB                │
│ new_state: JSONB                │
│ actor: VARCHAR(100)             │
│ timestamp: TIMESTAMP            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ontology_metadata (메타)        │
├─────────────────────────────────┤
│ domain_id: VARCHAR(100) PK      │
│ entity_count: INT               │
│ relationship_count: INT         │
│ last_updated: TIMESTAMP         │
│ metadata: JSONB                 │
└─────────────────────────────────┘
```

---

## 2. 상세 DDL

### 2.1 CREATE TABLE: entities

```sql
CREATE TABLE IF NOT EXISTS entities (
    -- 기본 키
    id VARCHAR(255) PRIMARY KEY,
    
    -- 분류
    entity_type VARCHAR(100) NOT NULL,
    
    -- 테넌트 + 문서
    domain_id VARCHAR(100) NOT NULL,
    doc_id VARCHAR(255),
    
    -- 속성 (반정형 데이터)
    properties JSONB DEFAULT '{}',
    
    -- 버전 관리 (낙관적 잠금)
    version INT DEFAULT 1 CHECK (version > 0),
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 제약사항
    CONSTRAINT entities_id_not_empty CHECK (id != ''),
    CONSTRAINT entities_type_not_empty CHECK (entity_type != ''),
    CONSTRAINT entities_domain_not_empty CHECK (domain_id != '')
);

-- 인덱스
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_domain ON entities(domain_id);
CREATE INDEX idx_entities_doc ON entities(doc_id);
CREATE INDEX idx_entities_properties ON entities USING GIN(properties);
CREATE INDEX idx_entities_created ON entities(created_at DESC);

-- Expression 인덱스 (자주 사용되는 properties 경로)
CREATE INDEX idx_entities_status ON entities((properties->>'status'));
CREATE INDEX idx_entities_name ON entities((properties->>'name'));

-- 변경 추적 트리거
CREATE TRIGGER entities_update_timestamp
BEFORE UPDATE ON entities
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
```

**용도 설명**:

| 컬럼 | 용도 | 예시 |
|------|------|------|
| `id` | 엔티티 고유 ID | `"entity_001"`, `"http://example.org/Person/1"` |
| `entity_type` | RDF 타입 | `"Person"`, `"Company"`, `"Project"` |
| `domain_id` | 온톨로지 도메인 | `"shipbuilding_v1"`, `"manufacturing_v2"` |
| `doc_id` | 출처 문서 | `"doc_20260101_001"` (혈통 추적) |
| `properties` | JSONB 속성 | `{"name": "Alice", "age": 30, "salary": 50000}` |
| `version` | 낙관적 잠금 | `1`, `2`, `3` (UPDATE 시 증가) |

**성능 고려사항**:

```
- entity_type: 가장 많이 필터링됨 (B-tree Index O)
- domain_id: 테넌트 격리 필요 (B-tree Index O)
- properties: JSONB 검색 (GIN Index + Expression Index)
- created_at: 시계열 쿼리 (DESC Index O)
```

---

### 2.2 CREATE TABLE: relationships

```sql
CREATE TABLE IF NOT EXISTS relationships (
    -- 기본 키
    id VARCHAR(255) PRIMARY KEY,
    
    -- 관계 정의
    from_entity_id VARCHAR(255) NOT NULL 
        REFERENCES entities(id) ON DELETE CASCADE,
    to_entity_id VARCHAR(255) NOT NULL 
        REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,
    
    -- 테넌트 + 문서
    domain_id VARCHAR(100) NOT NULL,
    doc_id VARCHAR(255),
    
    -- 관계 가중치 (선택)
    weight DECIMAL(10,2),
    
    -- 속성
    properties JSONB DEFAULT '{}',
    
    -- 버전 관리
    version INT DEFAULT 1 CHECK (version > 0),
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 제약사항
    CONSTRAINT relationships_id_not_empty CHECK (id != ''),
    CONSTRAINT relationships_type_not_empty CHECK (relation_type != ''),
    CONSTRAINT relationships_from_to CHECK (from_entity_id != to_entity_id)
);

-- 인덱스
CREATE INDEX idx_relationships_from ON relationships(from_entity_id);
CREATE INDEX idx_relationships_to ON relationships(to_entity_id);
CREATE INDEX idx_relationships_type ON relationships(relation_type);
CREATE INDEX idx_relationships_domain ON relationships(domain_id);
CREATE INDEX idx_relationships_created ON relationships(created_at DESC);

-- 복합 인덱스 (JOIN 성능)
CREATE INDEX idx_relationships_from_type ON relationships(from_entity_id, relation_type);
CREATE INDEX idx_relationships_to_type ON relationships(to_entity_id, relation_type);

-- 변경 추적 트리거
CREATE TRIGGER relationships_update_timestamp
BEFORE UPDATE ON relationships
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
```

**용도 설명**:

| 컬럼 | 용도 | 예시 |
|------|------|------|
| `from_entity_id` | 출발점 엔티티 | `"person_001"` |
| `to_entity_id` | 도착점 엔티티 | `"company_001"` |
| `relation_type` | 관계 종류 | `"works_at"`, `"knows"`, `"manages"` |
| `weight` | 관계 강도 (선택) | `0.9`, `1.0` (신뢰도) |

---

### 2.3 CREATE TABLE: audit_log

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    -- 기본 키
    id SERIAL PRIMARY KEY,
    
    -- 감사 대상
    domain_id VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255),  -- NULL이면 global operation
    
    -- 작업 종류
    operation VARCHAR(50) NOT NULL 
        CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'QUERY')),
    
    -- 상태 변경
    old_state JSONB,  -- 이전 상태 (UPDATE/DELETE시)
    new_state JSONB,  -- 새로운 상태 (INSERT/UPDATE시)
    
    -- 사용자/컨텍스트
    actor VARCHAR(100),  -- 사용자 ID
    actor_ip VARCHAR(45),  -- IPv4/IPv6
    
    -- 타임스탬프 (자동)
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 추가 메타데이터
    metadata JSONB DEFAULT '{}'
);

-- 인덱스
CREATE INDEX idx_audit_domain ON audit_log(domain_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_operation ON audit_log(operation);

-- 파티셔닝 (월별, 선택)
-- CREATE TABLE audit_log_202605 PARTITION OF audit_log
--     FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
```

**용도 설명**:

| 컬럼 | 용도 | 예시 |
|------|------|------|
| `operation` | CRUD 작업 | `"INSERT"`, `"UPDATE"`, `"DELETE"` |
| `old_state` | 변경 전 데이터 | `{"name": "Alice", "age": 29}` |
| `new_state` | 변경 후 데이터 | `{"name": "Alice", "age": 30}` |
| `actor` | 변경 수행자 | `"user_123"` |
| `metadata` | 추가 정보 | `{"reason": "birthday", "source": "api"}` |

---

### 2.4 CREATE TABLE: ontology_metadata

```sql
CREATE TABLE IF NOT EXISTS ontology_metadata (
    -- 기본 키
    domain_id VARCHAR(100) PRIMARY KEY,
    
    -- 버전 관리
    ontology_version VARCHAR(50),  -- "1.0.0", "2.1.0"
    schema_version INT DEFAULT 1,
    
    -- 통계
    entity_count INT DEFAULT 0,
    relationship_count INT DEFAULT 0,
    
    -- 상태
    status VARCHAR(50) DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'deprecated')),
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 메타데이터
    description TEXT,
    owner VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

-- 트리거
CREATE TRIGGER ontology_metadata_update_timestamp
BEFORE UPDATE ON ontology_metadata
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
```

---

### 2.5 CREATE TABLE: ontology_triples (View)

```sql
CREATE VIEW ontology_triples AS
-- rdf:type projection (엔티티 타입을 RDF 트리플로)
SELECT 
    CONCAT('entity:', e.id) AS subject,
    'rdf:type' AS predicate,
    CONCAT('type:', e.entity_type) AS object,
    'entity_type' AS triple_type,
    e.domain_id
FROM entities e

UNION ALL

-- 엔티티 속성을 트리플로 변환
SELECT 
    CONCAT('entity:', e.id) AS subject,
    CONCAT('property:', key) AS predicate,
    value::TEXT AS object,
    'entity_property' AS triple_type,
    e.domain_id
FROM entities e, 
     jsonb_each_text(e.properties) AS props(key, value)

UNION ALL

-- 관계를 트리플로 변환
SELECT
    CONCAT('entity:', r.from_entity_id) AS subject,
    CONCAT('relation:', r.relation_type) AS predicate,
    CONCAT('entity:', r.to_entity_id) AS object,
    'relationship' AS triple_type,
    r.domain_id
FROM relationships r;
```

**목적**: SPARQL 쿼리가 논리적으로 트리플을 본다.

---

## 3. 함수 정의

### 3.1 Timestamp 자동 갱신

```sql
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 3.2 엔티티 카운트 자동 갱신

```sql
CREATE OR REPLACE FUNCTION update_entity_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE ontology_metadata
    SET entity_count = (SELECT COUNT(*) FROM entities WHERE domain_id = NEW.domain_id)
    WHERE domain_id = NEW.domain_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER entities_count_trigger
AFTER INSERT OR DELETE ON entities
FOR EACH ROW
EXECUTE FUNCTION update_entity_count();
```

### 3.3 Version 관리 (낙관적 잠금)

```sql
CREATE OR REPLACE FUNCTION increment_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER entities_version_trigger
BEFORE UPDATE ON entities
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION increment_version();
```

---

## 4. 인덱싱 전략

### 4.1 인덱스 요약

| 테이블 | 인덱스 | 목적 | 크기 (예상) |
|--------|--------|------|-----------|
| **entities** | idx_entities_type | 타입별 조회 (가장 많음) | 100MB (1M행) |
| | idx_entities_domain | 테넌트 격리 | 100MB |
| | idx_entities_properties (GIN) | JSONB 쿼리 | 200MB |
| | idx_entities_created | 시계열 | 100MB |
| **relationships** | idx_relationships_from | JOIN 최적화 | 150MB |
| | idx_relationships_to | 역 조회 | 150MB |
| | idx_relationships_type | 관계 타입 필터 | 100MB |
| | idx_relationships_from_type (복합) | JOIN + 타입 | 150MB |
| **audit_log** | idx_audit_timestamp | 최근 조회 | 50MB |
| | idx_audit_domain | 테넌트별 감사 | 50MB |

### 4.2 인덱스 크기 예측

```sql
-- 1M 엔티티 기준
원본 entities 테이블:     ~500MB
└─ idx_entities_type:    ~100MB
└─ idx_entities_domain:  ~100MB
└─ idx_entities_properties: ~200MB
└─ idx_entities_created: ~100MB
총 인덱스:               ~500MB

비율: 인덱스/원본 = 1.0x (바람직함)
```

### 4.3 인덱스 유지보수

```sql
-- 정기적 재구성 (주간)
REINDEX TABLE entities;
REINDEX TABLE relationships;

-- 통계 갱신 (자동)
ANALYZE entities;
ANALYZE relationships;

-- 인덱스 크기 확인
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## 5. 성능 고려사항

### 5.1 JSONB vs 정규화 테이블

**선택**: JSONB 속성

```
✅ 장점:
- 스키마 변화에 유연 (온톨로지 진화)
- 집계 불필요 (속성이 동적)
- GIN 인덱싱 + Expression Index로 빠른 JSONB 조회

❌ 단점:
- 복잡한 쿼리는 SQL이 길어짐
- 타입 캐스팅 필요 (::INTEGER 등)

예시 쿼리:
SELECT * FROM entities 
WHERE (properties->>'age')::INTEGER > 25
```

### 5.2 트랜잭션 격리 레벨

**기본값**: `SERIALIZABLE` (가장 엄격)

```sql
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- 동시 쓰기 충돌 자동 감지 및 실패
UPDATE entities SET version = version + 1 WHERE id = 'entity_1';
COMMIT;  -- 또는 ROLLBACK

-- 애플리케이션에서 재시도
```

### 5.3 동시성 제어 (낙관적 잠금)

```sql
-- 업데이트 시 version 확인
UPDATE entities 
SET properties = $1, version = version + 1
WHERE id = $2 AND version = $3
RETURNING id, version;

-- 영향 행이 0이면 충돌 (누군가 먼저 수정함)
```

---

## 6. 백업 및 복구

### 6.1 전체 백업

```bash
# 폴더 포맷 (병렬화 가능)
pg_dump --format=directory --jobs=4 \
    --host=localhost --username=postgres \
    ontology_db > /backups/ontology_20260524.dump

# 복구
pg_restore --format=directory --jobs=4 \
    --host=localhost --username=postgres \
    --dbname=ontology_db /backups/ontology_20260524.dump
```

### 6.2 WAL (Write-Ahead Log)

```bash
# PostgreSQL 기본 제공 (자동)
# 변경사항 자동 기록 (pg_wal/)
# 시점 복구(Point-in-Time Recovery) 가능
```

### 6.3 정기 유지보수

```sql
-- 주간 VACUUM (삭제 공간 정리)
VACUUM ANALYZE entities;
VACUUM ANALYZE relationships;

-- 월간 REINDEX
REINDEX TABLE CONCURRENTLY entities;
REINDEX TABLE CONCURRENTLY relationships;
```

---

## 7. 마이그레이션 (JSONL → PostgreSQL)

### 7.1 마이그레이션 스크립트

```python
# scripts/migrate_jsonl_to_postgres.py

import json
from pathlib import Path
import psycopg2

def migrate():
    # 1. JSONL 파일 읽기
    with open('ontology.jsonl', 'r') as f:
        for line in f:
            triple = json.loads(line)
            if triple['type'] == 'triple':
                # 트리플 저장
                insert_triple(triple['data'])
    
    # 2. 통계 갱신
    cursor.execute("ANALYZE entities;")
    cursor.execute("ANALYZE relationships;")
    
    # 3. 메타데이터 갱신
    update_metadata()

def insert_triple(data):
    """RDF 트리플 → 관계형 행"""
    subject, predicate, obj = data['subject'], data['predicate'], data['object']
    
    if predicate == 'rdf:type':
        # 엔티티 타입 설정
        INSERT INTO entities VALUES (...)
    else:
        # 속성 추가
        UPDATE entities SET properties = properties || jsonb_build_object(...)
```

---

## 8. 보안

### 8.1 역할 기반 접근 제어 (RBAC)

```sql
-- 역할 생성
CREATE ROLE ontology_user LOGIN PASSWORD 'secure_password';
CREATE ROLE ontology_admin LOGIN PASSWORD 'admin_password';

-- 권한 부여
GRANT SELECT, INSERT, UPDATE ON entities TO ontology_user;
GRANT SELECT ON relationships TO ontology_user;
GRANT ALL ON entities TO ontology_admin;
GRANT ALL ON relationships TO ontology_admin;
GRANT ALL ON audit_log TO ontology_admin;
```

### 8.2 행 수준 보안 (RLS)

```sql
-- 테넌트별 격리 (선택)
ALTER TABLE entities ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON entities
USING (domain_id = current_setting('app.domain_id')::text);
```

---

## 9. 모니터링 쿼리

### 9.1 테이블 크기

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 9.2 인덱스 사용도

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### 9.3 느린 쿼리

```sql
-- postgresql.conf에 설정
# log_min_duration_statement = 1000  -- 1초 이상

-- 로그 분석
SELECT 
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 10. 체크리스트

- [ ] 모든 테이블 생성 (entities, relationships, audit_log, metadata)
- [ ] 인덱스 생성 (단일 + 복합)
- [ ] 함수/트리거 생성 (timestamp, version, count)
- [ ] View 생성 (ontology_triples)
- [ ] 테스트 데이터 삽입 (100개 엔티티)
- [ ] 기본 쿼리 테스트 (SELECT, INSERT, UPDATE, DELETE)
- [ ] 성능 벤치마크 (1000개 조회 시간)
- [ ] 백업/복구 테스트
- [ ] 보안 설정 (역할, 권한)
- [ ] 모니터링 쿼리 실행 가능 확인

---

**다음**: MIGRATION_SCRIPTS.md 참조 (자동화)
