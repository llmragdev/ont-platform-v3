# 스킬 시스템 검토보고서

- 작성자: Codex
- 작성일: 2026-06-14
- 검토 대상:
  - `design/스킬/SKILL_SYSTEM_DESIGN.md`
  - `design/스킬/skills_catalog.json`
  - `ont_platform/v5` 워크플로우 빌더 및 실행 구조

---

## 1. 검토 결론

현재 스킬 시스템 설계 방향은 적절합니다.

워크플로우 빌더에서 매번 노드 타입을 하드코딩하는 방식에서 벗어나, “설치 가능한 실행 기능”을 스킬로 관리하려는 방향은 v5 플랫폼이 앞으로 확장되기 위해 필요한 구조입니다.

다만 현재 문서는 아직 개념 설계 수준입니다. 실제 v5에 붙이려면 아래 네 가지를 먼저 정리해야 합니다.

1. 스킬은 워크플로우 노드의 실행 기능이고, 온톨로지는 업무 객체와 관계를 설명하는 모델이라는 경계를 명확히 해야 합니다.
2. 스킬 저장 위치는 `design/스킬`이 아니라 테넌트/프로젝트 단위 저장소 또는 백엔드 config/API로 이동해야 합니다.
3. 현재 프론트 타입에는 `skill`, `custom_code`, `skillId`, `skillConfig` 개념이 아직 없습니다.
4. Python ad-hoc 실행은 보안 위험이 크므로 MVP에서는 “정의만 가능, 실행은 Built-in 또는 MCP/HTTP만 가능”으로 제한하는 것이 안전합니다.

---

## 2. 현재 문서 상태

### 2.1 잘 되어 있는 점

- Built-in Skill, Custom Skill, Ad-hoc Code를 구분한 점은 좋습니다.
- 입력 스키마와 출력 스키마를 명시한 점도 좋습니다.
- 워크플로우 노드에 `skillId`, `inputMapping`, `outputMapping`을 붙이는 방향은 현재 워크플로우 빌더와 잘 맞습니다.
- `skills_catalog.json`은 JSON 형식 오류 없이 정상입니다.
- Phase 1, 2, 3으로 나눈 단계적 접근도 적절합니다.

### 2.2 보완이 필요한 점

현재 문서에는 저장소 구조 예시에 `01_스킬_카테고리_정의.md`가 포함되어 있지만 실제 파일은 없습니다.

현재 `skills_catalog.json`의 Built-in 예시는 `https://api.search.service/search`, `https://api.email.service/send` 같은 가상 엔드포인트를 사용합니다. 데모 설계로는 괜찮지만 실제 구현용으로는 “실행 불가 샘플”이라는 표시가 필요합니다.

현재 설계에는 테넌트와 프로젝트 분리가 약합니다. v5 워크플로우는 `company_id`, `project_id` 기준으로 그래프를 저장하고 실행합니다. 스킬도 같은 범위로 관리되어야 합니다.

---

## 3. v5 현 구조와의 정합성

### 3.1 현재 워크플로우 노드 타입

프론트엔드의 `GraphNodeKind`는 현재 다음과 같은 고정 노드 타입 중심입니다.

- `request_input`
- `intent_classify`
- `equipment_map`
- `recurrence_check`
- `knowledge_lookup`
- `draft_response`
- `customer_mcp_comment_create`
- `maintenance_task`
- `quality_link`
- `ontology_write`
- `http`
- `llm`
- 기타 승인/종료 노드

즉, 현재 구조는 “스킬 카탈로그에서 설치한 노드”보다 “미리 정의된 노드 종류를 팔레트에서 추가하는 방식”에 가깝습니다.

스킬 시스템을 붙이려면 최소한 아래 확장이 필요합니다.

```typescript
export type GraphNodeKind =
  | 기존 타입
  | "skill"
  | "custom_code";

export interface GraphNodeData {
  label?: string;
  prompt?: string;
  skillId?: string;
  skillVersion?: string;
  skillConfig?: {
    inputMapping?: Record<string, string>;
    outputMapping?: Record<string, string>;
    parameters?: Record<string, unknown>;
  };
}
```

### 3.2 백엔드 저장 구조

현재 워크플로우 그래프 저장은 프로젝트 단위 파일에 저장됩니다.

```text
storage/{company_id}/{project_id}/workflow_graphs.json
```

따라서 스킬 저장도 아래 중 하나로 가는 것이 자연스럽습니다.

```text
storage/{company_id}/{project_id}/skills/skills_catalog.json
```

또는 시스템 기본 스킬과 프로젝트 커스텀 스킬을 분리합니다.

```text
ont_platform/v5/backend/app/config/skills/builtin_skills.json
storage/{company_id}/{project_id}/skills/custom_skills.json
```

권장안은 두 번째입니다.

---

## 4. 스킬, 액션 타입, 온톨로지의 관계

이 부분은 꼭 문서에 추가해야 합니다. 세 개는 비슷해 보이지만 역할이 다릅니다.

| 구분 | 의미 | 예시 |
|---|---|---|
| 스킬 | 워크플로우 노드가 실행할 수 있는 기능 | 웹 검색, MCP 댓글 등록, 정비 지시 생성, 텍스트 변환 |
| 액션 타입 | 특정 객체에 대해 사용자가 실행하는 업무 명령 | 주문 승인, 정비 요청 생성, 댓글 등록 |
| 온톨로지 | 업무 객체와 관계의 모델 | 설비, 생산 라인, 고장 이벤트, 정비 작업, 서비스 요청 |

정리하면 다음과 같습니다.

```text
워크플로우 노드
  -> 스킬을 실행한다
  -> 실행 결과를 만든다
  -> 필요하면 온톨로지 객체/관계로 저장한다
```

예를 들어 공장 자동화 시나리오에서는 다음처럼 연결됩니다.

```text
현장 고장 요청 접수
  -> 반복 고장 확인 스킬 실행
  -> 정비 지시 생성 스킬 실행
  -> Factory, ProductionLine, Equipment, FaultEvent, MaintenanceTask 관계 저장
```

즉, 스킬은 “무엇을 실행할지”이고 온톨로지는 “그 실행 결과가 업무 세계에서 어떤 의미인지”입니다.

---

## 5. 보안 검토

현재 설계의 가장 큰 위험은 Python 코드 실행입니다.

문서에는 Custom Skill 생성 시 Python 코드를 저장하고 실행하는 흐름이 있습니다. 이 기능은 강력하지만, 기업 납품용 플랫폼에서는 초기 MVP에 바로 넣기 어렵습니다.

위험 요소는 다음과 같습니다.

- 파일 시스템 접근
- 네트워크 임의 호출
- 무한 루프 또는 과도한 CPU 사용
- 비밀키, 환경변수 탈취
- 테넌트 간 데이터 접근 위험

따라서 단계별 권장안은 다음과 같습니다.

| 단계 | 허용 방식 | 비고 |
|---|---|---|
| Phase 1 | Built-in, HTTP, MCP 스킬만 실행 | 가장 안전 |
| Phase 2 | Custom Skill 저장/편집만 허용 | 실행은 제한 |
| Phase 3 | 샌드박스 기반 Python 실행 | Docker, timeout, 권한 제한 필요 |

MVP에서는 `custom` 타입의 코드는 저장만 가능하게 하고, 실제 실행은 막는 것이 좋습니다.

---

## 6. 구현 영향도

### 6.1 프론트엔드 변경 대상

| 파일 | 변경 내용 |
|---|---|
| `frontend/src/types/api.ts` | `GraphNodeKind`, `GraphNodeData`, `Skill` 타입 추가 |
| `frontend/src/components/WorkflowGraph.tsx` | 우측 탭에 스킬 갤러리 추가, 노드에 스킬 연결 |
| `frontend/src/components/Sidebar.tsx` | 필요 시 “스킬 관리” 메뉴 추가 |
| 신규 `frontend/src/components/SkillGallery.tsx` | 스킬 검색, 필터, 설치 UI |
| 신규 `frontend/src/components/SkillEditor.tsx` | 커스텀 스킬 생성/편집 UI |
| `frontend/src/lib/api.ts` | 스킬 목록/저장/삭제/설치 API 클라이언트 추가 |

### 6.2 백엔드 변경 대상

| 파일 | 변경 내용 |
|---|---|
| 신규 `backend/app/api/skills.py` | 스킬 CRUD API |
| 신규 `backend/app/services/skill_service.py` | Built-in + Custom Skill 로딩, 저장, 권한 처리 |
| 신규 `backend/app/config/skills/builtin_skills.json` | 시스템 기본 스킬 카탈로그 |
| `backend/app/api/workflow.py` | `skill` 노드 실행 분기 추가 |
| `backend/app/services/workflow.py` | 그래프 저장 시 skill metadata 유지 검증 |
| `backend/app/main.py` | skills router 등록 |

### 6.3 저장소 변경 대상

권장 구조는 다음과 같습니다.

```text
ont_platform/v5/backend/app/config/skills/
└─ builtin_skills.json

ont_platform/storage/{company_id}/{project_id}/skills/
└─ custom_skills.json
```

`design/스킬/skills_catalog.json`은 구현용 저장소가 아니라 설계 샘플로 유지하는 것이 좋습니다.

---

## 7. 구현 우선순위 제안

### 1순위: 스킬 개념을 타입과 문서에 반영

먼저 프론트/백엔드 타입에 `Skill`, `skillId`, `skillConfig`를 추가합니다.

이 단계에서는 실행까지 하지 않아도 됩니다. 중요한 것은 워크플로우 그래프에 “이 노드는 어떤 스킬을 사용한다”는 정보가 저장되는 것입니다.

### 2순위: Built-in Skill 갤러리 UI

현재 노드 팔레트 옆이나 우측 패널에 스킬 갤러리를 추가합니다.

초기 Built-in Skill은 실제 v5 시나리오와 연결되는 것부터 넣는 것이 좋습니다.

- 고객 문의 댓글 등록
- 공장 현장 댓글 등록
- 정비 지시 생성
- 온톨로지 저장
- RAG/온톨로지 근거 조회

### 3순위: MCP/HTTP 실행 스킬

MVP에서 실제 실행 가능한 스킬은 MCP 또는 HTTP 기반으로 제한합니다.

예:

```json
{
  "id": "factory-comment-create",
  "name": "공장 게시판 댓글 등록",
  "implementation": {
    "type": "mcp",
    "tool": "comment.create",
    "server": "s2_factory_mcp"
  }
}
```

### 4순위: Custom Skill 저장

커스텀 스킬 생성/편집은 가능하게 하되, 실행은 막거나 `disabled` 상태로 둡니다.

### 5순위: 샌드박스 실행

Python 실행은 마지막 단계로 미룹니다.

---

## 8. 문서 보완 제안

`SKILL_SYSTEM_DESIGN.md`에는 아래 섹션을 추가하는 것이 좋습니다.

1. 스킬/액션/온톨로지 차이
2. 테넌트/프로젝트별 스킬 저장 구조
3. Built-in Skill과 Custom Skill의 실행 가능 범위
4. MVP에서는 Python 실행 제외
5. 현재 v5 워크플로우 타입 변경안
6. 스킬 설치 시 워크플로우 노드에 저장되는 실제 JSON 예시

또한 현재 문서의 저장소 구조에는 존재하지 않는 `01_스킬_카테고리_정의.md`가 있으므로, 실제로 만들거나 예시에서 제거해야 합니다.

---

## 9. 권장 MVP 범위

처음부터 완전한 스킬 마켓플레이스를 만들기보다, 현재 공장자동화/고객문의 시나리오를 더 잘 설명하고 실행할 수 있는 작은 범위로 시작하는 것이 좋습니다.

권장 MVP는 다음입니다.

```text
스킬 카탈로그 조회
  -> Built-in Skill 카드 표시
  -> 워크플로우에 Skill 노드 추가
  -> 노드 속성에서 input/output mapping 확인
  -> Run 시 MCP/HTTP 기반 스킬만 실행
  -> 실행 결과는 기존 WorkflowRun 이력에 저장
  -> 필요 시 온톨로지 매핑으로 저장
```

이렇게 하면 사용자에게도 설명하기 쉽습니다.

“워크플로우는 업무 순서이고, 스킬은 각 단계에서 실제로 수행하는 기능이며, 온톨로지는 그 결과를 업무 객체와 관계로 남기는 구조입니다.”

---

## 10. 최종 의견

스킬 시스템은 v5에 넣을 가치가 있습니다.

다만 지금 바로 Python 커스텀 코드 실행까지 가면 구현 범위와 보안 리스크가 커집니다. 먼저 Built-in/MCP/HTTP 스킬을 워크플로우 노드에 연결하고, 그 결과를 실행 이력과 온톨로지에 남기는 구조부터 만드는 것이 좋습니다.

특히 공장자동화 시나리오에서는 스킬 개념이 매우 잘 맞습니다.

- 고장 분류 스킬
- 설비 매핑 스킬
- 반복 고장 확인 스킬
- 정비 지시 생성 스킬
- 현장 댓글 등록 스킬
- 온톨로지 저장 스킬

이 흐름으로 보여주면 “워크플로우와 온톨로지를 왜 써야 하는가”도 훨씬 직관적으로 설명할 수 있습니다.
