# Phase 4 Week 1-2: OntologyStyle + DomainSchema
## Codex (Frontend) 수행 지시서

**기간**: 2026-07-21 ~ 2026-08-04 (2주)  
**할당**: 10% (주당 3-5시간)  
**목표**: OntologyExplorer UI/UX 설계, 라이브러리 선택

---

## 준비 작업 1: OntologyExplorer 컴포넌트 설계

**기간**: 07-21 ~ 07-31 (1주)  
**목표**: 온톨로지 브라우저의 완전한 UI/UX 설계

### 산출물 1: 와이어프레임

```
designs/OntologyExplorer_Wireframes.md 작성:

1. 전체 레이아웃
   ┌─────────────────────────────────────────┐
   │ Header (검색, 필터 초기화)               │
   ├──────────┬─────────────────┬────────────┤
   │          │                 │            │
   │ Filter   │  Graph/Tree     │ Metadata   │
   │ Panel    │  Visualization  │ Panel      │
   │ (좌측)   │   (중앙, 주요)   │ (우측)     │
   │          │                 │            │
   └──────────┴─────────────────┴────────────┘
   
2. 4가지 시각화 모드
   a) RDF Triple 모드
      - 삼중쌍 테이블 뷰
      - Subject - Predicate - Object 열
      - 우측 메타데이터 패널
      
   b) Tree (계층) 모드
      - 좌측에 접기/펼치기 트리
      - 각 노드에 아이콘 + 라벨
      - 선택된 노드 상세 우측에 표시
      
   c) Graph (네트워크) 모드
      - 중앙 Cytoscape/D3 그래프
      - 노드 선택 시 강조
      - 줌/팬 컨트롤
      
   d) List (테이블) 모드
      - 엔티티 목록 (정렬/필터 가능)
      - 행 선택 시 관계 표시

3. 우측 메타데이터 패널
   - Entity Info (이름, 타입, 생성자)
   - Version Selector (드롭다운)
   - Audit Log (최근 5개)
   - Lineage Preview (축소 그래프)
```

### 산출물 2: 상호작용 명세

```markdown
# OntologyExplorer 상호작용 패턴

## 1. 노드 선택
- 노드 클릭 → 강조 + 우측 메타데이터 표시
- 더블 클릭 → 드릴다운 (하위 관계 표시)

## 2. 필터링
- 필터 패널에서 "Entity Type" 선택
- 그래프 업데이트 (500ms 애니메이션)
- 필터 선택 유지

## 3. 검색
- 검색바에 텍스트 입력
- 자동완성 목록 표시
- 엔터 → 노드 강조 + 중앙으로 스크롤

## 4. 줌/팬
- 마우스 휠 → 줌 인/아웃
- 드래그 → 팬 (평행 이동)
- 더블 클릭 → 리셋

## 5. 버전 비교
- 우측 "Version" 드롭다운에서 v1.0 → v1.1 선택
- 변경된 필드 강조
- 비교 모드 토글 가능

## 6. 혈통 추적
- Lineage 버튼 클릭
- 데이터 소스부터 현재까지 경로 표시
- 각 변환 단계 클릭 가능
```

### 예상 시간: 3-4일

**체크리스트**:
- [ ] 4가지 시각화 모드 와이어프레임
- [ ] 상호작용 명세 문서화
- [ ] 색상/스타일 가이드 정의
- [ ] Figma/Excalidraw 프로토타입 (선택)

---

## 준비 작업 2: 라이브러리 프로토타입

**기간**: 08-01 ~ 08-11 (1주)  
**목표**: 3가지 그래프 라이브러리 비교 및 선택

### 프로토타입 1: Cytoscape.js

```tsx
// prototypes/CytoscapeExample.tsx

import CytoscopeComponent from 'react-cytoscapejs';

export function CytoscapeExample() {
  const elements = [
    { data: { id: 'a', label: 'Node A' } },
    { data: { id: 'b', label: 'Node B' } },
    { data: { source: 'a', target: 'b', label: 'leads' } }
  ];

  const layout = { name: 'grid' };
  const style = [
    { selector: 'node', style: { content: 'data(label)' } },
    { selector: 'edge', style: { 'target-arrow-shape': 'triangle' } }
  ];

  return (
    <CytoscopeComponent
      elements={elements}
      style={{ width: '800px', height: '600px' }}
      layout={layout}
      stylesheet={style}
    />
  );
}
```

**평가 포인트**:
- ✓ Property Graph 시각화 (Property Graph 스타일)
- ✓ 성능 (1000+ 노드 테스트)
- ✓ 상호작용 (선택, 드래그, 줌)
- ✗ 계층 구조 표현 (약함)

### 프로토타입 2: D3.js (계층 구조)

```tsx
// prototypes/D3HierarchyExample.tsx

import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export function D3HierarchyExample() {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const data = {
      name: "root",
      children: [
        { name: "child1", children: [{ name: "grandchild1" }] },
        { name: "child2" }
      ]
    };

    const hierarchy = d3.hierarchy(data);
    const treeLayout = d3.tree().size([800, 600]);
    treeLayout(hierarchy);

    // 노드와 링크 렌더링
    const svg = d3.select(svgRef.current);
    // ... D3 마크업 생성
  }, []);

  return <svg ref={svgRef} />;
}
```

**평가 포인트**:
- ✓ 계층 구조 시각화 (Hierarchical 스타일)
- ✓ 사용자 정의 가능
- ✗ 성능 (큰 그래프에서 느림)
- ✗ 상호작용 (직접 구현 필요)

### 프로토타입 3: Force-Graph

```tsx
// prototypes/ForceGraphExample.tsx

import ForceGraph3D from 'react-force-graph-3d';

export function ForceGraphExample() {
  const data = {
    nodes: [
      { id: 'node1', name: 'Node 1' },
      { id: 'node2', name: 'Node 2' }
    ],
    links: [
      { source: 'node1', target: 'node2' }
    ]
  };

  return (
    <ForceGraph3D
      graphData={data}
      nodeAutoColorBy="group"
      nodeLabel="name"
      width={800}
      height={600}
    />
  );
}
```

**평가 포인트**:
- ✓ 3D 시각화 (매력적)
- ✓ 성능 (중간 규모)
- ✓ 상호작용 (내장)
- ✗ 복잡도 (높음)

### 예상 시간: 3-4일

**테스트 결과 보고서 작성**:
- [ ] Cytoscape 테스트 완료
- [ ] D3 프로토타입 완료
- [ ] Force-Graph 프로토타입 완료
- [ ] 3가지 비교 분석 (LIBRARY_COMPARISON.md)
- [ ] 최종 선택 결정

---

## 준비 작업 3: Backend API 분석

**기간**: 08-12 ~ 08-18 (1주)  
**목표**: Claude가 구현할 API 명세 이해 및 요구사항 정의

### 필요 API 목록

```markdown
# OntologyExplorer가 필요로 하는 API

## 1. Schema 조회
GET /api/domains/{domain_id}/schema
- Response: DomainSchema 객체 전체
- 캐싱: Redis (1시간)
- 사용 시점: 초기 로드, 스타일 전환

## 2. Entities 조회
GET /api/domains/{domain_id}/entities?type=PROJECT&limit=100&offset=0
- Query params:
  - type: 엔티티 타입 필터 (선택)
  - limit: 페이지 크기 (기본 100)
  - offset: 페이지네이션
- Response: { total: int, items: [Entity] }
- 사용 시점: 초기 로드, 필터 변경

## 3. Relationships 조회
GET /api/domains/{domain_id}/relationships?from_type=PERSON&to_type=PROJECT
- Query params:
  - from_type, to_type, relation_type
- Response: { total: int, items: [Relationship] }
- 사용 시점: 그래프 렌더링

## 4. Entity 상세
GET /api/entities/{entity_id}
- Response: Entity 객체 + 메타데이터
- 캐싱: LRU (메모리)
- 사용 시점: 노드 클릭 시 우측 패널 표시

## 5. Entity 혈통
GET /api/entities/{entity_id}/lineage
- Response: { chain: [Transformation], source: Entity }
- 사용 시점: Lineage 버튼 클릭

## 6. Entity 버전 목록
GET /api/entities/{entity_id}/versions
- Response: { versions: [EntityVersion], current: int }
- 사용 시점: Version 드롭다운 채우기

## 7. 감사 로그
GET /api/audit-logs?entity_id={entity_id}&limit=10
- Response: { items: [AuditLog] }
- 사용 시점: 우측 메타데이터 패널, 감사 로그 탭

## 8. 검색 (자동완성)
GET /api/search?domain_id=...&q=name&type=PERSON
- Response: { suggestions: [{ id, label, type }] }
- 사용 시점: 검색바 입력 시
```

### API 응답 형식 정의

```typescript
// types/api.ts

interface Entity {
  id: string;
  type: string;
  properties: Record<string, any>;
  created_by: string;
  created_at: string;  // ISO 8601
  version: number;
}

interface Relationship {
  id: string;
  from_id: string;
  to_id: string;
  type: string;
  properties?: Record<string, any>;
}

interface EntityVersion {
  version: number;
  data: Entity;
  changed_fields: string[];
  changed_by: string;
  changed_at: string;
}

interface AuditLog {
  id: string;
  entity_id: string;
  action: string;  // "create", "update", "delete"
  old_value?: Record<string, any>;
  new_value?: Record<string, any>;
  performed_by: string;
  performed_at: string;
}

interface LineageInfo {
  chain: Array<{
    operation: string;  // "merge", "split", "enrich"
    performed_by: string;
    performed_at: string;
    input_ids: string[];
    output_id: string;
  }>;
  source: Entity;
}
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] API 명세 문서화 (API_INTEGRATION_PLAN.md)
- [ ] 응답 형식 TypeScript 타입 정의
- [ ] Mock API 데이터 생성 (프로토타입용)
- [ ] Claude와 API 설계 리뷰

---

## 📋 일일 진행 계획

### 07-21 (월) ~ 07-23 (수)
- [ ] 와이어프레임 작성 (4가지 모드)
- [ ] 상호작용 명세 정의
- [ ] 색상/스타일 가이드

### 07-24 (목) ~ 07-31 (목)
- [ ] Cytoscape 프로토타입
- [ ] D3 프로토타입
- [ ] Force-Graph 프로토타입
- [ ] 3가지 비교 분석

### 08-01 (금) ~ 08-04 (월)
- [ ] API 명세 분석 + 문서화
- [ ] TypeScript 타입 정의
- [ ] Mock API 데이터
- [ ] Claude와 리뷰

---

## 🎯 성공 기준

✅ 4가지 시각화 모드 와이어프레임 완성  
✅ 3가지 라이브러리 프로토타입 완성  
✅ 최종 라이브러리 선택 결정 (권장: Cytoscape)  
✅ API 명세 완전히 이해  
✅ Week 5-8 구현 준비 완료

---

## 📞 상호작용

**Claude와의 연계**:
- Task 1-4 샘플 스키마 완료 후 API 설계 리뷰
- 엔티티 구조 설명 요청 (필요시)

**Antigravity와의 협력**:
- 프로토타입 성능 측정 (선택)

---

**상태**: 설계 및 프로토타입 단계  
**예상 완료**: 2026-08-18  
**다음 단계**: Week 5-8 OntologyExplorer 구현 (09-02)
