# ont_platform v3 docs 리뷰
## (Kodex 관점: PostgreSQL/SPARQL 전환 문서의 구현 리스크 점검)

> **작성자**: Kodex  
> **작성일**: 2026-05-24  
> **대상 경로**: `ont_platform/v3/docs`  
> **검토 대상**: `POSTGRES_MIGRATION_ROADMAP.md`, `SPARQL_TRANSLATOR_DESIGN.md`, `SCHEMA_DESIGN.md`, `MIGRATION_SCRIPTS.md`  
> **목적**: 문서에 남아 있는 구현 리스크, 내부 모순, 과도한 성능/표준 약속을 정리한다.

---

## 1. 결론 요약

`ont_platform/v3/docs`의 큰 방향은 맞다.

핵심 방향:

```text
Mock SPARQL 제거
rdflib 기반 표준 호환 계층
PostgreSQL 기반 저장소
SPARQL→SQL 번역 레이어
마이그레이션/동시성/성능 테스트 계획
```

하지만 현재 문서는 아직 실행 가능한 설계서라기보다 낙관적인 계획서에 가깝다.

특히 다음 문제가 남아 있다.

```text
1. 완전 SPARQL 1.1 지원처럼 보이는 과도한 표현
2. 1M 엔티티 < 1s 같은 불명확한 성능 약속
3. SPARQL 지원/미지원 범위의 내부 충돌
4. PostgreSQL DDL 실행 가능성 문제
5. JSONB 인덱싱 전략 오류 가능성
6. RDF projection과 SQL translator 결과 불일치 위험
7. 마이그레이션 스크립트의 트랜잭션 실패 처리 부족
8. 존재하지 않는 schema.sql 참조
```

따라서 개발 착수 전 문서의 목표와 제약을 먼저 조정해야 한다.

---

## 2. High Risk Findings

### 2.1 `완전 SPARQL 1.1 지원` 표현은 위험하다

대상 문서:

- `ont_platform/v3/docs/POSTGRES_MIGRATION_ROADMAP.md`
- `ont_platform/v3/docs/SPARQL_TRANSLATOR_DESIGN.md`

문제 표현:

```text
W3C SPARQL 1.1 완벽 지원
rdflib 기반 표준 SPARQL 완벽 지원
SPARQL 1.1 쿼리 타입 완벽 지원 테스트
50개 패턴 모두 정확한 SQL 생성
```

문제점:

- 전체 SPARQL 1.1을 SQL로 번역하는 것은 별도 query engine 개발에 가깝다.
- Property Path, federation, arbitrary predicate variable, reasoning, nested query까지 포함하면 4주 구현 범위를 크게 벗어난다.
- rdflib로 실행 가능한 것과 SQL translator가 빠르게 처리 가능한 것을 구분하지 않고 있다.

권장 수정:

```text
수정 전:
W3C SPARQL 1.1 완벽 지원

수정 후:
rdflib 기반 SPARQL parser/fallback 호환.
SQL 번역은 Supported SPARQL Profile로 제한.
미지원 쿼리는 명확한 error와 대체 API를 제공.
```

권장 정책:

```text
Supported Profile:
- SELECT
- basic triple pattern
- rdf:type
- property lookup
- simple FILTER
- bounded JOIN
- OPTIONAL 일부
- LIMIT/OFFSET

Fallback Profile:
- CONSTRUCT
- DESCRIBE
- ASK 일부
- UNION 일부
- RDF projection query

Unsupported Profile:
- arbitrary property path
- SERVICE federation
- dynamic predicate variable
- complex nested query
- unbounded transitive closure
- online reasoning query
```

---

### 2.2 `1M 엔티티 < 1s` 성능 목표가 불명확하다

대상 문서:

- `ont_platform/v3/docs/POSTGRES_MIGRATION_ROADMAP.md`

문제 표현:

```text
100K 엔티티 SELECT < 100ms, 1M엔티티 < 1s
1M SELECT: < 1s
100K-1M 성능 벤치마크
```

문제점:

- 단순 id lookup, type lookup, indexed filter, one-hop join, two-hop join, aggregate query는 비용이 모두 다르다.
- `1M < 1s`가 어떤 query class 기준인지 불명확하다.
- 복잡한 SPARQL query까지 포함하는 것처럼 읽히면 기술 리스크가 커진다.

권장 수정:

```text
수정 전:
1M엔티티 < 1s

수정 후:
1M 엔티티 기준 hot-path query 성능 검증.
복잡 query는 query class별 목표를 분리한다.
```

권장 벤치마크:

```text
simple lookup by id: < 50ms
entity by type: < 100ms
indexed property filter: < 200ms
one-hop relation: < 300ms
two-hop relation: < 1s
aggregate query: 별도 측정
RDF export: async batch 처리
reasoning query: online target 제외
```

---

### 2.3 SPARQL 지원 범위가 문서 내부에서 충돌한다

대상 문서:

- `ont_platform/v3/docs/SPARQL_TRANSLATOR_DESIGN.md`

충돌 예:

```text
지원 패턴 48:
?x ?predicate "someValue"
SQL: 동적 열 선택

제약사항:
동적 패턴 (?x ?predicate ?y) - 지원 안 함
```

문제점:

- 같은 패턴이 지원 목록과 미지원 목록에 동시에 등장한다.
- 구현자와 테스트 작성자가 서로 다른 해석을 할 수 있다.
- 고객 문서로 노출될 경우 지원 범위에 대한 신뢰가 깨진다.

권장 수정:

```text
동적 predicate variable은 v1 SQL translator에서 미지원으로 둔다.
필요하면 rdflib fallback 또는 ontology_triples view 기반 저성능 fallback으로 분리한다.
```

권장 표기:

```text
?x ?predicate ?y:
- SQL hot-path: unsupported
- rdflib fallback: possible for small graph
- production large graph: not recommended
```

---

## 3. PostgreSQL Schema Findings

### 3.1 JSONB 인덱스에 `GiST`를 쓰는 설계는 재검토가 필요하다

대상 문서:

- `ont_platform/v3/docs/SCHEMA_DESIGN.md`

문제 표현:

```sql
CREATE INDEX idx_entities_properties ON entities USING GiST(properties);
```

문제점:

- PostgreSQL에서 JSONB containment/search 인덱스는 일반적으로 `GIN`을 사용한다.
- `GiST(properties)`는 기본 JSONB 사용 패턴에 맞지 않거나, 확장/연산자 클래스가 필요할 수 있다.
- 문서의 예시 쿼리인 `properties->>'age'` 조건에는 단순 JSONB GIN만으로도 충분하지 않을 수 있다.

권장 수정:

```sql
CREATE INDEX idx_entities_properties_gin
ON entities USING GIN (properties);
```

자주 쓰는 속성은 generated column 또는 expression index로 분리한다.

예:

```sql
CREATE INDEX idx_entities_age_int
ON entities (((properties->>'age')::integer));

CREATE INDEX idx_entities_name_text
ON entities ((properties->>'name'));
```

장기 권장:

```text
모든 속성을 JSONB 하나에 넣지 않는다.
핵심 속성은 column/generated column/expression index로 승격한다.
도메인별 확장 속성만 JSONB에 둔다.
```

---

### 3.2 trigger/function 선언 순서가 실행 실패를 만들 수 있다

대상 문서:

- `ont_platform/v3/docs/SCHEMA_DESIGN.md`

문제:

```text
entities_update_timestamp trigger가 update_timestamp() 함수 정의보다 먼저 나온다.
```

PostgreSQL은 trigger 생성 시점에 함수가 존재해야 한다.

권장 수정:

```text
DDL 순서:
1. extension
2. function
3. table
4. index
5. trigger
6. view
7. role / policy
```

문서 예시와 실제 `schema.sql`도 같은 순서를 따라야 한다.

---

### 3.3 `ontology_triples` view에 `rdf:type` projection이 명확하지 않다

대상 문서:

- `ont_platform/v3/docs/SCHEMA_DESIGN.md`

현재 view 개념:

```text
entities.properties → property triples
relationships → relationship triples
```

문제점:

- SPARQL translator 예시는 `?x a ex:Person` 또는 `rdf:type`을 핵심 패턴으로 사용한다.
- 그런데 RDF projection view가 `entity_type -> rdf:type`을 만들지 않으면 fallback/export 결과와 SQL translator 결과가 달라질 수 있다.

권장 수정:

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
SELECT
    CONCAT('entity:', e.id) AS subject,
    CONCAT('property:', key) AS predicate,
    value::TEXT AS object,
    'entity_property' AS triple_type,
    e.domain_id
FROM entities e,
     jsonb_each_text(e.properties) AS props(key, value)

UNION ALL

-- relationships
SELECT
    CONCAT('entity:', r.from_entity_id) AS subject,
    CONCAT('relation:', r.relation_type) AS predicate,
    CONCAT('entity:', r.to_entity_id) AS object,
    'relationship' AS triple_type,
    r.domain_id
FROM relationships r;
```

주의:

```text
rdf:type URI mapping은 임시 문자열이 아니라 schema_mappings/rdf_mappings 테이블에서 관리하는 것이 좋다.
```

---

### 3.4 `SERIALIZABLE` 기본값은 운영 비용을 고려해야 한다

대상 문서:

- `ont_platform/v3/docs/SCHEMA_DESIGN.md`
- `ont_platform/v3/docs/POSTGRES_MIGRATION_ROADMAP.md`

문제 표현:

```text
PostgreSQL 트랜잭션 격리 (SERIALIZABLE)
SERIALIZABLE 격리 레벨 기본
```

문제점:

- `SERIALIZABLE`은 가장 안전하지만 충돌/재시도 비용이 크다.
- 모든 write path에 기본 적용하면 성능과 사용자 경험이 나빠질 수 있다.
- optimistic locking과 transaction isolation의 역할이 섞여 있다.

권장 수정:

```text
기본: READ COMMITTED + optimistic locking
중요한 multi-entity action/write-back: REPEATABLE READ 또는 SERIALIZABLE
충돌 시 retry/backoff 정책 필수
```

---

## 4. Migration Script Findings

### 4.1 `docs/schema.sql` 참조 파일이 없다

대상 문서:

- `ont_platform/v3/docs/MIGRATION_SCRIPTS.md`

문제 표현:

```bash
psql -U postgres -d ontology_db < docs/schema.sql
```

문제점:

- 현재 `ont_platform/v3/docs`에는 `schema.sql` 파일이 없다.
- 문서대로 실행하면 바로 실패한다.

권장 수정:

```text
선택 1:
docs/schema.sql 파일을 실제로 생성한다.

선택 2:
SCHEMA_DESIGN.md의 DDL은 예시임을 명시하고,
실행 파일 경로를 scripts/schema.sql 또는 migrations/*.sql로 변경한다.
```

권장 구조:

```text
ont_platform/v3/
  migrations/
    001_initial_schema.sql
    002_indexes.sql
    003_rdf_projection.sql
  scripts/
    setup_postgres.ps1
    migrate_jsonl_to_postgres.py
```

---

### 4.2 psycopg2 오류 후 rollback/savepoint 없이 계속 진행한다

대상 문서:

- `ont_platform/v3/docs/MIGRATION_SCRIPTS.md`

문제 패턴:

```python
try:
    ...
except Exception as e:
    logger.error(...)
    continue
```

문제점:

- psycopg2는 SQL 오류가 발생하면 transaction이 aborted 상태가 될 수 있다.
- `rollback()` 또는 savepoint 없이 다음 row를 처리하면 이후 SQL도 계속 실패한다.
- 일부 row만 실패시키고 계속 가려는 설계와 실제 트랜잭션 동작이 맞지 않는다.

권장 수정:

```text
batch 단위 commit/rollback을 명확히 한다.
row 단위 격리가 필요하면 SAVEPOINT를 사용한다.
실패 row는 dead-letter file에 기록한다.
```

예:

```python
for line_num, line in enumerate(f, 1):
    try:
        cursor.execute("SAVEPOINT row_migration")
        process_line(line)
        cursor.execute("RELEASE SAVEPOINT row_migration")
    except Exception as e:
        cursor.execute("ROLLBACK TO SAVEPOINT row_migration")
        write_dead_letter(line_num, line, str(e))
```

대량 마이그레이션에서는 더 좋은 방식:

```text
1. staging table에 raw JSONL 적재
2. SQL로 검증/정규화
3. valid row만 canonical table로 insert
4. invalid row는 migration_errors 테이블에 보존
```

---

### 4.3 관계/속성 판별 로직이 너무 취약하다

대상 문서:

- `ont_platform/v3/docs/MIGRATION_SCRIPTS.md`

문제 패턴:

```python
non_relationships = [
    'rdf:type',
    'name',
    'age',
]
return predicate not in non_relationships
```

문제점:

- predicate가 관계인지 속성인지를 hard-coded list로 판단한다.
- 실제 온톨로지에서는 predicate mapping이 schema-dependent하다.
- 같은 predicate라도 object가 literal인지 IRI인지에 따라 처리 방식이 달라질 수 있다.

권장 수정:

```text
rdf_mappings 또는 predicate_mappings 테이블을 둔다.
predicate별 kind를 명시한다.
```

예:

```text
predicate_uri
canonical_field
predicate_kind: type | property | relationship | action | metadata
object_kind: iri | literal | typed_literal
datatype
domain_type
range_type
```

---

### 4.4 relationship id 생성 방식이 충돌과 길이 문제를 만들 수 있다

대상 문서:

- `ont_platform/v3/docs/MIGRATION_SCRIPTS.md`

문제 패턴:

```python
rel_id = f"{from_id}_{rel_type}_{to_id}"
```

문제점:

- URI가 길면 id가 매우 길어진다.
- `_` 구분자는 원본 id에 포함될 수 있다.
- 동일 관계가 여러 출처/doc/version에서 반복될 때 충돌한다.
- relation property, provenance, valid time을 반영하기 어렵다.

권장 수정:

```text
UUID 또는 stable hash를 사용한다.
source_id, doc_id, version, predicate_uri를 별도 컬럼으로 보존한다.
```

예:

```python
rel_id = sha256(f"{domain_id}|{doc_id}|{from_id}|{predicate}|{to_id}".encode()).hexdigest()
```

---

## 5. Documentation Consistency Findings

### 5.1 문서 목표와 `04_3` 제한선이 아직 완전히 맞지 않는다

관련 문서:

- `cross-source-comparison/04_3_kodex_경쟁분석_기술방향_제한제시.md`
- `ont_platform/v3/docs/*`

`04_3`의 제한선:

```text
RDF-native DB X
Operational Ontology Store + RDF/SPARQL compatibility layer O
완전 SPARQL 1.1 SQL 변환 X
Supported Profile + fallback + unsupported O
1M 복잡 JOIN < 1s X
hot-path query 기준 성능 검증 O
```

`ont_platform/v3/docs`에 남은 표현:

```text
W3C SPARQL 1.1 완벽 지원
SPARQL 1.1 쿼리 타입 완벽 지원
1M엔티티 < 1s
50개 패턴 모두 정확한 SQL 생성
```

권장:

```text
docs 전체에 "지원 범위 표"를 공통으로 추가한다.
roadmap, translator design, schema design의 용어를 통일한다.
```

---

### 5.2 `schema`와 `migration` 문서가 실행 파일 기준으로 연결되지 않는다

문제:

```text
SCHEMA_DESIGN.md는 DDL 예시를 담고 있다.
MIGRATION_SCRIPTS.md는 docs/schema.sql을 실행한다고 한다.
하지만 schema.sql은 없다.
```

권장:

```text
문서와 실행 산출물을 분리한다.

SCHEMA_DESIGN.md:
- 설계 설명
- 테이블 의미
- 인덱스 전략
- projection/mapping 원칙

migrations/*.sql:
- 실제 실행 가능한 SQL

MIGRATION_SCRIPTS.md:
- 실제 파일 경로와 명령만 사용
```

---

## 6. 권장 수정 우선순위

### Priority 0: 문서 목표 조정

바로 수정해야 한다.

```text
1. "완벽 지원" 표현 제거
2. SPARQL Profile 표 추가
3. 1M 성능 목표를 hot-path 기준으로 분해
4. SQL translator/fallback/unsupported 경계 명시
```

### Priority 1: 실행 가능한 PostgreSQL DDL 정리

```text
1. schema.sql 또는 migrations/*.sql 생성
2. function/table/index/trigger/view 순서 정리
3. JSONB GIN/expression index로 수정
4. ontology_triples에 rdf:type projection 추가
5. rdf_mappings 테이블 추가 검토
```

### Priority 2: 마이그레이션 안정성 강화

```text
1. staging table 도입
2. migration_errors/dead-letter 처리
3. savepoint 또는 batch rollback 정책
4. predicate mapping 기반 relationship/property 판별
5. stable hash/UUID 기반 relationship id
```

### Priority 3: 운영 정책 명확화

```text
1. SERIALIZABLE 기본 적용 여부 재검토
2. optimistic locking/retry 정책 문서화
3. audit/lineage/version 모델 구체화
4. PostgreSQL source of truth, Neo4j optional accelerator 원칙 반영
```

---

## 7. 최종 권고

`ont_platform/v3/docs`는 방향성이 좋다.

하지만 지금 상태로 바로 구현에 들어가면 다음 문제가 생길 가능성이 높다.

```text
1. 목표 범위 과대화
2. SPARQL 지원 범위 논쟁
3. DDL 실행 실패
4. 마이그레이션 중 partial failure 추적 불가
5. RDF projection과 SQL translator 결과 불일치
6. JSONB 성능 문제
```

따라서 먼저 문서를 다음 원칙으로 정리해야 한다.

```text
1. Operational Ontology Store가 source of truth다.
2. RDF/SPARQL은 compatibility/projection/fallback layer다.
3. SQL translator는 Supported Profile만 처리한다.
4. 복잡 SPARQL은 fallback/async/unsupported로 분리한다.
5. 성능 목표는 query class별로 나눈다.
6. 실행 가능한 SQL/script와 설명 문서를 분리한다.
```

이 정리가 끝나면 `04_2`의 하이브리드 아키텍처는 훨씬 현실적인 개발 계획이 된다.

