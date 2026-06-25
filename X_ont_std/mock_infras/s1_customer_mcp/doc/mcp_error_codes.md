# MCP Error Codes (s1_customer_mcp)

솔루션이 `s1_customer_mcp` 호출 중 실패했을 때 반환하는 규격화된 에러 응답 및 오류 코드 명세입니다.

---

## 🛑 에러 응답 포맷 (Error Schema)
에러 발생 시 `status: "error"`가 지정되며, `result`는 `null`이 됩니다. 또한 `error` 객체에 상세 필드가 반환됩니다.

```json
{
  "request_id": "수신된-uuid",
  "status": "error",
  "tool": "comment.create",
  "result": null,
  "error": {
    "code": "오류_코드",
    "message": "인간이 읽을 수 있는 상세 메시지",
    "retryable": true
  }
}
```

---

## 📊 오류 코드 정의 목록

| 오류 코드 (`code`) | HTTP 상태 코드 | 재시도 가능 여부 (`retryable`) | 발생 조건 및 상황 |
| :--- | :---: | :---: | :--- |
| **`INVALID_REQUEST`** | 400 | `false` | 필수 파라미터(`company_id`, `project_id`, `request_id`, `arguments` 등)가 누락되었거나 JSON 포맷 오류인 경우 |
| **`TOOL_NOT_FOUND`** | 404 | `false` | 시나리오 1에서 허용되지 않은 도구명으로 요청한 경우 (허용 도구: `comment.create`) |
| **`BOARD_API_ERROR`** | 404 / 500 | `true` (404는 `false`) | 대상 게시물 ID가 게시판 서버에 존재하지 않거나, 게시판 서버 API가 내부 오류를 리턴할 경우 |
| **`BOARD_TIMEOUT`** | 503 | `true` | `s1_customer_board` API 서버(포트 8090)가 꺼져 있거나 연결 제한 시간을 초과했을 때 |
| **`INTERNAL_ERROR`** | 500 | `true` | 중계 서버 내부에서 알 수 없는 런타임 예외가 발생했을 때 |

---

## 🛠️ 솔루션 대응 가이드
* **재시도 가능 (`retryable: true`)**: 솔루션의 워크플로우 엔진에서 일정 시간(예: 3초, 5초) 대기 후 최대 3회 재시도 정책을 적용하여 자동으로 다시 요청할 수 있습니다.
* **재시도 불가 (`retryable: false`)**: 즉시 실패로 감사 로그에 기록하며, 댓글 생성 작업을 `approval_required` 혹은 수동 재시도 대기 상태로 전환해야 합니다.
