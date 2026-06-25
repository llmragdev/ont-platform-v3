# Phase 5 Week 10: OWL 추론 결과 시각화 (프론트엔드)
## Codex (Frontend) 수행 지시서

**기간**: 2026-07-29 ~ 2026-08-02 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 추론된 관계 시각화 및 신뢰도 필터링

---

## 개요

Claude 팀의 OWL 추론 엔진이 도출한 새로운 개념 관계(inferred relationships)를 사용자에게 시각적으로 제시하고, 신뢰도 기반으로 필터링할 수 있는 UI를 구현합니다.

### Week 10의 3가지 핵심 기능

1. **추론 관계 시각화** (Task 10-1): Explicit vs Inferred 관계를 구분하여 표시
2. **신뢰도 필터링** (Task 10-2): 신뢰도 임계값으로 추론 결과 필터링
3. **추론 근거 표시** (Task 10-3): 어떤 규칙으로 도출됐는지 설명

---

## 🔧 환경 설정

```bash
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v4\frontend
npm install
npm run dev  # 포트 3001
npm run build  # 빌드 검증
npm run lint   # 타입/스타일 검증
npm run cypress:run  # e2e 테스트 (선택)
```

---

## Task 10-1: 추론 관계 시각화

**기간**: 07-29 ~ 07-30 (1.5일)

### 구현 항목

```typescript
// src/components/InferredRelationshipViewer.tsx
import React, { useState, useEffect } from 'react';
import { Cytoscape } from '@react-cytoscape/cytoscape';

interface InferredRelationship {
  id: string;
  subject: string;
  subjectLabel: string;
  predicate: string;
  object: string;
  objectLabel: string;
  confidence: number;  // 0.0 ~ 1.0
  inferenceChain: string[];
  evidence: string[];
  isExplicit: boolean;  // 명시적 vs 추론된
}

export const InferredRelationshipViewer: React.FC<{
  conceptUri: string;
}> = ({ conceptUri }) => {
  const [relationships, setRelationships] = useState<InferredRelationship[]>([]);
  const [graphMode, setGraphMode] = useState<'all' | 'explicit' | 'inferred'>('all');
  const [minConfidence, setMinConfidence] = useState(0.5);

  useEffect(() => {
    loadInferredRelationships();
  }, [conceptUri]);

  const loadInferredRelationships = async () => {
    const response = await fetch(
      `/api/ontology/inferred-relationships/${conceptUri}?minConfidence=${minConfidence}`
    );
    const data = await response.json();
    setRelationships(data.relationships);
  };

  // 필터링
  const filteredRelationships = relationships.filter(r => {
    if (graphMode === 'explicit') return r.isExplicit;
    if (graphMode === 'inferred') return !r.isExplicit;
    return true;
  });

  // 그래프 데이터 변환
  const graphData = {
    nodes: extractNodes(filteredRelationships, conceptUri),
    edges: extractEdges(filteredRelationships)
  };

  // Tailwind 기반 렌더링: antd 대신 자체 UI 패턴 사용
  return (
    <div className="inferred-relationship-viewer p-4">
      {/* 필터 버튼 */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setGraphMode('all')}
          className={`px-4 py-2 rounded ${graphMode === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          전체 ({relationships.length})
        </button>
        <button
          onClick={() => setGraphMode('explicit')}
          className={`px-4 py-2 rounded ${graphMode === 'explicit' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          명시적 ({relationships.filter(r => r.isExplicit).length})
        </button>
        <button
          onClick={() => setGraphMode('inferred')}
          className={`px-4 py-2 rounded ${graphMode === 'inferred' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          추론됨 ({relationships.filter(r => !r.isExplicit).length})
        </button>
      </div>

      {/* 그래프 시각화 */}
      <div className="h-96 mb-6 border border-gray-300 rounded">
        <Cytoscape
          elements={graphData.nodes.concat(graphData.edges)}
          style={{ width: '100%', height: '100%' }}
          layout={{ name: 'cose' }}
        />
      </div>

      {/* 테이블 (자체 구현) */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse border border-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="border border-gray-300 px-4 py-2 text-left">관계</th>
              <th className="border border-gray-300 px-4 py-2 text-left">대상</th>
              <th className="border border-gray-300 px-4 py-2 text-left">신뢰도</th>
              <th className="border border-gray-300 px-4 py-2 text-left">타입</th>
              <th className="border border-gray-300 px-4 py-2 text-left">근거</th>
            </tr>
          </thead>
          <tbody>
            {filteredRelationships.map((rel) => (
              <tr key={rel.id}>
                <td className="border border-gray-300 px-4 py-2">
                  <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                    {rel.predicate}
                  </span>
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <div>{rel.objectLabel}</div>
                  <code className="text-xs text-gray-600">{rel.object}</code>
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-2 bg-gray-300 rounded overflow-hidden">
                      <div
                        className={`h-full ${
                          rel.confidence > 0.8 ? 'bg-green-500' : 
                          rel.confidence > 0.5 ? 'bg-yellow-500' : 
                          'bg-red-500'
                        }`}
                        style={{ width: `${rel.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-sm">{(rel.confidence * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <span className={`inline-block px-2 py-1 rounded text-xs ${
                    rel.isExplicit ? 'bg-blue-100 text-blue-800' : 'bg-cyan-100 text-cyan-800'
                  }`}>
                    {rel.isExplicit ? '명시적' : '추론됨'}
                  </span>
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <span className="text-sm">{rel.inferenceChain.length > 0 ? `${rel.inferenceChain.length} 단계` : '직접'}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

function extractNodes(relationships: InferredRelationship[], centerUri: string) {
  const nodes = new Set([centerUri]);
  relationships.forEach(r => {
    nodes.add(r.object);
  });

  return Array.from(nodes).map(uri => ({
    data: { id: uri, label: uri.split('/').pop() }
  }));
}

function extractEdges(relationships: InferredRelationship[]) {
  return relationships.map(r => ({
    data: {
      source: r.subject,
      target: r.object,
      label: r.predicate,
      confidence: r.confidence,
      isExplicit: r.isExplicit
    }
  }));
}
```

### 성공 기준 (Task 10-1)
- [ ] 추론 관계 테이블: 명시적/추론됨 구분
- [ ] 그래프 시각화: Cytoscape로 관계 네트워크 표시
- [ ] 신뢰도 색상: 신뢰도에 따른 색상 구분
- [ ] 근거 표시: 추론 체인 길이 표시

---

## Task 10-2: 신뢰도 기반 필터링

**기간**: 07-30 ~ 07-31 (1.5일)

### 구현 항목

```typescript
// src/components/ConfidenceFilterPanel.tsx
export const ConfidenceFilterPanel: React.FC<{
  onFilterChange: (minConfidence: number) => void;
}> = ({ onFilterChange }) => {
  const [confidence, setConfidence] = useState(0.5);

  return (
    <div className="p-4 bg-gray-100 rounded">
      <h3 className="font-bold mb-4">신뢰도 필터</h3>
      
      <div className="flex items-center gap-4">
        <span>최소 신뢰도:</span>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={confidence}
          onChange={(e) => {
            const val = parseFloat(e.target.value);
            setConfidence(val);
            onFilterChange(val);
          }}
          className="w-48"
        />
        <span className="font-bold">
          {(confidence * 100).toFixed(0)}%
        </span>
      </div>

      <div className="mt-2 text-xs text-gray-600">
        신뢰도 {(confidence * 100).toFixed(0)}% 이상의 추론만 표시
      </div>
    </div>
  );
};
```

### 성공 기준 (Task 10-2)
- [ ] 슬라이더 필터: 신뢰도 임계값 설정
- [ ] 실시간 필터링: 결과 즉시 업데이트
- [ ] 필터링 통계: 필터링 전/후 개수 표시

---

## Task 10-3: 추론 근거 및 설명

**기간**: 07-31 ~ 08-02 (2일)

### 구현 항목

```typescript
// src/components/InferenceExplanation.tsx
export const InferenceExplanation: React.FC<{
  relationship: InferredRelationship;
}> = ({ relationship }) => {
  const [expanded, setExpanded] = useState(false);

  const explanationMap = {
    'rdfs_subclass_transitivity': '상위 클래스의 상위 클래스 관계',
    'owl_sameas_symmetry': '동일 개념의 역방향 관계',
    'owl_sameas_transitivity': '동일 개념을 통한 추이적 관계',
    'rdfs_domain_range': '속성의 정의역/치역 규칙',
    'skos_hierarchical': '개념 계층 구조의 추이성'
  };

  return (
    <div className="p-3 bg-gray-50 border-l-4 border-blue-600 rounded mb-2">
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <strong>{relationship.subjectLabel}</strong>
          <span className="mx-2">→</span>
          <strong>{relationship.objectLabel}</strong>
        </div>
        <span>{expanded ? '▼' : '▶'}</span>
      </div>

      {expanded && (
        <div className="mt-3">
          <div className="mb-2">
            <strong>추론 규칙:</strong>
            {relationship.inferenceChain.length === 0 ? (
              <span> 명시적 관계 (추론 없음)</span>
            ) : (
              <div className="pl-4 mt-2">
                {relationship.inferenceChain.map((rule, idx) => (
                  <div key={idx} className="mb-1 text-xs">
                    <code className="bg-gray-200 px-1 rounded">{rule}</code>
                    <span className="ml-2 text-gray-600">
                      {explanationMap[rule] || rule}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <strong>근거:</strong>
            <ul className="mt-2 pl-4">
              {relationship.evidence.map((e, idx) => (
                <li key={idx} className="text-xs list-disc">
                  {e}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-2">
            <strong>신뢰도:</strong>
            <span className="ml-2 font-bold">
              {(relationship.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
```

### 성공 기준 (Task 10-3)
- [ ] 근거 설명: 추론 규칙 및 증거 제시
- [ ] 확장 UI: 클릭하면 상세 정보 표시
- [ ] 규칙 설명: 각 추론 규칙의 의미 설명

---

## API 요구사항

```
GET /api/ontology/inferred-relationships/{conceptUri}?minConfidence=0.5
Response:
{
  "conceptUri": "...",
  "explicit": 15,
  "inferred": 42,
  "relationships": [...]
}

GET /api/ontology/reasoning-stats
Response:
{
  "inferredTripleCount": 15000,
  "processingTimeMs": 28000,
  "inferenceRules": {...}
}
```

---

**다음 단계**: Week 11 (Streaming & 거버넌스)
