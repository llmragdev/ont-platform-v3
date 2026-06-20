# Master Roadmap

Last updated: 2026-06-09

## 1. 관리 원칙

이 문서는 현재 프로젝트의 최상위 로드맵이다. 상세 설계, 검증 결과, 과거 보고서는 각 하위 폴더에 두고 이 문서에서는 현재 우선순위와 참조 위치만 관리한다.

- 현재 의사결정: `status_reports/MASTER_ROADMAP.md`
- 상세 설계: `design`
- 워크플로우 설계: `design/workflow`
- v5 검증 결과: `validation/ont_platform_v5_eval`
- 단계별 실행 지시: `week_instructions`
- 완료/참조 문서: 각 폴더의 `archive`

## 2. 현재 판단

v5 백엔드는 `/api/v5/hybrid/ask`, `QuestionAnalyzer`, `EvidenceGate`, no-answer 정책 등으로 이미 검증된 내용이 있다. 반면 v5 프론트엔드는 `frontend` 폴더는 있으나 실제 `src`가 없으므로, 사용자가 직접 저작 가능한 화면을 만들려면 v5 프론트 복원이 가장 먼저 필요하다.

기존 v3/v4 워크플로우 화면은 React Flow 기반 그래프 편집과 실행 표시가 가능하지만, 목표 화면은 단순 노드 그래프가 아니라 정교한 Agentic Workflow Builder다. 따라서 v5에서는 워크플로우 노드와 스킬 관리를 분리하고, 각 노드를 실행 가능한 블록으로 확장한다.

## 3. 최우선 개발 목표

1. v4 프론트엔드 소스를 v5 프론트엔드 기준선으로 승격한다.
2. v5 프론트엔드 API 경로를 v5 백엔드와 분리해 연결한다.
3. Workflow Home과 Use Case Gallery를 추가해 업무 시나리오 중심 진입 구조를 만든다.
4. Workflow Builder를 블록형 구조로 확장한다.
5. Skill Manager 화면을 추가해 스킬 정의와 실행 설정을 관리한다.
6. 서비스 요청 RAG 자동댓글 워크플로우를 시뮬레이션 가능한 첫 번째 대표 사례로 구현한다.
7. v5 프론트/백엔드 통합 smoke test를 수행한다.

## 4. 단계별 로드맵

### Phase A. v5 프론트 복원

- `ont_platform/v4/frontend/src`를 기준으로 `ont_platform/v5/frontend/src`를 구성한다.
- v5 전용 API base URL 또는 rewrite 설정을 분리한다.
- v3/v4와 동일한 화면이 v5에서 먼저 정상 기동되는지 확인한다.
- 기존 기능 손상 없이 워크플로우 그래프 화면을 v5 메뉴에 노출한다.

완료 기준:

- v5 프론트가 로컬에서 기동된다.
- v5 백엔드 health 및 `/api/v5/hybrid/ask` 호출 경로가 분리된다.
- 기존 워크플로우 그래프가 v5 화면에서 조회/저장/실행된다.

### Phase B. Workflow Builder 확장

- Workflow Home을 추가해 활성 워크플로우, 최근 실행, 수동 이관, governance 상태를 요약한다.
- Use Case Gallery를 추가해 업무별 workflow template을 선택할 수 있게 한다.
- Template Detail 화면을 추가해 적용 가능 조건, 자동화 제외 조건, 필요한 skill, 필요한 knowledge source, governance policy를 보여준다.
- 노드 팔레트를 단순 타입에서 블록 카테고리 기반으로 확장한다.
- 노드 속성 편집 패널을 스킬 기반 설정으로 개편한다.
- 조건 분기 edge label을 `Y`, `N`, `auto`, `manual`, `approval`, `error` 등으로 관리한다.
- 실행 결과를 노드별 input/output/evidence/status 형태로 표시한다.
- 캔버스에서 서비스 요청 자동댓글 플로우를 직접 구성할 수 있게 한다.

대표 블록:

- Input: 요청 수신, 티켓 입력, 첨부 파싱
- Classifier: 업무유형 분류, 변경 여부 판단, 보안등급 판단
- RAG: FAQ 검색, 정책 검색, 유사사례 검색, 근거 선택
- Decision: 자동댓글 가능 여부, 승인 필요 여부, 사람 검토 여부
- Generation: 답변 초안, 댓글 초안, 요약, 처리 가이드
- Action: 댓글 등록, 담당자 배정, 알림 발송, 외부 API 호출
- Guardrail: 근거 검증, 보안정보 검사, 금칙어 검사
- Terminal: 완료, 보류, 실패, 수동 이관

완료 기준:

- 사용자가 블록을 추가/연결/설정/저장할 수 있다.
- 실행 시 각 노드의 결과와 다음 분기 경로가 화면에 표시된다.
- RAG 자동댓글 예제가 캔버스에서 재현된다.

### Phase C. Skill Manager 추가

- 워크플로우 화면과 별도로 스킬 관리 화면을 만든다.
- 스킬의 타입, 입출력 스키마, 프롬프트, RAG 설정, 외부 API 설정, 검증 정책을 관리한다.
- 워크플로우 노드는 스킬 정의를 참조하고, 노드별 override 설정만 가진다.
- 스킬 버전과 활성/비활성 상태를 관리한다.

필요 화면:

- 스킬 목록
- 스킬 상세/편집
- 입출력 스키마 설정
- 프롬프트/정책 설정
- 테스트 실행
- 사용 중인 워크플로우 목록

완료 기준:

- 새 스킬을 등록하고 Workflow Builder에서 선택할 수 있다.
- 스킬 단위 테스트를 실행해 input/output을 확인할 수 있다.
- 워크플로우 실행 로그에서 어떤 스킬 버전이 사용됐는지 확인할 수 있다.

### Phase D. 서비스 요청 RAG 자동댓글 MVP

- 문장형 서비스 요청을 입력으로 받는다.
- RAG 검색으로 근거 문서를 찾는다.
- 근거가 충분하면 자동댓글 초안을 생성한다.
- 변경/권한/승인/보안 위험이 있으면 자동 완료하지 않고 안내 또는 수동 이관한다.
- 자동댓글은 mock 서버 또는 내부 adapter를 통해 등록한다.

기본 플로우:

```text
Request Input
  -> Intent Classify
  -> Artifact Change Check
  -> RAG Search
  -> Evidence Gate
  -> Draft Comment
  -> Validate Comment
  -> Post Comment
  -> End
```

완료 기준:

- 예시 문장 입력 후 자동댓글 결과가 생성된다.
- 근거 문서와 사용 스킬이 함께 표시된다.
- 근거 부족/위험 요청은 수동 이관으로 분기된다.

### Phase E. Palantir-style Backend 반영

Palantir-style 백엔드 설계는 전략적으로 중요하지만, 현재는 프론트 저작 경험과 v5 통합 실행이 우선이다. v5 Workflow Builder와 Skill Manager가 잡힌 뒤 다음 항목을 순차 반영한다.

- ontology core/source mapping
- evidence and lineage layer
- policy-based serving
- execution audit
- workflow action governance

## 5. 현재 활성 참조

- v5 통합 설계: `week_instructions/PHASE8/PHASE8_V5_UNIFIED_DESIGN_PLAN.md`
- v5 평가 작업공간: `validation/ont_platform_v5_eval`
- 워크플로우 개발 준비: `design/workflow/서비스요청_RAG자동댓글_개발준비.md`
- 프론트엔드 상세 설계: `design/workflow/v5_workflow_builder_frontend_design.md`
- 워크플로우 UI/UX 경쟁사 분석: `design/workflow/enterprise_workflow_ui_competitor_analysis.md`
- Palantir-style 전략 설계: `design/팔란티어스타일`
- 설계 개요: `design/README.md`
- 기술 마스터 리포트: `design/PHASE8_MASTER_TECHNICAL_REPORT.md`

## 6. Archive Policy

- 완료된 status report는 `status_reports/archive`로 이동한다.
- 현재 메인 작업이 아닌 design 루트 문서는 `design/archive`로 이동한다.
- active working directory는 구현, 검증, 계획에 사용 중이면 루트에 유지한다.
