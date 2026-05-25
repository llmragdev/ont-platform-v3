"""Phase 4 Week 6: 통합 테스트 (SPARQL 최적화 + 비동기 파이프라인)"""
import pytest
import asyncio
import time
from app.services.sparql_query_optimizer import SPARQLQueryOptimizer
from app.services.sparql_query_cache import SPARQLQueryCache, RDFGraphIndexer
from app.services.async_pipeline import SPARQLPipeline, ParallelImportEngine


class TestWeek6Integration:
    """Week 6 통합 테스트"""

    @pytest.fixture
    def optimizer(self):
        return SPARQLQueryOptimizer()

    @pytest.fixture
    def cache(self):
        return SPARQLQueryCache(ttl_seconds=300)

    @pytest.fixture
    def indexer(self):
        triples = [
            ("?person", "name", "?name"),
            ("?person", "age", "?age"),
            ("?person", "email", "?email"),
        ]
        return RDFGraphIndexer(triples)

    @pytest.fixture
    def pipeline(self):
        return SPARQLPipeline()

    def test_01_query_optimization_pipeline(self, optimizer):
        """1. 쿼리 최적화 파이프라인"""
        query = """
        SELECT ?name ?age
        WHERE {
            ?person name ?name .
            ?person age ?age .
            FILTER (?age > 18)
        }
        """

        start = time.time()
        optimized = optimizer.optimize_query(query)
        elapsed_ms = (time.time() - start) * 1000

        assert optimized is not None
        assert "SELECT" in optimized
        assert elapsed_ms < 50

    def test_02_cache_with_optimized_query(self, optimizer, cache):
        """2. 최적화된 쿼리 캐싱"""
        query = """
        SELECT ?name
        WHERE { ?person name ?name . }
        """

        # 쿼리 최적화
        optimized = optimizer.optimize_query(query)
        graph_hash = "graph_123"

        # 캐시에 저장
        cache.set(optimized, graph_hash, ["Alice", "Bob"])

        # 캐시에서 조회
        result = cache.get(optimized, graph_hash)
        assert result == ["Alice", "Bob"]

        # 캐시 통계
        stats = cache.get_stats()
        assert stats["hit_count"] == 1
        assert stats["hit_rate"] == "100.0%"

    def test_03_indexing_with_optimized_triples(self, indexer):
        """3. 인덱싱 구축"""
        indexer.build_indexes()

        # 인덱스 통계
        stats = indexer.get_index_stats()
        assert stats["total_triples"] > 0
        assert stats["subject_index_size"] > 0
        assert stats["predicate_index_size"] > 0
        assert stats["object_index_size"] > 0

    def test_04_parallel_import_with_optimization(self, pipeline):
        """4. 병렬 임포트 + 최적화"""
        configs = [
            {"source": "dbpedia", "uri": "http://ex1.com"},
            {"source": "wikidata", "qid": "Q123"},
            {"source": "rdf_file", "path": "/data/file.ttl"},
        ]

        async def run_test():
            start = time.time()
            results = await pipeline.import_engine.import_multiple_sources(
                configs
            )
            elapsed = (time.time() - start) * 1000

            assert len(results) > 0
            assert elapsed < 1000

        asyncio.run(run_test())

    def test_05_end_to_end_sparql_processing(self, optimizer, cache, pipeline):
        """5. End-to-End SPARQL 처리"""
        query = """
        SELECT ?name ?age
        WHERE {
            ?person name ?name .
            ?person age ?age .
        }
        """

        # 1. 쿼리 최적화
        optimized_query = optimizer.optimize_query(query)
        assert optimized_query is not None

        # 2. 캐시 확인 (미스)
        result = cache.get(optimized_query, "graph_123")
        assert result is None

        # 3. 처리 수행
        async def run_pipeline():
            config = {"source": "test", "data": "test_data"}
            return await pipeline.execute_end_to_end(optimized_query, config)

        result = asyncio.run(run_pipeline())
        assert result is not None

        # 4. 결과 캐싱
        cache.set(optimized_query, "graph_123", result)
        assert cache.get(optimized_query, "graph_123") is not None

    def test_06_batch_query_processing(self, optimizer, cache, pipeline):
        """6. 배치 쿼리 처리"""
        queries = [
            "SELECT ?name WHERE { ?x name ?name . }",
            "SELECT ?email WHERE { ?x email ?email . }",
            "SELECT ?phone WHERE { ?x phone ?phone . }",
        ]

        configs = [
            {"source": "source1", "data": "data1"},
            {"source": "source2", "data": "data2"},
        ]

        async def run_test():
            # 쿼리 최적화 및 배치 처리
            optimized_queries = [optimizer.optimize_query(q) for q in queries]

            # 배치 파이프라인 실행
            results = await pipeline.batch_execute_pipeline(
                optimized_queries, configs
            )

            assert len(results) == len(optimized_queries)
            assert all("query" in r for r in results)

        asyncio.run(run_test())

    def test_07_cache_invalidation(self, optimizer, cache):
        """7. 캐시 무효화"""
        query = "SELECT ?x WHERE { ?x type Person . }"
        optimized = optimizer.optimize_query(query)
        graph_hash = "graph_456"

        # 캐시 저장
        cache.set(optimized, graph_hash, ["result1", "result2"])
        assert cache.get(optimized, graph_hash) is not None

        # 특정 그래프 캐시 무효화
        removed_count = cache.invalidate_by_graph(graph_hash)
        assert removed_count > 0

        # 캐시에서 조회하면 None
        assert cache.get(optimized, graph_hash) is None

    def test_08_performance_improvement_measurement(self, optimizer):
        """8. 성능 개선 측정"""
        query = """
        SELECT ?name ?age ?email
        WHERE {
            ?person name ?name .
            ?person age ?age .
            ?person email ?email .
            ?person city ?city .
            FILTER (?age > 18)
            FILTER (?city = "Seoul")
        }
        """

        # 최적화 시간 측정
        start = time.time()
        optimized = optimizer.optimize_query(query)
        optimization_time_ms = (time.time() - start) * 1000

        # 성능 목표
        assert optimization_time_ms < 50  # < 50ms
        assert len(optimized) > 0

    def test_09_resource_utilization(self, pipeline):
        """9. 리소스 활용"""
        async def run_test():
            # 병렬 임포트 엔진
            engine = pipeline.import_engine

            configs = [
                {"source": f"source{i}", "data": f"data{i}"} for i in range(10)
            ]

            # 병렬 처리
            results = await engine.import_multiple_sources(configs)

            # 메트릭 확인
            metrics = engine.get_pipeline_metrics()
            assert metrics["total_stages"] > 0
            assert metrics["total_time_ms"] > 0

        asyncio.run(run_test())

    def test_10_concurrent_query_caching(self, cache):
        """10. 동시 쿼리 캐싱"""
        async def cache_operations():
            # 동시에 여러 쿼리를 캐시에 저장/조회
            queries = [f"SELECT ?x{i} WHERE {{ ?a ?b ?c . }}" for i in range(5)]

            # 저장
            for i, query in enumerate(queries):
                cache.set(query, f"graph_{i}", [f"result_{i}"])

            # 조회
            for i, query in enumerate(queries):
                result = cache.get(query, f"graph_{i}")
                assert result == [f"result_{i}"]

            stats = cache.get_stats()
            assert stats["hit_count"] == 5
            assert stats["hit_rate"] == "100.0%"

        asyncio.run(cache_operations())

    def test_11_query_optimization_consistency(self, optimizer):
        """11. 쿼리 최적화 일관성"""
        query = "SELECT ?name WHERE { ?x name ?name . }"

        # 여러 번 최적화해도 결과가 일관됨
        result1 = optimizer.optimize_query(query)
        result2 = optimizer.optimize_query(query)
        result3 = optimizer.optimize_query(query)

        # 모두 동일한 구조
        assert "SELECT" in result1
        assert "SELECT" in result2
        assert "SELECT" in result3

    def test_12_large_scale_batch_processing(self, pipeline):
        """12. 대규모 배치 처리"""
        queries = [
            f"SELECT ?x{i} WHERE {{ ?a ?b ?c . }}" for i in range(20)
        ]
        configs = [{"source": f"src{i}", "data": f"data{i}"} for i in range(10)]

        async def run_test():
            start = time.time()
            results = await pipeline.batch_execute_pipeline(queries, configs)
            elapsed = (time.time() - start) * 1000

            assert len(results) == len(queries)
            assert elapsed < 10000  # 10초 이내

        asyncio.run(run_test())

    def test_13_error_resilience(self, optimizer, cache):
        """13. 오류 회복성"""
        # 빈 쿼리 처리
        result = optimizer.optimize_query("")
        assert result == ""

        # 유효하지 않은 쿼리 처리
        invalid_query = "INVALID SPARQL"
        result = optimizer.optimize_query(invalid_query)
        assert result is not None

    def test_14_combined_performance(self, optimizer, pipeline):
        """14. 통합 성능 측정"""
        query = """
        SELECT ?name ?age
        WHERE {
            ?person name ?name .
            ?person age ?age .
        }
        """

        config = {"source": "test", "data": "test_data"}

        async def run_test():
            # 최적화
            optimized = optimizer.optimize_query(query)

            # 파이프라인 처리
            start = time.time()
            result = await pipeline.execute_end_to_end(optimized, config)
            elapsed = (time.time() - start) * 1000

            assert elapsed < 500  # 500ms 이내 완료

        asyncio.run(run_test())

    def test_15_cleanup_operations(self, cache):
        """15. 정리 작업"""
        # 여러 항목 캐시
        for i in range(5):
            cache.set(f"query_{i}", f"graph_{i}", [f"result_{i}"])

        # 모든 캐시 무효화
        cache.invalidate_all()
        assert cache.cache == {}

        # 통계 초기화 확인
        stats = cache.get_stats()
        assert stats["cache_size"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
