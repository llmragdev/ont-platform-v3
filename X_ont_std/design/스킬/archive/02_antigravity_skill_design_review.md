# 스킬 시스템 설계 검토 및 분석 보고서

본 문서는 `design/스킬/SKILL_SYSTEM_DESIGN.md` 및 `design/스킬/skills_catalog.json`에 정의된 **스킬(Skill) 시스템 설계**를 검토하고 개선 방향을 분석한 보고서입니다.

---

## 🌟 설계의 주요 강점 (Strengths)

1. **유연한 3가지 경로 모델 (Marketplace vs. Ad-hoc vs. Interactive)**
   - 스킬 마켓플레이스 카탈로그를 통한 **재사용 가능 도구(Marketplace)** 개발과 노드 속성에 직접 스크립팅하는 **임시 도구(Ad-hoc)**, 실행 중 즉시 값을 패치하는 **인터랙티브 디버깅** 모델의 구분은 설계적으로 완성도가 높습니다. 재사용성과 개발 생산성의 균형을 잘 잡았습니다.
2. **JSON Schema 기반의 동적 UI 인터페이스 정의**
   - 입력(`inputSchema`)과 출력(`outputSchema`)을 표준 `JSON Schema` 규격으로 정의함으로써, 프론트엔드에서 새로운 스킬이 추가될 때 별도의 코딩 없이 자동으로 양식(Form Elements)을 렌더링하고 유효성을 검사할 수 있습니다.
3. **MCP (Model Context Protocol) 지원 선언**
   - 스킬의 구현 타입(`implementation.type`)에 `mcp`를 선언해 둠으로써, 향후 다양한 외부 LLM 연동 및 외부 Agentic Tool 연결 규격을 즉시 수용할 수 있는 아키텍처적 확장성을 확보했습니다.
4. **선언과 설정의 깔끔한 분리**
   - 공통 스킬 정의 모델(`Skill`)과 실제 워크플로우에 결합되어 필드 값을 바인딩하는 설정 모델(`WorkflowNodeData`)이 독립적으로 정의되어 있어 그래프 엔진이 가볍게 구동될 수 있습니다.

---

## 🔍 기술적 한계점 및 보완이 필요한 설계 Gap (Gaps & Risks)

### 1. 변수 바인딩 및 컨텍스트 매핑 방식의 구체성 결여 (Data Flow)
- **문제점:** 설계상 `inputMapping: { "query": "request_text" }` 와 같이 필드를 지정하지만, 이 매핑 데이터가 런타임에서 어떻게 평가(evaluate)되는지 정의되어 있지 않습니다.
  - `request_text`가 글로벌 전역 컨텍스트 변수인지, 아니면 이전 노드의 특정 출력값(`nodes['node-A'].output.keywords`)인지 모호합니다.
- **영향:** 워크플로우 엔진은 순차적인 데이터 흐름(Data Dependency)이 핵심입니다. 노드 A의 실행 결과를 노드 B의 입력 변수로 체이닝할 수 있는 **표현식 엔진(Expression Evaluator)** 설계가 추가되어야 합니다.

### 2. Built-in 스킬의 인증 및 보안 설정 (Credentials & Secrets)
- **문제점:** 이메일 전송(`send-email`)이나 외부 HTTP 요청(`http-request`) 스킬 정의에서 실제 외부 API 엔드포인트가 명시되어 있으나, 이를 기동하기 위한 **API Key, SMTP 비밀번호 등 인증 정보**를 어디에 저장하고 처리할지 누락되어 있습니다.
- **영향:** 스킬 카탈로그(`skills_catalog.json`)나 워크플로우 그래프 구조 내에 암호화되지 않은 토큰이 들어가는 보안 취약점이 발생합니다. 시스템 환경 변수나 보안 키 저장소(Secret Store)로부터 동적으로 값을 가져오는 구조가 명시되어야 합니다.

### 3. MCP 서버 세부 실행 규격 부재
- **문제점:** `mcp` 유형에 대해 구체적으로 어떠한 방식으로 통신(Stdio 방식의 로컬 프로세스 기동, 혹은 SSE 방식의 원격 엔드포인트 연결)할지 정보가 빠져있습니다.
- **영향:** MCP 도구를 마켓플레이스에 등록할 때 필요한 부가 속성(예: Stdio 커맨드 경로, 실행 인자값 등)이 구조화되지 못해 실제 구현 단계에서 스키마 충돌이 발생할 수 있습니다.

### 4. 코드 실행 샌드박스(Sandbox) 적용 지연에 따른 보안 위협
- **문제점:** Phase 1(MVP) 단계에서는 보안 검증이나 샌드박싱 없이 사용자 코드를 서버 측에서 직접 구동하도록 설계되었습니다.
- **영향:** 비록 로컬이나 신뢰하는 환경일지라도 backend 프로세스에서 Python `eval` / `exec`이나 검증되지 않은 코드를 무제한 실행할 경우, 파일 시스템 파괴나 외부 악성코드 삽입 등의 공격에 매우 취약합니다.

---

## 💡 구체적인 아키텍처 개선 제안 (Recommendations)

### 🎯 제안 1: 템플릿 표현식 엔진 설계 추가
노드의 입력 매핑 필드에 변수 평가 식을 허용해야 합니다. `JsonPath`나 더 직관적인 중괄호 패턴(`{{nodes.nodeId.output.property}}`)을 사용하는 식 평가 레이어를 기획하십시오.
* **노드 설정 예시:**
```json
{
  "id": "n-notify-task",
  "type": "skill",
  "data": {
    "skillId": "send-email",
    "skillConfig": {
      "inputMapping": {
        "to": "manager@factory.com",
        "subject": "[고장 경보] {{nodes.n-asset-map.output.equipmentName}}",
        "body": "발생 이벤트 상세: {{nodes.n-fault-register.output.details}}"
      }
    }
  }
}
```

### 🎯 제안 2: 자격 증명 요구사항(Credentials Requirement) 도입
스킬 정의 내에 자격 증명이 필요한 키값 목록을 기재하고, 실행 엔진이 동작할 때 환경변수 또는 암호화된 `.env`에서 자격증명을 불러오도록 스키마를 보완합니다.
```json
{
  "id": "send-email",
  "name": "Send Email",
  "requiredCredentials": ["SMTP_PASSWORD", "SMTP_USERNAME"],
  "implementation": {
    "type": "http",
    "endpoint": "https://api.email.service/send"
  }
}
```

### 🎯 제안 3: MCP 구현 명세 보강
MCP 스킬을 위한 전용 환경 설정 블록(`mcpConfig`)을 추가하여 stdio 또는 sse 방식의 연결 정보를 명확히 담도록 설계합니다.
```typescript
interface Skill {
  implementation: {
    type: 'mcp';
    mcpConfig?: {
      transport: 'stdio' | 'sse';
      command?: string;         // 예: 'npx'
      args?: string[];          // 예: ['-y', '@modelcontextprotocol/server-postgres']
      env?: Record<string, string>;
      url?: string;             // SSE 서버 주소
    };
  };
}
```

### 🎯 제안 4: MVP(Phase 1) 단계 임시 샌드박스 안전장치 적용
컨테이너 환경(Docker)이 갖춰지기 이전인 Phase 1에서도 최소한의 AST 분석을 통해 dangerous 라이브러리 반입을 금지하는 가드레일을 적용해야 합니다.
- Python 코드 실행 전에 `import os`, `import sys`, `import subprocess`, `eval(`, `exec(` 키워드가 포함되었는지 확인하고 차단하는 검증 모듈 적용.
- 무한 루프 차단을 위한 실행 타임아웃 제한(예: 3초 초과 시 스레드 강제 중단).
