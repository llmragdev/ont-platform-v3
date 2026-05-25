"""
v3 성능 기준선 측정 스크립트.

목표:
1. v3 현재 성능 베이스라인 기록
2. 응답시간 (레이턴시) 측정
3. 처리량 (QPS) 측정
4. 개선 전/후 비교용 기준 확립

실행 방법:
    python tests/load/baseline_v3.py

예상 결과:
    - latency: p99 250ms
    - throughput: 550 QPS
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests

BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_HEADERS = {"X-Tenant-ID": "company_abc"}


def measure_search_latency(num_queries: int = 10) -> dict:
    """검색 응답시간 측정.

    Args:
        num_queries: 측정할 쿼리 수

    Returns:
        {
            "avg_ms": 평균 응답시간,
            "p50_ms": 중앙값,
            "p99_ms": 99 백분위수,
            "min_ms": 최소값,
            "max_ms": 최대값,
            "std_dev_ms": 표준편차,
        }
    """
    queries = [
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

    latencies = []
    success_count = 0

    print(f"[Latency Test] {num_queries}개 쿼리 측정 시작...")
    for i in range(num_queries):
        query = queries[i % len(queries)]
        try:
            start = time.perf_counter()
            resp = requests.post(
                f"{BASE_URL}/rag/search",
                headers=DEFAULT_HEADERS,
                json={"query": query, "top_k": 5},
                timeout=10,
            )
            latency_ms = (time.perf_counter() - start) * 1000

            if resp.status_code == 200:
                latencies.append(latency_ms)
                success_count += 1
                print(f"  [{i+1}/{num_queries}] {query[:20]:20s} → {latency_ms:.1f}ms")
            else:
                print(f"  [{i+1}/{num_queries}] {query[:20]:20s} → ERROR {resp.status_code}")
        except Exception as e:
            print(f"  [{i+1}/{num_queries}] {query[:20]:20s} → EXCEPTION {e}")

    if not latencies:
        return {"error": "No successful queries"}

    sorted_latencies = sorted(latencies)
    return {
        "success_count": success_count,
        "total_queries": num_queries,
        "success_rate": round(success_count / num_queries * 100, 2),
        "avg_ms": round(statistics.mean(latencies), 2),
        "p50_ms": round(sorted_latencies[len(sorted_latencies) // 2], 2),
        "p99_ms": round(
            sorted_latencies[int(len(sorted_latencies) * 0.99)] if len(sorted_latencies) > 1 else sorted_latencies[0],
            2
        ),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "std_dev_ms": round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0,
    }


def measure_throughput(num_concurrent: int = 100, duration_seconds: int = 10) -> dict:
    """처리량 측정 (동시 쿼리).

    Args:
        num_concurrent: 동시 요청 수
        duration_seconds: 테스트 지속 시간 (초)

    Returns:
        {
            "total_queries": 총 요청 수,
            "success_queries": 성공한 요청 수,
            "elapsed_seconds": 경과시간,
            "qps": 초당 처리 수,
            "success_rate": 성공률 (%),
            "avg_latency_ms": 평균 레이턴시,
        }
    """
    queries = [
        "온톨로지",
        "자연언어처리",
        "knowledge graph",
        "신입사원",
        "급여 규정",
        "취업규칙",
        "NLP embedding",
        "semantic relationship",
    ]

    print(f"[Throughput Test] {num_concurrent}개 동시 요청 시작...")

    start_time = time.perf_counter()
    latencies = []
    success_count = 0
    total_count = 0

    def make_request(query_idx: int) -> Optional[float]:
        try:
            query = queries[query_idx % len(queries)]
            req_start = time.perf_counter()
            resp = requests.post(
                f"{BASE_URL}/rag/search",
                headers=DEFAULT_HEADERS,
                json={"query": query, "top_k": 5},
                timeout=10,
            )
            req_latency = (time.perf_counter() - req_start) * 1000
            return req_latency if resp.status_code == 200 else None
        except Exception as e:
            print(f"    Exception in request: {e}")
            return None

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(make_request, i)
            for i in range(num_concurrent)
        ]

        for future in as_completed(futures):
            latency = future.result()
            total_count += 1
            if latency is not None:
                latencies.append(latency)
                success_count += 1

    elapsed = time.perf_counter() - start_time
    qps = total_count / elapsed if elapsed > 0 else 0

    return {
        "total_queries": total_count,
        "success_queries": success_count,
        "elapsed_seconds": round(elapsed, 2),
        "qps": round(qps, 2),
        "success_rate": round(success_count / total_count * 100, 2) if total_count > 0 else 0,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "p99_latency_ms": round(
            sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else (latencies[0] if latencies else 0),
            2
        ),
    }


def print_baseline_report(latency_results: dict, throughput_results: dict) -> None:
    """기준선 보고서 출력.

    Args:
        latency_results: 레이턴시 측정 결과
        throughput_results: 처리량 측정 결과
    """
    print("\n" + "=" * 70)
    print("v3 성능 기준선 (Baseline) 보고서")
    print("=" * 70)

    print("\n[1] 응답시간 (Latency) 측정")
    print("-" * 70)
    for key, value in latency_results.items():
        if key != "error":
            print(f"  {key:20s}: {value}")

    print("\n[2] 처리량 (Throughput) 측정")
    print("-" * 70)
    for key, value in throughput_results.items():
        print(f"  {key:20s}: {value}")

    print("\n[3] 성능 목표 비교 (v3 vs v4 target)")
    print("-" * 70)
    print(f"  응답시간 (p99):")
    print(f"    - v3 baseline    : {latency_results.get('p99_ms', 'N/A')}ms")
    print(f"    - v4 target      : <200ms")
    print(f"    - 개선 필요      : {latency_results.get('p99_ms', 0) > 200}")

    print(f"\n  처리량 (QPS):")
    print(f"    - v3 baseline    : {throughput_results.get('qps', 'N/A')} QPS")
    print(f"    - v4 target      : 1000 QPS")
    print(f"    - 개선 필요      : {throughput_results.get('qps', 0) < 1000}")

    print("\n" + "=" * 70)


def main() -> None:
    """메인 실행 함수."""
    print("v3 성능 기준선 측정 시작...")
    print()

    try:
        # 1. 응답시간 측정
        latency_results = measure_search_latency(num_queries=10)
        print()

        # 2. 처리량 측정
        throughput_results = measure_throughput(num_concurrent=100)
        print()

        # 3. 보고서 출력
        print_baseline_report(latency_results, throughput_results)

    except requests.exceptions.ConnectionError:
        print("ERROR: API 서버에 연결할 수 없습니다.")
        print(f"       {BASE_URL} 확인 후 재시도하세요.")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
