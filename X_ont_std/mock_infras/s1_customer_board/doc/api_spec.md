# REST API Specification (s1_customer_board)

고객사 모의 게시판 시스템이 제공하는 내부 및 외부 연동용 REST API 규격서입니다.

---

## ⚙️ 기본 정보
* **Base URL**: `http://localhost:8090`
* **Content-Type**: `application/json`

---

## 📋 엔드포인트 목록

### 1. 게시글 목록 조회
* **Method & Path**: `GET /api/posts`
* **Query Parameters**:
  * `status` (Optional): `"open"`으로 지정 시, 댓글이 전혀 달리지 않은 미처리 문의 목록만 필터링하여 반환합니다.
* **Response (200 OK)**:
  ```json
  [
    {
      "id": "q-001",
      "title": "[시나리오1] 비밀번호 초기화 요청",
      "author": "홍길동",
      "content": "로그인 비밀번호가 기억나지 않습니다.",
      "created_at": "2026-06-12T01:45:15.904993"
    }
  ]
  ```

### 2. 게시글 상세 및 댓글 조회
* **Method & Path**: `GET /api/posts/{post_id}`
* **Response (200 OK)**:
  ```json
  {
    "id": "q-001",
    "title": "[시나리오1] 비밀번호 초기화 요청",
    "author": "홍길동",
    "content": "로그인 비밀번호가 기억나지 않습니다.",
    "created_at": "2026-06-12T01:45:15.904993",
    "comments": [
      {
        "id": "comment-ed10550c",
        "post_id": "q-001",
        "author": "시스템봇",
        "content": "본 게시글은 접수 완료되었습니다.",
        "created_at": "2026-06-12T01:46:20.123456"
      }
    ]
  }
  ```
* **Response (404 Not Found)**: 해당 ID의 게시글이 존재하지 않는 경우
  ```json
  {
    "detail": "Post not found"
  }
  ```

### 3. 신규 게시글 작성 (이벤트 유발)
* **Method & Path**: `POST /api/posts`
* **Request Body**:
  ```json
  {
    "title": "비밀번호 초기화 요청",
    "author": "홍길동",
    "content": "초기화 부탁드립니다."
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "id": "q-abc12345",
    "title": "비밀번호 초기화 요청",
    "author": "홍길동",
    "content": "초기화 부탁드립니다.",
    "created_at": "2026-06-12T05:00:00.000000"
  }
  ```
* **설명**: 웹훅 자동 트리거 설정이 활성화(`webhook_enabled = true`)되어 있는 경우, 등록과 동시에 비동기 백그라운드 태스크로 `webhook_target` 주소에 신규 질문 생성 이벤트를 발행합니다.

### 4. 댓글 등록
* **Method & Path**: `POST /api/posts/{post_id}/comments`
* **Request Body**:
  ```json
  {
    "author": "ontology-workflow",
    "content": "생성된 AI 답변 내용"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "id": "comment-xyz98765",
    "post_id": "q-001",
    "author": "ontology-workflow",
    "content": "생성된 AI 답변 내용",
    "created_at": "2026-06-12T05:01:00.000000"
  }
  ```

---

## ⚙️ 시스템 설정 및 관리 API

### 5. 연동 설정 조회
* **Method & Path**: `GET /api/settings`
* **Response (200 OK)**:
  ```json
  {
    "webhook_enabled": true,
    "webhook_mode": "post",
    "webhook_target": "http://localhost:8001/api/extn/customer-questions/events"
  }
  ```

### 6. 연동 설정 수정
* **Method & Path**: `POST /api/settings`
* **Request Body**:
  ```json
  {
    "webhook_enabled": true,
    "webhook_mode": "post",
    "webhook_target": "http://localhost:8001/api/extn/customer-questions/events"
  }
  ```

### 7. 웹훅 전송 로그 조회
* **Method & Path**: `GET /api/webhook-logs`
* **Response (200 OK)**:
  ```json
  {
    "logs": [
      {
        "timestamp": "11:32:05",
        "event_id": "evt-8123-abc",
        "post_id": "q-002",
        "title": "초기화 요청",
        "status": "success",
        "mode": "post",
        "response": { "status": "accepted" },
        "error": null
      }
    ]
  }
  ```

### 8. 웹훅 전송 로그 비우기
* **Method & Path**: `POST /api/webhook-logs/clear`
* **Response (200 OK)**:
  ```json
  {
    "status": "cleared"
  }
  ```

### 9. 배치 폴링 수동 시뮬레이션
* **Method & Path**: `POST /api/simulate/polling`
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "scanned_posts": 5,
    "triggered_count": 1,
    "triggered_posts": [{ "id": "q-002", "title": "답변 없는 문의" }],
    "message": "배치 검사 결과, 댓글이 없는 미처리 문의글 1건에 대해 워크플로우 실행을 유도했습니다."
  }
  ```
