# 온톨로지 · 워크플로우 · 팔란티어 비교 분석

작성일: 2026-05-14  
대상 시스템: ont_platform v3.0

---

## 1. 온톨로지와 워크플로우의 관계

### 역할 분담

```
온톨로지 = "무엇이 존재하는가"          워크플로우 = "어떻게 처리되는가"
─────────────────────────────────────────────────────────────────
엔티티: Order, Product, Employee       상태 전이: Submitted → Approved
속성:   금액, 날짜, 담당자              액션:     ApproveOrder, RejectOrder
관계:   Order → Product (포함)         권한:     FinanceManager만 승인 가능
```

### 구조적 연결

워크플로우는 온톨로지를 두 가지 방향으로 사용한다.

**읽기** — 워크플로우 큐 조회 시 온톨로지에서 상태를 읽는다.
```python
# workflow.py
def queue(self, ctx):
    entities = self.ontology_svc.list_all_entities(ctx)
    # status=Submitted인 엔티티만 큐에 표시
```

**쓰기** — 워크플로우 액션 실행 시 온톨로지 상태를 변경한다.
```python
def execute(self, ctx, doc_id, entity_id, action_name):
    entity["status"] = transition["to"]
    self.ontology_svc.upsert_entity(doc_id, entity, ctx)
```

> **결론**: 온톨로지가 상태의 저장소이고, 워크플로우는 그 상태를 바꾸는 규칙 엔진이다.  
> 온톨로지 없이 워크플로우는 작동하지 않으며, 워크플로우 없이 온톨로지의 상태는 변하지 않는다.

---

## 2. 시나리오: 구매 주문 승인

**등장인물**: 구매담당자 Kim, 재무팀장 Lee

### ont_platform v3.0 흐름

```
1. Kim이 온톨로지에 엔티티 등록
   → POST /api/ontology/doc-001/entities
   {
     "type": "ORDER",
     "name": "노트북 50대 구매",
     "properties": { "amount": 5000000, "vendor": "삼성" },
     "status": "Submitted"
   }

2. Lee가 대시보드 접속 → 워크플로우 큐 조회
   → GET /api/workflow/queue
   "Submitted 상태인 ORDER 엔티티 목록"
   → [{ id: "ent-001", name: "노트북 50대 구매", amount: 5000000 }]

3. Lee가 AI에 질의: "이 업체 납품 이력 있어?"
   → POST /api/hybrid/ask { "question": "삼성 납품 이력" }
   → LLM이 온톨로지(ORDER 엔티티) + RAG(계약서 PDF) 동시 검색
   → "삼성전자는 2024년 3건 납품, 평균 납기 준수율 98%"

4. Lee가 승인
   → POST /api/workflow/execute
   { "entity_id": "ent-001", "action": "ApproveOrder" }
   → 온톨로지의 status: "Submitted" → "Approved" 로 변경
   → 감사 로그 자동 기록
```

### 팔란티어였다면

```
1. 온톨로지 스키마 자체에 이미 Action이 정의되어 있음
   Object Type: PurchaseOrder
     properties: amount, vendor, status
     Action: ApprovePurchaseOrder
       → status를 Approved로 변경
       → 회계 시스템에 자동 연동
       → 슬랙 알림 자동 발송

2. AIP 에이전트가 자동으로
   "삼성 납품 이력" + "현재 예산 잔액" + "유사 주문 승인 패턴"을
   온톨로지 컨텍스트로 자동 파악 후 Lee에게 추천

3. Lee가 "승인" 클릭 한 번
   → 온톨로지 상태 변경 + 회계 ERP 반영 + 알림 + 감사로그
      모두 Action 하나로 트랜잭션 처리
```

---

## 3. 팔란티어와의 비교

### 개념 구조 차이

팔란티어(Foundry/AIP)에서 온톨로지는 단순 데이터 모델이 아니라  
**비즈니스 운영 전체를 연결하는 단일 진실 공급원(Single Source of Truth)**이다.

```
팔란티어 온톨로지
  ├── Object Type  (우리 엔티티에 해당)
  ├── Link Type    (우리 관계에 해당)
  ├── Action       (우리 워크플로우 액션에 해당) ← 핵심 차이
  └── Function     (Python/TypeScript로 실시간 연산)
```

팔란티어에서는 **Action이 온톨로지 내부**에 정의된다.  
"ApproveOrder"라는 액션 자체가 온톨로지 스키마의 일부다.

### 항목별 비교표

| 항목 | ont_platform v3.0 | 팔란티어 |
|------|-------------------|---------|
| **온톨로지 범위** | 엔티티·관계·속성 (데이터 모델) | 엔티티·관계·속성 + 액션·함수까지 포함 |
| **워크플로우 위치** | 온톨로지와 별도 서비스 (`workflow.json`) | 온톨로지 스키마 안에 정의 |
| **상태 변경 방식** | 워크플로우가 온톨로지 JSON을 직접 수정 | Action이 온톨로지 Object를 트랜잭션으로 수정 |
| **AI 연동** | LLM이 온톨로지+RAG를 쿼리 시점에 결합 | AIP가 온톨로지를 컨텍스트로 에이전트 실행 |
| **저장소** | JSON 파일 (v3) → DB 예정 (v4) | 분산 데이터 플랫폼 (Spark, 실시간 스트림) |
| **권한 모델** | role 기반 헤더 | Object 단위 세밀한 ACL |
| **타 시스템 연동** | 개발자가 별도 API 호출 작성 | Action 정의에 연동 선언으로 자동 처리 |
| **감사 추적** | 별도 audit 서비스 | Object 변경 이력 자동 기록 |
| **규모** | 단일 서버, 수천 엔티티 | 수십억 Object, 엔터프라이즈 전사 |

### 상황별 차이

| 상황 | ont_platform | 팔란티어 |
|------|-------------|---------|
| 승인 후 회계 연동 | 개발자가 별도 코드 작성 | Action에 연동 로직 선언으로 끝 |
| AI 추천 컨텍스트 | 질의할 때만 결합 | 온톨로지 자체가 항상 컨텍스트 |
| 감사 추적 | 별도 audit 서비스 | Object 변경 이력 자동 기록 |
| 타 시스템 반영 | 수동 API 호출 | Object 변경 → 파이프라인 자동 트리거 |

---

## 4. 핵심 철학 차이

**ont_platform**
> "사람이 판단하고, 시스템이 상태를 기록한다"  
> 온톨로지 = 데이터 모델 / 워크플로우 = 운영 로직 (분리)

**팔란티어**
> "시스템이 컨텍스트를 제공하고, 사람이 결정하면, 연결된 모든 것이 자동으로 반응한다"  
> 온톨로지 = 데이터 + 로직 + 액션 + AI 컨텍스트 (통합)

---

## 5. ont_platform을 팔란티어 방향으로 발전시키려면 (v4 목표)

| 항목 | 현재 (v3) | 목표 (v4) |
|------|----------|---------|
| Action 위치 | `workflow.json` 별도 파일 | 온톨로지 스키마 안으로 이동 |
| 상태 변경 | JSON 직접 수정 | 온톨로지 트랜잭션 (원자성 보장) |
| AI 컨텍스트 | 쿼리 시점 결합 | 온톨로지 스키마 자동 인식 |
| 저장소 | JSON 파일 | SQLite → PostgreSQL |
| 외부 연동 | 없음 | Action에 webhook/이벤트 선언 |

> ont_platform은 팔란티어의 핵심 개념을 학습하고 검증하는 축소 모델로 설계됐다.  
> 개념 구조는 동일하며, 규모와 통합 깊이에서 차이가 난다.
