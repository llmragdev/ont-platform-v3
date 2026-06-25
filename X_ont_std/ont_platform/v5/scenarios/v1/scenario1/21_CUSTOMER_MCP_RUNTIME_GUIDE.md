# Customer MCP Runtime Guide - s1_customer_mcp

작성일: 2026-06-13  
대상 서버: `E:\ontology_edu\X_ont_std\mock_infras\s1_customer_mcp`  
원본 운영 문서: `E:\ontology_edu\X_ont_std\mock_infras\s1_customer_mcp\README.md`

## 1. 목적

이 문서는 Scenario 1에서 사용하는 고객사 MCP 중계 서버 `s1_customer_mcp`의 구동 방법과 검증 방법을 scenario1 문서 체계 안에서 요약한다.

상세 실행 매뉴얼은 `s1_customer_mcp/README.md`를 기준으로 한다.

`s1_customer_mcp`의 역할:

```text
ont_platform v5
  -> s1_customer_mcp
  -> s1_customer_board
```

`ont_platform v5`는 고객사 게시판 `s1_customer_board`를 직접 호출하지 않는다.  
댓글 등록은 반드시 `s1_customer_mcp`를 경유한다.

## 2. 서버 정보

| 항목 | 값 |
| --- | --- |
| 서버명 | `s1_customer_mcp` |
| 기본 포트 | `8080` |
| 실행 위치 | `E:\ontology_edu\X_ont_std\mock_infras\s1_customer_mcp` |
| 실행 파일 | `src/main.py` |
| 의존 서버 | `s1_customer_board` |
| 의존 서버 포트 | `8090` |

## 3. 사전 조건

- Python 3.10 이상 권장
- conda 환경 `claud_be`
- `fastapi`, `uvicorn`, `pydantic`
- `s1_customer_board`가 먼저 8090 포트에서 기동되어 있어야 함

`s1_customer_mcp`는 자체 데이터를 저장하지 않고, 고객사 게시판 API로 요청을 전달한다.

## 4. 실행 명령

PowerShell:

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\mock_infras\s1_customer_mcp
python src/main.py
```

정상 기동 예:

```text
Uvicorn running on http://0.0.0.0:8080
```

## 5. Health Check

```powershell
Invoke-RestMethod http://localhost:8080/health
```

정상 응답:

```json
{
  "status": "ok",
  "service": "customer_mcp"
}
```

주의:

- `s1_customer_board`가 꺼져 있으면 health check가 실패하거나 503이 날 수 있다.
- 이 경우 8090 게시판 서버를 먼저 확인한다.

## 6. 필수 Tool

Scenario 1에서 필수로 사용하는 MCP tool:

```http
POST /mcp/tools/comment.create
```

용도:

```text
ont_platform가 생성한 댓글 메시지
  -> customer_mcp가 수신
  -> customer_board 게시글 댓글로 등록
```

## 7. Dry-run 테스트

실제 댓글 저장 없이 호출 규격만 검증한다.

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/mcp/tools/comment.create" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"request_id":"test-dryrun-001","company_id":"demo-co","project_id":"proj-01","mode":"dry_run","tool":"comment.create","arguments":{"question_id":"q-001","post_id":"q-001","message":"Dry-run 테스트 댓글","author":"ontology-workflow"}}'
```

기대:

```json
{
  "status": "dry_run",
  "tool": "comment.create"
}
```

## 8. Post 테스트

실제 게시판 댓글을 등록한다.

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/mcp/tools/comment.create" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"request_id":"test-post-001","company_id":"demo-co","project_id":"proj-01","mode":"post","tool":"comment.create","arguments":{"question_id":"q-001","post_id":"q-001","message":"Post 테스트 댓글","author":"ontology-workflow"}}'
```

기대:

```json
{
  "status": "success",
  "tool": "comment.create",
  "result": {
    "external_comment_id": "comment-..."
  }
}
```

## 9. Batch Polling 후보 Tool

배치 방식에서 ont_platform이 미처리 문의를 조회할 때 사용하는 후보 API:

```http
GET /mcp/tools/question.list?status=open
```

용도:

```text
댓글이 없는 미처리 문의 목록 조회
```

이 API는 Scenario 1-1 배치 보정 흐름에서 사용된다.

## 10. 관련 문서

| 문서 | 역할 |
| --- | --- |
| `mock_infras/s1_customer_mcp/README.md` | 실제 서버 구동 매뉴얼 |
| `mock_infras/s1_customer_mcp/doc/architecture.md` | 중계 서버 구조 |
| `mock_infras/s1_customer_mcp/doc/integration_guide.md` | 연동 스모크 테스트 |
| `mock_infras/s1_customer_mcp/doc/mcp_error_codes.md` | 표준 오류 코드 |
| `20_CUSTOMER_MCP_CALL_SPEC.md` | ont_platform -> customer_mcp 공식 호출 계약 |
| `40_CUSTOMER_MOCK_INFRA_DESIGN.md` | customer_mcp/customer_board 전체 mock 인프라 설계 |

## 11. 책임 경계

- `ont_platform v5`는 `customer_mcp`만 호출한다.
- `customer_mcp`는 고객사 게시판 API 호출과 프로토콜 변환을 책임진다.
- `customer_board`는 고객사 게시판 mock API/UI다.
- customer_mcp/customer_board 장애는 ont_platform 전체 장애로 전파되지 않아야 한다.

## 12. 완료 기준

- `s1_customer_board` 8090 기동
- `s1_customer_mcp` 8080 기동
- `/health` 정상 응답
- `comment.create` dry_run 성공
- `comment.create` post 성공
- 게시판 UI에서 실제 댓글 확인 가능
- 오류 응답은 `20_CUSTOMER_MCP_CALL_SPEC.md` 구조를 따른다.
