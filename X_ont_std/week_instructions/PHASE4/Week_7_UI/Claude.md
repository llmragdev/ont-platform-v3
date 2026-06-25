# Phase 4 Week 7: 온톨로지 확장 백엔드 API
## Claude (Backend) 수행 지시서

**기간**: 2026-07-08 ~ 2026-07-12 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 온톨로지 매핑/조회 API, RDF 그래프 탐색, SPARQL 검색

---

## 중요 주의: Codex.md의 API 계약 준수

Codex 프론트엔드에서 호출하는 다음 4개 API를 반드시 구현해야 합니다:
- `POST /api/ontology/mappings` (매핑 생성)
- `GET /api/ontology/mapping-candidates` (매핑 후보 추출)
- `POST /api/ontology/import/preview` (RDF 임포트 미리보기)
- `GET /api/rdf/neighborhood/{uri}` (그래프 이웃 탐색)

---

## Task 7-1: RDF 그래프 탐색 API (Expand on Click)

**기간**: 07-08 ~ 07-09 (1.5일)

### 목표
1-hop/2-hop 이웃 탐색을 < 300ms로 반환

### 구현 항목

#### 1) 그래프 이웃 탐색 API

```python
# app/routers/rdf_api.py
from fastapi import APIRouter, Query
from typing import Dict, List
import asyncio
import time

router = APIRouter(prefix="/api/rdf", tags=["RDF Graph"])

class NeighborhoodService:
    """RDF 그래프 이웃 탐색"""
    
    def __init__(self, graph_db):
        self.graph_db = graph_db
    
    async def get_neighborhood(
        self,
        uri: str,
        depth: int = 1,
        limit: int = 100
    ) -> Dict:
        """
        주어진 URI의 이웃 노드 탐색
        
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
        
        # SPARQL로 1-hop/2-hop 이웃 조회
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT ?neighbor ?predicate ?direction ?nodeLabel
        WHERE {{
            {{
                <{uri}> ?predicate ?neighbor .
                BIND("outgoing" as ?direction)
            }} UNION {{
                ?neighbor ?predicate <{uri}> .
                BIND("incoming" as ?direction)
            }}
            
            OPTIONAL {{ ?neighbor rdfs:label ?nodeLabel }}
            
            FILTER (isIRI(?neighbor))
        }}
        LIMIT {limit * 2}
        """
        
        results = await self.graph_db.query_sparql(query)
        
        # 결과 구조화
        nodes = {}
        edges = []
        
        for result in results:
            neighbor = result['neighbor']
            predicate = result['predicate']
            direction = result['direction']
            label = result.get('nodeLabel', self._extract_label(neighbor))
            
            # 노드 추가
            if neighbor not in nodes:
                nodes[neighbor] = {
                    "id": neighbor,
                    "label": label,
                    "type": self._infer_type(neighbor)
                }
            
            # 엣지 추가
            if direction == "outgoing":
                edges.append({
                    "source": uri,
                    "target": neighbor,
                    "label": predicate,
                    "direction": "outgoing"
                })
            else:
                edges.append({
                    "source": neighbor,
                    "target": uri,
                    "label": predicate,
                    "direction": "incoming"
                })
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "centerNode": uri,
            "nodes": list(nodes.values()),
            "edges": edges[:limit],
            "processingTimeMs": round(elapsed_ms),
            "totalNodeCount": len(nodes),
            "totalEdgeCount": len(edges)
        }

@router.get("/neighborhood/{uri:path}")
async def get_neighborhood(
    uri: str,
    depth: int = Query(1, ge=1, le=2),
    limit: int = Query(100, ge=10, le=500)
) -> Dict:
    """RDF 그래프 이웃 탐색"""
    service = NeighborhoodService(graph_db)
    return await service.get_neighborhood(uri, depth, limit)
```

### 성공 기준 (Task 7-1)
- [ ] 이웃 탐색 API: 1-hop/2-hop 정확하게 반환
- [ ] 성능: < 300ms (100개 노드 기준)
- [ ] 라벨 추출: rdfs:label 또는 URI에서 추론
- [ ] 엣지 방향: incoming/outgoing 구분

---

## Task 7-2: 온톨로지 매핑 API

**기간**: 07-09 ~ 07-11 (1.5일)

### 목표

external URI와 internal URI 간 매핑 생성 및 검색

### 구현 항목

```python
# app/routers/ontology_api.py
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/ontology", tags=["Ontology"])

class MappingRequest(BaseModel):
    externalUri: str
    internalUri: str
    relationshipType: str = "skos:exactMatch"
    confidence: float = 1.0

class MappingCandidateRequest(BaseModel):
    externalUri: str
    limit: int = 10

class MappingService:
    """온톨로지 매핑 관리"""
    
    def __init__(self, graph_db, embedding_service):
        self.graph_db = graph_db
        self.embedding_service = embedding_service
    
    async def create_mapping(
        self,
        request: MappingRequest
    ) -> Dict:
        """매핑 생성"""
        
        # 1. 그래프에 triple 추가
        insert_query = f"""
        INSERT DATA {{
            <{request.externalUri}> <{request.relationshipType}> <{request.internalUri}> ;
                <http://ontology.platform/confidence> {request.confidence} .
        }}
        """
        
        await self.graph_db.execute_update(insert_query)
        
        return {
            "success": True,
            "mapping": {
                "externalUri": request.externalUri,
                "internalUri": request.internalUri,
                "relationshipType": request.relationshipType,
                "confidence": request.confidence
            }
        }
    
    async def get_mapping_candidates(
        self,
        request: MappingCandidateRequest
    ) -> Dict:
        """외부 URI와 유사한 내부 URI 후보 추출"""
        
        # 1. 벡터 기반 유사도 계산
        external_embedding = await self.embedding_service.embed(
            request.externalUri
        )
        
        # 2. 상위 N개 후보 찾기
        candidates = await self.graph_db.find_similar_uris(
            external_embedding,
            limit=request.limit
        )
        
        return {
            "externalUri": request.externalUri,
            "candidates": [
                {
                    "internalUri": c['uri'],
                    "similarity": round(c['score'], 3),
                    "label": c.get('label', c['uri'])
                }
                for c in candidates
            ]
        }

@router.post("/mappings")
async def create_mapping(
    request: MappingRequest = Body()
) -> Dict:
    """매핑 생성 API"""
    service = MappingService(graph_db, embedding_service)
    return await service.create_mapping(request)

@router.get("/mapping-candidates")
async def get_mapping_candidates(
    externalUri: str,
    limit: int = 10
) -> Dict:
    """매핑 후보 추출 API"""
    request = MappingCandidateRequest(
        externalUri=externalUri,
        limit=limit
    )
    service = MappingService(graph_db, embedding_service)
    return await service.get_mapping_candidates(request)
```

### 성공 기준 (Task 7-2)
- [ ] 매핑 생성: externalUri → internalUri 트리플 저장
- [ ] 매핑 후보: 벡터 유사도 기반 추천
- [ ] 신뢰도 저장: 매핑에 confidence 메타데이터
- [ ] API 응답: < 200ms (10개 후보)

---

## Task 7-3: Import Preview API

**기간**: 07-11 ~ 07-12 (1.5일)

### 목표

RDF 파일 임포트 전 변경 사항 미리보기

### 구현 항목

```python
# app/routers/import_api.py
from fastapi import APIRouter, UploadFile, File
from typing import List

router = APIRouter(prefix="/api/ontology/import", tags=["Import"])

class ImportPreviewService:
    """RDF 임포트 미리보기"""
    
    def __init__(self, graph_db):
        self.graph_db = graph_db
    
    async def preview_import(
        self,
        rdf_content: str
    ) -> Dict:
        """
        RDF 파일 임포트 미리보기
        
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
        
        # 1. RDF 파싱
        temp_graph = await self._parse_rdf(rdf_content)
        
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
            "suggestedMappings": suggested_mappings[:10]
        }

@router.post("/preview")
async def preview_import(
    file: UploadFile = File()
) -> Dict:
    """RDF 파일 임포트 미리보기"""
    content = await file.read()
    service = ImportPreviewService(graph_db)
    return await service.preview_import(content.decode('utf-8'))
```

### 성공 기준 (Task 7-3)
- [ ] RDF 파싱: Turtle/N-Triples/RDF/XML 지원
- [ ] 새 엔티티 추출: 기존 그래프와 비교
- [ ] 충돌 감지: 중복 클래스, 도메인 불일치 등
- [ ] 매핑 제안: 벡터 유사도 기반 자동 제안

---

## 환경 설정

```bash
# Conda 환경 활성화
conda activate claud_be

# 작업 디렉토리
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend

# 의존성 설치
pip install fastapi rdflib sparqlwrapper sentence-transformers

# 개발 서버
uvicorn main:app --reload --port 8001

# 테스트
pytest tests/phase4/week7_api_test.py -v
```

---

## 성능 목표

| API | 목표 | 측정 기준 |
|-----|------|----------|
| 이웃 탐색 | < 300ms | 100개 노드 |
| 매핑 생성 | < 100ms | 단일 triple |
| 후보 추출 | < 200ms | 10개 후보 |
| Import Preview | < 500ms | 1000 triple |

---

**다음 단계**: Week 7 Codex (프론트엔드 UI 구현)
