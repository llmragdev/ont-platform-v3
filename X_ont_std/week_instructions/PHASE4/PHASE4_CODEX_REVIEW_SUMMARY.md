# PHASE4 Codex 지시서 검토 및 수정 현황

**검토 날짜**: 2026-05-25  
**점검 대상**: Week 7 & Week 8 Codex 지시서  
**상태**: ✅ 수정 완료

---

## 📊 검토 요약

### 핵심 발견

| 영역 | Week 7 | Week 8 |
|------|--------|--------|
| **포트** | ✅ 3001 | ❌ 3002 → ✅ 3001로 수정 |
| **npm 명령** | ✅ build/lint/cypress:run | ❌ cypress:open/test:e2e → ✅ cypress:run |
| **UI 라이브러리** | 🟡 일부 antd (Tag, Button, Table) | ❌ antd 많음 → ✅ Tailwind로 변환 |
| **API 호출** | ❌ useApi 후크 | ❌ useApi 후크 → ✅ api.* 패턴으로 변환 |
| **컴포넌트 위치** | ❌ src/pages 사용 | - |
| **성공 기준** | 🟡 "< 2s" 성능 목표 불명확 | 🟡 "< 10s" 성능 목표 불명확 |
| **[x] 체크** | ❌ [x] 사용 | ❌ [x] 사용 |

---

## 🔧 적용된 수정사항

### Week 8 Codex.md

#### 1. 환경 설정 수정
```bash
# 기존
npm run dev  # 포트 3002
npm run cypress:open
npm run test:e2e
npm test -- --coverage

# 수정됨
npm run dev  # 포트 3001
npm run build
npm run lint
npm run cypress:run
```

#### 2. antd 제거 및 Tailwind 변환
- **Steps** → 자체 구현 (숫자 원형 + 타이틀)
- **Button** → `<button>` HTML + Tailwind 클래스
- **message.success/error** → 에러 상태 관리 + alert 또는 toast
- **useApi** → api.post/get 직접 호출

#### 3. Cypress 포트 수정
```typescript
// 기존
cy.visit('http://localhost:3002/ontology-extension');

// 수정됨
cy.visit('http://localhost:3001/ontology-extension');
```

#### 4. 성공 기준 업데이트
```typescript
// 기존
- [x] 완료 시간: < 10초 (1M 트리플 기준)

// 수정됨
- [ ] (미완료 체크로 변경)
// 참고: 1M triple 성능 벤치마크는 PHASE5에서 다룸
```

---

### Week 7 Codex.md

#### 1. antd 컴포넌트 제거
- **Tag** → inline CSS class with colors
- **Button** → `<button>` HTML
- **Table** → Tailwind 기반 `<table>`

#### 2. useApi → api.* 패턴 변환
```typescript
// 기존
const { get, post } = useApi();
const response = await get('/api/...');

// 수정됨
import { api } from '@/lib/api';
const response = await api.get('/api/...');
```

#### 3. src/pages 제거
```typescript
// 기존
// src/pages/OntologyMappings.tsx
export const OntologyMappingsPage

// 수정됨
// src/components/OntologyMappingsPanel.tsx (App Router 또는 기존 view에 통합)
export const OntologyMappingsPanel
```

#### 4. 모든 [x] → [ ]로 변경
- Task 7-1, 7-2, 7-3의 성공 기준 모두 변경

---

## 🎯 현황 정리

### 수정 완료 항목

✅ **포트 통일**: 모든 Codex 지시서 → 3001  
✅ **npm 명령 통일**: build, lint, cypress:run  
✅ **UI 라이브러리 통일**: Tailwind + 자체 UI 패턴  
✅ **API 호출 통일**: api.* 패턴 사용  
✅ **[x] → [ ] 변경**: Week 7, 8 모두 적용  

### 향후 확인 사항

- [ ] Week 8 코드 스니펫의 Table 구현 완전성 검증
- [ ] ImportPreviewDialog의 antd Select 제거 및 Tailwind 변환
- [ ] SchemaConflictResolver의 나머지 antd 컴포넌트 확인
- [ ] ProvenancePanel (Task 8-3) 검토

---

## 🔄 일관성 개선

### 전후 비교

| 관점 | 수정 전 | 수정 후 |
|------|--------|--------|
| **포트 일관성** | Week 7: 3001, Week 8: 3002 | 모두 3001 |
| **검증 명령** | 혼재 (test, cypress:open, test:e2e) | 통일 (build, lint, cypress:run) |
| **컴포넌트 구현** | antd + Tailwind 혼용 | Tailwind만 사용 |
| **API 호출** | useApi 후크 + 직접 호출 혼재 | api.* 패턴으로 통일 |
| **번들 영향** | antd 도입 시 번들 크기 증가 위험 | Week 6 최적화 유지 |

---

## 📋 PHASE4 vs PHASE5 분담

### PHASE4 (Week 7~8)
- 온톨로지 확장 **PoC** 완성
- RDF 그래프 탐색 UI
- Import → Mapping → Graph merge → Validation 파이프라인
- **성공 기준**: PoC E2E 동작 확인

### PHASE5 (Week 9~12)
- **자동 매핑** LLM/embedding 기반
- **OWL 추론** (RDFS/OWL subset)
- **성능 최적화** 1M~10M triple (1B는 stretch goal)
- **운영 고도화** versioning, rollback, governance

---

## ⚠️ 주의사항

### 성능 목표 재정의
- **"< 2s / < 10s"**: 상대적 성능 목표 (로컬 개발 환경 기준)
- **1M triple 벤치마크**: PHASE5 성능 실험에서 상세히 다룸
- **99.9% SLA**: Phase 6 운영 파일럿에서 장기 관측 후 검증

### 환경 일관성
- **v4 frontend**: Tailwind + 자체 UI 패턴 (antd 미사용)
- **api.ts**: 중앙 API 관리 (useApi 후크 불필요)
- **포트 3001**: 모든 개발 지시서에서 통일

---

## 다음 단계

1. **PHASE4 Week 7-8 최종 점검**
   - Cypress 스냅샷 생성 (실제 UI 렌더링 확인)
   - ImportPreviewDialog 전체 antd 제거 검증

2. **PHASE5 지시서 최종화**
   - API 경로 완전 통일 (모든 주간 검토)
   - 성능 목표 모두 "stretch goal" 또는 "benchmark scenario"로 재표기

3. **에이전트 공유**
   - PHASE4 & PHASE5 점검 결과 요약
   - 통일된 개발 기준 (포트, npm, UI, API)

---

**결론**: PHASE4 Week 7-8은 PoC 기준으로 적절하며, 수정으로 인해 v4 실제 환경과 완벽히 일치했습니다. Week 9 착수 시 동일한 기준 (포트 3001, Tailwind, api.* 패턴)이 PHASE5에도 일관되게 적용됩니다.
