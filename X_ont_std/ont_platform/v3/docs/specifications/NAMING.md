# ont_platform v3.0 네이밍 컨벤션

> 문서 버전: 1.0  
> 기준일: 2026-05-16  
> 목적: 6개월 후 레거시가 되지 않도록 일관성 있는 네이밍 강제

---

## 1. 폴더 구조 (Folder Organization)

### 1-1. 저장소 계층

```
storage/
├── {company_id}                          # 테넌트 회사 ID (lowercase)
│   └── {project_id}                      # 테넌트 프로젝트 ID (lowercase)
│       ├── ontology/
│       │   ├── domain_schema.json        # 타입 정의 (공통)
│       │   ├── {domain}/                 # 도메인별 폴더
│       │   │   ├── entities.json         # 인스턴스
│       │   │   ├── schema.json           # 도메인별 스키마 (선택)
│       │   │   └── README.md             # 도메인 설명
│       │   ├── materialized/             # 물리화된 데이터셋
│       │   │   └── {domain}_{frequency}.json
│       │   └── changelog/                # 변경 이력
│       │       └── {domain}.jsonl
│       ├── test_runs/
│       │   └── {test_project}/
│       └── audit/
│           └── {domain}_audit.jsonl
│
└── (향후) MongoDB, PostgreSQL 등으로 마이그레이션 시에는
    컨테이너 기반 저장이므로 폴더 구조 재설계
```

**원칙:**
- 회사/프로젝트 ID: lowercase (demo-co, proj-01)
- 도메인명: lowercase-kebab-case (ai-voucher, ship-building, manufacturing)

---

## 2. 파일 네이밍 (File Naming)

### 2-1. 온톨로지 저장 파일

**패턴: `{domain}[-{version}].json`**

```
✅ 좋은 예:
  ai-voucher-2025.json
  ai-voucher-2024.json
  ship-building-v2.json
  manufacturing.json

❌ 나쁜 예:
  entities.json              # 도메인 불명확
  data_2025.json             # 의도 불명확
  ontology_ai_voucher.json   # 불필요한 접두사
```

**버전 관리:**
```
도메인이 연년도별로 변하는 경우:
  ai-voucher-2025.json (○ 명확)
  ai-voucher-2024.json (○ 명확)

스키마가 진화하는 경우:
  ship-building.json    (v1 암시)
  ship-building-v2.json (v2 명시 — 주요 변경 시에만)
```

### 2-2. Materialize 파일

**패턴: `{domain}_{frequency}_{snapshot}.json`**

```
{frequency}:
  - daily    (매일 자정 스냅샷)
  - weekly   (주간 일요일)
  - monthly  (월간 1일)

{snapshot}: ISO 8601 date

예시:
  ai-voucher_monthly_20260501.json
  ship-building_weekly_20260511.json
  manufacturing_daily_20260516.json
```

### 2-3. 변경 로그 파일

**패턴: `{domain}[-changes].jsonl`**

```
✅ 좋은 예:
  ai-voucher-changes.jsonl
  ship-building.jsonl
  manufacturing-changes.jsonl

❌ 나쁜 예:
  changelog.jsonl          # 도메인 불명확
  {domain}_audit.jsonl     # audit과 혼동
```

### 2-4. 테스트 관련 파일

**패턴: `qa_dataset.json` (공통)**

```
test_data/
├── ai-voucher-2025/
│   ├── qa_dataset.json
│   └── run-20260514-020954.json

├── ship-building/
│   ├── qa_dataset.json
│   └── run-*.json

패턴 설명:
  qa_dataset.json         — 테스트 케이스 정의 (동적 변경 거의 없음)
  run-{YYYYMMDD-HHMMSS}   — 테스트 실행 결과 (매번 생성)
```

---

## 3. 코드 네이밍 (Code Naming)

### 3-1. Python 클래스 및 함수

**원칙: snake_case (PEP 8)**

```python
# ✅ 좋은 예
class OntologyService:
    def find_by_name(self, ctx: TenantContext, name_hint: str) -> List[Dict]:
        pass
    
    def filter_by_property(self, ctx, entity_type, prop_key, prop_value):
        pass

# ❌ 나쁜 예
class OntologyService:
    def findByName(self):  # camelCase 금지
        pass
    
    def find_entity_by_name_hint_parameter(self):  # 너무 길음
        pass
```

### 3-2. 엔티티 타입명

**원칙: PascalCase (고정 문자열)**

```python
# ✅ 좋은 예
ENTITY_TYPES = {
    "PROGRAM": {...},          # 대문자
    "ORGANIZATION": {...},
    "CATEGORY": {...},
}

# ❌ 나쁜 예
ENTITY_TYPES = {
    "program": {...},          # 소문자 (일관성 깨짐)
    "Org": {...},              # 축약형 (의도 불명확)
}
```

### 3-3. 속성명 (Property Names)

**원칙: snake_case (CamelCase 금지)**

```json
{
  "entity_id": "P001AAA",
  "entity_type": "PROGRAM",
  "created_at": "2026-05-14T09:00:00Z",
  "updated_by": "user@example.com"
}

# ❌ 나쁜 예
{
  "entityId": "...",         # camelCase
  "CreatedAt": "...",        # PascalCase
  "updated_By": "...",       # 혼합
}
```

### 3-4. 함수 인자명

```python
# ✅ 좋은 예
def upsert_entity(
    self,
    doc_id: str,
    entity: Dict,
    ctx: TenantContext,
) -> Dict:
    pass

# ❌ 나쁜 예
def upsert_entity(self, d: str, e: Dict, c):  # 약자 금지
    pass

def upsert_entity(self, documentId, entityObject, context):  # camelCase
    pass
```

---

## 4. 데이터베이스 네이밍 (향후 마이그레이션)

### 4-1. 테이블명 (Table Names)

```sql
-- ✅ 좋은 예
CREATE TABLE ontology_entities (
    entity_id VARCHAR PRIMARY KEY,
    entity_type VARCHAR,
    name VARCHAR,
    doc_id VARCHAR,
    created_at TIMESTAMP,
    ...
);

CREATE TABLE ontology_relations (
    from_id VARCHAR,
    to_id VARCHAR,
    relation_type VARCHAR,
    ...
);

CREATE TABLE entity_changes (
    change_id UUID PRIMARY KEY,
    entity_id VARCHAR,
    entity_type VARCHAR,
    field_changed VARCHAR,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR,
    changed_at TIMESTAMP,
    sync_status VARCHAR,  -- pending, synced, failed
    ...
);

-- ❌ 나쁜 예
CREATE TABLE entities;          -- domain 불명확
CREATE TABLE t_ontology;        # 접두사 (t_는 legacy)
CREATE TABLE ONTOLOGY_ENTITY;   # 대문자 (PostgreSQL에선 소문자로 변환)
```

### 4-2. 컬럼명

**원칙: snake_case, 예약어 피하기**

```sql
-- ✅
created_at, updated_at, deleted_at
created_by, updated_by
domain_id, entity_type
parent_id, child_id  (vs parent, child — 덜 명확)
is_active, is_deleted

-- ❌
createdAt, UpdatedAt  (camelCase)
create_date           (at vs date — 일관성)
type                  (너무 generic)
uid                   (약자)
```

---

## 5. API 엔드포인트 네이밍

**원칙: RESTful, lowercase-kebab-case**

```
✅ 좋은 예:
  GET /api/ontology/{domain}/entities
  POST /api/ontology/{domain}/entities
  PUT /api/ontology/{domain}/entities/{entity_id}
  DELETE /api/ontology/{domain}/entities/{entity_id}
  
  POST /api/ontology/schema
  GET /api/ontology/{domain}/schema
  
  POST /api/query/ask
  POST /api/query/classify-intent
  
  POST /api/integration-test/run
  GET /api/integration-test/projects
  GET /api/integration-test/{project}/runs

❌ 나쁜 예:
  GET /api/Ontology/GetEntities        (PascalCase, 동사 포함)
  POST /api/ontology/createEntity      (camelCase)
  GET /api/ontology_entities           (언더스코어)
  GET /api/ontology/getEntityById/123  (복잡)
```

---

## 6. 환경 변수 (Environment Variables)

**원칙: UPPERCASE_SNAKE_CASE**

```bash
# ✅
GEMINI_API_KEY=
DATABASE_URL=
COMPANY_ID=demo-co
PROJECT_ID=proj-01
LOG_LEVEL=INFO
ENABLE_WRITE_BACK=false

# ❌
gemini_api_key           (소문자)
GEMINIKEY                (연결, 약자)
API_KEY_GEMINI           (순서 이상)
database.url             (점 사용)
```

---

## 7. 주석 및 문서 네이밍

### 7-1. 파일 헤더 주석

```python
"""OntologyService v3.0 — 온톨로지 CRUD 및 쿼리 지원.

v3.0 변경사항:
  - find_by_name: 한글 토큰 기반 매칭 (SequenceMatcher → regex)
  - write_back: (향후) 액션 시 changelog 자동 생성

Responsibilities:
  - 온톨로지 엔티티 저장/조회
  - 다중 속성 필터링
  - 관계(Link) 모델 생성

Related:
  - OntologyRepository: 저장소 추상화
  - QueryPlannerService: 쿼리 의도 분류
"""
```

### 7-2. 섹션 주석

```python
# ── 온톨로지 조회 ──────────────────────────────────────
def find_by_name(self, ...):
    pass

def filter_by_property(self, ...):
    pass

# ── 온톨로지 수정 ──────────────────────────────────────
def upsert_entity(self, ...):
    pass

def delete_entity(self, ...):
    pass
```

### 7-3. 문서 파일명

```
✅ 좋은 예:
  README.md
  ARCHITECTURE.md
  NAMING_CONVENTION.md
  ROADMAP.md
  API_REFERENCE.md
  DEPLOYMENT.md

❌ 나쁜 예:
  readme.txt              # 소문자, 확장자
  architecture_doc.md     # _doc 불필요
  notes.md                # 일반적
  TODO.md (한시적이면 괜찮음)
```

---

## 8. 도메인별 폴더 구조 템플릿

```
당신의 새로운 도메인을 추가할 때:

storage/{company}/{project}/ontology/{domain}/
├── entities.json          # 인스턴스
├── schema.json            # (선택) 도메인 고유 스키마
└── README.md              # 도메인 설명

README.md 템플릿:
---
# {Domain Name} Ontology

## 개요
설명

## 엔티티 타입
- TYPE_A: 설명
- TYPE_B: 설명

## 관계
- TYPE_A --RELATION--> TYPE_B

## 액션 (Phase 3)
- Approve
- Reject
- ...

## 예시 쿼리
- "..."
- "..."
```

---

## 9. 자동 검증 (Linting & Formatting)

### 9-1. Python

```bash
# pyproject.toml에 설정
[tool.black]
line-length = 100

[tool.isort]
profile = "black"

[tool.pylint]
max-line-length = 100
```

### 9-2. JSON

```bash
# .prettierrc
{
  "printWidth": 100,
  "useTabs": false,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

### 9-3. SQL (향후)

```bash
# .sqlfluff
[sqlfluff:layout:type:comma]
spacing_before = touch
spacing_after = touch

[sqlfluff:rules:L014]
capitalisation_policy = lower
```

---

## 10. 체크리스트 (Code Review Checklist)

PR 머지 전에 다음을 확인:

- [ ] 파일명이 `{domain}-{version}.json` 형식인가?
- [ ] Python 함수/변수가 snake_case인가?
- [ ] 엔티티 타입이 UPPERCASE인가?
- [ ] JSON 속성이 snake_case인가?
- [ ] 폴더가 도메인별로 정리되어 있는가?
- [ ] 환경 변수가 UPPERCASE_SNAKE_CASE인가?
- [ ] 파일/함수에 주석(헤더, 섹션)이 있는가?

---

## 11. 마이그레이션 (기존 코드 정리)

### 현재 (정리 전)
```
✗ entities.json (도메인 불명확)
✗ find_entity (camelCase)
✗ property_key, property_value (너무 generic)
```

### 목표 (정리 후)
```
✓ ai-voucher-2025.json
✓ find_by_name, find_by_property
✓ entity_type, property_name (명확)
```

### 작업 계획
```
Week 1: 신규 파일은 컨벤션 준수 (엄격)
Week 2-3: 기존 파일 이름 변경 (ci/cd 테스트 포함)
Week 4: 리팩토링 (함수명, 변수명)
```

---

## 정리

**핵심 원칙 3가지:**

1. **명확성 (Clarity)** — 파일명/함수명만 봐도 목적 파악 가능
2. **일관성 (Consistency)** — 모든 곳에서 동일한 패턴
3. **확장성 (Scalability)** — 6개월 후에도 이해 가능하게

**Golden Rule:**
> 당신이 3개월 후 이 코드를 읽을 때 "이게 뭐지?" 하지 않아야 한다.
