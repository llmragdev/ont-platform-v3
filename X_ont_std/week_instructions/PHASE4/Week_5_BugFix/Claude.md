# Phase 4 Week 5: Bug Fix & Test Coverage
## Claude (Backend) 수행 지시서

**기간**: 2026-06-24 ~ 2026-06-28 (4일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 테스트 커버리지 ↑, 엣지 케이스 해결, 백엔드 안정성 강화

---

## Task 5-1: Unit Test Coverage 향상 (목표: ≥95%)

**기간**: 06-24 ~ 06-25 (1.5일)

### 커버리지 분석 (현재: ~85%)

```bash
# 현재 커버리지 측정
pytest --cov=app --cov-report=html tests/

# 주요 미커버리지 영역
- app/services/rdf_converter.py: 82% → 95% 목표
- app/services/ontology_importer.py: 75% → 95% 목표
- app/api/sparql_endpoints.py: 70% → 95% 목표
- app/services/write_back_worker.py: 88% → 95% 목표
```

### 작업 항목

#### 1) RDFConverter 엣지 케이스
```python
# 테스트할 엣지 케이스
def test_entity_to_rdf_with_none_properties():
    """None 속성 처리"""
    entity = {
        'id': 'e1',
        'name': None,
        'properties': {'key': None}
    }
    graph = converter.entity_to_rdf(entity)
    assert graph is not None

def test_rdf_to_entity_with_missing_label():
    """라벨 없는 엔티티"""
    graph = Graph()
    # 라벨 없이 생성
    entity = converter.rdf_to_entity(graph, "http://example.org/e1")
    assert entity['name'] == ''

def test_sparql_query_with_timeout():
    """SPARQL 타임아웃 처리"""
    # 매우 복잡한 쿼리
    query = "SELECT * WHERE { ?s ?p ?o . FILTER(...) . }" * 100
    with pytest.raises(ValueError):
        converter.sparql_query(graph, query)
```

#### 2) OntologyImporter 오류 처리
```python
def test_import_from_dbpedia_with_invalid_uri():
    """잘못된 DBpedia URI"""
    with pytest.raises(Exception):
        await importer.import_from_dbpedia("not-a-uri", "domain")

def test_import_from_wikidata_with_network_error():
    """네트워크 오류 처리"""
    # httpx.ConnectError 모의
    with patch('httpx.AsyncClient.get', side_effect=httpx.ConnectError(...)):
        with pytest.raises(Exception):
            await importer.import_from_wikidata('Q1', 'domain')

def test_merge_entities_with_complex_properties():
    """복잡한 속성 병합"""
    entity1 = {'properties': {'list': [1,2,3]}}
    entity2 = {'properties': {'list': [3,4,5]}}
    merged = await importer.merge_entities(entity1, entity2, 'merge_all')
    assert len(merged['properties']['list']) > 0
```

#### 3) SPARQL API 엣지 케이스
```python
def test_sparql_empty_query():
    """빈 SPARQL 쿼리"""
    response = client.post("/api/sparql/query", params={"query": ""})
    assert response.status_code == 400

def test_sparql_very_large_result():
    """대량 결과 처리 (10000+ rows)"""
    query = "SELECT * WHERE { ?s ?p ?o . }"
    response = client.post("/api/sparql/query", params={"query": query})
    assert response.status_code in [200, 400]

def test_batch_with_mixed_queries():
    """성공/실패 섞인 배치"""
    queries = [
        "SELECT * WHERE { ?s ?p ?o . }",  # 정상
        "INVALID SPARQL",                  # 오류
        "SELECT DISTINCT ?s WHERE { ?s ?p ?o . }"  # 정상
    ]
    response = client.post("/api/sparql/batch", json={"queries": queries})
    assert response.status_code == 200
```

### 테스트 작성 가이드

```python
# 패턴 1: 경계값 테스트
def test_large_entity_id():
    """10000자 이상의 entity_id"""
    entity = {'id': 'x' * 10000, 'name': 'Large'}
    graph = converter.entity_to_rdf(entity)
    assert len(graph) > 0

# 패턴 2: 동시성 테스트
@pytest.mark.asyncio
async def test_concurrent_imports():
    """동시 import 5개"""
    tasks = [
        importer.import_from_wikidata(f'Q{1+i}', f'domain_{i}')
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert len([r for r in results if not isinstance(r, Exception)]) >= 4

# 패턴 3: 리소스 누수 테스트
def test_rdf_converter_memory_leak():
    """대량 변환 후 메모리 해제"""
    import gc
    graphs = [converter.entity_to_rdf({'id': f'e{i}', 'name': f'E{i}'}) for i in range(1000)]
    del graphs
    gc.collect()
    # 메모리 상태 확인
```

### 테스트 목표
- [ ] RDFConverter: 95%+ 커버리지
- [ ] OntologyImporter: 95%+ 커버리지
- [ ] SPARQL API: 95%+ 커버리지
- [ ] 전체: ≥95% 커버리지 달성
- [ ] 0 warnings (Flake8)
- [ ] 0 type errors (mypy)

---

## Task 5-2: 엣지 케이스 & Exception Handling (30개+)

**기간**: 06-25 ~ 06-27 (2일)

### 주요 엣지 케이스

#### 1) 입력 검증 강화
```python
# 현재 상태: 최소한의 검증
# 개선: 상세한 검증

class RDFConverterEnhanced(RDFConverter):
    def validate_entity(self, entity: Dict) -> bool:
        """엔티티 검증"""
        if not entity.get('id'):
            raise ValueError("entity.id 필수")
        if len(entity['id']) > 1000:
            raise ValueError("entity.id는 1000자 이하")
        if not isinstance(entity.get('properties', {}), dict):
            raise ValueError("properties는 dict")
        return True
    
    def validate_sparql_query(self, query: str) -> bool:
        """SPARQL 쿼리 검증"""
        if not query or len(query) > 100000:
            raise ValueError("쿼리 크기 초과")
        # 위험한 UNION 패턴 감지
        if query.count("UNION") > 10:
            raise ValueError("과도한 UNION")
        return True
```

#### 2) 순환 참조 처리
```python
def test_circular_relationships_deep():
    """깊은 순환 관계 (A→B→C→...→Z→A)"""
    # A부터 Z까지 26개 엔티티 체인 + 순환
    entities = {}
    for i in range(26):
        entity_id = chr(65 + i)  # A~Z
        next_id = chr(65 + (i+1) % 26)
        entities[entity_id] = {
            'id': entity_id,
            'relationships': [{'to_entity_id': next_id}]
        }
    
    # 모두 RDF로 변환
    graphs = [converter.entity_to_rdf(e) for e in entities.values()]
    merged = converter.merge_graphs(graphs)
    
    # 순환 구조 검증
    assert len(list(merged.subjects())) == 26
```

#### 3) 리소스 한계 대응
```python
def test_sparql_with_limited_memory():
    """제한된 메모리 환경"""
    # 1GB 이상 쿼리 결과
    large_graph = Graph()
    for i in range(1000000):
        large_graph.add((
            URIRef(f"http://ex.org/{i}"),
            RDF.type,
            URIRef("http://ex.org/Type")
        ))
    
    # 페이징 처리 필요
    # 구현: LIMIT/OFFSET으로 청크 단위 처리
```

#### 4) 동시성 이슈
```python
@pytest.mark.asyncio
async def test_race_condition_entity_merge():
    """동시 merge 경쟁"""
    entity_base = {'id': 'e1', 'properties': {'count': 0}}
    
    async def increment():
        merged = await importer.merge_entities(
            entity_base,
            {'properties': {'count': 1}},
            'merge_all'
        )
        return merged
    
    results = await asyncio.gather(*[increment() for _ in range(100)])
    # 일관성 검증
    assert all(r['id'] == 'e1' for r in results)
```

### 예외 처리 체크리스트
- [ ] ValueError: 입력 검증 실패
- [ ] TimeoutError: SPARQL 쿼리 타임아웃
- [ ] MemoryError: 메모리 부족
- [ ] ConnectionError: 네트워크 오류
- [ ] ParseError: RDF/SPARQL 파싱 실패
- [ ] DuplicateError: 중복 엔티티
- [ ] CircularError: 순환 참조 (감지 및 처리)

---

## Task 5-3: 통합 테스트 & Regression Tests

**기간**: 06-27 ~ 06-28 (1.5일)

### 통합 시나리오 (15개)

```python
# 시나리오 1: 전체 임포트→변환→쿼리 파이프라인
@pytest.mark.integration
async def test_full_pipeline_dbpedia_to_sparql():
    """DBpedia → RDF → SPARQL 전체 흐름"""
    # 1. DBpedia 임포트
    entity = await importer.import_from_dbpedia(
        "http://dbpedia.org/resource/Paris",
        "geography"
    )
    
    # 2. RDF 변환
    graph = converter.entity_to_rdf(entity)
    
    # 3. SPARQL 쿼리
    results = converter.sparql_query(graph, """
        SELECT ?property ?value
        WHERE { ?s ?property ?value }
        LIMIT 10
    """)
    
    assert len(results) > 0

# 시나리오 2: 대량 데이터 처리
@pytest.mark.integration
async def test_batch_import_and_merge():
    """1000개 엔티티 임포트 후 중복 제거"""
    entities = []
    for i in range(1000):
        entity = {
            'entity_id': f'e{i%100}',  # 100개로 압축
            'source': 'test',
            'properties': {'index': i}
        }
        entities.append(entity)
    
    deduplicated = importer.deduplicate_by_uri(entities)
    assert len(deduplicated) == 100

# 시나리오 3: 실패 복구
@pytest.mark.integration
async def test_import_with_fallback():
    """주 소스 실패 시 대체 소스"""
    try:
        # DBpedia 시도 (실패)
        await importer.import_from_dbpedia("invalid", "domain")
    except Exception:
        # Wikidata로 폴백
        entity = await importer.import_from_wikidata('Q1', 'domain')
        assert entity is not None
```

### Regression Tests (10개)

```python
# Week 3.5 WriteBackWorker 호환성
def test_regression_write_back_worker_integration():
    """WriteBackWorker와의 통합"""
    from app.services.write_back_worker import WriteBackWorker
    
    worker = WriteBackWorker(db=db_session)
    result = worker.process_pending()
    assert result['processed'] >= 0

# Week 4 RDF 변환 역호환성
def test_regression_rdf_format_compatibility():
    """RDF 형식 호환성"""
    # Turtle → XML → Turtle
    turtle1 = converter.graph_to_rdf(graph, format='turtle')
    graph2 = converter.rdf_to_graph(turtle1, format='turtle')
    xml = converter.graph_to_rdf(graph2, format='xml')
    assert len(xml) > 0
```

---

## 🎯 성공 기준

- [x] Unit 테스트 커버리지 ≥ 95%
- [x] 30+ 엣지 케이스 테스트
- [x] 15개 통합 시나리오
- [x] 10개 회귀 테스트
- [x] 0 Flake8 경고
- [x] 0 mypy 타입 에러
- [x] 전체 50+ 새 테스트

---

## 📊 테스트 실행

```bash
# 커버리지 리포트
pytest --cov=app --cov-report=html tests/

# 린팅
flake8 app/ --max-line-length=100
mypy app/ --strict

# 전체 테스트
pytest tests/ -v --tb=short
```

---

## ⏭️ 다음 주차 준비

- Alembic 마이그레이션 상태 확인
- PostgreSQL 테이블 인덱싱 최적화
- 성능 기준선 데이터 준비

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_5_BugFix/Claude.md`
- 테스트: `tests/test_phase4_week5_bugfix.py`

---

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/claude/YYYYMMDD_PHASE4_WEEK5_Claude_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260628_1830_PHASE4_WEEK5_Claude_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Task 5-1~5-3" 섹션 → 실제 완료 항목만 체크
   - "테스트 결과" 표 → 실제 테스트 통과 결과 입력
   - "커버리지" → 실제 pytest 결과 입력

---

**상태**: Task 5-1~5-3 준비 완료  
**예상 완료**: 2026-06-28 (금요일 오후)  
**다음 주차**: Week 6 Performance Optimization

---

## 📋 보고서 저장 & 통합 지시

### 개별 보고서 경로 (필수)

**각 에이전트는 작업 완료 후 다음 경로에 보고서를 저장합니다:**

| 에이전트 | 저장 경로 | 예시 |
|---------|---------|------|
| **Claude** | `task_logs/claude/YYYYMMDD_HHMM_PHASE4_WEEK5_Claude_Complete.md` | `20260628_1830_PHASE4_WEEK5_Claude_Complete.md` |
| **Codex** | `task_logs/codex/YYYYMMDD_HHMM_PHASE4_WEEK5_Codex_Complete.md` | `20260628_1830_PHASE4_WEEK5_Codex_Complete.md` |
| **Antigravity** | `task_logs/antigravity/YYYYMMDD_HHMM_PHASE4_WEEK5_Antigravity_Complete.md` | `20260628_1830_PHASE4_WEEK5_Antigravity_Complete.md` |

### 통합 보고서 (Claude 담당) ⭐

**Claude는 3개 에이전트 보고서를 모니터링하다가 모두 완료되면 최종 통합 보고서를 작성합니다:**

| 항목 | 내용 |
|------|------|
| **저장 경로** | `task_logs/consolidated/YYYYMMDD_HHMM_PHASE4_WEEK5_Consolidated_Report.md` |
| **작성 시기** | 3개 에이전트 보고서 모두 제출 후 |
| **예시** | `20260628_2000_PHASE4_WEEK5_Consolidated_Report.md` |
| **포함 내용** | Executive Summary + Claude/Codex/Antigravity 작업 결과 + 통합 테스트 결과 + 성능 지표 |

**⚠️ Claude의 모니터링 체크리스트:**
- [ ] Claude 보고서 생성됨: `task_logs/claude/` 확인
- [ ] Codex 보고서 생성됨: `task_logs/codex/` 확인
- [ ] Antigravity 보고서 생성됨: `task_logs/antigravity/` 확인
- [ ] 3개 보고서 모두 확인 후 통합 보고서 작성
- [ ] 통합 보고서 저장: `task_logs/consolidated/`
