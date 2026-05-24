# SPARQL→SQL 번역기 설계 문서

> **목적**: ont_platform v3에서 표준 SPARQL 쿼리를 PostgreSQL SQL로 변환  
> **작성일**: 2026-05-24  
> **상태**: 📋 설계 문서, 🔴 구현 대기  
> **범위**: 50개 쿼리 패턴 지원  

---

## 📋 Executive Summary

| 항목 | 설명 |
|------|------|
| **목표** | 사용자는 SPARQL 작성, 시스템은 SQL 실행 (Supported Profile) |
| **입력** | SPARQL 쿼리 (표준 호환, rdflib 파서 사용) |
| **출력** | PostgreSQL SELECT 쿼리 (또는 rdflib fallback) |
| **성능** | 변환 시간 < 10ms |
| **정확도** | Supported Profile 50개 패턴 정확한 SQL 생성, 미지원은 명확한 에러 |

---

## 0. SPARQL Support Matrix

### Supported Profile (SQL 직접 번역)

| Category | Pattern | SQL 변환 | 예시 |
|----------|---------|---------|------|
| **SELECT** | 기본 SELECT | Direct | `SELECT ?name WHERE { ?s ex:name ?name }` |
| **Type Query** | rdf:type 매칭 | entity_type = ? | `?x rdf:type ex:Person` |
| **Property** | 속성 조회 | properties->>'key' = ? | `?x ex:age 30` |
| **Simple Filter** | FILTER (비교) | WHERE 절 | `FILTER (?age > 25)` |
| **One-hop Join** | 단일 관계 | INNER JOIN | `?x ex:knows ?y` |
| **Limit/Offset** | LIMIT, OFFSET | LIMIT, OFFSET | 페이징 지원 |

### Fallback Profile (rdflib 메모리 실행)

| Category | Pattern | 처리 방식 | 주의 |
|----------|---------|---------|------|
| **Property Path** | `foaf:knows+` (전이) | rdflib fallback | 성능 저하, 소규모만 권장 |
| **OPTIONAL** | LEFT JOIN 복잡 | rdflib 또는 부분 SQL | 조건부 변환 |
| **UNION** | 다중 패턴 | rdflib 실행 | SQL 최적화 없음 |
| **CONSTRUCT** | RDF 생성 | rdflib 실행 | SELECT 후 변환 |
| **DESCRIBE** | 리소스 정보 | rdflib 실행 | 전체 속성 반환 |

### Unsupported (에러 반환)

| Category | Pattern | 이유 |
|----------|---------|------|
| **Dynamic Predicate** | `?x ?predicate ?y` | 동적 열 선택 불가 |
| **Federation** | SERVICE | 외부 연동 미지원 |
| **Complex Reasoning** | 추론 기반 쿼리 | Offline 처리 필요 |

---

## 1. 아키텍처 개요

### 1.1 처리 파이프라인

```
Input: SPARQL Query String
  ↓
[1] Lexical Analysis (rdflib)
  - 토큰화
  - 문법 검증
  ↓
[2] Semantic Analysis
  - PREFIX 확인
  - 변수 바인딩
  - 패턴 추출
  ↓
[3] Query Planning
  - 패턴 정렬 (카디널리티 기반)
  - JOIN 최적화
  - 인덱스 선택
  ↓
[4] Code Generation
  - SQL 문자열 생성
  - 파라미터화 (?로 표현)
  ↓
Output: SQL Query String
```

### 1.2 클래스 설계

```python
# app/services/sparql_translator.py

class SPARQLTranslator:
    """SPARQL → SQL 번역 엔진"""
    
    def __init__(self, graph_schema: GraphSchema):
        self.schema = graph_schema  # 온톨로지 메타데이터
        self.pattern_cache = {}  # 컴파일된 패턴 캐시
    
    def translate(self, sparql_query: str) -> TranslatedQuery:
        """
        SPARQL 쿼리를 SQL로 변환
        
        Args:
            sparql_query: SPARQL 1.1 쿼리
        
        Returns:
            TranslatedQuery(sql, params, variables)
        
        Raises:
            SPARQLSyntaxError: 쿼리 파싱 실패
            TranslationError: SQL 변환 실패
        """
        pass
    
    def _parse_sparql(self, query: str) -> ParsedQuery:
        """rdflib를 사용하여 SPARQL 파싱"""
        pass
    
    def _extract_patterns(self, parsed) -> List[TriplePattern]:
        """WHERE 절에서 Triple Pattern 추출"""
        pass
    
    def _plan_execution(self, patterns: List[TriplePattern]) -> ExecutionPlan:
        """쿼리 실행 계획 수립"""
        pass
    
    def _generate_sql(self, plan: ExecutionPlan) -> str:
        """SQL 문자열 생성"""
        pass

class TriplePattern:
    """SPARQL Triple Pattern 표현"""
    subject: Union[str, Variable]  # URI 또는 변수
    predicate: Union[str, Variable]
    obj: Union[str, Literal, Variable]

class TranslatedQuery:
    sql: str  # "SELECT ... FROM ... WHERE ..."
    params: Dict[str, Any]  # SQL 파라미터
    variables: List[str]  # 반환 변수 (?x, ?name 등)
```

---

## 2. 핵심 알고리즘

### 2.1 Triple Pattern → SQL Table Mapping

**규칙**:

```
Triple Pattern: (?person, ex:type, "Person")
↓ 매핑 규칙 적용 ↓

Case 1: 모두 상수 (검증용)
  SELECT COUNT(*) FROM entities 
  WHERE entity_type = 'Person'

Case 2: 주어만 변수 (?x, predicate, object)
  SELECT id FROM entities 
  WHERE properties->>'type' = 'Person'

Case 3: 주어 + 목적어 변수 (?x, predicate, ?y)
  SELECT e.id, e.properties->>'type'
  FROM entities e
  WHERE entity_type = 'someType'

Case 4: 관계 포함 (?x, ex:works_at, ?company)
  SELECT e1.id, e2.id
  FROM entities e1
  JOIN relationships r ON e1.id = r.from_entity_id
  JOIN entities e2 ON r.to_entity_id = e2.id
  WHERE r.relation_type = 'works_at'
```

**온톨로지 메타데이터**:

```python
PREDICATE_MAPPING = {
    # 엔티티 속성 (properties JSONB)
    'http://example.org/name': ('entities', 'properties->>name'),
    'http://example.org/age': ('entities', 'properties->>age'),
    'http://example.org/type': ('entities', 'entity_type'),
    
    # 관계 (relationships 테이블)
    'http://example.org/works_at': ('relationships', 'works_at'),
    'http://example.org/knows': ('relationships', 'knows'),
}
```

### 2.2 JOIN 최적화

**패턴 순서 결정** (카디널리티):

```
입력 패턴 (임의 순서):
1. (?person, ex:type, "Person")        # 선택도 낮음 (10%)
2. (?person, ex:name, ?name)           # 모든 행 (100%)
3. (?person, ex:works_at, ?company)    # 관계 (50%)

↓ 카디널리티 추정 ↓

정렬된 순서:
1. (?person, ex:type, "Person")        # 100 결과
2. (?person, ex:works_at, ?company)    # 50 결과 JOIN 1
3. (?person, ex:name, ?name)           # 간단한 프로젝션

생성 SQL:
SELECT e.id, e.properties->>'name', c.id
FROM entities e
WHERE e.entity_type = 'Person'  -- 먼저 필터링
JOIN relationships r ON e.id = r.from_entity_id
  AND r.relation_type = 'works_at'
JOIN entities c ON r.to_entity_id = c.id
```

### 2.3 FILTER 조건 변환

```
SPARQL:
WHERE {
  ?person ex:name ?name ;
          ex:age ?age
  FILTER (?age > 25 && STRLEN(?name) > 3)
}

↓ 변환 ↓

SQL:
WHERE
  (e.properties->>'age')::INTEGER > 25
  AND STRLEN(e.properties->>'name') > 3
```

**지원하는 함수**:

| SPARQL | PostgreSQL | 예시 |
|--------|-----------|------|
| `STRLEN(?x)` | `LENGTH()` | `LENGTH(text)` |
| `UPPER(?x)` | `UPPER()` | `UPPER(text)` |
| `LOWER(?x)` | `LOWER()` | `LOWER(text)` |
| `CONTAINS(?x, "str")` | `LIKE` | `text LIKE '%str%'` |
| `REGEX(?x, "pattern")` | `~` | `text ~ 'pattern'` |
| `?x > 5` | `>` | `(col)::INTEGER > 5` |
| `?x = "value"` | `=` | `col = 'value'` |

---

## 3. 지원 쿼리 패턴 (50개)

### 그룹 A: 기본 SELECT (10개)

```sparql
1. 모든 엔티티 조회
   SELECT ?x WHERE { ?x a ex:Person }
   SQL: SELECT id FROM entities WHERE entity_type = 'Person'

2. 특정 속성 선택
   SELECT ?name WHERE { ?x ex:name ?name }
   SQL: SELECT properties->>'name' FROM entities

3. 변수 바인딩
   SELECT ?x ?name WHERE { ?x ex:name ?name }
   SQL: SELECT id, properties->>'name' FROM entities

4. DISTINCT
   SELECT DISTINCT ?type WHERE { ?x a ?type }
   SQL: SELECT DISTINCT entity_type FROM entities

5. LIMIT
   SELECT ?x WHERE { ?x a ex:Person } LIMIT 10
   SQL: ... LIMIT 10

6. OFFSET
   SELECT ?x WHERE { ?x a ex:Person } OFFSET 5 LIMIT 10
   SQL: ... OFFSET 5 LIMIT 10

7. ORDER BY (오름차순)
   SELECT ?x ?age WHERE { ?x ex:age ?age } ORDER BY ?age
   SQL: ... ORDER BY age ASC

8. ORDER BY (내림차순)
   SELECT ?x ?age WHERE { ?x ex:age ?age } ORDER BY DESC(?age)
   SQL: ... ORDER BY age DESC

9. 다중 변수 정렬
   SELECT ?x WHERE { ... } ORDER BY ?type ?name
   SQL: ... ORDER BY entity_type ASC, name ASC

10. 빈 결과
    SELECT ?x WHERE { ?x ex:nonExistent ?y }
    SQL: SELECT id FROM entities WHERE id NOT IN (...)
```

### 그룹 B: FILTER (10개)

```sparql
11. 비교 연산자 (>)
    WHERE { ?x ex:age ?age FILTER (?age > 25) }
    SQL: WHERE (age)::INTEGER > 25

12. 비교 연산자 (<)
    WHERE { ?x ex:age ?age FILTER (?age < 25) }
    SQL: WHERE (age)::INTEGER < 25

13. 등호 (=)
    WHERE { ?x ex:name ?name FILTER (?name = "Alice") }
    SQL: WHERE name = 'Alice'

14. 부등호 (!=)
    WHERE { ?x ex:type ?t FILTER (?t != "Bot") }
    SQL: WHERE type != 'Bot'

15. 논리 AND (&&)
    WHERE { ?x ex:age ?a FILTER (?a > 20 && ?a < 30) }
    SQL: WHERE age > 20 AND age < 30

16. 논리 OR (||)
    WHERE { ?x ex:type ?t FILTER (?t = "Person" || ?t = "Bot") }
    SQL: WHERE type = 'Person' OR type = 'Bot'

17. 논리 NOT (!)
    WHERE { ?x ex:type ?t FILTER (!(?t = "Bot")) }
    SQL: WHERE NOT (type = 'Bot')

18. STRLEN (문자열 길이)
    WHERE { ?x ex:name ?n FILTER (STRLEN(?n) > 5) }
    SQL: WHERE LENGTH(name) > 5

19. REGEX (정규식)
    WHERE { ?x ex:name ?n FILTER REGEX(?n, "^A") }
    SQL: WHERE name ~ '^A'

20. CONTAINS (포함 검사)
    WHERE { ?x ex:desc ?d FILTER CONTAINS(?d, "urgent") }
    SQL: WHERE desc LIKE '%urgent%'
```

### 그룹 C: JOIN (10개)

```sparql
21. 1-N 관계 (기본)
    WHERE {
      ?person ex:works_at ?company
      ?company ex:type "Company"
    }
    SQL: JOIN relationships + entities

22. 다중 JOIN (A→B→C)
    WHERE {
      ?person ex:works_at ?company
      ?company ex:located_in ?city
      ?city ex:name ?city_name
    }
    SQL: 3개 JOIN

23. 같은 엔티티 다중 속성
    WHERE {
      ?x ex:name ?name ;
         ex:age ?age ;
         ex:email ?email
    }
    SQL: 1개 테이블에서 JSONB 추출

24. 자기참조 관계
    WHERE {
      ?person1 ex:knows ?person2
      ?person2 ex:knows ?person3
    }
    SQL: relationships 테이블 자기 JOIN

25. 선택적 JOIN (OPTIONAL)
    WHERE {
      ?x ex:name ?name
      OPTIONAL { ?x ex:phone ?phone }
    }
    SQL: LEFT JOIN

26. UNION (두 패턴)
    WHERE {
      { ?x ex:type "Person" }
      UNION
      { ?x ex:type "Organization" }
    }
    SQL: UNION (두 SELECT)

27. UNION (세 패턴)
    WHERE {
      { ?x ex:type "Person" }
      UNION
      { ?x ex:type "Organization" }
      UNION
      { ?x ex:type "Project" }
    }
    SQL: UNION (세 SELECT)

28. 중첩된 패턴
    WHERE {
      ?person ex:works_at ?company
      { ?company ex:size "Large" }
      UNION
      { ?company ex:founding_year ?y FILTER (?y > 2000) }
    }
    SQL: JOIN + (SELECT UNION SELECT)

29. 관계 + 속성 필터
    WHERE {
      ?a ex:knows ?b
      ?b ex:age ?age
      FILTER (?age > 30)
    }
    SQL: JOIN relationships + entities + WHERE

30. 관계 타입 필터
    WHERE {
      ?a ex:knows ?b
      ?b ex:type "Professional"
    }
    SQL: JOIN with relation_type + entity_type
```

### 그룹 D: 집계 (10개)

```sparql
31. COUNT (모든 행)
    SELECT (COUNT(?x) as ?count) WHERE { ?x a ex:Person }
    SQL: SELECT COUNT(*) FROM entities WHERE entity_type = 'Person'

32. COUNT (DISTINCT)
    SELECT (COUNT(DISTINCT ?type) as ?count) WHERE { ?x a ?type }
    SQL: SELECT COUNT(DISTINCT entity_type) FROM entities

33. SUM
    SELECT (SUM(?salary) as ?total) WHERE { ?x ex:salary ?salary }
    SQL: SELECT SUM((salary)::NUMERIC) FROM entities

34. AVG
    SELECT (AVG(?age) as ?avg_age) WHERE { ?x ex:age ?age }
    SQL: SELECT AVG((age)::NUMERIC) FROM entities

35. MIN
    SELECT (MIN(?age) as ?min_age) WHERE { ?x ex:age ?age }
    SQL: SELECT MIN((age)::NUMERIC) FROM entities

36. MAX
    SELECT (MAX(?age) as ?max_age) WHERE { ?x ex:age ?age }
    SQL: SELECT MAX((age)::NUMERIC) FROM entities

37. GROUP BY (1개 열)
    SELECT ?type (COUNT(?x) as ?count) 
    WHERE { ?x a ?type } 
    GROUP BY ?type
    SQL: SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type

38. GROUP BY (다중 열)
    SELECT ?type ?status (COUNT(?x) as ?count)
    WHERE { ?x a ?type ; ex:status ?status }
    GROUP BY ?type ?status
    SQL: GROUP BY entity_type, status

39. HAVING (그룹 필터)
    SELECT ?type (COUNT(?x) as ?count)
    WHERE { ?x a ?type }
    GROUP BY ?type
    HAVING (?count > 5)
    SQL: GROUP BY ... HAVING COUNT(*) > 5

40. 집계 + JOIN
    SELECT ?company (COUNT(?person) as ?headcount)
    WHERE { ?person ex:works_at ?company }
    GROUP BY ?company
    SQL: JOIN + GROUP BY
```

### 그룹 E: 고급 (10개)

```sparql
41. CONSTRUCT (새 RDF 생성)
    CONSTRUCT { ?x ex:label ?name }
    WHERE { ?x ex:name ?name }
    SQL: SELECT id, name FROM entities (후처리로 RDF 생성)

42. DESCRIBE (리소스 전체 정보)
    DESCRIBE ?x
    WHERE { ?x a ex:Person }
    SQL: SELECT * FROM entities WHERE entity_type = 'Person'

43. ASK (불리언 결과)
    ASK { ?x ex:type "Person" }
    SQL: SELECT COUNT(*) > 0 FROM entities WHERE entity_type = 'Person'

44. 다중 조건 WHERE
    WHERE {
      ?x a ex:Person
      ?x ex:age ?age
      ?x ex:salary ?salary
      FILTER (?age > 25 && ?salary > 50000)
    }
    SQL: WHERE entity_type = 'Person' AND age > 25 AND salary > 50000

45. OPTIONAL + 필터
    WHERE {
      ?x ex:name ?name
      OPTIONAL { ?x ex:phone ?phone FILTER STRLEN(?phone) > 0 }
    }
    SQL: LEFT JOIN + FILTER

46. 중첩 FILTER
    WHERE {
      ?x ex:age ?age
      FILTER (
        (?age > 20 && ?age < 30) 
        || 
        (?age > 60)
      )
    }
    SQL: WHERE (age > 20 AND age < 30) OR (age > 60)

47. 변수 재사용
    WHERE {
      ?x ex:manager ?manager
      ?manager ex:manager ?ceo
      ?ceo ex:manager ?ceo  -- 자기 자신이 매니저
    }
    SQL: 자기참조 JOIN (3번)

48. 동적 바인딩
    WHERE {
      ?x ex:type ?type
      ?x ?predicate "someValue"  -- ?predicate는 변수
    }
    SQL: 동적 열 선택 (불가능한 경우 주의!)

49. 조건부 JOIN
    WHERE {
      ?x a ex:Person
      ?x ex:works_at ?company
      FILTER BOUND(?company)  -- company가 바인딩됨
    }
    SQL: WHERE company IS NOT NULL

50. 통합 복잡 쿼리
    SELECT ?person_name ?company_name (COUNT(?project) as ?projects)
    WHERE {
      ?person ex:name ?person_name ;
              ex:works_at ?company ;
              ex:manages ?project
      ?company ex:name ?company_name
      OPTIONAL { ?project ex:status ?status }
      FILTER (?status != "Cancelled")
    }
    GROUP BY ?person_name ?company_name
    ORDER BY ?projects DESC
    LIMIT 10
```

---

## 4. 구현 상세

### 4.1 Variable 추적

```python
class VariableTracker:
    """SPARQL 변수 바인딩 추적"""
    
    def __init__(self):
        self.bindings = {}  # 변수 → SQL 열 매핑
        self.aliases = {}   # 테이블 별칭
    
    def bind_variable(self, var_name: str, sql_expr: str):
        """변수를 SQL 표현식에 매핑"""
        self.bindings[var_name] = sql_expr
    
    def get_sql_expr(self, var_name: str) -> str:
        """변수의 SQL 표현식 반환"""
        return self.bindings.get(var_name)
    
    def get_table_alias(self, table_name: str) -> str:
        """테이블의 별칭 생성/반환 (e, e1, e2, ...)"""
        if table_name not in self.aliases:
            num = len(self.aliases) + 1
            self.aliases[table_name] = f"{table_name[0]}{num}"
        return self.aliases[table_name]
```

### 4.2 JOIN 생성

```python
class JoinPlanner:
    """JOIN 계획 수립"""
    
    def plan_joins(self, patterns: List[TriplePattern]) -> List[JoinClause]:
        """
        Triple Pattern 리스트를 SQL JOIN 클로즈로 변환
        
        입력:
        [
          (?person, ex:type, "Person"),
          (?person, ex:works_at, ?company),
          (?company, ex:type, "Company")
        ]
        
        출력:
        [
          SELECT e1.* FROM entities e1 WHERE e1.entity_type = 'Person',
          JOIN relationships r ON e1.id = r.from_entity_id 
               AND r.relation_type = 'works_at',
          JOIN entities e2 ON r.to_entity_id = e2.id 
               AND e2.entity_type = 'Company'
        ]
        """
        pass
    
    def _estimate_cardinality(self, pattern: TriplePattern) -> int:
        """패턴 결과 예상 행 수"""
        # 통계 기반 추정 (PostgreSQL 통계)
        pass
    
    def _reorder_patterns(self, patterns: List[TriplePattern]) -> List[TriplePattern]:
        """카디널리티 기반 패턴 정렬 (최적화)"""
        # 선택도 높은 패턴부터 처리 (필터링)
        pass
```

### 4.3 FILTER 구문 분석

```python
class FilterTranslator:
    """FILTER 조건을 SQL WHERE 절로 변환"""
    
    def translate_filter(self, filter_expr: FilterExpression) -> str:
        """
        FILTER (?age > 25 && STRLEN(?name) > 3)
        →
        (age)::INTEGER > 25 AND LENGTH(name) > 3
        """
        pass
    
    def _translate_comparison(self, op: str, left: str, right: str) -> str:
        """비교 연산자 변환: > < = !="""
        mapping = {
            '>': '>',
            '<': '<',
            '=': '=',
            '!=': '!='
        }
        return f"{left} {mapping[op]} {right}"
    
    def _translate_function_call(self, func_name: str, args: List[str]) -> str:
        """함수 호출 변환: STRLEN, UPPER, REGEX"""
        mapping = {
            'STRLEN': lambda x: f"LENGTH({x})",
            'UPPER': lambda x: f"UPPER({x})",
            'LOWER': lambda x: f"LOWER({x})",
            'REGEX': lambda *x: f"{x[0]} ~ {x[1]}",
        }
        return mapping[func_name](*args)
```

---

## 5. 에러 처리

```python
class SPARQLSyntaxError(Exception):
    """SPARQL 문법 오류"""
    pass

class TranslationError(Exception):
    """SQL 변환 오류"""
    pass

class UnsupportedPatternError(TranslationError):
    """지원하지 않는 패턴"""
    def __init__(self, pattern: str):
        super().__init__(f"Unsupported pattern: {pattern}")
```

---

## 6. 테스트 전략

### 6.1 단위 테스트 (40개)

```python
# tests/unit/test_sparql_translator.py

def test_simple_select():
    """기본 SELECT 변환"""
    query = "SELECT ?x WHERE { ?x a ex:Person }"
    sql = translator.translate(query).sql
    assert "SELECT" in sql
    assert "FROM entities" in sql

def test_filter_numeric():
    """숫자 FILTER 변환"""
    query = "SELECT ?x WHERE { ?x ex:age ?a FILTER (?a > 25) }"
    sql = translator.translate(query).sql
    assert "(age)::INTEGER > 25" in sql

def test_join_relationship():
    """관계 JOIN 변환"""
    query = "SELECT ?p ?c WHERE { ?p ex:works_at ?c }"
    sql = translator.translate(query).sql
    assert "JOIN relationships" in sql
    assert "FROM entities" in sql
```

### 6.2 통합 테스트 (50개 + E2E)

```python
# tests/integration/test_translator_e2e.py

def test_query_against_postgres():
    """실제 데이터로 쿼리 검증"""
    # 1. PostgreSQL에 데이터 삽입
    db.insert_entity("person1", "Person", {"name": "Alice", "age": 30})
    
    # 2. SPARQL 쿼리 실행
    sparql = "SELECT ?name WHERE { ?x a ex:Person ; ex:name ?name }"
    result = translator.execute(sparql)
    
    # 3. 결과 검증
    assert result.variables == ["name"]
    assert result.rows[0]["name"] == "Alice"
```

---

## 7. 성능 최적화

### 7.1 쿼리 캐싱

```python
class TranslatorCache:
    """변환된 쿼리 캐싱"""
    
    def __init__(self, max_size=1000):
        self.cache = {}
    
    def get(self, query: str) -> Optional[TranslatedQuery]:
        """캐시에서 조회"""
        hash_key = hashlib.sha256(query.encode()).hexdigest()
        return self.cache.get(hash_key)
    
    def put(self, query: str, translated: TranslatedQuery):
        """캐시에 저장"""
        hash_key = hashlib.sha256(query.encode()).hexdigest()
        self.cache[hash_key] = translated
        # LRU 제거 로직
```

### 7.2 Index Hints

```python
def add_index_hints(sql: str, schema: GraphSchema) -> str:
    """인덱스 힌트 추가"""
    if "WHERE entity_type" in sql:
        # entity_type 인덱스 사용 권장
        sql = sql.replace(
            "FROM entities e",
            "FROM entities e /*+ INDEX(e idx_entities_type) */"
        )
    return sql
```

---

## 8. 제약사항 (알려진 한계)

```
❌ 지원 안 함:
1. 동적 패턴 (?x ?predicate ?y) - 열 이름이 동적
2. 그래프 트래버설 (property path) - ?x foaf:knows*/knows+ ?y
3. SPARQL 엔드포인트 페더레이션 - 외부 쿼리 금지
4. 언어 태그 필터링 - @en, @ko 등

✅ 지원 함:
- 기본 SELECT, CONSTRUCT, DESCRIBE, ASK
- FILTER (논리/비교/함수)
- JOIN (OPTIONAL, UNION)
- 집계 (COUNT, SUM, AVG, MIN, MAX)
- GROUP BY, HAVING, ORDER BY, LIMIT
```

---

## 9. 배포 및 운영

### 9.1 마이그레이션 체크리스트

- [ ] 50개 쿼리 패턴 모두 테스트 통과
- [ ] PostgreSQL에서 실행 및 결과 검증
- [ ] 성능 벤치마크 (< 10ms 변환 시간)
- [ ] 실제 온톨로지 데이터 통합 테스트

### 9.2 모니터링

```python
class TranslatorMetrics:
    """번역기 성능 메트릭"""
    
    def record_translation(self, query: str, duration_ms: float):
        """변환 시간 기록"""
        metrics["translation_time"].observe(duration_ms)
        metrics["translated_queries"].inc()
```

---

## 10. 향후 확장

```
Phase 2 (2026-07):
- Property Path 지원 (?x foaf:knows+ ?y)
- 추론 규칙 (RDFS, OWL)
- 스키마 진화 (온톨로지 버전 관리)

Phase 3 (2026-08+):
- 페더레이션 쿼리 (여러 데이터소스)
- 그래프 알고리즘 (최단경로, 중심성)
- 실시간 스트리밍 (변경 알림)
```

---

**다음**: SCHEMA_DESIGN.md 참조 (PostgreSQL DDL)
