"""Phase 4 Week 6: 비동기 파이프라인 최적화"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PipelineMetrics:
    """파이프라인 메트릭"""
    stage_name: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    items_processed: int = 0
    error_count: int = 0


class ParallelImportEngine:
    """병렬 임포트 엔진"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.metrics: List[PipelineMetrics] = []
        self.semaphore = asyncio.Semaphore(max_workers)

    async def import_multiple_sources(
        self, source_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """여러 소스에서 병렬 임포트"""
        tasks = []

        for config in source_configs:
            task = self._import_single_source(config)
            tasks.append(task)

        # 동시 실행 (최대 workers개 동시)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 필터링
        return [r for r in results if not isinstance(r, Exception)]

    async def _import_single_source(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """단일 소스 임포트"""
        async with self.semaphore:
            start_time = time.time()

            try:
                # 시뮬레이션: 실제 환경에서는 다양한 소스에서 임포트
                source_type = config.get("source", "unknown")
                data = {
                    "source": source_type,
                    "config": config,
                    "imported_at": start_time,
                    "status": "success",
                }

                # 비동기 I/O 시뮬레이션
                await asyncio.sleep(0.1)

                return data

            except Exception as e:
                return {"source": config.get("source"), "error": str(e)}

            finally:
                duration_ms = (time.time() - start_time) * 1000
                metrics = PipelineMetrics(
                    stage_name="import",
                    start_time=start_time,
                    end_time=time.time(),
                    duration_ms=duration_ms,
                    items_processed=1,
                )
                self.metrics.append(metrics)

    async def batch_deduplicate(
        self, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """배치 중복 제거"""
        start_time = time.time()

        try:
            # 중복 제거 로직
            seen = set()
            deduplicated = []

            for item in items:
                item_id = item.get("source", "unknown")

                if item_id not in seen:
                    seen.add(item_id)
                    deduplicated.append(item)

            await asyncio.sleep(0.05)  # I/O 시뮬레이션

            return deduplicated

        finally:
            duration_ms = (time.time() - start_time) * 1000
            metrics = PipelineMetrics(
                stage_name="deduplicate",
                start_time=start_time,
                end_time=time.time(),
                duration_ms=duration_ms,
                items_processed=len(items),
            )
            self.metrics.append(metrics)

    async def import_with_deduplication(
        self, source_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """병렬 임포트 + 중복 제거"""
        # 단계 1: 병렬 임포트
        imported = await self.import_multiple_sources(source_configs)

        # 단계 2: 배치 중복 제거
        deduplicated = await self.batch_deduplicate(imported)

        # 단계 3: 병렬 병합
        merged = await self._parallel_merge(deduplicated)

        return {
            "imported": len(imported),
            "deduplicated": len(deduplicated),
            "merged": merged,
        }

    async def _parallel_merge(self, entities: List[Dict]) -> Dict[str, Any]:
        """병렬 엔티티 병합"""
        if not entities:
            return {}

        # 엔티티를 배치로 분할
        batch_size = max(1, len(entities) // self.max_workers + 1)
        batches = [
            entities[i : i + batch_size] for i in range(0, len(entities), batch_size)
        ]

        # 각 배치를 병렬로 병합
        tasks = [self._merge_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks)

        # 배치 결과 통합
        merged = {}
        for batch_result in batch_results:
            merged.update(batch_result)

        return merged

    async def _merge_batch(self, batch: List[Dict]) -> Dict[str, Any]:
        """배치 병합"""
        result = {}

        for item in batch:
            source = item.get("source", "unknown")
            result[source] = item

        await asyncio.sleep(0.01)  # I/O 시뮬레이션
        return result

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """파이프라인 메트릭 조회"""
        total_time_ms = sum(m.duration_ms for m in self.metrics)
        avg_time_ms = (
            total_time_ms / len(self.metrics) if self.metrics else 0
        )

        return {
            "total_stages": len(self.metrics),
            "total_time_ms": total_time_ms,
            "avg_stage_time_ms": avg_time_ms,
            "stages": [
                {
                    "name": m.stage_name,
                    "duration_ms": m.duration_ms,
                    "items_processed": m.items_processed,
                    "error_count": m.error_count,
                }
                for m in self.metrics
            ],
        }


class AsyncResourcePool:
    """비동기 리소스 풀"""

    def __init__(self, max_connections: int = 10):
        self.semaphore = asyncio.Semaphore(max_connections)
        self.active_tasks: set = set()
        self.max_connections = max_connections

    async def acquire(self) -> None:
        """리소스 획득"""
        await self.semaphore.acquire()

    def release(self) -> None:
        """리소스 해제"""
        self.semaphore.release()

    async def run_with_limit(self, coro) -> Any:
        """제한된 동시성으로 코루틴 실행"""
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self.active_tasks.add(task)

            try:
                return await task
            finally:
                self.active_tasks.discard(task)

    async def wait_all(self) -> None:
        """모든 작업 완료 기다리기"""
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

    def get_active_count(self) -> int:
        """활성 작업 수 반환"""
        return len(self.active_tasks)


class SPARQLPipeline:
    """SPARQL 처리 파이프라인"""

    def __init__(self):
        self.import_engine = ParallelImportEngine()
        self.resource_pool = AsyncResourcePool()

    async def execute_end_to_end(
        self,
        query: str,
        import_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """임포트 → 변환 → 쿼리를 병렬로 처리"""
        start_time = time.time()

        try:
            # 단계 1: 임포트 시작 (백그라운드)
            import_task = asyncio.create_task(
                self.import_engine._import_single_source(import_config)
            )

            # 단계 2: 임포트 완료 기다리면서 변환 준비
            entity = await import_task

            # 단계 3: RDF 변환 (시뮬레이션)
            await asyncio.sleep(0.05)  # 변환 I/O
            graph = {"entity": entity, "triples": 100}

            # 단계 4: SPARQL 쿼리 실행
            await asyncio.sleep(0.02)  # 쿼리 실행 I/O
            results = {"query": query, "result_count": 10}

            return {
                "entity": entity,
                "graph": graph,
                "results": results,
                "elapsed_ms": (time.time() - start_time) * 1000,
            }

        except Exception as e:
            return {"error": str(e), "elapsed_ms": (time.time() - start_time) * 1000}

    async def batch_execute_pipeline(
        self,
        queries: List[str],
        import_configs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """배치 파이프라인"""
        start_time = time.time()

        # 모든 임포트를 병렬 시작
        import_tasks = [
            self.import_engine._import_single_source(config)
            for config in import_configs
        ]
        entities = await asyncio.gather(*import_tasks)

        # 모든 엔티티를 변환 (병렬)
        await asyncio.sleep(0.05)  # 변환 I/O

        # 병합된 그래프로 모든 쿼리 실행
        query_tasks = [
            self.resource_pool.run_with_limit(self._execute_query(q))
            for q in queries
        ]
        results = await asyncio.gather(*query_tasks)

        elapsed_ms = (time.time() - start_time) * 1000

        return [
            {
                "query": q,
                "results": r,
                "elapsed_ms": elapsed_ms / len(queries),
            }
            for q, r in zip(queries, results)
        ]

    async def _execute_query(self, query: str) -> Dict[str, Any]:
        """쿼리 실행"""
        await asyncio.sleep(0.02)  # 쿼리 I/O
        return {"query": query, "result_count": 5}

    def get_metrics(self) -> Dict[str, Any]:
        """전체 파이프라인 메트릭"""
        return {
            "import_metrics": self.import_engine.get_pipeline_metrics(),
            "active_tasks": self.resource_pool.get_active_count(),
        }
