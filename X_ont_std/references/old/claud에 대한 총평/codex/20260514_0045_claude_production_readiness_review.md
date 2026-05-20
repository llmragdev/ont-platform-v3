# Claude Production Readiness Review

작성일: 2026-05-14 00:45 KST  
작성자: Codex  
대상: `E:\ontology_edu\claud_v1_legacy`

## 1. 결론
Claude 쪽 구현과 문서는 교육/시연용 고급 MVP로는 상당히 잘 구성되어 있습니다. 하이브리드 질의, 온톨로지 관리, workflow graph, 권한, 감사, telemetry 등 production으로 발전할 수 있는 핵심 골격을 갖추고 있습니다.

다만 현재 상태를 production 수준의 workflow와 온톨로지 완성도라고 보기는 어렵습니다. 운영형 제품으로 판단하려면 데이터 모델의 신뢰성, 온톨로지 품질 관리, 장기 실행 workflow 복구성, 질의 품질 평가, 버전 관리, 감사 추적성이 더 필요합니다.

요약하면 다음과 같습니다.

```text
현재 수준: 교육/시연용 고급 MVP + 운영형 골격
목표 수준: production-ready 업무 AI/RAG/ontology/workflow platform
필요 작업: Query Plan, Ontology Provenance, Workflow Run State, Evaluation, Versioning
```

## 2. 현재 갖춘 기반

### 2.1 Hybrid Query
Claude 구현에는 `ask_hybrid()` 흐름이 존재합니다.

* 질문 유형 분류
* 구조형 질의 실행
* descriptive/hybrid 유형의 Vector Search 실행
* 최종 LLM 답변 합성
* 감사 로그 기록

관련 구현:
* `backend/app/app_context.py`
* `backend/app/query_classifier.py`
* `backend/app/ontology_query_engine.py`
* `backend/app/ontology_extractor.py`
* `backend/app/ontology_store.py`

### 2.2 Ontology
온톨로지 스키마를 Python 코드에 고정하지 않고 JSON 설정으로 분리하려는 방향은 좋습니다.

갖춘 기반:
* 객체 타입, 관계 타입, 액션 타입 외부화
* 관계 추가/삭제 API
* graph 형태 조회
* object context 조회
* ontology management UI 방향성

관련 구현:
* `backend/app/config/ontology.default.json`
* `backend/app/ontology.py`
* `backend/app/ontology_store.py`

### 2.3 Workflow
workflow graph 관련 엔진과 서비스가 존재합니다.

갖춘 기반:
* workflow graph CRUD
* graph run 실행
* node type별 권한 정책
* audit event 기록
* 일부 테스트 기록

관련 구현:
* `backend/app/workflow.py`
* `backend/app/workflow_graph.py`
* `backend/app/workflow_graph_engine.py`

### 2.4 Tenant, Permission, Audit
멀티테넌트와 권한 관리도 MVP 수준의 뼈대가 있습니다.

갖춘 기반:
* tenant user/company/project config
* role default permissions
* API permission dependency
* company isolation check
* audit service

관련 구현:
* `backend/app/tenant.py`
* `backend/app/audit.py`
* `backend/app/config/users.json`
* `backend/app/config/role_defaults.json`
* `backend/app/config/projects.json`

### 2.5 Test and Sprint Records
문서상으로 Sprint 04에서 하이브리드 질의 테스트 45건, Sprint 06에서 멀티테넌트/권한 DoD 검증 기록이 있습니다. 이는 단순 설계서보다 신뢰도가 높은 부분입니다.

다만 일부 통합 테스트는 "실 서버 실행 후 수치 업데이트 필요"로 남아 있어, 모든 테스트가 production gate 수준으로 자동화된 상태는 아닙니다.

## 3. Production 기준 미흡 사항

### 3.1 Query Classification만으로는 부족
현재 설계는 질문을 `descriptive`, `filter`, `compare`, `calculate`, `hybrid`로 나누는 방식입니다. 하지만 production에서는 라벨만으로는 실행 안정성이 부족합니다.

필요한 것은 실행 가능한 Query Plan입니다.

```json
{
  "query_type": "hybrid",
  "ontology_filters": [
    {
      "entity_type": "PRODUCT",
      "property": "billing_model",
      "operator": "eq",
      "value": "Serverless"
    }
  ],
  "needs_vector": true,
  "doc_ids": ["doc-001"],
  "top_k": 5
}
```

LLM은 질의 계획만 만들고, 실제 실행은 검증된 executor가 담당해야 합니다.

### 3.2 Ontology Provenance 부족
운영형 온톨로지는 단순 엔티티/관계 저장만으로 부족합니다. 각 엔티티와 관계가 어디에서 왔고, 누가 승인했고, 어떤 버전에서 변경되었는지가 필요합니다.

필요 필드:
* `source_doc_id`
* `source_page`
* `source_chunk_id`
* `source_text`
* `confidence`
* `created_by`
* `approved_by`
* `status`
* `version`
* `created_at`
* `updated_at`

### 3.3 Workflow Run State 부족
현재 workflow graph 실행 기반은 있지만, production workflow engine으로 보려면 장기 실행과 실패 복구 모델이 필요합니다.

필요 기능:
* run 상태 저장
* step별 상태 저장
* retry policy
* timeout policy
* idempotency key
* compensation action
* manual approval step
* pause/resume
* failed run replay
* run-level audit trace

### 3.4 Ontology Versioning 부족
스키마와 인스턴스가 변경될 때 기존 질의 결과, workflow, 추출 결과가 어떤 버전을 기준으로 만들어졌는지 추적해야 합니다.

필요 기능:
* ontology schema version
* entity version
* relationship version
* migration history
* backward compatibility policy
* deprecated type 관리

### 3.5 품질 평가 체계 부족
하이브리드 질의는 "동작한다"와 "정확하다"가 다릅니다. production에서는 품질 평가가 별도 체계로 있어야 합니다.

필요 지표:
* query type classification accuracy
* ontology evidence accuracy
* retrieval precision
* answer faithfulness
* citation coverage
* fallback rate
* no-answer rate
* latency p50/p95
* workflow success/failure rate

### 3.6 JSON 저장소의 운영 한계
JSON 파일 저장은 MVP에는 좋지만 production에는 한계가 있습니다.

리스크:
* 동시성 충돌
* 부분 쓰기 실패
* 대량 검색 성능
* 권한 감사 쿼리 어려움
* 백업/복구 복잡도
* schema migration 어려움

MVP에서는 JSON을 유지하더라도, RDBMS 승격 가능한 논리 모델을 명확히 정의해야 합니다.

## 4. Workflow 보강 제안

### 4.1 Workflow Run Model
아래 논리 모델을 추가하는 것을 권장합니다.

| 모델 | 설명 |
| :--- | :--- |
| `TB_WORKFLOW_DEF` | workflow graph 정의 |
| `TB_WORKFLOW_DEF_VERSION` | workflow 정의 버전 |
| `TB_WORKFLOW_RUN` | workflow 실행 인스턴스 |
| `TB_WORKFLOW_STEP_RUN` | node/step 실행 상태 |
| `TB_WORKFLOW_APPROVAL` | 수동 승인 이력 |
| `TB_WORKFLOW_EVENT` | 실행 중 발생한 이벤트 |

### 4.2 Step State
각 step은 최소한 아래 상태를 가져야 합니다.

```text
PENDING
RUNNING
SUCCEEDED
FAILED
SKIPPED
WAITING_APPROVAL
TIMEOUT
CANCELLED
RETRYING
```

### 4.3 Run Trace
workflow 실행 결과에는 사용자에게 보여줄 trace와 운영자가 볼 수 있는 technical trace를 분리해야 합니다.

* user trace: 어떤 업무 단계가 진행되었는지
* technical trace: node id, input, output, latency, error, retry count

### 4.4 Workflow Guardrail
production workflow는 실행 전에 검증해야 합니다.

검증 항목:
* cycle 여부
* node type 권한
* required input 존재 여부
* 위험 action 승인 필요 여부
* 외부 HTTP 호출 allowlist
* 예상 비용 또는 token limit

## 5. Ontology 보강 제안

### 5.1 Ontology Logical Model
아래 논리 모델을 표준화하는 것을 권장합니다.

| 모델 | 설명 |
| :--- | :--- |
| `TB_ONT_SCHEMA` | 온톨로지 스키마 메타 |
| `TB_ONT_ENTITY_TYPE` | 엔티티 타입 정의 |
| `TB_ONT_RELATION_TYPE` | 관계 타입 정의 |
| `TB_ONT_ENTITY` | 엔티티 인스턴스 |
| `TB_ONT_RELATION` | 관계 인스턴스 |
| `TB_ONT_PROVENANCE` | 출처와 근거 |
| `TB_ONT_CHANGE_LOG` | 변경 이력 |
| `TB_ONT_EXTRACT_TASK` | 추출 작업 상태 |

### 5.2 Entity Merge and Deduplication
LLM 추출은 중복 엔티티를 만들 가능성이 높습니다. 다음 기능이 필요합니다.

* exact match merge
* alias match
* fuzzy match
* human approval before merge
* merge history
* undo merge

### 5.3 Human-in-the-loop Approval
추출된 엔티티와 관계는 바로 production graph에 반영하지 말고, 상태를 나누는 편이 안전합니다.

```text
EXTRACTED
REVIEW_REQUIRED
APPROVED
REJECTED
DEPRECATED
```

### 5.4 Ontology Evidence
온톨로지 질의 결과에도 문서 근거와 같은 수준의 근거 구조가 필요합니다.

```json
{
  "evidence_no": 1,
  "node_id": "E001",
  "node_type": "PRODUCT",
  "label": "Snowpipe",
  "source_doc_id": "doc-001",
  "source_page": 7,
  "source_chunk_id": "chunk-001-007",
  "source_text": "Snowpipe is a serverless ingestion service.",
  "confidence": 0.91
}
```

## 6. RAG and Hybrid Query 보강 제안

### 6.1 Query Plan Validator
LLM이 만든 plan은 실행 전에 검증해야 합니다.

검증 항목:
* 존재하는 entity type인지
* 존재하는 property인지
* operator가 허용되는지
* 접근 가능한 `doc_ids`인지
* tenant/project 범위 안인지
* query cost가 제한 이내인지

### 6.2 Hybrid Response Standard
응답 모델은 문서 근거와 온톨로지 근거를 모두 포함해야 합니다.

```json
{
  "query_id": "query-001",
  "query_type": "hybrid",
  "query_plan": {},
  "answer": "답변 본문 [1]",
  "structured_data": {
    "headers": [],
    "rows": []
  },
  "source_documents": [],
  "ontology_evidence": [],
  "trace": [],
  "quality_metrics": {
    "confidence_score": 0.89,
    "citation_coverage": 1.0,
    "fallback_used": false
  }
}
```

### 6.3 Evaluation Dataset
production 전에는 질의 유형별 고정 평가셋이 필요합니다.

권장 구성:
* descriptive 20개
* filter 20개
* compare 20개
* calculate 20개
* hybrid 20개
* negative/no-answer 20개

### 6.4 RAG Quality Controls
현재 vector search와 ontology routing이 있어도 RAG 품질 제어는 더 필요합니다.

필요 기능:
* reranking
* citation validation
* no-context answer blocking
* source document freshness
* chunk provenance
* retrieval debug trace

## 7. 버전 관리 제안

### 7.1 평가 문서 파일명 규칙
평가와 제안 문서는 날짜와 시간을 prefix로 둡니다.

```text
YYYYMMDD_HHMM_topic.md
```

예시:

```text
20260514_0045_claude_production_readiness_review.md
20260514_0110_claude_ontology_workflow_gap_analysis.md
20260515_0930_claude_followup_review_after_patch.md
```

### 7.2 문서 내부 메타데이터
모든 평가 문서 상단에 다음 정보를 둡니다.

```text
작성일
작성자
대상 경로
대상 버전 또는 기준 commit
검토 범위
결론 요약
```

### 7.3 변경 이력 관리
같은 문서를 덮어쓰기보다 새 리뷰 문서를 추가하는 방식을 권장합니다. 이후 `README.md`에서 최신 리뷰, 이전 리뷰, 반영 상태를 인덱싱합니다.

## 8. 우선순위 로드맵

### 8.1 Phase 1: Production Readiness Baseline
* Query Plan schema 추가
* Query Plan validator 추가
* Hybrid response 표준화
* Ontology evidence 필드 추가
* workflow run/step state 모델 정의

### 8.2 Phase 2: Ontology Quality
* provenance 필드 추가
* 추출 결과 승인 플로우 추가
* entity merge/dedup 기능 추가
* ontology schema versioning 추가
* change log 추가

### 8.3 Phase 3: Workflow Reliability
* retry/timeout/idempotency 추가
* failed run replay 추가
* manual approval step 추가
* external action allowlist 추가
* workflow run dashboard 추가

### 8.4 Phase 4: Evaluation and Operations
* 질의 평가셋 구축
* hybrid quality dashboard 추가
* p50/p95 latency 추적
* fallback/no-answer/citation coverage 지표 추가
* CI에서 regression eval 실행

## 9. 최종 판단
Claude 구현은 방향이 좋고, 단순 데모를 넘어 운영형 플랫폼의 골격을 일부 갖추고 있습니다. 특히 온톨로지와 workflow를 RAG 옆에 둔 방향은 적절합니다.

하지만 production 수준이라고 부르려면 다음 세 가지가 반드시 보강되어야 합니다.

1. 실행 가능한 Query Plan과 validator
2. 출처, 승인, 버전이 있는 Ontology quality model
3. 실패 복구와 상태 추적이 가능한 Workflow run model

이 세 가지가 들어가면 Claude 구현은 교육용 MVP에서 production-oriented MVP로 올라갈 수 있습니다.
