from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


class GraphIndex:
    """RDF 그래프 이웃 인덱스"""

    def __init__(self, triples: Optional[List[Tuple[str, str, str]]] = None):
        self.triples = triples or []
        self.node_index: Dict[str, Set[str]] = {}
        self.edge_index: Dict[str, List[Dict[str, str]]] = {}
        self.build_index()

    def build_index(self) -> None:
        """인덱스 구축"""
        self.node_index.clear()
        self.edge_index.clear()

        for subject, predicate, obj in self.triples:
            self.node_index.setdefault(subject, set()).add(obj)
            self.node_index.setdefault(obj, set()).add(subject)

            self.edge_index.setdefault(predicate, []).append(
                {
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                }
            )

    def lookup_neighborhood(
        self,
        uri: str,
        depth: int = 1,
        limit: int = 100,
    ) -> Dict[str, object]:
        """이웃 노드와 엣지 정보를 반환"""
        neighbors = self.node_index.get(uri, set())
        agent_nodes = [self._node_repr(uri)]  # center node included

        for neighbor in sorted(neighbors)[:limit]:
            agent_nodes.append(self._node_repr(neighbor))

        edges = self._get_edges_for_uri(uri, list(neighbors)[:limit])
        return {
            "centerNode": uri,
            "nodes": agent_nodes,
            "edges": edges,
            "has_more": len(neighbors) > limit,
        }

    def _node_repr(self, uri: str) -> Dict[str, str]:
        return {
            "id": uri,
            "label": self._extract_label(uri),
        }

    def _get_edges_for_uri(self, uri: str, neighbor_uris: List[str]) -> List[Dict[str, str]]:
        result = []
        neighbor_set = set(neighbor_uris)
        for subject, predicate, obj in self.triples:
            if subject == uri and obj in neighbor_set:
                result.append({"source": subject, "target": obj, "predicate": predicate})
            elif obj == uri and subject in neighbor_set:
                result.append({"source": subject, "target": obj, "predicate": predicate})
        return result

    def _extract_label(self, uri: str) -> str:
        return uri.split("/")[-1] if "/" in uri else uri
