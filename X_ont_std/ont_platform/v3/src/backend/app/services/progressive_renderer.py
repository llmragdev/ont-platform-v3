from __future__ import annotations

from typing import Dict, Generator, List, Tuple


class ProgressiveGraphRenderer:
    """점진적 그래프 렌더링"""

    def render_with_priority(
        self,
        graph_data: Dict,
        viewport_size: Tuple[int, int],
    ) -> Generator[Dict, None, None]:
        """뷰포트와 중요도 기반으로 그래프를 단계별로 반환"""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        center_nodes = self._get_center_nodes(nodes, count=max(1, len(nodes) // 10))
        center_edges = self._get_edges_for_nodes(edges, center_nodes)

        yield {
            "type": "batch_1",
            "nodes": center_nodes,
            "edges": center_edges,
            "priority": "critical",
        }

        viewport_nodes = self._get_viewport_nodes(nodes, viewport_size, exclude=center_nodes)
        viewport_edges = self._get_edges_for_nodes(edges, viewport_nodes)

        yield {
            "type": "batch_2",
            "nodes": viewport_nodes,
            "edges": viewport_edges,
            "priority": "high",
        }

        remaining_nodes = [
            n for n in nodes
            if n not in center_nodes and n not in viewport_nodes
        ]
        batch_size = 100

        for i in range(0, len(remaining_nodes), batch_size):
            batch = remaining_nodes[i:i + batch_size]
            batch_edges = self._get_edges_for_nodes(edges, batch)
            yield {
                "type": "batch_3",
                "nodes": batch,
                "edges": batch_edges,
                "priority": "low",
                "batchIndex": i // batch_size,
            }

    def _get_center_nodes(self, nodes: List[Dict], count: int) -> List[Dict]:
        """중심도 기반 중요 노드를 단순 정렬 방식으로 선택"""
        return sorted(nodes, key=lambda n: n.get("id", ""))[:count]

    def _get_viewport_nodes(
        self,
        nodes: List[Dict],
        viewport: Tuple[int, int],
        exclude: List[Dict],
    ) -> List[Dict]:
        """뷰포트 내 위치한 노드 집합을 선택"""
        exclude_ids = {n["id"] for n in exclude if "id" in n}
        viewport_w, viewport_h = viewport

        return [
            n for n in nodes
            if n.get("id") not in exclude_ids
            and 0.25 * viewport_w <= n.get("x", 0) <= 0.75 * viewport_w
            and 0.25 * viewport_h <= n.get("y", 0) <= 0.75 * viewport_h
        ]

    def _get_edges_for_nodes(self, edges: List[Dict], nodes: List[Dict]) -> List[Dict]:
        """주어진 노드 목록에 연결된 엣지 필터링"""
        node_ids = {n.get("id") for n in nodes if "id" in n}
        return [
            e for e in edges
            if e.get("source") in node_ids or e.get("target") in node_ids
        ]
