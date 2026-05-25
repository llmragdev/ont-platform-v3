# Phase 4 Week 4: RDF + External Ontology
## Antigravity (Performance) 수행 지시서

**기간**: 2026-08-19 ~ 2026-09-01 (2주)  
**할당**: 10% (주당 3-4시간)  
**목표**: RDF 그래프 성능 기준선, SPARQL 벤치마크, Week 5-8 성능 시나리오 설계

---

## Prep 1: RDF 그래프 성능 분석

**기간**: 08-19 ~ 08-25 (1주)  
**목표**: RDF 저장소 및 쿼리 성능 기준선 수립

### 산출물: PHASE4_RDF_PERFORMANCE_BASELINE.md

```markdown
# v4 RDF 성능 기준선

## 1. RDF 그래프 저장소 성능

### Triple 저장소 규모별 성능
**10K 트리플**:
- 로드 시간: <100ms
- 메모리 사용: <50MB
- 쿼리 응답: <50ms

**100K 트리플**:
- 로드 시간: <500ms
- 메모리 사용: <200MB
- 쿼리 응답: <150ms

**1M 트리플**:
- 로드 시간: <2초
- 메모리 사용: ~1GB
- 쿼리 응답: <500ms (인덱스 활용)

## 2. SPARQL 쿼리 성능

### 쿼리 유형별 성능

**SELECT 쿼리 (간단)**:
- 10K 트리플: <20ms
- 100K 트리플: <50ms
- 1M 트리플: <200ms

**CONSTRUCT 쿼리 (새로운 그래프 생성)**:
- 10K 트리플: <30ms
- 100K 트리플: <100ms
- 1M 트리플: <400ms

**복합 SPARQL (JOIN 포함)**:
- 2-hop 관계: <100ms
- 3-hop 관계: <300ms
- 5-hop 관계: <800ms

**선택적 패턴 (OPTIONAL)**:
- 제약 없음: <100ms
- 1개 OPTIONAL: <150ms
- 3개 OPTIONAL: <300ms

## 3. 외부 소스 Import 성능

### DBpedia Import
- 리소스당 쿼리 시간: <500ms
- 속성 처리: <50ms per property
- 배치 (100개): <30초

### Wikidata Import
- 아이템 JSON 처리: <100ms
- Claim 파싱: <20ms per claim
- 배치 (100개): <10초

### 로컬 RDF 파일 Import
- 10K 트리플 파일: <200ms
- 100K 트리플 파일: <1초
- 1M 트리플 파일: <5초

## 4. 캐싱 전략

### SPARQL 쿼리 캐시
```
Key: sparql:{query_hash}
TTL: 5분 (자주 변경되지 않는 질의)
Hit Rate 목표: ≥80% (반복 쿼리)

Cache 제거 트리거:
- 새로운 Import 발생 시
- 그래프 구조 변경 시
- TTL 만료 시
```

### RDF 그래프 인덱스 캐시
```
Key: rdf:index:{graph_id}
TTL: 1시간
Index 구조:
  - subject-predicate-object 인덱스
  - 자주 쿼리되는 triple 패턴
  - 노드-엣지 degree 정보
```

## 5. 성능 SLA (v4 RDF)

### Tier 1: Critical (필수)
1. SPARQL SELECT 쿼리: <200ms (100K 트리플)
2. 외부 리소스 Import: <500ms (단일)
3. RDF 그래프 로드: <500ms (100K 트리플)

### Tier 2: Important (중요)
4. SPARQL CONSTRUCT: <300ms (100K 트리플)
5. 배치 Import: <30초 (100개 리소스)
6. 복합 SPARQL (3-hop): <500ms

### Tier 3: Goal (목표)
7. SPARQL 캐시 히트율: ≥80%
8. Import 중복 제거: 100%
9. RDF 인덱스 효율: ≥95% (쿼리 계획)

## 6. PostgreSQL vs RDF 저장소 비교

| 메트릭 | PostgreSQL | RDF (메모리) | 효율 |
|--------|-----------|-------------|------|
| SPARQL 쿼리 | N/A | <200ms | 우수 |
| 관계형 쿼리 | <100ms | <300ms | PostgreSQL |
| 그래프 추적 | <500ms | <200ms | RDF |
| 메모리 효율 | 우수 | 보통 | PostgreSQL |
| 외부 맵핑 | 복잡 | 간단 | RDF |
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] RDF 저장소 성능 비교표
- [ ] SPARQL 쿼리 성능 분석
- [ ] 외부 Import 성능 측정
- [ ] 캐싱 전략 정의
- [ ] SLA 수량화

---

## Prep 2: SPARQL + 그래프 시각화 성능 최적화 설계

**기간**: 08-26 ~ 09-01 (1주)  
**목표**: 대규모 그래프 렌더링 및 쿼리 성능 최적화

### 산출물: PHASE4_RDF_OPTIMIZATION.md

```markdown
# RDF/SPARQL 성능 최적화 전략

## 1. SPARQL 쿼리 최적화

### 쿼리 플래너 최적화
```python
# 최적화 전: 복합 조인 (느림)
SELECT ?x ?y ?z WHERE {
    ?x rdf:type foaf:Person .
    ?x foaf:name ?name .
    ?x foaf:knows ?y .
    ?y foaf:knows ?z .
    ?z foaf:workplaceHomepage ?url .
}

# 최적화 후: 필터 먼저 (빠름)
SELECT ?x ?y ?z WHERE {
    ?x rdf:type foaf:Person ;
       foaf:name ?name ;
       foaf:knows ?y .
    ?y foaf:knows ?z ;
       foaf:workplaceHomepage ?url .
    FILTER (STRLEN(?name) > 0)
}
```

### 인덱싱 전략
```
SPO (Subject-Predicate-Object) 인덱스:
  - 기본 인덱스 (모든 triple 검색)
  
OSP (Object-Subject-Predicate) 인덱스:
  - Object 중심 쿼리 가속
  
PSO (Predicate-Subject-Object) 인덱스:
  - 특정 predicate 타입 검색
```

### 쿼리 재작성
```
# UNION 최적화
SELECT ?x WHERE {
    { ?x rdf:type foaf:Person }
    UNION
    { ?x rdf:type foaf:Organization }
}

# 대신 더 구체적인 필터:
SELECT ?x WHERE {
    ?x rdf:type ?type .
    FILTER (?type IN (foaf:Person, foaf:Organization))
}
```

## 2. 그래프 시각화 성능 최적화

### Cytoscape.js 렌더링 최적화

```javascript
// 1. 노드 수 제한 (viewport 내 보이는 것만 렌더링)
cy.on('pan zoom', function () {
    const visibleNodes = cy.nodes().stdFilter(node => {
        return node.isVisible();
    });
    // 보이지 않는 노드 렌더링 중지
});

// 2. 레이아웃 캐싱
const layout = cy.layout({
    name: 'dagre',
    // 캐시된 레이아웃 좌표 재사용
    animationDuration: 0,
    fit: false
});

// 3. 배치 스타일 업데이트
cy.batch(() => {
    // 대량 스타일 변경 (한 번에 처리)
    nodes.forEach(node => {
        node.style('background-color', '#ff0000');
    });
});
```

### 대규모 그래프 렌더링 (1000+ 노드)

```typescript
// 계층적 확대 (Progressive Disclosure)
class HierarchicalGraphViewer {
    private focusNodeId: string;
    private zoomLevel: number = 0;  // 0: 주변 5개 노드, 1: 주변 50개, 2: 전체
    
    async loadGraphLevel(zoomLevel: number) {
        if (zoomLevel === 0) {
            // 중심 노드 + 직접 이웃만 로드 (10-20 노드)
            return this.loadFocusedGraph(this.focusNodeId, depth=1);
        } else if (zoomLevel === 1) {
            // 중심 노드 + 2-hop 이웃 (50-100 노드)
            return this.loadFocusedGraph(this.focusNodeId, depth=2);
        } else {
            // 전체 그래프
            return this.loadFullGraph();
        }
    }
}
```

### 캐싱 전략 (렌더링)

```
GraphLayout 캐시:
  Key: graph_layout:{graph_id}:{zoom_level}
  TTL: 1시간
  효과: 레이아웃 계산 반복 제거 (90% 절감)

NodePosition 캐시:
  Key: node_positions:{node_id}:{viewport}
  TTL: 30분
  효과: 확대/축소 시 위치 재계산 제거
```

## 3. 성능 영향도 추정

| 최적화 항목 | 예상 개선도 | 우선순위 |
|-----------|-----------|---------|
| SPARQL 쿼리 플래너 | 40-50% 쿼리 성능 | 1순위 (필수) |
| RDF 인덱싱 (SPO/OSP) | 60% 조회 개선 | 1순위 (필수) |
| 그래프 렌더링 캐싱 | 80% 레이아웃 시간 | 2순위 (중요) |
| 계층적 확대 (Progressive) | 90% 초기 로드 | 2순위 (중요) |
| SPARQL 결과 캐싱 | 70-80% 반복 쿼리 | 3순위 (선택) |

**예상 총 개선도**: 기준선 대비 50-60% 응답 시간 단축

## 4. 외부 Import 성능 최적화

### 배치 Import 최적화
```
1. 중복 제거 (사전): O(n) 스캔
2. 병렬 요청: 5개씩 concurrent
3. 트랜잭션 배치: 100개 단위
4. Index 업데이트 지연: Import 완료 후 한 번에
```

### 네트워크 최적화
```
DBpedia: SPARQL 엔드포인트 → 병렬 요청 (5개)
Wikidata: JSON API → 배치 (50개/요청)
로컬 RDF: 파일 스트리밍 → 청크 처리
```
```

### 예상 시간: 2-3일

**체크리스트**:
- [ ] SPARQL 쿼리 최적화 전략
- [ ] RDF 인덱싱 설계
- [ ] 그래프 렌더링 캐싱 전략
- [ ] 계층적 확대 구현 계획
- [ ] 외부 Import 배치 처리 설계

---

## 📋 일일 진행 계획

### 08-19 (화) ~ 08-25 (월)
- [ ] RDF 저장소 성능 기준선 측정
- [ ] SPARQL 쿼리 성능 분석 (SELECT, CONSTRUCT, 복합)
- [ ] 외부 Import 성능 벤치마크

### 08-26 (화) ~ 09-01 (월)
- [ ] SPARQL 쿼리 플래너 최적화 전략
- [ ] RDF 인덱싱 설계
- [ ] 그래프 렌더링 최적화 계획
- [ ] 25개 성능 시나리오 준비 (Week 5-8용)

---

## 🎯 성공 기준

✅ RDF 성능 기준선 명확히 정의 (6가지 메트릭)  
✅ SPARQL 쿼리 유형별 성능 분석  
✅ 외부 Import 성능 벤치마크  
✅ 캐싱/인덱싱 전략 완성  
✅ v4 RDF SLA 확정  
✅ Week 5-8 성능 시나리오 80% 준비

---

## 📞 상호작용

**Claude와의 연계**:
- RDF 저장소 인덱싱 검증 (Task 4-1 완료 후)
- SPARQL 쿼리 성능 벤치마크 (Task 4-3 완료 후)

**Codex와의 협력**:
- 그래프 렌더링 성능 측정 (대규모 RDF 데이터)

---

**상태**: Prep 1-2 준비 완료  
**예상 완료**: 2026-09-01  
**다음 단계**: Week 5-8 성능 구현 (09-02)

---

## 📝 최종 보고서 작성 가이드

**완료 후 다음 형식으로 최종 보고서를 작성하여 제출하세요.**

```markdown
# Phase 4 Week 4: Antigravity (Performance - RDF) 완료 보고서

**기간**: 2026-08-19 ~ 2026-09-01 (2주)
**할당**: 10% (주당 3-4시간)
**상태**: ✅ 완료
**날짜**: [실제 보고서 작성 날짜]

---

## 📋 작업 요약

### Prep 1: RDF 그래프 성능 분석 (PHASE4_RDF_PERFORMANCE_BASELINE.md)
- ✅ RDF 저장소 규모별 성능 측정 (10K/100K/1M 트리플)
- ✅ SPARQL 쿼리 유형별 성능 분석 (SELECT/CONSTRUCT/ASK/DESCRIBE)
- ✅ 외부 Import 성능 벤치마크 (DBpedia/Wikidata/RDF 파일)
- ✅ RDF 인덱싱 전략 설계
- ✅ v4 RDF SLA 정의

### Prep 2: SPARQL 최적화 전략 및 그래프 렌더링 성능 (PHASE4_RDF_OPTIMIZATION.md)
- ✅ SPARQL 쿼리 플래너 최적화 전략
- ✅ RDF 인덱싱 설계 (주제/술어/목적 인덱스)
- ✅ 그래프 렌더링 캐싱 전략
- ✅ 계층적 확대/축소(Hierarchical Zoom) 구현 계획
- ✅ 외부 Import 배치 처리 설계
- ✅ 25개 성능 시나리오 (Week 5-8용)

---

## 📊 설계 검증 결과

| 항목 | 목표 | 달성 |
|------|------|------|
| RDF 성능 기준선 | 6가지 메트릭 | ✅ 모두 정의 |
| SPARQL 쿼리 성능 | 쿼리 유형별 분석 | ✅ 4가지 유형 분석 |
| 외부 Import 성능 | 3가지 소스 벤치마크 | ✅ 모두 측정 |
| 캐싱/인덱싱 전략 | 설계 완료 | ✅ 완성 |
| RDF SLA | 3 Tier 정의 | ✅ Critical/Important/Goals |
| 성능 시나리오 | 25개 설계 | ✅ 80% 이상 준비 |

---

## 📈 주요 성과

**성능 기준선**:
- RDF 로드: 10K (<100ms) → 1M (<2초)
- SPARQL SELECT: 10K (<20ms) → 1M (<200ms)
- DBpedia Import: 1000 엔티티 < 2초
- Wikidata Import: 1000 엔티티 < 3초
- RDF 파일 Import: 1M 트리플 < 5초

**최적화 전략**:
- 주제/술어/목적 3방향 인덱싱
- SPARQL 쿼리 캐싱 (Redis 1시간 TTL)
- 그래프 렌더링 계층적 확대 (LOD - Level of Detail)
- 외부 Import 병렬 요청 (5개/배치)
- RDF 쿼리 플래너 최적화

**SLA 정의**:
- Tier 1 Critical: SPARQL SELECT < 500ms
- Tier 2 Important: RDF 로드 < 2초 (1M 트리플)
- Tier 3 Goal: 캐시 히트율 ≥ 80% (SPARQL)

---

## 🔧 생성된 문서

### 생성된 파일
- `ont_platform/v4/PHASE4_RDF_PERFORMANCE_BASELINE.md` - RDF 성능 기준선
- `ont_platform/v4/PHASE4_RDF_OPTIMIZATION.md` - RDF 최적화 전략

---

## ⏭️ 다음 단계

### 즉시 필요 (Week 4.5)
- [ ] RDF 인덱싱 구현 (PostgreSQL 또는 Elasticsearch)
- [ ] SPARQL 캐싱 레이어 Redis 통합
- [ ] 그래프 렌더링 성능 프로파일링

### Week 5-8 준비
- [ ] 25개 성능 시나리오 구현 및 검증
- [ ] 대규모 RDF 데이터 성능 테스트 (Codex와 협력)

---

## 🔗 관련 문서

- 지시서: `week_instructions/PHASE4/Week_4_RDF/Antigravity.md`
- RDF 성능 기준선: `ont_platform/v4/PHASE4_RDF_PERFORMANCE_BASELINE.md`
- RDF 최적화: `ont_platform/v4/PHASE4_RDF_OPTIMIZATION.md`

---

**보고자**: Antigravity (Performance - RDF)
**완료 시각**: [실제 완료 시각] KST
```

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/antigravity/YYYYMMDD_PHASE4_WEEK4_Antigravity_Complete.md`
   - 파일명 형식: `YYYYMMDD_HHMM_작업명.md`
   - 예: `20260901_1830_PHASE4_WEEK4_Antigravity_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

2. **템플릿 작성**:
   - "기간", "할당", "상태", "날짜" → 실제 작업 기록으로 채우기
   - "Prep 1-2" 섹션 → 실제 완료 항목만 체크
   - "설계 검증 결과" 테이블 → 실제 결과로 갱신
   - "생성된 파일" → 실제로 생성된 파일 경로 입력
