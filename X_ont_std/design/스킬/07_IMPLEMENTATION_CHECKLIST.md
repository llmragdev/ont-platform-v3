# 스킬 시스템 구현 체크리스트

**일정:** Phase 1 (2주)  
**담당:** Backend + Frontend 팀  
**의존성:** 워크플로우 그래프 저장/실행 API 기존 기능

---

## 📋 전체 로드맵

```
Week 1: 타입 + 백엔드 기본
├─ Day 1-2: 타입 정의, skills.py API
├─ Day 3-4: skill_executor, expression_renderer
└─ Day 5: 테스트

Week 2: 프론트엔드 + 통합
├─ Day 1-2: SkillGallery UI, 설치 로직
├─ Day 3-4: 워크플로우 그래프 통합
└─ Day 5: e2e 테스트, 문서화
```

---

## 🔧 Backend Tasks (Week 1 중심)

### Day 1-2: 타입 정의 + API 스켈레톤

- [ ] **types/api.ts 확장** (프론트엔드)
  ```typescript
  export interface Skill { id, name, implementation, inputSchema, ... }
  export interface GraphNodeData { skillId, skillConfig, ... }
  export type SkillImplementationType = "builtin" | "http" | "mcp_http" | "custom"
  ```

- [ ] **backend/app/models/skill.py 생성**
  ```python
  class Skill(BaseModel): ...
  class SkillConfig(BaseModel): ...
  class MCPHttpConfig(BaseModel): ...
  ```

- [ ] **backend/app/config/skills/builtin_skills.json 작성**
  - 7개 Built-in Skill 정의 (06 문서 기준)
  - customer-comment-create, factory-comment-create 등

- [ ] **backend/app/api/skills.py 생성** (라우터)
  ```python
  GET    /api/skills              # 전체 스킬 조회
  GET    /api/skills/{skill_id}   # 스킬 상세
  POST   /api/skills/custom       # 커스텀 스킬 저장
  PUT    /api/skills/custom/{id}  # 커스텀 스킬 수정
  DELETE /api/skills/custom/{id}  # 커스텀 스킬 삭제
  POST   /api/skills/validate-expression  # 표현식 검증
  ```

- [ ] **backend/app/main.py 수정**
  - `app.include_router(skills_router)`

---

### Day 3-4: 핵심 로직 구현

- [ ] **backend/app/services/skill_service.py**
  ```python
  class SkillService:
      def list_skills(ctx: TenantContext) -> List[Skill]
          # Built-in + Custom 병합
      
      def get_skill(skill_id: str) -> Skill
      
      def save_custom_skill(skill: Skill, ctx: TenantContext)
          # 저장 위치: storage/{company_id}/{project_id}/skills/custom_skills.json
      
      def delete_custom_skill(skill_id: str, ctx: TenantContext)
      
      def validate_skill_schema(skill: Skill, input_data: Dict)
          # inputSchema 유효성 검증
  ```

- [ ] **backend/app/services/expression_renderer.py** ⭐ 핵심
  ```python
  def resolve_input_value(value: Any, execution_context: Dict) -> Any:
      # {{nodes.xxx.output.yyy}} 표현식 평가
      # 단일 표현식: 원본 타입 유지
      # 복합 보간: 문자열 변환
  
  def prepare_skill_input(skillConfig: Dict, executionContext: Dict) -> Dict:
      # inputMapping 렌더링
  ```

- [ ] **backend/app/services/skill_executor.py** ⭐ 핵심
  ```python
  class SkillExecutor:
      def execute(skill: Skill, input_data: Dict, ctx: TenantContext) -> Dict:
          if impl.type == "builtin":
              return self._execute_builtin(skill, input_data)
          elif impl.type == "http":
              return self._execute_http(impl, input_data)
          elif impl.type == "mcp_http":
              return self._execute_mcp_http(impl, input_data)
          elif impl.type == "custom":
              raise NotImplementedError("Phase 2+")
  
      def _execute_http(self, impl: HttpConfig, input_data: Dict) -> Dict
      
      def _execute_mcp_http(self, impl: MCPHttpConfig, input_data: Dict) -> Dict:
          # tool_endpoint vs jsonrpc_proxy 구분
          if impl.callStyle == "tool_endpoint":
              return requests.post(impl.endpoint, json=input_data)
          else:
              return requests.post(impl.endpoint, json=json_rpc_wrapper(...))
      
      def _execute_builtin(self, skill: Skill, input_data: Dict) -> Dict
          # ontology_write, rag_lookup 등
  ```

- [ ] **backend/app/services/workflow.py 수정** (기존 코드)
  - 노드 타입이 `"skill"`이면 `SkillExecutor` 호출
  - 실행 결과를 `WorkflowRun.steps` 에 저장

---

### Day 5: 테스트

- [ ] **tests/test_skill_service.py**
  ```python
  test_list_skills()
  test_get_builtin_skill()
  test_save_custom_skill()
  test_skill_schema_validation()
  ```

- [ ] **tests/test_expression_renderer.py**
  ```python
  test_single_expression_preserves_type()  # {{nodes.x}} → array, int 유지
  test_string_interpolation()              # "text {{nodes.x}}" → string
  test_missing_field_handling()            # {{nodes.x.missing}} → ""
  test_nested_properties()                 # {{nodes.x.output.a.b.c}}
  ```

- [ ] **tests/test_skill_executor.py**
  ```python
  test_execute_builtin_skill()
  test_execute_http_skill()
  test_execute_mcp_http_tool_endpoint()
  test_execute_mcp_http_jsonrpc_proxy()
  test_custom_skill_blocked_in_phase1()
  ```

---

## 🎨 Frontend Tasks (Week 2 중심)

### Day 1: 기본 구성

- [ ] **frontend/src/types/api.ts 확장**
  ```typescript
  interface Skill { ... }
  interface MCPHttpConfig { ... }
  type SkillImplementationType = ...
  ```

- [ ] **frontend/src/lib/skills.ts** (API 클라이언트)
  ```typescript
  export const skillsAPI = {
    list: () => api.get('/skills'),
    get: (id) => api.get(`/skills/${id}`),
    saveCustom: (skill) => api.post('/skills/custom', skill),
    deleteCustom: (id) => api.delete(`/skills/custom/${id}`),
    validateExpression: (expr, ctx) => api.post('/skills/validate-expression', {...})
  }
  ```

---

### Day 2-3: UI 컴포넌트

- [ ] **frontend/src/components/SkillGallery.tsx**
  ```tsx
  <SkillGallery>
    ├─ SearchBox
    ├─ CategoryFilter
    └─ SkillGrid
        ├─ SkillCard (Built-in)
        │  ├─ name, description
        │  ├─ inputSchema, outputSchema
        │  └─ [설치] 버튼
        └─ SkillCard (Custom)
           ├─ [설치], [편집], [삭제] 버튼
  ```

- [ ] **frontend/src/components/SkillEditor.tsx** (모달)
  ```tsx
  <SkillEditorModal>
    ├─ Name input
    ├─ Description textarea
    ├─ Category select
    ├─ inputSchema JSON editor
    ├─ outputSchema JSON editor
    └─ [Save], [Cancel] 버튼
  ```

- [ ] **frontend/src/components/SkillMappingPanel.tsx**
  ```tsx
  // WorkflowGraph 우측 사이드바에 추가
  // 선택한 노드의 skillConfig 편집
  ├─ inputMapping editor
  │  └─ key: value (expression 입력)
  └─ outputMapping editor
  ```

---

### Day 4: WorkflowGraph 통합

- [ ] **frontend/src/components/WorkflowGraph.tsx 수정**
  - [ ] 우측 탭에 "스킬" 추가 (기존 "선택항목" 탭 옆)
  - [ ] SkillGallery 렌더링
  - [ ] "설치" 클릭 → `type: "skill"` 노드 추가
  - [ ] 노드 선택 → SkillMappingPanel 표시
  - [ ] Run 결과 표시 → 스킬 입출력 확인

- [ ] **frontend/src/lib/workflowTemplates.ts** (선택사항)
  - 공장 자동화 시나리오 스킬 템플릿
  - 고객 자동댓글 시나리오 스킬 템플릿

---

### Day 5: 테스트 + 통합

- [ ] **스킬 갤러리 UI 테스트**
  - [ ] Built-in Skill 표시
  - [ ] Custom Skill 표시
  - [ ] 검색/필터
  - [ ] 설치 버튼 동작

- [ ] **e2e 테스트**
  - [ ] 스킬 설치 → 워크플로우에 노드 추가
  - [ ] inputMapping 입력 → 표현식 평가
  - [ ] 워크플로우 실행 → 스킬 실행
  - [ ] 결과 저장 → WorkflowRun에 기록

- [ ] **기존 기능 회귀 테스트**
  - [ ] 워크플로우 그래프 저장/로드
  - [ ] 노드 추가/삭제
  - [ ] 실행 이력

---

## 📊 구현 우선순위

### 필수 (P0)

- [ ] expression_renderer.py (타입 보존)
- [ ] skill_executor.py (builtin, http, mcp_http)
- [ ] skills.py API
- [ ] SkillGallery UI
- [ ] WorkflowGraph 통합

### 권장 (P1)

- [ ] SkillEditor (커스텀 스킬 편집)
- [ ] 테스트 완성도
- [ ] 문서화

### 선택 (P2)

- [ ] 시나리오별 템플릿
- [ ] 권한/감시 로깅

---

## 🧪 테스트 전략

### 단위 테스트 (Unit)

```python
# backend/tests/
test_skill_service.py       # SkillService
test_expression_renderer.py # {{...}} 렌더링
test_skill_executor.py      # 스킬 실행
```

### 통합 테스트 (Integration)

```python
# backend/tests/integration/
test_skill_workflow_integration.py
  - 스킬이 포함된 워크플로우 실행
  - inputMapping 렌더링 → 스킬 호출 → 결과 저장
```

### UI 테스트 (E2E, 선택사항)

```javascript
// frontend/tests/
test_skill_gallery.test.tsx
test_skill_mapping.test.tsx
test_workflow_skill_integration.test.tsx
```

---

## 📝 주의사항

### 🔴 Critical

- [ ] **Windows 호환성:** signal.alarm 사용 금지 (multiprocessing 사용)
- [ ] **타입 보존:** 배열/객체 타입을 문자열로 강제 변환하지 말 것
- [ ] **MCP HTTP 방식:** tool_endpoint vs jsonrpc_proxy 정확히 구분

### 🟠 Important

- [ ] **저장 경로:** 절대 경로 문자열 조합 금지, get_project_root() 사용
- [ ] **Custom Code:** Phase 1에서는 실행 금지 (저장만 가능)
- [ ] **GraphNodeKind:** 기존 타입 삭제 금지, 새 타입 추가만

### 🟡 Good to Have

- [ ] **에러 처리:** 스킬 호출 실패 시 WorkflowRun에 에러 기록
- [ ] **로깅:** 표현식 평가, 스킬 실행 과정 로깅
- [ ] **성능:** HTTP 타임아웃 설정, 병렬 스킬 실행 고려 (향후)

---

## 📦 산출물 체크리스트

구현 완료 시 다음을 제출하세요:

- [ ] **backend/app/services/skill_*.py** (3개 파일)
- [ ] **backend/app/api/skills.py**
- [ ] **backend/app/config/skills/builtin_skills.json**
- [ ] **frontend/src/components/Skill*.tsx** (3개 컴포넌트)
- [ ] **frontend/src/lib/skills.ts**
- [ ] **frontend/src/types/api.ts** (확장)
- [ ] **tests/** (최소 10개 테스트)
- [ ] **07_IMPLEMENTATION_CHECKLIST.md** (이 파일) 완료 표시

---

## ✅ 완료 기준

| 항목 | 기준 |
|------|------|
| 코드 | 모든 P0 항목 구현, 테스트 통과 |
| 테스트 | 단위 10+, 통합 5+, 회귀 기존 기능 무결 |
| 문서 | 코드 주석, API 명세, 트러블슈팅 가이드 |
| 검증 | 06_SKILL_SPEC_FINAL_CONSOLIDATED_REPORT.md 기준 준수 |

---

## 🚀 다음 단계

1. **이 체크리스트 대로 구현**
2. **테스트 완료 후 코드 리뷰**
3. **Codex/Antigravity 검증**
4. **Phase 2 (커스텀 스킬 편집) 계획**

**시작하세요!** 💪

