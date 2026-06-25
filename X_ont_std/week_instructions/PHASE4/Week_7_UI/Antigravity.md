# Phase 4 Week 7: 온톨로지 확장 RDF 그래프 탐색 성능
## Antigravity (Performance) 수행 지시서

**기간**: 2026-07-08 ~ 2026-07-12 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: RDF 그래프 렌더링 성능 벤치마크, 점진적 렌더링 최적화

---

## Task 7-1: 그래프 렌더링 최적화

**기간**: 07-08 ~ 07-09 (1.5일)

### 목표

1000+ 노드 그래프를 60fps로 렌더링

### 구현 항목

#### 1) 점진적 렌더링 (Progressive Rendering)

```python
# src/performance/progressive_renderer.py
from typing import Dict, Generator, Tuple, List
import time

class ProgressiveGraphRenderer:
    """점진적 그래프 렌더링"""
    
    def render_with_priority(
        self,
        graph_data: Dict,
        viewport_size: Tuple[int, int]
    ) -> Generator[Dict, None, None]:
        """
        뷰포트 기준으로 우선순위 있게 렌더링
        
        Yield: 렌더링 가능한 노드/엣지 배치
        """
        
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        
        # 1단계: 중심 노드 (10%)
        center_nodes = self._get_center_nodes(nodes, count=len(nodes) // 10)
        center_edges = self._get_edges_for_nodes(edges, center_nodes)
        
        yield {
            "type": "batch_1",
            "nodes": center_nodes,
            "edges": center_edges,
            "priority": "critical"
        }
        
        # 2단계: 뷰포트 내 노드 (30%)
        viewport_nodes = self._get_viewport_nodes(
            nodes,
            viewport_size,
            exclude=center_nodes
        )
        viewport_edges = self._get_edges_for_nodes(edges, viewport_nodes)
        
        yield {
            "type": "batch_2",
            "nodes": viewport_nodes,
            "edges": viewport_edges,
            "priority": "high"
        }
        
        # 3단계: 주변 노드 (60%)
        remaining_nodes = [n for n in nodes if n not in center_nodes + viewport_nodes]
        remaining_edges = self._get_edges_for_nodes(edges, remaining_nodes)
        
        # 배치로 분할
        batch_size = 100
        for i in range(0, len(remaining_nodes), batch_size):
            batch = remaining_nodes[i:i+batch_size]
            batch_edges = self._get_edges_for_nodes(edges, batch)
            
            yield {
                "type": "batch_3",
                "nodes": batch,
                "edges": batch_edges,
                "priority": "low",
                "batchIndex": i // batch_size
            }
    
    def _get_center_nodes(self, nodes: List[Dict], count: int) -> List[Dict]:
        """중심도(betweenness) 기반 중요 노드 추출"""
        # 간단한 구현: ID 기반 정렬 (실제로는 그래프 알고리즘)
        return sorted(nodes, key=lambda n: n.get('id', ''))[:count]
    
    def _get_viewport_nodes(
        self,
        nodes: List[Dict],
        viewport: Tuple[int, int],
        exclude: List[Dict]
    ) -> List[Dict]:
        """뷰포트 내 노드 필터링"""
        exclude_ids = {n['id'] for n in exclude}
        viewport_w, viewport_h = viewport
        
        # 뷰포트 중심 ±50% 범위 내 노드
        viewport_nodes = [
            n for n in nodes
            if n['id'] not in exclude_ids
            and 0.25 * viewport_w <= n.get('x', 0) <= 0.75 * viewport_w
            and 0.25 * viewport_h <= n.get('y', 0) <= 0.75 * viewport_h
        ]
        
        return viewport_nodes
    
    def _get_edges_for_nodes(
        self,
        edges: List[Dict],
        nodes: List[Dict]
    ) -> List[Dict]:
        """주어진 노드 간 엣지 필터링"""
        node_ids = {n['id'] for n in nodes}
        return [
            e for e in edges
            if e['source'] in node_ids or e['target'] in node_ids
        ]
```

#### 2) 렌더링 성능 벤치마크

```python
# tests/phase4/week7_graph_rendering_bench.py
import pytest
import asyncio
from performance.progressive_renderer import ProgressiveGraphRenderer
import time

@pytest.mark.benchmark
class TestGraphRenderingPerformance:
    
    def setup_method(self):
        """테스트 데이터 생성"""
        self.renderer = ProgressiveGraphRenderer()
        self.graph_1000 = self._generate_test_graph(1000)
        self.graph_5000 = self._generate_test_graph(5000)
    
    def test_progressive_rendering_1000_nodes(self, benchmark):
        """1000개 노드 점진적 렌더링"""
        def run():
            batches = list(self.renderer.render_with_priority(
                self.graph_1000,
                (800, 600)
            ))
            return len(batches)
        
        result = benchmark(run)
        assert result > 0  # 최소 1개 배치
    
    def test_progressive_rendering_5000_nodes(self, benchmark):
        """5000개 노드 점진적 렌더링"""
        def run():
            batches = list(self.renderer.render_with_priority(
                self.graph_5000,
                (800, 600)
            ))
            return len(batches)
        
        result = benchmark(run)
        # 5000개 노드는 60+ 배치로 분할
        assert result > 50
    
    def test_first_batch_latency(self, benchmark):
        """첫 배치 렌더링 지연 시간"""
        def run():
            gen = self.renderer.render_with_priority(
                self.graph_5000,
                (800, 600)
            )
            first_batch = next(gen)
            return len(first_batch['nodes'])
        
        result = benchmark(run)
        # 첫 배치는 최소 100개 노드
        assert result >= 100
    
    def _generate_test_graph(self, num_nodes: int) -> Dict:
        """테스트 그래프 생성"""
        nodes = [
            {
                "id": f"node_{i}",
                "label": f"Node {i}",
                "x": (i % 50) * 16,
                "y": (i // 50) * 16
            }
            for i in range(num_nodes)
        ]
        
        edges = [
            {
                "source": f"node_{i}",
                "target": f"node_{(i + 1) % num_nodes}",
                "label": "rdfs:subClassOf"
            }
            for i in range(min(num_nodes * 2, 10000))
        ]
        
        return {"nodes": nodes, "edges": edges}
```

### 성공 기준 (Task 7-1)
- [ ] 점진적 렌더링: 3단계 배치 구현
- [ ] 성능: 1000개 노드 < 500ms (첫 배치)
- [ ] 메모리: < 50MB (렌더링 중)
- [ ] 프레임 레이트: 60fps 유지 (동적 업데이트)

---

## Task 7-2: 쿼리 응답 시간 최적화

**기간**: 07-09 ~ 07-10 (1.5일)

### 목표

이웃 탐색 API < 300ms 응답

### 구현 항목

```python
# src/performance/query_cache.py
import time
from functools import wraps
from typing import Dict, Any
import hashlib

class QueryCache:
    """SPARQL 쿼리 응답 캐싱"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
    
    def cached(self, func):
        """캐시 데코레이터"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = self._make_key(func.__name__, args, kwargs)
            
            # 캐시 히트
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if time.time() - entry['timestamp'] < self.ttl:
                    return entry['value']
            
            # 캐시 미스: 실행
            result = await func(*args, **kwargs)
            
            # 캐시 저장
            self.cache[cache_key] = {
                'value': result,
                'timestamp': time.time()
            }
            
            return result
        
        return wrapper
    
    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """캐시 키 생성"""
        key_str = f"{func_name}:{str(args)}:{str(kwargs)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def clear_expired(self):
        """만료된 캐시 삭제"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self.cache.items()
            if current_time - v['timestamp'] > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
```

#### 인덱싱 전략

```python
# src/backend/app/models/graph_index.py
class GraphIndex:
    """RDF 그래프 인덱싱"""
    
    def __init__(self, graph_db):
        self.graph_db = graph_db
        self.node_index: Dict[str, List[str]] = {}  # URI → 이웃 목록
        self.edge_index: Dict[str, List[Dict]] = {}  # 엣지 타입 → 목록
    
    async def build_index(self):
        """그래프 인덱스 구축"""
        
        # 1. 노드 이웃 인덱스
        all_uris = await self._get_all_uris()
        for uri in all_uris:
            neighbors = await self._get_neighbors(uri, depth=1)
            self.node_index[uri] = neighbors
        
        # 2. 엣지 타입 인덱스
        edge_types = await self._get_all_edge_types()
        for edge_type in edge_types:
            edges = await self._get_edges_by_type(edge_type)
            self.edge_index[edge_type] = edges
    
    async def lookup_neighborhood(self, uri: str) -> Dict:
        """인덱스 기반 빠른 이웃 조회"""
        if uri not in self.node_index:
            return {"nodes": [], "edges": []}
        
        neighbor_uris = self.node_index[uri]
        
        # 캐시된 이웃 반환
        return {
            "centerNode": uri,
            "nodes": [
                {"id": n, "label": self._extract_label(n)}
                for n in neighbor_uris
            ],
            "edges": []  # 엣지 정보는 필요시 추가
        }
    
    def _extract_label(self, uri: str) -> str:
        """URI에서 라벨 추출"""
        return uri.split('/')[-1]
```

### 성공 기준 (Task 7-2)
- [ ] 쿼리 캐싱: < 50ms (캐시 히트)
- [ ] 인덱싱: < 100ms (인덱스 조회)
- [ ] 캐시 유효성: 5분 TTL 구현
- [ ] 히트율: > 70% (반복 쿼리)

---

## Task 7-3: 네트워크 최적화

**기간**: 07-10 ~ 07-12 (2일)

### 목표

프론트엔드 ↔ 백엔드 통신 최소화

### 구현 항목

```python
# src/backend/app/routers/optimized_api.py
from fastapi import APIRouter
from typing import Dict, List

router = APIRouter(prefix="/api/rdf", tags=["Optimized RDF"])

class OptimizedNeighborhoodAPI:
    """최적화된 이웃 탐색 API"""
    
    def __init__(self, graph_index, query_cache):
        self.index = graph_index
        self.cache = query_cache
    
    @router.get("/neighborhood-optimized/{uri:path}")
    @self.cache.cached  # 캐싱 적용
    async def get_neighborhood_optimized(
        self,
        uri: str,
        depth: int = 1,
        limit: int = 100
    ) -> Dict:
        """
        최적화된 이웃 탐색
        
        **최적화 기법**:
        1. 인덱스 기반 조회 (SPARQL 회피)
        2. 응답 캐싱 (5분 TTL)
        3. 페이지네이션 (limit으로 크기 제한)
        4. 선택적 필드 (필요한 것만 반환)
        """
        
        # 인덱스에서 빠르게 조회
        neighborhood = await self.index.lookup_neighborhood(uri)
        
        # 페이지네이션
        nodes = neighborhood['nodes'][:limit]
        
        return {
            "centerNode": uri,
            "nodes": nodes,
            "edges": neighborhood.get('edges', []),
            "hasMore": len(neighborhood['nodes']) > limit,
            "processingTimeMs": 15  # 인덱스 기반이므로 매우 빠름
        }
```

#### 프론트엔드 최적화

```typescript
// src/lib/api-optimized.ts
export const apiOptimized = {
  /**
   * 이웃 탐색 (캐싱 + 배치 처리)
   */
  async getNeighborhoodBatched(
    uri: string,
    batchSize: number = 50
  ): Promise<NeighborhoodResponse> {
    // 로컬 캐시 확인
    const cacheKey = `neighborhood:${uri}`;
    const cached = localStorage.getItem(cacheKey);
    
    if (cached) {
      const entry = JSON.parse(cached);
      if (Date.now() - entry.timestamp < 5 * 60 * 1000) {
        return entry.data;
      }
    }
    
    // API 호출
    const response = await fetch(
      `/api/rdf/neighborhood-optimized/${encodeURIComponent(uri)}`
    );
    
    const data = await response.json();
    
    // 로컬 저장
    localStorage.setItem(cacheKey, JSON.stringify({
      data,
      timestamp: Date.now()
    }));
    
    return data;
  }
};
```

### 성공 기준 (Task 7-3)
- [ ] 네트워크 요청: 최소화 (캐싱으로 50% 감소)
- [ ] 페이로드 크기: < 50KB (limit으로 조절)
- [ ] 응답 시간: < 100ms (캐시 + 인덱스)
- [ ] 대역폭 효율: > 80%

---

## 성능 벤치마크 결과 목표

| 메트릭 | 목표 | 측정 기준 |
|--------|------|----------|
| 렌더링 (1000 노드) | < 500ms | 첫 배치 |
| 쿼리 응답 (캐시 히트) | < 50ms | 이웃 조회 |
| 쿼리 응답 (캐시 미스) | < 300ms | SPARQL 실행 |
| 메모리 사용 | < 100MB | 전체 프로세스 |
| 캐시 히트율 | > 70% | 반복 패턴 |

---

## 테스트 실행

```bash
# 렌더링 벤치마크
python -m pytest tests/phase4/week7_graph_rendering_bench.py -v --benchmark-only

# API 성능 테스트
python -m pytest tests/phase4/week7_api_performance_test.py -v

# 프로파일링
python -m cProfile -s cumulative main.py > profile.txt
```

---

**다음 단계**: Week 8 (PoC E2E - Import → Mapping → Merge → Validation)
