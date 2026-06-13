# Workflow-Ontology Trace 설계

작성일: 2026-06-13  
대상: Scenario 1 고객 문의 자동댓글, Workflow Builder, Ontology Explorer  
목적: 워크플로우 실행 내용을 온톨로지 객체/관계로 저장하고, 워크플로우와 온톨로지 흐름을 쉽게 볼 수 있게 한다.

## 1. 배경

현재 Scenario 1은 다음 흐름까지 구현되어 있다.

```text
customer_board 문의
  -> webhook 또는 batch trigger
  -> Workflow Builder graph 실행
  -> draft 생성
  -> customer_mcp 호출
  -> customer_board 댓글 등록
  -> workflow_runs / event state / audit 저장
```

하지만 현재 저장은 주로 로그와 실행 이력 중심이다.

```text
workflow_runs/*.json
events/customer_question_events.jsonl
events/customer_question_state.json
audit/customer_mcp_calls.jsonl
```

이것은 감사와 디버깅에는 충분하지만, 팔란티어식 업무 온톨로지 관점에서는 부족하다.

업무적으로는 고객 문의, 자동답변, 댓글, 워크플로우 실행이 각각 객체가 되고, 서로 관계로 연결되어야 한다.

## 2. 왜 온톨로지로 저장하는가

DB/log 저장만으로도 이벤트 보관은 가능하다.

온톨로지로 저장하는 이유는 다음이다.

| 목적 | DB/log 중심 | 온톨로지 중심 |
| --- | --- | --- |
| 저장 | row/event로 보관 | 업무 객체로 보관 |
| 의미 | 테이블/필드 해석 필요 | `ServiceRequest`, `AutoReply` 등 명시 |
| 관계 | 조인/쿼리 필요 | 객체 관계로 탐색 |
| 상태 | 화면별 구현 필요 | 객체 상태 변화로 관리 |
| 자동화 | if문/쿼리 증가 | 객체/관계/정책 기반 조건 |
| AI 맥락 | 텍스트 중심 | 객체, 관계, 과거 이력, 정책을 함께 제공 |
| 운영 화면 | 별도 대시보드 필요 | 온톨로지 탐색/워크플로우 화면에서 연결 |

정리:

```text
로그는 증거이고,
온톨로지 객체는 업무 상태 모델이다.
```

## 3. 우선순위

현재 우선순위는 "자동 댓글 기능 확장"보다 "워크플로우 실행 내용을 온톨로지에 남기고 흐름을 보여주는 것"을 먼저 둔다.

### P0. Workflow 실행 결과를 온톨로지 객체로 저장

목표:

- 고객 문의가 `ServiceRequest` 객체로 저장된다.
- 워크플로우 실행이 `WorkflowExecution` 객체로 저장된다.
- 생성 답변이 `AutoReply` 객체로 저장된다.
- 실제 게시판 댓글이 `ExternalComment` 객체로 저장된다.
- 객체 간 관계가 저장된다.

완료 기준:

- Workflow Builder에서 `Run`을 실행하면 온톨로지 객체/관계가 생성 또는 갱신된다.
- 온톨로지 Explorer에서 해당 문의와 실행 흐름을 조회할 수 있다.
- 기존 로그/audit도 계속 남는다.

### P0-A. Workflow-Ontology 매핑 템플릿

Workflow와 Ontology는 바로 연결하지 않고, 중간에 "매핑 템플릿"을 둔다.

이유:

- 같은 워크플로우를 회사/프로젝트별로 다른 온톨로지 모델에 연결할 수 있어야 한다.
- 워크플로우 복제 후에도 어떤 노드가 어떤 업무 객체를 만들지 확인하고 수정할 수 있어야 한다.
- 하드코딩된 writer만 있으면 화면에서 관계도를 설명하거나 변경하기 어렵다.

현재 Scenario 1의 기본 매핑 템플릿:

```text
backend/app/config/workflow_ontology_mappings/scenario1_customer_question_auto_reply.json
```

주요 매핑:

| Workflow node | Ontology object | 설명 |
| --- | --- | --- |
| `request-input` | `ServiceRequest` | 고객 문의/서비스 요청 객체 생성 또는 갱신 |
| `draft-response` | `AutoReply` | 자동 답변 객체 생성 |
| `post-comment` | `ExternalComment` | 고객사 게시판 댓글 결과 객체 생성 |
| `audit-write` | `WorkflowExecution` | 워크플로우 실행 이력 객체 생성 |

관계도:

```text
ServiceRequest
  -- handled_by --> WorkflowExecution
WorkflowExecution
  -- generated --> AutoReply
AutoReply
  -- posted_as --> ExternalComment
ServiceRequest
  -- has_reply --> AutoReply
```

설정 과정:

1. Workflow Builder에서 시스템 템플릿을 프로젝트 워크플로우로 복제한다.
2. Workflow-Ontology 매핑 템플릿을 선택한다.
3. 매핑 템플릿의 entity/relation type을 프로젝트 온톨로지 스키마에 설치한다.
4. 노드별 필드 매핑을 확인한다.
5. `dry_run`으로 온톨로지 기록을 검증한 뒤 `post`로 실제 댓글 등록까지 실행한다.

제공 API:

| API | 용도 |
| --- | --- |
| `GET /api/workflow-ontology-mappings` | 사용 가능한 매핑 템플릿 목록 조회 |
| `GET /api/workflow-ontology-mappings/{mapping_id}` | 매핑 상세 조회 |
| `POST /api/workflow-ontology-mappings/{mapping_id}/install-schema` | 프로젝트 온톨로지 스키마에 타입/관계 설치 |

### P1. Workflow-Ontology Trace 화면

목표:

- WorkflowRun 화면에서 관련 온톨로지 객체를 보여준다.
- ServiceRequest 상세에서 처리한 WorkflowExecution, AutoReply, ExternalComment를 보여준다.
- 그래프 형태로 흐름을 본다.

완료 기준:

```text
ServiceRequest
  -> handled_by WorkflowExecution
  -> generated AutoReply
  -> posted_as ExternalComment
```

이 관계를 화면에서 확인할 수 있다.

### P2. 정책/권한/AI 판단과 온톨로지 연결

목표:

- VIP 고객, 보안 요청, 근거 부족 등 조건을 온톨로지 객체/관계 기반으로 판단한다.
- 자동 `post` 가능 여부를 객체 상태와 정책으로 결정한다.
- AI 답변에 관련 과거 요청, 정책, 고객 상태를 함께 제공한다.

## 4. 최소 온톨로지 모델

### 4.1 Object Types

#### ServiceRequest

고객사 게시판 문의를 업무 요청 객체로 표현한다.

```json
{
  "id": "sr-q-1400af0f",
  "type": "ServiceRequest",
  "name": "비밀번호 초기화 요청",
  "properties": {
    "external_id": "q-1400af0f",
    "source_system": "customer_board",
    "source_channel": "web",
    "status": "replied",
    "title": "비밀번호 초기화 요청",
    "content": "관리자 계정 비밀번호를 분실했습니다.",
    "requester": "홍길동",
    "created_at": "2026-06-13T07:14:03Z",
    "last_processed_at": "2026-06-13T07:22:00Z"
  }
}
```

상태:

```text
open
drafted
replied
failed
closed
handoff
```

#### WorkflowExecution

워크플로우 그래프 실행 1회를 업무 실행 객체로 표현한다.

```json
{
  "id": "wfe-run-cf6c64e2a1dc",
  "type": "WorkflowExecution",
  "name": "서비스 요청 자동댓글 실행",
  "properties": {
    "run_id": "run-cf6c64e2a1dc",
    "graph_id": "wfg-7a73426dac06",
    "graph_name": "서비스 요청 자동댓글 - 테스트2",
    "executor": "scenario1.customer_question_auto_reply",
    "mode": "post",
    "status": "succeeded",
    "started_at": "2026-06-13T07:22:00Z",
    "finished_at": "2026-06-13T07:22:05Z"
  }
}
```

#### AutoReply

LLM/RAG/룰로 생성된 답변 초안을 표현한다.

```json
{
  "id": "reply-q-1400af0f-run-cf6c64e2a1dc",
  "type": "AutoReply",
  "name": "자동 답변",
  "properties": {
    "message": "안녕하세요. 문의 주신 계정/비밀번호 관련 요청을 확인했습니다...",
    "mode": "post",
    "status": "posted",
    "confidence": 0.5,
    "generated_by": "llm_webhook",
    "created_at": "2026-06-13T07:22:00Z"
  }
}
```

#### ExternalComment

고객사 게시판에 실제 등록된 댓글을 표현한다.

```json
{
  "id": "ext-comment-a2e6aaf8",
  "type": "ExternalComment",
  "name": "customer_board 댓글",
  "properties": {
    "external_comment_id": "comment-a2e6aaf8",
    "external_thread_id": "q-1400af0f",
    "url": "http://localhost:8090/posts/q-1400af0f#comment-comment-a2e6aaf8",
    "source_system": "customer_board",
    "status": "success",
    "posted_at": "2026-06-13T07:22:00Z"
  }
}
```

### 4.2 Relationship Types

```text
ServiceRequest --handled_by--> WorkflowExecution
WorkflowExecution --generated--> AutoReply
AutoReply --posted_as--> ExternalComment
ServiceRequest --has_reply--> AutoReply
WorkflowExecution --called--> CustomerMcpCall
```

P0에서는 `CustomerMcpCall`을 별도 객체로 만들지 않고 audit reference만 properties에 저장해도 된다.

## 5. 저장 방식

기존 온톨로지 저장 방식에 맞춰 프로젝트별 ontology JSON에 저장한다.

권장 파일:

```text
storage/{company_id}/{project_id}/ontology/service-requests.json
```

구조:

```json
{
  "doc_id": "service-requests",
  "domain": "scenario1",
  "entities": [],
  "relationships": []
}
```

기존 `OntologyService`/repository와 호환되도록 `entities`, `relationships` 배열 구조를 사용한다.

## 6. Workflow 실행 시 Write-back 시점

WorkflowGraph runner에서 Scenario 1 실행 후 온톨로지 write-back을 수행한다.

```text
_run_scenario1_customer_reply_stream
  -> _run_batch_once
  -> batch_result.items 순회
  -> ServiceRequest upsert
  -> WorkflowExecution upsert
  -> AutoReply upsert
  -> ExternalComment upsert
  -> relationships upsert
  -> WorkflowRun 저장
```

write-back 실패 정책:

- 댓글 등록 성공 후 ontology write-back 실패는 전체 댓글 등록을 rollback하지 않는다.
- WorkflowRun에는 `ontology_writeback_status=failed`를 남긴다.
- 재처리 API 또는 다음 batch에서 보정 가능하게 한다.

## 7. 화면 설계

### 7.1 Workflow Builder

Run 완료 후 보여줄 정보:

```text
처리 문의 수
댓글 등록 수
온톨로지 객체 생성/갱신 수
온톨로지 Trace 보기 버튼
```

버튼:

```text
View Ontology Trace
```

동작:

- 관련 `ServiceRequest` 객체를 열거나
- Workflow-Ontology Trace 패널을 연다.

### 7.2 Ontology Explorer

`ServiceRequest` 타입 필터 추가.

표시:

- 요청 제목
- 상태
- 외부 게시판 ID
- 마지막 처리 시간
- 관련 WorkflowExecution
- 관련 AutoReply
- 관련 ExternalComment

### 7.3 Trace Graph

간단한 그래프:

```text
[ServiceRequest]
      |
      handled_by
      v
[WorkflowExecution]
      |
      generated
      v
[AutoReply]
      |
      posted_as
      v
[ExternalComment]
```

## 8. 변경 대상 프로그램

### Backend

| Program | 변경 |
| --- | --- |
| `app/services/workflow_ontology_writer.py` | 신규. ServiceRequest/WorkflowExecution/AutoReply/ExternalComment upsert |
| `app/config/workflow_ontology_mappings/scenario1_customer_question_auto_reply.json` | 신규. Scenario 1 노드-온톨로지 매핑 템플릿 |
| `app/services/workflow_ontology_mapping_service.py` | 신규. 매핑 템플릿 조회 및 프로젝트 스키마 설치 |
| `app/api/workflow_ontology_mappings.py` | 신규. 매핑 템플릿 API |
| `app/api/workflow.py` | Scenario 1 runner 종료 후 ontology writer 호출 |
| `app/services/workflow.py` | WorkflowRun output에 ontology write-back 결과 저장 |
| `app/repositories/ontology.py` | 필요 시 entity/relationship upsert helper 추가 |
| `app/models/ontology.py` | 필요 시 서비스 요청 타입 모델 추가 |

### Frontend

| Program | 변경 |
| --- | --- |
| `components/WorkflowGraph.tsx` | Run 결과에 ontology write-back summary 표시 |
| `components/WorkflowRunHistory.tsx` | run별 ontology refs 표시 |
| `components/OntologyExplorer.tsx` | `ServiceRequest` 타입 탐색 강화 |
| 신규 `components/WorkflowOntologyTrace.tsx` | ServiceRequest -> WorkflowExecution -> AutoReply -> ExternalComment 흐름 표시 |

### Storage

| Path | 변경 |
| --- | --- |
| `storage/{company}/{project}/ontology/domain_schema.json` | 매핑 템플릿 설치 시 ServiceRequest/WorkflowExecution/AutoReply/ExternalComment 타입과 관계 추가 |
| `storage/{company}/{project}/ontology/service-requests.json` | 신규 또는 자동 생성 |
| `storage/{company}/{project}/workflow_runs/*.json` | ontology refs 추가 |
| `storage/{company}/{project}/audit/customer_mcp_calls.jsonl` | audit_id를 ontology refs와 연결 |

## 9. 구현 우선순위 상세

### P0-1. Ontology writer 신규 구현

가장 먼저 한다.

이유:

- 화면보다 데이터가 먼저 있어야 한다.
- 워크플로우 실행 결과가 온톨로지에 남는지 확인해야 한다.

### P0-2. Workflow runner와 writer 연결

두 번째로 한다.

이유:

- Workflow Builder에서 Run을 눌렀을 때 온톨로지 변화가 생겨야 한다.

### P0-3. 최소 조회 API/Explorer 확인

세 번째로 한다.

이유:

- 저장된 객체를 운영자가 확인할 수 있어야 한다.

### P1-1. Workflow-Ontology Trace 컴포넌트

P0 이후 한다.

이유:

- P0 데이터가 있어야 시각화가 의미 있다.

### P1-2. WorkflowRunHistory에 ontology refs 표시

Trace 컴포넌트와 함께 한다.

### P2. 정책/AI 판단 고도화

마지막에 한다.

## 10. 완료 기준

P0 완료 기준:

- Workflow Builder에서 Scenario 1 그래프 Run 실행
- 고객 게시판 댓글 등록
- `service-requests.json`에 ServiceRequest/WorkflowExecution/AutoReply/ExternalComment 저장
- 관계 4종 저장
- 같은 question_id 재실행 시 ServiceRequest가 중복 생성되지 않고 갱신
- WorkflowRun 결과에 ontology write-back summary 포함

P1 완료 기준:

- 화면에서 워크플로우 실행 결과와 온톨로지 객체 흐름을 함께 볼 수 있음
- ServiceRequest에서 관련 WorkflowExecution/AutoReply/ExternalComment로 이동 가능

P2 완료 기준:

- 온톨로지 객체 상태/관계에 따라 자동 post, human handoff, approval gate가 달라짐
