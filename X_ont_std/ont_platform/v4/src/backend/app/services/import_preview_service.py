"""RDF 임포트 미리보기 서비스"""
from typing import Dict, List, Any, Set
import logging
from rdflib import Graph

logger = logging.getLogger(__name__)


class ConflictDetector:
    """RDF 충돌 감지"""

    @staticmethod
    def detect_duplicate_class(subject: str, existing_uris: Set[str]) -> bool:
        """중복 클래스 감지"""
        return subject in existing_uris

    @staticmethod
    def detect_domain_mismatch(predicate: str, obj: str) -> bool:
        """도메인 불일치 감지"""
        # 간단한 휴리스틱: 타입 선언과 인스턴스 간 불일치
        return False  # 구체적인 로직은 온톨로지 스키마에 따라 구현


class ImportPreviewService:
    """RDF 임포트 미리보기"""

    def __init__(self, graph_db):
        self.graph_db = graph_db
        self.conflict_detector = ConflictDetector()

    async def preview_import(
        self,
        rdf_content: str,
        rdf_format: str = "turtle"
    ) -> Dict[str, Any]:
        """
        RDF 파일 임포트 미리보기

        Args:
            rdf_content: RDF 콘텐츠 (문자열)
            rdf_format: RDF 포맷 (turtle, xml, n-triples, etc.)

        Returns:
        {
            "newTripleCount": 1000,
            "newEntityCount": 150,
            "potentialConflicts": [
                {
                    "externalUri": "...",
                    "internalUri": "...",
                    "conflictType": "duplicate_class",
                    "severity": "high"
                }
            ],
            "suggestedMappings": [...]
        }
        """

        try:
            # 1. RDF 파싱
            temp_graph = await self._parse_rdf(rdf_content, rdf_format)

            if temp_graph is None:
                return {
                    "newTripleCount": 0,
                    "newEntityCount": 0,
                    "potentialConflicts": [],
                    "suggestedMappings": [],
                    "error": "Invalid RDF format"
                }

            # 2. 새 엔티티 추출
            new_entities = await self._identify_new_entities(temp_graph)

            # 3. 충돌 감지
            conflicts = await self._detect_conflicts(new_entities)

            # 4. 매핑 제안
            suggested_mappings = await self._suggest_mappings(new_entities)

            return {
                "newTripleCount": len(temp_graph),
                "newEntityCount": len(new_entities),
                "potentialConflicts": conflicts,
                "suggestedMappings": suggested_mappings[:10],
                "parseSuccess": True
            }
        except Exception as e:
            logger.error(f"Failed to preview import: {str(e)}")
            return {
                "newTripleCount": 0,
                "newEntityCount": 0,
                "potentialConflicts": [],
                "suggestedMappings": [],
                "error": str(e)
            }

    async def _parse_rdf(
        self,
        rdf_content: str,
        rdf_format: str
    ) -> Graph | None:
        """RDF 콘텐츠 파싱"""

        try:
            graph = Graph()

            # rdflib 지원 포맷 매핑
            format_map = {
                "turtle": "turtle",
                "ttl": "turtle",
                "rdf": "xml",
                "xml": "xml",
                "n-triples": "nt",
                "nt": "nt",
                "jsonld": "json-ld"
            }

            parsed_format = format_map.get(rdf_format.lower(), "turtle")

            graph.parse(data=rdf_content, format=parsed_format)
            return graph
        except Exception as e:
            logger.error(f"RDF parsing failed: {str(e)}")
            return None

    async def _identify_new_entities(self, graph: Graph) -> List[Dict[str, str]]:
        """새로운 엔티티 추출"""

        entities = []

        # 모든 subject와 object에서 IRI 추출
        iris = set()
        for s, p, o in graph:
            if isinstance(s, object) and hasattr(s, 'startswith'):
                iris.add(str(s))
            if isinstance(o, object) and hasattr(o, 'startswith') and str(o).startswith('http'):
                iris.add(str(o))

        for iri in iris:
            # 기존 데이터베이스와 비교하여 새 것만 필터링
            exists = await self._entity_exists_in_db(iri)

            if not exists:
                entities.append({
                    "uri": iri,
                    "label": self._extract_label(iri),
                    "isNew": True
                })

        return entities

    async def _entity_exists_in_db(self, uri: str) -> bool:
        """엔티티가 이미 데이터베이스에 존재하는지 확인"""

        try:
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            ASK WHERE {{
                <{uri}> ?p ?o .
            }}
            """

            result = await self.graph_db.query_sparql(query)
            return bool(result)
        except Exception:
            return False  # 오류 시 존재하지 않는 것으로 간주

    async def _detect_conflicts(
        self,
        new_entities: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """충돌 감지"""

        conflicts = []

        for entity in new_entities:
            uri = entity['uri']
            label = entity['label']

            # 1. 라벨 기반 중복 클래스 감지
            similar_uris = await self._find_similar_uris(label)

            for similar_uri in similar_uris:
                if similar_uri != uri:
                    conflicts.append({
                        "externalUri": uri,
                        "internalUri": similar_uri,
                        "conflictType": "duplicate_class",
                        "severity": "high",
                        "reason": f"Label '{label}' matches existing URI"
                    })

        return conflicts[:10]  # 최대 10개

    async def _find_similar_uris(self, label: str) -> List[str]:
        """유사 라벨을 가진 URI 찾기"""

        try:
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?uri
            WHERE {{
                ?uri rdfs:label ?label .
                FILTER(REGEX(STR(?label), "{label}", "i"))
            }}
            LIMIT 5
            """

            results = await self.graph_db.query_sparql(query)
            return [r['uri'] for r in results if 'uri' in r]
        except Exception:
            return []

    async def _suggest_mappings(
        self,
        new_entities: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """매핑 제안"""

        suggestions = []

        for entity in new_entities:
            uri = entity['uri']
            label = entity['label']

            # 라벨 기반 후보 찾기
            candidates = await self._find_mapping_candidates(label)

            for candidate in candidates:
                suggestions.append({
                    "externalUri": uri,
                    "internalUri": candidate['uri'],
                    "similarity": candidate.get('similarity', 0.8),
                    "reason": f"Label match: {label}",
                    "relationshipType": "skos:exactMatch"
                })

        return suggestions

    async def _find_mapping_candidates(self, label: str) -> List[Dict[str, Any]]:
        """라벨 기반 매핑 후보 찾기"""

        try:
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?uri ?candidateLabel
            WHERE {{
                ?uri rdfs:label ?candidateLabel .
                FILTER(REGEX(STR(?candidateLabel), "{label}", "i"))
            }}
            LIMIT 5
            """

            results = await self.graph_db.query_sparql(query)

            candidates = []
            for result in results:
                if 'uri' in result:
                    candidates.append({
                        "uri": result['uri'],
                        "label": result.get('candidateLabel', ''),
                        "similarity": 0.85  # 기본 유사도
                    })

            return candidates
        except Exception:
            return []

    def _extract_label(self, uri: str) -> str:
        """URI에서 라벨 추출"""
        if '/' in uri:
            return uri.split('/')[-1]
        elif '#' in uri:
            return uri.split('#')[-1]
        return uri
