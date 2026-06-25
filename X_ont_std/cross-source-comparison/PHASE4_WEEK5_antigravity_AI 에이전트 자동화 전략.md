# AI 에이전트 자동화 전략 및 보안 샌드박스 우회 가이드

본 문서는 개발 프로세스에서 AI 에이전트(Gemini 기반 Antigravity, Anthropic 기반 Claude Code 등)를 운용할 때, 안전하지 않은 명령어 실행을 차단하는 보안 샌드박스(Sandbox) 정책으로 인해 발생하는 불필요한 승인 팝업(mcp/ask)을 로컬 개발 환경에서 해제하고 에이전트의 자동화 효율을 극대화하기 위한 가이드입니다.

---

## 1. 샌드박스 경고 발생 원인 및 쉘 명령어 차단 메커니즘

AI 에이전트는 로컬 운영체제(OS) 환경에 직접적인 위해를 가할 수 있는 위험한 명령(예: `rm -rf /`, `curl | sh` 등)의 실행을 방지하기 위해 샌드박스 보호 장치를 가동합니다.

1.  **화이트리스트 기반 첫 단어(Executable/Binary) 매칭**:
    *   보안 엔진은 실행하려는 명령어의 첫 번째 단어(예: `git`, `pytest`, `python` 등)가 허용 목록(Allowed List)에 등록되어 있는지 검증합니다.
2.  **복합 명령어(Chained Commands) 무력화**:
    *   `cd <경로> ; pytest <파일> | Select-Object` 와 같이 세미콜론(`;`), 앰퍼샌드(`&&`), 파이프라인(`|`)을 이용해 다중 명령을 체이닝하면, 첫 단어 매칭 규칙이 붕괴되어 전체 명령이 `command(*)` 즉 임의 쉘 실행 시도로 분류되어 차단됩니다.
3.  **OS 내장 명령어(Shell Built-in) 매칭 한계**:
    *   `cd`와 같은 쉘 내장 명령어는 독립적인 바이너리가 존재하지 않으므로 실행 기준 화이트리스트 검사기에서 차단 대상으로 오판받기 쉽습니다.

---

## 2. Gemini 기반 에이전트 (Antigravity/Gemini Agent) 자동화 설정

Gemini 및 MCP(Model Context Protocol) 기반 아키텍처 환경에서는 에이전트 설정 및 보안 허용 규칙이 로컬 AppData 또는 홈 폴더 하위의 `.gemini` 경로에서 관리됩니다.

### 2.1 전역 설정 파일 수동 편집
*   **설정 파일 위치 (Windows)**:
    *   `C:\Users\<사용자명>\.gemini\antigravity\mcp_config.json`
    *   `C:\Users\<사용자명>\.gemini\config\config.json`
*   **설정 방법**:
    JSON 파일 내 `permissions` 또는 `allowed_commands` 배열에 차단되는 명령어를 명시적으로 추가하고 `"allowed"`로 상태를 지정합니다.

```json
{
  "permissions": {
    "commands": [
      { "command": "git", "status": "allowed" },
      { "command": "pytest", "status": "allowed" },
      { "command": "python", "status": "allowed" },
      { "command": "cd", "status": "allowed" },
      { "command": "Select-Object", "status": "allowed" }
    ]
  }
}
```

### 2.2 대화형 팝업 등록
*   처음 실행하는 명령어의 경우 CLI 팝업 또는 UI 모달이 뜰 때, 일회성 허용인 `Allow` 대신 **`Always allow this command(항상 이 명령 허용)`**을 선택하면 위 JSON 파일에 자동으로 규칙이 갱신되어 저장됩니다.

---

## 3. Claude Code 기반 에이전트 (Claude Code CLI) 자동화 설정

Anthropic에서 제공하는 Claude Code CLI 환경에서는 설정 명령어(`claude config`)와 홈 디렉토리 내 `.config/claude` 폴더를 사용하여 권한을 제어합니다.

### 3.1 CLI 설정 명령어를 통한 즉각 변경 (권장)
터미널 창에 직접 아래 명령어를 입력하여 대화형으로 설정을 조절하거나 자동 승인을 활성화할 수 있습니다.

```bash
# 1. Claude Code 설정 대화창 실행 및 전체 상태 조회
claude config

# 2. 테스트/조회 등 위험하지 않은 명령의 자동 승인(Auto-Approve) 활성화
claude config set autoApprove true
```

### 3.2 로컬 설정 파일 수동 편집
*   **설정 파일 위치 (Windows)**:
    *   `C:\Users\<사용자명>\.config\claude\settings.json`
    *   `C:\Users\<사용자명>\.claude\config.json`
*   **설정 방법**:
    `settings.json` 파일을 열어 `autoApproveCommands` 배열에 자동 실행을 허용할 도구명 및 쉘 유틸리티명을 추가합니다.

```json
{
  "autoApproveCommands": [
    "pytest",
    "git",
    "cd",
    "npm",
    "Select-Object",
    "grep"
  ]
}
```

### 3.3 실행 시 샌드박스 비활성화 (보안 수준 최하 설정)
보안 경고 없이 모든 로컬 터미널 명령을 자유롭게 실행하게 하려면 에이전트 시작 시 아래 인자를 추가합니다.
*   *주의: 신뢰할 수 없는 인터넷 리소스를 다룰 때는 보안에 주의해야 합니다.*
```bash
claude --dangerously-disable-sandbox
```

---

## 4. 에이전트 명령 실행 최적화를 위한 훈육(Prompting) 전략

설정 파일을 건드리지 않고도 프롬프트 작성 가이드(Instruction)를 통해 승인 팝업을 원천 차단할 수 있습니다.

### 4.1 단일 명령어 분할 지시 (Chaining 해제)
에이전트에게 복합 명령어를 지시하지 않고 단건으로 나누어 동작하도록 가이드합니다.
*   **차단 대상**: `cd ont_platform/v4/backend; pytest tests/performance/` (세미콜론 결합)
*   **정상 동작**: 
    1.  `cd ont_platform/v4/backend`
    2.  `pytest tests/performance/` (따로 나누어 실행하면 pytest 단독 매칭으로 무검증 통과)

### 4.2 시스템/에이전트 가이드 프롬프트 예시
프로젝트 루트 또는 `System Prompt`에 아래 제약사항을 추가해 두면, 에이전트가 알아서 팝업이 뜨지 않는 안전한 단일 명령어로 변환하여 작동합니다.

> "터미널 명령어를 실행할 때는 세미콜론(;), 앰퍼샌드(&&), 파이프라인(|)을 사용하여 여러 명령을 묶지 마십시오. 항상 작업 디렉토리를 cd로 이동한 후, 다음 턴에서 본 명령어를 단독으로 실행하여 샌드박스 승인 정책을 회피하십시오."
