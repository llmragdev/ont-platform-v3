# Enterprise Workflow UI Competitor Analysis

Last updated: 2026-06-09

## 1. 목적

이 문서는 v5 Workflow Builder와 Skill Manager 설계를 위해 참고할 만한 엔터프라이즈급 워크플로우/에이전트 저작 UI를 정리한다.

분석 관점:

- 사용자가 직접 워크플로우를 그릴 수 있는가
- 노드/블록 기반 확장성이 있는가
- AI/RAG/Agent 실행 단위를 표현할 수 있는가
- 스킬, 액션, 커넥터, 도구 관리가 분리되어 있는가
- 실행 결과, 감사, 버전, 승인, 운영 관리가 가능한가
- 우리 v5에 어떤 UX를 반영할 수 있는가

## 2. 요약 판단

우리가 목표로 할 방향은 단일 제품을 그대로 따라가는 것이 아니라 여러 제품의 강점을 조합하는 것이다.

권장 벤치마크 조합:

- ServiceNow: 업무 요청, 승인, 이관, 감사 중심의 엔터프라이즈 안정성
- Camunda: BPMN 기반 프로세스 표현력과 분기/사람 태스크 명확성
- Flowise/Dify: LLM, RAG, Agent, Tool 노드 기반 AI workflow UX
- n8n: HTTP, Webhook, 외부 시스템 연동과 node catalog UX
- UiPath: 실행, 테스트, 평가, 배포, Human-in-the-loop 운영성
- IBM watsonx Orchestrate/Salesforce Agentforce: agent/skill catalog와 governed agent 관리

v5는 다음 방향이 적합하다.

```text
ServiceNow식 업무 안정성
  + Camunda식 프로세스 명확성
  + Flowise/Dify식 AI 블록
  + n8n식 외부 연동
  + UiPath식 실행/평가/운영
  + ontology/RAG 근거 추적
```

## 3. 주요 경쟁/참조 제품

### 3.1 ServiceNow Workflow Studio / Flow Designer

URL:

- https://www.servicenow.com/docs/r/build-workflows/workflow-studio/workflow-studio.html
- https://www.servicenow.com/in/products/platform-flow-designer.html

참조 가치:

- ITSM, Helpdesk, Service Catalog 업무 흐름에 가장 가까운 제품군이다.
- Trigger, Action, Condition, Approval, Subflow 등 업무 자동화 구성요소가 명확하다.
- 업무 요청의 접수, 담당자 이관, 승인, 완료, 감사 흐름을 엔터프라이즈 관점에서 다룬다.

우리 v5 반영 포인트:

- 서비스 요청 자동댓글/수동 이관/승인 대기 흐름의 기준 모델로 삼는다.
- 워크플로우 실행 결과를 업무 상태와 연결한다.
- 실행 이력, 실패 원인, 승인 상태, 담당자 이관 상태를 화면에 표시한다.
- 업무 프로세스용 block category를 명확히 둔다.

주의점:

- 화면이 업무 플랫폼에 강하게 결합되어 있어, 범용 AI/RAG workflow UX로는 다소 무거울 수 있다.
- 우리 제품은 특정 Helpdesk 종속이 아니므로, ServiceNow식 업무 안정성만 참조하고 데이터 모델은 범용화해야 한다.

### 3.2 Camunda Modeler

URL:

- https://camunda.com/products/camunda-platform/modeler/
- https://camunda.com/bpmn

참조 가치:

- BPMN 기반 엔터프라이즈 프로세스 저작 UI의 대표적인 참고 대상이다.
- Business task, service task, gateway, event, subprocess, human task 표현이 명확하다.
- 복잡한 분기, 장기 실행 프로세스, 사람 개입, 시스템 작업을 한 다이어그램에서 표현한다.

우리 v5 반영 포인트:

- 조건 분기와 사람 개입 표현 방식을 참고한다.
- `manual`, `approval`, `error`, `timeout` 같은 edge label을 명확히 표현한다.
- 단순 AI 노드 나열이 아니라 업무 프로세스의 시작/분기/대기/종료 상태를 안정적으로 보여준다.
- 향후 BPMN export/import 가능성도 검토할 수 있다.

주의점:

- BPMN은 정확하지만 비전문 사용자에게 다소 복잡할 수 있다.
- v5 초기 화면은 BPMN 전체 표준보다 실무형 블록 UI로 시작하는 것이 좋다.

### 3.3 UiPath Agent Builder / Studio Web

URL:

- https://www.uipath.com/product/agent-builder
- https://docs.uipath.com/agents/automation-suite/latest/user-guide/building-an-agent-in-studio-web

참조 가치:

- Agent, Robot, Human이 함께 작업하는 실행/운영 구조가 강하다.
- agent를 만들고 테스트하고 평가하고 배포하는 흐름이 잘 잡혀 있다.
- enterprise-grade agent를 위해 score, optimizer, test case, deployment option을 강조한다.

우리 v5 반영 포인트:

- Skill Manager에 테스트 실행과 평가 기능을 둔다.
- 워크플로우 실행 패널에 단계별 결과, 소요시간, 실패, 재실행을 표시한다.
- 자동댓글 품질 평가, 근거 기반성 평가, 금칙어 검사 결과를 운영 화면에 연결한다.
- Human-in-the-loop를 별도 상태로 표현한다.

주의점:

- RPA 중심 제품이므로 UI 자동화와 봇 실행에 강하다.
- 우리 v5는 RPA보다 RAG/ontology/evidence 기반 의사결정에 무게를 둔다.

### 3.4 n8n

URL:

- https://docs.n8n.io/workflows/create/
- https://docs.n8n.io/advanced-ai/ai-workflow-builder/
- https://docs.n8n.io/keyboard-shortcuts/

참조 가치:

- 노드 기반 자동화 UX가 직관적이다.
- HTTP, Webhook, API, 외부 시스템 연동을 쉽게 구성한다.
- node catalog, credential, expression, execution history UX가 실무적이다.
- AI Workflow Builder는 자연어로 workflow를 생성/수정하는 UX를 제공한다.

우리 v5 반영 포인트:

- 좌측 block palette와 검색 UX를 참고한다.
- HTTP/Webhook/MCP Relay 노드를 쉽게 추가할 수 있게 한다.
- credential은 노드에 직접 입력하지 않고 reference로 선택하도록 한다.
- 자연어로 workflow 초안을 생성하는 기능은 중장기 과제로 둘 수 있다.

주의점:

- 엔터프라이즈 ITSM/승인/감사 모델은 ServiceNow/UiPath보다 약하다.
- 자유도가 높아질수록 보안 통제가 약해질 수 있으므로, v5에서는 skill policy와 network policy를 함께 관리해야 한다.

### 3.5 Flowise AgentFlow V2

URL:

- https://docs.flowiseai.com/using-flowise/agentflowv2
- https://docs.flowiseai.com/using-flowise/analytics

참조 가치:

- LLM, Agent, Tool, HTTP, Retriever, Custom Function 같은 AI workflow 노드 구성이 강하다.
- AgentFlow V2는 세분화된 standalone node로 workflow를 구성하는 방향이다.
- Human-in-the-loop와 checkpoint 개념을 제공한다.
- Agent 간 task delegation과 shared context를 표현한다.

우리 v5 반영 포인트:

- RAG, LLM, tool, HTTP, decision node 구성을 직접 참고한다.
- 각 노드가 flow state를 읽고 업데이트하는 개념을 도입한다.
- 실행 중 conversation context, evidence, output을 단계별로 보여준다.
- MCP relay나 skill executor를 Tool/HTTP 계열 노드로 표현할 수 있다.

주의점:

- 범용 업무 프로세스/승인/감사보다는 AI workflow 제작에 강하다.
- 우리 v5는 Flowise식 AI 노드에 엔터프라이즈 업무 상태를 결합해야 한다.

### 3.6 Dify Workflow

URL:

- https://docs.dify.ai/
- https://docs.dify.ai/guides/workflow
- https://docs.dify.ai/guides/workflow/node/agent

참조 가치:

- LLM application workflow를 빠르게 구성하기 좋다.
- input variable, LLM node, knowledge retrieval, condition, code, API trigger UX가 참고할 만하다.
- RAG 기반 답변 생성과 API 호출 흐름을 표현하기 쉽다.

우리 v5 반영 포인트:

- RAG 자동댓글 MVP의 기본 UX 참고 대상으로 삼는다.
- input/output variable mapping을 명확히 한다.
- knowledge retrieval 결과와 생성 결과를 함께 보여준다.
- workflow를 API로 실행하는 구조를 참고한다.

주의점:

- 대기업 운영 관점의 승인, 감사, 네트워크 보안, 고정 IP 정책은 별도 보강이 필요하다.

### 3.7 Microsoft Copilot Studio

URL:

- https://learn.microsoft.com/en-us/microsoft-copilot-studio/flow-designer
- https://developer.microsoft.com/en-us/agents

참조 가치:

- agent flow designer, action, knowledge source, topic, Microsoft 365 연동 UX가 강하다.
- 업무 사용자가 agent를 만들고 테스트하는 경험을 제공한다.
- 자연어 기반 agent 생성 흐름을 참고할 수 있다.

우리 v5 반영 포인트:

- Skill Manager에서 knowledge source와 action을 분리한다.
- agent 또는 workflow 테스트 패널을 오른쪽/하단에 제공한다.
- 비전문 사용자용 문장 기반 설정 보조 기능을 중장기 과제로 둔다.

주의점:

- Microsoft 생태계 의존성이 강하다.
- 우리 v5는 독립형 플랫폼이므로 연결 방식만 참고한다.

### 3.8 Salesforce Agentforce Builder

URL:

- https://www.salesforce.com/agentforce/agent-builder/
- https://trailhead.salesforce.com/content/learn/modules/introduction-to-agent-builder/get-to-know-agent-builder

참조 가치:

- CRM 업무 중심 agent/topic/action/test UX가 강하다.
- action, topic, instruction, testing을 업무 데이터와 결합한다.
- agent builder와 flow/action 체계를 함께 사용한다.

우리 v5 반영 포인트:

- skill을 topic/action 관점으로 묶는 화면을 검토한다.
- 자동댓글 시나리오에서 업무 유형별 topic 또는 template을 둘 수 있다.
- 테스트-수정-재테스트 루프를 UX에 반영한다.

주의점:

- CRM 중심 제품이므로 ITSM/RAG/ontology 플랫폼과는 도메인이 다르다.

### 3.9 IBM watsonx Orchestrate

URL:

- https://www.ibm.com/products/watsonx-orchestrate

참조 가치:

- agent catalog, tool catalog, multi-agent orchestration, governance UX 참고에 좋다.
- 엔터프라이즈 ready agent와 tool을 검색/재사용하는 방향이 강하다.
- 다양한 agent를 하나의 control plane에서 관리하는 메시지가 명확하다.

우리 v5 반영 포인트:

- Skill Manager를 단순 설정 화면이 아니라 governed skill catalog로 확장한다.
- 스킬 검색, 태그, 도메인, 사용처, 활성/비활성, 버전 관리가 필요하다.
- agent/skill의 보안 정책과 감사 요구 여부를 metadata로 관리한다.

주의점:

- 실제 상세 Builder UX는 공개 자료만으로는 제한적으로 파악된다.

### 3.10 Appian Process Modeler

URL:

- https://docs.appian.com/suite/help/26.2/process-model-object.html

참조 가치:

- 전통적인 low-code process modeler의 운영/권한/버전/문서화 관점이 강하다.
- process model documentation, version, security, monitoring 관점이 참고된다.
- 업무 프로세스와 애플리케이션 객체를 함께 관리한다.

우리 v5 반영 포인트:

- 워크플로우 문서화 기능을 중장기 과제로 둔다.
- 프로세스 security, version, publish/draft 상태를 관리한다.
- 실행 중인 process monitoring과 설계 편집을 분리한다.

주의점:

- AI/RAG/Agent workflow UX는 Flowise/Dify 계열이 더 직접적이다.

## 4. 직접 체험 우선순위

우선 직접 만져볼 대상:

1. Camunda Modeler
2. n8n
3. Flowise AgentFlow V2
4. Dify Workflow

공식 캡처/문서 중심으로 참고할 대상:

1. ServiceNow Workflow Studio / Flow Designer
2. UiPath Agent Builder / Studio Web
3. Microsoft Copilot Studio
4. Salesforce Agentforce Builder
5. IBM watsonx Orchestrate
6. Appian Process Modeler

## 5. v5 설계 반영 항목

### 5.1 Workflow Builder

필수 반영:

- block palette
- canvas zoom/minimap
- node category/filter/search
- node property panel
- edge label/condition editor
- run button
- node execution status
- execution result panel

고도화:

- subflow
- reusable workflow template
- workflow version
- draft/publish
- import/export
- workflow documentation generation

### 5.2 Skill Manager

필수 반영:

- skill list
- skill detail
- skill type/category
- input/output schema
- default config
- prompt/RAG/API settings
- skill test run
- enabled/disabled

고도화:

- version management
- usage list
- approval required flag
- network policy metadata
- credential reference
- audit required flag
- risk level

### 5.3 Workflow Simulation

필수 반영:

- sample input
- run status
- node-by-node result
- input/output JSON viewer
- evidence viewer
- decision route
- generated comment
- validation result
- handoff reason

고도화:

- test case set
- regression evaluation
- answer quality score
- no-answer policy score
- replay run
- compare runs

## 6. v5 차별화 포인트

경쟁 제품과 비교했을 때 v5의 차별화는 다음으로 잡는 것이 좋다.

- ontology 기반 업무/데이터 의미 구조
- RAG 근거 추적과 evidence gate
- no-answer/insufficient-evidence 정책
- 보수적 기업 보안에 맞는 relay/webhook/network policy 설정
- skill과 workflow의 분리
- 자동댓글처럼 낮은 위험 업무부터 시작하는 실무형 agentic process
- 실행 로그와 감사 추적을 전제로 한 엔터프라이즈 설계

## 7. 결론

아까 참고한 워크플로우 이미지는 PoC/데모 상위 수준이다. 다만 엔터프라이즈 운영 제품으로 보려면 다음이 필요하다.

- Skill Manager 별도 화면
- skill version, schema, prompt, RAG, API 설정 관리
- 실행 결과와 evidence 추적
- audit, approval, manual handoff, retry
- credential/network policy 분리
- draft/publish/version 관리

따라서 v5는 단순히 노드 그래프를 예쁘게 만드는 것이 아니라, 워크플로우 저작 UI와 스킬 관리 UI를 함께 설계해야 한다. 초기 구현은 `Workflow Builder + Skill Manager + RAG 자동댓글 Simulation`의 세 축으로 진행한다.

## 8. 산업별 솔루션 페이지 디자인 패턴 비교

UiPath의 Banking & Financial Services 페이지는 단순 제품 기능 소개가 아니라, 산업별 업무 문제를 agentic automation 패키지로 설득하는 구조다.

참조 URL:

- https://www.uipath.com/solutions/industry/banking-automation

### 8.1 UiPath 페이지 구조

UiPath 페이지의 핵심 구성:

1. 산업별 메시지
   - banking and financial services라는 명확한 산업 도메인을 첫 화면에서 제시한다.
   - agentic business orchestration이라는 상위 메시지로 AI, automation, people을 묶는다.

2. 성과 지표
   - productivity gain, faster time to value, AI agent value share 같은 수치형 지표를 전면에 둔다.
   - 도입 효과를 추상적 기능이 아니라 경영 언어로 설명한다.

3. 사전 구축 솔루션
   - financial crime compliance, loan origination 같은 산업별 pre-built solution을 제시한다.
   - 개별 기능보다 end-to-end workflow package처럼 보이게 한다.

4. 업무별 데모/유스케이스
   - client onboarding, mortgage origination, QA/QC, sanctions alert review 등 실제 업무 흐름을 나열한다.
   - 각 유스케이스는 `문제 -> agentic 처리 -> human review -> 결과` 구조로 설명된다.

5. 신뢰 요소
   - governance, auditability, security, guardrails를 반복해서 강조한다.
   - 고객사 로고, case study, 수치 성과를 함께 배치한다.

### 8.2 디자인 패턴

UiPath식 산업 페이지 패턴:

```text
Industry Hero
  -> Business Outcomes
  -> Pre-built Solutions
  -> Use Case Tabs
  -> Demo/Video Cards
  -> Customer Proof
  -> Governance/Trust Message
  -> Resources/CTA
```

우리 플랫폼에 맞춘 패턴:

```text
업무 적용 시나리오 Hero
  -> 적용 대상 업무 범위
  -> 자동화 가능/불가 기준
  -> 대표 워크플로우 Preview
  -> RAG/근거/검증 흐름
  -> 시뮬레이션 입력
  -> 실행 결과/자동댓글 예시
  -> 보안/감사/수동 이관 기준
  -> 개발자/관리자용 Builder 진입
```

### 8.3 우리 제품과의 차이

| 항목 | UiPath Banking Automation | 우리 v5 방향 |
|---|---|---|
| 주 메시지 | 산업별 agentic business orchestration | 온톨로지/RAG 기반 업무 의사결정 및 자동댓글 |
| 핵심 업무 | 금융 범죄, 대출, 모기지, QA/QC | 서비스 요청, 지식 검색, 근거 기반 댓글, 수동 이관 |
| 실행 주체 | AI agents + robots + humans | workflow nodes + skills + RAG + relay/handoff |
| 강점 | RPA, 운영 자동화, 대형 고객 사례, 산업 패키지 | ontology, evidence gate, no-answer, 보수적 보안 환경 |
| 화면 패턴 | 마케팅/솔루션 페이지 중심 | 저작 UI + 시뮬레이션 + 운영 로그 중심 |
| 신뢰 요소 | governance, auditability, security, case study | 근거 문서, 정책 검증, 감사 로그, network policy |
| 확장 방식 | pre-built industry solution | skill catalog + workflow template |

### 8.4 v5에 반영할 화면 유형

현재 v5에서 Builder와 Skill Manager만 만들면 개발자 도구처럼 보일 수 있다. UiPath식 패턴을 참고하면, 다음 화면이 추가로 필요하다.

1. Use Case Gallery
   - 서비스 요청 자동댓글
   - 권한 요청 안내
   - 정책/FAQ 문의 응답
   - 승인 후 처리 안내
   - 근거 부족 수동 이관

2. Workflow Template Detail
   - 업무 설명
   - 적용 가능 조건
   - 자동화 제외 조건
   - 필요한 skill 목록
   - 필요한 knowledge source
   - 보안/감사 요구사항
   - 캔버스 preview
   - 시뮬레이션 시작 버튼

3. Scenario Simulation Page
   - 요청 문장 입력
   - 실행 단계
   - RAG 근거
   - 자동댓글 결과
   - 수동 이관 사유
   - 감사 로그 preview

4. Trust & Governance Panel
   - no-answer policy
   - evidence gate
   - source allowlist
   - fixed egress IP/relay policy
   - credential reference
   - human approval rule

### 8.5 우리에게 필요한 메시지 전환

기능 중심 표현:

```text
워크플로우 노드를 추가하고 RAG 검색 후 댓글을 생성한다.
```

엔터프라이즈 솔루션 표현:

```text
산출물 변경이 없는 서비스 요청에 대해, 근거 문서가 충분한 경우에만 자동댓글을 생성하고,
승인/권한/변경 위험이 있는 요청은 사람 검토로 이관한다.
모든 판단 근거와 실행 이력은 감사 가능하게 남긴다.
```

이 표현이 대기업 제안/보고용으로 더 적합하다.

### 8.6 v5 프론트엔드 설계 보완 사항

`Workflow Builder` 앞단에 다음 정보 구조를 추가하는 것이 좋다.

```text
Workflow Home
  - KPI summary
  - active workflow templates
  - recent simulation results
  - risk/handoff count

Use Case Gallery
  - 업무별 카드
  - 적용 가능 조건
  - 자동화 기대 효과

Template Detail
  - 업무 프로세스 설명
  - canvas preview
  - required skills
  - required knowledge sources
  - governance policy

Builder
  - 실제 워크플로우 저작

Simulation
  - 실행 테스트

Operations
  - 실행 이력
  - 실패/이관/재시도
  - 감사 로그
```

### 8.7 결론

UiPath의 산업별 페이지는 우리에게 두 가지 힌트를 준다.

첫째, 엔터프라이즈 고객은 "무엇을 만들 수 있는가"보다 "어떤 업무를 안전하게 개선하는가"를 먼저 본다. 따라서 v5는 Builder 화면만이 아니라 업무 시나리오 중심의 진입 화면이 필요하다.

둘째, agentic workflow는 자율 실행보다 governance, auditability, security, human control을 함께 보여줄 때 설득력이 생긴다. 우리 v5는 ontology/RAG/evidence/no-answer를 이 신뢰 요소로 전면에 배치해야 한다.
