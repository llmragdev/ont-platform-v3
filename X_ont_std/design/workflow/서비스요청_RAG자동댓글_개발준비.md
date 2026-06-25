# 서비스 요청 RAG 자동 댓글 워크플로우 개발 준비

## 1. 현재 확인 상태

- 웹 기동 가능: `http://127.0.0.1:3001`
- 백엔드 API 정상: `http://127.0.0.1:8001/api/health`
- 워크플로우 그래프 저작 가능
  - React Flow 기반 노드/엣지 편집
  - 그래프 저장/조회/삭제
  - SSE 기반 실행 결과 표시
- 저장된 샘플 그래프
  - `helpdesk2` (`wfg-089ea014778d`)

현재 실행 엔진은 노드 배열 순서대로 0.3초씩 성공 처리하는 목업이다.
서비스 요청 RAG 자동 댓글 시뮬레이션을 위해서는 노드 타입별 업무 의미와 분기 실행을 추가해야 한다.

## 2. 목표 업무 범위

대상 업무:

> 서비스 요청 중 산출물의 변경이 없는 업무 중 Agentic AI 적용이 가능한 업무 프로세스

주의:

- 구현은 특정 접수 시스템이나 고객사에 종속시키지 않는다.
- mock 서버는 문장형 요청/응답을 제공하는 외부 시스템으로 본다.
- 워크플로우 엔진은 "문장형 서비스 요청"을 입력으로 받아 범용적으로 분류, 판단, 실행, 이관한다.
- 예: "결재 후 비밀번호 초기화 해 주세요.", "VPN 접속이 안 됩니다.", "SAP 조회 권한 신청 방법을 알려주세요."

자동화 범위:

- 문장형 요청 접수
- 요청 유형 분류
- 산출물 변경 여부 판단
- FAQ/규정/RAG 조회
- 자동 답변 초안 생성
- 승인 필요 여부 판단
- 선행 조건 판단
  - 예: 결재 후 처리, 승인 후 처리, 담당자 확인 후 처리
- 담당자 이관 판단
- 처리 완료 및 종료 통보
- 실행 이력/Audit 기록

자동화 제외:

- 도면/BOM/문서/마스터데이터 직접 변경
- 권한 실제 부여/삭제
- 발주/결재/ERP 변경 트랜잭션 직접 실행
- 변경 가능성이 있는 요청의 자동 완료 처리

## 3. 권장 워크플로우 흐름

```text
문장형 요청 입력
  -> 요청 등록
  -> AI 요청 의도 분류
  -> 선행 조건/승인 조건 판단
  -> 산출물 변경 여부 판단
  -> 처리 규정/FAQ/RAG 조회
  -> 자동 처리 가능 여부 판단
  -> 답변 초안 생성
  -> 검증
  -> 처리 완료
  -> 종료 통보
```

변경 가능성이 있거나 근거가 부족한 경우:

```text
산출물 변경 가능성 있음
  -> 수동 검토 이관
  -> IT 서비스 담당자 처리
  -> 종료 처리
```

승인/선행 조건이 필요한 경우:

```text
요청 입력
  -> 선행 조건 추출
  -> 승인/결재 상태 확인
  -> 조건 충족 시 처리 실행 또는 안내
  -> 조건 미충족 시 대기/이관/추가 안내
```

## 4. 개발할 노드 타입

1. `request_input`
   - 문장형 서비스 요청 입력
   - 입력: 요청 문장, 요청자, 부서, 시스템명, 긴급도
   - 출력: 표준 Request Context

2. `request_register`
   - 외부 mock 서버/서비스 시스템 접수 처리
   - 출력: request_id, 접수 시각, 접수 상태, 원문 문장

3. `intent_classify`
   - 요청 유형 분류
   - 출력: `simple_inquiry`, `account_action`, `permission_request`, `incident`, `change_related`, `unknown`

4. `precondition_check`
   - 선행 조건/승인 조건 판단
   - 예: "결재 후", "승인 후", "담당자 확인 후"
   - 출력: precondition_required, precondition_type, precondition_status

5. `artifact_change_check`
   - 산출물 변경 여부 판단
   - 출력: `no_artifact_change`, `possible_artifact_change`, `artifact_change_required`

6. `knowledge_lookup`
   - FAQ/규정/처리 기준 검색
   - 출력: 근거 문서, FAQ, confidence

7. `approval_check`
   - 승인 필요 여부 판단
   - 출력: approval_required, approver_group

8. `action_plan`
   - 실제 처리 액션 후보 생성
   - 예: password_reset 안내, account_unlock 안내, vpn_troubleshoot 안내
   - 출력: action_code, action_mode, risk_level

9. `draft_response`
   - 사용자 답변 초안 생성
   - 출력: answer, evidence, next_action

10. `human_handoff`
   - 담당자 수동 이관
   - 출력: assignee_group, handoff_reason

11. `validate_response`
   - 근거/정책/변경 없음 검증
   - 출력: validation_status, validation_notes

12. `complete_request`
   - 처리 완료
   - 출력: final_status, resolution_code

13. `notify_user`
   - 현업 종료 통보
   - 출력: notification_status

## 5. 실행 엔진 보강 항목

현재:

- `run_graph`가 `nodes` 배열 순서대로 실행한다.
- 엣지 방향, 조건 분기, 노드별 실제 로직은 반영하지 않는다.
- 모든 노드가 `[node_type] executed`로 성공 처리된다.

필요:

- 시작 노드 탐색
- 엣지 기반 다음 노드 실행
- condition 노드의 분기 라벨 처리
  - 예: `Y`, `N`, `manual`, `auto`, `approval`
- 노드 타입별 executor 분리
- 실행 context 누적
- 실패/스킵/수동대기 상태 처리
- timeout 및 max step guard
- 실행 이력에 입력/출력/근거 저장

## 6. 데이터 모델 초안

```json
{
  "request": {
    "request_id": "REQ-2026-0001",
    "text": "결재 후 비밀번호 초기화 해 주세요.",
    "requester": "user01",
    "department": "R&D",
    "system": "Account",
    "urgency": "normal"
  },
  "classification": {
    "category": "account_action",
    "sub_category": "password_reset",
    "confidence": 0.86
  },
  "precondition": {
    "required": true,
    "type": "approval",
    "status": "pending",
    "reason": "요청 문장에 '결재 후' 조건이 포함됨"
  },
  "artifact_change": {
    "status": "no_artifact_change",
    "reason": "계정 지원 업무이며 업무 산출물 직접 변경 없음"
  },
  "evidence": [
    {
      "source": "FAQ",
      "title": "VPN 접속 장애 1차 조치",
      "score": 0.91
    }
  ],
  "decision": {
    "route": "wait_approval",
    "approval_required": true,
    "handoff_required": false
  }
}
```

## 7. 프론트 개발 항목

- 서비스 요청 전용 노드 팔레트 추가
- 노드 속성 편집 폼 확장
  - category
  - prompt
  - rule
  - condition expression
  - output key
- handoff group
- 엣지 라벨 편집 지원
  - `Y`
  - `N`
  - `auto`
  - `manual`
  - `approval`
- 실행 context 패널 추가
- 노드별 입력/출력 JSON 보기
- 수동 이관/승인대기 상태 표시
- 스윔레인형 보기 또는 레인 메타데이터 추가

## 8. 백엔드 개발 항목

- `WorkflowGraphRunner` 서비스 신설
- 노드 executor registry 추가
- 외부 mock service adapter 추가
  - 문장형 요청 수신
  - 문장형 결과/상태 응답 처리
  - 내부 Request Context로 정규화
- RAG mock/real lookup 인터페이스 추가
- condition evaluator 구현
- 실행 이력에 step input/output 저장
- 수동 이관/승인대기 상태 정의
- API 추가
  - `POST /api/workflow-graphs/{graph_id}/run`
  - request body로 ticket 입력 지원
  - `GET /api/workflow-graphs/{graph_id}/runs/{run_id}`

## 9. 1차 개발 순서

1. 현재 목업 실행 엔진을 엣지 기반 실행으로 교체
2. 서비스 요청/RAG 댓글 노드 타입과 타입 정의 추가
3. `helpdesk2`를 범용 서비스 요청 샘플 그래프로 재구성
4. 노드별 mock executor 구현
5. 조건 분기 실행 구현
6. 실행 결과에 context/evidence/decision 표시
7. 수동 이관/변경 가능성 판단 케이스 추가
8. 참조 시나리오 3개 저장

## 10. 1차 시나리오 후보

### 시나리오 A: 단순 문의 자동 답변

- 입력: "VPN 접속 방법을 알려주세요."
- 판단: 산출물 변경 없음
- 처리: FAQ 조회 후 자동 답변
- 종료: 자동 완료

### 시나리오 B: 선행 결재 후 계정 조치

- 입력: "결재 후 비밀번호 초기화 해 주세요."
- 판단: 산출물 변경 없음, 선행 조건 있음
- 처리: 결재 상태 확인 후 처리 안내 또는 대기
- 종료: 결재 미완료면 대기/이관, 결재 완료면 처리 안내

### 시나리오 C: 변경 가능성으로 수동 이관

- 입력: "부품 마스터 정보가 잘못되어 수정하고 싶습니다."
- 판단: 산출물/마스터데이터 변경 가능성 있음
- 처리: 자동 완료 금지, 담당자 수동 이관
- 종료: 이관 완료

## 11. 완료 기준

- 사용자가 웹에서 서비스 요청 워크플로우를 직접 저작할 수 있다.
- 그래프 엣지 순서대로 실행된다.
- 조건 노드에서 Y/N 분기가 동작한다.
- 산출물 변경 없음 요청은 자동 응답까지 진행된다.
- 변경 가능성 있는 요청은 자동 완료하지 않고 수동 이관된다.
- 실행 이력에 각 노드의 입력, 판단 결과, 근거, 출력이 남는다.

## 12. 보안/네트워크 비용 관점 보완

Azure LLM 웹훅 스타일은 클라우드 네이티브하게는 단순해 보이지만, 보수적인 기업 보안 요건을 맞추려면 별도 네트워크 계층이 필요해질 수 있다.

특히 고객사 방화벽이 고정 발신지 IP, 제한된 inbound 허용, 감사 로그, 망분리 정책을 요구하는 경우에는 다음 구성이 추가될 수 있다.

- API Management 또는 별도 Webhook Gateway
- Azure Function/App Service 같은 중계 실행 계층
- VNet Integration
- NAT Gateway 및 고정 Public IP
- Private Link, VPN, ExpressRoute
- Key Vault, Managed Identity, 인증서/토큰 관리
- Monitor, Log Analytics, 감사 로그 저장

따라서 Azure LLM 웹훅을 보안 중계 네트워크와 묶는 구조는 클라우드 리소스 비용과 운영 복잡도가 증가한다.

반면 직접 구현한 Relay/n8n/LLM 추론 스킬 기반 구조는 outbound 호출 주체를 직접 통제할 수 있다. 고정 IP가 붙은 VM, NAT Gateway 뒤의 컨테이너, 또는 고정 IP Forward Proxy를 사용하면 고객사에는 "이 고정 IP만 허용"하는 방식으로 설명할 수 있다.

권장 방향:

```text
LLM 추론 스킬
  -> 직접 운영 Relay/Webhook
  -> RAG/MCP/API 호출
  -> 자동 댓글 등록
```

이 방식은 초기 PoC와 국내 보수적 보안 환경에서 비용, 설명, 방화벽 협의 측면의 부담이 낮다.

## 13. 개발 계획 요약

1. 현재 그래프 실행 엔진 분석
   - `run_graph`의 노드 배열 순차 실행 제거
   - 엣지 기반 실행 순서 계산 추가

2. 범용 RAG 자동 댓글 노드 타입 정의
   - `question_input`
   - `query_normalize`
   - `rag_search`
   - `evidence_select`
   - `answer_generate`
   - `answer_validate`
   - `post_comment`
   - `human_handoff`
   - `end`

3. 백엔드 실행기 구현
   - `WorkflowGraphRunner` 신설
   - 노드 타입별 executor registry 추가
   - 실행 context 누적
   - 조건 분기 및 skip 처리
   - step input/output 저장

4. mock 서버 연동
   - 문장형 질의 수신
   - RAG 검색 mock 또는 실제 API 호출
   - 자동 댓글 등록 mock API 호출

5. 프론트 보강
   - RAG 자동 댓글용 팔레트 추가
   - 노드별 속성 편집 필드 추가
   - 실행 context/evidence/answer 표시
   - 엣지 라벨 기반 분기 표시

6. 샘플 그래프 구성
   - 단순 FAQ 질의 자동 댓글
   - 결재/승인 조건이 있는 요청 안내 댓글
   - 산출물 변경 가능성이 있는 요청의 수동 이관 댓글

7. 검증
   - 그래프 저장/불러오기
   - 엣지 순서 실행
   - RAG 검색 결과 기반 댓글 생성
   - 근거 부족 시 자동 댓글 차단 또는 수동 이관
   - 실행 이력/Audit 저장

## 14. v5 개발 우선순위 결정

검토 기준:

- `ont_platform v5` 백엔드는 `/api/v5/hybrid/ask`, `QuestionAnalyzer`, `EvidenceGate`, no-answer policy가 이미 구현되어 있고 `validation/ont_platform_v5_eval`에서 동일 24문항 평가가 수행되었다.
- v5 평가 결과는 기존 예상답변 기준 49.38%, STD-S no-answer 보정 기준 75.21%이다.
- v5 프론트는 현재 `.next` 빌드 산출물은 있으나 `frontend/src` 소스가 없어 화면 개발/수정의 직접 기준이 없다.
- `design/팔란티어스타일` 설계는 온톨로지 코어, source mapping, accuracy layer, EvidenceGate, 영향도 분석을 1순위로 보고, workflow/action은 코어 안정 후 확장하는 방향이다.

결론:

```text
1순위: v5 프론트 소스 복원/승격
2순위: v5 백엔드 API contract 고정 및 RAG 자동 댓글용 최소 backend slice
3순위: 프론트-백엔드 end-to-end 화면 검증
4순위: 팔란티어스타일 백엔드 코어 고도화
```

이유:

- 백엔드는 v5 평가 기준선이 이미 있으므로 당장 전체 백엔드를 다시 크게 확장하기보다, 프론트가 붙을 수 있는 API contract를 먼저 고정한다.
- 프론트 소스가 없는 상태에서는 v5 기능이 실제 사용자 흐름으로 검증되지 않는다.
- 다만 프론트만 먼저 크게 만들면 backend contract가 흔들릴 수 있으므로, v5 프론트 복원 직후 RAG 자동 댓글용 최소 API와 mock adapter를 함께 고정한다.
- 팔란티어스타일 백엔드 방향은 전략적으로 중요하지만, 현재 작업의 1차 목표인 "웹에서 워크플로우를 저작하고 RAG 자동 댓글 흐름을 시뮬레이션"하는 데에는 v5 화면 복원이 선행 병목이다.

권장 실행 순서:

1. `ont_platform/v4/frontend/src`를 `ont_platform/v5/frontend/src`로 복사해 v5 프론트 소스를 복원한다.
2. v5 프론트가 `http://localhost:8002` 또는 명시된 v5 backend API base를 보도록 설정한다.
3. v5 백엔드의 `/api/v5/hybrid/ask` contract를 프론트에서 호출 가능한 형태로 문서화한다.
4. RAG 자동 댓글 workflow에 필요한 최소 API를 정의한다.
   - `POST /api/v5/service-requests/mock`
   - `POST /api/v5/workflow-graphs/{graph_id}/run-comment`
   - 또는 기존 `/api/workflow-graphs/{graph_id}/run`에 request body 확장
5. 워크플로우 화면에 RAG 자동 댓글 노드 팔레트와 실행 결과 패널을 추가한다.
6. v5 backend + v5 frontend 조합으로 별도 스모크 테스트를 수행한다.
7. 이후 source mapping, EvidenceGate 강화, QuestionAnalyzer 개선, 영향도 분석 등 팔란티어스타일 백엔드 코어를 단계적으로 넣는다.
