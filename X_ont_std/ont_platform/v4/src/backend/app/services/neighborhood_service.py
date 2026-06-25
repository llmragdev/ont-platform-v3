"""RDF 그래프 이웃 탐색 서비스"""
from typing import Dict, List, Set, Any
import time
import logging

logger = logging.getLogger(__name__)


class NeighborhoodService:
    """RDF 그래프 이웃 탐색"""

    def __init__(self, graph_db):
        self.graph_db = graph_db

    async def get_neighborhood(
        self,
        uri: str,
        depth: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        주어진 URI의 이웃 노드 탐색

        Args:
            uri: 중심 노드 URI
            depth: 탐색 깊이 (1 또는 2)
            limit: 반환할 최대 노드 수

        Returns:
        {
            "centerNode": "http://example.org/concept/1",
            "nodes": [
                {
                    "id": "http://example.org/concept/2",
                    "label": "Child Concept",
                    "type": "Class"
                }
            ],
            "edges": [
                {
                    "source": "http://example.org/concept/1",
                    "target": "http://example.org/concept/2",
                    "label": "rdfs:subClassOf",
                    "direction": "outgoing"
                }
            ],
            "processingTimeMs": 45,
            "totalNodeCount": 45,
            "totalEdgeCount": 120
        }
        """

        start_time = time.time()

        try:
            # SPARQL로 1-hop/2-hop 이웃 조회
            query = self._build_neighborhood_query(uri, depth, limit)
            results = await self.graph_db.query_sparql(query)

            # 결과 구조화
            nodes = self._extract_nodes(results, uri)
            edges = self._extract_edges(results)

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "centerNode": uri,
                "nodes": list(nodes.values()),
                "edges": edges[:limit],
                "processingTimeMs": round(elapsed_ms),
                "totalNodeCount": len(nodes),
                "totalEdgeCount": len(edges)
            }
        except Exception as e:
            logger.error(f"Failed to get neighborhood for {uri}: {str(e)}")
            raise

    def _build_neighborhood_query(self, uri: str, depth: int, limit: int) -> str:
        """SPARQL 쿼리 생성"""

        if depth == 1:
            return f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?neighbor ?predicate ?direction ?nodeLabel ?nodeType
            WHERE {{
                {{
                    <{uri}> ?predicate ?neighbor .
                    BIND("outgoing" as ?direction)
                }} UNION {{
                    ?neighbor ?predicate <{uri}> .
                    BIND("incoming" as ?direction)
                }}

                OPTIONAL {{ ?neighbor rdfs:label ?nodeLabel }}
                OPTIONAL {{ ?neighbor rdf:type ?nodeType }}

                FILTER (isIRI(?neighbor))
            }}
            LIMIT {limit * 2}
            """
        else:  # depth == 2
            return f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?neighbor ?predicate ?direction ?nodeLabel ?nodeType
            WHERE {{
                {{
                    <{uri}> ?pred1 ?neighbor1 .
                    ?neighbor1 ?predicate ?neighbor .
                    BIND("outgoing" as ?direction)
                }} UNION {{
                    ?neighbor1 ?pred1 <{uri}> .
                    ?neighbor ?predicate ?neighbor1 .
                    BIND("incoming" as ?direction)
                }}

                OPTIONAL {{ ?neighbor rdfs:label ?nodeLabel }}
                OPTIONAL {{ ?neighbor rdf:type ?nodeType }}

                FILTER (isIRI(?neighbor) && ?neighbor != <{uri}>)
            }}
            LIMIT {limit * 3}
            """

    def _extract_nodes(self, results: List[Dict], center_uri: str) -> Dict[str, Dict]:
        """결과에서 노드 추출"""
        nodes = {
            center_uri: {
                "id": center_uri,
                "label": self._extract_label(center_uri),
                "type": "Center"
            }
        }

        for result in results:
            neighbor = result.get('neighbor')
            if neighbor and neighbor not in nodes:
                nodes[neighbor] = {
                    "id": neighbor,
                    "label": result.get('nodeLabel') or self._extract_label(neighbor),
                    "type": self._infer_type(result.get('nodeType', ''))
                }

        return nodes

    def _extract_edges(self, results: List[Dict]) -> List[Dict]:
        """결과에서 엣지 추출"""
        edges = []
        seen = set()

        for result in results:
            neighbor = result.get('neighbor')
            predicate = result.get('predicate')
            direction = result.get('direction', 'outgoing')

            if not neighbor or not predicate:
                continue

            # 중복 제거
            edge_key = (neighbor, predicate, direction)
            if edge_key in seen:
                continue
            seen.add(edge_key)

            if direction == "outgoing":
                source = neighbor
                target = neighbor
            else:
                source = neighbor
                target = neighbor

            edges.append({
                "source": source,
                "target": target,
                "label": predicate,
                "direction": direction
            })

        return edges

    def _extract_label(self, uri: str) -> str:
        """URI에서 라벨 추출"""
        # 마지막 '/' 또는 '#' 이후의 부분 반환
        if '/' in uri:
            return uri.split('/')[-1]
        elif '#' in uri:
            return uri.split('#')[-1]
        return uri

    def _infer_type(self, rdf_type: str) -> str:
        """RDF 타입에서 타입 이름 추론"""
        if not rdf_type:
            return "Resource"

        if 'Class' in rdf_type:
            return "Class"
        elif 'Property' in rdf_type:
            return "Property"
        elif 'Ontology' in rdf_type:
            return "Ontology"
        else:
            return self._extract_label(rdf_type)
