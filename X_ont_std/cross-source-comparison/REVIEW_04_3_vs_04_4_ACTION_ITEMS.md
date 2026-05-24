# 04_3 vs 04_4 리뷰: 반영해야 할 부분 정리

> **검토일**: 2026-05-24  
> **목적**: 04_3(기술방향 제한) vs 04_4(문서 실행 리스크)의 충돌점을 정리하고 구현 전 수정 순서 제시

---

## 1. 핵심 충돌 분석

### 1.1 SPARQL 지원 범위 불명확

**04_3의 주장:**
```text
"표준 RDF/SPARQL 호환성"이 차별화 포인트
Operational Ontology Store + RDF/SPARQL compatibility layer
```

**04_4의 현실:**
```text
POSTGRES_MIGRATION_ROADMAP: "W3C SPARQL 1.1 완벽 지원"
SPARQL_TRANSLATOR_DESIGN: "50개 패턴 모두 정확한 SQL 생성"
→ 현실적으로 불가능
```

**반영할 방향:**
- ✅ 04_3의 "호환성 계층"이 맞다
- ❌ 04_4의 "완벽 지원"은 현실적이지 않다
- **수정**: Supported SPARQL Profile (50개 기본 패턴) + Fallback + Unsupported로 명확히 분리

---

### 1.2 성능 목표의 모호함

**04_3의 주장:**
```text
"운영 온톨로지 hot path에서 빠른 성능"
```

**04_4의 문제:**
```text
1M 엔티티 < 1s
100K-1M 성능 벤치마크
→ 어떤 query 기준인지 불명확
```

**반영할 방향:**
- ✅ 04_3의 "hot path" 개념을 명확히 정의해야 함
- **수정**: Query class별 성능 목표 분해

| Query Class | 목표 | 예 |
|-----------|------|-----|
| Simple lookup by ID | < 50ms | entity_id 검색 |
| Entity by type filter | < 100ms | 타입별 조회 |
| Indexed property filter | < 200ms | status='active' |
| One-hop relation | < 300ms | 선박의 모든 블록 |
| Two-hop relation | < 1s | 부품의 공급자 |
| Aggregate/RDF export | Async batch | 대규모 분석 |
| Reasoning query | Offline/batch | 영향 분석 |

---

### 1.3 도메인 모델 구체화 부족

**04_3의 주장:**
```text
"조선/제조 도메인 모델, BOM, 도면, 공정, 기자재, 검사, 변경관리"
```

**04_4의 발견:**
```text
SCHEMA_DESIGN: 범용 entities, relationships 테이블만 있음
→ Ship, Block, Part, WorkOrder 같은 도메인 타입 없음
```

**반영할 방향:**
- ✅ 도메인 타입 정의 추가 필요
- **수정**: Entity Type Enumeration / Domain Schema

```sql
-- 예시
entity_type ENUM ('Ship', 'Block', 'Part', 'Drawing', 
                  'Supplier', 'Equipment', 'Inspection', 
                  'WorkOrder', 'ChangeRequest', 'Document')
```

---

## 2. 우선순위별 수정 항목

### Priority 0: 문서 목표/용어 통일 (이번 주 중)

#### 0-1. 모든 docs에 "SPARQL Support Matrix" 추가

**04_3, 04_4 모두 지적:** 지원 범위가 명확하지 않음

```markdown
## SPARQL Support Matrix

| Category | Pattern | Status | SQL Translation | Fallback |
|----------|---------|--------|-----------------|----------|
| SELECT | ?x ?y ?z | Supported | Direct | - |
| Type | ?x rdf:type ex:Type | Supported | entity_type | - |
| Property | ?x ex:prop "value" | Supported | properties->>'key' | - |
| Simple Filter | FILTER(?age > 30) | Supported | WHERE clause | - |
| One-hop Join | ?x ex:hasChild ?y | Supported | entities + relationships | - |
| Optional | OPTIONAL {...} | Partial | LEFT JOIN | rdflib |
| Property Path | ?x ex:knows+ ?y | Unsupported | - | rdflib/online |
| Dynamic Predicate | ?x ?pred ?y | Unsupported | - | rdflib fallback |
| Federated | SERVICE {...} | Unsupported | - | - |
```

**파일 수정 대상:**
- `ont_platform/v3/docs/SPARQL_TRANSLATOR_DESIGN.md` (현재 혼재된 50개 패턴 목록 → 위 테이블로 재구성)
- `ont_platform/v3/docs/POSTGRES_MIGRATION_ROADMAP.md` ("완벽 지원" 표현 제거, "Supported Profile" 명시)

#### 0-2. "완벽 지원" 표현 제거

**수정 대상:**

| 문서 | 현재 표현 | 수정 후 |
|------|---------|--------|
| POSTGRES_MIGRATION_ROADMAP.md | "W3C SPARQL 1.1 완벽 지원" | "rdflib 기반 SPARQL parser, SQL translator는 Supported Profile로 제한" |
| SPARQL_TRANSLATOR_DESIGN.md | "SPARQL 1.1 쿼리 타입 완벽 지원 테스트" | "기본 SPARQL 쿼리 50개 패턴 테스트 + fallback 검증" |
| SPARQL_TRANSLATOR_DESIGN.md | "50개 패턴 모두 정확한 SQL 생성" | "50개 패턴은 SQL로 직접 변환, 복잡 패턴은 rdflib fallback" |

#### 0-3. 성능 목표 분해

**수정 대상:** `POSTGRES_MIGRATION_ROADMAP.md`, Week 4 section

```markdown
## Week 4 성능 검증

### Benchmark Targets (100K entities, 1M relationships 기준)

Hot-path queries:
- Simple lookup by ID: < 50ms
- Entity by type: < 100ms  
- Indexed property filter: < 200ms
- One-hop relation: < 300ms
- Two-hop relation: < 1s

Complex queries:
- Async/batch processing for RDF export, impact analysis
- Online reasoning: not in scope v1
```

---

### Priority 1: 실행 가능한 PostgreSQL DDL (Week 1)

#### 1-1. schema.sql 파일 생성

**04_4 지적:** "docs/schema.sql이 참조되지만 존재하지 않음"

**수정 방식:**

옵션 A: 실제 schema.sql 생성 (권장)
```
ont_platform/v3/scripts/init_schema.sql  ← 이미 존재 (SETUP_NEON.md 참고)
```

옵션 B: migrations 폴더 구조화
```
ont_platform/v3/
  migrations/
    001_initial_schema.sql
    002_indexes.sql
    003_rdf_projection.sql
```

**현재 상태:** scripts/init_schema.sql이 이미 있으므로 **옵션 A 적용**

#### 1-2. JSONB 인덱스 전략 수정

**04_4 지적:** "GiST 사용은 JSONB 기본 패턴에 맞지 않음"

**현재:**
```sql
CREATE INDEX idx_entities_properties ON entities USING GiST(properties);
```

**수정:**
```sql
-- 일반 속성 검색
CREATE INDEX idx_entities_properties_gin 
ON entities USING GIN (properties);

-- 자주 사용되는 속성 (expression index)
CREATE INDEX idx_entities_status
ON entities ((properties->>'status'));

CREATE INDEX idx_entities_doc_id
ON entities (doc_id);
```

**파일 수정:** `scripts/init_schema.sql` 및 `SCHEMA_DESIGN.md`

#### 1-3. DDL 실행 순서 정리

**04_4 지적:** "trigger가 function 정의보다 먼저 나올 수 있음"

**현재 상태:** init_schema.sql은 이미 올바른 순서를 따르고 있음 ✅

**검증할 순서:**
1. ✅ Extension
2. ✅ Function (update_timestamp)
3. ✅ Table (entities, relationships, audit_log, ontology_metadata)
4. ✅ Index
5. ✅ Trigger
6. ✅ View (ontology_triples)

#### 1-4. ontology_triples VIEW에 rdf:type 추가

**04_4 지적:** "rdf:type projection이 명확하지 않음"

**현재:**
```sql
CREATE VIEW ontology_triples AS
SELECT ... FROM entities ... UNION ALL
SELECT ... FROM entities WHERE jsonb_each ... UNION ALL
SELECT ... FROM relationships ...
```

**수정:**
```sql
CREATE VIEW ontology_triples AS
-- rdf:type projection
SELECT
    CONCAT('entity:', e.id) AS subject,
    'rdf:type' AS predicate,
    CONCAT('type:', e.entity_type) AS object,
    'entity_type' AS triple_type,
    e.domain_id
FROM entities e

UNION ALL

-- entity properties
SELECT ... FROM entities ...

UNION ALL

-- relationships
SELECT ... FROM relationships ...
```

**파일 수정:** `scripts/init_schema.sql`

#### 1-5. 트랜잭션 격리 레벨 정책 명시

**04_4 지적:** "SERIALIZABLE 기본 적용은 성능 리스크"

**현재:** SCHEMA_DESIGN.md에 "SERIALIZABLE" 명시

**수정:**
```markdown
## Transaction Isolation Policy

### Default: READ COMMITTED + Optimistic Locking
- version column for optimistic locking
- retry policy on version conflict

### Multi-entity Actions: REPEATABLE READ or SERIALIZABLE
- write-back operations
- change impact analysis
- audit trail with lineage

### Connection Pool: 
- Max connections managed by Neon.tech pooler
- Automatic retry on connection timeout
```

---

### Priority 2: 마이그레이션 안정성 (Week 1-2)

#### 2-1. SAVEPOINT 기반 행 단위 격리

**04_4 지적:** "row 단위 실패 처리 없이 계속 진행하는 문제"

**수정 대상:** scripts/migrate_jsonl_to_postgres.py (새로 작성)

```python
# Row-level error handling with SAVEPOINT
for line_num, line in enumerate(raw_triples, 1):
    try:
        cursor.execute("SAVEPOINT row_" + str(line_num))
        process_triple(line)
        cursor.execute("RELEASE SAVEPOINT row_" + str(line_num))
    except Exception as e:
        cursor.execute("ROLLBACK TO SAVEPOINT row_" + str(line_num))
        write_dead_letter(line_num, line, str(e))
        continue
    
    # Batch commit every 1000 rows
    if line_num % 1000 == 0:
        conn.commit()
```

#### 2-2. 동적 predicate 판별 로직 개선

**04_4 지적:** "hard-coded list 기반 판별은 취약함"

**수정:** predicate_mappings 테이블 추가

```sql
CREATE TABLE predicate_mappings (
    predicate_uri VARCHAR(255) PRIMARY KEY,
    canonical_field VARCHAR(100),
    predicate_kind VARCHAR(50) -- 'type', 'property', 'relationship', 'action'
    object_kind VARCHAR(50) -- 'iri', 'literal', 'typed_literal'
    datatype VARCHAR(100),
    domain_entity_type VARCHAR(100),
    range_entity_type VARCHAR(100)
);

-- 마이그레이션에서 테이블 참조
SELECT predicate_kind FROM predicate_mappings WHERE predicate_uri = ?
```

#### 2-3. Relationship ID 생성 방식 개선

**04_4 지적:** "simple concatenation은 충돌 위험"

**현재:**
```python
rel_id = f"{from_id}_{rel_type}_{to_id}"
```

**수정:**
```python
import hashlib

rel_id = hashlib.sha256(
    f"{domain_id}|{doc_id}|{from_id}|{predicate}|{to_id}".encode()
).hexdigest()[:16]  # 16자로 truncate

# properties에 원본 정보 보존
properties = {
    "source_id": f"{from_id}_{rel_type}_{to_id}",
    "canonical_id": rel_id,
    "from_id": from_id,
    "to_id": to_id,
    "predicate": predicate,
    "doc_id": doc_id,
    "version": 1
}
```

---

### Priority 3: 운영 정책 명확화 (Week 2)

#### 3-1. Audit/Lineage 모델 구체화

**04_3 주장:** "감사 추적 & 혈통"이 차별화 포인트

**현재:** audit_log 테이블만 있음

**추가 필요:**

```sql
CREATE TABLE entity_lineage (
    entity_id VARCHAR(255) PRIMARY KEY,
    source_entity_ids TEXT[], -- jsonb array of source IDs
    transformation_rule TEXT, -- 어떻게 derived되었는가
    transformation_timestamp TIMESTAMP,
    data_quality_score FLOAT,
    confidence FLOAT
);

CREATE TABLE write_back_changelog (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(255),
    operation VARCHAR(50), -- 'INSERT', 'UPDATE', 'DELETE'
    old_state JSONB,
    new_state JSONB,
    target_system VARCHAR(100), -- 'SAP', 'ERP', 'PLM'
    status VARCHAR(50), -- 'pending', 'success', 'failed'
    executed_at TIMESTAMP,
    error_message TEXT
);
```

#### 3-2. PostgreSQL vs Neo4j 역할 정의

**04_3 주장:** "Neo4j를 accelerator로 사용 가능"

**명시할 정책:**

```markdown
## Architecture Decision: PostgreSQL as Source of Truth

### PostgreSQL (Primary Store)
- Operational Ontology: entities, relationships, audit_log
- Source of truth for all writes
- Consistency, audit trail, lineage guaranteed

### Neo4j (Optional Accelerator) 
- Read-only synced from PostgreSQL
- Traversal-heavy queries (graph analysis)
- Visualization/exploration
- Fallback for complex graph queries

### Sync Strategy
- One-way: PostgreSQL → Neo4j (async batch job)
- Hourly or on-demand sync
- Neo4j stale data acceptable (reporting, analysis)
- Business-critical queries: always PostgreSQL
```

---

## 3. 반영 체크리스트

### 문서 수정 순서

| 우선순위 | 작업 | 파일 | 담당 | 기한 |
|---------|------|------|------|------|
| 0 | "완벽 지원" → "Supported Profile" | POSTGRES_MIGRATION_ROADMAP.md | Claude | 2026-05-25 |
| 0 | SPARQL Support Matrix 테이블 추가 | SPARQL_TRANSLATOR_DESIGN.md | Claude | 2026-05-25 |
| 0 | Hot-path 성능 목표 분해 | POSTGRES_MIGRATION_ROADMAP.md | Claude | 2026-05-25 |
| 1 | GiST → GIN, expression index | scripts/init_schema.sql | Claude | 2026-05-25 |
| 1 | ontology_triples에 rdf:type | scripts/init_schema.sql | Claude | 2026-05-25 |
| 1 | Transaction isolation policy | SCHEMA_DESIGN.md | Claude | 2026-05-26 |
| 2 | predicate_mappings 테이블 설계 | MIGRATION_SCRIPTS.md | Claude | 2026-05-26 |
| 2 | SAVEPOINT 기반 마이그레이션 | scripts/migrate.py | Claude | 2026-05-27 |
| 2 | Relationship ID hash 함수 | scripts/migrate.py | Claude | 2026-05-27 |
| 3 | entity_lineage, write_back_changelog | SCHEMA_DESIGN.md | Claude | 2026-05-28 |
| 3 | Neo4j sync strategy 정책 | ARCHITECTURE.md | Claude | 2026-05-28 |

---

## 4. 최종 권고

### 04_3 (기술방향)과 04_4 (문서리스크)의 합의점

✅ **04_3이 맞다:**
- 도메인 특화 (조선/제조)
- 운영형 온톨로지 (read + write + action)
- RDF/SPARQL 호환 (완벽이 아니라)
- Neo4j는 accelerator (primary가 아니라)

⚠️ **04_4의 우려가 현실:**
- 문서에는 "완벽 지원" 오버스테이트먼트 존재
- DDL과 스크립트가 연결 안 됨
- 성능 목표가 모호함
- 마이그레이션 안정성 계획 부족

### 개발 착수 전 꼭 필요한 수정

**필수 (Priority 0):**
1. SPARQL Support Matrix 정의
2. "완벽 지원" → "Supported Profile + Fallback"
3. Hot-path 성능 목표 분해 (query class별)

**강력 권장 (Priority 1):**
1. GIN 인덱스, expression index
2. ontology_triples VIEW에 rdf:type
3. Transaction 격리 정책

**나머지 (Priority 2-3):**
- 이번 주 중에 설계, 구현은 Week 1-2에 진행

### 타이밍

- **지금 (2026-05-24):** 문서 수정 (Priority 0)
- **내일 (2026-05-25):** DDL 수정 (Priority 1)
- **일주일 (2026-05-27):** Week 1 개발 시작

이 정리가 끝나면 `04_2`의 하이브리드 아키텍처는 훨씬 현실적이고 실행 가능한 개발 계획이 된다.
