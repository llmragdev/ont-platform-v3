# 하이브리드 질의 시스템 설계서

> 기반 요건: `hybrid_query_requirements.md`  
> 작성일: 2026-05-13  
> 범위: `claud_통합` 백엔드 + 프론트엔드

---

## 1. 전체 아키텍처

```
PDF 업로드
    │
    ├─── [기존] 청크 분할 → 벡터 임베딩 → Chroma DB
    │
    └─── [신규] 전체 텍스트 → LLM 엔티티 추출 → ontology_db/
                                                    {doc_id}.json

질문 입력
    │
    ▼
[신규] 질문 유형 분류기 (LLM 1회 호출)
    │
    ├── descriptive  → 벡터 검색만  → 기존 ask_rag()
    ├── filter       → 온톨로지만   → ontology_query()
    ├── compare      → 온톨로지만   → ontology_query()
    ├── calculate    → 온톨로지만   → ontology_query()
    └── hybrid       → 둘 다       → merge_results()
    │
    ▼
LLM 최종 답변 생성 (서술형 + 구조형 동시)
```

---

## 2. 온톨로지 데이터 모델

### 2-1. 저장 위치
```
backend/
  ontology_db/
    {doc_id}_ontology.json   ← 문서별 그래프
    ontology_registry.json   ← 문서-그래프 인덱스
```

### 2-2. JSON 스키마
```json
{
  "doc_id": "doc-abc12345",
  "filename": "Snowflake_소개서_HDC.pdf",
  "entities": [
    {
      "id": "E001",
      "type": "인물",
      "name": "Benoit Dageville",
      "properties": {
        "소속": "Oracle 출신",
        "특기": "parallel query execution",
        "역할": "창립자"
      }
    },
    {
      "id": "E002",
      "type": "기능",
      "name": "Virtual Warehouse",
      "properties": {
        "과금방식": "초단위",
        "기능": ["Scale up", "Scale out", "Suspend"],
        "계층": "컴퓨팅"
      }
    },
    {
      "id": "E003",
      "type": "기능",
      "name": "Snowpipe",
      "properties": {
        "과금방식": "Serverless",
        "계층": "Cloud Services"
      }
    }
  ],
  "relationships": [
    {
      "from": "E001",
      "relation": "창립자_of",
      "to": "Snowflake"
    },
    {
      "from": "E003",
      "relation": "속한_계층",
      "to": "Cloud Services"
    }
  ]
}
```

### 2-3. 엔티티 유형 — 2계층 구조

#### Layer 1: 범용 유형 (모든 문서에 공통 적용, 하드코딩 X)
| 범용 유형 | 설명 | 예시 |
|-----------|------|------|
| `PERSON` | 인물, 직책, 역할 | 창립자, 임원, 저자 |
| `ORGANIZATION` | 회사, 기관, 단체 | Snowflake, Oracle, 삼성전자 |
| `PRODUCT` | 제품, 서비스, 기능 | Virtual Warehouse, Snowpipe |
| `METRIC` | 수치, 지표, 통계 | 매출 $640.2M, 고객수 8537 |
| `CONCEPT` | 개념, 방법론, 아키텍처 | Data Sharing, MVCC |
| `CATEGORY` | 분류, 그룹 | 통신사, Serverless, 한국 고객 |
| `EVENT` | 사건, 일정, 이정표 | NYSE 상장, 한국 지사 설립 |
| `LOCATION` | 지역, 클라우드 리전 | AWS ap-northeast-2, 한국 |

#### Layer 2: 도메인 유형 (문서별 config로 주입, 없으면 범용만 사용)
```json
// backend/ontology_db/domain_config.json (사용자가 정의)
{
  "domain": "cloud_data_platform",
  "extra_types": ["과금방식", "아키텍처계층", "데이터공유방식"],
  "extra_relations": ["속한_계층", "과금_방식", "지원_클라우드"]
}
```

> **범용 유형만으로도 동작**하며, domain_config.json이 있으면 추출 정밀도가 높아짐.  
> domain_config.json이 없으면 LLM이 문서에서 스스로 유형을 추론.

---

## 3. 백엔드 신규 모듈

### 3-0. `ontology_store.py` (신규 — JSON 영속성 계층)
```
역할: ontology_db/ 폴더의 JSON 파일 CRUD 전담
      ontology_extractor / ontology_query_engine 이 직접 파일 IO 하지 않음

주요 메서드:
  save_ontology(doc_id, data: dict) -> None
  load_ontology(doc_id) -> dict | None
  list_ontologies() -> list[dict]          ← registry 조회
  delete_ontology(doc_id) -> bool

  # 인스턴스 수준 편집
  upsert_entity(doc_id, entity: dict) -> dict
  delete_entity(doc_id, entity_id) -> bool
  add_relationship(doc_id, rel: dict) -> dict
  delete_relationship(doc_id, rel_id) -> bool

  # 스키마 수준 편집
  get_schema() -> dict                     ← domain_config.json 반환
  save_schema(schema: dict) -> None

저장 경로:
  backend/ontology_db/
    {doc_id}_ontology.json
    ontology_registry.json
    domain_config.json
```

---

### 3-1. `ontology_extractor.py` (신규)
```
역할: PDF 텍스트 → LLM → 엔티티/관계 JSON 생성

주요 메서드:
  extract(text: str, doc_id: str, domain_config: dict | None = None) -> dict
    - 전체 텍스트를 LLM에 전달해 엔티티/관계 추출
    - 결과를 ontology_db/{doc_id}_ontology.json 저장

프롬프트 전략 (범용화 핵심):

  [1단계] LLM에 전달하는 유형 목록 구성 방식
    base_types = PERSON, ORGANIZATION, PRODUCT, METRIC, CONCEPT, CATEGORY, EVENT, LOCATION
    extra_types = domain_config["extra_types"] if domain_config else []
    final_types = base_types + extra_types   ← 런타임 조합

  [2단계] 프롬프트 구조
    "다음 텍스트에서 아래 유형의 엔티티를 추출하고 관계를 JSON으로 반환하라.
     유형: {final_types}
     - 유형에 맞지 않는 것은 CONCEPT으로 분류
     - 수치는 반드시 METRIC 유형으로 value, unit 포함
     - 관계는 from/relation/to 방향 명시
     - 문서에 없는 내용 추가 금지"

  [3단계] 결과 검증
    - JSON 파싱 실패 시 재시도 1회
    - entity id 중복 제거
    - 빈 name 필터링
```

### 3-2. `ontology_query_engine.py` (신규)
```
역할: 온톨로지 JSON → 구조형 질의 처리 (문서 도메인 무관하게 동작)

모든 메서드는 entity_type에 범용 유형(PERSON 등)과
도메인 유형(과금방식 등) 둘 다 허용.

filter_by_property(entity_type, property_key, property_value, docs=None)
  - docs: 특정 문서만 검색 (None이면 전체 ontology_db 검색)
  예: filter_by_property("PRODUCT", "과금방식", "Serverless")
  예: filter_by_property("ORGANIZATION", "산업군", "통신")

compare_entities(names: list[str], docs=None) -> structured_table
  - name 기반으로 엔티티 검색 후 properties 교집합 컬럼으로 테이블 생성
  - 컬럼은 고정하지 않고 실제 데이터에서 동적 추출
  예: compare_entities(["Benoit Dageville", "Thierry Curanes", "Marcin Zukowski"])

calculate(metric_names: list[str], operation: str) -> number | str
  - operation: "sum" | "ratio" | "avg" | "max" | "min"
  - METRIC 유형에서 value 추출 후 연산
  예: calculate(["전체 고객수", "$1M 고객수"], "ratio")

find_by_category(entity_type, category_hint: str, docs=None) -> list
  - category_hint를 LLM 없이 fuzzy match로 처리
  예: find_by_category("ORGANIZATION", "통신")
  예: find_by_category("PRODUCT", "Serverless")

search_relations(from_name: str, relation_hint: str = None) -> list
  - 엔티티 이름으로 연결된 관계 전체 조회
  예: search_relations("Snowflake", "창립자")
```

### 3-3. `query_classifier.py` (신규)
```
역할: 질문 → 유형 분류

입력: question: str
출력: {
  "type": "filter" | "compare" | "calculate" | "hybrid" | "descriptive",
  "entities": ["Virtual Warehouse", "Snowpipe"],   ← 힌트
  "operation": "list" | "compare" | "ratio"        ← 힌트
}

구현: LLM 1회 호출 (짧은 classification 프롬프트, ~300ms)
```

### 3-4. `app_context.py` 수정
```
ask_hybrid() 추가:
  1. query_classifier로 유형 판별
  2. descriptive → 기존 ask_rag() 호출
  3. 구조형 → ontology_query_engine 호출
  4. hybrid → 둘 다 호출 후 merge
  5. LLM에 "서술형 요약 + 구조형 데이터" 동시 생성 요청
```

### 3-5. `schemas.py` 추가 Pydantic 모델
```python
# 온톨로지 추출 요청
class OntologyExtractRequest(BaseModel):
    doc_id: str

# 스키마 관리
class EntityTypeCreate(BaseModel):
    name: str
    description: str = ""
    properties: list[str] = []

class RelationTypeCreate(BaseModel):
    name: str
    from_type: str
    to_type: str

# 인스턴스 관리
class EntityCreate(BaseModel):
    type: str
    name: str
    properties: dict = {}

class EntityUpdate(BaseModel):
    name: str | None = None
    properties: dict | None = None

class RelationshipCreate(BaseModel):
    from_id: str
    relation: str
    to_id: str

# 하이브리드 질의
class HybridAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    doc_ids: list[str] | None = None   # None = 전체 문서 대상
```

---

### 3-6. `Sidebar.tsx` 추가 ViewKey
```typescript
// 기존 ViewKey에 추가
| "ontology-schema"    // 스키마 정의
| "ontology-instance"  // 인스턴스 편집
| "ontology-graph-edit"// 관계 그래프 편집 (기존 ontology-graph 는 탐색 전용 유지)

// Sidebar items 추가
{ key: "ontology-schema",     label: "스키마 정의",    description: "엔티티·관계 유형 관리" },
{ key: "ontology-instance",   label: "인스턴스 편집",  description: "추출된 엔티티 수정·추가" },
{ key: "ontology-graph-edit", label: "관계 그래프 편집", description: "React Flow 노드·엣지 편집" },
```

---

### 3-7. `main.py` 신규 엔드포인트
```
# 온톨로지 추출
POST /api/documents/extract-ontology
  body: { doc_id: str }
  → 업로드된 PDF에서 온톨로지 추출 실행

# 하이브리드 질의
POST /api/hybrid/ask
  body: { question: str, doc_ids: list[str] | None }
  → 유형 분류 → 라우팅 → 답변 반환

# ── 온톨로지 관리 (스키마) ──────────────────────────
GET  /api/ontology/schema
  → 전체 엔티티 유형 + 관계 유형 목록 반환

POST /api/ontology/schema/entity-types
  body: { name: str, description: str, properties: list[str] }
  → 사용자 정의 엔티티 유형 추가

DELETE /api/ontology/schema/entity-types/{type_name}
  → 엔티티 유형 삭제

POST /api/ontology/schema/relation-types
  body: { name: str, from_type: str, to_type: str }
  → 관계 유형 추가

# ── 온톨로지 관리 (인스턴스) ────────────────────────
GET  /api/ontology/{doc_id}/entities
  → 문서의 엔티티 목록 (페이징)
  query: ?type=PERSON&page=1&size=20

PUT  /api/ontology/{doc_id}/entities/{entity_id}
  body: { name: str, properties: dict }
  → 엔티티 속성 수정

POST /api/ontology/{doc_id}/entities
  body: { type: str, name: str, properties: dict }
  → 엔티티 수동 추가

DELETE /api/ontology/{doc_id}/entities/{entity_id}
  → 엔티티 삭제

GET  /api/ontology/{doc_id}/relationships
  → 관계 목록

POST /api/ontology/{doc_id}/relationships
  body: { from_id: str, relation: str, to_id: str }
  → 관계 수동 추가

DELETE /api/ontology/{doc_id}/relationships/{rel_id}
  → 관계 삭제

# ── 그래프 뷰용 ──────────────────────────────────────
GET /api/ontology/{doc_id}/graph
  → React Flow 형식 { nodes: [...], edges: [...] } 반환
```

---

## 4. 프론트엔드 설계

### 4-0. 사이드바 메뉴 추가
```
기존 메뉴에 "온톨로지 관리" 그룹 추가:

  온톨로지 관리
  ├── ontology-schema   스키마 정의    (엔티티/관계 유형 폼 편집)
  ├── ontology-instance 인스턴스 편집  (추출 데이터 테이블 편집)
  └── ontology-graph    관계 그래프    (React Flow 탐색 + 엣지 편집)

  기존 "통합 질의" → hybrid-query   (준비중 → 실제 구현)
```

---

### 4-1. `OntologySchemaManager.tsx` (신규 — 스키마 정의 화면)

**팔란티어 Ontology Manager 대응 화면**

```
┌──────────────────────────────────────────────────────┐
│ 스키마 정의                                           │
│ 엔티티 유형과 관계 유형을 설정합니다                  │
├────────────────────────┬─────────────────────────────┤
│ 엔티티 유형            │ 관계 유형                    │
│                        │                              │
│ 범용 (자동, 수정불가)  │ [+ 관계 유형 추가]          │
│  • PERSON              │                              │
│  • ORGANIZATION        │ 창립자_of                    │
│  • PRODUCT             │   from: PERSON               │
│  • METRIC              │   to:   ORGANIZATION  [삭제] │
│  • CONCEPT             │                              │
│  • CATEGORY            │ 속한_계층                    │
│  • EVENT               │   from: PRODUCT              │
│  • LOCATION            │   to:   CONCEPT       [삭제] │
│                        │                              │
│ 도메인 (편집 가능)     │                              │
│  • 과금방식     [삭제] │                              │
│  • 아키텍처계층 [삭제] │                              │
│ [+ 유형 추가]          │                              │
└────────────────────────┴─────────────────────────────┘
```

- 범용 8종은 읽기 전용 (삭제/수정 불가)
- 도메인 유형은 추가/삭제 가능
- 변경 시 `/api/ontology/schema` PUT 호출

---

### 4-2. `OntologyInstanceEditor.tsx` (신규 — 인스턴스 편집 화면)

**추출된 엔티티 데이터를 테이블로 조회/편집**

```
┌──────────────────────────────────────────────────────┐
│ 인스턴스 편집                 [문서 선택 ▼]          │
│ Snowflake_소개서_HDC.pdf                             │
├──────────────────────────────────────────────────────┤
│ 유형 필터: [전체 ▼]  [PERSON] [ORGANIZATION] ...    │
│                                      [+ 수동 추가]   │
├───┬──────────────────┬────────────┬──────────────────┤
│   │ 이름             │ 유형       │ 주요 속성        │
├───┼──────────────────┼────────────┼──────────────────┤
│ ✎ │ Benoit Dageville │ PERSON     │ 역할: 창립자...  │
│ ✎ │ Virtual Warehouse│ PRODUCT    │ 과금: 초단위...  │
│ ✎ │ Snowflake        │ ORGANIZATION│ 설립: 2012...   │
│ ✎ │ $640.2M          │ METRIC     │ 기준: Q2 FY24   │
└───┴──────────────────┴────────────┴──────────────────┘

[행 클릭 시 오른쪽에 속성 편집 패널 슬라이드인]
┌─────────────────────────────┐
│ Benoit Dageville  [저장][삭제]│
│ 유형: PERSON                │
│ 속성:                       │
│   역할: [창립자          ]  │
│   소속: [Oracle 출신     ]  │
│   특기: [parallel query..]  │
│   [+ 속성 추가]             │
└─────────────────────────────┘
```

---

### 4-3. `OntologyGraphEditor.tsx` (신규 — 관계 그래프 화면)

**React Flow 기반, 기존 OntologyExplorerCanvas 확장**

```
┌──────────────────────────────────────────────────────┐
│ 관계 그래프          [문서 선택 ▼]  [필터: 유형 ▼]  │
├──────────────────────────────────────────────────────┤
│                                                       │
│   [PERSON]           [ORGANIZATION]                  │
│  Benoit ──창립자_of──▶ Snowflake                     │
│  Thierry ──창립자_of──▶                              │
│                          │                            │
│                    지원_클라우드                       │
│                    ↙    ↓    ↘                       │
│                 [AWS] [GCP] [Azure]                   │
│                                                       │
│  ── 노드 클릭: 속성 팝업                             │
│  ── 엣지 클릭: 관계 삭제 버튼 표시                   │
│  ── 노드 드래그 후 다른 노드에 드롭: 관계 추가 모달  │
└──────────────────────────────────────────────────────┘

관계 추가 모달 (드래그 드롭 시):
┌──────────────────────────┐
│ 관계 추가                │
│ From: Benoit Dageville   │
│ To:   Virtual Warehouse  │
│ 관계: [관계 유형 선택 ▼] │
│       [확인]  [취소]     │
└──────────────────────────┘
```

---

### 4-4. `HybridQuery.tsx` (신규, 현재 준비중 placeholder 대체)

```
레이아웃:
┌─────────────────────────────────────────┐
│ 통합 질의 (온톨로지 + 문서 RAG)          │
│ 업로드된 문서와 온톨로지를 함께 활용      │
├─────────────────────────────────────────┤
│ [질문 입력창]          [질의 실행 버튼]  │
│ 감지된 유형: [필터형 배지]               │
├─────────────────────────────────────────┤
│ AI 답변 (서술형)                         │
│ ...텍스트 답변...                        │
├─────────────────────────────────────────┤
│ 구조형 결과                              │
│ ┌──────┬────────────┬──────────────┐   │
│ │ 이름 │ 특기       │ 소속         │   │
│ ├──────┼────────────┼──────────────┤   │
│ │ ...  │ ...        │ ...          │   │
│ └──────┴────────────┴──────────────┘   │
├─────────────────────────────────────────┤
│ 근거: 벡터 청크 N건 / 온톨로지 노드 M개  │
└─────────────────────────────────────────┘
```

### 4-5. `RAGQuery.tsx` 수정 (온톨로지 추출 옵션 추가)
```
PDF 업로드 버튼 옆에 체크박스 추가:
  ☑ 온톨로지 자동 추출 (구조형 질문 지원)
  → 체크 시 업로드 후 /api/documents/extract-ontology 추가 호출
  → 추출 중 스피너 표시
```

### 4-6. 신규 API 타입 (`api.ts`)
```typescript
type QueryType = "descriptive" | "filter" | "compare" | "calculate" | "hybrid"

// 하이브리드 질의 응답
interface HybridAskResponse {
  answer: string
  query_type: QueryType
  structured_data?: { headers: string[]; rows: string[][] }
  vector_evidence: Evidence[]
  ontology_nodes: string[]
  steps: Step[]
  latency_ms: number
}

// 스키마 관리
interface EntityTypeDef { name: string; description: string; is_builtin: boolean; properties: string[] }
interface RelationTypeDef { name: string; from_type: string; to_type: string }
interface OntologySchema { entity_types: EntityTypeDef[]; relation_types: RelationTypeDef[] }

// 인스턴스 관리
interface OntologyEntity { id: string; type: string; name: string; properties: Record<string, unknown> }
interface OntologyRelationship { id: string; from_id: string; relation: string; to_id: string }
interface OntologyInstancesResponse { entities: OntologyEntity[]; total: number; page: number }

// 그래프 뷰
interface OntologyGraphResponse {
  nodes: { id: string; label: string; type: string; properties: Record<string, unknown> }[]
  edges: { id: string; from: string; to: string; label: string }[]
}
```

---

## 5. 구현 순서 (권장)

```
Phase 1 — 백엔드 온톨로지 구축
  1. ontology_extractor.py 작성
  2. /api/documents/extract-ontology 엔드포인트
  3. 스노우플레이크 PDF로 추출 검증

Phase 2 — 백엔드 관리 API
  4. 스키마 관리 엔드포인트 (GET/POST/DELETE /api/ontology/schema/*)
  5. 인스턴스 관리 엔드포인트 (GET/PUT/POST/DELETE /api/ontology/{doc_id}/entities)
  6. 관계 관리 엔드포인트 (POST/DELETE /api/ontology/{doc_id}/relationships)
  7. 그래프 뷰 엔드포인트 (GET /api/ontology/{doc_id}/graph)

Phase 3 — 질의 엔진
  8. query_classifier.py 작성
  9. ontology_query_engine.py 작성
  10. ask_hybrid() 통합

Phase 4 — 프론트엔드 관리 화면
  11. Sidebar에 온톨로지 관리 메뉴 3개 추가
  12. OntologySchemaManager.tsx (스키마 정의 화면)
  13. OntologyInstanceEditor.tsx (인스턴스 테이블 편집)
  14. OntologyGraphEditor.tsx (React Flow 그래프 + 엣지 편집)

Phase 5 — 프론트엔드 질의 화면
  15. HybridQuery.tsx (통합 질의 메뉴 구현)
  16. RAGQuery.tsx 온톨로지 추출 체크박스 추가

Phase 6 — 테스트
  17. 요건서의 6가지 질문 유형 전부 통과 확인
  18. 스키마 CRUD → 인스턴스 편집 → 질의 E2E 확인
```

---

## 6. 설계 결정 사항

| 항목 | 결정 | 이유 |
|------|------|------|
| 온톨로지 저장소 | JSON 파일 | 추가 의존성 없음, 이 규모에서 충분 |
| 엔티티 추출 방식 | 전체 텍스트 요약본으로 1회 LLM 호출 | 청크별 호출 시 중복/누락 발생 |
| 엔티티 유형 | 범용 8종 고정 + 도메인 config 선택 주입 | 하드코딩 없이 어떤 문서든 동작 |
| 도메인 config | JSON 파일 (없으면 범용만 사용) | 강제 아님, 있으면 정밀도 향상 |
| 질문 분류 | LLM (짧은 프롬프트) | 규칙 기반보다 한국어 자연어에 강함 |
| 구조형 결과 렌더링 | 동적 테이블 (headers + rows) | 엔티티 유형마다 컬럼이 다름 |
| 온톨로지 추출 타이밍 | 선택적 (체크박스) | 항상 추출 시 업로드 속도 저하 |
| 관리 UI 방식 | 팔란티어 패턴 (스키마=폼, 인스턴스=테이블, 관계=그래프) | 역할별 최적 인터페이스 분리 |
| 그래프 편집 | 노드 드래그 드롭 → 관계 추가 모달 | 엣지 직접 드로잉보다 실수 방지 |

---

## 7. 범용화 보장 체크리스트

- [ ] 엔티티 유형이 코드에 문자열로 박혀있지 않음 (런타임 조합)
- [ ] domain_config.json 없이도 전체 파이프라인 동작
- [ ] 질의 엔진 메서드가 특정 도메인 용어를 가정하지 않음
- [ ] 테이블 컬럼이 고정되지 않고 데이터에서 동적 추출
- [ ] 스노우플레이크 PDF 외 다른 PDF(계약서, 기술문서 등)로 동작 검증
