"""Phase 4 Week 2: 혈통 추적 서비스"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Set, Any

from app.models.entity_metadata import (
    LineageInfo, Transformation, TransformationType, DataSourceType,
    ImportMetadata, LineageQuery
)
from app.repositories.audit_repository import AuditRepository


class LineageGraph:
    """혈통 그래프 표현"""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}  # entity_id → metadata
        self.edges: List[Dict[str, Any]] = []        # {from, to, type, metadata}

    def add_node(self, entity_id: str, metadata: Dict[str, Any]) -> None:
        """노드 추가"""
        self.nodes[entity_id] = metadata

    def add_edge(
        self, from_id: str, to_id: str, edge_type: str, metadata: Optional[Dict] = None
    ) -> None:
        """엣지 추가 (데이터 흐름)"""
        self.edges.append({
            "from": from_id,
            "to": to_id,
            "type": edge_type,
            "metadata": metadata or {}
        })

    def to_dict(self) -> Dict[str, Any]:
        """사전으로 변환"""
        return {
            "nodes": self.nodes,
            "edges": self.edges
        }


class LineageService:
    """데이터 혈통 추적 서비스"""

    def __init__(self, audit_repo: Optional[AuditRepository] = None):
        self.audit_repo = audit_repo or AuditRepository()
        # 메모리 캐시 (간단한 구현)
        self.lineage_cache: Dict[str, LineageInfo] = {}

    def record_lineage(self, entity_id: str, lineage: LineageInfo) -> None:
        """혈통 정보 기록"""
        self.lineage_cache[entity_id] = lineage

    def record_transformation(
        self,
        entity_id: str,
        transformation: Transformation,
        lineage: Optional[LineageInfo] = None
    ) -> None:
        """변환 기록"""
        if lineage:
            self.record_lineage(entity_id, lineage)

        if entity_id not in self.lineage_cache:
            self.lineage_cache[entity_id] = LineageInfo(
                source_type=DataSourceType.DERIVED
            )

        self.lineage_cache[entity_id].transformations.append(transformation)

    def get_lineage(self, entity_id: str) -> Optional[LineageInfo]:
        """혈통 정보 조회"""
        return self.lineage_cache.get(entity_id)

    def trace_upstream(
        self, entity_id: str, depth: int = 3
    ) -> LineageGraph:
        """상류 추적 (입력 데이터)"""
        graph = LineageGraph()
        visited: Set[str] = set()

        def _trace(eid: str, current_depth: int):
            if current_depth <= 0 or eid in visited:
                return

            visited.add(eid)
            lineage = self.get_lineage(eid)

            if lineage:
                graph.add_node(eid, {"source_type": lineage.source_type.value})

                # 직접 부모들
                for parent_id in lineage.direct_parent_ids:
                    graph.add_edge(parent_id, eid, "derived_from")
                    _trace(parent_id, current_depth - 1)

                # 변환 입력들
                for transformation in lineage.transformations:
                    for input_id in transformation.input_ids:
                        graph.add_edge(input_id, eid, transformation.transformation_type.value)
                        _trace(input_id, current_depth - 1)

        _trace(entity_id, depth)
        return graph

    def trace_downstream(
        self, entity_id: str, depth: int = 3, all_lineages: Optional[Dict[str, LineageInfo]] = None
    ) -> LineageGraph:
        """하류 추적 (출력 데이터)"""
        if all_lineages is None:
            all_lineages = self.lineage_cache

        graph = LineageGraph()
        visited: Set[str] = set()

        def _trace(eid: str, current_depth: int):
            if current_depth <= 0 or eid in visited:
                return

            visited.add(eid)
            graph.add_node(eid, {})

            # entity_id를 입력으로 하는 모든 엔티티 찾기
            for target_id, target_lineage in all_lineages.items():
                if eid in target_lineage.direct_parent_ids:
                    graph.add_edge(eid, target_id, "parent_of")
                    _trace(target_id, current_depth - 1)

                for transformation in target_lineage.transformations:
                    if eid in transformation.input_ids:
                        graph.add_edge(eid, target_id, transformation.transformation_type.value)
                        _trace(target_id, current_depth - 1)

        _trace(entity_id, depth)
        return graph

    def trace_both_directions(
        self, entity_id: str, depth: int = 3
    ) -> Dict[str, LineageGraph]:
        """양방향 추적"""
        return {
            "upstream": self.trace_upstream(entity_id, depth),
            "downstream": self.trace_downstream(entity_id, depth)
        }

    def find_lineage_path(
        self, source_id: str, target_id: str, max_hops: int = 10
    ) -> Optional[List[str]]:
        """두 엔티티 간의 연결 경로 찾기 (BFS)"""
        from collections import deque

        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current, path = queue.popleft()

            if len(path) > max_hops:
                continue

            if current == target_id:
                return path

            lineage = self.get_lineage(current)
            if not lineage:
                continue

            # 다음 노드들
            next_nodes = set(lineage.direct_parent_ids)
            for transformation in lineage.transformations:
                next_nodes.update(transformation.input_ids)

            for next_node in next_nodes:
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))

        return None

    def get_data_quality_by_source(self, source_type: DataSourceType) -> Dict[str, Any]:
        """데이터 원천별 품질 지표"""
        entities_by_source = {}

        for entity_id, lineage in self.lineage_cache.items():
            if lineage.source_type == source_type:
                if source_type not in entities_by_source:
                    entities_by_source[source_type] = []
                entities_by_source[source_type].append(entity_id)

        return {
            "source_type": source_type.value,
            "entity_count": len(entities_by_source.get(source_type, [])),
            "entities": entities_by_source.get(source_type, [])
        }

    def get_most_transformed_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """가장 많이 변환된 엔티티들"""
        entities_with_transforms = []

        for entity_id, lineage in self.lineage_cache.items():
            transform_count = len(lineage.transformations)
            if transform_count > 0:
                entities_with_transforms.append({
                    "entity_id": entity_id,
                    "transformation_count": transform_count,
                    "transformations": [
                        {
                            "type": t.transformation_type.value,
                            "description": t.description
                        }
                        for t in lineage.transformations
                    ]
                })

        # 변환 수로 정렬
        entities_with_transforms.sort(
            key=lambda x: x["transformation_count"], reverse=True
        )

        return entities_with_transforms[:limit]

    def get_data_sources_summary(self) -> Dict[str, Any]:
        """데이터 원천 요약"""
        sources = {}

        for entity_id, lineage in self.lineage_cache.items():
            source_type = lineage.source_type.value
            if source_type not in sources:
                sources[source_type] = {"count": 0, "import_sources": set()}

            sources[source_type]["count"] += 1

            if lineage.import_metadata:
                sources[source_type]["import_sources"].add(lineage.import_metadata.source_name)

        # Set을 List로 변환
        for source_type in sources:
            sources[source_type]["import_sources"] = list(sources[source_type]["import_sources"])

        return sources

    def detect_circular_dependencies(self) -> List[List[str]]:
        """순환 의존성 감지"""
        cycles = []

        def _has_cycle(start: str, current: str, path: List[str], visited: Set[str]) -> bool:
            if current in visited:
                if start in path:
                    cycle_start = path.index(start)
                    cycles.append(path[cycle_start:] + [current])
                return True

            visited.add(current)
            lineage = self.get_lineage(current)

            if lineage:
                for parent_id in lineage.direct_parent_ids:
                    if _has_cycle(start, parent_id, path + [current], visited.copy()):
                        return True

            return False

        # 모든 엔티티에서 시작해 순환 검사
        for entity_id in self.lineage_cache.keys():
            _has_cycle(entity_id, entity_id, [], set())

        return cycles

    def export_lineage_graph(self, entity_id: str, direction: str = "both") -> Dict[str, Any]:
        """혈통 그래프 내보내기"""
        if direction == "upstream":
            graph = self.trace_upstream(entity_id)
        elif direction == "downstream":
            graph = self.trace_downstream(entity_id)
        else:  # both
            graphs = self.trace_both_directions(entity_id)
            return {
                "entity_id": entity_id,
                "upstream": graphs["upstream"].to_dict(),
                "downstream": graphs["downstream"].to_dict(),
                "exported_at": datetime.utcnow().isoformat()
            }

        return {
            "entity_id": entity_id,
            "direction": direction,
            "graph": graph.to_dict(),
            "exported_at": datetime.utcnow().isoformat()
        }
