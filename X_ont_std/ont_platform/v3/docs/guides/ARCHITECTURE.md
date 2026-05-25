# ont_platform v3.0 아키텍처

> 문서 버전: 1.0  
> 기준일: 2026-05-16  
> 기반: 13_팔란티어_실무_설계원칙.md

---

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js v3)                        │
│  - Dashboard, Explorer, AIQuery, RAGQuery, Workflow, Audit      │
│  - IntegrationTestRunner                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI v3)                           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Query Layer (query_planner, query_executor)           │   │
│  │  ├─ Intent Classifier (LLM — Gemini)                  │   │
│  │  ├─ Ontology Query Engine                             │   │
│  │  └─ Vector Search Engine                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Ontology Layer (OntologyService)                      │   │
│  │  ├─ find_by_name (Korean token-based matching)        │   │
│  │  ├─ filter_by_property                                │   │
│  │  ├─ upsert_entity (Create/Update)                     │   │
│  │  └─ get_schema                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Synthesis Layer (HybridSynthesizer)                   │   │
│  │  └─ LLM 기반 다중 소스 답변 생성                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Storage Layer (OntologyRepository)                    │   │
│  │  └─ JSON 파일 기반 저장 (현재)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼─────┐    ┌────────▼────────┐  ┌─────▼──────┐
    │ Ontology  │    │ Vector Search   │  │ LLM Client │
    │ Storage   │    │ (문서 임베딩)    │  │ (Gemini)   │
    │           │    │                 │  │            │
    │ JSON      │    │ Embeddings      │  │ Classify   │
    │ Files     │    │ Index           │  │ Synthesize │
    └───────────┘    └─────────────────┘  └────────────┘
```

---

## 2. 저장소 구조 (Storage Layer) — 진화 경로

### 2-0. 현재 상태 vs 목표 상태

| 계층 | 현재 (Phase 1-2) | 목표 (Phase 2.5+) | 마이그레이션 |
|------|-----------------|-------------------|------------|
| **쓰기/읽기** | JSON 파일 (원자적 rename) | PostgreSQL (JSONB) | ✅ Phase 2.5 |
| **성능 한계** | ~10K 엔티티 (테스트 중심) | 100K-1M 엔티티 | 100배 확장 |
| **SPARQL** | Mock (정규식) | rdflib 실제 구현 | ✅ Phase 2.5 |
| **동시성** | Atomic Rename (파일 잠금) | PostgreSQL Tx (격리 레벨) | ✅ Phase 2.5 |
| **보안** | 헤더 기반 (위조 가능) | JWT 기반 (암호화) | ✅ Phase 3 초 |

### 2-1. Phase 1-2: JSON 파일 기반 (현재)

```
storage/
└── {company_id}/
    └── {project_id}/
        ├── ontology/
        │   ├── domain_schema.json          # 엔티티 타입, 관계 타입 정의
        │   ├── {domain_name}.json          # 도메인별 온톨로지 인스턴스
        │   ├── materialized/               # ⭐ Materialize 대상 (물리 데이터셋)
        │   │   ├── program_snapshot.json
        │   │   ├── organization_index.json
        │   │   └── ...
        │   └── changelog/                  # ⭐ 변경 이력 (Write-back 추적용)
        │       └── {domain_name}_changes.jsonl
        │
        ├── test_runs/
        │   └── {test_project}/
        │       ├── qa_dataset.json
        │       └── run-{YYYYMMDD-HHMMSS}.json
        │
        └── audit/
            └── {domain_name}_audit.jsonl   # 모든 액션 이력
```

**⚠️ 한계**:
- O(N) 풀 스캔 병목 (100K+ 엔티티에서 급격히 악화)
- 레이스 컨디션 위험 (다중 프로세스 동시 쓰기)
- 메모리 누적 (서버 재시작 시 데이터 손실)

### 2-2. Phase 2.5+: PostgreSQL 하이브리드 (목표)

```
┌─────────────────────────────────────────────────────────┐
│ PostgreSQL (Primary Storage)                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ entities (JSONB + 인덱싱)                               │
│ ├─ id (PK), entity_type, domain_id                     │
│ ├─ properties (JSONB) — GIN 인덱스                    │
│ ├─ version, created_at, updated_at                     │
│ └─ tenant_id (FK → tenants)                            │
│                                                          │
│ relationships (JSONB + 인덱싱)                         │
│ ├─ id (PK), from_entity_id (FK), to_entity_id (FK)   │
│ ├─ relation_type, properties (JSONB)                  │
│ └─ version, created_at, updated_at                     │
│                                                          │
│ audit_log (완전 추적)                                  │
│ ├─ id (PK), entity_id (FK), operation                 │
│ ├─ old_state, new_state (JSONB)                       │
│ ├─ actor, timestamp, reason                           │
│ └─ sync_status (pending/synced)                        │
│                                                          │
│ write_back_queue (동기화 대기)                          │
│ ├─ id (PK), entity_id (FK)                            │
│ ├─ action_type, target_system                         │
│ ├─ payload (JSONB), retry_count                       │
│ └─ status (pending/synced/failed)                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
           ↓ (SPARQL → SQL 번역)
┌─────────────────────────────────────────────────────────┐
│ SPARQL Query Layer (호환성 인터페이스)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ rdflib in-memory 그래프 (작업 영역)                    │
│ ├─ SELECT / CONSTRUCT / DESCRIBE / ASK 지원           │
│ ├─ PREFIX, FILTER, OPTIONAL 지원                      │
│ └─ Property Path (foaf:knows+ 등) 지원               │
│                                                          │
│ SPARQL → SQL 변환 레이어 (성능 최적화)               │
│ ├─ Supported: SELECT * WHERE { ?s ?p ?o }            │
│ ├─ Fallback: 복잡한 쿼리 → rdflib 실행               │
│ └─ Unsupported: 지원 불가 케이스 명시               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**✅ 이점**:
- 100배 성능 향상 (100K-1M 엔티티 지원)
- 트랜잭션 격리 (동시 쓰기 안전)
- 영속성 보장 (서버 재시작 안전)
- 표준 SPARQL 호환 (외부 연동 가능)

### 2-2. 논리 vs 물리 레이어

| 레이어 | 저장 위치 | 특징 | 사용 시점 |
|---|---|---|---|
| **논리 (Logical)** | `ontology/{domain}.json` | 모든 엔티티, 실시간 업데이트 | 조회, 분석 |
| **물리 (Materialized)** | `ontology/materialized/*.json` | 정제·축소된 데이터셋 | 고빈도 쿼리, 보고서 생성 |
| **변경 (Changes)** | `ontology/changelog/*.jsonl` | 액션 로그 (write-back 추적) | 감사, 동기화 |

### 2-3. Materialize 대상 결정 기준

```
온톨로지 엔티티 → Materialize 결정

기준:
1. 조회 빈도 높음 (일일 10회 이상)
2. 조인 비용 높음 (여러 도메인 연관)
3. 계산 비용 높음 (수백 개 엔티티 집계)
4. 변경 빈도 낮음 (주/월 단위)

우선순위:
High   → PROGRAM, ORGANIZATION, METRIC
Medium → CATEGORY, DIVISION
Low    → EVENT, DIVISION_MEMBER
```

### 2-4. Changelog 포맷 (Write-back 추적)

```json
{
  "timestamp": "2026-05-16T10:30:00Z",
  "entity_id": "P001AAA",
  "entity_type": "PROGRAM",
  "action_type": "UPDATE",
  "field_changed": "budget",
  "old_value": "276억원",
  "new_value": "300억원",
  "actor": "user@example.com",
  "source": "web_ui",
  "sync_status": "pending",  // pending | synced | failed
  "target_system": "ERP",    // 원천 DB 동기화 대상
  "sync_timestamp": null
}
```

---

## 3. 쿼리 흐름 (Query Layer)

### 3-1. Intent Classification

```
사용자 질문
  ↓
LLM Classifier (query_planner._llm_classify)
  ├─ FILTER:      "예산 276억 이상인 프로그램 보여줘"
  ├─ DESCRIPTIVE: "AI바우처 2025 총 예산은?"
  ├─ HYBRID:      "지연된 프로젝트와 관련 자료 찾아줘"
  └─ Fallback:    휴리스틱 분류 (_heuristic_classify)
  ↓
QueryPlanV3 생성
```

### 3-2. ONTOLOGY Step (온톨로지 조회)

```
QueryPlanV3.intent = FILTER or HYBRID
  ↓
OntologyQueryEngine.execute(FILTER step)
  ├─ 1) filter_by_property (property=X 조건 명시)
  └─ 2) find_by_name (속성명 불명시 → 토큰 기반 검색)
  ↓
ontology_results = [entity1, entity2, ...]
```

### 3-3. VECTOR Step (문서 검색)

```
QueryPlanV3.intent = DESCRIPTIVE or HYBRID
  ↓
VectorSearchService.search(query, k=5)
  ├─ Gemini Embeddings로 임베딩
  ├─ 벡터 거리 계산
  └─ Top-k 문서 반환
  ↓
vector_results = [doc1, doc2, ...]
```

### 3-4. Synthesis (LLM 합성)

```
HybridSynthesizer.synthesize(
  query,
  ontology_results,  # ONTOLOGY step의 결과
  vector_results,    # VECTOR step의 결과
  trace
)
  ↓
최종 답변 생성 + quality_metrics
  ├─ ontology_hits: len(ontology_results)
  ├─ vector_hits: len(vector_results)
  ├─ llm_used: boolean
  └─ answer: string
```

---

## 4. 온톨로지 설계 (Ontology Schema)

### 4-1. 엔티티 타입 정의

```json
{
  "entity_types": [
    {
      "name": "PROGRAM",
      "description": "정부 지원 프로그램 (예: AI바우처)",
      "properties": ["budget", "year", "quota", "deadline"]
    },
    {
      "name": "ORGANIZATION",
      "description": "기관/기업",
      "properties": ["role", "type", "contact"]
    },
    {
      "name": "CATEGORY",
      "description": "분류/분과 (예: 일반/AI반도체)",
      "properties": ["code", "description"]
    },
    {
      "name": "METRIC",
      "description": "수치/지표",
      "properties": ["value", "unit", "period"]
    }
    // ... 더 많은 타입
  ],
  
  "relation_types": [
    {
      "name": "MANAGES",
      "description": "A가 B를 주관하거나 관리",
      "from": "ORGANIZATION",
      "to": "PROGRAM"
    },
    {
      "name": "HAS_DIVISION",
      "description": "A가 B 분과를 포함",
      "from": "PROGRAM",
      "to": "CATEGORY"
    }
    // ...
  ]
}
```

### 4-2. 인스턴스 저장 포맷

```json
{
  "doc_id": "ai-voucher-2025",
  "entities": [
    {
      "id": "P001AAA",
      "type": "PROGRAM",
      "name": "AI바우처 2025",
      "properties": {
        "budget": "276억원",
        "year": 2025,
        "quota": 130
      },
      "created_at": "2026-05-14T09:00:00Z",
      "updated_at": "2026-05-14T09:00:00Z",
      "version": 1
    }
  ],
  "relations": [
    {
      "from_id": "O001AAA",
      "to_id": "P001AAA",
      "type": "MANAGES",
      "metadata": {}
    }
  ]
}
```

---

## 5. 현재 구현 단계 vs 로드맵

### 5-1. 현재 상태 (Phase 2.5)

```
✅ Phase 1: 데이터 연결
   └─ Ontology JSON 저장소 구축
   └─ 기본 쿼리 (find_by_name, filter_by_property)

✅ Phase 2: 온톨로지 + RAG 하이브리드
   └─ Intent 분류 (LLM)
   └─ ONTOLOGY + VECTOR 병렬 실행
   └─ HybridSynthesizer로 답변 생성

❌ Phase 3: 워크플로우 + Action 실행
   └─ 비즈니스 액션 미정의 (쿼리 액션만 있음)
   └─ Write-back 메커니즘 없음
   └─ Action 버튼/UI 없음
```

### 5-2. Phase 3 요구사항

```
1. ActionType 확장
   - APPROVE (승인)
   - REJECT (반려)
   - CHANGE_STATUS (상태 변경)
   - REQUEST_PROCUREMENT (발주 요청)

2. Workflow Engine 통합
   - 상태 전이 규칙 정의
   - 조건부 승인 (금액 이상 → 관리자만)
   - 실행 이력 저장 (audit)

3. Write-back 메커니즘
   - changelog 항목 자동 생성
   - 원천 시스템 동기화 (ERP, SAP)
   - 실패 처리 및 재시도

4. Frontend 연동
   - available_actions 버튼 렌더링
   - 액션 실행 후 결과 표시
   - 실행 이력 조회
```

---

## 6. 도메인 온톨로지 예시 (다중 도메인 확장)

### 6-1. AI바우처 도메인 (현재)

```
PROGRAM (AI바우처 2025)
  ├─ MANAGES → ORGANIZATION (과기정통부, NIPA, ...)
  ├─ HAS_DIVISION → CATEGORY (일반, AI반도체, ...)
  └─ HAS_METRIC → METRIC (2025총예산, 과제당최대지원비, ...)
```

### 6-2. 조선 도메인 (추가 예정)

```
SHIP (선박)
  ├─ 속성: ship_id, name, wc_date, status
  ├─ CONSISTS_OF → BLOCK (블록)
  │   ├─ 속성: block_id, name, status
  │   └─ CONTAINS → MATERIAL (자재)
  │
  ├─ ASSIGNED_TO → WORKER (담당자)
  │
  └─ MONITORED_BY → SENSOR (센서)

ACTION:
  - ChangeWCDate (공정 지연 대응)
  - RequestMaterial (자재 긴급 발주)
  - NotifyWorker (담당자 알림)
  - SyncToERP (ERP 자동 업데이트)
```

### 6-3. 제조/공정 도메인 (추가 예정)

```
FACTORY (공장)
  ├─ OPERATES → PRODUCTION_LINE (생산라인)
  │
  ├─ PRODUCES → PRODUCT (제품)
  │
  └─ MONITORS → METRIC (생산량, 불량율, ...)

ACTION:
  - AdjustSchedule
  - OrderComponent
  - StopLine
  - AlertQC
```

---

## 7. 비용 구조 (Cost Planning)

### 7-1. 온톨로지 유지 비용

| 항목 | 단위 | 월 비용(추정) | 근거 |
|---|---|---|---|
| Ontology 조회 (find_by_name) | 1만 건 | ~₩10K | 토큰 기반 매칭 경량 |
| Filter 조회 | 1만 건 | ~₩5K | 정확한 필터링 |
| Materialize (스냅샷) | 월 1회 | ~₩50K | JSON 파일 생성 |
| 벡터 임베딩 (쿼리당) | 100 쿼리 | ~₩1M | Gemini API 과금 |
| LLM 분류/합성 | 100 쿼리 | ~₩2M | Gemini API 과금 |

**월 총액: ~₩3.5M**

### 7-2. 확장 시나리오

```
현재 (1 도메인)         → ₩3.5M/월
3 도메인 (조선+제조)   → ₩10M/월
5 도메인 + 실시간      → ₩25M/월
```

### 7-3. 비용 최적화 전략

```
1. Materialize 대상 한정
   - 고빈도 조회만 물리화 (주당 100회 이상)
   - 저빈도 조회는 온디맨드 계산

2. LLM API 캐싱
   - 동일 쿼리 재사용 (1주일 캐시)
   - 배치 처리 (대량 쿼리 시간대 분산)

3. 벡터 검색 최적화
   - 도메인별 임베딩 재사용
   - 오래된 문서는 인덱스에서 제거
```

---

## 8. 마이그레이션 경로 (JSON → 프로덕션)

### 현재 (프로토타입)
```
JSON 파일 저장소
└─ 개발/테스트 용도
└─ 단일 테넌트
```

### 단기 (6개월)
```
JSON 저장소 + PostgreSQL
├─ JSON: 온톨로지 스키마 정의
├─ PostgreSQL: 인스턴스 저장
└─ 변경 로그 추적
```

### 장기 (1년+)
```
PostgreSQL + Elasticsearch + S3
├─ PostgreSQL: 온톨로지 + 관계
├─ Elasticsearch: 벡터 검색 인덱스
├─ S3: Materialize 스냅샷
└─ 외부 LLM API 또는 on-prem 모델
```

---

## 9. 정리

**현재 아키텍처의 강점:**
- 온톨로지 개념 명확
- LLM + RAG 하이브리드 쿼리 동작
- 멀티테넌트 기반

**보완 필요:**
- Materialize / Write-back 메커니즘
- 비즈니스 액션 정의
- 도메인 확장 (다중 도메인)
- 원천 시스템 동기화
