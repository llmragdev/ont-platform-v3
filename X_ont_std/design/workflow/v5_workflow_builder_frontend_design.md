# v5 Workflow Builder Frontend Design

Last updated: 2026-06-09

## 1. 목표

v5 프론트엔드는 단순 워크플로우 그래프 편집기를 넘어, 사용자가 직접 업무 프로세스를 조립하고 실행 결과를 검증할 수 있는 Agentic Workflow Builder가 되어야 한다.

핵심 목표:

- 다양한 블록을 캔버스에서 조립한다.
- 각 블록은 독립 실행 가능한 skill을 참조한다.
- 스킬 정의와 워크플로우 배치를 분리한다.
- 실행 중 input/output/evidence/decision을 단계별로 확인한다.
- 서비스 요청 RAG 자동댓글을 첫 번째 대표 시나리오로 구현한다.

## 2. 화면 구조

### 2.0 Workflow Home

역할:

- 사용자가 Builder로 바로 들어가기 전에 적용 가능한 업무 시나리오를 고른다.
- 현재 활성 workflow template, 최근 simulation 결과, 수동 이관/실패 현황을 요약한다.
- 엔터프라이즈 사용자에게 "무엇을 만들 수 있는가"보다 "어떤 업무를 안전하게 개선하는가"를 먼저 보여준다.

권장 구성:

```text
상단 요약
  - active workflows
  - recent runs
  - auto comment success
  - manual handoff count

Use Case Gallery
  - 서비스 요청 자동댓글
  - 권한 요청 안내
  - 정책/FAQ 문의 응답
  - 승인 후 처리 안내
  - 근거 부족 수동 이관

Recent Simulation
  - 입력 문장
  - 결과 상태
  - 사용 workflow
  - 실행 시각

Governance Snapshot
  - evidence gate enabled
  - no-answer policy enabled
  - audit logging enabled
  - relay/network policy status
```

### 2.0.1 Use Case Gallery

역할:

- 산업별/업무별 workflow template을 선택한다.
- 각 template의 적용 가능 조건, 자동화 제외 조건, 필요한 skill, 필요한 knowledge source를 보여준다.

카드 구성:

```text
Template name
업무 설명
적용 가능 조건
자동화 제외 조건
필요 skill 수
필요 knowledge source
governance policy badge
시뮬레이션 시작
Builder에서 열기
```

### 2.0.2 Template Detail

역할:

- 워크플로우 템플릿을 업무 관점에서 설명한다.
- 캔버스 preview와 필요한 skill/policy를 함께 보여준다.

권장 구성:

```text
좌측
  - 업무 설명
  - 기대 효과
  - 적용 가능 조건
  - 자동화 제외 조건

중앙
  - workflow canvas preview
  - 주요 분기 설명

우측
  - required skills
  - required knowledge sources
  - governance policy
  - network/relay policy
  - audit policy
```

### 2.1 Workflow Builder

역할:

- 워크플로우 캔버스 저작
- 노드 추가/연결/분기 설정
- 노드별 skill 선택
- 실행/저장/복제/삭제
- 실행 결과 시각화

권장 레이아웃:

```text
좌측 사이드바
  - 블록 팔레트
  - 검색/카테고리 필터

중앙 캔버스
  - React Flow 기반 노드/엣지 편집
  - 확대/축소/미니맵
  - 실행 상태 배지

우측 속성 패널
  - 선택 노드 속성
  - skill 선택
  - input mapping
  - output mapping
  - 조건/분기 설정

하단 실행 패널
  - 실행 이력
  - 노드별 결과
  - evidence
  - 오류/수동 이관 사유
```

### 2.2 Skill Manager

역할:

- skill 등록/수정/비활성화
- skill type 관리
- 입출력 스키마 관리
- prompt/RAG/API 설정 관리
- skill 단위 테스트
- 사용 중인 워크플로우 확인

권장 메뉴:

- 스킬 목록
- 스킬 상세
- 스킬 테스트
- 스킬 버전/이력
- 스킬 사용처

### 2.3 Workflow Simulation

역할:

- 입력 문장을 넣고 워크플로우 실행
- 단계별 처리 결과 확인
- 자동댓글 초안 확인
- 근거 문서 확인
- 수동 이관 여부 확인

이 화면은 Builder 하단 패널로 시작해도 되고, 이후 별도 메뉴로 분리할 수 있다.

## 3. 블록 카테고리

### 3.1 Input

- Request Input: 문장형 서비스 요청 입력
- Ticket Fetch: 외부 mock 서버 또는 티켓 시스템에서 요청 수신
- Attachment Parse: 첨부파일 텍스트 추출
- Context Load: 사용자/부서/시스템 컨텍스트 로드

### 3.2 Classifier

- Intent Classify: 단순문의, 권한요청, 장애, 변경요청 등 분류
- Artifact Change Check: 산출물 변경 여부 판단
- Security Level Check: 보안등급/민감정보 여부 판단
- Urgency Classify: 긴급도 판단

### 3.3 RAG

- FAQ Search
- Policy Search
- Similar Case Search
- Hybrid Search
- Evidence Select

### 3.4 Decision

- Evidence Gate: 근거 충분성 판단
- Auto Comment Gate: 자동댓글 가능 여부 판단
- Approval Gate: 승인/결재 필요 여부 판단
- Human Handoff Gate: 담당자 이관 여부 판단

### 3.5 Generation

- Draft Comment: 댓글 초안 생성
- Draft Answer: 답변 생성
- Summarize Request: 요청 요약
- Action Guide: 처리 가이드 생성

### 3.6 Action

- Post Comment: 댓글 등록
- Assign Owner: 담당자 배정
- Notify User: 사용자 알림
- Call HTTP: 외부 API 호출
- Create Audit Log: 감사 로그 생성

### 3.7 Guardrail

- Grounding Check: 근거 기반성 검사
- Sensitive Data Check: 민감정보 검사
- Forbidden Action Check: 금지 액션 검사
- Output Policy Check: 자동댓글 정책 검사

### 3.8 Terminal

- End Success
- End Pending
- End Manual Handoff
- End Failed

## 4. Skill과 Node의 분리

워크플로우 노드는 화면상의 실행 단계이고, skill은 실제 실행 로직이다. 두 개념을 분리해야 확장성이 생긴다.

```text
SkillDefinition
  - skill_id
  - name
  - type
  - version
  - input_schema
  - output_schema
  - config_schema
  - executor_type
  - default_config
  - enabled

WorkflowNode
  - node_id
  - label
  - block_category
  - skill_id
  - position
  - node_config_override
  - input_mapping
  - output_mapping
```

예시:

- `RAG Search` 노드는 `faq_search_v1`, `policy_search_v2`, `hybrid_search_v5` 중 하나의 skill을 참조할 수 있다.
- `Draft Comment` 노드는 동일한 생성 skill을 쓰되, 워크플로우별 prompt override를 가질 수 있다.
- `Post Comment` 노드는 mock server adapter 또는 실제 ticket adapter를 선택할 수 있다.

## 5. 프론트엔드 데이터 모델

### 5.1 WorkflowGraph

```ts
type WorkflowGraph = {
  id: string;
  name: string;
  version: number;
  status: "draft" | "active" | "archived";
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  createdAt: string;
  updatedAt: string;
};
```

### 5.2 WorkflowNode

```ts
type WorkflowNode = {
  id: string;
  type: string;
  label: string;
  category: BlockCategory;
  skillId?: string;
  position: { x: number; y: number };
  config: Record<string, unknown>;
  inputMapping?: MappingRule[];
  outputMapping?: MappingRule[];
};
```

### 5.3 WorkflowEdge

```ts
type WorkflowEdge = {
  id: string;
  source: string;
  target: string;
  label?: "Y" | "N" | "auto" | "manual" | "approval" | "error";
  condition?: string;
};
```

### 5.4 SkillDefinition

```ts
type SkillDefinition = {
  id: string;
  name: string;
  type:
    | "input"
    | "classifier"
    | "rag"
    | "decision"
    | "generation"
    | "action"
    | "guardrail"
    | "terminal";
  version: string;
  description?: string;
  inputSchema: JsonSchema;
  outputSchema: JsonSchema;
  configSchema?: JsonSchema;
  defaultConfig?: Record<string, unknown>;
  enabled: boolean;
};
```

### 5.5 NodeExecutionResult

```ts
type NodeExecutionResult = {
  runId: string;
  nodeId: string;
  skillId?: string;
  status: "pending" | "running" | "success" | "failed" | "skipped" | "handoff";
  startedAt?: string;
  endedAt?: string;
  durationMs?: number;
  input?: unknown;
  output?: unknown;
  evidence?: EvidenceItem[];
  error?: string;
  nextEdgeLabel?: string;
};
```

## 6. API 계약 초안

프론트엔드는 아래 API가 필요하다.

```text
GET    /api/v5/workflow-graphs
POST   /api/v5/workflow-graphs
GET    /api/v5/workflow-graphs/{graph_id}
PUT    /api/v5/workflow-graphs/{graph_id}
DELETE /api/v5/workflow-graphs/{graph_id}

POST   /api/v5/workflow-graphs/{graph_id}/run
GET    /api/v5/workflow-runs/{run_id}
GET    /api/v5/workflow-runs/{run_id}/events

GET    /api/v5/skills
POST   /api/v5/skills
GET    /api/v5/skills/{skill_id}
PUT    /api/v5/skills/{skill_id}
POST   /api/v5/skills/{skill_id}/test
GET    /api/v5/skills/{skill_id}/usages
```

초기에는 기존 v3/v4 API와 호환되도록 adapter를 둘 수 있지만, v5 화면은 `/api/v5` 기준으로 설계한다.

## 7. 서비스 요청 RAG 자동댓글 화면 흐름

대표 시나리오:

```text
Request Input
  -> Intent Classify
  -> Artifact Change Check
  -> RAG Search
  -> Evidence Gate
  -> Draft Comment
  -> Validate Comment
  -> Post Comment
  -> End Success
```

수동 이관 시나리오:

```text
Evidence Gate
  -> End Manual Handoff
```

승인 필요 시나리오:

```text
Approval Gate
  -> Notify User
  -> End Pending
```

화면에서 반드시 보여야 하는 값:

- 입력 요청 원문
- 분류 결과
- 변경 여부 판단
- 검색된 근거 문서
- 자동댓글 초안
- 검증 결과
- 댓글 등록 결과
- 수동 이관 사유

## 8. 구현 우선순위

1. v5 frontend `src` 복원
2. Workflow Home과 Use Case Gallery 기본 화면 추가
3. 기존 WorkflowGraph를 v5 메뉴에서 정상 표시
4. 블록 팔레트 카테고리 확장
5. 우측 속성 패널을 skill 선택 중심으로 개편
6. Skill Manager 목록/상세 화면 추가
7. workflow run 결과 패널에 node input/output/evidence 표시
8. 서비스 요청 RAG 자동댓글 샘플 그래프 추가
9. v5 backend API와 연결
10. smoke test 및 screenshot 검증

## 9. 설계 판단

Skill Manager는 별도 화면으로 둔다. 워크플로우 캔버스에서 모든 프롬프트, RAG 설정, API 인증, 입출력 스키마를 직접 편집하면 화면이 복잡해지고 재사용성이 떨어진다.

권장 분리:

- Workflow Builder: 순서, 분기, 노드 배치, 실행 상태
- Skill Manager: 실행 단위의 정의, 설정, 테스트, 버전
- Simulation: 실제 입력 기반 실행과 결과 검증

이 구조를 따르면 향후 MCP relay, HTTP webhook, RAG, ontology query, approval check, audit writeback 같은 실행 단위를 같은 캔버스에서 조합할 수 있다.

## 10. 보안/네트워크 고려

외부 webhook 또는 MCP relay 호출은 skill의 executor 설정으로 관리한다. 보수적인 기업 환경에서는 고정 발신지 IP, allowlist, audit log, credential isolation이 중요하므로, 프론트 화면에서도 다음 설정을 노출할 수 있어야 한다.

- executor type: local, backend, relay, webhook
- network policy label
- credential reference
- allowed target systems
- audit required 여부
- manual approval required 여부

Azure managed webhook 스타일을 그대로 쓰는 경우 고정 발신지 IP를 위해 별도 네트워크 구성이 필요할 수 있다. 자체 구현 relay는 이 지점을 더 단순하게 만들 수 있으므로, v5에서는 skill executor 설정에 network/security metadata를 포함하는 쪽이 좋다.

## 11. 엔터프라이즈 솔루션 UX 보완

UiPath Banking Automation 같은 산업별 솔루션 페이지는 Builder를 먼저 보여주기보다 업무 문제, 성과, 사전 구축 솔루션, 유스케이스, 고객 신뢰 요소를 먼저 보여준다. v5도 내부 운영 도구이지만, 대기업 PoC/제안/보고를 고려하면 다음 진입 구조가 유리하다.

```text
업무 시나리오
  -> 적용 가능 조건
  -> 워크플로우 템플릿
  -> 시뮬레이션
  -> Builder 편집
  -> 운영/감사
```

기능 중심 표현보다 아래 표현이 더 적합하다.

```text
산출물 변경이 없는 서비스 요청에 대해, 근거 문서가 충분한 경우에만 자동댓글을 생성하고,
승인/권한/변경 위험이 있는 요청은 사람 검토로 이관한다.
모든 판단 근거와 실행 이력은 감사 가능하게 남긴다.
```

따라서 v5 프론트엔드는 `Builder-first`가 아니라 `Use-case-first, Builder-second` 구조를 권장한다.
