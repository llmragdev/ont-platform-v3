# 국내 경쟁 환경 및 기술 방향 제한 제시
## (Kodex 관점: Palantir식 운영 온톨로지 + RDF 호환 계층의 현실적 제품화)

> **작성자**: Kodex  
> **작성일**: 2026-05-24  
> **기반 문서**: `04_1_안티그래피티_온톨로지_분석.md`, `04_2_클로드코드_온톨로지_재제안.md`  
> **목적**: 국내 경쟁 제품 가능성, 차별화 지점, 기술 구현 범위의 제한선을 정리한다.

---

## 1. 결론 요약

현재 방향으로 개발하면 국내에 경쟁 제품은 존재한다.

다만 정확히 같은 제품이라기보다는 다음 영역들과 경쟁하게 된다.

| 경쟁 영역 | 대표 유형 | 경쟁 강도 |
|---------|----------|----------|
| 온톨로지 + LLM 플랫폼 | 솔트룩스 Ontology Foundry 계열 | 높음 |
| 지식그래프 + GraphRAG 솔루션 | SKAI Ontovia 계열 | 높음 |
| 그래프 기반 기업 의사결정 AI | GraphAI 계열 | 중간 |
| 산업 데이터/AX 플랫폼 | 심플랫폼 NUBISON 계열 | 중간 |
| Neo4j/SI 기반 구축 | 그래프DB 리셀러 및 SI 업체 | 중간 |
| 대형 SI 데이터 플랫폼 | 삼성SDS, LG CNS, SK C&C 등 | 간접 경쟁 |

따라서 범용 온톨로지 플랫폼으로 가면 경쟁이 강하다.

현실적인 승부 지점은 다음이다.

```text
범용 온톨로지 플랫폼 X
조선/제조 실행형 운영 온톨로지 O

RDF-native DB X
Operational Ontology Store + RDF/SPARQL compatibility layer O

GraphRAG 검색 도구 X
Action, Write-back, Audit, Lineage까지 포함한 업무 실행 플랫폼 O
```

---

## 2. 국내 경쟁 제품 가능성

### 2.1 직접 경쟁군

#### 솔트룩스 Ontology Foundry

솔트룩스는 온톨로지와 LLM을 결합한 산업형 AI 플랫폼을 전면에 내세우고 있다. 방향성은 다음과 같이 겹친다.

- 기업 내부 데이터의 의미와 관계 구조화
- 온톨로지 기반 뉴로심볼릭 AI
- 설명 가능한 의사결정
- 산업형 AI 및 에이전트 구현

경쟁 리스크:

- 브랜드와 고객 기반이 강하다.
- 온톨로지 구축 경험과 특허를 강조할 수 있다.
- 범용 산업 AI 플랫폼 포지션에서 먼저 시장 인식을 가져갈 가능성이 있다.

대응 방향:

- 범용 AI 플랫폼 정면 승부를 피한다.
- 조선/제조 도메인 모델, BOM, 도면, 공정, 기자재, 검사, 변경관리로 범위를 좁힌다.
- 표준 RDF/SPARQL 호환성과 운영계 write-back을 명확한 차별점으로 둔다.

#### SKAI Ontovia

SKAI의 Ontovia는 온톨로지, 지식그래프, GraphRAG를 결합한 AI 데이터 솔루션으로 포지셔닝된다.

겹치는 부분:

- 기업 데이터 자산을 AI가 활용 가능한 구조로 재구성
- 지식그래프 기반 데이터 통합
- GraphRAG를 통한 환각 감소
- 공공/민간 고객 대상 커스터마이징

경쟁 리스크:

- GraphRAG 시장에서는 메시지가 쉽고 명확하다.
- "AI 환각 감소"는 고객이 이해하기 쉬운 구매 명분이다.

대응 방향:

- GraphRAG만으로 포지셔닝하지 않는다.
- 검색 정확도보다 "업무 상태 변경과 이력 추적"을 강조한다.
- 사용자가 질문만 하는 시스템이 아니라, 판단 결과가 업무 시스템에 반영되는 플랫폼으로 정의한다.

### 2.2 간접 경쟁군

#### 심플랫폼 NUBISON

심플랫폼은 산업 현장의 데이터, AI, 워크플로우를 통합하는 AX 플랫폼에 가깝다.

경쟁 가능 영역:

- 제조 현장 데이터 통합
- AI-ready data lake
- 산업 워크플로우 통합
- 설비/안전/품질 관련 데이터 운영

차이:

- 직접적인 RDF/SPARQL 온톨로지 표준 플랫폼이라기보다는 산업 AX 플랫폼이다.
- 그러나 제조 고객 예산에서는 충분히 경쟁자가 될 수 있다.

#### Neo4j 기반 구축 업체

Neo4j, GraphDB, 기타 그래프DB를 활용하는 SI 업체는 프로젝트 단위에서 경쟁할 수 있다.

차이:

- Neo4j는 RDF import/export 및 semantic toolkit을 제공할 수 있지만, 질의 중심은 Cypher다.
- 완전한 SPARQL 표준 운영 플랫폼이라고 보기는 어렵다.

대응 방향:

- Neo4j를 무조건 배제하지 않는다.
- 필요 시 traversal accelerator로 선택 도입한다.
- primary store는 PostgreSQL 기반 operational ontology store로 유지한다.

---

## 3. 제품 포지셔닝 제안

### 3.1 피해야 할 포지션

다음 포지션은 경쟁이 강하거나 구현 난도가 높다.

```text
1. 범용 온톨로지 플랫폼
2. 범용 GraphRAG 솔루션
3. 자체 RDF triple store
4. 완전한 SPARQL 1.1 SQL 변환 엔진
5. Palantir Foundry 전체 대체재
6. Neo4j보다 빠른 범용 그래프DB
```

특히 "Palantir와 같은 성능", "Neo4j와 같은 성능", "RDF 확장성"을 동시에 주장하면 기술 리스크가 커진다.

이를 다음과 같이 재정의해야 한다.

```text
Palantir와 같은 성능
→ 운영 온톨로지 hot path에서 빠른 성능

Neo4j와 같은 성능
→ 정해진 traversal/profile query에서 빠른 성능

RDF 확장성
→ RDF를 내부 저장 모델이 아니라 표준 projection/API로 제공
```

### 3.2 권장 포지션

권장 포지션은 다음이다.

```text
조선/제조 산업을 위한 실행형 운영 온톨로지 플랫폼

핵심:
- 기업 데이터의 의미 구조화
- 도면/BOM/공정/자재/검사/변경관리 연결
- AI Agent가 참조 가능한 신뢰 지식 계층
- 업무 action 및 write-back
- audit, lineage, version 관리
- RDF/SPARQL 호환 export/query layer
```

이 포지션은 국내 범용 온톨로지/GraphRAG 제품과 다르게 보일 수 있다.

---

## 4. 기술 방향 제한선

### 4.1 내부 canonical model

내부 저장 모델은 RDF triple을 중심에 두지 않는다.

권장 canonical model:

```text
Entity
Relation
Action
Property
Policy
AuditLog
Lineage
Version
Provenance
```

이 모델은 Palantir식 Object-Link-Action 구조와 유사하지만, 조선/제조 도메인에 맞게 구체화한다.

예시:

```text
Entity:
- Ship
- Block
- Equipment
- Part
- Drawing
- Process
- InspectionItem
- Supplier
- WorkOrder

Relation:
- part_of
- installed_in
- derived_from
- inspected_by
- supplied_by
- replaces
- affects

Action:
- approve_change
- create_work_order
- request_inspection
- update_bom
- link_drawing_revision
```

### 4.2 RDF/SPARQL의 역할

RDF는 primary storage가 아니다.

RDF의 역할:

- 외부 표준 교환 형식
- ontology vocabulary 표현
- SHACL 검증
- 외부 ontology와의 mapping
- SPARQL endpoint 제공
- JSON-LD/Turtle/N-Triples export

즉, RDF는 canonical model에서 생성되는 projection이다.

```text
Operational Model
    ↓ projection
RDF Graph
    ↓ query/export/validation
SPARQL / SHACL / JSON-LD / Turtle
```

### 4.3 SPARQL 처리 정책

전체 SPARQL 1.1을 SQL로 완전 번역하려고 하면 안 된다.

SPARQL 처리는 3단계로 제한한다.

```text
1. Supported Profile
   - SELECT
   - basic triple pattern
   - rdf:type
   - property lookup
   - simple FILTER
   - bounded JOIN
   - OPTIONAL 일부
   - LIMIT/OFFSET
   → SQL로 번역

2. Fallback Profile
   - CONSTRUCT
   - DESCRIBE
   - UNION 일부
   - 복잡한 RDF projection query
   → rdflib로 실행

3. Unsupported Profile
   - arbitrary property path
   - complex nested query
   - SERVICE federation
   - complex reasoning query
   - unbounded transitive closure
   → 명확한 오류와 대체 API 안내
```

이 제한을 문서화하지 않으면 고객과 개발 모두에서 기대치가 깨진다.

### 4.4 PostgreSQL의 역할

PostgreSQL은 RDF triple table이 아니라 operational ontology store다.

권장 테이블:

```text
entities
relationships
entity_properties
relationship_properties
actions
action_results
audit_log
lineage_edges
ontology_versions
schema_mappings
rdf_mappings
```

JSONB는 빠른 시작에는 좋지만, 모든 속성을 JSONB에만 넣으면 성능과 제약 관리가 어려워진다.

권장:

- 자주 조회하는 핵심 속성은 column 또는 generated column으로 승격
- 검색성 높은 속성은 별도 인덱스
- 도메인별 확장 속성은 JSONB
- RDF predicate mapping은 별도 테이블로 관리

### 4.5 Neo4j의 역할

Neo4j는 primary store로 고정하지 않는다.

선택적 역할:

- deep traversal
- path finding
- impact analysis
- dependency graph query
- visualization

권장 구조:

```text
PostgreSQL: source of truth
Neo4j: optional graph acceleration/read model
RDF: standard projection/read model
```

이렇게 하면 운영 일관성과 성능을 동시에 관리하기 쉽다.

---

## 5. 성능 목표의 현실화

기존 문서의 성능 목표는 일부 낙관적이다.

수정 권장:

| 항목 | 기존 표현 | 현실적 표현 |
-----|----------|------------|
| SPARQL 1.1 | 완전 준수 | rdflib fallback 기준 호환, SQL 번역은 profile 제한 |
| 1M 엔티티 | 복잡 JOIN < 1s | hot-path query 기준 < 1s, 복잡 query는 별도 측정 |
| Neo4j급 성능 | 범용 그래프 성능 | 제한된 traversal use case에서 경쟁 |
| Palantir급 성능 | 전체 플랫폼 성능 | 운영 온톨로지 hot path에서 빠른 응답 |
| RDF 확장성 | RDF native scale-out | RDF projection/export 확장성 |

권장 벤치마크:

```text
Dataset:
- 100K entities
- 1M relationships
- 10M properties

Hot-path queries:
- entity by id
- entity by type
- property filter
- one-hop relation
- two-hop relation
- drawing revision impact
- BOM part lookup
- supplier/equipment dependency

Target:
- simple lookup: < 50ms
- indexed filter: < 200ms
- one-hop join: < 300ms
- two-hop join: < 1s
- RDF export batch: async 처리
- full graph reasoning: online target 제외
```

---

## 6. 차별화 전략

### 6.1 기술 차별화

```text
1. Operational Ontology
   단순 지식그래프가 아니라 업무 상태를 변경할 수 있는 온톨로지

2. RDF Compatibility
   표준 export/query/validation 계층 제공

3. Domain-Aware Schema
   조선/제조 도메인 객체를 기본 모델로 제공

4. Action + Write-back
   AI 판단 결과를 업무 시스템에 반영

5. Audit + Lineage
   누가, 왜, 어떤 근거로 변경했는지 추적

6. On-premise Friendly
   폐쇄망/내부망 제조 환경에 배포 가능
```

### 6.2 시장 차별화

범용 AI/GraphRAG 메시지보다 다음 메시지가 더 강하다.

```text
부정확한 답변을 줄이는 AI 검색 솔루션
→ 약함. 경쟁자가 많다.

조선/제조 데이터의 변경, 영향, 책임, 근거를 추적하고 실행하는 운영 온톨로지
→ 강함. 도메인 진입장벽이 생긴다.
```

---

## 7. 구현 우선순위 재정의

### Phase 1: 표준 호환 최소 기반

목표:

- rdflib 기반 RDF import/export
- Turtle/JSON-LD/N-Triples 처리
- SPARQL parser/fallback
- SHACL validation 기초

하지 않을 것:

- 자체 RDF triple store 고도화
- 전체 SPARQL SQL 번역

### Phase 2: Operational Ontology Store

목표:

- PostgreSQL canonical model
- Entity/Relation/Action/Audit/Lineage 구현
- 조선/제조 기본 schema 정의
- migration path 확보

하지 않을 것:

- 모든 속성을 JSONB 하나에 몰아넣기
- RDF triple table을 primary store로 만들기

### Phase 3: SPARQL Profile Translator

목표:

- hot-path query만 SQL 변환
- 지원 profile 명시
- 미지원 query는 rdflib fallback 또는 오류
- 성능 테스트 기반 확장

하지 않을 것:

- SPARQL 1.1 완전 SQL 번역 선언
- reasoning query를 online query로 처리

### Phase 4: Action/Write-back

목표:

- 업무 action 모델
- 트랜잭션 처리
- optimistic locking
- audit log
- versioned change

하지 않을 것:

- 읽기 전용 GraphRAG 제품으로 축소

### Phase 5: Optional Graph Accelerator

목표:

- impact analysis
- dependency traversal
- deep path query
- visualization

선택지:

- Neo4j
- PostgreSQL recursive CTE
- graph projection cache

---

## 8. 의사결정 체크리스트

제품 방향을 검토할 때 다음 질문에 모두 답할 수 있어야 한다.

```text
1. 이 기능은 operational ontology에 필요한가?
2. 이 기능은 조선/제조 도메인 차별화를 만드는가?
3. RDF/SPARQL 표준 호환성에 필요한가?
4. SQL hot path로 빠르게 처리 가능한가?
5. 미지원 SPARQL 범위를 명확히 설명할 수 있는가?
6. action/write-back/audit와 연결되는가?
7. 범용 GraphRAG 경쟁으로 빨려 들어가지 않는가?
```

위 질문에 답하기 어렵다면 우선순위를 낮춘다.

---

## 9. 최종 권고

`04_2`의 하이브리드 방향은 대체로 맞다.

다만 다음 표현은 조정해야 한다.

```text
수정 전:
- rdflib SPARQL 1.1 완벽 준수
- SPARQL 1.1 모든 쿼리 형식 지원
- 1M 엔티티 복잡 JOIN < 1s
- SPARQL→SQL 번역기 완성

수정 후:
- rdflib 기반 표준 parser/fallback 호환
- SQL 번역은 지원 SPARQL Profile로 제한
- 1M 엔티티 hot-path query 성능 검증
- 복잡 query는 fallback/async/unsupported 정책 명시
```

최종 제품 방향:

```text
조선/제조 실행형 운영 온톨로지 플랫폼
= Operational Ontology Store
+ RDF/SPARQL Compatibility Layer
+ Action/Write-back
+ Audit/Lineage
+ Optional Graph Accelerator
+ On-premise Deployment
```

이 방향이면 국내 경쟁 제품과 겹치면서도 정면 충돌을 피할 수 있다.

핵심은 "온톨로지로 답변을 잘하는 AI"가 아니라,
"온톨로지로 기업 업무 상태를 안전하게 이해하고 변경하는 플랫폼"이 되는 것이다.

