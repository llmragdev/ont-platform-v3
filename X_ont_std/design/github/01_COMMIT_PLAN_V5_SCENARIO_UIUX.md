# v5 시나리오/UIUX 작업 커밋 계획

작성일: 2026-06-13  
작성자: Codex  
대상 repo root: `E:\ontology_edu`

## 1. 배경

현재 `git status` 기준으로 변경 사항이 여러 작업 범위에 섞여 있다.

이번 대화에서 주로 진행한 작업은 다음 범위다.

- `ont_platform/v5` 시나리오 1/2 워크플로우 구현 보완
- 고객사 자동댓글 및 공장 반복 고장 대응 워크플로우 연동
- `s1_customer_*`, `s2_factory_*` mock board/MCP 서버 구성
- 워크플로우/온톨로지 UI/UX 개선 기획 문서 작성

반면 현재 working tree에는 다음과 같은 unrelated 변경도 함께 보인다.

- `ont_platform/v3/storage/...`
- `ont_platform/v4/...`
- `X_rag_std/...`
- `status_reports/...` 삭제/이동
- 평가/리포트 생성 스크립트
- 오래된 storage/vector DB 변경

따라서 전체 커밋은 금지하고, 작업 목적별로 명시적으로 path를 골라 커밋한다.

## 2. 커밋 원칙

1. 이번 커밋에는 `X_ont_std` 내부의 v5 시나리오/UIUX 관련 작업만 포함한다.
2. `X_rag_std` 변경은 포함하지 않는다.
3. `ont_platform/v3`, `ont_platform/v4` 변경은 포함하지 않는다.
4. storage, vector DB, runtime log, cache, `.pytest_cache`, `node_modules`는 포함하지 않는다.
5. 고객사 mock 서버는 기능 커밋과 분리한다.
6. UI/UX 문서는 기능 커밋과 분리한다.
7. 커밋 전 `git diff --cached --stat`으로 staged 파일을 확인한다.

## 3. 권장 커밋 분리

### Commit 1. mock 서버 추가

목적:

고객사 게시판/MCP, 공장 게시판/MCP mock 서비스를 독립적으로 추가한다.

대상 경로:

```text
X_ont_std/s1_customer_board/
X_ont_std/s1_customer_mcp/
X_ont_std/s2_factory_board/
X_ont_std/s2_factory_mcp/
```

제외 후보:

```text
**/__pycache__/
**/.pytest_cache/
**/*.db
**/*.sqlite
**/*.sqlite3
**/node_modules/
**/logs/
```

커밋 메시지:

```text
feat(mock): add customer and factory board MCP services
```

검증:

```powershell
Invoke-RestMethod http://127.0.0.1:8081/health
Invoke-RestMethod http://127.0.0.1:8091/api/health
```

비고:

사용자가 "고객사 쪽은 건드리지 말라"고 한 이후에는 mock 서버 변경을 실행하지 않았다.
다만 repo에 새 mock 서버가 untracked로 잡혀 있으므로, 커밋 여부는 별도 확인 후 진행한다.

### Commit 2. ont_platform v5 시나리오/워크플로우 구현

목적:

v5에서 고객 자동댓글 및 공장 반복 고장 대응 워크플로우를 실행 가능하게 하고, MCP 호출과 온톨로지 write-back을 연결한다.

대상 경로:

```text
X_ont_std/ont_platform/v5/backend/
X_ont_std/ont_platform/v5/frontend/
X_ont_std/ont_platform/v5/scenarios/
X_ont_std/ont_platform/v5/config/
X_ont_std/ont_platform/v5/scripts/
X_ont_std/ont_platform/v5/RUNBOOK.md
X_ont_std/ont_platform/v5/README.md
```

핵심 포함 파일 예:

```text
backend/app/api/extn/factory_events.py
backend/app/extn/factory_mcp_client.py
backend/app/services/factory_event_state.py
backend/app/services/factory_ontology_writer.py
backend/app/api/workflow.py
backend/app/config/workflow_templates/factory_repeated_fault_response.json
backend/app/config/workflow_ontology_mappings/factory_repeated_fault_response.json
frontend/src/components/WorkflowGraph.tsx
frontend/src/components/WorkflowOntologyTrace.tsx
backend/tests/test_workflow_ontology_writer.py
backend/tests/test_workflow_templates.py
```

제외 후보:

```text
X_ont_std/ont_platform/v5/.pytest_cache/
X_ont_std/ont_platform/v5/frontend/node_modules/
X_ont_std/ont_platform/v5/storage/
X_ont_std/ont_platform/v5/**/__pycache__/
X_ont_std/ont_platform/v5/**/*.pyc
X_ont_std/ont_platform/v5/**/*.db
X_ont_std/ont_platform/v5/**/*.sqlite
X_ont_std/ont_platform/v5/**/*.sqlite3
```

커밋 메시지:

```text
feat(v5): add factory workflow MCP integration and ontology trace
```

검증:

```powershell
cd E:\ontology_edu\X_ont_std\ont_platform\v5
pytest backend\tests\test_workflow_templates.py backend\tests\test_workflow_ontology_writer.py backend\tests\test_workflow_ontology_mapping_service.py -q

cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npx tsc --noEmit
```

확인된 상태:

- 고객 자동댓글은 동작 확인됨.
- 공장 워크플로우 실행 후 `s2_factory_mcp` 경유로 댓글/정비지시 등록 확인됨.
- 한글 깨짐 일부는 Workflow Builder/공장 템플릿에서 보정함.

### Commit 3. UI/UX 개선 기획 문서

목적:

v5 기능 안정화 이후 진행할 v5.1 UI/UX 개선 방향과 커밋/문서 관리 기준을 남긴다.

대상 경로:

```text
X_ont_std/design/UI_UX개선/
X_ont_std/design/github/
```

핵심 포함 파일:

```text
design/UI_UX개선/UI_UX_개선안_및_참고웹사이트.md
design/UI_UX개선/02_CODEX_REVIEW_OF_01_WORKFLOW_BUILDER_UX.md
design/github/01_COMMIT_PLAN_V5_SCENARIO_UIUX.md
```

주의:

`01_WORKFLOW_BUILDER_UX_IMPROVEMENT_PLAN.md`는 Claude 작성 원안이므로 덮어쓰지 않는다.
Codex는 별도 `02` 검토 문서로 의견을 남겼다.

커밋 메시지:

```text
docs(uiux): add v5 workflow and ontology UX improvement plan
```

검증:

```powershell
rg -n "작성자: Codex|Workflow Builder|Workflow Trace|온톨로지" E:\ontology_edu\X_ont_std\design\UI_UX개선
```

## 4. 이번 커밋에서 제외할 항목

다음 항목은 이번 작업과 직접 관련이 없으므로 커밋하지 않는다.

```text
X_ont_std/ont_platform/v3/storage/
X_ont_std/ont_platform/v4/
X_ont_std/status_reports/
X_rag_std/
AI_TASK_CONTROL/
reports/
X_ont_std/evaluation_framework/
X_ont_std/generate_*.py
X_ont_std/analyze_and_generate_excel.py
```

특히 `status_reports` 삭제 항목은 의도 확인 전까지 절대 stage하지 않는다.

## 5. 실제 커밋 전 확인 명령

### 전체 상태 확인

```powershell
cd E:\ontology_edu
git status --short
```

### staged 파일 확인

```powershell
git diff --cached --stat
git diff --cached --name-only
```

### 실수 방지

아래 명령은 사용하지 않는다.

```powershell
git add .
git add -A
```

대신 path를 명시해서 stage한다.

예:

```powershell
git add X_ont_std/design/UI_UX개선 X_ont_std/design/github
```

## 6. 권장 실행 순서

1. UI/UX 문서 커밋부터 진행한다.
   - 위험이 가장 낮다.
   - 현재 사용자의 요청과 직접 연결된다.

2. v5 구현 커밋을 진행한다.
   - 테스트를 다시 돌린 뒤 커밋한다.
   - storage/cache 제외를 확인한다.

3. mock 서버 커밋은 사용자 확인 후 진행한다.
   - 고객사 mock 서버는 외부 시스템 성격이 있으므로 별도 판단한다.

권장 순서:

```text
docs(uiux)
  -> feat(v5)
  -> feat(mock)
```

## 7. 최종 판단

지금은 커밋하기 좋은 시점이다.
다만 전체 working tree가 넓게 오염되어 있으므로, 반드시 선택 커밋으로 진행해야 한다.

가장 안전한 첫 커밋은 다음이다.

```text
docs(uiux): add v5 workflow and ontology UX improvement plan
```

그 다음에 v5 구현 커밋을 진행하는 것이 좋다.
