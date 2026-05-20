# 04. 운영 표준 (Deployment & Operation Standard)

이 문서는 엔터프라이즈 AI Agent/RAG 플랫폼이 실제 서비스 환경(Production)에서 안정적으로 동작하고, 데이터의 신뢰성을 보장하며, 문제 발생 시 추적 및 복구가 가능하도록 하기 위한 운영 아키텍처 표준을 정의합니다.

단순한 기능 구현(MVP)을 넘어, 멀티 테넌트 환경에서의 **보안, 감사 추적(Audit), 워크플로우 상태 관리, 그리고 Human-in-the-loop 기반의 데이터 품질 통제**를 핵심 목표로 합니다.

---

## 1. 테넌트 및 권한 관리 (Tenant & Permission)

엔터프라이즈 환경에서는 데이터 격리와 권한 통제가 필수적입니다.

### 1.1 데이터 격리 (Data Isolation)
*   **논리적 격리**: 모든 DB 테이블 및 Vector/Ontology 저장소에는 반드시 `tenant_id` (또는 `company_id`)가 포함되어야 합니다.
*   **API 계층 통제**: 모든 API 요청은 인증 토큰(JWT 등)을 통해 테넌트를 식별하고, 해당 테넌트 범위를 벗어나는 데이터 접근을 원천 차단(Interceptor/Middleware 레벨)해야 합니다.

### 1.2 역할 기반 접근 제어 (RBAC)
*   **Role 정의**: 최소 권한의 원칙에 따라 사용자 역할을 구분합니다. (예: `System Admin`, `Tenant Admin`, `Knowledge Manager`, `General User`)
*   **리소스 권한**: 특정 워크플로우 노드(예: 외부 시스템 API 호출 노드)나 온톨로지 스키마 수정은 특정 권한(예: `Knowledge Manager` 이상)을 가진 사용자만 실행할 수 있도록 통제해야 합니다.

---

## 2. 감시 및 추적성 (Observability & Audit)

AI 시스템의 특성상 내부 판단 로직(LLM)이 블랙박스처럼 동작할 수 있으므로, 입력과 출력 그리고 시스템 상태에 대한 완벽한 추적성이 요구됩니다.

### 2.1 감사 로그 (Audit Trail)
누가, 언제, 어떤 데이터에 접근하거나 변경했는지 영구적으로 기록해야 합니다.
*   **필수 기록 대상**: 온톨로지(스키마 및 인스턴스) 변경, 프롬프트 변경, 워크플로우 승인 내역, 시스템 설정 변경.
*   **저장 포맷**: 이벤트 타입, 타임스탬프, 사용자 ID, IP, 대상 리소스 ID, 변경 전/후 상태(Diff) 포함.

### 2.2 LLM 텔레메트리 (Telemetry)
*   **실행 추적(Trace)**: 사용자의 최초 질의부터 Query Plan 생성, Vector 검색 결과, LLM 응답 생성까지의 전체 Chain 과정을 Trace ID로 묶어 로깅해야 합니다.
*   **비용 및 성능 지표**: API 호출 횟수, 토큰 사용량(입력/출력), P50/P95 응답 지연 시간(Latency)을 모니터링 대시보드와 연동합니다.

---

## 3. 워크플로우 상태 관리 (Workflow Run Management)

단순한 순차적 파이프라인을 넘어, 예외 상황에 대비한 견고한 상태 관리(State Machine) 모델이 필요합니다.

### 3.1 실행 상태 (Run State)
워크플로우와 각 단계(Step)는 명확한 상태값을 가져야 합니다.
*   **상태 정의**: `PENDING` (대기), `RUNNING` (실행 중), `SUCCEEDED` (성공), `FAILED` (실패), `WAITING_APPROVAL` (승인 대기), `CANCELLED` (취소).

### 3.2 복구 및 재시도 (Resilience)
*   **Retry Policy**: 일시적인 오류(네트워크 타임아웃, LLM API Rate Limit) 발생 시, 지수 백오프(Exponential Backoff) 방식으로 자동 재시도해야 합니다.
*   **Idempotency (멱등성)**: 워크플로우가 실패하여 재실행되더라도, 중복 데이터가 생성되지 않도록 멱등키(Idempotency Key)를 활용해야 합니다.
*   **Fallback**: LLM 응답 실패 시 사용자에게 노출할 안전한 기본 응답(Fallback Message) 규격을 정의해야 합니다.

---

## 4. 데이터 신뢰성 및 Human-in-the-Loop (HITL)

AI가 추출한 지식(Ontology)은 곧바로 프로덕션 데이터로 사용되지 않고 반드시 검증 단계를 거쳐야 합니다.

### 4.1 온톨로지 출처 (Provenance)
지식 그래프의 모든 노드와 엣지는 출처가 명확해야 합니다.
*   **필수 메타데이터**: `source_doc_id` (원본 문서), `source_chunk_id` (해당 단락), `confidence_score` (LLM 확신도), `extracted_by` (추출 모델/버전).

### 4.2 승인 워크플로우 (Approval Flow)
*   LLM에 의해 자동 추출된 지식은 초기 상태를 `REVIEW_REQUIRED` (검토 필요)로 지정합니다.
*   도메인 전문가(Knowledge Manager)가 근거(Evidence)를 확인한 후 `APPROVED` (승인) 상태로 변경해야만, 실제 하이브리드 검색의 대상이 됩니다.
*   엔티티 병합(Merge) 및 중복 제거(Deduplication) 작업 또한 관리자의 승인 이력을 남겨야 합니다.

---

## 5. 보안 및 가드레일 (Security & Guardrails)

생성형 AI 플랫폼의 취약점을 방어하기 위한 실행 전/후 검증 표준입니다.

### 5.1 Query Plan 검증 (Validator)
LLM이 생성한 '질의 계획(Query Plan)'은 실행 전(DB/Vector 접근 전)에 반드시 룰 기반(Rule-based) 검증기를 통과해야 합니다.
*   존재하지 않는 Entity Type 또는 속성(Property) 접근 차단.
*   사용자 권한 범위를 벗어나는 `doc_id` 또는 테넌트 필터 누락 차단.
*   과도한 비용이 예상되는 대규모 조회 쿼리(Query Cost Limit) 차단.

### 5.2 입출력 가드레일 (I/O Guardrails)
*   **프롬프트 인젝션 방어**: 사용자 입력 텍스트 내 악의적인 명령(예: "이전 지시 무시")을 사전에 필터링합니다.
*   **개인정보 마스킹 (PII)**: 시스템 내부로 들어오기 전(Ingestion)과 사용자에게 응답하기 전(Generation)에 민감 정보(주민번호, 이메일 등)를 마스킹 처리합니다.

---

## 6. 품질 평가 (Evaluation)

시스템이 프로덕션 환경에 배포되기 전, 그리고 주기적으로 RAG 품질을 평가하는 체계입니다.

*   **고정 평가셋 (Ground Truth Dataset)**: 다양한 질의 유형(단순 검색, 조건 검색, 비교, 요약 등)에 대한 고정된 질문-정답(QnA) 쌍을 최소 100개 이상 유지합니다.
*   **핵심 측정 지표**:
    *   **Retrieval Precision/Recall**: 검색된 문서가 질문과 얼마나 관련이 있는지.
    *   **Answer Faithfulness (충실도)**: LLM의 답변이 검색된 컨텍스트(문서/온톨로지)에만 기반하고 있는지 (환각 탐지).
    *   **Citation Coverage**: 답변 내용 중 몇 %가 실제 출처(근거)를 참조하고 있는지.
    *   **No-Answer Rate**: 모르는 질문에 대해 지어내지 않고 "모른다"고 올바르게 답변한 비율.
