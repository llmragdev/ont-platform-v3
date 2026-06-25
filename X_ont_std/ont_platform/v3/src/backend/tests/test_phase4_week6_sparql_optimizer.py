"""Phase 4 Week 6: SPARQL 쿼리 최적화 엔진 테스트"""
import pytest
import time
from app.services.sparql_query_optimizer import (
    SPARQLQueryOptimizer,
    QueryPattern,
)


class TestTask61SPARQLOptimizer:
    """SPARQL 쿼리 재작성 엔진 테스트"""

    @pytest.fixture
    def optimizer(self):
        return SPARQLQueryOptimizer()

    def test_01_simple_query_parsing(self, optimizer):
        """1. 간단한 쿼리 파싱"""
        query = """
        SELECT ?name
        WHERE {
            ?person a Person .
            ?person name ?name .
        }
        """

        patterns, filters, query_type = optimizer._parse_query(query)

        assert query_type == "SELECT"
        assert len(patterns) >= 1
        assert any("name" in p.predicate for p in patterns)

    def test_02_filter_extraction(self, optimizer):
        """2. FILTER 조건 추출"""
        query = """
        SELECT ?name
        WHERE {
            ?person name ?name .
            FILTER (?name = "Alice")
        }
        """

        patterns, filters, query_type = optimizer._parse_query(query)

        assert len(filters) > 0
        assert any("name" in f for f in filters)

    def test_03_optional_pattern_detection(self, optimizer):
        """3. OPTIONAL 패턴 감지"""
        query = """
        SELECT ?name ?phone
        WHERE {
            ?person ?name ?name .
            OPTIONAL { ?person ?phone ?phone . }
        }
        """

        patterns, filters, query_type = optimizer._parse_query(query)

        # 최소한 패턴이 추출되어야 함
        assert len(patterns) > 0

    def test_04_filter_pushdown(self, optimizer):
        """4. FILTER 푸시다운"""
        patterns = [
            QueryPattern("?x", "type", "Person", is_optional=False),
            QueryPattern("?x", "name", "?name", is_optional=False),
        ]
        filters = ["?name = 'Alice'"]

        optimized = optimizer._pushdown_filters(patterns, filters)

        # 최적화가 완료되어야 함
        assert len(optimized) > 0
        assert all(isinstance(p, QueryPattern) for p in optimized)

    def test_05_selectivity_estimation(self, optimizer):
        """5. 선택도 추정"""
        # 상수 객체: 낮은 선택도
        pattern_constant = QueryPattern("?x", "type", "Person")
        selectivity_const = optimizer._estimate_selectivity(pattern_constant)

        # 변수만: 높은 선택도
        pattern_variable = QueryPattern("?x", "?p", "?o")
        selectivity_var = optimizer._estimate_selectivity(pattern_variable)

        assert selectivity_const < selectivity_var

    def test_06_join_reordering(self, optimizer):
        """6. 조인 순서 최적화"""
        patterns = [
            QueryPattern("?x", "?p", "?o"),  # 높은 선택도
            QueryPattern("?person", "type", "Person"),  # 낮은 선택도
            QueryPattern("?person", "name", "?name"),  # 중간 선택도
        ]

        reordered = optimizer._reorder_joins(patterns)

        # 낮은 선택도 패턴이 먼저 와야 함
        assert reordered[0].obj == "Person"

    def test_07_optional_separation(self, optimizer):
        """7. OPTIONAL 패턴 분리"""
        patterns = [
            QueryPattern("?x", "name", "?name", is_optional=False),
            QueryPattern("?x", "phone", "?phone", is_optional=True),
            QueryPattern("?x", "email", "?email", is_optional=False),
        ]

        separated = optimizer._separate_optional_patterns(patterns)

        # 필수 패턴이 먼저, OPTIONAL 패턴이 나중
        required_indices = [
            i for i, p in enumerate(separated) if not p.is_optional
        ]
        optional_indices = [i for i, p in enumerate(separated) if p.is_optional]

        if required_indices and optional_indices:
            assert max(required_indices) < min(optional_indices)

    def test_08_variable_extraction(self, optimizer):
        """8. 변수 추출"""
        text = "?person a Person . FILTER (?age > 18)"
        variables = optimizer._extract_variables(text)

        assert "person" in variables
        assert "age" in variables

    def test_09_optimization_timing(self, optimizer):
        """9. 최적화 시간 (< 50ms)"""
        query = """
        SELECT ?name ?age
        WHERE {
            ?person type Person .
            ?person name ?name .
            ?person age ?age .
            ?person city ?city .
            FILTER (?age > 18)
            OPTIONAL { ?person phone ?phone . }
        }
        """

        start_time = time.time()
        optimized = optimizer.optimize_query(query)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 50, f"Optimization took {elapsed_ms}ms (expected < 50ms)"
        assert len(optimized) > 0

    def test_10_query_correctness(self, optimizer):
        """10. 최적화 후 쿼리 정확성 (SELECT 절 보존)"""
        query = """
        SELECT ?name ?age
        WHERE {
            ?person name ?name .
            ?person age ?age .
        }
        """

        optimized = optimizer.optimize_query(query)

        # SELECT 절이 보존되어야 함
        assert "SELECT" in optimized.upper()
        assert "?name" in optimized
        assert "?age" in optimized

    def test_11_complex_query_with_multiple_filters(self, optimizer):
        """11. 복잡한 쿼리 (여러 FILTER)"""
        query = """
        SELECT ?name
        WHERE {
            ?person name ?name .
            ?person age ?age .
            ?person city ?city .
            FILTER (?age > 18)
            FILTER (?city = "Seoul")
        }
        """

        optimized = optimizer.optimize_query(query)
        assert "WHERE" in optimized

    def test_12_ask_query_optimization(self, optimizer):
        """12. ASK 쿼리 최적화"""
        query = """
        ASK WHERE {
            ?person type Person .
            ?person name "Alice" .
        }
        """

        patterns, filters, query_type = optimizer._parse_query(query)
        assert query_type == "ASK"

    def test_13_construct_query_optimization(self, optimizer):
        """13. CONSTRUCT 쿼리 최적화"""
        query = """
        CONSTRUCT { ?person name ?name . }
        WHERE {
            ?person name ?name .
        }
        """

        patterns, filters, query_type = optimizer._parse_query(query)
        assert query_type == "CONSTRUCT"

    def test_14_empty_query_handling(self, optimizer):
        """14. 빈 쿼리 처리"""
        result = optimizer.optimize_query("")
        assert result == ""

    def test_15_invalid_query_handling(self, optimizer):
        """15. 유효하지 않은 쿼리 처리"""
        invalid_query = "SELECT * FROM table"
        result = optimizer.optimize_query(invalid_query)

        # 유효하지 않은 쿼리는 원본 반환
        assert result == invalid_query

    def test_16_optimization_stats(self, optimizer):
        """16. 최적화 통계 조회"""
        stats = optimizer.get_optimization_stats()

        assert "total_optimizations" in stats
        assert "avg_improvement" in stats
        assert "history" in stats

    def test_17_constant_detection(self, optimizer):
        """17. 상수 판별"""
        assert optimizer._is_constant("Person")
        assert optimizer._is_constant('"Alice"')
        assert not optimizer._is_constant("?name")

    def test_18_variable_detection(self, optimizer):
        """18. 변수 판별"""
        assert optimizer._is_variable("?name")
        assert optimizer._is_variable("?person")
        assert not optimizer._is_variable("Person")
        assert not optimizer._is_variable('"Alice"')

    def test_19_pattern_variable_extraction(self, optimizer):
        """19. 패턴에서 변수 추출"""
        pattern = QueryPattern("?person", "?p", "?name")
        variables = optimizer._get_pattern_variables(pattern)

        assert "?person" in variables
        assert "?p" in variables
        assert "?name" in variables
        assert len(variables) == 3

    def test_20_large_query_optimization(self, optimizer):
        """20. 대형 쿼리 최적화"""
        # 많은 패턴의 쿼리
        patterns_str = "\n".join(
            [f"?x property{i} ?o{i} ." for i in range(50)]
        )
        query = f"""
        SELECT ?x
        WHERE {{
            {patterns_str}
        }}
        """

        start_time = time.time()
        optimized = optimizer.optimize_query(query)
        elapsed_ms = (time.time() - start_time) * 1000

        assert optimized is not None
        assert elapsed_ms < 100, f"Large query optimization took {elapsed_ms}ms"


class TestTask62CacheManager:
    """쿼리 캐싱 매니저 테스트"""

    def test_01_cache_initialization(self):
        """1. 캐시 초기화"""
        from app.services.sparql_query_cache import SPARQLQueryCache

        cache = SPARQLQueryCache(ttl_seconds=300)
        stats = cache.get_stats()

        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0
        assert stats["cache_size"] == 0

    def test_02_cache_hit_and_miss(self):
        """2. 캐시 히트/미스"""
        from app.services.sparql_query_cache import SPARQLQueryCache

        cache = SPARQLQueryCache()
        query = "SELECT ?name WHERE { ?x name ?name . }"
        graph_hash = "hash_123"

        # 미스
        result = cache.get(query, graph_hash)
        assert result is None

        # 저장
        cache.set(query, graph_hash, ["result1"])

        # 히트
        result = cache.get(query, graph_hash)
        assert result == ["result1"]

        stats = cache.get_stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
