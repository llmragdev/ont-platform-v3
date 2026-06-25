"""온톨로지 매핑 서비스"""
from typing import Dict, List, Any
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MappingRequest(BaseModel):
    """매핑 생성 요청"""
    externalUri: str
    internalUri: str
    relationshipType: str = "skos:exactMatch"
    confidence: float = 1.0


class MappingCandidateRequest(BaseModel):
    """매핑 후보 요청"""
    externalUri: str
    limit: int = 10


class MappingService:
    """온톨로지 매핑 관리"""

    def __init__(self, graph_db, embedding_service=None):
        self.graph_db = graph_db
        self.embedding_service = embedding_service

    async def create_mapping(
        self,
        request: MappingRequest
    ) -> Dict[str, Any]:
        """
        매핑 생성 - external URI를 internal URI로 매핑

        Args:
            request: 매핑 요청 (external URI, internal URI, 관계 타입, 신뢰도)

        Returns:
        {
            "success": True,
            "mapping": {
                "externalUri": "...",
                "internalUri": "...",
                "relationshipType": "skos:exactMatch",
                "confidence": 1.0
            }
        }
        """

        try:
            # 1. 그래프에 triple 추가 (Batch Transaction 패턴)
            insert_query = self._build_insert_mapping_query(
                request.externalUri,
                request.internalUri,
                request.relationshipType,
                request.confidence
            )

            await self.graph_db.execute_update(insert_query)

            logger.info(
                f"Mapping created: {request.externalUri} -> {request.internalUri}"
            )

            return {
                "success": True,
                "mapping": {
                    "externalUri": request.externalUri,
                    "internalUri": request.internalUri,
                    "relationshipType": request.relationshipType,
                    "confidence": request.confidence
                }
            }
        except Exception as e:
            logger.error(f"Failed to create mapping: {str(e)}")
            raise

    async def get_mapping_candidates(
        self,
        request: MappingCandidateRequest
    ) -> Dict[str, Any]:
        """
        외부 URI와 유사한 내부 URI 후보 추출

        Args:
            request: 매핑 후보 요청 (external URI, 최대 개수)

        Returns:
        {
            "externalUri": "...",
            "candidates": [
                {
                    "internalUri": "...",
                    "similarity": 0.95,
                    "label": "..."
                }
            ]
        }
        """

        try:
            # 1. 벡터 기반 유사도 계산 (embedding_service가 있는 경우)
            if self.embedding_service:
                candidates = await self._get_candidates_by_embedding(
                    request.externalUri,
                    request.limit
                )
            else:
                # 기본: URI 문자열 유사도
                candidates = await self._get_candidates_by_label(
                    request.externalUri,
                    request.limit
                )

            return {
                "externalUri": request.externalUri,
                "candidates": candidates
            }
        except Exception as e:
            logger.error(f"Failed to get mapping candidates: {str(e)}")
            raise

    async def _get_candidates_by_embedding(
        self,
        external_uri: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """벡터 유사도 기반 후보 추출"""

        try:
            # 1. 외부 URI 임베딩
            external_embedding = await self.embedding_service.embed(
                external_uri
            )

            # 2. 모든 내부 URI 임베딩 조회 및 유사도 계산
            candidates = await self.graph_db.find_similar_uris(
                external_embedding,
                limit=limit
            )

            # 3. 결과 포맷팅
            return [
                {
                    "internalUri": c['uri'],
                    "similarity": round(c['score'], 3),
                    "label": c.get('label', self._extract_label(c['uri']))
                }
                for c in candidates
            ]
        except Exception as e:
            logger.warning(f"Embedding-based search failed: {str(e)}")
            # 폴백: 라벨 기반 검색
            return await self._get_candidates_by_label(external_uri, limit)

    async def _get_candidates_by_label(
        self,
        external_uri: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """라벨 기반 후보 추출 (폴백)"""

        try:
            external_label = self._extract_label(external_uri)

            # SPARQL로 유사 라벨 검색
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT ?uri ?label
            WHERE {{
                ?uri rdfs:label ?label .
                FILTER(REGEX(STR(?label), "{external_label}", "i"))
            }}
            LIMIT {limit * 2}
            """

            results = await self.graph_db.query_sparql(query)

            # 문자열 유사도 계산
            candidates = []
            for result in results[:limit]:
                uri = result.get('uri')
                label = result.get('label', '')
                similarity = self._calculate_string_similarity(
                    external_label,
                    label
                )

                candidates.append({
                    "internalUri": uri,
                    "similarity": round(similarity, 3),
                    "label": label
                })

            # 유사도 정렬
            candidates.sort(key=lambda x: x['similarity'], reverse=True)

            return candidates[:limit]
        except Exception as e:
            logger.error(f"Label-based search failed: {str(e)}")
            return []

    def _build_insert_mapping_query(
        self,
        external_uri: str,
        internal_uri: str,
        relationship_type: str,
        confidence: float
    ) -> str:
        """매핑 저장 쿼리 생성 (Batch Transaction 패턴)"""

        return f"""
        INSERT DATA {{
            GRAPH <http://ontology.platform/graphs/mappings> {{
                <{external_uri}> <{relationship_type}> <{internal_uri}> ;
                    <http://ontology.platform/confidence> {confidence} ;
                    <http://ontology.platform/mappedAt> "{self._get_timestamp()}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
            }}
        }}
        """

    def _extract_label(self, uri: str) -> str:
        """URI에서 라벨 추출"""
        if '/' in uri:
            return uri.split('/')[-1]
        elif '#' in uri:
            return uri.split('#')[-1]
        return uri

    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """문자열 유사도 계산 (간단한 Levenshtein 기반)"""

        s1 = s1.lower()
        s2 = s2.lower()

        if s1 == s2:
            return 1.0

        # 공통 문자 개수 / 전체 문자 개수
        common = sum(1 for c in s1 if c in s2)
        return common / max(len(s1), len(s2)) if max(len(s1), len(s2)) > 0 else 0

    def _get_timestamp(self) -> str:
        """현재 시간을 ISO 8601 형식으로 반환"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
