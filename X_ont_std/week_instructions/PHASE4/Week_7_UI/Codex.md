# Phase 4 Week 7: 온톨로지 확장 UI & 그래프 탐색
## Codex (Frontend) 수행 지시서

**기간**: 2026-07-08 ~ 2026-07-12 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 온톨로지 확장 UI 고도화 - 그래프 탐색, 매핑 URI 비교, Import Preview

---

## 개요

Week 6에서 구축한 온톨로지 확장 기능을 바탕으로 **최종 사용 가능한 온톨로지 확장 모델을 갖춘 깔끔한 UI와 UX를 구현**합니다.

### Week 7의 3가지 핵심 기능

1. **RDF 그래프 탐색 UI** (Task 7-1): 그래프를 시각화하고 Expand on Click으로 1-hop/2-hop 탐색 구현
2. **매핑 URI 비교 대시보드** (Task 7-2): 자동 추천된 온톨로지 개념 간 비교, 속성 시각화 (owl:sameAs, skos:exactMatch 등)
3. **Import Preview & Diff** (Task 7-3): RDF 임포트 전 변경 사항 미리보기, 자동 매핑 후보 제시

---

## 환경 설정 (필수)

```bash
# Conda 환경 활성화
conda activate claud_fe

# 작업 디렉토리
cd E:\ontology_edu\X_ont_std\ont_platform\v4\frontend

# 의존성 설치
npm install

# 개발 서버 (포트 3001)
npm run dev

# 스타일 린트 + 타입 체크
npm run lint
npm run build

# E2E 테스트 (Cypress)
npm run cypress:run
```

**중요**: 
- ✅ 포트 3001 (3002 아님)
- ✅ npm run dev (npm start 아님)
- ✅ Tailwind CSS 전용 (antd 미사용)
- ✅ API 호출: `api.get()`, `api.post()` (useApi 후크 미사용)
- ✅ 모든 체크박스: [ ] (미완료)

---

## Task 7-1: RDF 그래프 탐색 UI (Interactive Graph Viewer)

**기간**: 07-08 ~ 07-09 (1.5일)

### 목표

RDF 그래프를 시각화하고 Expand on Click으로 동적 탐색

### 구현 항목

#### 1) 그래프 시각화 컴포넌트

```tsx
// src/components/GraphViewer.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';

interface Node {
  id: string;
  label: string;
  type: string;
}

interface Edge {
  source: string;
  target: string;
  label: string;
  direction: 'incoming' | 'outgoing';
}

export const GraphViewer: React.FC<{ rootUri: string }> = ({ rootUri }) => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // 초기 로드
  useEffect(() => {
    loadNeighborhood(rootUri);
  }, [rootUri]);

  const loadNeighborhood = async (uri: string) => {
    setLoading(true);
    try {
      const response = await api.get(
        `/api/rdf/neighborhood/${encodeURIComponent(uri)}`
      );
      
      setNodes(response.nodes);
      setEdges(response.edges);
      
      // 캔버스에 그리기
      if (canvasRef.current) {
        drawGraph(response.nodes, response.edges);
      }
    } finally {
      setLoading(false);
    }
  };

  const drawGraph = (nodes: Node[], edges: Edge[]) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 간단한 레이아웃: 중심 노드 + 원형 배치
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 150;

    const positions: Record<string, { x: number; y: number }> = {};
    positions[rootUri] = { x: centerX, y: centerY };

    nodes.forEach((node, idx) => {
      if (node.id !== rootUri) {
        const angle = (idx / nodes.length) * Math.PI * 2;
        positions[node.id] = {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        };
      }
    });

    // 엣지 그리기
    ctx.strokeStyle = '#999';
    ctx.lineWidth = 1;
    edges.forEach((edge) => {
      const from = positions[edge.source];
      const to = positions[edge.target];
      if (from && to) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
      }
    });

    // 노드 그리기
    nodes.forEach((node) => {
      const pos = positions[node.id];
      if (!pos) return;

      ctx.fillStyle = node.id === rootUri ? '#3b82f6' : '#e5e7eb';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 20, 0, Math.PI * 2);
      ctx.fill();

      // 라벨
      ctx.fillStyle = '#000';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const label = node.label.substring(0, 8);
      ctx.fillText(label, pos.x, pos.y);
    });
  };

  const handleNodeClick = (nodeId: string) => {
    if (nodeId !== rootUri) {
      loadNeighborhood(nodeId);
    }
  };

  return (
    <div className="w-full h-screen flex flex-col">
      <div className="p-4 bg-gray-100 border-b">
        <h2 className="text-lg font-bold">{rootUri}</h2>
        <p className="text-sm text-gray-600">Nodes: {nodes.length} | Edges: {edges.length}</p>
      </div>
      
      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        onClick={(e) => {
          const rect = canvasRef.current?.getBoundingClientRect();
          if (rect) {
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            // 클릭한 노드 찾기
            const clicked = nodes.find(n => {
              const pos = { x: 0, y: 0 }; // 실제로는 positions에서 찾아야 함
              return Math.hypot(x - pos.x, y - pos.y) < 20;
            });
            if (clicked) handleNodeClick(clicked.id);
          }
        }}
        className="flex-1 border cursor-pointer bg-white"
      />
      
      {loading && <p className="p-4 text-center">로딩 중...</p>}
    </div>
  );
};
```

#### 2) 통합 대시보드

```tsx
// src/app/page.tsx
'use client';

import React, { useState } from 'react';
import { GraphViewer } from '@/components/GraphViewer';

export default function Home() {
  const [selectedUri, setSelectedUri] = useState(
    'http://example.org/ontology/Concept'
  );

  return (
    <div className="flex h-screen">
      {/* 사이드바 */}
      <div className="w-64 bg-gray-50 border-r p-4">
        <h1 className="text-2xl font-bold mb-4">온톨로지 탐색</h1>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">URI 입력</label>
          <input
            type="text"
            value={selectedUri}
            onChange={(e) => setSelectedUri(e.target.value)}
            placeholder="http://example.org/..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={() => {}}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 mb-4"
        >
          탐색
        </button>

        {/* 탐색 히스토리 */}
        <div className="text-sm">
          <p className="font-semibold mb-2">최근 탐색</p>
          <ul className="space-y-1">
            <li className="text-blue-600 cursor-pointer hover:underline">
              Concept #1
            </li>
          </ul>
        </div>
      </div>

      {/* 그래프 뷰 */}
      <div className="flex-1">
        <GraphViewer rootUri={selectedUri} />
      </div>
    </div>
  );
}
```

### 성공 기준 (Task 7-1)
- [ ] 그래프 시각화: Canvas 또는 SVG로 노드/엣지 렌더링
- [ ] Expand on Click: 노드 클릭 시 이웃 동적 로드
- [ ] 레이아웃: 중심 노드 기준 원형/계층적 배치
- [ ] 성능: < 500ms 로드 (100개 노드)

---

## Task 7-2: 매핑 URI 비교 대시보드

**기간**: 07-09 ~ 07-11 (1.5일)

### 목표

외부 URI와 내부 URI를 비교하여 매핑 가능성 평가

### 구현 항목

```tsx
// src/components/MappingComparisonPanel.tsx
'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';

interface ComparisonResult {
  externalUri: string;
  internalUri: string;
  similarity: number;
  properties: Array<{
    name: string;
    externalValue: string;
    internalValue: string;
    match: boolean;
  }>;
}

export const MappingComparisonPanel: React.FC = () => {
  const [externalUri, setExternalUri] = useState('');
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/ontology/mapping-candidates', {
        params: { externalUri, limit: 5 }
      });

      if (response.candidates.length > 0) {
        const best = response.candidates[0];
        setComparison({
          externalUri,
          internalUri: best.internalUri,
          similarity: best.similarity,
          properties: [
            {
              name: 'Label',
              externalValue: 'External Label',
              internalValue: 'Internal Label',
              match: best.similarity > 0.8
            }
          ]
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMapping = async () => {
    if (!comparison) return;
    
    await api.post('/api/ontology/mappings', {
      externalUri: comparison.externalUri,
      internalUri: comparison.internalUri,
      relationshipType: 'skos:exactMatch',
      confidence: comparison.similarity
    });

    alert('매핑 생성됨!');
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">매핑 비교</h2>

      {/* 입력 */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">외부 URI</label>
        <input
          type="text"
          value={externalUri}
          onChange={(e) => setExternalUri(e.target.value)}
          placeholder="http://example.org/..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '검색 중...' : '검색'}
        </button>
      </div>

      {/* 비교 결과 */}
      {comparison && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm font-medium text-gray-600">유사도</p>
              <div className="w-64 h-2 bg-gray-300 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{ width: `${comparison.similarity * 100}%` }}
                />
              </div>
            </div>
            <span className="text-lg font-bold">
              {(comparison.similarity * 100).toFixed(1)}%
            </span>
          </div>

          {/* 속성 비교 */}
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="text-left py-2">속성</th>
                <th className="text-left py-2">외부 URI</th>
                <th className="text-left py-2">내부 URI</th>
                <th className="text-center py-2">일치</th>
              </tr>
            </thead>
            <tbody>
              {comparison.properties.map((prop) => (
                <tr key={prop.name} className="border-b">
                  <td className="py-2">{prop.name}</td>
                  <td className="py-2">{prop.externalValue}</td>
                  <td className="py-2">{prop.internalValue}</td>
                  <td className="text-center py-2">
                    {prop.match ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-red-600">✗</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* 액션 */}
          <button
            onClick={handleCreateMapping}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            이 매핑 승인
          </button>
        </div>
      )}
    </div>
  );
};
```

### 성공 기준 (Task 7-2)
- [ ] URI 입력: 자동 완성 또는 검색
- [ ] 후보 추천: 상위 5개 표시
- [ ] 유사도 시각화: 진행 바로 표시
- [ ] 속성 비교: 일치/불일치 표시

---

## Task 7-3: Import Preview & Diff

**기간**: 07-11 ~ 07-12 (1.5일)

### 목표

RDF 파일 임포트 전 변경 사항 미리보기

### 구현 항목

```tsx
// src/components/ImportPreviewDialog.tsx
'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';

export const ImportPreviewDialog: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.post('/api/ontology/import/preview', formData);
      setPreview(response);
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    await api.post('/api/ontology/import', formData);
    alert('임포트 완료!');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full p-6">
        <h2 className="text-2xl font-bold mb-4">RDF 임포트</h2>

        {/* 파일 선택 */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">RDF 파일 선택</label>
          <input
            type="file"
            accept=".rdf,.ttl,.nt,.xml"
            onChange={handleFileSelect}
            className="block w-full text-sm text-gray-500 file:px-4 file:py-2 file:bg-blue-600 file:text-white file:rounded-md file:cursor-pointer"
          />
        </div>

        {/* 미리보기 */}
        {preview && (
          <div className="space-y-4 p-4 bg-gray-50 rounded-lg mb-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  새 Triple
                </p>
                <p className="text-lg font-bold">{preview.newTripleCount}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">
                  새 엔티티
                </p>
                <p className="text-lg font-bold">{preview.newEntityCount}</p>
              </div>
            </div>

            {/* 충돌 경고 */}
            {preview.potentialConflicts && preview.potentialConflicts.length > 0 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
                <h3 className="font-semibold text-yellow-800 mb-2">
                  잠재적 충돌 ({preview.potentialConflicts.length})
                </h3>
                <ul className="space-y-1 text-sm">
                  {preview.potentialConflicts.slice(0, 5).map((conflict: any, idx: number) => (
                    <li key={idx} className="text-yellow-700">
                      {conflict.conflictType}: {conflict.severity}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 추천 매핑 */}
            {preview.suggestedMappings && preview.suggestedMappings.length > 0 && (
              <div>
                <h3 className="font-semibold mb-2">
                  추천 매핑 ({preview.suggestedMappings.length})
                </h3>
                <div className="space-y-2">
                  {preview.suggestedMappings.slice(0, 3).map((mapping: any, idx: number) => (
                    <div key={idx} className="p-2 bg-white border rounded text-sm">
                      <input type="checkbox" defaultChecked className="mr-2" />
                      <span>{mapping.externalUri} → {mapping.internalUri}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 액션 */}
        <div className="flex gap-2 justify-end">
          <button className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
            취소
          </button>
          <button
            onClick={handleImport}
            disabled={!preview || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '처리 중...' : '임포트'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

### 성공 기준 (Task 7-3)
- [ ] 파일 업로드: Turtle/N-Triples/RDF/XML 지원
- [ ] 미리보기: 새 엔티티 및 Triple 개수 표시
- [ ] 충돌 감지: 잠재적 문제 경고
- [ ] 매핑 제안: 자동 추천 매핑 제시

---

## 환경 일관성 체크

- ✅ 포트: 3001 (npm run dev)
- ✅ npm 명령: build, lint, cypress:run
- ✅ UI: Tailwind CSS (antd 제거)
- ✅ API: api.get() / api.post() (useApi 제거)
- ✅ 컴포넌트: src/components/
- ✅ 체크박스: [ ] (모두 미완료)

---

**다음 단계**: Week 7 Antigravity (성능 최적화)
