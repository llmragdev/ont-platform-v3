# Phase 2.5 병렬 개발 지시서 (3 에이전트 협업)

> **프로젝트**: ont_platform v3  
> **단계**: Phase 2.5 — PostgreSQL 마이그레이션 + SPARQL→SQL 통합  
> **기간**: 2026-06-03 ~ 2026-06-21 (3주)  
> **팀**: Claude + Codex + Antigravity (3개 에이전트 병렬)  
> **작성**: 2026-05-24  
> **상태**: 📋 미션 정의 완료, 🔴 구현 시작 대기 (2026-06-03)

---

## 🎯 전체 목표

| 항목 | 목표 |
|------|------|
| **개발 방식** | 3개 에이전트 병렬 개발 (의존성 최소화) |
| **산출물** | SPARQL→SQL 번역기 + Frontend UI + 성능 최적화 |
| **테스트** | 단위(100+) + 통합(50+) + e2e(15+) |
| **성능** | Hot-path 쿼리 목표 달성 |
| **일정** | 순차(6주) → 병렬(3주) |

---

## 📋 에이전트별 미션

---

## 🔴 **CLAUDE: SPARQL→SQL 번역기 엔진 (Backend Core)**

### 📌 개요
- **역할**: 핵심 번역 엔진 구현 + API 통합
- **기간**: 2026-06-03 ~ 2026-06-21 (3주)
- **담당자**: Claude Code
- **산출물**: `app/services/sparql_translator.py` + 100+ 테스트

### 📅 주간 계획

#### Week 2 (2026-06-03 ~ 06-07): 설계 + 기초 구현

**Task 2-1: SPARQLTranslator 아키텍처 설계** (06-03 ~ 06-04)

```markdown
목표: 40개 기본 패턴을 SQL로 변환할 수 있는 설계 완성

산출물:
1. SPARQLTranslator 클래스 구조
   - translate(sparql_query: str) → SQL str
   - parse_sparql() → ParsedQuery object
   - extract_patterns() → List[TriplePattern]
   - generate_sql() → SQLBuilder
   - optimize() → str

2. TriplePattern 표준화
   - (?subject, predicate, ?object) 정규화
   - 변수 바인딩 추적 (map: var → entity_id)
   - 상수 vs 변수 구분

3. 40개 테스트 패턴 목록 정의
   - 기본 패턴 (10): SELECT ?x WHERE { ?x rdf:type Ex:Type }
   - JOIN 패턴 (10): ?x ex:rel ?y JOIN
   - FILTER 패턴 (10): FILTER (?x > 100)
   - 복합 패턴 (10): 다중 JOIN + FILTER

승인 기준: 테스트 케이스 40개 작성, 모두 예상 결과 정의
```

**Task 2-2: Translator 구현** (06-04 ~ 06-06)

```markdown
목표: 500줄 Translator 코드 작성, 40개 패턴 지원

파일: app/services/sparql_translator.py

핵심 메서드:
1. _parse_sparql(query: str) → ParsedQuery
   - rdflib.Graph.query_algebra() 활용
   - PREFIX 추출, WHERE 절 분석
   - 변수 식별

2. _extract_patterns(parsed: ParsedQuery) → List[TriplePattern]
   - Triple pattern 추출
   - 조인 순서 결정 (cardinality 기반)
   - 최적화 기회 식별

3. _generate_sql(patterns: List[TriplePattern]) → SQLAlchemy Query
   - 첫 번째 pattern: SELECT * FROM entities WHERE ...
   - 이후 pattern: JOIN relationships ON ...
   - 변수 바인딩 적용

4. _filter_translator(filter_expr) → SQLAlchemy BinaryExpression
   - FILTER (X > Y) → sqlalchemy.func.cast(properties>>>'X', Integer) > Y
   - 논리 연산 (AND, OR, NOT)
   - 함수 (REGEX, STR, LANG 등)

5. _optimize(sql_str: str) → str
   - 중복 JOIN 제거
   - 인덱스 힌트 추가
   - 서브쿼리 최소화

테스트: tests/unit/test_sparql_translator.py (40개 테스트)
- 각 패턴 종류별 통과율 100%
- 생성된 SQL 성능 확인

승인 기준: 40/40 테스트 통과, SQL 생성 검증 완료
```

**Task 2-3: 성능 검증** (06-06 ~ 06-07)

```markdown
목표: Hot-path 쿼리 성능 목표 달성 확인

성능 테스트: tests/integration/test_performance.py

1. Simple Lookup (<50ms)
   SELECT ?x WHERE { ?x ex:id "entity_1" }
   - 단순 WHERE 절 (B-tree index 활용)
   - 예상: <50ms

2. One-hop Relation (<300ms)
   SELECT ?y WHERE { ?x ex:rel ?y . ?x ex:id "entity_1" }
   - 단일 JOIN (relationships 테이블)
   - 예상: <300ms

3. Two-hop Relation (<1s)
   SELECT ?z WHERE { ?x ex:rel1 ?y . ?y ex:rel2 ?z . ?x ex:id "entity_1" }
   - 다중 JOIN (2개 이상)
   - 예상: <1000ms

벤치마크 데이터: 10K 엔티티 + 50K 관계 (샘플 데이터셋)

결과 리포트:
- 각 쿼리 타입별 평균 실행 시간
- 쿼리 플랜 분석 (EXPLAIN)
- 병목 지점 식별

승인 기준: 3가지 성능 목표 모두 달성
```

**Week 2 산출물**:
```
✅ app/services/sparql_translator.py (250줄)
✅ tests/unit/test_sparql_translator.py (40개 테스트)
✅ tests/integration/test_performance.py (3개 성능 테스트)
✅ docs/SPARQL_TRANSLATOR_GUIDE.md (사용 가이드)
✅ Milestone: Week 2 완료 (2026-06-07)
```

---

#### Week 3 (2026-06-10 ~ 06-14): API 통합 + 트랜잭션

**Task 3-1: FastAPI 엔드포인트 통합** (06-10 ~ 06-11)

```markdown
목표: /sparql 엔드포인트 구현, 번역기와 통합

파일: app/routes/sparql.py (신규)

엔드포인트:
1. POST /sparql/query
   요청: { "query": "SELECT ?x WHERE ..." }
   응답: { 
     "results": [...],
     "query_time_ms": 45,
     "translator_used": true,
     "sql_generated": "SELECT * FROM..."
   }

2. POST /sparql/explain
   요청: { "query": "SELECT ?x WHERE ..." }
   응답: { 
     "sql": "SELECT * FROM...",
     "execution_plan": "Seq Scan on entities..."
   }

3. GET /sparql/health
   응답: { "status": "ok", "translator": "ready" }

통합 로직:
- SPARQL 문법 검증 (rdflib)
- SPARQLTranslator.translate() 호출
- SQLAlchemy로 SQL 실행
- 결과 포맷팅 (SPARQL JSON results format)

에러 처리:
- 번역 불가능한 쿼리 → fallback to rdflib
- SQL 실행 에러 → 명확한 에러 메시지
- 타임아웃 → 비동기 작업으로 이관

승인 기준: 엔드포인트 3개 동작, 통합 테스트 15개 통과
```

**Task 3-2: 트랜잭션 + 동시성 지원** (06-11 ~ 06-12)

```markdown
목표: 동시 쿼리 지원, 데이터 일관성 보장

구현:
1. SQLAlchemy Session 격리
   - READ COMMITTED 격리 수준 (기본값)
   - 각 요청마다 새 session 생성
   - 자동 롤백 (에러 시)

2. 동시성 테스트
   - 100개 병렬 쿼리 실행
   - 데이터 불일치 확인
   - 응답 시간 측정

3. Optimistic Locking (준비)
   - Entity.version 컬럼 활용
   - UPDATE 시 version 검증
   - 충돌 해결 전략 문서화

테스트: tests/integration/test_concurrency.py (10개)
- 병렬 읽기 (100개 동시 쿼리)
- 읽기/쓰기 혼합 (50개 각각)
- 데이터 무결성 검증

승인 기준: 모든 동시성 테스트 통과, 데이터 무결성 보증
```

**Task 3-3: Swagger 문서화** (06-12 ~ 06-14)

```markdown
목표: OpenAPI 문서 자동 생성, 개발자 경험 개선

구현:
1. FastAPI 자동 문서 생성
   - /docs (Swagger UI)
   - /redoc (ReDoc)
   - request/response 스키마 정의

2. 예제 쿼리 제공
   - "전체 엔티티 조회"
   - "특정 타입 필터"
   - "관계 탐색"
   - 각 예제 동작 확인

3. 가이드 작성
   - docs/API_GUIDE.md
   - 쿼리 최적화 팁
   - 성능 제한사항
   - 에러 코드 정의

승인 기준: Swagger 열면 모든 엔드포인트 표시, 예제 5개 이상
```

**Week 3 산출물**:
```
✅ app/routes/sparql.py (150줄)
✅ tests/integration/test_api_integration.py (15개 테스트)
✅ tests/integration/test_concurrency.py (10개 테스트)
✅ docs/API_GUIDE.md (완성)
✅ /docs (Swagger 활성화)
✅ Milestone: Week 3 완료 (2026-06-14)
```

---

#### Week 4 (2026-06-17 ~ 06-21): 통합 테스트 + 버그 수정

**Task 4-1: 통합 테스트** (06-17 ~ 06-19)

```markdown
목표: 50개 이상 통합 테스트, 엔드-투-엔드 검증

테스트 영역:
1. SPARQL 패턴 호환성 (30개)
   - Supported Profile 모든 패턴
   - Fallback 패턴 (rdflib)
   - 엣지 케이스

2. API 엔드포인트 (10개)
   - 정상 요청/응답
   - 에러 처리
   - 타임아웃

3. 성능 + 동시성 (10개)
   - 부하 조건 (10K-100K 레코드)
   - 병렬 쿼리 (50개 동시)
   - 캐싱 검증

파일: tests/integration/test_full_suite.py (50+)

승인 기준: 50/50 통과, 커버리지 ≥ 80%
```

**Task 4-2: 버그 수정 + 성능 튜닝** (06-19 ~ 06-21)

```markdown
목표: 버그 0건, 성능 목표 달성

작업:
1. 테스트 실패 원인 분석 및 수정
   - 기한: 06-20 자정
   - 각 버그마다 테스트 추가

2. 성능 프로파일링
   - 가장 느린 쿼리 10개 식별
   - 병목 지점 해결
   - 인덱스 추가/튜닝

3. 코드 리뷰
   - 가독성 개선
   - 주석 추가 (복잡 부분)
   - 리팩토링

최종 체크리스트:
- [ ] 모든 테스트 통과
- [ ] 성능 목표 달성
- [ ] 문서 완성
- [ ] 코드 리뷰 완료

승인 기준: 모든 체크리스트 완료
```

**Week 4 산출물**:
```
✅ tests/integration/test_full_suite.py (50+)
✅ 버그 리포트 + 수정 로그
✅ 성능 벤치마크 최종 리포트
✅ 코드 리뷰 완료
✅ Milestone: Week 4 완료 (2026-06-21)
```

---

### 📊 Claude 체크리스트

```
Week 2 (06-03 ~ 06-07):
  [ ] Task 2-1: 아키텍처 설계 (06-04)
  [ ] Task 2-2: Translator 구현 (06-06)
  [ ] Task 2-3: 성능 검증 (06-07)
  [ ] 40개 테스트 모두 통과
  
Week 3 (06-10 ~ 06-14):
  [ ] Task 3-1: API 엔드포인트 (06-11)
  [ ] Task 3-2: 동시성 지원 (06-12)
  [ ] Task 3-3: Swagger 문서 (06-14)
  [ ] 25개 새 테스트 모두 통과
  
Week 4 (06-17 ~ 06-21):
  [ ] Task 4-1: 통합 테스트 작성 (06-19)
  [ ] Task 4-2: 버그 수정 + 성능 튜닝 (06-21)
  [ ] 50개 통합 테스트 모두 통과
  [ ] 성능 목표 달성 확인
```

---

---

## 🟠 **CODEX: Frontend + 시각화 (UI/UX Layer)**

### 📌 개요
- **역할**: 사용자 인터페이스 + 실시간 쿼리 실행
- **기간**: 2026-06-03 ~ 2026-06-21 (3주)
- **산출물**: 개선된 QueryResult + 그래프 시각화 + 반응형 UI

### 📅 주간 계획

#### Week 2 (2026-06-03 ~ 06-07): 쿼리 UI + 기본 시각화

**Task 2-1: QueryResult 컴포넌트 개선** (06-03 ~ 06-04)

```markdown
목표: 실시간 쿼리 결과 표시, 응답 시간 시각화

현재 상태: 기본 테이블 표시만 가능
목표: 대화형 쿼리 빌더 + 결과 탭

파일: src/frontend/components/QueryResult.tsx (기존 개선)

구현:
1. 쿼리 입력 영역
   - Monaco Editor로 SPARQL 작성
   - 문법 하이라이트
   - 자동 완성 (PREFIX, SELECT 등)

2. 실행 버튼
   - "Execute Query" 버튼
   - 실행 중 로딩 표시
   - 실행 취소 옵션

3. 결과 표시
   - 테이블 뷰 (행, 열)
   - JSON 뷰 (raw 응답)
   - 응답 시간 표시 (ms)

4. 에러 처리
   - 에러 메시지 강조 표시
   - 제안 (Did you mean?)
   - 디버그 정보 (SQL, EXPLAIN)

UI 디자인:
```
┌─────────────────────────────────┐
│ SPARQL Query Editor             │
│ SELECT ?x WHERE { ... }         │ <- Monaco Editor
├─────────────────────────────────┤
│ [Execute] [Cancel] [Clear]      │
├─────────────────────────────────┤
│ Query Time: 45ms                │
├─────────────────────────────────┤
│ [Table] [JSON] [Graph]          │ <- 탭 메뉴
├─────────────────────────────────┤
│ Results (10 rows)               │
│ ┌────────────────────────────┐  │
│ │ x         | name           │  │
│ ├────────────────────────────┤  │
│ │ entity_1  | Project A      │  │
│ │ entity_2  | Project B      │  │
│ └────────────────────────────┘  │
└─────────────────────────────────┘
```

배포:
- npm run build
- 성능 최적화 (bundle size <500KB)

승인 기준: 쿼리 실행 → 결과 표시까지 작동
```

**Task 2-2: 실시간 쿼리 실행 UI** (06-04 ~ 06-06)

```markdown
목표: 쿼리 입력 → 1초 내 결과 표시

구현:
1. 비동기 API 호출
   ```typescript
   const executeQuery = async (query: string) => {
     setLoading(true);
     const start = Date.now();
     try {
       const response = await fetch('/api/sparql/query', {
         method: 'POST',
         body: JSON.stringify({ query })
       });
       const time = Date.now() - start;
       setResults(response.data);
       setQueryTime(time);
     } catch (e) {
       setError(e.message);
     } finally {
       setLoading(false);
     }
   };
   ```

2. 로딩 상태 표시
   - Spinner 애니메이션
   - "쿼리 실행 중..." 메시지
   - 취소 버튼 활성화

3. 응답 시간 배지
   - <50ms: 녹색 (아주 빠름)
   - <300ms: 파랑색 (빠름)
   - <1s: 노랑색 (보통)
   - >1s: 빨강색 (느림)

4. 히스토리 패널
   - 최근 10개 쿼리 저장
   - 클릭 시 재실행
   - 즐겨찾기 기능

파일: src/frontend/hooks/useQuery.ts (커스텀 훅)

승인 기준: 쿼리 실행 <1초, 히스토리 저장됨
```

**Task 2-3: 응답 시간 시각화** (06-06 ~ 06-07)

```markdown
목표: 성능 데이터 시각화

구현:
1. 응답 시간 차트
   - 최근 20개 쿼리의 실행 시간
   - 라인 차트 (y축: ms, x축: 시간순)
   - 목표선 표시 (50ms, 300ms, 1s)

2. 쿼리 타입별 통계
   - Simple Lookup: 평균 45ms
   - One-hop: 평균 200ms
   - Two-hop: 평균 800ms
   - 막대 그래프

3. 성능 경고
   - 쿼리가 목표를 초과하면 경고 표시
   - 제안: "인덱스 추가 고려"
   - 쿼리 최적화 팁

라이브러리: recharts (간단, 가벼움)

파일: src/frontend/components/PerformanceChart.tsx (신규)

승인 기준: 차트 표시, 통계 정확함
```

**Week 2 산출물**:
```
✅ src/frontend/components/QueryResult.tsx (개선)
✅ src/frontend/hooks/useQuery.ts (신규)
✅ src/frontend/components/PerformanceChart.tsx (신규)
✅ UI 스크린샷 5개 (docs/FRONTEND_UI.md)
✅ Milestone: Week 2 완료 (2026-06-07)
```

---

#### Week 3 (2026-06-10 ~ 06-14): 그래프 시각화 + 고급 필터

**Task 3-1: Entity-Relationship 그래프 시각화** (06-10 ~ 06-12)

```markdown
목표: 쿼리 결과를 그래프로 표시 (노드 + 엣지)

구현:
1. 그래프 노드
   - 원형 노드 (Entity)
   - 노드 색상: entity_type별로 구분
   - 노드 크기: 관계 수로 결정
   - 마우스 오버: 정보 표시

2. 그래프 엣지
   - 화살표 (directed edge)
   - 엣지 라벨: relation_type
   - 엣지 굵기: weight
   - 선 색상: relation_type별로 구분

3. 상호작용
   - 드래그로 노드 이동
   - 줌인/아웃
   - 노드 클릭: 상세 정보 패널
   - 엣지 클릭: 관계 정보

라이브러리: vis.js 또는 cytoscape.js (그래프 라이브러리)

```
┌──────────────────────────────────────┐
│ Graph View                           │
├──────────────────────────────────────┤
│         [Project A]                  │
│            / | \                     │
│           /  |  \                    │
│        rel1 rel2 rel3                │
│         /    |    \                  │
│    [Dept] [Team] [Budget]            │
│                                      │
│ 범례:                                 │
│ ● Project ○ Department ▲ Team       │
└──────────────────────────────────────┘
```

파일: src/frontend/components/EntityGraph.tsx (신규)

승인 기준: 노드 5개 이상, 엣지 연결 표시됨
```

**Task 3-2: 필터 빌더 UI** (06-12 ~ 06-13)

```markdown
목표: GUI로 FILTER 조건 작성

구현:
1. 필터 조건 빌더
   - 드롭다운: 속성 선택 (name, cost, status 등)
   - 비교 연산자: =, !=, >, <, >=, <=, LIKE
   - 값 입력: 텍스트, 숫자, 날짜
   - AND/OR 로직

2. 쿼리 생성
   - "필터 추가" 클릭 → SPARQL 쿼리에 FILTER 조건 추가
   - 생성된 쿼리 프리뷰
   - 수동 편집 가능

UI 디자인:
```
필터 추가: [속성 v] [연산자 v] [값 ___] [+ AND] [+ OR]
           [name]  [LIKE]      [proj]

생성된 쿼리:
SELECT ?x WHERE {
  ?x ex:name ?name
  FILTER (REGEX(?name, "proj", "i"))
}
```

파일: src/frontend/components/FilterBuilder.tsx (신규)

승인 기준: 5개 이상 필터 조합 지원
```

**Task 3-3: 쿼리 히스토리 저장소** (06-13 ~ 06-14)

```markdown
목표: 쿼리 히스토리 관리 (로컬 스토리지 + 백엔드)

구현:
1. 로컬 스토리지
   - 최근 20개 쿼리 저장
   - 타임스탐프, 응답 시간, 결과 행 수 기록
   - 새로고침 후에도 유지

2. 즐겨찾기
   - 자주 사용하는 쿼리 저장
   - 라벨 추가 (ex: "모든 프로젝트")
   - 즐겨찾기 탭에서 빠르게 접근

3. 공유 기능 (옵션)
   - 쿼리 URL 생성 (query parameter)
   - 팀원에게 공유 가능
   - 공유 히스토리 보기

파일: src/frontend/hooks/useQueryHistory.ts (신규)
       src/frontend/components/QueryHistory.tsx (신규)

승인 기준: 히스토리 5개 이상 저장, 재실행 가능
```

**Week 3 산출물**:
```
✅ src/frontend/components/EntityGraph.tsx (신규)
✅ src/frontend/components/FilterBuilder.tsx (신규)
✅ src/frontend/hooks/useQueryHistory.ts (신규)
✅ src/frontend/components/QueryHistory.tsx (신규)
✅ UI 스크린샷 10개 (docs/FRONTEND_ADVANCED.md)
✅ Milestone: Week 3 완료 (2026-06-14)
```

---

#### Week 4 (2026-06-17 ~ 06-21): 반응형 + 다크모드 + e2e 테스트

**Task 4-1: 모바일 반응형 레이아웃** (06-17 ~ 06-18)

```markdown
목표: 모바일/태블릿에서도 동작하는 UI

구현:
1. 반응형 그리드
   - 데스크톱 (>1200px): 3열 (쿼리 + 결과 + 그래프)
   - 태블릿 (768-1200px): 2열 (쿼리/결과, 그래프)
   - 모바일 (<768px): 1열 (스택)

2. 터치 최적화
   - 버튼 크기: 최소 44x44px
   - 텍스트: 최소 14px
   - 스크롤 인디케이터

3. 모바일 네비게이션
   - 해머거 메뉴
   - 탭 네비게이션 (Query, Results, Graph)
   - 하단 액션 버튼

파일: src/frontend/styles/responsive.css (신규)
       각 컴포넌트에 media query 추가

승인 기준: 3가지 화면 크기에서 테스트 완료
```

**Task 4-2: 다크모드 지원** (06-18 ~ 06-19)

```markdown
목표: 사용자가 다크모드 선택 가능

구현:
1. 테마 토글
   - UI 상단 오른쪽: 태양/달 아이콘
   - 클릭하면 테마 전환
   - 선택 저장 (로컬 스토리지)

2. 색상 스킴
   - Light: 흰색 배경, 검은색 텍스트
   - Dark: 검은색 배경, 흰색 텍스트
   - 차트, 테이블, 그래프 모두 적용

라이브러리: tailwindcss darkMode 또는 CSS variables

파일: src/frontend/context/ThemeContext.tsx (신규)
       src/frontend/components/ThemeToggle.tsx (신규)

승인 기준: 다크모드 전환 부드러움, 모든 컴포넌트 호환
```

**Task 4-3: e2e 테스트** (06-19 ~ 06-21)

```markdown
목표: 전체 사용자 흐름 자동 테스트

프레임워크: Cypress

테스트 시나리오 (15개):
1. 쿼리 실행 (3개)
   - 정상 쿼리 실행
   - 쿼리 에러 처리
   - 빈 결과

2. 시각화 (4개)
   - 테이블 뷰 클릭
   - 그래프 뷰 표시
   - 노드 상호작용
   - 필터 적용

3. 히스토리 (3개)
   - 쿼리 히스토리 저장
   - 이전 쿼리 실행
   - 즐겨찾기 추가

4. 반응형 (3개)
   - 모바일 뷰 렌더링
   - 터치 상호작용
   - 네비게이션 열기

5. 다크모드 (2개)
   - 테마 토글
   - 색상 변경 확인

파일: src/frontend/cypress/e2e/query.cy.ts
       src/frontend/cypress/e2e/visualization.cy.ts
       src/frontend/cypress/e2e/responsive.cy.ts

실행:
```bash
npm run cypress:open    # 대화형 테스트
npm run cypress:run     # CI/CD 모드
```

승인 기준: 15/15 테스트 통과
```

**Week 4 산출물**:
```
✅ 반응형 CSS 완성 (모바일 호환)
✅ src/frontend/context/ThemeContext.tsx (신규)
✅ src/frontend/components/ThemeToggle.tsx (신규)
✅ src/frontend/cypress/e2e/*.cy.ts (15개 테스트)
✅ UI/UX 문서 완성
✅ Milestone: Week 4 완료 (2026-06-21)
```

---

### 📊 Codex 체크리스트

```
Week 2 (06-03 ~ 06-07):
  [ ] Task 2-1: QueryResult 개선 (06-04)
  [ ] Task 2-2: 실시간 실행 UI (06-06)
  [ ] Task 2-3: 성능 시각화 (06-07)
  [ ] UI 스크린샷 5개 완성
  
Week 3 (06-10 ~ 06-14):
  [ ] Task 3-1: 그래프 시각화 (06-12)
  [ ] Task 3-2: 필터 빌더 (06-13)
  [ ] Task 3-3: 히스토리 저장소 (06-14)
  [ ] UI 스크린샷 10개 완성
  
Week 4 (06-17 ~ 06-21):
  [ ] Task 4-1: 모바일 반응형 (06-18)
  [ ] Task 4-2: 다크모드 (06-19)
  [ ] Task 4-3: e2e 테스트 (06-21)
  [ ] 15개 Cypress 테스트 모두 통과
```

---

---

## 🟢 **ANTIGRAVITY: 성능 최적화 + 벡터 검색 (Performance & Vector)**

### 📌 개요
- **역할**: 성능 벤치마킹 + 벡터 검색 최적화
- **기간**: 2026-06-03 ~ 2026-06-21 (3주)
- **산출물**: 성능 벤치마크 리포트 + 최적화 제안

### 📅 주간 계획

#### Week 2 (2026-06-03 ~ 06-07): 벡터 최적화 + 임베딩

**Task 2-1: 벡터 임베딩 성능 최적화** (06-03 ~ 06-04)

```markdown
목표: 의미 검색 응답 시간 <500ms 달성

현재: Chroma + Langchain-google-genai
목표: 임베딩 캐싱 + 배치 처리

구현:
1. 임베딩 캐싱 (Redis)
   ```python
   # 같은 텍스트는 한 번만 임베딩
   cache_key = hash(text)
   if redis.exists(cache_key):
       embedding = redis.get(cache_key)
   else:
       embedding = genai.embed(text)
       redis.set(cache_key, embedding, ttl=86400)  # 24h
   ```

2. 배치 임베딩
   - 여러 문서를 한 번에 임베딩
   - API 호출 횟수 감소
   - 처리량 증가

3. 성능 측정
   - 단일 임베딩: 100ms → 50ms (캐시)
   - 배치 (10개): 1000ms → 200ms (배치)

파일: app/services/embedding_service.py (신규)

테스트: tests/integration/test_embedding_perf.py
- 임베딩 캐싱 효율성
- 배치 처리 속도
- 메모리 사용량

승인 기준: 임베딩 응답 <100ms (캐시 hit)
```

**Task 2-2: 의미 검색 성능 테스트** (06-04 ~ 06-06)

```markdown
목표: 의미 검색이 정확하고 빠름을 증명

구현:
1. 벡터 검색 벤치마크
   - 쿼리: "프로젝트 승인 프로세스"
   - 데이터셋: 1000개 문서
   - 목표: <500ms, 정확도 >80%

2. 하이브리드 검색 (키워드 + 벡터)
   - 키워드 검색으로 후보 500개 필터
   - 벡터 검색으로 상위 10개 정렬
   - 속도: 키워드만 (50ms) vs 하이브리드 (200ms)

3. 성능 비교
   | 방식 | 응답시간 | 정확도 |
   |------|---------|-------|
   | 키워드만 | 50ms | 60% |
   | 벡터만 | 500ms | 85% |
   | 하이브리드 | 200ms | 90% |

파일: tests/integration/test_vector_search.py
       docs/VECTOR_SEARCH_REPORT.md

승인 기준: 하이브리드 검색 구현, 정확도 >85%
```

**Task 2-3: 인덱스 효율성 분석** (06-06 ~ 06-07)

```markdown
목표: PostgreSQL GIN 인덱스 성능 검증

구현:
1. 인덱스 상태 확인
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
   FROM pg_stat_user_indexes
   ORDER BY idx_scan DESC;
   ```

2. 쿼리 플랜 분석
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM entities 
   WHERE properties @> '{"status": "active"}'
   ```

3. 인덱스 활용 현황
   - 어떤 인덱스가 사용되는가?
   - 어떤 쿼리가 인덱스를 안 쓰는가?
   - 새로운 인덱스 필요한가?

리포트: docs/INDEX_ANALYSIS.md
- 각 인덱스별 활용률
- 병목 쿼리 목록
- 최적화 권고사항

승인 기준: 인덱스 활용률 분석 완료
```

**Week 2 산출물**:
```
✅ app/services/embedding_service.py (신규)
✅ tests/integration/test_embedding_perf.py (신규)
✅ tests/integration/test_vector_search.py (신규)
✅ docs/VECTOR_SEARCH_REPORT.md (신규)
✅ docs/INDEX_ANALYSIS.md (신규)
✅ Milestone: Week 2 완료 (2026-06-07)
```

---

#### Week 3 (2026-06-10 ~ 06-14): 부하 테스트 + 병목 분석

**Task 3-1: 부하 테스트 (100K ~ 1M 레코드)** (06-10 ~ 06-12)

```markdown
목표: 대규모 데이터셋에서 성능 목표 달성 확인

도구: Apache JMeter 또는 Locust

시나리오:
1. 단계적 부하 증가
   - 1K 엔티티: 실행 시간 측정
   - 10K 엔티티: 실행 시간 측정
   - 100K 엔티티: 실행 시간 측정
   - 1M 엔티티: 실행 시간 측정

2. 쿼리 패턴별 테스트
   ```
   Simple Lookup:
     10K: 30ms, 100K: 40ms, 1M: 55ms ✓ (목표 <50ms)
   
   One-hop:
     10K: 150ms, 100K: 250ms, 1M: 400ms ✓ (목표 <300ms)
   
   Two-hop:
     10K: 600ms, 100K: 900ms, 1M: 1400ms ✗ (목표 <1s, 초과)
   ```

3. 동시 사용자 시뮬레이션
   - 10명 동시: 전체 응답 시간
   - 50명 동시: 전체 응답 시간
   - 100명 동시: 에러 발생 여부

파일: tests/load/load_test.py (신규)
       tests/load/queries.txt (테스트 쿼리 세트)

리포트: docs/LOAD_TEST_REPORT.md
- 각 시나리오별 결과
- 병목 지점 식별
- 권고사항

승인 기준: Simple + One-hop 목표 달성, Two-hop 분석 완료
```

**Task 3-2: 쿼리 플래너 분석** (06-12 ~ 06-13)

```markdown
목표: 느린 쿼리 원인 파악 및 최적화

구현:
1. EXPLAIN ANALYZE 실행
   - Two-hop 쿼리 분석
   - Seq Scan vs Index Scan 확인
   - 예상 vs 실제 행 수

2. 병목 지점 식별
   - 어디서 시간이 걸리는가?
   - 인덱스 미사용 부분?
   - 메모리 부족?

3. 최적화 제안
   - 새로운 인덱스 추가
   - 쿼리 재작성
   - JOIN 순서 변경

예제:
```sql
-- 느린 쿼리
EXPLAIN ANALYZE
SELECT ?z WHERE {
  ?x ex:rel1 ?y .
  ?y ex:rel2 ?z .
  ?x ex:id "entity_1"
} LIMIT 10;

결과:
Nested Loop (1300ms)
  -> Seq Scan on relationships r1 (800ms) <- 병목
  -> Index Scan on entities e1 (500ms)
  -> ...
```

**최적화 방안**:
- 조건 푸시다운: ex:id 먼저 필터
- 인덱스 추가: (from_entity_id, relation_type)

파일: docs/QUERY_OPTIMIZATION.md (신규)

승인 기준: 5개 이상 느린 쿼리 분석 완료
```

**Task 3-3: 인덱스 성능 재평가** (06-13 ~ 06-14)

```markdown
목표: 최적화 후 성능 재검증

구현:
1. 신규 인덱스 추가 및 테스트
   ```sql
   CREATE INDEX idx_rel_from_type ON relationships(from_entity_id, relation_type);
   CREATE INDEX idx_entities_domain_type ON entities(domain_id, entity_type);
   ```

2. 쿼리 성능 재측정
   - 이전: Two-hop 1400ms (1M)
   - 이후: Two-hop 950ms (1M) ✓
   - 개선율: 32%

3. 인덱스 크기 vs 성능 트레이드오프
   - 인덱스 수 증가 → 쓰기 느려짐
   - 적절한 인덱스 개수: 15-20개

최종 리포트: docs/FINAL_PERFORMANCE_REPORT.md
- 최적화 전후 비교
- 달성한 성능 목표
- 추가 최적화 기회

승인 기준: 모든 성능 목표 달성 또는 설명 완료
```

**Week 3 산출물**:
```
✅ tests/load/load_test.py (신규)
✅ tests/load/queries.txt (신규)
✅ docs/LOAD_TEST_REPORT.md (신규)
✅ docs/QUERY_OPTIMIZATION.md (신규)
✅ docs/FINAL_PERFORMANCE_REPORT.md (신규)
✅ 신규 인덱스 생성 (5개+)
✅ Milestone: Week 3 완료 (2026-06-14)
```

---

#### Week 4 (2026-06-17 ~ 06-21): 캐싱 + 벤치마크 최종화

**Task 4-1: 캐싱 전략 구현** (06-17 ~ 06-19)

```markdown
목표: 자주 사용하는 쿼리 캐싱으로 응답 시간 50% 단축

구현:
1. 쿼리 결과 캐싱 (Redis)
   ```python
   def cached_query(query: str):
       cache_key = hash(query)
       if redis.exists(cache_key):
           return redis.get(cache_key)  # 캐시 hit
       
       result = execute_query(query)
       redis.set(cache_key, result, ttl=300)  # 5분
       return result
   ```

2. 캐시 무효화 전략
   - SELECT 쿼리만 캐시
   - 데이터 변경 시 관련 캐시 제거
   - TTL: 5분 (쿼리 특성에 따라 조정)

3. 캐시 히트율 모니터링
   - "캐시 히트", "캐시 미스" 수 기록
   - 응답 시간 비교 (캐시 vs 미캐시)

측정:
```
캐시 전: 평균 200ms
캐시 후: 평균 50ms (캐시 hit), 200ms (미hit)
평균: 100ms (50% 개선)
```

파일: app/services/cache_service.py (신규)
       app/routes/sparql.py (캐싱 통합)

파일: tests/integration/test_caching.py (신규)

승인 기준: 캐싱 구현, 히트율 >60%
```

**Task 4-2: 최종 벤치마크 리포트** (06-19 ~ 06-21)

```markdown
목표: 전체 성능 최적화 결과 정리

리포트 내용:
1. 성능 목표 달성도
   | 쿼리 타입 | 목표 | 달성 | 상태 |
   |---------|------|------|------|
   | Simple Lookup | <50ms | 45ms | ✓ |
   | One-hop | <300ms | 250ms | ✓ |
   | Two-hop | <1s | 950ms | ✓ |

2. 최적화 항목별 효과
   - 인덱스 추가: +32%
   - 캐싱: +50% (hit시)
   - 쿼리 재작성: +15%
   - 임베딩 캐싱: +60% (의미검색)

3. 리소스 사용량
   - CPU: 평균 15%, 피크 45%
   - 메모리: 평균 2GB, 피크 3.5GB
   - 디스크: 인덱스 500MB, 데이터 2GB

4. 추가 최적화 기회
   - 파티셔닝 (1M+ 레코드 시)
   - 읽기 레플리카 (높은 동시성)
   - 애플리케이션 레벨 캐싱

파일: docs/PERFORMANCE_FINAL_REPORT.md

발표: PowerPoint 슬라이드 5-10장
- 그래프, 수치, 권고사항

승인 기준: 상세한 벤치마크 리포트 완성
```

**Task 4-3: PR 작성 및 병합** (06-20 ~ 06-21)

```markdown
목표: 최적화 코드를 main 브랜치에 병합

작업:
1. 성능 최적화 코드 PR
   - 신규 인덱스 생성 스크립트
   - 캐싱 서비스 코드
   - 마이그레이션 (Alembic)

2. 문서 PR
   - 성능 리포트
   - 쿼리 최적화 가이드
   - 모니터링 가이드

3. 코드 리뷰
   - Claude & Codex의 리뷰
   - 피드백 반영
   - 최종 승인

PR 템플릿:
```
## 성능 최적화

### 변경사항
- [x] 인덱스 5개 추가
- [x] 캐싱 서비스 구현
- [x] 쿼리 최적화 (2개 쿼리)

### 성능 개선
- Simple Lookup: 50ms → 45ms (10%)
- One-hop: 300ms → 250ms (17%)
- Two-hop: 1200ms → 950ms (21%)

### 테스트
- [x] 부하 테스트 통과
- [x] 캐싱 테스트 통과
- [x] 통합 테스트 통과

### 리뷰 필요
- [ ] Claude: API 통합
- [ ] Codex: UI 성능
```

승인 기준: 모든 PR 병합, main 브랜치 안정화
```

**Week 4 산출물**:
```
✅ app/services/cache_service.py (신규)
✅ tests/integration/test_caching.py (신규)
✅ docs/PERFORMANCE_FINAL_REPORT.md (신규)
✅ Alembic 마이그레이션 (인덱스 추가)
✅ 성능 최적화 PR
✅ Milestone: Week 4 완료 (2026-06-21)
```

---

### 📊 Antigravity 체크리스트

```
Week 2 (06-03 ~ 06-07):
  [ ] Task 2-1: 벡터 임베딩 캐싱 (06-04)
  [ ] Task 2-2: 의미 검색 테스트 (06-06)
  [ ] Task 2-3: 인덱스 분석 (06-07)
  [ ] 성능 리포트 1차 완성
  
Week 3 (06-10 ~ 06-14):
  [ ] Task 3-1: 부하 테스트 (06-12)
  [ ] Task 3-2: 쿼리 플래너 분석 (06-13)
  [ ] Task 3-3: 인덱스 최적화 (06-14)
  [ ] 신규 인덱스 5개 추가
  
Week 4 (06-17 ~ 06-21):
  [ ] Task 4-1: 캐싱 구현 (06-19)
  [ ] Task 4-2: 최종 벤치마크 (06-21)
  [ ] Task 4-3: PR 작성 및 병합 (06-21)
  [ ] 성능 목표 달성 (Simple <50ms, One-hop <300ms, Two-hop <1s)
```

---

---

## 🔄 협업 규칙

### 일정 동기화

```
🟢 **주간 스탠드업** (매주 월요일 9:00)
- 각 팀의 진행 상황 (5분)
- 블로킹 이슈 공유 (5분)
- 다음 주 목표 확인 (5분)

🔵 **통합 포인트** (주말)
- 코드 병합 검토
- 호환성 확인
- 성능 재측정
```

### 문서 규칙

```
📝 **커밋 메시지**
format: [Team] Task 번호 - 간단한 설명
예: [Claude] Task 2-1 - SPARQL translator architecture
    [Codex] Task 3-2 - Filter builder UI implementation
    [Antigravity] Task 3-1 - Load test 100K records

📋 **PR 템플릿**
- 담당 팀 명시
- 관련 이슈/PR 링크
- 성능 영향 (있으면)
- 테스트 결과

📌 **문서 위치**
- 설계: docs/
- 코드: src/backend/ or src/frontend/
- 테스트: tests/
- 리포트: docs/ (REPORT prefix)
```

### 코드 리뷰

```
🔴 **Critical** (반드시 리뷰)
- API 변경
- 데이터베이스 마이그레이션
- 성능 영향 > 10%

🟡 **Important** (권장)
- 핵심 로직 변경
- 테스트 추가
- 문서 업데이트

🟢 **Nice-to-have**
- 스타일 개선
- 주석 추가
- 리팩토링
```

### 문제 해결

```
문제 발생 시:
1. Slack/Email로 즉시 공유
   - 문제 설명
   - 영향 범위
   - 임시 우회 방법

2. 다른 팀 영향 검토
   - Claude 변경 → Codex/Antigravity 영향?
   - Codex 변경 → Claude/Antigravity 영향?

3. 함께 해결
   - 원인 분석 (15분)
   - 솔루션 논의 (15분)
   - 구현 + 테스트 (30분)

4. 사후 대응
   - 유사 문제 예방책
   - 테스트 추가
```

---

## 📅 마일스톤 및 체크포인트

### Week 2 (06-03 ~ 06-07) - 기초 완성

| 날짜 | Claude | Codex | Antigravity |
|------|--------|-------|-------------|
| 06-03 | 설계 시작 | QueryResult 개선 | 벡터 최적화 |
| 06-04 | 아키텍처 완성 | 실시간 UI | 임베딩 캐싱 |
| 06-05 | 구현 시작 | 시각화 기초 | 테스트 틀 |
| 06-06 | 40개 테스트 | 성능 차트 | 의미 검색 테스트 |
| 06-07 | 성능 검증 ✅ | UI 완성 ✅ | 인덱스 분석 ✅ |

### Week 3 (06-10 ~ 06-14) - 심화 개발

| 날짜 | Claude | Codex | Antigravity |
|------|--------|-------|-------------|
| 06-10 | API 엔드포인트 | 그래프 시각화 | 부하 테스트 |
| 06-11 | 엔드포인트 완성 | 필터 빌더 | 병목 분석 |
| 06-12 | 동시성 지원 | 필터 완성 | 부하 테스트 완료 |
| 06-13 | Swagger 문서 | 히스토리 저장 | 쿼리 최적화 |
| 06-14 | 문서 완성 ✅ | UI 완성 ✅ | 인덱스 최적화 ✅ |

### Week 4 (06-17 ~ 06-21) - 최종 완성

| 날짜 | Claude | Codex | Antigravity |
|------|--------|-------|-------------|
| 06-17 | 통합 테스트 | 반응형 레이아웃 | 캐싱 구현 |
| 06-18 | 통합 테스트 | 모바일 최적화 | 캐싱 완성 |
| 06-19 | 버그 수정 | 다크모드 | 벤치마크 리포트 |
| 06-20 | 성능 튜닝 | e2e 테스트 | 최종 리포트 |
| 06-21 | 최종 완성 ✅ | e2e 완성 ✅ | PR 병합 ✅ |

---

## 📊 산출물 요약

### Claude: Backend SPARQL 엔진
```
코드:
  ├── app/services/sparql_translator.py (500줄)
  ├── app/routes/sparql.py (150줄)
  └── app/db/ (모델 + 설정)

테스트:
  ├── tests/unit/test_sparql_translator.py (40개)
  ├── tests/integration/test_api_integration.py (15개)
  ├── tests/integration/test_concurrency.py (10개)
  └── tests/integration/test_full_suite.py (50개)

문서:
  ├── docs/SPARQL_TRANSLATOR_GUIDE.md
  ├── docs/API_GUIDE.md
  └── /docs (Swagger)

총 115+ 테스트
```

### Codex: Frontend UI/UX
```
컴포넌트:
  ├── QueryResult.tsx (개선)
  ├── EntityGraph.tsx (신규)
  ├── FilterBuilder.tsx (신규)
  ├── QueryHistory.tsx (신규)
  ├── PerformanceChart.tsx (신규)
  ├── ThemeToggle.tsx (신규)
  └── 반응형 CSS

테스트:
  └── cypress/e2e/ (15개 e2e 테스트)

문서:
  ├── docs/FRONTEND_UI.md
  ├── docs/FRONTEND_ADVANCED.md
  └── Component guide

총 15개 e2e 테스트
```

### Antigravity: Performance & Optimization
```
성능 도구:
  ├── app/services/embedding_service.py
  ├── app/services/cache_service.py
  └── tests/load/load_test.py

분석:
  ├── docs/VECTOR_SEARCH_REPORT.md
  ├── docs/LOAD_TEST_REPORT.md
  ├── docs/QUERY_OPTIMIZATION.md
  ├── docs/INDEX_ANALYSIS.md
  └── docs/PERFORMANCE_FINAL_REPORT.md

인덱스:
  ├── 5개+ 신규 인덱스
  ├── Alembic 마이그레이션
  └── 성능 개선 30-50%

테스트:
  └── tests/load/ + tests/integration/

총 5개+ 리포트 + 인덱스 최적화
```

---

## ✅ 성공 기준

### Code Quality
- [ ] 모든 테스트 통과 (115 + 15 + load tests)
- [ ] 코드 커버리지 ≥ 80%
- [ ] 린터/포맷터 통과 (Black, ESLint)
- [ ] 보안 취약점 0개

### Performance
- [ ] Simple Lookup: <50ms ✓
- [ ] One-hop Relation: <300ms ✓
- [ ] Two-hop Relation: <1000ms ✓
- [ ] 부하 테스트 (100 동시 사용자) 통과

### Features
- [ ] SPARQL→SQL 번역 (Supported Profile)
- [ ] FastAPI 엔드포인트 3개
- [ ] Frontend UI 완성 (반응형 + 다크모드)
- [ ] 의미 검색 정확도 >85%

### Documentation
- [ ] API 문서 (Swagger)
- [ ] 성능 가이드
- [ ] 배포 가이드
- [ ] 사용자 매뉴얼

---

## 🚀 시작 체크리스트 (2026-06-03)

### 모든 팀이 확인할 것

```
[ ] E:\ontology_edu\X_ont_std\ont_platform\v3\ 폴더 구조 확인
[ ] 각자 담당 폴더 확인
    [ ] Claude: app/services/, app/routes/, tests/integration/
    [ ] Codex: src/frontend/, cypress/
    [ ] Antigravity: tests/load/, docs/
[ ] .env 파일 설정 (DATABASE_URL)
[ ] 요구 패키지 설치 (pip install -r requirements.txt)
[ ] 로컬 PostgreSQL 시작 (docker-compose.dev.yml)
[ ] 테스트 한 번 실행 (pytest tests/ 또는 npm test)
[ ] 지시서 다시 읽기 (이 문서)
[ ] Slack/Email 채널 설정 (일일 동기화)
```

### 매일 확인할 것

```
[ ] 어제 타스크 완료? (예/아니오)
[ ] 오늘 목표 명확? (그날의 Task)
[ ] 블로킹 이슈? (있으면 Slack)
[ ] 다른 팀 영향?
```

---

## 📞 연락처 & 질문

문제 발생 시:
1. **Slack #dev-ont-platform**: 실시간 질문
2. **Email**: 정식 문서 공유
3. **Weekly Sync (월 9:00)**: 진행 상황 공유

---

**지시서 최종 확인**: 2026-05-24  
**구현 시작 일정**: 2026-06-03  
**최종 완료 목표**: 2026-06-21

---
