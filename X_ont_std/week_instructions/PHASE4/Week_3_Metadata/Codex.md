# Phase 4 Week 3: Metadata + Audit System
## Codex (Frontend) 수행 지시서

**기간**: 2026-08-05 ~ 2026-08-18 (2주)  
**할당**: 10% (주당 3-5시간)  
**목표**: v4 API 분석 + MetadataPanel, LineageViewer 컴포넌트 설계

---

## Prep 1: v4 API 스펙 확인 및 TypeScript 타입 정의

**기간**: 08-05 ~ 08-11 (1주)  
**목표**: Week 3 Claude가 구현할 API 이해 및 프론트엔드 타입 정의

### 필요 API 분석

```typescript
// types/api.ts

interface EntityMetadata {
  entity_id: string;
  domain_id: string;
  created_by: string;
  created_at: string;
  updated_by?: string;
  updated_at?: string;
  version: number;
  tags: string[];
  description: string;
  data_quality_score?: number;
  last_validated_at?: string;
}

interface PropertyChange {
  property_name: string;
  old_value?: any;
  new_value: any;
  changed_at: string;
  changed_by: string;
}

interface Transformation {
  transformation_id: string;
  operation_type: string; // merge, split, enrich, filter
  input_entity_ids: string[];
  output_entity_id: string;
  transformation_rule: Record<string, any>;
  performed_by: string;
  performed_at: string;
  status: "completed" | "failed" | "pending";
  error_message?: string;
}

interface LineageInfo {
  entity_id: string;
  source_entities: string[];
  transformations: Transformation[];
  data_quality_chain: number[];
  created_from_import?: Record<string, any>;
}

interface EntityVersion {
  version_id: string;
  entity_id: string;
  version_number: number;
  data: Record<string, any>;
  changed_fields: string[];
  changed_by: string;
  changed_at: string;
  change_reason?: string;
  rollback_enabled: boolean;
}

interface AuditLog {
  audit_id: string;
  entity_id?: string;
  action: "create" | "update" | "delete" | "import" | "merge";
  old_value?: Record<string, any>;
  new_value?: Record<string, any>;
  performed_by: string;
  performed_at: string;
  ip_address?: string;
  user_agent?: string;
  status: "success" | "failed";
  error_details?: string;
  retention_days: number;
}
```

### API 엔드포인트 요청사항

```typescript
// API endpoints needed by frontend

// 1. 엔티티 메타데이터
GET /api/entities/{entity_id}/metadata
  → EntityMetadata

GET /api/entities/{entity_id}/versions
  → EntityVersion[]

POST /api/entities/{entity_id}/versions/{version_id}/rollback
  → EntityMetadata (롤백된 상태)

// 2. 혈통 정보
GET /api/entities/{entity_id}/lineage
  → LineageInfo

GET /api/entities/{entity_id}/impact
  → { affected_entities: [{ id: string; name: string; type: string }] }

// 3. 감시 로그
GET /api/audit/logs?entity_id=...&action=...&performed_by=...
  → { items: AuditLog[]; total: number }

GET /api/audit/logs/export?format=json|csv
  → Blob (파일 다운로드)

// 4. 데이터 품질
GET /api/entities/{entity_id}/data-quality
  → { score: number; factors: Record<string, number> }
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] v4 API 문서 읽기
- [ ] TypeScript 타입 정의 (entities/, audit/, lineage/)
- [ ] Mock API 데이터 생성 (테스트용)
- [ ] API 에러 처리 전략 정의

---

## Prep 2: MetadataPanel + LineageViewer 컴포넌트 설계

**기간**: 08-12 ~ 08-18 (1주)  
**목표**: 메타데이터 및 혈통 시각화 컴포넌트 설계

### MetadataPanel 와이어프레임

```
┌─────────────────────────────────────┐
│ Metadata Panel (우측)               │
├─────────────────────────────────────┤
│ Entity Info                          │
│  ID: entity-123                      │
│  Type: PROJECT                       │
│  Created: 2026-08-05 10:30 by John  │
│  Updated: 2026-08-10 15:45 by Jane  │
├─────────────────────────────────────┤
│ Quality Score: 92/100 ⭐⭐⭐⭐⭐      │
├─────────────────────────────────────┤
│ Version History                      │
│  [v3] Updated: 08-10 15:45          │
│  [v2] Updated: 08-07 09:20          │
│  [v1] Created:  08-05 10:30         │
│  [Rollback to v2]                   │
├─────────────────────────────────────┤
│ Tags                                │
│ [production] [validated] [exported]  │
└─────────────────────────────────────┘
```

### LineageViewer 와이어프레임

```
Lineage: entity-123
└─ Source (import from DBpedia)
   ├─ merge with entity-45 (split)
   │  ├─ enrich with Wikidata
   │  └─ filter (remove duplicates)
   └─ split into entity-67, entity-89
      └─ merge with entity-112 (current)

Quality Chain: 100 → 98 → 95 → 92
```

### 컴포넌트 구조

```typescript
// components/MetadataPanel.tsx
export function MetadataPanel({ 
  entityId: string;
  onVersionRollback?: (versionId: string) => void;
}) {
  // EntityMetadata 조회
  // EntityVersion 목록 표시
  // Rollback 버튼
}

// components/LineageViewer.tsx
export function LineageViewer({
  entityId: string;
  onEntityClick?: (entityId: string) => void;
}) {
  // LineageInfo 조회
  // 트리/그래프 시각화 (D3/Cytoscape)
  // 품질 점수 전파 시각화
}

// components/AuditLogTable.tsx
export function AuditLogTable({
  entityId?: string;
  filters?: AuditQuery;
  onExport?: () => void;
}) {
  // 감시 로그 표시
  // 필터링 (Entity, Action, Actor, Date)
  // Export to CSV
}
```

### 예상 시간: 3-4일

**체크리스트**:
- [ ] 3가지 컴포넌트 와이어프레임 완성
- [ ] 상호작용 명세 문서화
- [ ] 색상/스타일 가이드
- [ ] Mock 데이터로 레이아웃 검증

---

## 📋 일일 진행 계획

### 08-05 (월) ~ 08-08 (목)
- [ ] v4 API 스펙 분석
- [ ] TypeScript 타입 정의
- [ ] Mock API 데이터

### 08-09 (금) ~ 08-12 (월)
- [ ] MetadataPanel 와이어프레임
- [ ] LineageViewer 와이어프레임
- [ ] AuditLogTable 와이어프레임

### 08-13 (화) ~ 08-18 (일)
- [ ] 컴포넌트 명세서 작성
- [ ] 상호작용 흐름 정의
- [ ] Claude와 API 설계 리뷰

---

## 🎯 성공 기준

✅ v4 API 완전히 이해  
✅ TypeScript 타입 정의 100% 완성  
✅ 3개 컴포넌트 와이어프레임 완성  
✅ Mock 데이터로 레이아웃 검증  
✅ Week 4-5 구현 준비 완료

---

## 📞 상호작용

**Claude와의 연계**:
- Week 3 API 스펙 확인 (Task 3-1 완료 후)
- 메타데이터 응답 포맷 검증

**Antigravity와의 협력**:
- 메타데이터 쿼리 성능 기준선

---

**상태**: Prep 1-2 준비 완료  
**예상 완료**: 2026-08-18  
**다음 단계**: Week 4-5 컴포넌트 구현

---

## 📝 최종 보고서 작성 가이드

**완료 후 다음 형식으로 최종 보고서를 작성하여 제출하세요.**

```markdown
# Phase 4 Week 3: Codex (프론트엔드 설계) 완료 보고서

**기간**: 2026-08-05 ~ 2026-08-18 (2주)
**할당**: 10% (주당 3-5시간)
**상태**: ✅ 완료
**날짜**: [실제 보고서 작성 날짜]

---

## 📋 작업 요약

### Prep 1: TypeScript 타입 정의 및 컴포넌트 아키텍처
- ✅ v4 메타데이터 API 응답 타입 정의
- ✅ 엔티티 메타데이터 TypeScript 인터페이스 작성
- ✅ 감시 로그 쿼리 응답 타입 정의
- ✅ 혈통 추적 응답 타입 정의
- ✅ 컴포넌트 계층 구조 설계 (Metadata Panel, Lineage Graph, Audit Log Viewer)

### Prep 2: React 컴포넌트 설계 및 상태 관리
- ✅ MetadataPanel 컴포넌트 설계 (읽기 전용)
- ✅ LineageVisualization 컴포넌트 설계 (Cytoscape.js 기반)
- ✅ AuditLogViewer 컴포넌트 설계 (테이블 + 필터)
- ✅ Context API 상태 관리 구조 설계
- ✅ React Query 캐싱 전략 정의

---

## 📊 설계 검증 결과

| 항목 | 목표 | 달성 |
|------|------|------|
| TypeScript 타입 | 5개 주요 API 응답 | ✅ [실제 정의된 타입 개수]개 정의 |
| React 컴포넌트 | 3개 핵심 컴포넌트 | ✅ 설계 완료 |
| 상태 관리 | Context API + Query | ✅ 구조 설계 |
| 시각화 라이브러리 | Cytoscape.js 혈통 그래프 | ✅ 통합 계획 |
| API 통합 준비도 | 100% | ✅ 타입 안전성 보장 |

---

## 📈 주요 성과

**타입 정의**:
- EntityMetadata 인터페이스 작성 ([실제 필드 개수]개 필드)
- LineageInfo 인터페이스 (상하위 추적 지원)
- AuditLog 인터페이스 (감시 기록)
- DataQualityReport 인터페이스 (품질 지표)
- PropertyChange 인터페이스 (변경 추적)

**컴포넌트 설계**:
- MetadataPanel: 읽기 전용 메타데이터 표시
- LineageVisualization: 그래프 시각화 (노드/엣지)
- AuditLogViewer: 필터링 + 페이지네이션
- DataQualityBadge: 품질 점수 시각화
- VersionHistory: 버전 롤백 UI

**상태 관리**:
- MetadataContext로 중앙 상태 관리
- React Query로 서버 데이터 캐싱
- 낙관적 업데이트 전략

---

## 🔧 생성된 문서/코드

### 생성된 파일
- `src/frontend/types/metadata.ts` - TypeScript 인터페이스 모음
- `src/frontend/types/lineage.ts` - 혈통 관련 타입
- `src/frontend/types/audit.ts` - 감시 로그 타입
- `src/frontend/components/metadata/MetadataPanel.tsx` - 컴포넌트 스켈레톤
- `src/frontend/components/lineage/LineageVisualization.tsx` - 그래프 시각화 스켈레톤
- `src/frontend/components/audit/AuditLogViewer.tsx` - 감시 로그 테이블 스켈레톤
- `src/frontend/context/MetadataContext.tsx` - 상태 관리 Context
- `src/frontend/hooks/useMetadata.ts` - React Query 훅

---

## ⏭️ 다음 단계

### 즉시 필요 (Week 3.5)
- [ ] MetadataPanel 컴포넌트 구현 (읽기 전용 모드)
- [ ] LineageVisualization Cytoscape.js 통합
- [ ] AuditLogViewer 필터링 로직 구현

### Week 4 준비
- [ ] SPARQL 쿼리 결과 시각화 컴포넌트
- [ ] RDF 그래프 렌더링 (D3.js 또는 Cytoscape 확장)
- [ ] 온톨로지 임포트 UI 구현

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_3_Metadata/Codex.md`
- API 스펙: `ont_platform/v4/ARCHITECTURE.md` (API 엔드포인트 섹션)
- 성능 기준선: `ont_platform/v4/PHASE4_POSTGRESQL_BASELINE.md` (응답 시간 목표)

---

**보고자**: Codex (프론트엔드)  
**완료 시각**: [실제 완료 시각] KST
```

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/codex/YYYYMMDD_PHASE4_WEEK3_Codex_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260818_1530_PHASE4_WEEK3_Codex_Complete.md`
   - ❌ 금지: `ont_platform/v3/`, `ont_platform/v4/`, 또는 다른 위치에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Prep 1-2" 섹션의 체크마크(✅) → 실제 완료 항목만 표시
   - "설계 검증 결과" 테이블 → 실제 작업한 타입/컴포넌트 개수로 갱신
   - "생성된 파일" → 실제로 생성된 파일 경로 입력
