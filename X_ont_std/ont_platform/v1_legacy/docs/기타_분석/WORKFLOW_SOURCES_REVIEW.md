# 외부 Workflow 소스 6종 비교 리뷰

> 작성일: 2026-05-12
> 목적: 우리 `claud_통합/frontend`의 워크플로우 화면을 만들기 전, 참고할 수 있는 6개 외부 소스의 장단점을 한 화면에 비교한다.
> 검토 대상 (모두 Next.js 기반 Workflow-On-File 구현):

| 그룹 | 소스 | 경로 |
| --- | --- | --- |
| **A — 생성소스** | Antigravity1 | `F:\HNIX dev\…\01-생성소스\Antigravity1` |
| A | Prometheus1 | `F:\HNIX dev\…\01-생성소스\Prometheus1` |
| A | prometheus5 | `F:\HNIX dev\…\01-생성소스\prometheus5\workflow-app` |
| **B — proj_boot 부트스트랩** | workflowOn | `F:\proj_boot\workflowOn` |
| B | workflowTwo3Layer1 | `F:\proj_boot\workflowTwo3Layer1` |
| B | workflowTwo3Layer2 | `F:\proj_boot\workflowTwo3Layer2` |

## 0. 공통 미션 (그룹 A — SOURCE_SPEC_TEST.md)

3개 소스 모두 같은 미션:
1. 모든 데이터는 `./data/workflows/*.json`에 저장 (fs 모듈)
2. **React Flow** 캔버스 (드래그&드롭)
3. `POST /api/workflows` 저장 API
4. 필수 필드(id, type, position) 검증
5. Jest/Vitest 유닛 테스트
- 제약: Next.js 15 + App Router + Tailwind + 토스트 알림

→ 즉 A그룹은 **같은 요구사항에 대한 3가지 AI 구현물**입니다 (Antigravity, Prometheus1, Prometheus5 = 평가/비교용 데이터셋).

## 1. 한눈에 비교

| 항목 | Antigravity1 | Prometheus1 | prometheus5 | workflowOn | workflowTwo3Layer1 | workflowTwo3Layer2 |
| --- | --- | --- | --- | --- | --- | --- |
| Next.js | 16.2 | 14.2 | 16.2 | 15 | 15 | 15 |
| React | 19 | 18 | 19 | — | — | — |
| 상태관리 | useState | useNodesState/useEdgesState | **Zustand** | **Zustand** | Zustand | Zustand |
| 노드 타입 | LLM/Output/Generic | Custom 1종 | Start/Process/Condition/End | LLM/HTTP | LLM/HTTP | LLM/HTTP |
| 노드 팔레트(좌측) | ❌ 헤더 버튼 | ❌ | ✅ NodePalette | ✅ NodeSidebar | ✅ | ✅ NodeSidebarView |
| 속성 패널(우측) | ✅ Properties | ❌ | ✅ NodeProperties | — | — | — |
| 로그/감사 | logs/history.log | logs/history.log + /api/logs | LogPanel UI + /api/logs | — | — | — |
| 검증 | id/type/position | path traversal까지 차단 | zod 사용 | — | — | — |
| 실행 엔진 | Kahn 위상정렬 (시뮬레이션) | client에서 단순 실행 | **AsyncGenerator + DAG** | Kahn + 실제 HTTP fetch | Biz 분리 + Kahn | Biz 분리 + Kahn |
| 디자인 톤 | 다크 그라데이션, 사이드바 | 단순 표 | 한글 UI, 깔끔 | shadcn/ui 기반 | — | shadcn/ui |
| 아키텍처 | flat (lib/storage, lib/engine) | flat (lib/workflowRepository) | lib/lib/lib (5개) + stores | biz/rpo/components | **3계층 엄격 분리** | **3계층 엄격 분리** |
| 테스트 | vitest 2종 (storage + engine) | vitest 1종 | jest 1종 | ❌ | ❌ | ❌ |

## 2. 그룹 A (생성소스) — 자세히

### 2.1 Antigravity1

**장점**:
- UI 완성도 가장 높음 (다크 그라데이션, blur 효과, 슬라이드 사이드바). 우리 시연에 그대로 쓸 만한 디자인 수준
- **노드 타입별 컴포넌트 분리** (LLMNode, OutputNode, GenericNode)
- 실행 결과를 한 노드씩 1초 간격으로 UI에 반영 (`for (const step of result.trace)` 패턴) — 시연 임팩트 강함
- 토스트(`sonner`)·아이콘(`lucide-react`) 완비
- 테스트 2종 (storage + engine)

**단점**:
- 상태가 useState 직접 관리 → 다른 컴포넌트에서 워크플로우 접근 어려움
- `storage.ts`에 비즈니스 로직과 fs IO가 섞여 있음
- 노드 타입 추가하려면 `nodeTypes` map + 컴포넌트 파일 + 헤더 버튼 세 군데 수정

### 2.2 Prometheus1

**장점**:
- **보안 의식 가장 강함** — `sanitizeFileName`, path traversal 차단 (`getSafeWorkflowPath`)
- Repository 패턴 분리 (`WorkflowRepository` 클래스)
- 로그 API(`/api/logs`)까지 분리
- zod 의존성 (스키마 검증 가능)

**단점**:
- React Flow 핸들을 직접 `<div>`로 그림 (정식 `Handle` 컴포넌트 미사용) → React Flow의 연결 동작이 이상해질 수 있음
- 좌측 노드 팔레트 없음, 우측 속성 패널도 없음
- UI 완성도 가장 낮음 (단순 표)

### 2.3 prometheus5

**장점**:
- **AsyncGenerator로 실행 진행 상황 yield** — 진짜 스트리밍 실행. UI에서 진행률을 실시간으로 받기 좋음
- Zustand store 분리 (`stores/workflowStore.ts`)
- 한글 UI ("워크플로우 빌더", "드래그 앤 드롭으로...")
- 5개 lib 분리: validation / storage / logger / FileIO / engine — 책임 명확
- NodePalette + NodePropertiesPanel + LogPanel 3패널 모두 있음
- 9개 JSON 샘플 워크플로우 데이터 동봉 (시연 즉시 가능)
- 조건 노드에서 10% 확률 실패 시뮬레이션 (오류 처리 시연 가능)

**단점**:
- 5개 lib 분리가 약간 과함 (`WorkflowFileIO`, `workflowStorage`가 역할 겹침)
- vitest와 jest가 둘 다 devDependency에 있음 (정리 필요)
- 외부 폴더 한 단계 더 깊음 (`prometheus5/workflow-app/`)

## 3. 그룹 B (proj_boot) — 자세히

### 3.1 workflowOn

**장점**:
- **shadcn/ui 사용** (`components.json` 있음). 디자인 시스템 통일성
- `biz/`(서비스) + `rpo/`(리포지터리) 분리 — 우리 백엔드 `src_codex` 패턴과 일치
- **실제 HTTP fetch 실행** (`httpNode`에 url 넣고 실행하면 진짜 호출)
- 좌측 NodeSidebar 있음

**단점**:
- 테스트 전혀 없음
- 노드 속성 편집 UI 없음
- 로그/감사 없음
- 그래프 검증(사이클·필수필드 등) 약함

### 3.2 workflowTwo3Layer1 / Layer2

이 두 소스가 **이 비교에서 가장 흥미로움**. 둘 다 같은 **3계층 분리** 아키텍처 표준을 따름:

```
Frontend
  ├ page/   *Page.tsx     UI 엔트리
  ├ hook/   *Hook.ts      Zustand 로직
  ├ view/   *View.tsx     순수 UI
  └ client/ *Client.ts    API 호출 전담

Backend
  ├ app/    *App.ts       서버 엔트리
  ├ biz/    *Biz.ts       비즈니스 로직
  ├ rpo/    *Rpo.ts       영속성
  └ core/   *Core.ts      도메인 모델 + 포트(Interface)
```

**파일 명명 규칙이 강제됨** (Page/Hook/View/Client/App/Biz/Rpo/Core 8가지 suffix 필수).

**Layer1 vs Layer2 차이**:
- Layer1: 최상위 `app/`, `backend/`, `frontend/` 폴더 3개로 단절
- Layer2: 모두 `src/` 하위 (`src/app`, `src/frontend`, `src/backend`)로 통합 — Next.js 표준에 더 가까움

**장점 (공통)**:
- 우리 백엔드(`src_codex` → claud_통합 이식)와 **거의 동일한 철학**: Repository(Rpo) + Biz + Core(Port/Interface) 분리
- 포트(`WorkflowRpoPortCore`) 인터페이스 분리 → 저장소 교체 용이
- DTO(`WorkflowRequestDtoCore`) 분리 → 네트워크 경계 명확
- Layer2는 NodeSidebarView까지 view 폴더에 들어 있어 가장 정리됨

**단점 (공통)**:
- 테스트 전혀 없음
- 의존 라이브러리 최소 (`reactflow`만) — 토스트/아이콘/디자인 시스템 부재
- UI 디자인 매력 낮음
- 명명 규칙이 학습 곡선이 있음 (Page/Hook/View/Client 분리가 처음엔 과해 보일 수 있음)

## 4. 우리 `claud_통합`에 가장 적합한 조합 추천

우리 요구사항을 다시 확인:
- 온톨로지 JSON 외부화
- 검색 가능
- **워크플로우 화면 그리고 실행**
- 화면 또는 `/docs`에서 거의 수정 없이 호출

### 4.1 최선 조합 (시각적 임팩트 + 운영 가능)

```
디자인 / UX        ← Antigravity1
좌측 노드 팔레트    ← prometheus5
우측 속성 패널      ← Antigravity1
실행 진행 표시     ← prometheus5 (AsyncGenerator) 또는 Antigravity1 (for-of)
저장소·실행 분리   ← workflowTwo3Layer2 (3계층 + Port 인터페이스)
보안 (path traversal) ← Prometheus1
샘플 데이터        ← prometheus5의 9개 JSON
```

즉 **"workflowTwo3Layer2의 폴더 구조 + Antigravity1의 UI + prometheus5의 실행 엔진"** 조합이 가장 강합니다.

### 4.2 가장 적은 노력으로 가져올 수 있는 단일 소스

**prometheus5 (workflow-app)** — 추천.
- Next.js 16, Zustand, 3패널 UI, 9개 샘플, AsyncGenerator 실행 모두 갖춤
- 한글 UI라 우리 교육 자료와 톤 일치
- 단점인 lib 중복은 무시해도 동작에 문제 없음

대안: **workflowTwo3Layer2** — 아키텍처 깔끔하나 UI를 직접 입혀야 함

### 4.3 우리 백엔드(FastAPI)와 결합하는 방식

claud_통합 백엔드는 **FastAPI**이고, 6개 소스 모두 **Next.js API Route**에 워크플로우 저장 로직을 둠. 둘 중 하나 결정 필요:

| 옵션 | 결정 시 영향 |
| --- | --- |
| **A. FastAPI로 워크플로우 API 옮기기** | 6개 소스의 백엔드 코드는 참고만, UI/실행 엔진은 Next.js. 우리 FastAPI에 `/api/workflows` 추가 |
| **B. Next.js API Route 그대로 사용** | Next.js가 워크플로우 도메인 담당, FastAPI는 온톨로지·검색·인증 담당. 도메인 분할 |

**옵션 A 추천**. 이유:
- 워크플로우 실행이 온톨로지 객체와 연결돼야 함 (예: 주문 객체에 결재 워크플로우 적용)
- 그러려면 두 도메인이 같은 백엔드에 있어야 데이터 접근 쉬움
- 우리 백엔드는 이미 WorkflowService + 7전이가 있음 — 거기에 React Flow 그래프 데이터를 추가만 하면 됨

## 5. 작업 권고 순서 (참고용)

1. **prometheus5의 frontend/(components, stores, lib)를 우리 `claud_통합/frontend/src/`에 이식** (~1시간)
2. fetch 호출 경로를 `/api/workflows`(Next.js) → `http://localhost:8000/api/workflows`(FastAPI)로 변경
3. 우리 FastAPI에 `POST /api/workflows/graph` 추가 — 기존 `WorkflowService`에 그래프 저장 메서드 1개 추가
4. 노드 타입을 우리 도메인(ApproveOrder, RejectOrder, …)에 맞게 교체
5. AG-1(다크모드)·AG-3(차트) 같은 Antigravity 제안은 이 단계 끝난 후

## 6. 라이선스·출처 주의

위 6개 소스가 회사 내부 자산인지 외부 공개인지에 따라 직접 코드 복사 가능 여부가 달라집니다. **구조·패턴은 참고**하되 **코드 복사 전 출처 확인** 필요.

---

## 7. 한 줄 결론

> **우리 워크플로우 화면은 prometheus5를 베이스로 가져오되, 폴더 구조는 workflowTwo3Layer2의 3계층 분리를 따르고, 백엔드는 우리 FastAPI에 통합한다.**

이것이 가장 적은 위험으로 시연 + 향후 솔루션화까지 일관성 있게 가는 길입니다.
