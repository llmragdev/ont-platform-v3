# 스킬 시스템 구현 명세서

**작성일:** 2026-06-14  
**버전:** 1.0  
**대상:** Codex/Antigravity 검토 의견 반영  
**범위:** MVP (Phase 1) 구현 가이드

---

## 📑 목차

1. 스킬/액션/온톨로지 구분
2. 변수 바인딩 및 표현식 엔진
3. 인증 정보 관리
4. MCP 구현 명세
5. 저장 구조 및 위치
6. v5 타입 확장
7. MVP 샌드박스 규칙
8. 구현 예시

---

## 1. 스킬 / 액션 / 온톨로지 구분

이 세 가지는 비슷해 보이지만 역할이 명확히 다릅니다.

### 개념 정의

| 개념 | 의미 | 저장 위치 | 예시 |
|------|------|---------|------|
| **Skill** | 워크플로우 노드가 **실행할 수 있는 기능/도구** | `skills_catalog.json` | 웹 검색, 이메일 발송, 댓글 등록 |
| **Action** | 특정 업무 객체에 사용자가 **실행 승인하는 명령** | `ActionDefinition` (온톨로지) | 주문 승인, 정비 요청 생성, 댓글 등록 |
| **Ontology** | 업무 세계의 **객체와 관계**를 설명하는 모델 | `ontology.json` | Equipment, ProductionLine, FaultEvent, MaintenanceTask |

### 워크플로우 흐름도

```text
┌──────────────────────────────────────────────────────────┐
│ 워크플로우 실행                                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 1: 현장 요청 접수                                   │
│    └─ 스킬 실행: request_input (외부 요청 수신)         │
│                                                          │
│  Step 2: 고장 분류                                       │
│    └─ 스킬 실행: category_classify (LLM 호출)           │
│                                                          │
│  Step 3: 설비 매핑                                       │
│    └─ 스킬 실행: asset_map (온톨로지 조회)              │
│       └─ 온톨로지 읽기: Equipment, ProductionLine       │
│                                                          │
│  Step 4: 정비 지시 생성                                  │
│    └─ 스킬 실행: maintenance_task_create (MCP)          │
│       └─ 액션 실행: CreateMaintenanceTask               │
│                                                          │
│  Step 5: 온톨로지 저장                                   │
│    └─ 스킬 실행: ontology_write                         │
│       └─ 온톨로지 저장: FaultEvent → MaintenanceTask    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 정리

```text
워크플로우 노드
  → 스킬을 **실행한다** (무엇을 할 것인가)
  → 실행 결과를 **액션**으로 사용자 승인 요청 가능
  → 필요하면 결과를 **온톨로지 객체/관계**로 저장한다 (업무 의미)
```

---

## 2. 변수 바인딩 및 표현식 엔진

### 문제점

현재 설계:
```json
{
  "skillConfig": {
    "inputMapping": {
      "to": "manager@company.com",
      "subject": "고장 경보"
    }
  }
}
```

**문제:** 이전 노드의 실행 결과를 입력값으로 사용할 방법이 없습니다.

### 해결책: 템플릿 표현식 엔진

#### 2.1 표현식 문법

```
{{노드ID.출력.필드경로}}
```

**예시:**

```json
{
  "skillConfig": {
    "inputMapping": {
      "to": "manager@factory.com",
      "subject": "[고장 경보] {{nodes.n-asset-map.output.equipmentName}}",
      "body": "{{nodes.n-fault-register.output.details}}\n\n근거: {{nodes.n-knowledge-lookup.output.document}}"
    }
  }
}
```

#### 2.2 파싱 규칙

```python
# 정규식
EXPRESSION_PATTERN = r'\{\{(nodes\.[a-z0-9\-]+\.[a-z]+(\.[\w]+)*)\}\}'

# 평가 함수 (의사코드)
def evaluate_expression(expr: str, execution_context: Dict) -> str:
    """
    expr: "nodes.n-asset-map.output.equipmentName"
    execution_context: {
      'nodes': {
        'n-asset-map': {
          'output': {'equipmentName': '설비-001', ...},
          'status': 'success'
        }
      }
    }
    """
    parts = expr.split('.')
    value = execution_context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return f"{{{{ERROR: {expr}}}}}"
    return str(value) if value is not None else ""
```

#### 2.3 워크플로우 실행 시 적용

```typescript
// 백엔드에서 노드 실행 전
function prepareSkillInput(
  skillConfig: SkillConfig,
  executionContext: ExecutionContext
): Record<string, unknown> {
  const prepared = {};
  
  for (const [key, value] of Object.entries(skillConfig.inputMapping)) {
    if (typeof value === 'string' && value.includes('{{')) {
      // 표현식 평가
      prepared[key] = evaluateExpression(value, executionContext);
    } else {
      // 상수값
      prepared[key] = value;
    }
  }
  
  return prepared;
}
```

#### 2.4 예시: 실제 워크플로우

```json
{
  "nodes": [
    {
      "id": "n-category-classify",
      "type": "skill",
      "data": {
        "label": "고장/품질 분류",
        "skillId": "category-classify"
      }
    },
    {
      "id": "n-asset-map",
      "type": "skill",
      "data": {
        "label": "공장-라인-설비 매핑",
        "skillId": "asset-map",
        "skillConfig": {
          "inputMapping": {
            "category": "{{nodes.n-category-classify.output.category}}"
          }
        }
      }
    },
    {
      "id": "n-send-email",
      "type": "skill",
      "data": {
        "label": "정비팀 알림",
        "skillId": "send-email",
        "skillConfig": {
          "inputMapping": {
            "to": "maintenance-team@factory.com",
            "subject": "[{{nodes.n-category-classify.output.severity}}] {{nodes.n-asset-map.output.equipmentName}}",
            "body": "카테고리: {{nodes.n-category-classify.output.category}}\n설비: {{nodes.n-asset-map.output.equipmentName}}\n라인: {{nodes.n-asset-map.output.lineName}}"
          }
        }
      }
    }
  ]
}
```

---

## 3. 인증 정보 관리

### 문제점

현재 `send-email` 스킬은 SMTP 엔드포인트를 노출하고 있으나, 비밀번호나 API Key는 저장되지 않습니다.

```json
{
  "id": "send-email",
  "implementation": {
    "type": "http",
    "endpoint": "https://api.email.service/send"  // ← 비밀번호 어디에?
  }
}
```

### 해결책: requiredCredentials + 환경변수

#### 3.1 스킬 정의에 필요 자격 증명 명시

```json
{
  "id": "send-email",
  "name": "Send Email",
  "description": "이메일 전송",
  "requiredCredentials": [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD"
  ],
  "implementation": {
    "type": "http",
    "endpoint": "https://api.email.service/send",
    "credentialMapping": {
      "auth": "SMTP_USERNAME:SMTP_PASSWORD"
    }
  }
}
```

#### 3.2 MCP 스킬의 자격 증명

```json
{
  "id": "factory-comment-create",
  "name": "공장 게시판 댓글 등록",
  "requiredCredentials": [
    "MCP_FACTORY_SERVER_TOKEN"
  ],
  "implementation": {
    "type": "mcp",
    "mcpConfig": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-factory"],
      "env": {
        "FACTORY_API_KEY": "${MCP_FACTORY_SERVER_TOKEN}"
      }
    }
  }
}
```

#### 3.3 워크플로우 실행 시 자격 증명 주입

```python
# 백엔드에서 스킬 실행 전
def prepare_skill_with_credentials(
    skill: Skill,
    credentials_store: CredentialsStore
) -> Dict:
    """
    스킬에 필요한 자격 증명을 환경변수에서 주입
    """
    prepared = {**skill.to_dict()}
    
    if skill.requiredCredentials:
        # 모든 필요 자격 증명이 있는지 확인
        missing = [
            cred for cred in skill.requiredCredentials
            if cred not in credentials_store
        ]
        if missing:
            raise CredentialsMissingError(f"Missing: {missing}")
        
        # 자격 증명 주입
        if skill.implementation.type == 'mcp':
            for key, placeholder in (skill.implementation.mcpConfig.env or {}).items():
                if placeholder.startswith('${') and placeholder.endswith('}'):
                    cred_name = placeholder[2:-1]
                    prepared['env'][key] = credentials_store[cred_name]
    
    return prepared
```

#### 3.4 저장소 구조

```text
backend/app/config/
├─ skills/
│  └─ builtin_skills.json          # Built-in 스킬 정의 (requiredCredentials 명시)
│
backend/
├─ .env.local                        # 로컬 개발 (Git 제외)
├─ .env.example                      # 예시
│  └─ SMTP_PASSWORD=your_password
│  └─ MCP_FACTORY_SERVER_TOKEN=token

운영 환경:
├─ 환경변수 또는 Vault/Secret Manager에서 주입
```

---

## 4. MCP 구현 명세

### 4.1 MCP 스킬 타입 확장

```typescript
interface MCPConfig {
  // 통신 방식
  transport: 'stdio' | 'sse';

  // stdio 모드 (로컬 프로세스)
  command?: string;                    // 예: 'npx'
  args?: string[];                     // 예: ['-y', '@modelcontextprotocol/server-factory']
  cwd?: string;                        // 작업 디렉토리

  // SSE 모드 (원격 서버)
  url?: string;                        // MCP 서버 URL
  headers?: Record<string, string>;    // 인증 헤더

  // 공통
  env?: Record<string, string>;        // 환경변수 (자격 증명 포함)
  timeout?: number;                    // 타임아웃 (ms)
}

interface Skill {
  implementation: {
    type: 'mcp';
    mcpConfig: MCPConfig;
    tool: string;                      // 실행할 도구 이름 (예: 'comment.create')
    server: string;                    // 서버 식별자 (예: 's2_factory_mcp')
  };
}
```

### 4.2 실제 예시

#### 예시 1: Stdio 방식 (로컬)

```json
{
  "id": "factory-comment-create",
  "name": "공장 게시판 댓글 등록",
  "implementation": {
    "type": "mcp",
    "server": "s2_factory_mcp",
    "tool": "comment.create",
    "mcpConfig": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-factory"],
      "cwd": "/opt/mcp-servers/factory",
      "env": {
        "FACTORY_API_KEY": "${MCP_FACTORY_SERVER_TOKEN}",
        "LOG_LEVEL": "info"
      },
      "timeout": 10000
    }
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "boardId": { "type": "string" },
      "content": { "type": "string" }
    },
    "required": ["boardId", "content"]
  }
}
```

#### 예시 2: SSE 방식 (원격)

```json
{
  "id": "web-search",
  "name": "Web Search (via MCP)",
  "implementation": {
    "type": "mcp",
    "server": "mcp_web_search",
    "tool": "search",
    "mcpConfig": {
      "transport": "sse",
      "url": "https://mcp-server.example.com/sse",
      "headers": {
        "Authorization": "Bearer ${MCP_WEB_SEARCH_TOKEN}"
      },
      "timeout": 30000
    }
  }
}
```

### 4.3 백엔드 실행 로직

```python
class MCPSkillExecutor:
    def execute(self, skill: Skill, input_data: Dict) -> Dict:
        config = skill.implementation.mcpConfig
        
        if config.transport == 'stdio':
            return self._execute_stdio(config, skill.tool, input_data)
        elif config.transport == 'sse':
            return self._execute_sse(config, skill.tool, input_data)
    
    def _execute_stdio(self, config: MCPConfig, tool: str, input_data: Dict):
        """로컬 프로세스를 통해 MCP 실행"""
        import subprocess
        import json
        
        env = os.environ.copy()
        env.update(config.env or {})
        
        # MCP 도구 호출 (stdin/stdout)
        process = subprocess.Popen(
            [config.command, *config.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=config.cwd,
            env=env
        )
        
        request = {
            "jsonrpc": "2.0",
            "method": "call_tool",
            "params": {
              "name": tool,
              "arguments": input_data
            }
        }
        
        try:
            stdout, stderr = process.communicate(
                input=json.dumps(request).encode(),
                timeout=config.timeout / 1000
            )
            result = json.loads(stdout.decode())
            return result.get('result', {})
        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError(f"MCP skill '{tool}' timeout")
```

---

## 5. 저장 구조 및 위치

### 현재 (잘못됨)
```text
design/스킬/
└─ skills_catalog.json    # ← 설계 문서로만 사용
```

### 변경 후 (올바름)

```text
ont_platform/v5/backend/app/config/skills/
├─ builtin_skills.json         # 시스템 기본 스킬 (Git 관리)
├─ README.md                    # 스킬 정의 가이드
└─ examples/
   └─ factory_scenario.json     # 공장 시나리오 스킬 예시

ont_platform/storage/
├─ {company_id}/
│  └─ {project_id}/
│     ├─ workflow_graphs.json   # 기존
│     └─ skills/
│        └─ custom_skills.json  # 프로젝트별 커스텀 스킬
│
design/스킬/                    # 설계 문서만 유지
├─ SKILL_SYSTEM_DESIGN.md
├─ 01_Codex_스킬_시스템_검토보고서.md
├─ 02_antigravity_skill_design_review.md
├─ 03_SKILL_IMPLEMENTATION_SPEC.md
└─ skills_catalog.json          # 설계 샘플 (참고용)
```

---

## 6. v5 타입 확장

### 6.1 프론트엔드 타입

**파일:** `frontend/src/types/api.ts`

```typescript
// 기존 타입 확장
export type GraphNodeKind =
  | 'request_input'
  | 'intent_classify'
  | 'equipment_map'
  | 'recurrence_check'
  | 'knowledge_lookup'
  | 'policy_search'
  | 'evidence_gate'
  | 'approval_check'
  | 'action_plan'
  | 'draft_response'
  | 'customer_mcp_comment_create'
  | 'maintenance_task'
  | 'quality_link'
  | 'ontology_write'
  | 'human_handoff'
  | 'notify_user'
  | 'start'
  | 'condition'
  | 'llm'
  | 'http'
  | 'end'
  // ← 새 타입 추가
  | 'skill'
  | 'custom_code';

// 스킬 관련 타입
export interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  author: string;
  tags?: string[];

  // 스키마
  inputSchema: Record<string, any>;
  outputSchema: Record<string, any>;

  // 구현
  implementation: {
    type: 'builtin' | 'custom' | 'http' | 'mcp';
    endpoint?: string;                           // http
    code?: string;                               // custom
    mcpConfig?: MCPConfig;                       // mcp
  };

  // 보안
  requiredCredentials?: string[];

  // 메타데이터
  createdAt?: string;
  updatedAt?: string;
}

export interface MCPConfig {
  transport: 'stdio' | 'sse';
  command?: string;
  args?: string[];
  cwd?: string;
  url?: string;
  headers?: Record<string, string>;
  env?: Record<string, string>;
  timeout?: number;
}

// 노드 데이터에 스킬 정보 추가
export interface GraphNodeData {
  label?: string;
  prompt?: string;
  
  // ← 새 필드
  skillId?: string;
  skillVersion?: string;
  skillConfig?: {
    inputMapping?: Record<string, string>;     // 변수 바인딩
    outputMapping?: Record<string, string>;
    parameters?: Record<string, unknown>;
  };
}
```

---

## 7. MVP 샌드박스 규칙

### 7.1 Phase 1 제약사항

**Python 코드 실행 금지 목록:**

```python
FORBIDDEN_PATTERNS = [
    r'\bimport\s+(os|sys|subprocess|socket|shutil|tempfile)',
    r'\bfrom\s+(os|sys|subprocess|socket|shutil|tempfile)\s+import',
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\bopen\s*\(',
    r'__import__',
]

def validate_custom_skill_code(code: str) -> bool:
    """Python 코드 안전성 검증"""
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return False
    return True
```

### 7.2 실행 제약

```python
# 타임아웃 제한
def execute_custom_code_with_timeout(code: str, input_data: Dict, timeout_sec: int = 3):
    """3초 이내 실행, 초과 시 강제 중단"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Custom code execution timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)
    
    try:
        exec_globals = {'input': input_data}
        exec(code, exec_globals)
        signal.alarm(0)  # 타이머 해제
        return exec_globals.get('output')
    except TimeoutError:
        raise
    finally:
        signal.alarm(0)
```

### 7.3 운영 가이드

| 실행 환경 | Built-in | HTTP | MCP | Custom Code |
|----------|----------|------|-----|-------------|
| **MVP (Phase 1)** | ✅ 가능 | ✅ 가능 | ✅ 가능 | ❌ 저장만 (실행 불가) |
| **Phase 2** | ✅ 가능 | ✅ 가능 | ✅ 가능 | ⚠️ 검증 후 실행 |
| **Phase 3** | ✅ 가능 | ✅ 가능 | ✅ 가능 | ✅ Docker 샌드박스 실행 |

---

## 8. 구현 예시

### 예시 1: 공장 자동화 워크플로우

**시나리오:** 현장 고장 요청 → 분류 → 설비 매핑 → 정비팀 알림 → 온톨로지 저장

```json
{
  "id": "wf-factory-fault-response",
  "name": "공장 반복 고장 자동 대응",
  "nodes": [
    {
      "id": "n-input",
      "type": "request_input",
      "data": {
        "label": "현장 요청 입력"
      }
    },
    {
      "id": "n-classify",
      "type": "skill",
      "data": {
        "label": "고장/품질 분류",
        "skillId": "category-classify",
        "skillConfig": {
          "inputMapping": {
            "text": "{{nodes.n-input.output.faultDescription}}"
          }
        }
      }
    },
    {
      "id": "n-asset-map",
      "type": "skill",
      "data": {
        "label": "공장-라인-설비 매핑",
        "skillId": "asset-map",
        "skillConfig": {
          "inputMapping": {
            "category": "{{nodes.n-classify.output.category}}"
          }
        }
      }
    },
    {
      "id": "n-recurrence-check",
      "type": "skill",
      "data": {
        "label": "반복 고장 확인",
        "skillId": "recurrence-check",
        "skillConfig": {
          "inputMapping": {
            "equipmentId": "{{nodes.n-asset-map.output.equipmentId}}",
            "faultType": "{{nodes.n-classify.output.faultType}}"
          }
        }
      }
    },
    {
      "id": "n-notify",
      "type": "skill",
      "data": {
        "label": "정비팀 알림",
        "skillId": "factory-comment-create",
        "skillConfig": {
          "inputMapping": {
            "boardId": "maintenance-requests",
            "content": "[{{nodes.n-classify.output.severity}}] {{nodes.n-asset-map.output.equipmentName}} - {{nodes.n-classify.output.description}}"
          }
        }
      }
    },
    {
      "id": "n-ontology-save",
      "type": "skill",
      "data": {
        "label": "온톨로지 저장",
        "skillId": "ontology-write",
        "skillConfig": {
          "inputMapping": {
            "entityType": "FaultEvent",
            "properties": "{{nodes.n-classify.output}}"
          }
        }
      }
    }
  ],
  "edges": [
    { "source": "n-input", "target": "n-classify" },
    { "source": "n-classify", "target": "n-asset-map" },
    { "source": "n-asset-map", "target": "n-recurrence-check" },
    { "source": "n-recurrence-check", "target": "n-notify" },
    { "source": "n-notify", "target": "n-ontology-save" }
  ]
}
```

### 예시 2: 커스텀 스킬 (저장만, Phase 1)

```json
{
  "id": "custom-extract-keywords",
  "name": "Extract Keywords",
  "description": "텍스트에서 주요 키워드를 추출",
  "category": "text",
  "author": "ontology-team",
  "version": "1.0",
  "implementation": {
    "type": "custom",
    "code": "def execute(input):\n    import re\n    from collections import Counter\n    \n    text = input.get('text', '')\n    max_keywords = input.get('maxKeywords', 10)\n    min_length = input.get('minLength', 2)\n    \n    # 텍스트 전처리\n    words = re.findall(r'\\b[가-힣a-z]+\\b', text.lower())\n    words = [w for w in words if len(w) >= min_length]\n    \n    # 키워드 추출\n    counter = Counter(words)\n    keywords = [\n        {'word': word, 'frequency': count, 'score': count / len(words)}\n        for word, count in counter.most_common(max_keywords)\n    ]\n    \n    return {'keywords': keywords}"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "text": { "type": "string" },
      "maxKeywords": { "type": "integer", "default": 10 },
      "minLength": { "type": "integer", "default": 2 }
    },
    "required": ["text"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "keywords": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "word": { "type": "string" },
            "frequency": { "type": "integer" },
            "score": { "type": "number" }
          }
        }
      }
    }
  }
}
```

---

## 9. 체크리스트: MVP 구현 단계

### Phase 1 (지금 ~ 2주)

- [ ] 타입 정의 (GraphNodeKind, Skill, MCPConfig)
- [ ] Built-in Skill 5개 정의 (backend/config/skills/builtin_skills.json)
- [ ] 스킬 갤러리 UI (SkillGallery.tsx)
- [ ] 표현식 엔진 (evaluateExpression)
- [ ] 스킬 설치 로직 (노드 추가)
- [ ] API 클라이언트 (skills CRUD)

### Phase 2 (2주 후)

- [ ] 커스텀 스킬 생성/편집 UI
- [ ] 저장 구조 (storage/{company_id}/{project_id}/skills/)
- [ ] 자격 증명 관리 (requiredCredentials)
- [ ] MCP 실행 (stdio 모드)

### Phase 3 (1개월 후)

- [ ] Docker 샌드박싱
- [ ] Python 코드 안전 실행
- [ ] 고급 표현식 (조건부, 반복)

---

