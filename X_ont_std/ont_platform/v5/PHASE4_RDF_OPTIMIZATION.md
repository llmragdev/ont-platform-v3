# RDF/SPARQL 성능 최적화 전략

본 문서는 Phase 4 Week 4 성능 최적화(Performance) 설계의 핵심 산출물로서, v4 RDF 플랫폼 하에서의 SPARQL 질의 속도 향상, Cytoscape.js 기반 대규모 그래프(1000+ 노드) 시각화 렌더링 최적화, 외부 소스 Import 성능 병목 제거 및 향후 Week 5-8 단계에서 실행할 25개의 구체적인 성능 시나리오 계획을 정의합니다.

---

## 1. SPARQL 쿼리 최적화

SPARQL 엔진(e.g., rdflib, Oxigraph)의 실행 속도 및 쿼리 플래너의 효율성을 높이기 위한 최적화 전략입니다.

### 1.1 쿼리 플래너 최적화 (Query Planner Optimization)
SPARQL 질의 시 그래프 패턴 매칭의 순서(Triple Pattern Ordering)를 최적화하여 중간 결과셋(Intermediate Result Set)의 크기를 최소화합니다.

*   **최적화 원칙**:
    1.  **가장 제약 조건이 강한(Selective) 패턴을 최상단에 배치**: 매칭되는 주어(Subject) 또는 목적어(Object)의 수가 가장 적은 패턴부터 먼저 매칭하여 조인 대상 트리플 수를 크게 줄입니다.
    2.  **공유 변수를 통한 빠른 바인딩**: 선행 트리플 패턴에서 상수로 고정되거나 바인딩된 변수를 후속 패턴의 주어나 술어에 빠르게 전파합니다.
    3.  **FILTER 및 BIND 연산 지연**: 가능한 한 패턴 매칭이 끝난 후 또는 필요한 매칭 직후에 FILTER를 수행하되, 단순 값 비교의 경우 조인 전에 미리 필터링되도록 작성 순서를 제어합니다.

```sparql
# [최적화 전]: 대규모 데이터셋에서 불필요한 카티션 곱 또는 과도한 중간 조인을 유발하는 패턴
SELECT ?person ?friend ?workplace WHERE {
    ?person foaf:knows ?friend .               # (1) 1-hop 관계: 결과 매칭이 매우 많음
    ?friend foaf:workplaceHomepage ?workplace . # (2) 2-hop 관계: 중간 조인 발생
    ?person rdf:type foaf:Person .              # (3) 가장 제약이 약한 타입 정의가 아래에 있음
    ?person foaf:name ?name .                   # (4) 이름 바인딩
    FILTER (strstarts(?name, "Admin"))          # (5) 필터가 최하단에 적용되어 중간 조인 비대화
}

# [최적화 후]: 제약이 강한 조건(Type, Name Filter)을 먼저 바인딩하여 횡단하는 경로 제한
SELECT ?person ?friend ?workplace WHERE {
    ?person rdf:type foaf:Person .              # (1) 타겟 인스턴스 범위 제한
    ?person foaf:name ?name .                   # (2) 이름 바인딩
    FILTER (strstarts(?name, "Admin"))          # (3) 필터를 즉시 적용하여 ?person 후보군을 극단적으로 축소
    ?person foaf:knows ?friend .               # (4) 제한된 ?person에 대해서만 knows 관계 추적
    ?friend foaf:workplaceHomepage ?workplace . # (5) 마지막 최소 매칭 대상만 2-hop 조인
}
```

### 1.2 인덱싱 전략 (Indexing Strategy)
메모리 및 영구 저장소에 트리플 데이터를 저장할 때 다방면의 탐색 경로를 가속화하기 위해 3방향 기본 인덱스를 설계 및 구현합니다.

1.  **SPO (Subject-Predicate-Object) 인덱스**:
    *   **용도**: 특정 주어(S)의 모든 속성과 관계를 조회할 때 최적 (`SELECT ?p ?o WHERE { :subject ?p ?o }`)
    *   **설명**: 가장 기본적인 인덱스로, 엔티티의 상세 메타데이터나 속성 집합을 로드할 때 활용됩니다.
2.  **OSP (Object-Subject-Predicate) 인덱스**:
    *   **용도**: 특정 객체/값(O)을 가리키는 주어들을 역방향으로 조회할 때 최적 (`SELECT ?s ?p WHERE { ?s ?p :object }`)
    *   **설명**: 특정 태그를 공유하는 노드 목록 조회 또는 외부 온톨로지(DBpedia/Wikidata URI)를 참조하는 로컬 엔티티의 역방향 매핑 확인 시 유용합니다.
3.  **PSO (Predicate-Subject-Object) 인덱스**:
    *   **용도**: 특정 관계/속성(P)에 해당하는 주어와 목적어의 쌍을 전역적으로 스캔할 때 최적 (`SELECT ?s ?o WHERE { ?s rdf:type :Class }`)
    *   **설명**: 특정 타입의 인스턴스를 일괄 열거하거나, 특정 엣지(e.g., `foaf:knows`)를 가진 관계망 전체를 시각화 레이아웃에 로드할 때 쿼리 지연을 최소화합니다.

### 1.3 쿼리 재작성 규칙 (Query Rewriting Rules)
SPARQL 엔진의 연산 부하를 제어하기 위해 시스템이 쿼리를 실행하기 전 자동으로 최적의 형태로 재작성(Rewrite)합니다.

*   **UNION을 FILTER IN으로 변환**:
    *   *이유*: `UNION`은 내부적으로 여러 서브 쿼리를 실행한 후 결과셋을 합치기 때문에 다중 스캔이 발생합니다. 동일 변수의 다중 값 바인딩은 `FILTER IN` 또는 `VALUES` 구문으로 통합하여 단일 스캔으로 처리합니다.
    ```sparql
    # [재작성 전]
    SELECT ?x WHERE {
        { ?x rdf:type foaf:Person } UNION { ?x rdf:type foaf:Organization }
    }
    
    # [재작성 후]
    SELECT ?x WHERE {
        ?x rdf:type ?type .
        FILTER (?type IN (foaf:Person, foaf:Organization))
    }
    ```
*   **OPTIONAL 패턴의 BIND 결합**:
    *   *이유*: 다중 `OPTIONAL`은 조인 곱을 유발하므로 필수 매칭 패턴 내부로 통합하거나, 기본값 바인딩(`COALESCE`)을 활용하여 지연 연산을 방지합니다.

---

## 2. 그래프 시각화 성능 최적화

프론트엔드 Cytoscape.js를 통해 1000개 이상의 노드와 복잡한 엣지를 렌더링할 때 브라우저 렉(Lag)을 방지하고 FPS(Frames Per Second)를 60대로 유지하기 위한 시각화 렌더링 최적화 설계입니다.

### 2.1 Cytoscape.js 렌더링 최적화 기법

1.  **뷰포트 컬링 (Viewport Culling)**:
    *   현재 화면(Viewport) 영역을 벗어난 노드 및 엣지는 GPU/CPU 렌더링 루프에서 동적으로 숨김(`display: none` 또는 `.hide()`) 처리합니다.
    *   사용자가 Pan(화면 이동) 또는 Zoom(확대/축소)할 때 이벤트 디바운싱(Debounce, 100ms)을 적용하여 화면 범위 내 노드만 가시성을 토글합니다.
2.  **레이아웃 캐싱 (Layout Caching)**:
    *   Dagre, CoSE 등의 포스-디렉티드(Force-directed) 레이아웃 연산은 O(N^2) 이상의 복잡도를 가집니다.
    *   그래프의 위상 구조(Topology)가 변경되지 않았다면 최초 1회 계산된 노드의 x, y 좌표값 배열을 브라우저 로컬 저장소 또는 Redis에 캐싱하여 다음 렌더링 시 연산 없이 즉시 배치합니다.
3.  **배치 스타일 업데이트 (Batching Updates)**:
    *   여러 노드 또는 엣지의 스타일이나 상태를 변경할 때 브라우저 리플로우(Reflow)가 매번 발생하는 것을 막기 위해 `cy.batch()` 내에서 한 번에 묶어 실행합니다.

```javascript
// 프론트엔드 최적화 구현 패턴 예시
cy.batch(() => {
    // 1000개 노드의 스타일을 한 번에 업데이트하여 리플로우 비용을 단 1회로 단축
    nodes.forEach(node => {
        node.style({
            'background-color': '#4A90E2',
            'border-width': '2px',
            'label': node.data('label')
        });
    });
});
```

### 2.2 계층적 확대 (LOD: Level of Detail / Progressive Disclosure)
대규모 그래프(1000+ 노드)를 한 번에 화면에 그릴 경우 가독성과 성능이 모두 저하됩니다. 줌 레벨에 따라 데이터의 상세도를 조절합니다.

*   **단계별 로드 정책**:
    *   **초기 상태 (Zoom < 0.5)**: 핵심 중요 노드(Degree가 높은 노드)와 최상위 클래스 노드만 노출 (약 50개 노드로 요약)
    *   **중간 단계 (Zoom 0.5 ~ 1.2)**: 마우스 휠로 확대 시, 중심 2-hop 이내의 상세 관계 노드들을 비동기 로딩하여 추가 렌더링 (약 150-300개 노드)
    *   **상세 단계 (Zoom > 1.2)**: 특정 영역 집중 시, 해당 영역 주변의 모든 속성 노드 및 리터럴 값 노출 (개별 도메인 밀집 영역 탐색)

### 2.3 렌더링 정보 캐싱 전략
*   **GraphLayout 캐시**:
    *   *Key*: `graph_layout:{graph_id}:{zoom_level}`
    *   *TTL*: 1시간
    *   *효과*: 레이아웃 좌표 재활용을 통해 대규모 그래프 로딩 시 레이아웃 배치 연산 속도 90% 이상 절감.
*   **NodePosition 캐시**:
    *   *Key*: `node_positions:{node_id}:{viewport_boundary}`
    *   *TTL*: 30분

---

## 3. 성능 영향도 추정 및 우선순위

각 최적화 항목이 전체 시스템 성능에 미칠 것으로 예상되는 영향도와 구현 우선순위는 다음과 같습니다.

| 최적화 항목 | 예상 개선도 | 우선순위 | 리스크 및 영향 범위 |
| :--- | :--- | :--- | :--- |
| **SPARQL 쿼리 플래너 최적화** | 40% ~ 50% 응답 시간 단축 | 1순위 (필수) | 저리스크 / 쿼리 작성 스타일 가이드화 필요 |
| **RDF 3방향 인덱싱 (SPO/OSP/PSO)** | 60% ~ 70% 조회 속도 개선 | 1순위 (필수) | 중리스크 / 메모리 사용량 증가 (인덱스 유지 비용) |
| **외부 Import 배치 및 중복 제거** | 80% 이상의 Import 지연 감소 | 1순위 (필수) | 저리스크 / 외부 API 스로틀링 회피 |
| **시각화 뷰포트 컬링 & 배치 스타일** | 브라우저 FPS 15 → 60 개선 | 2순위 (중요) | 중리스크 / 화면 전환 시 미세한 팝인(Pop-in) 현상 |
| **계층적 LOD 그래프 뷰어** | 초기 렌더링 속도 90% 이상 절감 | 2순위 (중요) | 고리스크 / 프론트엔드 비동기 상태 관리 복잡성 |
| **SPARQL 결과 캐싱 (Redis)** | 70% ~ 80% 반복 질의 즉각 응답 | 3순위 (선택) | 중리스크 / 그래프 갱신 시 캐시 정합성(Eviction) 관리 |

---

## 4. 외부 Import 성능 최적화

### 4.1 배치 Import 프로세스 최적화
외부 온톨로지(Wikidata, DBpedia)에서 수만 개의 트리플 데이터를 로컬 저장소로 수입할 때의 병목을 제어합니다.
1.  **사전 중복 제거 (O(N) 스캔)**:
    *   가져올 URI 목록 중 로컬 RDF 저장소나 메타데이터 DB에 이미 존재하는 URI는 네트워크 요청 전 해시 셋을 활용해 사전 필터링합니다.
2.  **동시성 제어 및 병렬 커넥션**:
    *   동시에 실행되는 외부 HTTP 요청 수를 최대 5개(Semaphore limit = 5)로 제한하여 대상 서버의 IP 차단 및 API 스로틀링을 방지하고 네트워크 안정성을 유지합니다.
3.  **트랜잭션 청크 배치 (Chunking)**:
    *   트리플 쓰기(Write) 작업을 100개 또는 500개 단위의 세션/트랜잭션 단위로 묶어 처리함으로써 파일 쓰기 및 영크락 커밋 횟수를 줄입니다.
4.  **인덱스 빌드 지연**:
    *   대량 임포트가 진행되는 동안에는 트리플 인덱스 갱신을 일시 중단하고, 임포트 작업이 완료된 최종 시점에 배치로 인덱스를 벌크 빌드합니다.

### 4.2 네트워크 및 파싱 최적화
*   **Wikidata JSON API**: JSON 엔티티 페이로드를 스트리밍 파서(ijson 등)로 파싱하여 메모리 점유율을 최소화합니다.
*   **로컬 RDF 파일**: 대용량 Turtle/RDF/XML 파일 로드 시 전체 파일을 메모리에 로드하지 않고 청크(Chunk) 단위로 읽는 스트리밍 파서 파이프라인을 구축합니다.

---

## 5. Week 5-8 성능 테스트 시나리오 계획 (25개 시나리오)

성능 설계가 실질적으로 잘 동작하는지 검증하기 위해, Week 5-8 단계에서 수행할 구체적인 25가지 부하 및 성능 시나리오를 구성합니다.

### 5.1 대규모 RDF 데이터 로딩 시나리오 (5개)
*   **TC-LOD-01**: 10K 트리플 RDF 파일(Turtle) 로딩 시간 및 가용 메모리 증가량 측정 (SLA: < 200ms)
*   **TC-LOD-02**: 100K 트리플 RDF 파일 로딩 시간 및 메모리 한계점 측정 (SLA: < 1.0초)
*   **TC-LOD-03**: 1M 트리플 대용량 RDF 파일 로딩 시간 및 OOM(Out of Memory) 발생 여부 검증 (SLA: < 5.0초)
*   **TC-LOD-04**: 벌크 로드 중 시스템 비정상 종료 시 복구 무결성 검증 (데이터 정합성 깨짐 여부)
*   **TC-LOD-05**: 바이너리 RDF 포맷(e.g., HDT) 도입 시 텍스트 파싱 대비 로딩 시간 개선율 비교

### 5.2 SPARQL 쿼리 성능 시나리오 (5개)
*   **TC-SPQ-01**: 100K 트리플 기준 단순 SELECT 질의의 지연 시간 측정 (SLA: < 50ms)
*   **TC-SPQ-02**: 2-hop 및 3-hop 복합 JOIN 쿼리 질의 시 쿼리 플래너 최적화 전후 Latency 비교 (SLA: 3-hop < 300ms)
*   **TC-SPQ-03**: 다중 `OPTIONAL` 패턴이 3개 이상 중첩된 쿼리 실행 시 조인 지연 및 쿼리 플래너의 실행 계획 시간 검증
*   **TC-SPQ-04**: 대규모 데이터셋(1M)에서 복합 정렬(`ORDER BY`) 및 페이징(`LIMIT`/`OFFSET`) 쿼리 수행 시 응답 성능 측정
*   **TC-SPQ-05**: `CONSTRUCT` 쿼리를 통한 새로운 그래프 세그먼트 생성 및 가공 시 지연 시간 측정 (SLA: < 400ms)

### 5.3 외부 온톨로지 수입(Import) 부하 시나리오 (5개)
*   **TC-IMP-01**: DBpedia 엔드포인트 대상 10개 엔티티 실시간 수입 시 API 지연 시간 및 파싱 속도 측정 (SLA: < 5초)
*   **TC-IMP-02**: Wikidata API 대상 100개 엔티티 배치 임포트 시 병렬 커넥션(5개 제한) 안정성 및 누수 여부 검증 (SLA: < 10초)
*   **TC-IMP-03**: 존재하지 않거나 잘못된 형식의 외부 URI 임포트 요청 시 예외 처리 속도 및 시스템 전파 지연 측정
*   **TC-IMP-04**: 대량 임포트 중복 유입 시 사전 중복 제거(Deduplication Set)의 중복 필터링 성공률 및 오버헤드 측정 (100% 필터링)
*   **TC-IMP-05**: 1,000개 이상의 연속 임포트 배치 작업 시 메모리 누수(Memory Leak) 프로파일링 및 가비지 컬렉션(GC) 추이 분석

### 5.4 캐싱 및 인덱싱 무결성 시나리오 (5개)
*   **TC-CCH-01**: Redis 기반 SPARQL 결과 캐시 히트율(Target: ≥80%) 달성 여부 및 캐시 적중 시 응답 속도 검증 (SLA: < 10ms)
*   **TC-CCH-02**: RDF 그래프 업데이트(트리플 추가/삭제) 시 연관된 캐시 세그먼트의 완전 무효화(Cache Invalidation) 정합성 검증
*   **TC-CCH-03**: 캐시 만료 시점에 대량의 동일 쿼리 유입 시 Cache Stampede(캐시 허리케인) 방지 메커니즘 동작 검증
*   **TC-CCH-04**: 3방향 인덱스(SPO, OSP, PSO) 적용 시 단일 쿼리 탐색 경로에 인덱스가 정상 할당되는지 인덱스 효율 검증 (Target: ≥95%)
*   **TC-CCH-05**: 다중 스레드 동시 읽기/쓰기 환경에서 RDF 그래프 락(Lock) 경합 최소화 및 데드락(Deadlock) 방지 상태 검증

### 5.5 시각화 렌더링 성능 시나리오 (5개)
*   **TC-VIS-01**: Cytoscape.js에서 100개 노드/300개 엣지 로딩 및 레이아웃 배치 속도 측정 (SLA: < 100ms)
*   **TC-VIS-02**: 1,000개 노드/3,000개 엣지 대규모 그래프 초기 렌더링 시 레이아웃 캐시 적용 유무에 따른 프레임 드랍(FPS) 비교 (SLA: 레이아웃 캐시 활용 시 < 300ms)
*   **TC-VIS-03**: 5,000개 노드 극단적 대규모 그래프 로딩 시 뷰포트 컬링(Culling)에 의한 렌더링 메모리 절감율 및 FPS 변화 검증 (Target: 60 FPS 유지)
*   **TC-VIS-04**: 계층적 LOD(Level of Detail) 줌 레벨 조정 시 노드/엣지 디테일 추가 로드에 걸리는 동적 렌더링 지연 속도 측정 (SLA: < 150ms)
*   **TC-VIS-05**: 대규모 그래프 렌더링 후 드래그, 줌인, 줌아웃 연속 수행 시 CPU 점유율 및 브라우저 가비지 컬렉션(GC) 주기 분석
