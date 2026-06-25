import asyncio
import time
import json
import numpy as np
from httpx import AsyncClient
import sys
from pathlib import Path

# Add project roots for potential imports
backend_path = Path(__file__).resolve().parents[2] / "src" / "backend"
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

async def measure_query(client: AsyncClient, name: str, query: str, repetitions: int = 20):
    """Measure cold vs warm performance of a query"""
    print(f"Measuring {name}...")
    latencies = []
    
    # 1. Cold execution (First run)
    start = time.perf_counter()
    try:
        response = await client.post(API_URL, json={"query": query, "limit": 1000}, headers=TENANT_HEADERS, timeout=10.0)
        cold_time = (time.perf_counter() - start) * 1000 # ms
        if response.status_code != 200:
            print(f"  [Error] Cold run failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"  [Error] Cold run exception: {e}")
        return None
        
    # 2. Warm executions (Subsequent runs to trigger caching)
    for i in range(repetitions - 1):
        await asyncio.sleep(0.05) # subtle pause between runs
        start = time.perf_counter()
        try:
            response = await client.post(API_URL, json={"query": query, "limit": 1000}, headers=TENANT_HEADERS, timeout=10.0)
            elapsed = (time.perf_counter() - start) * 1000
            if response.status_code == 200:
                latencies.append(elapsed)
        except Exception:
            pass
            
    if not latencies:
        # If all warm runs failed, return just cold run
        latencies = [cold_time]
        
    arr = np.array(latencies)
    return {
        "query_name": name,
        "cold_latency_ms": round(cold_time, 2),
        "warm_mean_ms": round(float(np.mean(arr)), 2),
        "warm_p50_ms": round(float(np.percentile(arr, 50)), 2),
        "warm_p95_ms": round(float(np.percentile(arr, 95)), 2),
        "warm_p99_ms": round(float(np.percentile(arr, 99)), 2),
        "success_rate": round((len(latencies) + 1) / repetitions * 100, 1)
    }

async def collect_baseline():
    """Collect baseline metrics for all defined patterns"""
    results = {}
    
    # Using AsyncClient with longer limits to handle sequential tasks cleanly
    async with AsyncClient() as client:
        for name, query in BENCHMARK_QUERIES.items():
            metrics = await measure_query(client, name, query)
            if metrics:
                results[name] = metrics
                
    return results

def save_and_report(results):
    """Save results as JSON and output formatted report to console"""
    output_path = Path(__file__).resolve().parent / "baseline_data.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n" + "="*50)
    print("=== PERFORMANCE BASELINE REPORT ===")
    print("="*50)
    
    for name, metrics in results.items():
        print(f"\n{name}:")
        print(f"  Cold Run Latency: {metrics['cold_latency_ms']:.2f} ms")
        print(f"  Warm Mean Latency: {metrics['warm_mean_ms']:.2f} ms")
        print(f"  Warm P95 Latency:  {metrics['warm_p95_ms']:.2f} ms")
        print(f"  Warm P99 Latency:  {metrics['warm_p99_ms']:.2f} ms")
        print(f"  Success Rate:      {metrics['success_rate']:.1f}%")
        
    print("\n" + "="*50)
    print(f"Baseline saved to: {output_path}")
    print("="*50 + "\n")

async def main():
    print("Starting SPARQL query performance baseline collection...")
    print("Make sure the FastAPI backend is running on http://localhost:8001")
    print("Checking endpoint connection...")
    
    async with AsyncClient() as client:
        try:
            res = await client.get("http://localhost:8001/api/health", timeout=2.0)
            if res.status_code != 200:
                print("[Warning] API health check did not return 200. Is backend running?")
        except Exception as e:
            print(f"[Warning] Could not connect to backend server: {e}")
            print("Please spin up the backend locally before running benchmark tests.")
            
    results = await collect_baseline()
    if results:
        save_and_report(results)
    else:
        print("[Error] No performance baseline metrics were collected.")

if __name__ == "__main__":
    asyncio.run(main())
