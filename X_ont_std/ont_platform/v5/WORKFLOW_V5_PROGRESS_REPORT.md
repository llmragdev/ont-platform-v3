# Workflow v5 진행 보고서

작성일: 2026-06-11

## 1. 작업 목적

v5 프론트엔드에서 사용자가 처음부터 빈 캔버스에 노드를 그리는 방식만 제공하지 않고, 실제 업무 시나리오 기반으로 워크플로우에 진입할 수 있도록 구성했다.

핵심 방향은 다음과 같다.

- "서비스 요청 자동댓글", "권한 요청 안내", "승인 후 계정 조치" 같은 업무 템플릿을 먼저 제공한다.
- 사용자는 템플릿을 복제한 뒤 Workflow Builder에서 노드와 연결을 직접 수정할 수 있다.
- 비밀번호 변경/초기화 같은 서비스 요청 워크플로우를 v5에서 시연 가능한 형태로 만든다.
- 아직 실제 계정 조치나 외부 시스템 writeback은 하지 않고, 프론트엔드 기반 설계와 mock 시뮬레이션까지 구현한다.

## 2. 실행 기준

중요: v5 프론트는 반드시 conda 가상환경을 먼저 활성화한 뒤 실행한다. PowerShell에서 `npm run dev` 또는 `npm run build`를 바로 실행하지 말고, 아래 순서를 기준으로 한다.

v3 프론트 실행 방식과 맞춰 v5는 아래 기준으로 실행한다.

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run dev -- -p 3002
```

기본 `package.json`의 `dev` 스크립트는 `3001`을 사용하지만, 현재 `3001` 포트가 이미 사용 중이어서 검증은 `3002`로 진행했다.

빌드 검증도 같은 conda 환경 안에서 수행한다.

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run build
```

접속 주소:

```text
http://localhost:3002
```

## 3. 주요 변경 파일

이번 작업의 핵심 변경 파일은 다음과 같다.

```text
ont_platform/v5/frontend/src/app/page.tsx
ont_platform/v5/frontend/src/components/Sidebar.tsx
ont_platform/v5/frontend/src/components/WorkflowHome.tsx
ont_platform/v5/frontend/src/components/TemplateGallery.tsx
ont_platform/v5/frontend/src/components/WorkflowGraph.tsx
ont_platform/v5/frontend/src/lib/workflowTemplates.ts
ont_platform/v5/frontend/src/types/api.ts
```

참고: `ont_platform/v5/frontend/src`는 v4 프론트의 구조를 v5로 가져온 뒤, 워크플로우 v5 목적에 맞게 일부 파일을 교체/추가했다. 현재 git 상태에서는 `ont_platform/v5/frontend/package.json`과 `ont_platform/v5/frontend/src/`가 미추적 파일로 보인다.

## 4. 구현 내용

### 4.1 v5 사이드바 개편

파일:

```text
ont_platform/v5/frontend/src/components/Sidebar.tsx
```

변경 내용:

- v5 메뉴를 "워크플로우 v5" 중심으로 재구성했다.
- 새 메뉴를 추가했다.
  - 워크플로우 홈
  - 템플릿 갤러리
  - 워크플로우 빌더
  - 승인 워크플로우
  - Writeback DLQ
- 기존 분석, 온톨로지 관리, 운영 메뉴도 유지했다.

의도:

- 사용자가 v5에 들어왔을 때 바로 "워크플로우를 어떻게 시작해야 하는지" 볼 수 있도록 한다.
- 업무 시나리오 기반 진입을 기본 UX로 둔다.

### 4.2 워크플로우 홈 추가

파일:

```text
ont_platform/v5/frontend/src/components/WorkflowHome.tsx
```

구현 내용:

- v5 워크플로우 첫 화면을 추가했다.
- 템플릿 갤러리로 이동하는 진입점을 제공한다.
- 최근 워크플로우/운영 상태/검증 필요 영역을 보여준다.
- "템플릿 복제는 가능하지만 실제 계정 조치는 아직 백엔드 Skill/Adapter 연결이 필요하다"는 경계를 명확히 했다.

검증 포인트:

- v5 기본 진입 화면이 빈 캔버스가 아니라 업무 시나리오 중심인지 확인한다.
- 화면 문구가 하드코딩된 업무 예시이긴 하지만, 기능의 본질은 `workflowTemplates.ts`의 템플릿 데이터 기반인지 확인한다.

### 4.3 템플릿 갤러리 추가

파일:

```text
ont_platform/v5/frontend/src/components/TemplateGallery.tsx
```

구현 내용:

- 업무 템플릿 목록을 보여주는 갤러리를 추가했다.
- 템플릿 상세에서 아래 정보를 확인할 수 있다.
  - 목적
  - 필요한 Skill
  - 데이터 소스
  - 거버넌스/승인 조건
- "복제해서 수정" 버튼을 제공한다.
- 복제 시 `api.workflowGraphs.save(...)`를 호출해 그래프를 저장하고, 저장된 그래프 ID를 `localStorage.workflow:lastClonedGraphId`에 기록한다.
- 이후 Workflow Builder로 이동한다.

검증 포인트:

- "하드코딩된 단순 버튼"이 아니라 템플릿 데이터에서 그래프를 생성하는 구조인지 확인한다.
- 저장 API가 현재 백엔드의 `/api/workflow-graphs` 계약과 맞는지 확인한다.

### 4.4 템플릿 정의 추가

파일:

```text
ont_platform/v5/frontend/src/lib/workflowTemplates.ts
```

구현 내용:

- `WorkflowTemplate` 타입을 정의했다.
- `workflowTemplates` 배열에 업무 템플릿을 정의했다.
- `buildGraphFromTemplate(template)` 함수로 템플릿을 Workflow Graph 저장 형식으로 변환한다.

현재 포함된 템플릿:

- 서비스 요청 자동댓글
- 승인 후 계정 조치
- 권한 요청 안내
- VPN 장애 응대

의도:

- 업무 예시는 UI에 박힌 설명이 아니라 데이터화된 템플릿으로 관리한다.
- 이후 DB/API 기반 템플릿 관리로 전환하기 쉽게 한다.

검증 포인트:

- `buildGraphFromTemplate` 결과가 백엔드 `WorkflowGraph` 스키마와 호환되는지 확인한다.
- node kind, edge id, position, config 구조가 저장/실행 API에서 문제 없는지 확인한다.

### 4.5 Workflow Builder 교체/확장

파일:

```text
ont_platform/v5/frontend/src/components/WorkflowGraph.tsx
```

구현 내용:

- React Flow 기반 워크플로우 빌더를 v5 목적에 맞게 정리했다.
- 노드 팔레트에 서비스 요청/분류/정책 검색/승인/응답/완료 계열 노드를 추가했다.
- 새 그래프 생성, 저장, 불러오기, 삭제, 실행 버튼을 제공한다.
- 템플릿 갤러리에서 복제한 그래프 ID를 `localStorage.workflow:lastClonedGraphId`에서 읽어 자동 로드한다.
- 사용자가 직접 노드를 추가하고 연결할 수 있다.
- "서비스 요청 시뮬레이션" 패널을 추가했다.
  - 예: "결재 후 비밀번호 초기화 해 주세요."
  - 입력 텍스트를 기준으로 비밀번호/VPN/SAP 권한 등 간단한 mock 분류를 수행한다.
  - 분류 결과, 라우팅, 근거, 응답 초안을 표시한다.

중요한 경계:

- 현재 시뮬레이션은 프론트 mock이다.
- 실제 LLM Gateway, 계정계, ITSM, IAM, Approval API 호출은 아직 연결하지 않았다.
- 실제 실행은 백엔드 `WorkflowGraphRunner`와 Skill executor registry가 필요하다.

검증 포인트:

- 템플릿 복제 후 Builder 자동 로드가 정상 동작하는지 확인한다.
- React Flow 노드 추가/연결/저장/실행이 기존 API 계약과 충돌하지 않는지 확인한다.
- mock 시뮬레이션이 실제 실행으로 오해되지 않도록 UI 경계가 충분한지 확인한다.

### 4.6 API 타입 확장

파일:

```text
ont_platform/v5/frontend/src/types/api.ts
```

변경 내용:

- `GraphNodeKind`에 v5 업무 워크플로우용 node kind를 추가했다.

추가된 주요 kind:

```text
request_input
request_register
intent_classify
precondition_check
artifact_change_check
knowledge_lookup
policy_search
evidence_gate
approval_check
action_plan
draft_response
human_handoff
validate_response
complete_request
notify_user
end_pending
end_failed
```

검증 포인트:

- 백엔드 타입/스키마가 위 kind를 허용하는지 확인한다.
- 백엔드에서 허용하지 않는다면 저장 또는 실행 시 validation 실패 가능성이 있다.

## 5. 검증 결과

### 5.1 빌드 검증

실행 명령:

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run build
```

결과:

- Next.js build 성공
- static page generation 성공
- exit code 0

주의:

- 빌드 중 `eslint-plugin-jsx-a11y` 관련 경고가 출력되었다.
- 경고 내용은 플러그인 내부 모듈 로딩 문제로 보이며, 이번 변경 코드의 TypeScript compile 실패는 아니었다.
- 빌드는 성공했지만, 클로드 코드가 의존성/ESLint 설정은 별도 확인하는 것이 좋다.

### 5.2 서버 응답 검증

먼저 conda 환경을 활성화하고 dev server를 실행한다.

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run dev -- -p 3002
```

실행 명령:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:3002
```

결과:

```text
StatusCode: 200
```

### 5.3 브라우저 자동화 검증

Browser Use skill을 확인했으나, 현재 세션에서 실제 브라우저 조작용 callable tool이 노출되지 않았다. 따라서 화면 클릭 검증은 자동화하지 못했고, 빌드 성공 및 HTTP 200 응답으로만 검증했다.

클로드 코드 검증 시에는 실제 브라우저에서 다음 흐름을 확인하면 된다.

1. `http://localhost:3002` 접속
2. 좌측 메뉴에서 "템플릿 갤러리" 이동
3. "서비스 요청 자동댓글" 또는 "승인 후 계정 조치" 선택
4. "복제해서 수정" 클릭
5. Workflow Builder로 이동하는지 확인
6. 복제된 그래프가 자동 로드되는지 확인
7. 노드 추가/연결/저장 가능 여부 확인
8. 서비스 요청 시뮬레이션 입력 후 결과 표시 확인

## 6. 현재 한계

현재 구현은 v5 워크플로우 UX와 템플릿 기반 진입을 만드는 단계다.

아직 완료되지 않은 부분:

- 템플릿 데이터가 DB/API에서 관리되지 않고 프론트 파일에 있다.
- 서비스 요청 시뮬레이션은 mock 로직이다.
- LLM Gateway 연결은 아직 없다.
- 실제 승인 시스템, 계정계, IAM, ITSM writeback은 아직 없다.
- 백엔드 runner가 새 node kind를 실제로 실행하는지는 확인이 필요하다.
- 현재 v5 프론트 전체가 git 기준 미추적 상태이므로, 추적/커밋 정책 확인이 필요하다.

## 7. 클로드 코드에게 요청할 검증 항목

클로드 코드는 아래를 우선 검증하면 된다.

### 7.1 실행/빌드 검증

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run build
npm run dev -- -p 3002
```

확인:

- conda 가상환경 `claud_fe`가 정상 활성화되는가
- build가 성공하는가
- dev server가 뜨는가
- `http://localhost:3002` 접속이 되는가
- 3001/3002 포트 충돌이 없는가

### 7.2 템플릿 복제 검증

확인:

- 템플릿 갤러리에서 템플릿 선택이 되는가
- 복제 버튼 클릭 시 `api.workflowGraphs.save` 호출이 성공하는가
- 저장된 graph ID가 Builder에서 자동 로드되는가
- localStorage 값이 정상 정리되는가

### 7.3 백엔드 API 계약 검증

확인:

- `/api/workflow-graphs` 저장 API가 v5 node kind를 허용하는가
- graph node의 `config`, `position`, `data`, `edges` 구조가 백엔드 schema와 맞는가
- 실행 API가 새 node kind를 만나도 실패하지 않는가

### 7.4 UI/UX 검증

확인:

- v5 첫 화면이 업무 시나리오 중심으로 보이는가
- "직접 그리기" 기능이 남아 있는가
- "템플릿 복제 후 수정" 흐름이 자연스러운가
- mock 시뮬레이션이 실제 계정 조치처럼 오해되지 않는가

### 7.5 인코딩 검증

PowerShell 출력에서 일부 한글이 깨져 보일 수 있다. 파일 자체가 UTF-8로 저장되어 있고 Next.js 화면에서 한글이 정상 표시되는지 확인해야 한다.

## 8. 앞으로의 개발 계획

### 8.1 1단계: 백엔드 Runner 계약 정리

목표:

- 프론트 node kind와 백엔드 runner의 실행 단위를 맞춘다.

작업:

- `GraphNodeKind`와 백엔드 enum/schema 비교
- 신규 node kind validation 추가
- 실행 불가능한 node kind는 `pending`, `manual`, `mock` 상태로 명확히 처리
- run history에 node별 상태와 evidence를 남김

클로드 코드 확인:

- 현재 백엔드에 `WorkflowGraphRunner` 또는 유사 실행기가 있는지 확인
- 없다면 최소 runner interface 설계 제안

### 8.2 2단계: LLM Gateway 연결

목표:

- `intent_classify`, `draft_response`, `policy_search` 일부를 LLM Gateway와 연결한다.

작업:

- LLM Gateway 실행 방법 문서화
- port `8001` 의존성 확인
- `/api/hybrid/ask`, `/api/ontology` proxy 구조 확인
- 프론트 mock 분류를 백엔드 호출로 교체

클로드 코드 확인:

- `ECONNREFUSED 127.0.0.1:8001`의 원인이 gateway 미기동인지, proxy 설정 문제인지 확인
- gateway 시작 스크립트 또는 README 위치 확인

### 8.3 3단계: 템플릿 저장소 API화

목표:

- 프론트 하드코딩 템플릿을 API/DB 기반으로 전환한다.

작업:

- template list API
- template detail API
- clone template API
- template versioning
- 조직별 템플릿 공개/비공개

클로드 코드 확인:

- 기존 DB schema 중 workflow template에 재사용 가능한 테이블이 있는지 확인
- 없다면 migration 설계 필요

### 8.4 4단계: 승인/조치 어댑터 연결

목표:

- 승인 후 계정 조치 같은 업무를 실제 시스템과 연결 가능한 구조로 만든다.

작업:

- approval node
- action plan node
- external adapter registry
- writeback DLQ 연계
- dry-run / approval-required / execute 모드 분리

클로드 코드 확인:

- 기존 WriteBack/DLQ 구현과 연결 가능한지 확인
- 실제 실행 전 human approval gate가 강제되는지 확인

### 8.5 5단계: 감사/거버넌스 강화

목표:

- 팔란티어식 object/action/audit 모델과 온톨로지 기반 evidence 모델을 연결한다.

작업:

- 요청 객체, 정책 객체, 승인 객체, 실행 객체를 온톨로지 instance로 남김
- 각 실행 결과에 provenance/evidence 연결
- 사용자가 어떤 근거로 어떤 조치를 했는지 audit trail 제공

클로드 코드 확인:

- 기존 Audit, Provenance, Ontology schema 기능과 재사용 가능한 부분 확인

## 9. 설계 판단

이번 작업의 설계 판단은 다음과 같다.

- 템플릿 예시는 현재 프론트 파일에 있지만, 구조는 템플릿 데이터 기반이다.
- 직접 그리기는 제거하지 않았다. 템플릿 기반 진입과 직접 편집을 같이 제공한다.
- 비밀번호 변경/초기화 워크플로우는 현재 "가능한 UX와 graph 구조"를 만든 단계다.
- 실제 계정 변경은 반드시 승인 gate, adapter, audit, DLQ가 붙은 뒤에만 실행해야 한다.
- v5의 우선순위는 "노드 편집기"보다 "업무 시나리오 기반 실행 경험"이다.

## 10. 결론

v5는 현재 다음 상태다.

- 프론트 실행 가능
- 템플릿 기반 워크플로우 진입 가능
- 템플릿 복제 후 Builder 수정 가능
- 서비스 요청 mock 시뮬레이션 가능
- 빌드 성공
- 실제 LLM Gateway/계정계/승인계 연동은 다음 단계

클로드 코드는 우선 빌드, 브라우저 흐름, 백엔드 API 계약, 신규 node kind 호환성을 검증하면 된다.
