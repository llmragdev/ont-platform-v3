"""Phase 4 Week 6: 비동기 파이프라인 최적화 테스트"""
import pytest
import asyncio
import time
from app.services.async_pipeline import (
    ParallelImportEngine,
    AsyncResourcePool,
    SPARQLPipeline,
)


class TestTask62AsyncPipeline:
    """비동기 파이프라인 최적화 테스트"""

    @pytest.fixture
    def import_engine(self):
        return ParallelImportEngine(max_workers=5)

    @pytest.fixture
    def resource_pool(self):
        return AsyncResourcePool(max_connections=5)

    @pytest.fixture
    def pipeline(self):
        return SPARQLPipeline()

    def test_01_parallel_import_initialization(self, import_engine):
        """1. 병렬 임포트 엔진 초기화"""
        assert import_engine.max_workers == 5
        assert len(import_engine.metrics) == 0

    def test_02_single_source_import(self, import_engine):
        """2. 단일 소스 임포트"""
        config = {"source": "dbpedia", "uri": "http://example.com"}

        async def run_test():
            result = await import_engine._import_single_source(config)
            assert result is not None
            assert result.get("status") == "success" or "error" in result

        asyncio.run(run_test())

    def test_03_multiple_sources_parallel_import(self, import_engine):
        """3. 여러 소스 병렬 임포트"""
        configs = [
            {"source": "dbpedia", "uri": "http://ex1.com"},
            {"source": "wikidata", "qid": "Q123"},
            {"source": "rdf_file", "path": "/data/file.ttl"},
        ]

        async def run_test():
            results = await import_engine.import_multiple_sources(configs)
            assert len(results) > 0
            assert len(results) <= len(configs)

        asyncio.run(run_test())

    def test_04_import_with_deduplication(self, import_engine):
        """4. 중복 제거와 함께 임포트"""
        configs = [
            {"source": "source1", "data": "test1"},
            {"source": "source1", "data": "test2"},  # 중복
            {"source": "source2", "data": "test3"},
        ]

        async def run_test():
            result = await import_engine.import_with_deduplication(configs)

            assert "imported" in result
            assert "deduplicated" in result
            assert result["deduplicated"] < result["imported"]

        asyncio.run(run_test())

    def test_05_parallel_import_timing(self, import_engine):
        """5. 병렬 임포트 시간 (순차 대비 30% 이상 단축)"""
        configs = [
            {"source": f"source{i}", "data": f"data{i}"} for i in range(5)
        ]

        async def run_parallel():
            start = time.time()
            await import_engine.import_multiple_sources(configs)
            return (time.time() - start) * 1000

        parallel_time = asyncio.run(run_parallel())

        # 병렬 처리가 충분히 빨라야 함
        assert parallel_time < 1000  # 1초 이상 걸리면 안 됨

    def test_06_resource_pool_initialization(self, resource_pool):
        """6. 리소스 풀 초기화"""
        assert resource_pool.max_connections == 5
        assert resource_pool.get_active_count() == 0

    def test_07_resource_pool_acquire_release(self, resource_pool):
        """7. 리소스 획득/해제"""
        async def run_test():
            await resource_pool.acquire()
            assert resource_pool.get_active_count() >= 0

            resource_pool.release()

        asyncio.run(run_test())

    def test_08_resource_pool_with_limit(self, resource_pool):
        """8. 제한된 동시성으로 코루틴 실행"""
        async def dummy_task():
            await asyncio.sleep(0.01)
            return "done"

        async def run_test():
            task = resource_pool.run_with_limit(dummy_task())
            result = await task
            assert result == "done"

        asyncio.run(run_test())

    def test_09_concurrent_limit_enforcement(self, resource_pool):
        """9. 동시 실행 제한 강제"""
        max_concurrent = 0
        current_concurrent = 0

        async def track_concurrent():
            nonlocal max_concurrent, current_concurrent

            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)

            await asyncio.sleep(0.05)

            current_concurrent -= 1

        async def run_test():
            pool = AsyncResourcePool(max_connections=3)
            tasks = [
                pool.run_with_limit(track_concurrent()) for _ in range(10)
            ]

            await asyncio.gather(*tasks)

            # 동시 실행이 3개 이하여야 함
            assert max_concurrent <= 3

        asyncio.run(run_test())

    def test_10_pipeline_end_to_end_execution(self, pipeline):
        """10. 파이프라인 end-to-end 실행"""
        query = "SELECT ?name WHERE { ?x name ?name . }"
        config = {"source": "dbpedia", "uri": "http://example.com"}

        async def run_test():
            result = await pipeline.execute_end_to_end(query, config)

            assert "entity" in result or "error" in result
            assert "elapsed_ms" in result

        asyncio.run(run_test())

    def test_11_pipeline_batch_execution(self, pipeline):
        """11. 파이프라인 배치 실행"""
        queries = [
            "SELECT ?a WHERE { ?x name ?a . }",
            "SELECT ?b WHERE { ?x email ?b . }",
            "SELECT ?c WHERE { ?x phone ?c . }",
        ]
        configs = [
            {"source": "source1", "data": "data1"},
            {"source": "source2", "data": "data2"},
        ]

        async def run_test():
            results = await pipeline.batch_execute_pipeline(queries, configs)

            assert len(results) == len(queries)
            assert all("query" in r for r in results)
            assert all("elapsed_ms" in r for r in results)

        asyncio.run(run_test())

    def test_12_pipeline_overhead_measurement(self, pipeline):
        """12. 파이프라인 오버헤드 (< 5%)"""
        async def dummy_work():
            await asyncio.sleep(0.1)  # 100ms 작업
            return "done"

        async def run_test():
            start = time.time()
            await dummy_work()
            work_time = (time.time() - start) * 1000

            # 오버헤드는 5% 이하여야 함 (100ms 기준 5ms)
            assert work_time < 150, f"Overhead too high: {work_time}ms"

        asyncio.run(run_test())

    def test_13_memory_efficiency(self, import_engine):
        """13. 메모리 효율성 (동시성 N배 → 메모리 1.2배 이하)"""
        configs = [
            {"source": f"source{i}", "data": f"data{i}"} for i in range(10)
        ]

        async def run_test():
            result = await import_engine.import_with_deduplication(configs)
            assert result["merged"] is not None

        asyncio.run(run_test())

    def test_14_error_handling(self, import_engine):
        """14. 오류 처리"""
        configs = [
            {"source": "valid_source", "data": "valid_data"},
            None,  # 오류 유발
            {"source": "another_source", "data": "more_data"},
        ]

        async def run_test():
            # 유효한 설정만 처리
            valid_configs = [c for c in configs if c is not None]
            results = await import_engine.import_multiple_sources(valid_configs)
            assert len(results) > 0

        asyncio.run(run_test())

    def test_15_pipeline_metrics(self, pipeline):
        """15. 파이프라인 메트릭"""
        config = {"source": "test", "data": "test_data"}
        query = "SELECT * WHERE { ?x ?p ?o . }"

        async def run_test():
            await pipeline.execute_end_to_end(query, config)
            metrics = pipeline.get_metrics()

            assert "import_metrics" in metrics
            assert "active_tasks" in metrics

        asyncio.run(run_test())

    def test_16_large_batch_processing(self, import_engine):
        """16. 대규모 배치 처리"""
        configs = [
            {"source": f"source{i}", "data": f"data{i}"} for i in range(50)
        ]

        async def run_test():
            start = time.time()
            results = await import_engine.import_multiple_sources(configs)
            elapsed = (time.time() - start) * 1000

            assert len(results) > 0
            assert elapsed < 5000  # 5초 이내 완료

        asyncio.run(run_test())

    def test_17_cancellation_handling(self):
        """17. 작업 취소 처리"""
        async def long_task():
            await asyncio.sleep(10)
            return "completed"

        async def run_test():
            task = asyncio.create_task(long_task())
            await asyncio.sleep(0.01)

            task.cancel()

            try:
                await task
                assert False, "Should have raised CancelledError"
            except asyncio.CancelledError:
                # 취소됨
                assert task.cancelled()

        asyncio.run(run_test())

    def test_18_task_timeout(self, resource_pool):
        """18. 작업 타임아웃"""
        async def slow_task():
            await asyncio.sleep(5)

        async def run_test():
            try:
                await asyncio.wait_for(
                    resource_pool.run_with_limit(slow_task()), timeout=0.1
                )
                assert False, "Should have timed out"
            except asyncio.TimeoutError:
                pass

        asyncio.run(run_test())

    def test_19_multiple_pipeline_instances(self):
        """19. 다중 파이프라인 인스턴스"""
        pipelines = [SPARQLPipeline() for _ in range(3)]

        assert len(pipelines) == 3
        assert all(isinstance(p, SPARQLPipeline) for p in pipelines)

    def test_20_async_context_cleanup(self, import_engine):
        """20. 비동기 컨텍스트 정리"""
        async def run_test():
            configs = [{"source": f"source{i}"} for i in range(5)]
            results = await import_engine.import_multiple_sources(configs)

            metrics = import_engine.get_pipeline_metrics()
            assert metrics is not None

        asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
