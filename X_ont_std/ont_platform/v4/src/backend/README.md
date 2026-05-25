# ont_platform v4 - Ontology Extension API (Week 7)

## 개요

Phase 4 Week 7의 온톨로지 확장 기능을 위한 FastAPI 백엔드 구현입니다.

**3가지 핵심 기능**:
1. **Task 7-1: RDF 그래프 이웃 탐색** - 1-hop/2-hop 그래프 탐색
2. **Task 7-2: 온톨로지 매핑** - 자동 매핑 생성 및 후보 추출
3. **Task 7-3: Import Preview** - RDF 파일 임포트 전 미리보기

---

## 설치 및 실행

### 1. 환경 설정

```bash
# Conda 환경 활성화
conda activate claud_be

# 작업 디렉토리로 이동
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend

# 의존성 설치
pip install -r requirements.txt
```

### 2. 개발 서버 실행

```bash
# 포트 8001에서 실행
python main.py

# 또는 uvicorn으로 직접 실행
uvicorn main:app --reload --port 8001
```

서버가 시작되면:
- **API 문서**: http://localhost:8001/docs (Swagger UI)
- **API 스키마**: http://localhost:8001/openapi.json
- **루트**: http://localhost:8001/

---

## API 엔드포인트

### Task 7-1: RDF 이웃 탐색

```bash
GET /api/ontology/rdf/neighborhood/{uri}
```

**파라미터**:
- `uri`: 중심 노드 URI
- `depth`: 탐색 깊이 (1 또는 2, 기본값: 1)
- `limit`: 반환할 최대 노드 수 (기본값: 100)

**예제**:
```bash
curl "http://localhost:8001/api/ontology/rdf/neighborhood/http://example.org/concept/1?depth=1&limit=100"
```

**응답**:
```json
{
  "centerNode": "http://example.org/concept/1",
  "nodes": [
    {
      "id": "http://example.org/concept/2",
      "label": "Concept 2",
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
  "totalNodeCount": 1,
  "totalEdgeCount": 1
}
```

---

### Task 7-2: 매핑 생성

```bash
POST /api/ontology/mappings
```

**요청 본문**:
```json
{
  "externalUri": "http://external.org/concept/1",
  "internalUri": "http://internal.org/concept/1",
  "relationshipType": "skos:exactMatch",
  "confidence": 0.95
}
```

**예제**:
```bash
curl -X POST "http://localhost:8001/api/ontology/mappings" \
  -H "Content-Type: application/json" \
  -d '{
    "externalUri": "http://external.org/concept/1",
    "internalUri": "http://internal.org/concept/1",
    "relationshipType": "skos:exactMatch",
    "confidence": 0.95
  }'
```

**응답**:
```json
{
  "success": true,
  "mapping": {
    "externalUri": "http://external.org/concept/1",
    "internalUri": "http://internal.org/concept/1",
    "relationshipType": "skos:exactMatch",
    "confidence": 0.95
  }
}
```

---

### Task 7-2: 매핑 후보 추출

```bash
GET /api/ontology/mapping-candidates
```

**파라미터**:
- `externalUri`: 외부 URI (필수)
- `limit`: 반환할 최대 후보 수 (기본값: 10)

**예제**:
```bash
curl "http://localhost:8001/api/ontology/mapping-candidates?externalUri=http://external.org/concept/1&limit=5"
```

**응답**:
```json
{
  "externalUri": "http://external.org/concept/1",
  "candidates": [
    {
      "internalUri": "http://internal.org/concept/1",
      "similarity": 0.95,
      "label": "Concept 1"
    },
    {
      "internalUri": "http://internal.org/concept/2",
      "similarity": 0.85,
      "label": "Concept 1 Alternative"
    }
  ]
}
```

---

### Task 7-3: Import Preview

```bash
POST /api/ontology/import/preview
```

**요청**:
- 파일 업로드 (multipart/form-data)
- 지원 포맷: Turtle, RDF/XML, N-Triples, JSON-LD

**예제** (curl):
```bash
curl -X POST "http://localhost:8001/api/ontology/import/preview" \
  -F "file=@ontology.ttl"
```

**응답**:
```json
{
  "newTripleCount": 1000,
  "newEntityCount": 150,
  "potentialConflicts": [
    {
      "externalUri": "http://new.org/concept/1",
      "internalUri": "http://existing.org/concept/1",
      "conflictType": "duplicate_class",
      "severity": "high",
      "reason": "Label 'Concept 1' matches existing URI"
    }
  ],
  "suggestedMappings": [
    {
      "externalUri": "http://new.org/concept/1",
      "internalUri": "http://existing.org/concept/1",
      "similarity": 0.95,
      "reason": "Label match: Concept 1",
      "relationshipType": "skos:exactMatch"
    }
  ],
  "parseSuccess": true
}
```

---

### Task 7-3: 실제 Import

```bash
POST /api/ontology/import
```

**파라미터**:
- `file`: RDF 파일
- `applyMappings`: 제안된 매핑 자동 적용 여부 (기본값: true)

**예제**:
```bash
curl -X POST "http://localhost:8001/api/ontology/import" \
  -F "file=@ontology.ttl" \
  -F "applyMappings=true"
```

---

## 프로젝트 구조

```
ont_platform/v4/src/backend/
├── main.py                          # FastAPI 진입점
├── requirements.txt                 # 의존성
├── README.md                        # 이 파일
│
├── app/
│   ├── __init__.py
│   ├── services/                    # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── neighborhood_service.py  # Task 7-1 서비스
│   │   ├── mapping_service.py       # Task 7-2 서비스
│   │   └── import_preview_service.py # Task 7-3 서비스
│   │
│   └── routers/                     # FastAPI 라우터
│       ├── __init__.py
│       └── ontology_api.py          # 모든 API 엔드포인트
│
└── tests/
    ├── __init__.py
    ├── conftest.py                  # pytest 설정
    └── test_week7_ontology_api.py   # 통합 테스트
```

---

## 테스트 실행

### 단위 테스트

```bash
# 모든 테스트 실행
pytest tests/ -v

# 특정 테스트 클래스만 실행
pytest tests/test_week7_ontology_api.py::TestNeighborhoodAPI -v

# 특정 테스트 함수만 실행
pytest tests/test_week7_ontology_api.py::TestNeighborhoodAPI::test_neighborhood_service_initialization -v
```

### 성능 벤치마크

```bash
# 벤치마크 마크된 테스트 실행
pytest tests/test_week7_ontology_api.py::TestPerformance -v --benchmark-only
```

---

## 주요 구현 패턴

### 1. Batch Transaction (Task 7-2)

매핑 저장 시 여러 INSERT를 한 번의 SPARQL 호출로 묶음:

```python
# 코드 예: mapping_service.py의 _build_insert_mapping_query()
INSERT DATA {
    GRAPH <http://ontology.platform/graphs/mappings> {
        <external_uri> <relationship_type> <internal_uri> ;
            <http://ontology.platform/confidence> <confidence> .
    }
}
```

### 2. Incremental Reasoning (Task 7-1)

1-hop/2-hop만 탐색하여 성능 최적화:

```python
# 코드 예: neighborhood_service.py의 _build_neighborhood_query()
# depth=1: 직접 이웃만 조회
# depth=2: 이웃의 이웃까지 조회 (제한적)
```

### 3. Named Graph 격리 (Task 7-3)

임포트 결과를 staging 그래프에 먼저 저장:

```sparql
GRAPH <http://ontology.platform/graphs/inferred/session_{id}> {
    -- Import preview 결과 저장
}
```

---

## 환경 변수 (선택)

`.env` 파일에서 다음을 설정할 수 있습니다:

```bash
# GraphDB 연결 (필요시)
GRAPH_DB_HOST=localhost
GRAPH_DB_PORT=7200
GRAPH_DB_REPOSITORY=ontology

# 임베딩 서비스 (선택)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## 다음 단계

1. **GraphDB 연결**
   - 실제 RDF 저장소 (GraphDB, Virtuoso, Fuseki 등)와 연결
   - `graph_db` 인터페이스 구현

2. **벡터 임베딩 통합**
   - embedding_service 구현 및 연결
   - 벡터 유사도 기반 매핑 후보 추출

3. **프론트엔드 연동**
   - Codex.md의 React 컴포넌트와 연동
   - CORS, 인증 추가

4. **배포**
   - Docker 컨테이너화
   - 프로덕션 설정 (Gunicorn, Nginx 등)

---

## 참고 문서

- **Claude.md**: 백엔드 구현 지시서
- **Codex.md**: 프론트엔드 구현 지시서
- **Antigravity.md**: 성능 최적화 가이드
- **BACKEND_ARCHITECTURE_ENTERPRISE_REVIEW.md**: 엔터프라이즈 아키텍처 패턴

---

## 문제 해결

### GraphDB 연결 오류

```python
# graph_db가 None인 경우, Mock으로 대체 가능
mock_graph_db = AsyncMock()
service = NeighborhoodService(mock_graph_db)
```

### SPARQL 쿼리 오류

- 쿼리 문법 확인
- 네임스페이스 선언 확인
- GraphDB 쿼리 편집기에서 테스트

### 임베딩 서비스 오류

- sentence-transformers 설치 확인
- 모델 다운로드 (첫 실행 시 자동)

---

**작성일**: 2026-05-25  
**버전**: 0.4.0  
**상태**: ✅ 구현 완료
