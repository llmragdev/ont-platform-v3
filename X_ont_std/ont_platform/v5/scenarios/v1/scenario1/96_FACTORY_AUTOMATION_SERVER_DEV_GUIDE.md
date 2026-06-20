# Factory Automation Mock Server Development Guide

작성일: 2026-06-13  
대상 구현자: Antigravity  
대상 범위: 공장 반복 고장 시나리오용 고객사/공장 영역 mock 서버  
관련 템플릿: `factory-repeated-fault-response`, `factory.repeated_fault_response.v1`

## 1. 목적

이 문서는 공장 자동화 예시를 실제로 시연하기 위한 공장 쪽 mock 서버 개발 가이드다.

현재 ont_platform v5에는 다음이 준비되어 있다.

- 공장 반복 고장 Workflow Builder 템플릿
- 공장 반복 고장 Workflow-Ontology 매핑 템플릿
- `Factory`, `ProductionLine`, `Equipment`, `FaultEvent`, `MaintenanceTask`, `QualityIssue` 온톨로지 타입

하지만 공장 쪽 입력 서버는 아직 없다.

Antigravity는 이 문서를 기준으로 공장 현장 요청/설비 이벤트 mock 서버를 구현한다.

## 2. 전체 구성

권장 구성:

```text
ont_platform v5
  -> factory_mcp
  -> factory_board
```

또는 초기 단순 구현:

```text
ont_platform v5
  -> factory_board
```

단, 최종 구조는 기존 고객사 게시판과 동일하게 MCP 중계 경계를 둔다.

| 구성 요소 | 권장 디렉터리 | 기본 포트 | 역할 |
| --- | --- | ---: | --- |
| `factory_mcp` | `E:\ontology_edu\X_ont_std\mock_infras\s2_factory_mcp` | 8081 | ont_platform의 tool 호출을 받아 factory_board API로 중계 |
| `factory_board` | `E:\ontology_edu\X_ont_std\mock_infras\s2_factory_board` | 8091 | 공장 현장 요청/설비 이벤트 mock API/UI |
| ont_platform backend | `ont_platform/v5/backend` | 8001 | 워크플로우 실행, 온톨로지 write-back |
| ont_platform frontend | `ont_platform/v5/frontend` | 3002 | Workflow Builder, Workflow Trace, 온톨로지 관리 |

## 3. 핵심 데모 스토리

화면과 API는 아래 세 건을 쉽게 넣을 수 있어야 한다.

### 이벤트 1. 첫 고장

```text
카테고리: 장비 고장
공장: 세종 배터리팩 공장
라인: 3번 조립 라인
공정: 용접 단계
장비: 배터리 탭 용접기
발생 시각: 오전 10시
오류 메시지: 압력이 낮습니다
내용: 오전 10시에 배터리 탭 용접기가 멈췄습니다.
```

기대 처리:

```text
FaultEvent 신규 생성
상태: observed
현장 안내 댓글/응답 생성
```

### 이벤트 2. 반복 고장

```text
카테고리: 장비 고장
공장: 세종 배터리팩 공장
라인: 3번 조립 라인
공정: 용접 단계
장비: 배터리 탭 용접기
발생 시각: 오전 11시
오류 메시지: 압력이 낮습니다
내용: 오전 11시에 같은 장비가 같은 오류로 다시 멈췄습니다.
```

기대 처리:

```text
기존 FaultEvent와 연결
occurrence_count 증가
상태: repeated
MaintenanceTask 생성
정비팀 확인 건으로 승격
```

### 이벤트 3. 품질 문제 연결

```text
카테고리: 품질 문제
공장: 세종 배터리팩 공장
라인: 3번 조립 라인
공정: 검사 단계
장비: 검사 카메라
발생 시각: 오전 11시 40분
내용: 용접기 재가동 이후 검사 카메라에서 불량이 평소보다 많이 잡힙니다.
```

기대 처리:

```text
QualityIssue 생성
최근 FaultEvent와 possibly_caused_by 관계 연결
정비팀 + 품질팀 공동 확인 대상으로 표시
```

## 4. factory_board 기능 요구사항

`factory_board`는 공장 현장 요청을 만들고 조회하는 mock 서버다.

### 필수 UI

브라우저 접속:

```text
http://localhost:8091
```

필수 화면:

- 현장 요청 목록
- 새 현장 요청 등록
- 카테고리 선택
- 공장/라인/공정/장비 선택 또는 입력
- 오류 메시지 입력
- 발생 시각 입력
- 요청 상세
- 처리 결과/댓글 또는 응답 표시
- webhook on/off 토글
- webhook target 설정

### 필수 API

```http
GET /health
GET /api/factory/events
GET /api/factory/events/{event_id}
POST /api/factory/events
GET /api/factory/events/open
POST /api/factory/events/{event_id}/responses
GET /api/settings
POST /api/settings
POST /api/simulate/webhook/{event_id}
```

## 5. DB 설계

SQLite 사용을 권장한다.

DB 파일:

```text
E:\ontology_edu\X_ont_std\mock_infras\s2_factory_board\s2_factory_board.db
```

### 5.1 factory_events

```sql
CREATE TABLE factory_events (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    factory_name TEXT NOT NULL,
    line_name TEXT NOT NULL,
    process_step TEXT NOT NULL,
    equipment_name TEXT NOT NULL,
    fault_message TEXT,
    severity TEXT NOT NULL DEFAULT 'medium',
    occurred_at TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    reporter TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL
);
```

권장 `category`:

```text
equipment_fault
quality_issue
maintenance_request
```

권장 `severity`:

```text
low
medium
high
critical
```

### 5.2 factory_responses

```sql
CREATE TABLE factory_responses (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    response_type TEXT NOT NULL DEFAULT 'comment',
    created_at TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES factory_events (id) ON DELETE CASCADE
);
```

### 5.3 settings

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

필수 설정:

```text
webhook_enabled=true|false
webhook_target=http://localhost:8001/api/extn/factory-events/events
webhook_mode=dry_run|post
```

## 6. API 계약

### 6.1 Health

Request:

```http
GET http://localhost:8091/health
```

Response:

```json
{
  "status": "ok",
  "service": "factory_board"
}
```

### 6.2 Create Factory Event

Request:

```http
POST /api/factory/events
Content-Type: application/json
```

```json
{
  "category": "equipment_fault",
  "factory_name": "세종 배터리팩 공장",
  "line_name": "3번 조립 라인",
  "process_step": "용접 단계",
  "equipment_name": "배터리 탭 용접기",
  "fault_message": "압력이 낮습니다",
  "severity": "high",
  "occurred_at": "2026-06-13T10:00:00+09:00",
  "title": "배터리 탭 용접기 압력 낮음 오류",
  "content": "오전 10시에 배터리 탭 용접기가 멈췄습니다. 화면에 압력이 낮습니다라는 오류가 떴습니다.",
  "reporter": "라인 작업자"
}
```

Response:

```json
{
  "id": "fe-001",
  "status": "open",
  "webhook": {
    "enabled": true,
    "status": "sent",
    "target": "http://localhost:8001/api/extn/factory-events/events"
  }
}
```

### 6.3 List Open Events

Request:

```http
GET /api/factory/events/open?limit=20
```

Response:

```json
{
  "items": [
    {
      "id": "fe-001",
      "category": "equipment_fault",
      "factory_name": "세종 배터리팩 공장",
      "line_name": "3번 조립 라인",
      "process_step": "용접 단계",
      "equipment_name": "배터리 탭 용접기",
      "fault_message": "압력이 낮습니다",
      "severity": "high",
      "occurred_at": "2026-06-13T10:00:00+09:00",
      "title": "배터리 탭 용접기 압력 낮음 오류",
      "content": "오전 10시에 배터리 탭 용접기가 멈췄습니다.",
      "reporter": "라인 작업자",
      "status": "open",
      "created_at": "2026-06-13T10:01:00+09:00"
    }
  ]
}
```

### 6.4 Add Response

Request:

```http
POST /api/factory/events/{event_id}/responses
Content-Type: application/json
```

```json
{
  "author": "ontology-workflow",
  "content": "같은 장비에서 같은 문제가 반복 접수되었습니다. 정비팀 확인 건으로 올리겠습니다.",
  "response_type": "comment"
}
```

Response:

```json
{
  "id": "fr-001",
  "event_id": "fe-001",
  "status": "created"
}
```

## 7. Webhook 계약

`factory_board`는 새 이벤트 등록 시 webhook이 켜져 있으면 ont_platform에 이벤트를 전송한다.

Target:

```text
POST http://localhost:8001/api/extn/factory-events/events
```

Headers:

```http
Content-Type: application/json
X-Company-Id: demo-co
X-Project-Id: proj-01
X-User-Id: factory-board
```

Payload:

```json
{
  "event_id": "evt-fe-001",
  "event_type": "factory_event.created",
  "factory_event_id": "fe-001",
  "category": "equipment_fault",
  "factory_name": "세종 배터리팩 공장",
  "line_name": "3번 조립 라인",
  "process_step": "용접 단계",
  "equipment_name": "배터리 탭 용접기",
  "fault_message": "압력이 낮습니다",
  "severity": "high",
  "occurred_at": "2026-06-13T10:00:00+09:00",
  "title": "배터리 탭 용접기 압력 낮음 오류",
  "content": "오전 10시에 배터리 탭 용접기가 멈췄습니다.",
  "reporter": "라인 작업자",
  "mode": "post",
  "metadata": {
    "source": "factory_board"
  }
}
```

주의:

- ont_platform의 factory endpoint는 다음 단계에서 구현된다.
- 지금은 factory_board 쪽에서 webhook 송신 구조와 실패 로그를 먼저 구현한다.
- ont_platform이 꺼져 있어도 이벤트 등록 자체는 성공해야 한다.

## 8. factory_mcp 기능 요구사항

`factory_mcp`는 ont_platform이 공장 시스템에 직접 접근하지 않도록 하는 중계 서버다.

필수 endpoint:

```http
GET /health
POST /mcp/tools/factory_event.list
POST /mcp/tools/factory_response.create
POST /mcp/tools/maintenance_task.create
```

### 8.1 factory_event.list

Request:

```json
{
  "request_id": "uuid",
  "company_id": "demo-co",
  "project_id": "proj-01",
  "mode": "dry_run",
  "tool": "factory_event.list",
  "arguments": {
    "status": "open",
    "limit": 20
  },
  "metadata": {
    "source": "ont_platform_v5"
  }
}
```

Response:

```json
{
  "request_id": "uuid",
  "status": "success",
  "tool": "factory_event.list",
  "result": {
    "items": []
  },
  "error": null
}
```

### 8.2 factory_response.create

Request:

```json
{
  "request_id": "uuid",
  "company_id": "demo-co",
  "project_id": "proj-01",
  "mode": "post",
  "tool": "factory_response.create",
  "arguments": {
    "event_id": "fe-001",
    "message": "같은 장비에서 같은 문제가 반복 접수되었습니다. 정비팀 확인 건으로 올리겠습니다.",
    "author": "ontology-workflow"
  },
  "metadata": {
    "workflow_run_id": "run-001",
    "source": "ont_platform_v5"
  }
}
```

Response:

```json
{
  "request_id": "uuid",
  "status": "success",
  "tool": "factory_response.create",
  "result": {
    "external_response_id": "fr-001",
    "external_event_id": "fe-001",
    "url": "http://localhost:8091/events/fe-001#response-fr-001"
  },
  "error": null
}
```

### 8.3 maintenance_task.create

Request:

```json
{
  "request_id": "uuid",
  "company_id": "demo-co",
  "project_id": "proj-01",
  "mode": "post",
  "tool": "maintenance_task.create",
  "arguments": {
    "factory_event_id": "fe-002",
    "equipment_name": "배터리 탭 용접기",
    "fault_message": "압력이 낮습니다",
    "assigned_team": "정비팀",
    "priority": "high",
    "message": "2시간 내 동일 장비 동일 오류가 반복되었습니다."
  },
  "metadata": {
    "workflow_run_id": "run-001",
    "source": "ont_platform_v5"
  }
}
```

Response:

```json
{
  "request_id": "uuid",
  "status": "success",
  "tool": "maintenance_task.create",
  "result": {
    "external_task_id": "mt-001",
    "external_event_id": "fe-002",
    "assigned_team": "정비팀"
  },
  "error": null
}
```

## 9. Dry-run 규칙

모든 MCP tool은 `mode=dry_run`을 지원해야 한다.

Dry-run일 때:

- DB에 response/task를 저장하지 않는다.
- 저장했을 경우의 결과 형태를 미리 반환한다.
- `status`는 `dry_run`으로 반환한다.

예:

```json
{
  "request_id": "uuid",
  "status": "dry_run",
  "tool": "maintenance_task.create",
  "result": {
    "external_task_id": null,
    "would_create": true
  },
  "error": null
}
```

## 10. Error 규격

공통 error response:

```json
{
  "request_id": "uuid",
  "status": "error",
  "tool": "factory_response.create",
  "result": null,
  "error": {
    "code": "FACTORY_BOARD_ERROR",
    "message": "factory_board 호출 실패",
    "retryable": true
  }
}
```

권장 error code:

| Code | Meaning | Retryable |
| --- | --- | --- |
| `INVALID_REQUEST` | 필수 필드 누락 또는 값 오류 | false |
| `EVENT_NOT_FOUND` | 대상 event 없음 | false |
| `FACTORY_BOARD_ERROR` | factory_board 호출 실패 | true |
| `FACTORY_TIMEOUT` | factory_board timeout | true |
| `TOOL_NOT_FOUND` | 지원하지 않는 tool | false |
| `INTERNAL_ERROR` | 예상하지 못한 오류 | true |

## 11. 시드 데이터

서버 시작 시 아래 데이터를 기본으로 넣는다.

### 마스터 데이터

```text
Factory: 세종 배터리팩 공장
ProductionLine: 3번 조립 라인
ProcessStep: 용접 단계
ProcessStep: 검사 단계
Equipment: 배터리 탭 용접기
Equipment: 검사 카메라
```

### 샘플 이벤트

기본 이벤트 1건만 넣고, 반복 시나리오는 UI 버튼으로 추가하는 방식을 권장한다.

```text
오전 10시 배터리 탭 용접기 압력 낮음 오류
```

UI 버튼:

```text
샘플 1: 첫 고장 생성
샘플 2: 반복 고장 생성
샘플 3: 품질 문제 생성
```

## 12. ont_platform 연동 예정 사항

Antigravity는 공장 서버를 먼저 개발하고, ont_platform 쪽은 이후 다음 기능을 붙인다.

예정 endpoint:

```http
POST /api/extn/factory-events/events
POST /api/extn/factory-events/batch/run-once
POST /api/extn/factory-responses/generate-and-post
```

예정 writer:

```text
backend/app/services/factory_ontology_writer.py
```

예정 온톨로지 문서:

```text
storage/{company_id}/{project_id}/ontology/factory-repeated-faults.json
```

## 13. 완료 기준

Antigravity 구현 완료 기준:

- `factory_board` 8091 기동
- `factory_mcp` 8081 기동
- UI에서 샘플 이벤트 3건 생성 가능
- 이벤트 목록/상세 확인 가능
- response 등록 가능
- maintenance task 생성 가능
- webhook on/off 가능
- ont_platform이 꺼져 있어도 이벤트 등록은 성공
- MCP dry_run/post 둘 다 동작
- API response에 `request_id`가 그대로 반환
- README에 실행 명령과 포트 충돌 대처 방법 포함

## 14. 실행 명령 예시

권장 conda env는 기존 서버와 맞춘다.

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\mock_infras\s2_factory_board
python main.py
```

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\mock_infras\s2_factory_mcp
python main.py
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8091/health
Invoke-RestMethod http://127.0.0.1:8081/health
```

## 15. 구현 시 주의사항

- `ont_platform`은 공장 board를 직접 호출하지 않는 구조로 간다.
- `factory_mcp`를 통해서만 response/task를 생성하게 한다.
- webhook 실패는 이벤트 등록 실패로 처리하지 않는다.
- 한글 데이터는 UTF-8로 저장한다.
- 시간은 ISO 8601 문자열을 사용한다.
- `mode=dry_run`은 반드시 실제 저장 없이 동작한다.
- 같은 이벤트에 중복 response/task가 생기지 않도록 idempotency key를 고려한다.

## 16. ont_platform v5 구현 완료 경로

2026-06-13 기준으로 ont_platform v5에는 공장 반복 고장 시나리오 실행 경로가 구현되어 있다.

### 호출 경계

ont_platform는 `s2_factory_board`를 직접 호출하지 않는다.

```text
ont_platform v5 backend :8001
  -> s2_factory_mcp :8081
  -> s2_factory_board :8091
```

실제 호출되는 MCP tool:

```text
factory_event.list
factory_response.create
maintenance_task.create
```

### ont_platform API

```http
POST /api/extn/factory-events/events
POST /api/extn/factory-events/batch/run-once
```

PowerShell 수동 배치 실행 예:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8001/api/extn/factory-events/batch/run-once" `
  -Method Post `
  -Headers @{
    "Content-Type" = "application/json"
    "X-Company-Id" = "demo-co"
    "X-Project-Id" = "proj-01"
    "X-User-Id" = "factory-admin"
  } `
  -Body '{"status":"open","mode":"post","limit":10,"force_reprocess":false}'
```

### Workflow Builder 실행

1. `공장 반복 고장 대응` 템플릿을 복제한다.
2. 복제된 워크플로우를 선택한다.
3. 실행 모드가 `post`인지 확인한다.
4. `Run`을 누르면 backend가 `/api/extn/factory-events/batch/run-once`와 같은 실행기를 사용한다.
5. 실행 결과는 `s2_factory_mcp`를 통해 8091 게시판에 댓글/정비지시로 등록된다.

### 온톨로지 write-back

실행 결과는 회사/프로젝트별 온톨로지 문서에 저장된다.

```text
storage/{company_id}/{project_id}/ontology/factory-repeated-faults.json
```

주요 객체:

```text
Factory
ProductionLine
ProcessStep
Equipment
ServiceRequest
FaultEvent
MaintenanceTask
QualityIssue
```

주요 관계:

```text
has_line
has_step
uses
reports
affects
creates
possibly_caused_by
```

### 화면 확인

`Workflow-Ontology Trace` 화면에서 고객 자동댓글 워크플로우뿐 아니라 `factory.repeated_fault_response` 실행 이력도 선택할 수 있다.
공장 실행을 선택하면 `factory-repeated-faults` 문서의 공장, 라인, 공정, 설비, 고장, 정비지시 객체 흐름을 확인한다.

### 서버 재기동 주의

이미 8001 서버가 떠 있는 상태에서 코드가 변경되었다면 ont_platform backend를 재기동해야 새 route가 로딩된다.
재기동 전에는 `/api/extn/factory-events/...` 호출이 404로 보일 수 있다.
