# Scenario 1 실행 한 장 가이드

작성일: 2026-06-13  
대상: 고객사 게시판 문의 자동 댓글 테스트  
범위: Scenario 1-2 실시간 Webhook, Scenario 1-1 수동 배치/워크플로우 호출

## 1. 서버 기동 확인

필수 서버 3개를 모두 켠다.

| Server | Port | 실행 위치 | 역할 |
| --- | ---: | --- | --- |
| ont_platform v5 backend | 8001 | `ont_platform/v5/backend` | 이벤트 수신, 답변 생성, MCP 호출 |
| customer_mcp | 8080 | `s1_customer_mcp` | 고객사 게시판 API 중계 |
| customer_board | 8090 | `s1_customer_board` | 고객사 모의 게시판 UI/API |

ont_platform v5 backend 실행:

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v5\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

헬스 체크:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-RestMethod http://127.0.0.1:8080/health
```

게시판 UI:

```text
http://127.0.0.1:8090/
```

## 2. 공통 테스트 문의 예시

제목:

```text
비밀번호 초기화 요청
```

내용:

```text
안녕하세요. 관리자 계정 비밀번호를 분실했습니다. 비밀번호 초기화 절차와 처리 예상 시간을 안내해 주세요.
```

## 3. 방법 A: 실시간 Webhook 자동 댓글

목적: 고객사 게시판에서 새 문의가 등록되면 즉시 ont_platform으로 이벤트가 전달되고 댓글이 자동 등록되는지 확인한다.

1. `http://127.0.0.1:8090/` 접속
2. 우측 설정에서 `실시간 Webhook 자동 트리거`를 ON
3. Webhook mode를 `post`로 설정
   - `dry_run`: 흐름만 확인하고 게시판 댓글은 실제 등록하지 않음
   - `post`: 게시판에 실제 댓글 등록
4. Webhook target 확인

```text
http://localhost:8001/api/extn/customer-questions/events
```

5. 새 문의 작성
6. 문의 상세에서 `ontology-workflow` 댓글이 달렸는지 확인
7. 실패 시 게시판의 Webhook 로그에서 `Connection refused` 여부 확인
   - 이 경우 대부분 ont_platform backend `8001`이 꺼져 있는 상태다.

Webhook 경로:

```text
customer_board:8090
  -> POST /api/extn/customer-questions/events
  -> 답변 초안 생성
  -> customer_mcp:8080 /mcp/tools/comment.create
  -> customer_board 댓글 등록
```

## 4. 방법 B: 수동 배치/워크플로우 호출

목적: 실시간 Webhook이 꺼졌거나 누락된 문의를 ont_platform이 `customer_mcp`를 통해 찾아 댓글 처리하는지 확인한다.

1. `http://127.0.0.1:8090/` 접속
2. 우측 설정에서 `실시간 Webhook 자동 트리거`를 OFF
3. 새 문의 작성
   - 이때 댓글이 바로 달리지 않아야 정상이다.
4. PowerShell에서 수동 배치 실행

먼저 dry-run:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8001/api/extn/customer-questions/batch/run-once" `
  -Headers @{"Content-Type"="application/json";"X-Company-Id"="default";"X-Project-Id"="proj-default";"X-User-Id"="default-user"} `
  -Body (@{status="open";mode="dry_run";limit=10} | ConvertTo-Json)
```

실제 댓글 등록:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8001/api/extn/customer-questions/batch/run-once" `
  -Headers @{"Content-Type"="application/json";"X-Company-Id"="default";"X-Project-Id"="proj-default";"X-User-Id"="default-user"} `
  -Body (@{status="open";mode="post";limit=10} | ConvertTo-Json)
```

응답 확인 기준:

| Field | 의미 |
| --- | --- |
| `checked` | MCP에서 조회한 미처리 문의 수 |
| `started` | 이번 실행에서 워크플로우가 시작된 수 |
| `skipped` | 이미 처리되어 건너뛴 수 |
| `errors` | 처리 실패 수 |

배치 경로:

```text
ont_platform batch/run-once
  -> customer_mcp:8080 /mcp/tools/question.list?status=open
  -> 각 문의에 대해 답변 초안 생성
  -> customer_mcp:8080 /mcp/tools/comment.create
  -> customer_board 댓글 등록
```

## 5. 자주 나는 실수

PowerShell에서 `curl`은 실제 curl이 아니라 `Invoke-WebRequest` 별칭이다. `-H "Content-Type: application/json"` 문법이 실패하면 `Invoke-RestMethod`를 쓰거나 `curl.exe`로 실행한다.

이미 `mode=post`로 성공 댓글이 달린 문의는 중복 방지 때문에 다시 처리되지 않는다. 같은 문의를 다시 처리해야 할 때는 새 문의를 만들거나 강제 재처리 옵션을 별도로 사용한다.

배치 검증을 하려면 Webhook을 먼저 OFF 해야 한다. Webhook이 ON이면 새 문의 작성 즉시 댓글이 달려서 배치가 처리할 미처리 문의가 남지 않는다.

## 6. 산출물 확인 위치

Audit 로그:

```text
ont_platform/v5/backend/storage/default/proj-default/audit/customer_mcp_calls.jsonl
```

Event/idempotency 상태:

```text
ont_platform/v5/backend/storage/default/proj-default/events/customer_question_events.jsonl
ont_platform/v5/backend/storage/default/proj-default/events/customer_question_state.json
```

고객사 게시판 DB:

```text
s1_customer_board/s1_customer_board.db
```
