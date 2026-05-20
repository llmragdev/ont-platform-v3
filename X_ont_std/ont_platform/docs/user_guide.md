# ont_platform v2.0 — 사용자 가이드

> **대상**: 시스템 관리자 / 업무 운영자  
> **버전**: v2.0  
> **경로**: `E:\ontology_edu\ont_platform\v2\`  
> **기준일**: 2026-05-14 (폴더 구조 v2/v3 분리)

---

## 1. 개요

ont_platform v2.0은 **멀티테넌트 온톨로지 기반 의사결정 지원 시스템**입니다.  
문서(PDF)를 업로드하고 엔티티·관계를 추출하여, AI 질의 및 워크플로우 승인 자동화를 지원합니다.

### 핵심 기능

| 기능 | 설명 |
|------|------|
| 온톨로지 관리 | 엔티티·관계 CRUD, 도메인 스키마 확장 |
| 문서 관리 | PDF 업로드, 벡터 검색(Chroma) 연동 |
| AI 질의 (Hybrid Ask) | 필터 / 설명형 질의 자동 분류·응답 |
| 워크플로우 승인 | 역할 기반 상태 전이 (Submitted → Approved → Fulfilled → Closed) |
| 멀티테넌트 | Company / Project 단위 물리 격리 |

---

## 2. 빠른 시작

### 2.1 백엔드 실행

PowerShell에서 실행합니다.

```powershell
# conda 환경 활성화
conda activate claud_be

# 백엔드 실행
cd "e:\ontology_edu\ont_platform\v2\src\backend"
uvicorn app.main:app --reload --port 8000
```

접속 확인: `http://localhost:8000/api/health` → `{"status":"ok","version":"2.0.0"}`

### 2.2 프론트엔드 실행

프론트엔드는 전용 conda 환경 `claud_fe`(Node.js)를 사용합니다.

**최초 1회 — 환경 생성:**

```powershell
conda create -n claud_fe nodejs=20 -c conda-forge -y
conda activate claud_fe
cd "e:\ontology_edu\ont_platform\v2\src\frontend"
npm install
```

**이후 실행:**

```powershell
conda activate claud_fe
cd "e:\ontology_edu\ont_platform\v2\src\frontend"
npm run dev   # → http://localhost:3000
```

> **참고**: 백엔드(`localhost:8000`)가 먼저 실행 중이어야 LIVE 모드로 연결됩니다.  
> 백엔드 없이 실행하면 자동으로 DEMO 모드(목업 데이터)로 전환됩니다.

프론트엔드는 `/api/*` 요청을 `localhost:8000`으로 자동 프록시합니다.

---

## 3. 멀티테넌트 구조

### 3.1 헤더 기반 테넌트 컨텍스트

모든 API 요청에 아래 HTTP 헤더를 포함해야 합니다:

| 헤더 | 설명 | 예시 |
|------|------|------|
| `x-user-id` | 사용자 ID | `user-alice` |
| `x-company-id` | 회사 식별자 | `acme-corp` |
| `x-project-id` | 프로젝트 식별자 | `proj-2026` |
| `x-role` | 사용자 역할 | `Admin` |

### 3.2 역할(Role) 정의

| 역할 | 권한 |
|------|------|
| `Admin` | 모든 액션 + 워크플로우 그래프 삭제 |
| `FinanceManager` | ApproveOrder, RejectOrder, FulfillOrder, CloseOrder |
| `AccountManager` | RejectOrder, HoldOrder |
| `Viewer` | 조회만 가능 (액션 없음) |

### 3.3 물리 격리 경로

```
storage/
  {company_id}/
    {project_id}/
      ontology/          ← 엔티티·관계 JSON
      documents/         ← 문서 메타데이터
      vectors/           ← Chroma 벡터 샤드
      workflow_graphs.json
```

---

## 4. API 레퍼런스

### 4.1 헬스체크

```
GET /api/health
→ {"status": "ok", "version": "2.0.0"}
```

### 4.2 문서 관리

```
POST   /api/documents/upload          PDF 업로드
GET    /api/documents                 문서 목록
DELETE /api/documents/{doc_id}        문서 삭제
```

**문서 업로드 예시 (curl):**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "x-user-id: user1" \
  -H "x-company-id: acme" \
  -H "x-project-id: proj1" \
  -H "x-role: Admin" \
  -F "file=@contract.pdf"
```

### 4.3 온톨로지 (엔티티·관계)

```
GET    /api/ontology                            문서 목록 (엔티티 수 포함)
GET    /api/ontology/schema                     도메인 스키마 조회
GET    /api/ontology/{doc_id}/entities          엔티티 목록
POST   /api/ontology/{doc_id}/entities          엔티티 생성
PUT    /api/ontology/{doc_id}/entities/{id}     엔티티 수정
DELETE /api/ontology/{doc_id}/entities/{id}     엔티티 삭제
GET    /api/ontology/{doc_id}/relationships     관계 목록
POST   /api/ontology/{doc_id}/relationships     관계 생성
DELETE /api/ontology/{doc_id}/relationships/{id} 관계 삭제
GET    /api/ontology/{doc_id}/graph             React Flow 그래프 데이터
```

**엔티티 생성 예시:**
```bash
curl -X POST http://localhost:8000/api/ontology/doc-001/entities \
  -H "Content-Type: application/json" \
  -H "x-user-id: user1" -H "x-company-id: acme" \
  -H "x-project-id: proj1" -H "x-role: Admin" \
  -d '{"name": "Order O001", "type": "Order", "status": "Submitted",
       "properties": {"customerId": "C001", "amount": 3200}}'
```

### 4.4 AI 질의 (Hybrid Ask)

```
POST /api/hybrid/ask
```

**요청:**
```json
{
  "question": "Submitted 상태인 Order를 찾아줘",
  "doc_ids": null,
  "override": null
}
```

**응답 예시 (filter 유형):**
```json
{
  "query_type": "filter",
  "classification": {
    "type": "filter",
    "entity_type": "Order",
    "property_key": "status",
    "property_value": "Submitted"
  },
  "sources": [{"source_type": "ontology", "citation": "ontology:demo-orders:E001"}],
  "structured_data": {"ontology": {"count": 1, "items": []}},
  "evidence": [{"citation": "ontology:demo-orders:E001"}],
  "trace": ["planner: generated query plan", "ontology.filter: matched 1 item(s)"]
}
```

**지원 질의 유형:**

| 유형 | 예시 질문 | 처리 |
|------|-----------|------|
| `filter` | "승인된 주문 찾아줘", "status가 Approved인 Order" | 속성 기반 필터링 |
| `descriptive` | "Order가 뭐야?", "온톨로지 설명해줘" | 벡터 검색 |
| `hybrid` | "하이브리드로 status: Approved 찾아줘" | 온톨로지 + 벡터 결과 합성 |

### 4.5 워크플로우

```
GET  /api/workflow/queue              역할 기반 액션 가능 엔티티 목록
POST /api/workflow/execute            상태 전이 실행
```

**queue 응답 예시:**
```json
{
  "count": 2,
  "items": [
    {
      "id": "E001",
      "name": "Order O001",
      "type": "Order",
      "status": "Submitted",
      "available_actions": ["ApproveOrder", "RejectOrder", "HoldOrder"],
      "doc_id": "demo-orders",
      "properties": {"customerId": "C001", "amount": 3200}
    }
  ]
}
```

**execute 요청:**
```json
{"doc_id": "demo-orders", "entity_id": "E001", "action": "ApproveOrder"}
```

**워크플로우 상태 전이:**
```
Submitted ──ApproveOrder──→ Approved ──FulfillOrder──→ Fulfilled ──CloseOrder──→ Closed
         ──HoldOrder──→ Review ──ApproveOrder──→ Approved
         ──RejectOrder──→ Rejected (종료)
```

### 4.6 워크플로우 그래프 (DAG)

```
GET    /api/workflow-graphs              그래프 목록
GET    /api/workflow-graphs/{id}         그래프 단건 조회
POST   /api/workflow-graphs              그래프 생성/수정
DELETE /api/workflow-graphs/{id}         그래프 삭제 (Admin 전용)
```

---

## 5. 도메인 확장

### 5.1 새 엔티티 타입 추가

`ont_platform/v2/src/backend/app/config/domain.json` 편집:

```json
{
  "entity_types": [
    {"name": "Order", "description": "주문", "properties": ["status", "customerId", "amount"]},
    {"name": "Contract", "description": "계약", "properties": ["value", "startDate", "endDate"]}
  ],
  "relation_types": [
    {"name": "BELONGS_TO", "description": "소속 관계"}
  ]
}
```

코드 변경 없이 신규 타입이 즉시 적용됩니다.

### 5.2 워크플로우 전이 규칙 변경

`ont_platform/v2/src/backend/app/config/workflow.json` 편집:

```json
{
  "object_type": "Contract",
  "actions": {
    "SignContract": {
      "from_statuses": ["Draft"],
      "to_status": "Active",
      "allowed_roles": ["Admin", "LegalManager"]
    },
    "TerminateContract": {
      "from_statuses": ["Active"],
      "to_status": "Terminated",
      "allowed_roles": ["Admin"]
    }
  }
}
```

서버 재시작 없이 JSON만 수정하면 워크플로우 규칙이 변경됩니다.

---

## 6. 프론트엔드 설정

### 6.1 테넌트 설정 변경

`ont_platform/v2/src/frontend/src/lib/api.ts`의 `DEFAULT_TENANT`를 수정:

```typescript
export const DEFAULT_TENANT = {
  userId: "alice",
  companyId: "acme-corp",
  projectId: "proj-2026",
  role: "FinanceManager",
};
```

### 6.2 백엔드 URL 변경

기본값은 `localhost:8000`입니다. 다른 서버를 사용하려면 `ont_platform/v2/src/frontend/next.config.mjs` 수정:

```js
destination: "http://your-backend-server:8000/api/:path*",
```

---

## 7. 운영 FAQ

**Q: 백엔드가 꺼져도 프론트엔드가 동작하나요?**  
A: 네. 백엔드 미연결 시 자동으로 DEMO 모드로 전환되어 목업 데이터를 표시합니다.

**Q: 데이터는 어디에 저장되나요?**  
A: `ont_platform/v2/storage/{company_id}/{project_id}/` 디렉터리에 JSON 파일로 저장됩니다. 별도 데이터베이스가 필요 없습니다.

**Q: 새 프로젝트를 추가하려면?**  
A: 다른 `x-project-id` 헤더 값을 사용하면 됩니다. 디렉터리가 자동 생성됩니다.

**Q: AI 질의가 LLM을 사용하나요?**  
A: v2.0 기준으로 키워드 휴리스틱 분류기를 사용합니다. LLM 연동은 Sprint 08+에서 추가될 예정입니다.

**Q: 벡터 검색(RAG)이 작동하려면?**  
A: Chroma와 임베딩 모델이 필요합니다. `GET /api/search`로 테스트하세요.

---

## 8. 테스트 실행

```bash
conda activate claud_be
cd ont_platform/v2/src/backend

# 전체 테스트 (86개)
python -m pytest tests/ -v

# 스프린트별 실행
python -m pytest tests/test_sprint07_1_dod.py -v  # Sprint 07-1 (39개)
python -m pytest tests/test_sprint07_2_dod.py -v  # Sprint 07-2 (14개)
python -m pytest tests/test_sprint07_3_dod.py -v  # Sprint 07-3 (23개)
```

---

## 9. 아키텍처 다이어그램

```
프론트엔드 (Next.js 14)
  ont_platform/v2/src/frontend/src/
    lib/api.ts          ← API 클라이언트 (테넌트 헤더 자동 첨부)
    app/page.tsx        ← 단일 페이지 앱

        ↕ HTTP (프록시: localhost:3000/api/* → localhost:8000/api/*)

백엔드 (FastAPI)
  app/
    main.py             ← 라우터 등록, CORS 설정
    api/
      hybrid.py         ← POST /api/hybrid/ask
      workflow.py       ← GET /api/workflow/queue, POST /api/workflow/execute
    services/
      ontology.py       ← 엔티티·관계 CRUD + fuzzy 검색
      document.py       ← PDF 업로드·목록
      query_planner.py  ← 질의 유형 분류 (filter/descriptive)
      workflow.py       ← WorkflowService + WorkflowGraphService
      vector_search.py  ← Chroma 벡터 검색
    config/
      workflow.json     ← 상태 전이 규칙 (편집 가능)
      domain.json       ← 엔티티 타입 정의 (편집 가능)

  storage/
    {company_id}/{project_id}/
      ontology/         ← *.json (엔티티·관계)
      workflow_graphs.json
```

---

*Sprint 07 + Phase 3~5 완료 기준 (86/86 테스트 통과) — Sprint 08+ 운영 준비 예정*
