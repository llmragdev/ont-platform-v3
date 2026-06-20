# 스킬 시스템 구현 내역

- 작성자: Codex
- 작성일: 2026-06-14
- 대상 범위: `ont_platform/v5` 스킬 시스템 백엔드, 프론트엔드, 워크플로우 연동
- 목적: 스킬 시스템 도입을 위해 수정 또는 추가한 프로그램 내역과 구현 내용을 정리한다.

---

## 1. 구현 요약

이번 구현은 워크플로우 빌더에 “재사용 가능한 실행 기능”인 스킬 개념을 연결하기 위한 1차 구현입니다.

주요 구현 방향은 다음과 같습니다.

```text
스킬 카탈로그
  -> Built-in / Custom Skill 조회
  -> 워크플로우 Skill 노드로 설치
  -> Skill 노드 실행 시 inputMapping 표현식 렌더링
  -> builtin / http / mcp_http 실행
  -> 실행 결과를 WorkflowRun 이력과 노드 입출력 화면에 표시
```

Phase 1 기준으로 Custom Code 실행은 제한했습니다.

---

## 2. 주요 기능 구현 내역

### 2.1 스킬 데이터 모델 추가

스킬 정의를 위한 백엔드 모델을 추가했습니다.

지원하는 구현 타입:

- `builtin`
- `http`
- `mcp_http`
- `custom`

`mcp_http`는 현재 v5의 고객사/공장 MCP 중계 서버 구조에 맞춘 타입입니다.

주요 필드:

- `id`
- `name`
- `description`
- `category`
- `version`
- `inputSchema`
- `outputSchema`
- `requiredCredentials`
- `implementation`
- `mcpConfig`
- `auth`

대상 파일:

```text
ont_platform/v5/backend/app/models/skill.py
```

---

### 2.2 Built-in Skill 카탈로그 추가

시스템 기본 스킬 카탈로그를 추가했습니다.

현재 등록된 Built-in Skill:

| Skill ID | 이름 | 구현 타입 | 용도 |
|---|---|---|---|
| `customer-comment-create` | 고객 게시판 댓글 등록 | `mcp_http` | 고객 문의 자동댓글 |
| `factory-comment-create` | 공장 게시판 댓글 등록 | `mcp_http` | 공장 현장 요청 댓글 |
| `factory-maintenance-create` | 정비 지시 생성 | `mcp_http` | 공장 정비 지시 |
| `ontology-write` | 온톨로지 저장 | `builtin` | 실행 결과를 온톨로지에 저장 |
| `rag-ontology-lookup` | RAG/온톨로지 조회 | `builtin` | 근거 조회 |
| `fault-recurrence-check` | 반복 고장 확인 | `builtin` | 반복 고장 분석 |
| `request-classify` | 요청 분류 | `builtin` | 요청 카테고리 분류 |

대상 파일:

```text
ont_platform/v5/backend/app/config/skills/builtin_skills.json
```

---

### 2.3 스킬 관리 서비스 추가

Built-in Skill과 프로젝트별 Custom Skill을 관리하는 서비스를 추가했습니다.

구현 내용:

- Built-in Skill 로딩
- 프로젝트별 Custom Skill 로딩
- Skill ID 기반 조회
- Custom Skill 저장
- Custom Skill 삭제
- Built-in + Custom 목록 병합 조회

대상 파일:

```text
ont_platform/v5/backend/app/services/skill_service.py
```

현재 Custom Skill 저장 경로:

```text
storage/{company_id}/{project_id}/skills/custom_skills.json
```

주의:

현재 `skill_service.py`는 자체 `get_project_root()` helper를 포함하고 있습니다. 기존 플랫폼의 `storage_config.get_project_root()`와 통일하는 후속 정리가 필요합니다.

---

### 2.4 표현식 렌더링 엔진 추가

워크플로우의 이전 노드 실행 결과를 다음 Skill 노드 입력으로 전달하기 위한 표현식 렌더링 엔진을 추가했습니다.

지원 문법:

```text
{{nodes.node-id.output.field}}
```

핵심 규칙:

| 입력 형태 | 처리 |
|---|---|
| `{{nodes.x.output.value}}` | 원본 타입 보존 |
| `prefix {{nodes.x.output.value}} suffix` | 문자열 보간 |
| 리터럴 값 | 그대로 반환 |

예:

```text
{{nodes.n-asset.output.equipmentIds}}
```

결과가 배열이면 문자열이 아니라 배열 타입 그대로 유지됩니다.

대상 파일:

```text
ont_platform/v5/backend/app/services/expression_renderer.py
```

구현 함수:

- `evaluate_expression`
- `resolve_input_value`
- `prepare_skill_input`
- `validate_skill_schema`

---

### 2.5 스킬 실행 엔진 추가

스킬 타입별 실행 엔진을 추가했습니다.

지원 실행 타입:

- `builtin`
- `http`
- `mcp_http`
- `custom`

Phase 1 정책:

```text
custom 타입은 실행하지 않고 오류를 반환한다.
```

`mcp_http` 실행 방식:

- `tool_endpoint`: `/mcp/tools/{tool}` endpoint에 payload 직접 전송
- `jsonrpc_proxy`: JSON-RPC `tools/call` wrapper 사용

현재 v5는 `tool_endpoint` 중심입니다.

대상 파일:

```text
ont_platform/v5/backend/app/services/skill_executor.py
```

주의:

일부 Built-in Skill은 Phase 1 Mock 구현입니다.

- `ontology-write`
- `rag-ontology-lookup`
- `fault-recurrence-check`
- `request-classify`

향후 실제 온톨로지 서비스, RAG 검색, LLM 분류 로직과 연결해야 합니다.

---

### 2.6 Skills API 추가

프론트엔드에서 스킬을 조회하고 관리할 수 있도록 API를 추가했습니다.

추가 API:

```text
GET    /api/skills
GET    /api/skills/{skill_id}
POST   /api/skills/custom
PUT    /api/skills/custom/{skill_id}
DELETE /api/skills/custom/{skill_id}
POST   /api/skills/validate-expression
```

대상 파일:

```text
ont_platform/v5/backend/app/api/skills.py
```

라우터 등록:

```text
ont_platform/v5/backend/app/main.py
```

등록 내용:

```python
from app.api.skills import router as skills_router
app.include_router(skills_router)
```

---

### 2.7 워크플로우 실행기에 Skill 노드 실행 연결

워크플로우 실행 중 노드 타입이 `skill`이면 스킬 실행기로 위임하도록 연결했습니다.

처리 흐름:

```text
WorkflowGraph run
  -> node.type == "skill"
  -> node.data.skillId 확인
  -> SkillService로 Skill 조회
  -> skillConfig.inputMapping 렌더링
  -> SkillExecutor 실행
  -> execution_context 업데이트
  -> WorkflowRun.steps.output 저장
  -> SSE node_finished 이벤트로 프론트 전달
```

대상 파일:

```text
ont_platform/v5/backend/app/api/workflow.py
```

---

### 2.8 프론트엔드 타입 확장

프론트엔드 API 타입에 스킬 관련 타입을 추가했습니다.

추가 타입:

- `SkillImplementationType`
- `MCPHttpConfig`
- `Skill`

`GraphNodeKind` 확장:

- `skill`

`GraphNodeData` 확장:

- `skillId`
- `skillVersion`
- `skillConfig`

대상 파일:

```text
ont_platform/v5/frontend/src/types/api.ts
```

---

### 2.9 프론트엔드 API 클라이언트 확장

프론트엔드에서 Skills API를 호출할 수 있도록 API 클라이언트를 확장했습니다.

추가 클라이언트:

```typescript
api.skills.list()
api.skills.get(skillId)
api.skills.createCustom(skill)
```

대상 파일:

```text
ont_platform/v5/frontend/src/lib/api.ts
```

---

### 2.10 별도 스킬 관리 화면 추가

좌측 메뉴에서 접근 가능한 별도 스킬 관리 화면을 추가했습니다.

화면 기능:

- Built-in Skill 목록 조회
- Custom Skill 목록 조회
- 전체/Built-in/Custom 필터
- 검색
- 총 스킬 수, Built-in 수, Custom 수, Phase 1 실행 가능 수 표시
- Input/Output schema 요약 표시
- Custom Code 실행 제한 안내

대상 파일:

```text
ont_platform/v5/frontend/src/components/SkillManager.tsx
```

메뉴 연결:

```text
ont_platform/v5/frontend/src/components/Sidebar.tsx
```

화면 라우팅:

```text
ont_platform/v5/frontend/src/app/page.tsx
```

메뉴 위치:

```text
워크플로우 > 스킬 관리
```

---

### 2.11 워크플로우 빌더 내 스킬 탭 추가

워크플로우 빌더 우측 패널에 스킬 탭을 추가했습니다.

기능:

- Built-in Skill 카드 표시
- Custom Skill 카드 표시
- 스킬 클릭 시 워크플로우에 `skill` 노드 추가
- 추가된 노드에 `skillId`, `skillVersion`, `skillConfig` 저장
- 노드 속성에서 연결된 Skill ID 표시

대상 파일:

```text
ont_platform/v5/frontend/src/components/WorkflowGraph.tsx
```

---

### 2.12 워크플로우 입출력 표시 개선

실행 완료 후 입출력 탭에서 결과가 보이지 않던 문제를 수정했습니다.

기존 문제:

```text
실행 완료 시 activeNodeId가 null이 되어 선택된 노드 결과를 찾지 못함
```

수정 내용:

```text
입출력 탭은 activeNodeId가 아니라 selectedNodeId 기준의 최신 StepResult를 조회한다.
```

추가 개선:

- 최근 완료 단계 클릭 시 입출력 탭 이동
- 결과 테이블 output 클릭 시 입출력 탭 이동
- 선택된 노드의 Skill ID 표시

대상 파일:

```text
ont_platform/v5/frontend/src/components/WorkflowGraph.tsx
```

---

### 2.13 워크플로우 저장 시 Skill 메타데이터 보존

Skill 노드를 추가한 뒤 저장/새로고침 시 스킬 정보가 사라지지 않도록 저장 payload에 스킬 필드를 포함했습니다.

보존 대상:

- `skillId`
- `skillVersion`
- `skillConfig`

대상 파일:

```text
ont_platform/v5/frontend/src/components/WorkflowGraph.tsx
```

---

### 2.14 워크플로우 블록/연결선 삭제 기능 개선

워크플로우 빌더에서 블록 또는 연결선을 선택한 뒤 삭제할 수 없던 문제를 수정했습니다.

기존 문제:

```text
ReactFlow의 선택 상태는 있었지만,
사용자가 명시적으로 선택된 블록이나 연결선을 삭제할 수 있는 UI/키보드 동작이 부족했다.
```

수정 내용:

- 상단 툴바에 `선택 삭제` 버튼 추가
- 우측 `선택 항목` 탭에 `블록 삭제` 버튼 추가
- 우측 `선택 항목` 탭에 `연결선 삭제` 버튼 추가
- `Delete`, `Backspace` 키 삭제 지원
- 블록 삭제 시 해당 블록과 연결된 선을 함께 삭제
- 블록 삭제 시 해당 블록의 실행 결과 상태도 화면에서 제거
- 삭제 후 선택 상태와 active 상태 정리

대상 파일:

```text
ont_platform/v5/frontend/src/components/WorkflowGraph.tsx
```

---

## 3. 테스트 추가 내역

스킬 시스템 백엔드 단위 테스트를 추가했습니다.

추가 테스트 파일:

```text
ont_platform/v5/backend/tests/test_expression_renderer.py
ont_platform/v5/backend/tests/test_skill_executor.py
ont_platform/v5/backend/tests/test_skill_service.py
```

검증 대상:

- 표현식 타입 보존
- inputMapping 렌더링
- inputSchema 기본 검증
- builtin skill 실행
- http skill 실행
- mcp_http skill 실행
- custom skill 실행 제한
- Built-in / Custom Skill 로딩
- Custom Skill 저장/삭제

---

## 4. 수정 또는 추가된 프로그램 목록

### 4.1 백엔드 신규 파일

| 파일 | 내용 |
|---|---|
| `backend/app/models/skill.py` | Skill, SkillConfig, MCPHttpConfig 모델 |
| `backend/app/api/skills.py` | Skills API |
| `backend/app/services/skill_service.py` | 스킬 목록/저장/조회 서비스 |
| `backend/app/services/skill_executor.py` | 스킬 실행 엔진 |
| `backend/app/services/expression_renderer.py` | 표현식 렌더링 엔진 |
| `backend/app/config/skills/builtin_skills.json` | Built-in Skill 카탈로그 |
| `backend/tests/test_expression_renderer.py` | 표현식 엔진 테스트 |
| `backend/tests/test_skill_executor.py` | 스킬 실행 테스트 |
| `backend/tests/test_skill_service.py` | 스킬 서비스 테스트 |

### 4.2 백엔드 수정 파일

| 파일 | 내용 |
|---|---|
| `backend/app/main.py` | Skills API router 등록 |
| `backend/app/api/workflow.py` | Skill 노드 실행 처리 추가 |

### 4.3 프론트엔드 신규 파일

| 파일 | 내용 |
|---|---|
| `frontend/src/components/SkillManager.tsx` | 별도 스킬 관리 화면 |

### 4.4 프론트엔드 수정 파일

| 파일 | 내용 |
|---|---|
| `frontend/src/types/api.ts` | Skill 타입, GraphNodeData 확장 |
| `frontend/src/lib/api.ts` | `api.skills` 클라이언트 추가 |
| `frontend/src/components/Sidebar.tsx` | `스킬 관리` 메뉴 추가 |
| `frontend/src/app/page.tsx` | `skills` 화면 라우팅 추가 |
| `frontend/src/components/WorkflowGraph.tsx` | 스킬 탭, Skill 노드 설치, 입출력 표시 개선 |

추가 반영:

```text
WorkflowGraph.tsx
  - 선택된 블록 삭제
  - 선택된 연결선 삭제
  - Delete/Backspace 키 삭제
  - 블록 삭제 시 연결선과 실행 결과 상태 정리
```

---

## 5. 검증 내역

프론트엔드 검증:

```text
npx tsc --noEmit
```

결과:

```text
통과
```

Tailwind 컴파일 검증:

```text
npx tailwindcss -i ./src/app/globals.css -o %TEMP%/ont_platform_v5_tailwind_check.css --content "./src/**/*.{ts,tsx}"
```

결과:

```text
통과
```

Skills API 응답 확인:

```text
GET http://127.0.0.1:8001/api/skills
```

결과:

```text
Built-in Skill 7개 반환 확인
```

주의:

PowerShell 출력에서는 한글이 깨져 보였으나, API 응답 자체는 UTF-8 JSON으로 반환됩니다. 브라우저 UI에서는 정상 표시 여부를 별도로 확인해야 합니다.

---

## 6. 현재 한계와 후속 보완 필요 사항

### 6.1 Built-in Skill 일부는 Mock 구현

다음 Built-in Skill은 현재 Phase 1 Mock 구현입니다.

- `ontology-write`
- `rag-ontology-lookup`
- `fault-recurrence-check`
- `request-classify`

후속 작업:

- 실제 OntologyService 연결
- 실제 Vector/RAG 조회 연결
- 실제 LLM 분류 연결
- 공장 반복 고장 데이터 기반 분석 연결

---

### 6.2 Custom Code 실행은 제한됨

현재 정책:

```text
Custom Skill은 저장/조회 가능하지만 실행은 제한한다.
```

이유:

- Python 코드 실행 보안 위험
- 샌드박스 미구현
- Windows/Linux 타임아웃 처리 차이
- 리소스 제한 미구현

후속 작업:

- Docker 또는 별도 프로세스 샌드박스 검토
- timeout, memory, network 제한
- AST 기반 코드 검증
- 실행 감사 로그

---

### 6.3 SkillService 저장 helper 정리 필요

현재 `skill_service.py`는 자체 `get_project_root()` helper를 가지고 있습니다.

기존 플랫폼은 `storage_config.get_project_root()`를 사용합니다.

후속 작업:

```text
skill_service.py의 자체 helper를 제거하고 storage_config.get_project_root로 통일
```

---

### 6.4 Skill Manager의 생성/편집 UI는 아직 미구현

현재 별도 스킬 관리 화면은 조회 중심입니다.

구현된 것:

- 조회
- 검색
- 필터
- schema 요약

아직 없는 것:

- Custom Skill 생성 모달
- Custom Skill 편집 화면
- Custom Skill 삭제 버튼
- input/output schema 편집기
- 실행 테스트 패널

---

### 6.5 Skill 노드 실행은 일반 workflow runner 중심

현재 `skill` 노드는 일반 워크플로우 실행 경로에서 처리됩니다.

다만 고객사/공장 전용 executor:

- `scenario1.customer_question_auto_reply`
- `factory.repeated_fault_response`

이 경로는 전용 executor 로직을 우선 사용합니다.

후속 작업:

```text
전용 executor 기반 시나리오와 일반 skill node 실행 모델의 경계를 문서화하고,
필요하면 전용 executor 내부도 skill 기반으로 재구성한다.
```

---

## 7. 사용자 화면 기준 변경 사항

### 7.1 좌측 메뉴

추가 메뉴:

```text
워크플로우 > 스킬 관리
```

### 7.2 스킬 관리 화면

볼 수 있는 것:

- 전체 스킬 수
- Built-in Skill 수
- Custom Skill 수
- Phase 1 실행 가능 Skill 수
- Built-in/Custom Skill 카드
- Input/Output schema 요약
- 구현 타입
- 카테고리와 태그

### 7.3 워크플로우 빌더

우측 탭:

```text
실행 현황 / 선택 항목 / 입출력 / 스킬 / 온톨로지 / 이력
```

스킬 탭 기능:

```text
스킬 카드 클릭 -> 워크플로우에 Skill 노드 추가
```

입출력 탭 개선:

```text
선택한 노드의 실행 결과 표시
```

---

## 8. 구현 상태 판단

현재 상태:

```text
Phase 1 부분 구현 완료
```

완료된 것:

- Skill 모델
- Built-in Skill 카탈로그
- Skills API
- SkillService
- Expression Renderer
- SkillExecutor
- Workflow Skill 노드 실행 연결
- Frontend Skill 타입/API
- 별도 Skill Manager 화면
- Workflow Builder 내 Skill 탭
- 입출력 표시 개선
- 워크플로우 블록/연결선 삭제 기능

남은 것:

- Custom Skill 생성/편집 UI
- Built-in Skill 실제 서비스 연결
- Skill 실행 감사 로그
- Skill 실행 결과 상세 trace
- 전용 executor와 Skill 실행 모델 통합
- storage helper 통일

---

## 9. 다음 작업 제안

우선순위 1:

```text
SkillService 저장 경로를 storage_config.get_project_root로 통일
```

우선순위 2:

```text
Skill Manager에서 Custom Skill 생성/편집/삭제 UI 추가
```

우선순위 3:

```text
WorkflowGraph의 Skill 노드 속성에서 inputMapping 편집 UI 추가
```

우선순위 4:

```text
공장/고객사 전용 executor를 점진적으로 Skill 기반 실행 모델과 연결
```

우선순위 5:

```text
Skill 실행 이력을 별도 패널 또는 WorkflowRun trace에 더 명확히 표시
```

---

## 10. 한 줄 요약

스킬 시스템은 현재 v5 워크플로우에 1차로 연결되었습니다.

현재 구현은 “스킬을 정의하고, 조회하고, 워크플로우 노드로 설치하고, 일반 워크플로우 실행에서 실행하는 구조”까지 포함합니다.

다만 운영 수준으로 가려면 Custom Skill 편집 UI, 실제 Built-in 서비스 연결, storage helper 통일, 감사 로그 보강이 추가로 필요합니다.
