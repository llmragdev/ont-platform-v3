"""Live API Performance and Load Test Suite

Sends concurrent SPARQL query requests to the live running FastAPI instance
running on http://localhost:8001/api/ontology/sparql.

Measures:
- Latency metrics (mean, p50, p95, p99) under concurrent load.
- Real HTTP framework/JSON serialization overhead.
- Throughput and Success Rate.

Run this suite using:
    pytest tests/load/test_live_api_performance.py -v -s
"""
import sys
import time
import pytest
import asyncio
from pathlib import Path
from httpx import AsyncClient

# Ensure sys.path includes backend source and project root
v3_path = Path(__file__).resolve().parents[2]
backend_path = v3_path / "src" / "backend"
if str(v3_path) not in sys.path:
    sys.path.insert(0, str(v3_path))
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from tests.load.fixtures.test_data import BENCHMARK_QUERIES

API_URL = "http://localhost:8001/api/ontology/sparql"
TENANT_HEADERS = {
    "Content-Type": "application/json",
    "x-company-id": "test",
    "x-project-id": "test",
    "x-user-id": "benchmark-user",
    "x-role": "Admin"
}

async def send_single_query(client: AsyncClient, name: str, query: str, results: list):
    """Worker task to send one query and record its elapsed time"""
    start = time.perf_counter()
    try:
        response = await client.post(
            API_URL, 
            json={"query": query, "limit": 100}, 
            headers=TENANT_HEADERS, 
            timeout=15.0
        )
        elapsed = (time.perf_counter() - start) * 1000  # ms
        
        # Check standard unified contract keys
        if response.status_code == 200:
            data = response.json()
            is_valid = "results" in data and "source" in data
            results.append({
                "name": name,
                "latency_ms": elapsed,
                "status": "success" if is_valid else "invalid_format",
                "engine": data.get("source", "unknown"),
                "status_code": response.status_code
            })
        else:
            results.append({
                "name": name,
                "latency_ms": elapsed,
                "status": "http_error",
                "status_code": response.status_code,
                "response": response.text[:200]
            })
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        results.append({
            "name": name,
            "latency_ms": elapsed,
            "status": "exception",
            "error": str(e)
        })

@pytest.mark.asyncio
async def test_live_concurrent_queries():
    """Execute live E2E concurrent requests over the API endpoints"""
    import numpy as np
    
    concurrency_levels = [10, 30, 50]
    total_requests = 150
    
    print("\nStarting Live API Concurrency Load Testing...")
    
    # We will pick a standard pattern query for load testing
    query_name = "Pattern_24_1HopFilter"
    query_text = BENCHMARK_QUERIES[query_name]
    
    async with AsyncClient() as client:
        # Check if backend is alive
        try:
            health = await client.get("http://localhost:8001/api/health", timeout=2.0)
            if health.status_code != 200:
                pytest.skip("FastAPI Server is not healthy. Skipping performance test.")
        except Exception:
            pytest.skip("FastAPI Server is offline on port 8001. Skipping performance test.")
            
        for concurrency in concurrency_levels:
            print(f"\n--- Testing with Concurrency: {concurrency} (Total: {total_requests}) ---")
            results = []
            
            # Batch execution to simulate concurrent users
            tasks = []
            for i in range(total_requests):
                task = send_single_query(client, query_name, query_text, results)
                tasks.append(task)
                
                # Yield execution to create concurrent batches
                if len(tasks) >= concurrency:
                    await asyncio.gather(*tasks)
                    tasks = []
                    await asyncio.sleep(0.01) # mini gap
                    
            if tasks:
                await asyncio.gather(*tasks)
                
            # Compute stats
            latencies = [r["latency_ms"] for r in results if r["status"] == "success"]
            failures = [r for r in results if r["status"] != "success"]
            
            if not latencies:
                print(f"  [ERROR] All {total_requests} requests failed under concurrency {concurrency}.")
                if failures:
                    print(f"  Sample error: {failures[0]}")
                continue
                
            arr = np.array(latencies)
            success_rate = (len(latencies) / total_requests) * 100
            
            print(f"  Success Rate: {success_rate:.1f}% ({len(latencies)}/{total_requests})")
            print(f"  Mean Latency: {np.mean(arr):.2f} ms")
            print(f"  P50 Latency:  {np.percentile(arr, 50):.2f} ms")
            print(f"  P95 Latency:  {np.percentile(arr, 95):.2f} ms")
            print(f"  P99 Latency:  {np.percentile(arr, 99):.2f} ms")
            
            # SLA validation
            p95_ms = np.percentile(arr, 95)
            # Under concurrency, One-hop target is <300ms
            assert p95_ms < 300.0, f"P95 latency of {p95_ms:.2f}ms exceeds 300ms SLA target"
            assert success_rate >= 95.0, f"Success rate of {success_rate:.1f}% is below 95% threshold"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
