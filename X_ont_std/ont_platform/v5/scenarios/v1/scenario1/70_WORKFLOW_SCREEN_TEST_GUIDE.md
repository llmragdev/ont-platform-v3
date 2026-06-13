# Workflow 화면 테스트 가이드

작성일: 2026-06-13  
대상 화면: ont_platform v5 frontend `Workflow Home`, `Workflow Builder`, `승인 워크플로우`

## 1. 현재 결론

현재 Workflow 화면은 다음 기능을 제공한다.

- Workflow Home에서 템플릿 목록 확인
- Workflow Builder에서 템플릿 복제, 그래프 저장, 노드 추가/수정
- Workflow Builder의 실행 버튼으로 그래프 실행 시뮬레이션
- 실행 결과와 WorkflowRun 이력 확인

하지만 현재 화면의 `실행` 버튼은 고객사 게시판 자동 댓글 API와 직접 연결되어 있지 않다.

즉, 지금 화면에서 가능한 것은 "워크플로우 그래프 실행 시뮬레이션"이고, 실제 고객사 게시판에 댓글을 다는 처리는 아래 API 또는 8090 게시판 Webhook/Batch 절차로 실행해야 한다.

```text
POST /api/extn/customer-questions/events
POST /api/extn/customer-questions/batch/run-once
POST /api/extn/customer-replies/generate-and-post
```

## 2. 화면 접속

프론트엔드가 `3002`에서 실행 중이어야 한다.

```powershell
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run dev -- --port 3002
```

브라우저:

```text
http://127.0.0.1:3002/
```

## 3. Workflow Home에서 템플릿 확인

1. 좌측 메뉴에서 `Workflow Home` 선택
2. `Use Case Gallery` 영역 확인
3. `서비스 요청 자동댓글` 템플릿이 있으면 Scenario 1 계열 템플릿으로 보면 된다.
4. `템플릿 선택` 버튼을 눌러 Template Gallery로 이동한다.

주의:

- 현재 일부 템플릿 문자열은 인코딩 문제로 깨져 보일 수 있다.
- 그래도 템플릿 구조 자체는 저장/복제/실행 확인에 사용할 수 있다.

## 4. Workflow Builder에서 그래프 실행 시뮬레이션

1. 좌측 메뉴에서 `Workflow Builder` 선택
2. 저장된 그래프가 있으면 상단 드롭다운에서 선택
3. 없으면 Template Gallery에서 `서비스 요청 자동댓글` 템플릿을 복제하거나, Builder에서 노드를 직접 추가
4. `저장` 클릭
5. `실행` 클릭
6. 노드 상태가 `running` -> `success`로 변하는지 확인
7. 하단 `노드별 실행 결과`와 `WorkflowRun 이력` 확인

현재 실행 결과는 실제 Skill/MCP 호출 결과가 아니라 다음 형태의 mock 결과다.

```text
[request_input] executed
[intent_classify] executed
[knowledge_lookup] executed
[evidence_gate] executed
[draft_response] executed
```

## 5. Workflow 화면과 실제 자동 댓글의 차이

| 구분 | 현재 Workflow 화면 | 실제 Scenario 1 자동 댓글 |
| --- | --- | --- |
| 실행 진입점 | `/api/workflow-graphs/{graph_id}/run` | `/api/extn/customer-questions/events`, `/batch/run-once` |
| 처리 방식 | 노드 실행 시뮬레이션 | 고객 문의 수신/조회 후 답변 생성 및 MCP 댓글 등록 |
| 게시판 댓글 등록 | 안 함 | `customer_mcp` 경유로 등록 |
| Audit | WorkflowRun 저장 | `customer_mcp_calls.jsonl`, event state 저장 |
| 현재 상태 | UI/그래프 검증 가능 | 운영 흐름 검증 가능 |

## 6. 실제 댓글 처리를 화면에서 검증하려면

현재는 Workflow Builder 화면만으로 실제 게시판 댓글 등록까지 처리할 수 없다.

대신 아래 중 하나로 검증한다.

### A. Webhook 방식

1. `http://127.0.0.1:8090/` 접속
2. Webhook ON
3. mode `post`
4. 새 문의 작성
5. 댓글 등록 확인

### B. 수동 배치 방식

1. `http://127.0.0.1:8090/` 접속
2. Webhook OFF
3. 새 문의 작성
4. PowerShell에서 batch 실행

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8001/api/extn/customer-questions/batch/run-once" `
  -Headers @{"Content-Type"="application/json";"X-Company-Id"="default";"X-Project-Id"="proj-default";"X-User-Id"="default-user"} `
  -Body (@{status="open";mode="post";limit=10} | ConvertTo-Json)
```

## 7. 화면에서 실제 처리까지 가능하게 만들려면 필요한 보완

Workflow 화면에서 실제 자동 댓글을 처리하려면 다음 중 하나를 구현해야 한다.

### 옵션 1. Workflow Builder에 Scenario 1 실행 패널 추가

가장 빠른 보완 방식이다.

- `mode`: `dry_run` / `post`
- `trigger`: `batch/run-once`
- `limit`
- 실행 버튼
- 결과 요약: `checked`, `started`, `skipped`, `errors`
- 게시판 링크 또는 최근 처리 question 목록

호출 API:

```text
POST /api/extn/customer-questions/batch/run-once
```

### 옵션 2. WorkflowGraphRunner가 실제 Skill executor를 호출

정석 구현 방식이다.

- `request_input`
- `intent_classify`
- `knowledge_lookup`
- `evidence_gate`
- `draft_response`
- `customer_mcp.comment_create`

이 경우 `/api/workflow-graphs/{graph_id}/run` 내부가 mock 실행이 아니라 실제 executor dispatch를 해야 한다.

## 8. 테스트 체크리스트

- Workflow Builder에서 그래프 저장이 되는가?
- 실행 버튼 클릭 시 노드별 상태가 변하는가?
- 실행 이력이 남는가?
- 같은 시간에 8090 게시판 자동 댓글 시나리오가 별도 API로 정상 동작하는가?
- 운영자에게 "현재 화면 실행은 mock, 실제 댓글 등록은 Webhook/Batch API"라는 경계가 명확히 안내되는가?
