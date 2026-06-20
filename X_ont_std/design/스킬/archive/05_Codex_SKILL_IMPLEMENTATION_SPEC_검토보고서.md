# 03_SKILL_IMPLEMENTATION_SPEC 검토보고서

- 작성자: Codex
- 작성일: 2026-06-14
- 검토 대상: `design/스킬/03_SKILL_IMPLEMENTATION_SPEC.md`
- 검토 기준:
  - `ont_platform/v5` 현재 워크플로우 빌더 구조
  - `GraphNodeKind`, `GraphNodeData` 타입 정합성
  - 고객사/공장 MCP 연동 방식
  - 테넌트/프로젝트 저장 구조
  - MVP 구현 가능성과 보안 리스크

---

## 1. 총평

`03_SKILL_IMPLEMENTATION_SPEC.md`는 기존 스킬 시스템 개념 문서보다 구현 명세에 훨씬 가까워졌습니다.

특히 아래 내용이 들어간 점은 좋습니다.

- 스킬, 액션, 온톨로지의 역할 구분
- 이전 노드 결과를 다음 노드 입력으로 넘기는 변수 바인딩 개념
- 인증 정보와 환경변수 분리
- MCP 스킬 타입 정의
- Built-in Skill과 Custom Skill 저장 위치 분리
- v5 타입 확장 방향
- MVP에서는 Custom Code 실행을 제한한다는 원칙

다만 바로 구현에 들어가기에는 몇 가지 보완이 필요합니다. 가장 중요한 수정 포인트는 다음 네 가지입니다.

1. 표현식 엔진은 타입을 보존해야 합니다.
2. MCP 실행 방식은 현재 v5의 HTTP 중계 MCP 구조를 우선해야 합니다.
3. Custom Code 실행 예시는 Phase 1 문서에서 분리해야 합니다.
4. `GraphNodeKind` 예시는 현재 실제 타입을 누락하지 않도록 “추가 확장” 방식으로 표현해야 합니다.

---

## 2. 주요 검토 의견

### 2.1 표현식 정규식이 너무 좁음

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
2.2 파싱 규칙
EXPRESSION_PATTERN = r'\{\{(nodes\.[a-z0-9\-]+\.[a-z]+(\.[\w]+)*)\}\}'
```

현재 정규식은 노드 ID를 `[a-z0-9\-]+`로 제한합니다.

현재 v5 템플릿은 `request-input`, `draft-response`처럼 kebab-case를 쓰고 있어 당장은 일부 맞지만, 향후 아래 형태가 들어오면 깨질 수 있습니다.

- `_`가 들어간 노드 ID
- 대문자가 들어간 노드 ID
- 외부 시스템에서 생성한 UUID 기반 ID
- `node:xxx` 같은 namespace 형태

권장안:

```python
EXPRESSION_PATTERN = r"\{\{\s*(nodes\.[^.]+\.(?:output|status|result)(?:\.[\w-]+)*)\s*\}\}"
```

또는 더 안전하게 표현식 파서를 별도 함수로 두고, `{{ ... }}` 내부의 경로만 검증하는 방식이 좋습니다.

---

### 2.2 표현식 평가 시 타입이 문자열로 변환됨

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
2.2 파싱 규칙
return str(value) if value is not None else ""
```

현재 의사코드는 모든 값을 문자열로 변환합니다.

이 방식은 이메일 제목이나 메시지 본문처럼 문자열 치환에는 괜찮습니다. 하지만 MCP/HTTP payload에서는 객체, 배열, 숫자, boolean 타입을 그대로 넘겨야 합니다.

문제 예시:

```json
{
  "properties": "{{nodes.n-classify.output}}"
}
```

기대값:

```json
{
  "properties": {
    "category": "equipment_fault",
    "severity": "HIGH"
  }
}
```

현재 방식의 실제 결과:

```json
{
  "properties": "{'category': 'equipment_fault', 'severity': 'HIGH'}"
}
```

권장 규칙:

| 입력값 형태 | 처리 방식 |
|---|---|
| 값 전체가 표현식 하나 | 원본 타입 그대로 반환 |
| 문자열 중간에 표현식 포함 | 문자열 치환 |
| 표현식 경로가 없음 | 오류 또는 빈 문자열 정책 선택 |

권장 의사코드:

```python
def render_value(value: Any, context: dict) -> Any:
    if not isinstance(value, str):
        return value

    matches = find_expressions(value)
    if not matches:
        return value

    if is_single_expression(value, matches):
        return resolve_path(matches[0], context)

    rendered = value
    for expr in matches:
        resolved = resolve_path(expr, context)
        rendered = rendered.replace(f"{{{{{expr}}}}}", "" if resolved is None else str(resolved))
    return rendered
```

---

### 2.3 HTTP 인증 정보 매핑이 모호함

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
3.1 스킬 정의에 필요 자격 증명 명시
"credentialMapping": {
  "auth": "SMTP_USERNAME:SMTP_PASSWORD"
}
```

이 구조는 실제 실행 시 어디에 인증 정보를 넣어야 하는지 불명확합니다.

다음 중 무엇인지 알 수 없습니다.

- Basic Auth
- Bearer Token
- HTTP Header
- Query Parameter
- Body Field
- SMTP 연결 설정

권장안:

```json
{
  "requiredCredentials": ["SMTP_USERNAME", "SMTP_PASSWORD"],
  "implementation": {
    "type": "http",
    "endpoint": "https://api.email.service/send",
    "method": "POST",
    "auth": {
      "type": "basic",
      "username": "${SMTP_USERNAME}",
      "password": "${SMTP_PASSWORD}"
    },
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

Bearer Token 방식은 다음처럼 분리합니다.

```json
{
  "requiredCredentials": ["API_TOKEN"],
  "implementation": {
    "type": "http",
    "endpoint": "https://api.example.com/action",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}"
    }
  }
}
```

---

### 2.4 MCP 구현이 현재 v5 구조와 다름

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
4. MCP 구현 명세
transport: 'stdio' | 'sse'
```

현재 v5 시나리오는 이미 아래 구조를 사용합니다.

- `customer_mcp_client.py`
- `factory_mcp_client.py`
- 고객사/공장 mock infra는 HTTP API로 기동
- ont_platform은 중계 MCP API를 통해 댓글/정비 지시를 등록

즉, 현재 프로젝트의 현실은 순수 MCP stdio보다 “HTTP 기반 MCP 중계 서버 호출”에 가깝습니다.

MVP 권장 타입:

```typescript
type SkillImplementationType =
  | "builtin"
  | "http"
  | "mcp_http"
  | "custom";
```

권장 MCP HTTP 예시:

```json
{
  "id": "factory-comment-create",
  "name": "공장 게시판 댓글 등록",
  "implementation": {
    "type": "mcp_http",
    "server": "s2_factory_mcp",
    "tool": "comment.create",
    "endpoint": "http://127.0.0.1:8081/mcp/tools/comment.create",
    "method": "POST",
    "timeout": 10000
  }
}
```

Phase 1에서는 `mcp_http`를 우선 구현하고, `stdio`, `sse`는 Phase 3로 미루는 것이 안전합니다.

---

### 2.5 MCP stdio 의사코드는 실제 프로토콜 절차가 부족함

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
4.3 백엔드 실행 로직
process = subprocess.Popen(...)
request = {
  "jsonrpc": "2.0",
  "method": "call_tool"
}
```

이 예시는 MCP의 실제 초기화 절차를 단순화하고 있습니다.

일반적인 MCP 흐름은 다음 단계가 필요합니다.

1. 프로세스 시작
2. `initialize`
3. `initialized`
4. `tools/list`
5. `tools/call`
6. 응답 파싱
7. 프로세스 종료 또는 세션 재사용

따라서 현재 예시는 “구현 코드”가 아니라 “의사코드”라고 명확히 표시해야 합니다.

권장 문구:

```text
주의: 아래 코드는 MCP stdio 실행의 개념 예시이며, 실제 구현 시에는 MCP initialize/tools/call 절차와 세션 관리가 필요하다.
Phase 1에서는 stdio MCP 실행을 구현하지 않는다.
```

---

### 2.6 저장 구조는 좋지만 실제 helper 사용을 명시해야 함

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
5. 저장 구조 및 위치
ont_platform/storage/{company_id}/{project_id}/skills/custom_skills.json
```

방향은 맞습니다.

다만 구현자는 `ont_platform/v5/storage` 같은 잘못된 위치에 저장할 수 있습니다. 현재 v5 백엔드는 `storage_config.get_project_root(ctx.company_id, ctx.project_id)` 흐름을 사용합니다.

권장 문구:

```text
프로젝트별 Custom Skill 저장은 반드시 `get_project_root(ctx.company_id, ctx.project_id)`를 기준으로 한다.
직접 상대경로 문자열을 조합하지 않는다.
```

권장 구현:

```python
def _custom_skill_file(ctx: TenantContext) -> Path:
    return get_project_root(ctx.company_id, ctx.project_id) / "skills" / "custom_skills.json"
```

---

### 2.7 GraphNodeKind 예시가 실제 타입 일부를 누락함

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
6.1 프론트엔드 타입
export type GraphNodeKind = ...
```

현재 실제 `GraphNodeKind`에는 문서 예시에 없는 타입이 있습니다.

현재 실제 타입 예:

- `approve_order`
- `risk_assess`
- `request_register`
- `precondition_check`
- `artifact_change_check`
- `validate_response`
- `complete_request`
- `end_pending`
- `end_failed`

문서가 전체 union을 다시 쓰는 방식이면 구현자가 기존 타입을 지울 위험이 있습니다.

권장 표현:

```typescript
// 기존 GraphNodeKind union은 유지하고 아래 두 타입만 추가한다.
export type GraphNodeKind =
  | ExistingGraphNodeKind
  | "skill"
  | "custom_code";
```

실제 코드에서는 TypeScript union을 이런 식으로 나눌 수 없다면, 문서에는 최소한 다음 문구를 넣어야 합니다.

```text
주의: 아래 목록은 전체 재정의가 아니라 기존 GraphNodeKind에 `skill`, `custom_code`를 추가한다는 의미다. 기존 타입을 삭제하지 않는다.
```

---

### 2.8 Custom Code 실행 예시가 MVP 정책과 충돌함

문서 위치:

```text
03_SKILL_IMPLEMENTATION_SPEC.md
7. MVP 샌드박스 규칙
execute_custom_code_with_timeout(...)
```

문서 표에서는 Phase 1에 Custom Code는 “저장만, 실행 불가”라고 되어 있습니다.

그런데 바로 위에 `execute_custom_code_with_timeout` 구현 예시가 들어가 있어, 구현자가 Phase 1에 Python 실행까지 넣어야 한다고 오해할 수 있습니다.

권장안:

- Phase 1 문서에서는 Python 실행 코드를 제거
- 또는 `부록: Phase 3 참고용`으로 이동
- Phase 1 API는 Custom Skill 실행 요청 시 명확히 거절

권장 응답:

```json
{
  "status": "blocked",
  "reason": "custom_code_execution_disabled_in_phase1"
}
```

---

## 3. MVP 구현 범위 재정의 제안

현재 명세는 범위가 약간 넓습니다. MVP에서는 아래까지만 구현하는 것을 권장합니다.

### 3.1 Phase 1에 포함

- Built-in Skill 카탈로그 API
- 프로젝트별 Custom Skill 저장/조회 API
- 워크플로우 노드에 `skillId`, `skillConfig` 저장
- Skill Gallery UI
- Skill 설치 시 워크플로우에 노드 추가
- 표현식 엔진
- `mcp_http` 또는 `http` 기반 스킬 실행
- 실행 결과를 `WorkflowRun.steps.output`에 저장

### 3.2 Phase 1에서 제외

- Python Custom Code 실행
- MCP stdio 서버 프로세스 직접 기동
- MCP SSE 세션 관리
- Docker 샌드박스
- 외부 마켓플레이스 공유

---

## 4. v5 기준 권장 Built-in Skill

현재 프로젝트의 시나리오와 바로 연결되는 Built-in Skill부터 정의하는 것이 좋습니다.

| Skill ID | 이름 | 구현 타입 | 연결 시나리오 |
|---|---|---|---|
| `customer-comment-create` | 고객 게시판 댓글 등록 | `mcp_http` | Scenario 1 |
| `factory-comment-create` | 공장 게시판 댓글 등록 | `mcp_http` | Scenario 2 |
| `factory-maintenance-create` | 정비 지시 생성 | `mcp_http` | Scenario 2 |
| `ontology-write` | 온톨로지 저장 | `builtin` | 공통 |
| `rag-ontology-lookup` | RAG/온톨로지 근거 조회 | `builtin` | 공통 |
| `fault-recurrence-check` | 반복 고장 확인 | `builtin` | 공장 자동화 |
| `request-classify` | 요청 분류 | `builtin` | 공통 |

예시:

```json
{
  "id": "factory-comment-create",
  "name": "공장 게시판 댓글 등록",
  "category": "integration",
  "implementation": {
    "type": "mcp_http",
    "server": "s2_factory_mcp",
    "tool": "comment.create",
    "endpoint": "http://127.0.0.1:8081/mcp/tools/comment.create",
    "method": "POST",
    "timeout": 10000
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "event_id": { "type": "string" },
      "content": { "type": "string" },
      "mode": { "type": "string", "enum": ["dry_run", "post"] }
    },
    "required": ["event_id", "content"]
  }
}
```

---

## 5. 권장 백엔드 API

MVP에서는 아래 API 정도면 충분합니다.

```text
GET    /api/skills
GET    /api/skills/{skill_id}
POST   /api/skills/custom
PUT    /api/skills/custom/{skill_id}
DELETE /api/skills/custom/{skill_id}
POST   /api/skills/validate-expression
```

워크플로우 실행 API는 기존 API를 유지합니다.

```text
POST /api/workflow-graphs/{graph_id}/run
```

`run` 내부에서 노드 타입이 `skill`이면 `SkillExecutor`로 위임합니다.

---

## 6. 권장 백엔드 구조

```text
backend/app/api/skills.py
backend/app/services/skill_service.py
backend/app/services/skill_executor.py
backend/app/services/expression_renderer.py
backend/app/config/skills/builtin_skills.json
```

역할:

| 파일 | 역할 |
|---|---|
| `skills.py` | 스킬 조회/저장 API |
| `skill_service.py` | Built-in + Custom Skill 병합, 권한 체크 |
| `skill_executor.py` | builtin/http/mcp_http 실행 |
| `expression_renderer.py` | `{{nodes.xxx.output.yyy}}` 렌더링 |
| `builtin_skills.json` | 시스템 기본 스킬 정의 |

---

## 7. 권장 프론트엔드 구조

```text
frontend/src/components/SkillGallery.tsx
frontend/src/components/SkillEditor.tsx
frontend/src/components/SkillMappingPanel.tsx
frontend/src/lib/skills.ts
frontend/src/types/api.ts
```

WorkflowGraph에는 다음을 추가합니다.

- 우측 패널 탭: `스킬`
- 노드 속성 탭에 `skillId`, `inputMapping`, `outputMapping`
- 팔레트 또는 갤러리에서 “설치” 클릭 시 `type: "skill"` 노드 추가
- 실행 결과 패널에서 스킬 입출력 확인

---

## 8. 구현 전 수정 체크리스트

`03_SKILL_IMPLEMENTATION_SPEC.md`에 아래 항목을 반영한 뒤 구현을 시작하는 것을 권장합니다.

- [ ] 표현식 엔진 타입 보존 규칙 추가
- [ ] 표현식 정규식 완화
- [ ] HTTP 인증 정보 매핑 구조화
- [ ] MVP MCP 타입을 `mcp_http` 중심으로 재정의
- [ ] MCP stdio 예시는 Phase 3 또는 부록으로 이동
- [ ] 저장 경로는 `get_project_root()` 기준이라고 명시
- [ ] `GraphNodeKind`는 전체 재정의가 아니라 기존 타입에 추가라고 명시
- [ ] Custom Code 실행 코드는 Phase 1 본문에서 제거하거나 비활성 정책 명시
- [ ] Built-in Skill 예시는 현재 고객사/공장 시나리오 기반으로 교체
- [ ] 실행 결과 저장 위치를 `WorkflowRun.steps.output`으로 명시

---

## 9. 최종 의견

이 명세서는 구현에 들어갈 수 있는 수준에 가깝습니다.

다만 현재 v5 플랫폼은 이미 고객사/공장 MCP 중계 서버, 워크플로우 그래프 저장, 실행 이력, 온톨로지 매핑을 갖고 있습니다. 따라서 스킬 시스템은 새 런타임을 크게 만드는 방식보다, 기존 워크플로우 노드 실행 구조 위에 “재사용 가능한 실행 단위”를 얹는 방식이 좋습니다.

가장 안전한 첫 구현은 다음입니다.

```text
Skill Catalog
  -> Skill 노드 설치
  -> inputMapping 표현식 렌더링
  -> mcp_http 또는 builtin 실행
  -> WorkflowRun 이력 저장
  -> 필요 시 ontology_write 노드에서 온톨로지 저장
```

이 순서로 가면 공장자동화 시나리오에도 자연스럽게 붙고, 고객사 자동댓글 시나리오에도 그대로 재사용할 수 있습니다.
