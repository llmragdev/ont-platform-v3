# 스킬 시스템 최종 통합 검토 보고서

**작성일:** 2026-06-14  
**작성자:** Claude Code (Codex + Antigravity 검토 통합)  
**대상:** 03_SKILL_IMPLEMENTATION_SPEC.md 에 대한 Codex/Antigravity 검토의견 통합 분석

---

## 📋 Executive Summary

`03_SKILL_IMPLEMENTATION_SPEC.md`는 스킬 시스템 구현의 방향을 올바르게 제시했으나, **실제 구현에 들어갈 때 서버 크래시나 프로토콜 오류를 유발할 수 있는 8개 이슈**가 발견되었습니다.

### 이슈 분류

| 심각도 | 개수 | 설명 |
|------|------|------|
| **Critical** | 3개 | 서버 크래시, 프로토콜 위반, 타입 오류 |
| **High** | 3개 | MVP 범위/구조 오류 |
| **Medium** | 2개 | 코드 예시 명확성 |

**결론:** 아래 8개 항목을 반영한 후 구현을 시작하면 안전합니다.

---

## 🚨 Critical Issues (서버 크래시 위험)

### Issue #1: Windows 환경에서 signal.alarm 작동 불가

**심각도:** 🔴 Critical  
**발견자:** Antigravity  
**발생 위치:** Section 7.2 `execute_custom_code_with_timeout`

#### 문제

```python
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(timeout_sec)  # ← Windows에서 AttributeError 발생
```

- `signal.alarm()`과 `SIGALRM`은 **Unix 전용**
- 현재 개발 환경 (Windows 11) 에서 즉시 크래시
- 서버 프로세스 중단

#### 해결책

**multiprocessing을 사용한 크로스 플랫폼 구현:**

```python
import multiprocessing
import queue
from typing import Dict, Any

def _raw_run_code(code: str, input_data: Dict, result_queue: multiprocessing.Queue):
    """서브프로세스 격리 환경에서 실행"""
    try:
        exec_globals = {'input': input_data, 'output': None}
        exec(code, exec_globals)
        result_queue.put({
            "success": True, 
            "output": exec_globals.get('output')
        })
    except Exception as e:
        result_queue.put({
            "success": False, 
            "error": str(e)
        })

def execute_custom_code_with_timeout(code: str, input_data: Dict, timeout_sec: int = 3) -> Any:
    """Windows/Linux 모두 지원, 프로세스 격리"""
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_raw_run_code, 
        args=(code, input_data, result_queue)
    )
    process.start()
    
    # 타임아웃 대기
    process.join(timeout=timeout_sec)
    
    if process.is_alive():
        process.terminate()
        process.join()
        raise TimeoutError(f"Custom code exceeded {timeout_sec}s limit")
    
    try:
        res = result_queue.get_nowait()
        if not res["success"]:
            raise RuntimeError(res["error"])
        return res["output"]
    except queue.Empty:
        raise RuntimeError("No result from code process")
```

**장점:**
- ✅ Windows/Linux/Mac 모두 호환
- ✅ 프로세스 격리 → 메모리 격리 + 안전한 강제 종료
- ✅ 서브프로세스 크래시가 메인 백엔드 영향 없음

---

### Issue #2: MCP 초기화 프로토콜 누락

**심각도:** 🔴 Critical  
**발견자:** Antigravity  
**발생 위치:** Section 4.3 `_execute_stdio`

#### 문제

```python
request = {
    "jsonrpc": "2.0",
    "method": "call_tool",  # ← 초기화 없이 바로 호출
    "params": { ... }
}
```

- MCP 표준: **initialize 핸드셰이크 필수**
- 현재 코드는 프로세스 시작 후 바로 `call_tool`
- 표준 MCP 서버는 미초기화 상태에서 요청 거부

#### MCP 표준 프로토콜 절차

```
1. [CLIENT] → [SERVER] initialize
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "initialize",
     "params": {
       "protocolVersion": "2024-11-05",
       "capabilities": {},
       "clientInfo": {
         "name": "ontology-console",
         "version": "1.0"
       }
     }
   }

2. [SERVER] → [CLIENT] initialize response
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "serverInfo": {...},
       "capabilities": {...}
     }
   }

3. [CLIENT] → [SERVER] notifications/initialized (no id)
   {
     "jsonrpc": "2.0",
     "method": "notifications/initialized"
   }

4. [CLIENT] → [SERVER] tools/call (최신 규격)
   {
     "jsonrpc": "2.0",
     "id": 2,
     "method": "tools/call",
     "params": {
       "name": "comment.create",
       "arguments": {...}
     }
   }
```

#### 수정 방향

- **Phase 1:** stdio MCP 제외, `mcp_http` 중심으로 구현
- **Phase 3:** stdio 구현 시 위 절차를 엄격히 따를 것

---

### Issue #3: 변수 바인딩 타입 캐스팅 오류

**심각도:** 🔴 Critical  
**발견자:** Codex & Antigravity (동일 지적)  
**발생 위치:** Section 2.3 `prepareSkillInput`

#### 문제

```python
prepared[key] = evaluateExpression(value, executionContext)  # → 무조건 str 반환
```

**시나리오:**

입력:
```json
{
  "limit": "{{nodes.n-config.output.maxItems}}"
}
```

실행 컨텍스트:
```python
nodes['n-config'].output = {'maxItems': 10}
```

**현재 결과 (오류):**
```json
{
  "limit": "10"  # 문자열이 되어 inputSchema 정수 검증 실패!
}
```

**기대 결과:**
```json
{
  "limit": 10  # 원본 타입 유지
}
```

#### 해결책: 단일 표현식 vs 복합 보간 구분

```python
import re
from typing import Any, Dict

# 단일 표현식만 포함되는 경우: "{{nodes.xxx}}"
SINGLE_EXPR_PATTERN = r'^\s*\{\{([^{}]+)\}\}\s*$'

def resolve_input_value(value: Any, execution_context: Dict) -> Any:
    """
    표현식 평가 및 타입 보존
    
    - "{{expr}}" 형태 → 원본 타입 유지 (배열, 객체, 숫자 등)
    - "prefix {{expr}} suffix" → 문자열 보간
    - "literal" → 그대로 반환
    """
    if not isinstance(value, str):
        return value
    
    # Case A: 단일 표현식만 있는 경우
    match = re.match(SINGLE_EXPR_PATTERN, value)
    if match:
        expr_path = match.group(1).strip()
        # 원본 타입을 보존하여 반환
        return evaluate_expression(expr_path, execution_context)
    
    # Case B: 문자열 템플릿 (복합 보간)
    def replacer(m):
        expr_path = m.group(1).strip()
        result = evaluate_expression(expr_path, execution_context)
        return str(result) if result is not None else ""
    
    return re.sub(r'\{\{([^{}]+)\}\}', replacer, value)
```

**예시:**

```python
# Case A: 배열 타입 보존
resolve_input_value(
    "{{nodes.n-asset.output.equipmentIds}}",  # "로 감싼 배열
    ctx
)
# → [102, 103]  (list 타입 유지)

# Case B: 문자열 보간
resolve_input_value(
    "Equipment: {{nodes.n-asset.output.name}}",
    ctx
)
# → "Equipment: Motor-01"  (문자열)

# Case C: 정수 보존
resolve_input_value(
    "{{nodes.n-config.output.timeout}}",
    ctx
)
# → 3000  (int 타입 유지)
```

---

## ⚠️ High Priority Issues (MVP 범위 오류)

### Issue #4: MCP 구현이 현재 v5 구조와 불일치

**심각도:** 🟠 High  
**발견자:** Codex  
**발생 위치:** Section 4 (MCP 구현 명세)

#### 문제

문서는 **Stdio와 SSE 기반 직접 MCP 구현**을 제시하지만, 현재 v5는 이미 **HTTP 기반 MCP 중계 서버**를 사용하고 있습니다.

**현재 v5 구조:**
```
ont_platform (FastAPI)
  ↓ (HTTP 호출)
s2_factory_mcp / s2_customer_mcp (HTTP 서버)
  ↓ (stdio)
MCP 도구들
```

#### 해결책: MVP는 `mcp_http` 중심 (2가지 호출 방식)

**새로운 타입 정의:**

```typescript
type SkillImplementationType =
  | "builtin"      // 온톨로지 조회, 재인용 등 내부 로직
  | "http"         // 일반 HTTP API
  | "mcp_http"     // ← MVP 우선: HTTP 기반 MCP 중계 호출
  | "custom";      // Phase 2+: Python 코드 (저장만)
```

**⚠️ 중요: mcp_http의 두 가지 호출 방식**

현재 프로젝트의 s1_customer_mcp, s2_factory_mcp는 **tool-specific endpoint** 방식을 사용합니다.

| 방식 | 엔드포인트 | 요청 형태 | 예시 |
|------|---------|---------|------|
| **jsonrpc_proxy** | `/mcp` (단일) | JSON-RPC wrapper | 향후 표준 MCP 서버용 |
| **tool_endpoint** | `/mcp/tools/{tool_id}` | 직접 arguments | 현재 v5 mock MCP |

**Example 1: tool_endpoint (현재 v5 구조) ✅ 권장**

```json
{
  "id": "factory-comment-create",
  "name": "공장 게시판 댓글 등록",
  "implementation": {
    "type": "mcp_http",
    "callStyle": "tool_endpoint",
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

**Example 2: jsonrpc_proxy (표준 방식, Phase 2+)**

```json
{
  "id": "external-service-tool",
  "implementation": {
    "type": "mcp_http",
    "callStyle": "jsonrpc_proxy",
    "endpoint": "http://mcp-server:3000/mcp",
    "tool": "service.action",
    "timeout": 10000
  }
}
```

**구현 로직:**

```python
class SkillExecutor:
    def execute(self, skill: Skill, input_data: Dict) -> Dict:
        impl = skill.implementation
        
        if impl.type == "builtin":
            return self._execute_builtin(skill, input_data)
        elif impl.type == "http":
            return self._execute_http(impl, input_data)
        elif impl.type == "mcp_http":
            return self._execute_mcp_http(impl, input_data)
        elif impl.type == "custom":
            raise NotImplementedError("Phase 2+")
    
    def _execute_mcp_http(self, impl: MCPHttpConfig, input_data: Dict) -> Dict:
        """HTTP로 MCP 도구 호출"""
        import requests
        
        if impl.callStyle == "tool_endpoint":
            # ✅ 현재 v5: 직접 tool-specific endpoint에 arguments 전송
            response = requests.post(
                impl.endpoint,
                json=input_data,
                timeout=impl.timeout / 1000
            )
        else:  # jsonrpc_proxy
            # Phase 2+: JSON-RPC wrapper로 감싸서 전송
            response = requests.post(
                impl.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": impl.tool,
                        "arguments": input_data
                    }
                },
                timeout=impl.timeout / 1000
            )
        
        response.raise_for_status()
        
        if impl.callStyle == "tool_endpoint":
            return response.json()  # 직접 결과 반환
        else:
            return response.json().get("result", {})  # JSON-RPC 래퍼 벗김
```

**이점:**
- ✅ 현재 v5 구조와 일치 (tool_endpoint)
- ✅ 향후 표준 MCP 확장 가능 (jsonrpc_proxy)
- ✅ stdio 프로세스 관리 복잡도 제거
- ✅ 기존 MCP 클라이언트 재사용
- ✅ Phase 1에서 구현 가능

---

### Issue #5: HTTP 인증 정보 매핑 모호

**심각도:** 🟠 High  
**발견자:** Codex  
**발생 위치:** Section 3.1

#### 문제

```json
"credentialMapping": {
  "auth": "SMTP_USERNAME:SMTP_PASSWORD"
}
```

어떤 방식으로 인증을 넘길지 불명확함:
- Basic Auth?
- Bearer Token?
- HTTP Header?
- Query Parameter?
- SMTP 설정?

#### 해결책: 명시적인 인증 구조

```json
{
  "id": "send-email",
  "implementation": {
    "type": "http",
    "endpoint": "https://api.email.service/send",
    "method": "POST",
    "requiredCredentials": ["SMTP_USERNAME", "SMTP_PASSWORD"],
    "auth": {
      "type": "basic",
      "username": "${SMTP_USERNAME}",
      "password": "${SMTP_PASSWORD}"
    }
  }
}
```

또는 Bearer Token:

```json
{
  "implementation": {
    "type": "http",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}"
    },
    "requiredCredentials": ["API_TOKEN"]
  }
}
```

---

### Issue #6: GraphNodeKind 전체 재정의의 위험

**심각도:** 🟠 High  
**발견자:** Codex  
**발생 위치:** Section 6.1

#### 문제

문서가 모든 `GraphNodeKind`를 나열하면, 구현자가 기존 타입을 실수로 삭제할 수 있습니다.

#### 해결책: "추가" 명시

```typescript
// ✅ 권장: 기존 타입은 그대로, 새 타입만 추가
export type GraphNodeKind =
  | ExistingGraphNodeKind
  | "skill"
  | "custom_code";

// ❌ 피해야 할 방식: 전체 재정의
export type GraphNodeKind = "..." | "skill" | "custom_code"
```

문서에는 명확히:

> ⚠️ 주의: 아래는 `skill`, `custom_code` 두 타입을 기존 `GraphNodeKind`에 **추가**하는 것입니다. 기존 타입을 삭제하지 않습니다.

---

## 📋 Medium Priority Issues (코드 명확성)

### Issue #7: Custom Code 실행 코드는 Phase 1 문서에서 제거

**심각도:** 🟡 Medium  
**발견자:** Codex  
**발생 위치:** Section 7.2

#### 문제

표에서는 "Phase 1: Custom Code 저장만, 실행 불가"라고 했는데, 바로 위에 `execute_custom_code_with_timeout` 구현 예시가 있어 혼란 유발.

#### 해결책

**Option A: Phase 1 본문에서 제거**
- Section 7.1 (금지 패턴) 만 유지
- 실행 코드는 부록이나 Phase 3 문서로 이동

**Option B: 명확한 정책 명시**

```
⛔ Phase 1 구현 정책

Custom Skill은 저장 및 편집만 가능합니다.
실행 요청 시 다음 응답을 반환합니다.

{
  "status": "blocked",
  "reason": "custom_code_execution_disabled_in_phase1",
  "message": "Custom code execution is available in Phase 3+"
}
```

---

### Issue #8: MCP stdio 예시는 의사코드임을 명시

**심각도:** 🟡 Medium  
**발견자:** Codex  
**발생 위치:** Section 4.3

#### 문제

MCP stdio 코드 예시가 **개념 수준의 의사코드**인데 마치 구현 가능한 것처럼 보임.

#### 해결책

섹션 4.3 상단에 다음 경고 추가:

```text
⚠️ 주의: 아래 코드는 MCP stdio 실행의 **개념 설명용 의사코드**입니다.

실제 구현 시에는:
1. MCP initialize/initialized 핸드셰이크
2. tools/list 호출
3. 세션 유지 및 재사용
4. 에러 처리 및 로깅
5. 프로세스 생명주기 관리

등이 필요합니다.

Phase 1에서는 MCP stdio를 구현하지 않으며, 
Phase 3에서 완전한 구현을 제공할 때까지 
mcp_http 또는 http 기반 스킬만 사용합니다.
```

---

## ✅ 최종 구현 체크리스트

03_SKILL_IMPLEMENTATION_SPEC.md 를 다음과 같이 수정한 후 구현을 시작하세요.

### A. Critical Fix (필수)

- [ ] **Section 7.2:** Custom Code 실행 코드는 Phase 1에서 제거
  - 현재 Section 7.2의 `execute_custom_code_with_timeout` 함수는 **Phase 1 문서에서 삭제**
  - signal.alarm → multiprocessing 교체 코드는 **Phase 3 부록으로 이동**
  - Phase 1: "Custom Code 실행은 불가능. Phase 3+에서 지원" 명시
  
- [ ] **Section 4.3:** MCP stdio 의사코드 경고 추가
  - Phase 1에서 제외함을 명시
  
- [ ] **Section 2.3:** 타입 캐스팅 규칙 추가
  - 단일 표현식: 원본 타입 유지
  - 복합 보간: 문자열로 변환
  - 테스트 예시 포함

### B. High Priority Fix (권장)

- [ ] **Section 4:** MCP 타입을 `mcp_http` 중심으로 재구성
  - `stdio`, `sse` 제거 또는 Phase 3로 이동
  - 현재 v5 고객사/공장 MCP 클라이언트 기반으로 예시 작성
  
- [ ] **Section 3:** HTTP 인증 정보 구조화
  - `auth.type` (basic, bearer, custom)
  - 환경변수 치환 방식 명시 (`${VAR_NAME}`)
  
- [ ] **Section 6.1:** GraphNodeKind "추가" 명시
  - 전체 재정의 아님을 강조
  - 주의 문구 추가

### C. Medium Priority Fix (선택)

- [ ] **Section 7:** Custom Code 실행 코드 제거 또는 이동
  - Phase 1 본문에서는 제외
  - 부록이나 Phase 3 문서로 이동
  
- [ ] **Section 2.2:** 표현식 정규식 완화
  - 현재: `[a-z0-9\-]+` → 더 넓은 패턴
  - Codex 제안: `"{{\\s*(nodes\\.[^.]+\\.(output|status|result)(?:\\.[\\w-]+)*)\\s*}}"`

### D. 구현 체크리스트

#### Phase 1 구현 범위

- [ ] Built-in Skill 카탈로그 API (`GET /api/skills`)
- [ ] 프로젝트별 Custom Skill 저장 API (`POST /api/skills/custom`)
- [ ] Skill Gallery UI (SkillGallery.tsx)
- [ ] 워크플로우 노드에 `skillId`, `skillConfig` 저장
- [ ] 표현식 엔진 (타입 보존 포함)
- [ ] `builtin`, `http`, `mcp_http` 실행
- [ ] 실행 결과를 `WorkflowRun.steps.output`에 저장

#### Phase 1에서 **명시적으로 제외**

- [ ] ❌ Custom Code 실행
- [ ] ❌ MCP stdio 직접 실행
- [ ] ❌ Docker 샌드박싱
- [ ] ❌ 외부 마켓플레이스

---

## 🎯 권장 Built-in Skill 목록 (v5 기준)

현재 프로젝트의 시나리오와 연결되는 스킬부터 시작:

| ID | 이름 | 타입 | 시나리오 |
|----|------|------|--------|
| `customer-comment-create` | 고객 게시판 댓글 등록 | `mcp_http` | 고객 자동댓글 |
| `factory-comment-create` | 공장 게시판 댓글 등록 | `mcp_http` | 공장 자동화 |
| `factory-maintenance-create` | 정비 지시 생성 | `mcp_http` | 공장 자동화 |
| `ontology-write` | 온톨로지 저장 | `builtin` | 공통 |
| `rag-ontology-lookup` | RAG/온톨로지 근거 조회 | `builtin` | 공통 |
| `fault-recurrence-check` | 반복 고장 확인 | `builtin` | 공장 자동화 |
| `request-classify` | 요청 분류 | `builtin` | 공통 |

---

## 🏗️ 권장 백엔드 구조

```
backend/app/
├─ api/
│  └─ skills.py                      # GET/POST/PUT/DELETE 스킬
├─ services/
│  ├─ skill_service.py               # Built-in + Custom 병합, 권한
│  ├─ skill_executor.py              # builtin/http/mcp_http 실행
│  └─ expression_renderer.py         # {{...}} 렌더링 (타입 보존)
├─ config/
│  └─ skills/
│     ├─ builtin_skills.json         # 시스템 기본 스킬
│     └─ README.md                   # 스킬 정의 가이드
└─ main.py                           # skills router 등록
```

**저장 경로 (필수):**

```python
def _custom_skill_file(ctx: TenantContext) -> Path:
    # ✅ 권장: get_project_root 사용
    return get_project_root(ctx.company_id, ctx.project_id) / "skills" / "custom_skills.json"

# ❌ 피해야 할 방식:
# path = f"storage/{company_id}/{project_id}/skills/custom_skills.json"
```

---

## 📊 최종 의견

### Codex 평가

> 이 명세서는 구현에 들어갈 수 있는 수준입니다.
> 
> 현재 v5 플랫폼은 이미 고객사/공장 MCP 중계 서버, 워크플로우 그래프 저장, 실행 이력을 갖고 있으므로, 스킬 시스템은 새 런타임을 크게 만드는 대신 **기존 워크플로우 노드 실행 구조 위에 "재사용 가능한 실행 단위"를 얹는 방식**이 최적입니다.

### Antigravity 평가

> 설계 자체는 완성도가 높습니다.
> 
> 다만 **Windows 환경, MCP 프로토콜 표준, 타입 시스템**의 3가지 실무적 세부사항에서 런타임 오류가 발생할 수 있습니다. 이 3가지만 수정하면 안전합니다.

### 종합 결론

**상태:** ✅ 구현 준비 완료 (8개 이슈 반영 후)

**다음 단계:**
1. 이 체크리스트의 모든 항목 반영
2. 03_SKILL_IMPLEMENTATION_SPEC.md 개정판 작성
3. Codex/Antigravity 최종 승인
4. Phase 1 구현 시작

---

## 📎 Appendix: 표현식 엔진 테스트 케이스

구현 후 다음 테스트를 통과하는지 확인하세요.

```python
ctx = {
    'nodes': {
        'n-asset': {
            'output': {
                'equipmentIds': [102, 103],
                'name': 'Motor-01',
                'timeout': 3000
            }
        }
    }
}

# Test 1: 배열 타입 보존
assert resolve_input_value("{{nodes.n-asset.output.equipmentIds}}", ctx) == [102, 103]
assert isinstance(..., list)

# Test 2: 정수 타입 보존
assert resolve_input_value("{{nodes.n-asset.output.timeout}}", ctx) == 3000
assert isinstance(..., int)

# Test 3: 문자열 보간
assert resolve_input_value(
    "Equipment: {{nodes.n-asset.output.name}}", 
    ctx
) == "Equipment: Motor-01"

# Test 4: 복합 보간
assert resolve_input_value(
    "[{{nodes.n-asset.output.timeout}}ms] {{nodes.n-asset.output.name}}", 
    ctx
) == "[3000ms] Motor-01"

# Test 5: 리터럴 값
assert resolve_input_value("literal_string", ctx) == "literal_string"

# Test 6: Missing field 처리
assert resolve_input_value(
    "Status: {{nodes.n-asset.output.missingField}}", 
    ctx
) == "Status: "
```

