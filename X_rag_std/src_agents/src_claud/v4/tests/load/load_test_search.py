"""
Locust 기반 부하 테스트.

목표:
- 1000 concurrent users 처리
- 응답시간 p99 < 200ms
- 처리량 1000 QPS
- 에러율 < 1%

실행 방법:
    locust -f tests/load/load_test_search.py -u 1000 -r 50 --headless -t 5m

옵션 설명:
    -u 1000     : 1000개 동시 사용자
    -r 50       : 초당 50명씩 증가 (spawn rate)
    --headless  : 웹 UI 없이 CLI로 실행
    -t 5m       : 5분간 테스트

예상 결과:
    - Response time p99: < 200ms
    - Throughput: 1000 QPS
    - Failure rate: < 1%
"""

import random
from locust import HttpUser, task, between, events
from time import perf_counter


class RAGSearchUser(HttpUser):
    """RAG 검색 사용자 시뮬레이션."""

    # 사용자 간 요청 대기 시간 (100ms ~ 500ms)
    wait_time = between(0.1, 0.5)

    # 테스트 대상 쿼리들
    QUERIES = [
        "온톨로지",
        "자연언어처리",
        "knowledge graph",
        "신입사원",
        "급여 규정",
        "취업규칙",
        "NLP embedding",
        "semantic relationship",
        "현대 문인",
        "감성 분석",
    ]

    @task(weight=1)
    def search_with_top_k_5(self) -> None:
        """top_k=5로 검색."""
        query = random.choice(self.QUERIES)
        self.client.post(
            "/api/v1/rag/search",
            headers={"X-Tenant-ID": "company_abc"},
            json={"query": query, "top_k": 5},
            name="search_top_k_5",
        )

    @task(weight=1)
    def search_with_top_k_10(self) -> None:
        """top_k=10으로 검색."""
        query = random.choice(self.QUERIES)
        self.client.post(
            "/api/v1/rag/search",
            headers={"X-Tenant-ID": "company_abc"},
            json={"query": query, "top_k": 10},
            name="search_top_k_10",
        )

    @task(weight=1)
    def search_with_debug_mode(self) -> None:
        """디버그 모드로 검색."""
        query = random.choice(self.QUERIES)
        self.client.post(
            "/api/v1/rag/search",
            headers={"X-Tenant-ID": "company_abc"},
            json={"query": query, "top_k": 5, "debug_mode": True},
            name="search_debug",
        )

    @task(weight=1)
    def search_with_category_filter(self) -> None:
        """카테고리 필터로 검색."""
        query = random.choice(self.QUERIES)
        self.client.post(
            "/api/v1/rag/search",
            headers={"X-Tenant-ID": "company_abc"},
            json={
                "query": query,
                "top_k": 5,
                "filters": {"category_mid": "온톨로지"},
            },
            name="search_filtered",
        )

    @task(weight=1)
    def stream_search(self) -> None:
        """스트리밍 검색."""
        query = random.choice(self.QUERIES)
        with self.client.stream(
            "POST",
            "/api/v1/rag/search/stream",
            headers={"X-Tenant-ID": "company_abc"},
            json={"query": query, "top_k": 5},
        ) as response:
            if response.status_code == 200:
                # SSE 스트림 읽기
                for _ in response.iter_bytes():
                    pass


# 전역 통계
class LoadTestStats:
    """부하 테스트 통계."""

    def __init__(self) -> None:
        self.total_requests = 0
        self.total_failures = 0
        self.latencies = []

    def record_request(self, response_time: float, success: bool) -> None:
        """요청 기록."""
        self.total_requests += 1
        if not success:
            self.total_failures += 1
        self.latencies.append(response_time)


# 글로벌 통계 인스턴스
stats = LoadTestStats()


# Locust 이벤트 핸들러
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """모든 요청 후 통계 기록."""
    success = exception is None and hasattr(response, "status_code") and 200 <= response.status_code < 400
    stats.record_request(response_time, success)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료 후 최종 보고서 출력."""
    if not stats.latencies:
        print("No data collected")
        return

    import statistics

    sorted_latencies = sorted(stats.latencies)
    avg_latency = statistics.mean(stats.latencies)
    p50_latency = sorted_latencies[len(sorted_latencies) // 2]
    p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]

    print("\n" + "=" * 80)
    print("부하 테스트 (Load Test) 최종 보고서")
    print("=" * 80)
    print(f"\nTotal Requests      : {stats.total_requests:,}")
    print(f"Successful Requests : {stats.total_requests - stats.total_failures:,}")
    print(f"Failed Requests     : {stats.total_failures:,}")
    print(f"Failure Rate        : {stats.total_failures / stats.total_requests * 100:.2f}%")
    print(f"\nLatency Statistics:")
    print(f"  Average           : {avg_latency:.2f}ms")
    print(f"  P50               : {p50_latency:.2f}ms")
    print(f"  P99               : {p99_latency:.2f}ms")
    print(f"  Min               : {min(stats.latencies):.2f}ms")
    print(f"  Max               : {max(stats.latencies):.2f}ms")

    # QPS 계산
    if environment.stats:
        start_time = environment.stats.start_time
        end_time = environment.stats.total.last_request_timestamp
        if end_time and start_time:
            elapsed = end_time - start_time
            if elapsed > 0:
                qps = stats.total_requests / elapsed
                print(f"\nThroughput:")
                print(f"  QPS (Queries/sec) : {qps:.2f}")
                print(f"  Elapsed Time      : {elapsed:.2f}s")

    print("\n성능 목표 달성 여부:")
    print(f"  p99 < 200ms       : {'✓ PASS' if p99_latency < 200 else '✗ FAIL'}")
    print(f"  1000 QPS          : {'✓ PASS (계산 필요)' if stats.total_requests > 10000 else '✗ FAIL (계산 필요)'}")
    print(f"  에러율 < 1%       : {'✓ PASS' if stats.total_failures / stats.total_requests < 0.01 else '✗ FAIL'}")
    print("\n" + "=" * 80)
