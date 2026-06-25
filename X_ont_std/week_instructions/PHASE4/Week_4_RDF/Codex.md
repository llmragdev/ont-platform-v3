# Phase 4 Week 4: RDF + External Ontology
## Codex (Frontend) 수행 지시서

**기간**: 2026-08-19 ~ 2026-09-01 (2주)  
**할당**: 90% (주당 27-30시간)  
**목표**: RDF 그래프 시각화, SPARQL Workbench UI, 외부 import 인터페이스

---

## Prep 1: RDF 그래프 시각화 라이브러리 선택 및 프로토타입

**기간**: 08-19 ~ 08-25 (1주)  
**목표**: D3.js/Cytoscape 중 선택 및 기본 그래프 렌더링

### 라이브러리 비교

```typescript
// 후보 라이브러리
// 1. D3.js: 완전한 커스터마이징, 가파른 학습곡선
// 2. Cytoscape.js: 그래프 최적화, 노드-엣지 기반
// 3. Vis.js: 간단한 API, 괜찮은 성능
// 4. React Flow: React 최적화, 인터랙티브

// 추천: Cytoscape.js (RDF 트리플 시각화에 최적)
// 설치: npm install cytoscape cytoscape-dagre
```

### RDFGraphViewer 컴포넌트 설계

```typescript
// components/RDFGraphViewer.tsx

import Cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import React, { useEffect, useRef } from 'react';

export interface RDFGraphData {
  nodes: Array<{
    id: string;
    label: string;
    type: 'entity' | 'property' | 'literal';
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string;
  }>;
}

export function RDFGraphViewer({
  entityId: string;
  onNodeClick?: (nodeId: string) => void;
  highlightPath?: string[]; // 경로 강조
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const data = fetchRDFGraph(entityId);
    
    const cy = Cytoscape({
      container: containerRef.current,
      style: [
        {
          selector: 'node[type="entity"]',
          style: {
            'background-color': '#3498db',
            'label': 'data(label)',
            'width': 60,
            'height': 60
          }
        },
        {
          selector: 'node[type="property"]',
          style: {
            'background-color': '#2ecc71',
            'label': 'data(label)',
            'width': 40,
            'height': 40
          }
        },
        {
          selector: 'edge',
          style: {
            'curve-style': 'straight',
            'target-arrow-shape': 'triangle',
            'label': 'data(label)'
          }
        }
      ],
      elements: [
        ...data.nodes.map(n => ({ data: n })),
        ...data.edges.map(e => ({ data: e }))
      ],
      layout: { name: 'dagre' }
    });
    
    // 경로 강조
    if (highlightPath?.length) {
      cy.nodes().forEach(node => {
        if (highlightPath.includes(node.id())) {
          node.style('background-color', '#e74c3c');
        }
      });
    }
    
    cy.on('tap', 'node', (evt) => {
      onNodeClick?.(evt.target.id());
    });
    
  }, [entityId, highlightPath]);
  
  return <div ref={containerRef} style={{ width: '100%', height: '500px' }} />;
}
```

### 와이어프레임: RDF 그래프 시각화 패널

```
┌─────────────────────────────────────────────────┐
│ RDF Graph Viewer                                │
├─────────────────────────────────────────────────┤
│                                                 │
│      [Entity A] --merge--> [Entity B]           │
│         |                      |                │
│         v                      v                │
│   [Property X]           [Property Y]           │
│         |                      |                │
│         +------ has_value -----+                │
│                                                 │
├─────────────────────────────────────────────────┤
│ Legend:                                         │
│ ● Entity (blue)  ● Property (green)             │
│ ─> Relation      ─• Literal value              │
└─────────────────────────────────────────────────┘
```

### 예상 시간: 3-4일

**체크리스트**:
- [ ] Cytoscape.js 설치 및 기본 세팅
- [ ] RDFGraphViewer 컴포넌트 구현
- [ ] 노드/엣지 스타일 정의
- [ ] Mock RDF 데이터로 레이아웃 검증

---

## Prep 2: SPARQL Workbench UI + 외부 Import 인터페이스

**기간**: 08-26 ~ 09-01 (1주)  
**목표**: SPARQL 쿼리 에디터 및 결과 시각화

### SPARQLWorkbench 컴포넌트 설계

```typescript
// components/SPARQLWorkbench.tsx

export interface SPARQLResult {
  source: 'cache' | 'query';
  data: Array<Record<string, string>>;
  execution_time_ms: number;
}

export function SPARQLWorkbench() {
  const [query, setQuery] = React.useState<string>('');
  const [result, setResult] = React.useState<SPARQLResult | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [useCache, setUseCache] = React.useState(true);
  
  const executeQuery = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/sparql/query', {
        method: 'POST',
        body: JSON.stringify({
          query,
          format: 'json',
          cache: useCache
        })
      });
      setResult(await response.json());
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="sparql-workbench">
      <div className="query-editor">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
          rows={10}
        />
      </div>
      
      <div className="controls">
        <button onClick={executeQuery} disabled={loading}>
          {loading ? 'Executing...' : 'Execute Query'}
        </button>
        <label>
          <input 
            type="checkbox" 
            checked={useCache}
            onChange={(e) => setUseCache(e.target.checked)}
          />
          Use Cache
        </label>
      </div>
      
      {result && (
        <div className="results">
          <div className="metadata">
            Execution time: {result.execution_time_ms}ms (source: {result.source})
          </div>
          <table>
            <thead>
              <tr>
                {Object.keys(result.data[0] || {}).map(col => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.data.map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val, j) => (
                    <td key={j}>{val}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

### OntologyImporter 컴포넌트 설계

```typescript
// components/OntologyImporter.tsx

export interface ImportSource {
  type: 'dbpedia' | 'wikidata' | 'rdf_file';
  identifier: string;  // DBpedia URI, Wikidata ID, 파일 경로
  domainId: string;
}

export function OntologyImporter() {
  const [importType, setImportType] = React.useState<'dbpedia' | 'wikidata' | 'rdf_file'>('dbpedia');
  const [identifier, setIdentifier] = React.useState('');
  const [domainId, setDomainId] = React.useState('');
  const [importProgress, setImportProgress] = React.useState(0);
  
  const handleImport = async () => {
    const endpoint = {
      'dbpedia': '/api/import/dbpedia',
      'wikidata': '/api/import/wikidata',
      'rdf_file': '/api/import/rdf-file'
    }[importType];
    
    const response = await fetch(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        identifier,
        domain_id: domainId
      })
    });
    
    const result = await response.json();
    return result;
  };
  
  return (
    <div className="ontology-importer">
      <div className="import-type-selector">
        <label>
          <input
            type="radio"
            value="dbpedia"
            checked={importType === 'dbpedia'}
            onChange={(e) => setImportType(e.target.value as any)}
          />
          DBpedia Resource
        </label>
        
        <label>
          <input
            type="radio"
            value="wikidata"
            checked={importType === 'wikidata'}
            onChange={(e) => setImportType(e.target.value as any)}
          />
          Wikidata Item
        </label>
        
        <label>
          <input
            type="radio"
            value="rdf_file"
            checked={importType === 'rdf_file'}
            onChange={(e) => setImportType(e.target.value as any)}
          />
          RDF File
        </label>
      </div>
      
      {importType === 'dbpedia' && (
        <input
          type="text"
          placeholder="http://dbpedia.org/resource/Machine_Learning"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
        />
      )}
      
      {importType === 'wikidata' && (
        <input
          type="text"
          placeholder="Q11019"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
        />
      )}
      
      {importType === 'rdf_file' && (
        <input
          type="file"
          accept=".rdf,.ttl,.n3"
          onChange={(e) => setIdentifier(e.target.files?.[0]?.name || '')}
        />
      )}
      
      <select
        value={domainId}
        onChange={(e) => setDomainId(e.target.value)}
      >
        <option>-- Select Domain --</option>
        <option value="ai">AI/ML Domain</option>
        <option value="biology">Biology Domain</option>
      </select>
      
      <button onClick={handleImport}>Import</button>
      
      {importProgress > 0 && (
        <progress value={importProgress} max={100} />
      )}
    </div>
  );
}
```

### LinkedDataViewer 컴포넌트

```typescript
// components/LinkedDataViewer.tsx

export function LinkedDataViewer({
  entityId: string;
}) {
  const [linkedResources, setLinkedResources] = React.useState([]);
  
  useEffect(() => {
    // DESCRIBE 쿼리로 Linked Data 조회
    fetch(`/api/sparql/describe/${entityId}`)
      .then(r => r.json())
      .then(data => setLinkedResources(data));
  }, [entityId]);
  
  return (
    <div className="linked-data-viewer">
      {linkedResources.map(resource => (
        <div key={resource.uri} className="resource-card">
          <h4>{resource.label}</h4>
          <p>{resource.description}</p>
          <div className="source-badges">
            {resource.sources?.map(source => (
              <span key={source} className="badge">{source}</span>
            ))}
          </div>
          <a href={resource.uri} target="_blank">View Source</a>
        </div>
      ))}
    </div>
  );
}
```

### 와이어프레임: SPARQL Workbench

```
┌──────────────────────────────────────────┐
│ SPARQL Workbench                         │
├──────────────────────────────────────────┤
│ Query Editor (Ace Editor)                │
│ ┌────────────────────────────────────┐  │
│ │ SELECT ?s ?p ?o WHERE {            │  │
│ │   ?s ?p ?o .                       │  │
│ │   FILTER (?p = dbpedia:type)      │  │
│ │ } LIMIT 100                        │  │
│ └────────────────────────────────────┘  │
│ [Execute] [Cache ✓] [Format: JSON ▼]   │
├──────────────────────────────────────────┤
│ Results (Execution: 45ms, cached)        │
│ ┌────────────────────────────────────┐  │
│ │ s                  │ p      │ o    │  │
│ ├────────────────────┼────────┼──────┤  │
│ │ dbpedia:ML         │ type   │ ...  │  │
│ │ wikidata:Q123      │ type   │ ...  │  │
│ └────────────────────────────────────┘  │
│ [Export CSV] [Visualize Graph]          │
└──────────────────────────────────────────┘
```

### 와이어프레임: Ontology Importer

```
┌──────────────────────────────────────────┐
│ Import External Ontology                 │
├──────────────────────────────────────────┤
│ ◉ DBpedia ○ Wikidata ○ RDF File         │
│                                          │
│ Resource URI:                            │
│ [http://dbpedia.org/resource/Machine...] │
│                                          │
│ Target Domain: [AI Domain ▼]             │
│                                          │
│ [Import] [Batch Upload]                 │
│                                          │
│ Progress: ████████░░░░░░░░░ 40%         │
│ Status: Importing... (235/500 entities)  │
├──────────────────────────────────────────┤
│ Import History:                          │
│ ✓ dbpedia:MachineLearning (100 props)   │
│ ✓ wikidata:Q11019 (45 claims)           │
│ ✓ ml_ontology.rdf (1200 triples)        │
└──────────────────────────────────────────┘
```

### 예상 시간: 4-5일

**체크리스트**:
- [ ] SPARQLWorkbench 컴포넌트 구현
- [ ] OntologyImporter 컴포넌트 구현
- [ ] LinkedDataViewer 컴포넌트 구현
- [ ] Ace Editor 통합 (쿼리 문법 강조)
- [ ] Mock 데이터로 레이아웃 검증

---

## 📋 일일 진행 계획

### 08-19 (화) ~ 08-25 (월)
- [ ] Cytoscape.js 라이브러리 선택 및 설치
- [ ] RDFGraphViewer 컴포넌트 구현
- [ ] 노드 클릭 상호작용 구현
- [ ] Mock RDF 데이터로 테스트

### 08-26 (화) ~ 09-01 (월)
- [ ] SPARQLWorkbench 컴포넌트 구현
- [ ] Ace Editor 쿼리 문법 강조
- [ ] OntologyImporter 다중 소스 UI
- [ ] LinkedDataViewer 구현
- [ ] Claude와 API 스펙 최종 검증

---

## 🎯 성공 기준

✅ RDFGraphViewer 완성 (노드/엣지 스타일, 상호작용)  
✅ SPARQLWorkbench 완성 (쿼리 에디터, 결과 표시)  
✅ OntologyImporter 완성 (3가지 소스 UI)  
✅ LinkedDataViewer 완성 (외부 리소스 통합 표시)  
✅ 모든 컴포넌트 Mock 데이터로 검증  
✅ Week 5-8 구현 준비 완료

---

## 📞 상호작용

**Claude와의 연계**:
- SPARQL API 스펙 확인 (Task 4-3 완료 후)
- RDF 그래프 데이터 포맷 최종 확인
- Linked Data 응답 포맷 검증

**Antigravity와의 연계**:
- 그래프 렌더링 성능 벤치마크
- 대규모 RDF 데이터 시각화 테스트

---

**상태**: Prep 1-2 준비 완료  
**예상 완료**: 2026-09-01  
**다음 단계**: Week 5-8 컴포넌트 구현 + 통합

---

## 📝 최종 보고서 작성 가이드

**완료 후 다음 형식으로 최종 보고서를 작성하여 제출하세요.**

```markdown
# Phase 4 Week 4: Codex (Frontend - RDF) 완료 보고서

**기간**: 2026-08-19 ~ 2026-09-01 (2주)
**할당**: 90% (주당 27-30시간)
**상태**: ✅ 완료
**날짜**: [실제 보고서 작성 날짜]

---

## 📋 작업 요약

### Prep 1: RDF 그래프 시각화 라이브러리 선택 및 프로토타입
- ✅ D3.js, Cytoscape.js, Vis.js, React Flow 비교 분석
- ✅ Cytoscape.js 선택 및 설치
- ✅ RDFGraphViewer 컴포넌트 설계 완료
- ✅ 노드-엣지 스타일링 및 상호작용 설계
- ✅ Mock RDF 데이터로 프로토타입 검증

### Prep 2: SPARQL Workbench + OntologyImporter + LinkedDataViewer
- ✅ SPARQLWorkbench 컴포넌트 설계 (쿼리 에디터, 결과 표시)
- ✅ Ace Editor 쿼리 문법 강조 통합
- ✅ OntologyImporter UI 설계 (DBpedia, Wikidata, 로컬 RDF)
- ✅ LinkedDataViewer 컴포넌트 설계
- ✅ 전체 컴포넌트 Mock 데이터로 검증

---

## 📊 설계 검증 결과

| 항목 | 목표 | 달성 |
|------|------|------|
| RDF 그래프 라이브러리 선택 | 최적 라이브러리 결정 | ✅ Cytoscape.js 선택 |
| RDFGraphViewer 설계 | 노드/엣지/상호작용 | ✅ 완전 설계 |
| SPARQLWorkbench 설계 | 쿼리 에디터 + 결과 | ✅ 설계 완료 |
| OntologyImporter 설계 | 3가지 소스 UI | ✅ UI 설계 완료 |
| LinkedDataViewer 설계 | 외부 리소스 통합 | ✅ 설계 완료 |
| Mock 데이터 검증 | 모든 컴포넌트 테스트 | ✅ 검증 완료 |

---

## 📈 주요 성과

**그래프 시각화**:
- Cytoscape.js 라이브러리 선택 및 설정
- RDFGraphViewer: 노드 색상/크기별 분류 표시
- 상호작용: 노드 클릭/드래그, 줌/팬 지원
- 대규모 그래프 성능 최적화 (hierarchical 레이아웃)

**SPARQL Workbench**:
- 쿼리 에디터 (Ace Editor 기반, 문법 강조)
- 쿼리 결과 표시 (테이블/그래프)
- 쿼리 히스토리 저장
- 즐겨찾기 쿼리 기능

**OntologyImporter**:
- DBpedia 선택 UI
- Wikidata 자동 완성 검색
- 로컬 RDF 파일 업로드
- 매핑 미리보기

**LinkedDataViewer**:
- 외부 URI 클릭 시 Linked Data 표시
- DBpedia/Wikidata 통합
- 여러 언어 지원 (한글, 영문, 등)

---

## 🔧 생성된 문서/코드

### 생성된 파일
- `src/frontend/components/RDFGraphViewer.tsx` - RDF 그래프 시각화
- `src/frontend/components/SPARQLWorkbench.tsx` - SPARQL 쿼리 에디터
- `src/frontend/components/OntologyImporter.tsx` - 온톨로지 임포트 UI
- `src/frontend/components/LinkedDataViewer.tsx` - Linked Data 뷰어
- `src/frontend/types/rdf.ts` - RDF 관련 TypeScript 타입
- `src/frontend/hooks/useSPARQL.ts` - SPARQL 쿼리 React Hook
- `src/frontend/hooks/useOntologyImport.ts` - 임포트 React Hook

---

## ⏭️ 다음 단계

### 즉시 필요 (Week 4.5)
- [ ] RDFGraphViewer 컴포넌트 구현
- [ ] SPARQLWorkbench 컴포넌트 구현
- [ ] Cytoscape.js 성능 최적화

### Week 5-8 준비
- [ ] 대규모 RDF 데이터 시각화 테스트 (Antigravity와 협력)
- [ ] 그래프 렌더링 캐싱 전략

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_4_RDF/Codex.md`
- RDF 성능 기준선: `ont_platform/v4/PHASE4_RDF_PERFORMANCE_BASELINE.md`

---

**보고자**: Codex (Frontend - RDF)
**완료 시각**: [실제 완료 시각] KST
```

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/codex/YYYYMMDD_PHASE4_WEEK4_Codex_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260901_1830_PHASE4_WEEK4_Codex_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Prep 1-2" 섹션 → 실제 완료 항목만 체크
   - "설계 검증 결과" 테이블 → 실제 결과로 갱신
   - "생성된 파일" → 실제로 생성된 파일 경로 입력
