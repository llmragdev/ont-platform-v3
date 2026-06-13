# [시나리오 1] 고객사 모의 인프라 설계 및 개발 보고서

**작성일**: 2026-06-12  
**작성자**: Antigravity (고객사 연동 개발 담당)  
**상태**: 검토 및 검증 완료  
**대상 시스템**: 고객사 게시판 시스템(`s1_customer_board`), 고객사 MCP 중계 서버(`s1_customer_mcp`)

---

## 📌 1. 개요 및 배경

본 보고서는 `ont_platform v5`와의 통합 연동을 검증하기 위해 독립적으로 구축된 **고객사 측 모의 인프라(Mock Infrastructure)**의 설계 및 개발 명세를 기술한다. 

시나리오 1은 고객사 게시판에 새 문의글이 올라왔을 때 이를 감지하여 AI가 자동으로 댓글을 다는 시나리오다. 이를 현실감 있게 검증하기 위해 실제 상용 시스템 구조를 모방한 독자적인 서비스 바운더리를 설계하고 개발을 진행했다.

---

## 🏗️ 2. 시스템 아키텍처

고객사 측 Mock 시스템은 `ont_platform` 솔루션 영역과 분리된 독립된 2개의 프로세스로 실행되며, 상호 HTTP API를 통해 유기적으로 통신한다.

```mermaid
graph TD
    subgraph Solution_v5 [ont_platform v5 영역 (Port: 8001)]
        API_Trigger[Event API /api/extn/customer-questions/events]
        Replies_API[Replies API /api/extn/customer-replies/generate-and-post]
    end

    subgraph Customer_Side [고객사 mock 영역]
        MCP_Server[s1_customer_mcp (Port: 8080)]
        Board_Server[s1_customer_board (Port: 8090)]
        SQLite_DB[(SQLite DB s1_customer_board.db)]
    end

    %% 시나리오 1-2 (실시간 웹훅) 흐름
    Board_Server -- "1. 신규 문의 감지 시 웹훅 트리거" --> API_Trigger
    API_Trigger -- "2. AI 댓글 생성 후 MCP 호출" --> MCP_Server
    
    %% 시나리오 1-1 (배치 폴링) 흐름
    Replies_API -- "배치 폴링 미처리 문의 조회" --> MCP_Server
    
    %% MCP와 Board 간 연동
    MCP_Server -- "3. API 호출 변환" --> Board_Server
    Board_Server -- "4. 데이터 읽기/쓰기" --> SQLite_DB
```

### 2.1 프로세스 구성 명세
* **`s1_customer_board` (Port 8090)**:
  * 역할: SQLite 기반 고객사 게시판 시스템 모사, 웹 화면(3단 프리미엄 대시보드) 제공 및 이벤트 트리거 역할 수행
* **`s1_customer_mcp` (Port 8080)**:
  * 역할: `ont_platform`의 표준 MCP(Model Context Protocol) 툴 호출을 수신하여 고객사 게시판 API로 중계 및 프로토콜 변환

---

## 💾 3. 데이터베이스 설계 (SQLite)

고객사 게시판 시스템(`s1_customer_board`)은 단일 SQLite DB 파일(`s1_customer_board.db`)을 통해 지속성을 확보한다.

### 3.1 테이블 스키마
* **`posts` (문의글 테이블)**:
  ```sql
  CREATE TABLE posts (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      author TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TEXT NOT NULL
  );
  ```
* **`comments` (댓글 테이블)**:
  ```sql
  CREATE TABLE comments (
      id TEXT PRIMARY KEY,
      post_id TEXT NOT NULL,
      author TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
  );
  ```

---

## 🔌 4. API 규격 및 도구 정의

### 4.1 MCP 도구 호출 규격 (POST `/mcp/tools/comment.create`)
`ont_platform`이 생성된 AI 댓글 초안을 최종 등록할 때 호출하는 API 규격이다. 하이브리드 어댑터 레이어를 통해 Codex 표준 포맷과 Claude Code 레거시 포맷을 모두 견고하게 처리하도록 설계했다.

* **요청 Payload (Spec Version)**:
  ```json
  {
    "request_id": "uuid",
    "company_id": "demo-company",
    "project_id": "demo-project",
    "mode": "post",
    "tool": "comment.create",
    "arguments": {
      "question_id": "q-001",
      "thread_id": "thread-001",
      "post_id": "q-001",
      "message": "AI 자동 생성 댓글 내용",
      "author": "ontology-workflow"
    }
  }
  ```
* **응답 (성공 시)**:
  ```json
  {
    "request_id": "uuid",
    "status": "success",
    "tool": "comment.create",
    "result": {
      "external_comment_id": "comment-ed10550c",
      "external_thread_id": "q-001",
      "url": "http://localhost:8090/posts/q-001#comment-comment-ed10550c"
    },
    "error": null
  }
  ```

### 4.2 오류 응답 규격화 및 예외 처리
API 장애 대응을 위한 오류 코드 매핑 테이블을 구축했다.

| Error Code | Retryable | Description |
| :--- | :---: | :--- |
| `INVALID_REQUEST` | false | 필수 파라미터(텍스트, 대상 ID 등) 누락 혹은 잘못된 페이로드 포맷 |
| `BOARD_API_ERROR` | true | `customer_board` API 통신 오류 혹은 대상 게시글이 존재하지 않음 |
| `BOARD_TIMEOUT` | true | 게시판 서버와의 제한 시간 초과 |
| `TOOL_NOT_FOUND` | false | 지원하지 않는 부적절한 도구명 호출 |
| `INTERNAL_ERROR` | true | MCP 중계 서버 내부 기타 예외 상황 발생 |

---

## 🔄 5. 시나리오별 상세 개발 내용

### 5.1 시나리오 1-2: 실시간 Webhook 자동 트리거 (Push 방식)
고객사 게시판에서 신규 문의 등록 시 솔루션에 이벤트를 전송하는 실시간 시나리오다.
* **이벤트 발행 페이로드**:
  * 대상 엔드포인트: `POST http://localhost:8001/api/extn/customer-questions/events`
  * 필드: `event_id`, `event_type`, `question_id`, `title`, `content`, `author`, `created_at`, `mode`
* **개발 조치**:
  * `s1_customer_board` 단에서 비동기 백그라운드 스레드 형태로 웹훅을 호출하도록 구성하여, 솔루션 서버의 상태(다운 등)가 게시판 본연의 등록 지연을 유발하지 않도록 격리했다.

### 5.2 시나리오 1-1: 배치 폴링 및 미처리 문의 보정 (Pull 방식)
솔루션 스케줄러가 정기적으로 미처리 내역을 수집하는 방식이다. 요구사항 보완에 따라 배치 쿼리용 후보 API 2종을 새로 추가 구현했다.
* **`GET /mcp/tools/question.list?status=open`**:
  * 고객사 DB에 접근하여 댓글(`comments`)의 카운트가 `0`인 아직 답변이 달리지 않은 오픈 문의들만 추려 리스트로 리턴한다.
* **`GET /mcp/tools/question.get?question_id={id}`**:
  * 개별 문의글의 내용과 등록된 댓글 현황(`comments_count`)을 추적 조회한다.

---

## 🧪 6. 연동 검증 및 결과 (Smoke Test)

고객사 Mock 인프라(`8080`, `8090`)와 `ont_platform v5` 백엔드(`8001`)간의 통합 연동 테스트를 진행했으며 결과는 모두 **PASS** 판정을 기록했다.

1. **Dry-run 검증 (PASS)**:
   * `mode=dry_run`일 때 DB에 데이터가 생성되지 않고 요청 필드 정합성만 통과하는지 확인.
2. **Post 검증 (PASS)**:
   * `mode=post`일 때 `s1_customer_board.db`에 실제 AI 답변 댓글이 저장 및 렌더링되는지 확인.
3. **배치 Polling 검증 (PASS)**:
   * 신규 배치 조회 도구 API(`/mcp/tools/question.list?status=open`)를 통해 댓글이 없는 게시물만 정확하게 걸러져 출력되는지 PowerShell을 활용해 검증 성공.
4. **Audit 생성 확인 (PASS)**:
   * 연동 즉시 `ont_platform/v5/backend/storage/.../audit/customer_mcp_calls.jsonl` 파일 내 거래 이력 로깅 정상 적재 완료.

---

## 🚨 7. 차기 개선 과제 및 플랫폼 Gap 요약

현재 고객사 Mock 서버 및 연동 규격은 완전한 대비를 완료했으나, `ont_platform v5` 솔루션 백엔드에 다음과 같은 요구사항 구현이 누락되어 있어 보완이 필요하다.

1. **이벤트 수신부 (`POST /api/extn/customer-questions/events`) 구현**:
   * 웹훅 전송을 받아 댓글 초안 생성 및 MCP 호출로 밀어넣어 줄 이벤트 리시버 라우터 구현이 필요하다.
2. **멱등성 보장(Idempotency) 상태 추적 레이어 구축**:
   * 이벤트 중복 처리를 방지하기 위한 `customer_question_events.jsonl` 및 `customer_question_state.json` 상태 관리 유틸리티가 구현되어야 한다.
3. **배치 스케줄러 탑재**:
   * 정기적으로 `question.list?status=open`을 폴링하여 연동 누락분을 지속 감지하고 동기화할 백그라운드 태스크 엔진 도입이 요구된다.
