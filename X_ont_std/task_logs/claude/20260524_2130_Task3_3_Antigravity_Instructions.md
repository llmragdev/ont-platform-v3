# Task 3-3 Phase 3: Antigravity Integrated Load Tests - Instructions

**Date**: 2026-05-24 21:30  
**For**: Antigravity Team (Performance)  
**Task**: Load testing against live PostgreSQL + FastAPI backend  
**Timeline**: 2026-06-12 ~ 06-14 (2.5 days)  
**Deliverable**: `task_logs/claude/YYYYMMDD_HHMM_Antigravity_Week4_LoadTest_Complete.md`

---

## 📋 Overview

Backend (Claude) has completed PostgreSQL E2E tests. Now stress-test the entire system:
1. Execute load tests against live PostgreSQL + FastAPI
2. Measure concurrent query performance
3. Validate multi-tenant isolation under load
4. Compare against baseline expectations
5. Verify no data leakage or corruption

---

## 🎯 Success Criteria

- ✅ All query patterns execute under concurrent load
- ✅ p50 latency < 100ms
- ✅ p99 latency < 300ms
- ✅ Throughput: >100 queries/sec
- ✅ Error rate: <0.1%
- ✅ Multi-tenant isolation maintained
- ✅ No database connection leaks
- ✅ Performance report generated

---

## 🚀 Setup Instructions

### Step 1: Ensure Backend is Running

```bash
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend
conda activate claud_be
uvicorn main:app --reload --port 8001
```

Verify health:
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy"}
```

### Step 2: Create Load Test Script

**File**: `tests/load/load_test_e2e.py`

```python
"""End-to-End Load Testing against Live Backend

Executes all SPARQL patterns #18-26 with concurrent requests
against PostgreSQL backend via FastAPI /api/ontology/sparql endpoint.
"""

import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configuration
BACKEND_URL = "http://localhost:8001"
QUERIES_FILE = "tests/load/queries.txt"
NUM_THREADS = [10, 50, 100]  # Sequential load levels
DURATION_SECONDS = 60  # Per load level
DOMAIN_ID = "test"  # Multi-tenant context

# Query templates (all patterns #18-26)
QUERIES = [
    # Pattern #18: Simple ID lookup
    """PREFIX ex: <http://test.org/>
    SELECT ?name WHERE {
        ex:ship1 ex:name ?name
    }""",
    
    # Pattern #19: Type filtering
    """PREFIX ex: <http://test.org/>
    SELECT ?ship WHERE {
        ?ship a ex:Ship
    }""",
    
    # Pattern #20: Numeric comparison
    """PREFIX ex: <http://test.org/>
    SELECT ?part ?cost WHERE {
        ?part ex:cost ?cost
        FILTER (?cost > 500)
    }""",
    
    # Pattern #21: Equality filter
    """PREFIX ex: <http://test.org/>
    SELECT ?ship WHERE {
        ?ship ex:status "Active"
    }""",
    
    # Pattern #24: 1-hop + filter
    """PREFIX ex: <http://test.org/>
    SELECT ?part ?cost WHERE {
        ex:supplier1 ex:supplies ?part .
        ?part ex:cost ?cost
        FILTER (?cost > 500)
    }""",
    
    # Pattern #25: 2-hop relation
    """PREFIX ex: <http://test.org/>
    SELECT ?part WHERE {
        ex:ship1 ex:has_block ?block .
        ?block ex:has_part ?part
    }""",
    
    # Pattern #26: 2-hop + filter
    """PREFIX ex: <http://test.org/>
    SELECT ?part ?rating WHERE {
        ex:project1 ex:involves_supplier ?supplier .
        ?supplier ex:supplies ?part .
        ?part ex:quality_rating ?rating
        FILTER (?rating >= 5)
    }""",
]

class LoadTestRunner:
    def __init__(self, backend_url, queries, domain_id="test"):
        self.backend_url = backend_url
        self.queries = queries
        self.domain_id = domain_id
        self.endpoint = f"{backend_url}/api/ontology/sparql"
        self.results = {
            "latencies": [],
            "errors": 0,
            "success": 0,
        }
    
    def execute_query(self, query: str):
        """Execute single SPARQL query against backend"""
        try:
            start = time.time()
            response = requests.post(
                self.endpoint,
                json={"query": query, "limit": 1000},
                headers={"X-Domain-ID": self.domain_id},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000  # ms
            
            if response.status_code == 200:
                self.results["latencies"].append(elapsed)
                self.results["success"] += 1
                return True, elapsed
            else:
                self.results["errors"] += 1
                print(f"Error: HTTP {response.status_code}")
                return False, elapsed
        except Exception as e:
            self.results["errors"] += 1
            print(f"Exception: {str(e)}")
            return False, 0
    
    def run_load_test(self, num_threads: int, duration_seconds: int):
        """Execute load test with specified concurrency"""
        print(f"\n{'='*60}")
        print(f"Load Test: {num_threads} threads, {duration_seconds}s duration")
        print(f"{'='*60}")
        
        self.results = {"latencies": [], "errors": 0, "success": 0}
        start_time = time.time()
        query_count = 0
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            while time.time() - start_time < duration_seconds:
                # Submit queries to thread pool
                for query in self.queries:
                    if time.time() - start_time >= duration_seconds:
                        break
                    future = executor.submit(self.execute_query, query)
                    futures.append(future)
                    query_count += 1
            
            # Wait for all futures to complete
            for future in as_completed(futures):
                future.result()
        
        # Calculate metrics
        self.print_results(num_threads)
        return self.results
    
    def print_results(self, num_threads: int):
        """Print load test results and metrics"""
        latencies = self.results["latencies"]
        total = self.results["success"] + self.results["errors"]
        
        if not latencies:
            print("No successful queries - cannot calculate metrics")
            return
        
        success_rate = (self.results["success"] / total * 100) if total > 0 else 0
        
        print(f"\nResults ({num_threads} threads):")
        print(f"  Total Requests: {total}")
        print(f"  Success: {self.results['success']} ({success_rate:.1f}%)")
        print(f"  Errors: {self.results['errors']}")
        print(f"  Throughput: {self.results['success'] / 60:.1f} req/sec")
        
        print(f"\nLatency Statistics (ms):")
        print(f"  Min: {min(latencies):.2f}")
        print(f"  p50: {statistics.median(latencies):.2f}")
        print(f"  p90: {sorted(latencies)[int(len(latencies)*0.9)]:.2f}")
        print(f"  p99: {sorted(latencies)[int(len(latencies)*0.99)]:.2f}")
        print(f"  Max: {max(latencies):.2f}")
        print(f"  Mean: {statistics.mean(latencies):.2f}")
        print(f"  StdDev: {statistics.stdev(latencies):.2f}" if len(latencies) > 1 else "")

# Main execution
if __name__ == "__main__":
    runner = LoadTestRunner(BACKEND_URL, QUERIES, DOMAIN_ID)
    
    # Run progressively increasing loads
    for num_threads in NUM_THREADS:
        runner.run_load_test(num_threads, DURATION_SECONDS)
```

### Step 3: Run Load Tests

```bash
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend

# Run load test
python tests/load/load_test_e2e.py

# Or run with pytest
pytest tests/load/load_test_e2e.py -v -s
```

---

## 📊 Expected Results Reference

Based on Claude's E2E tests (baseline):
- Pattern #18: ~200ms on Neon cloud
- Pattern #25-26: ~300-400ms on Neon cloud
- Single thread throughput: ~5-10 queries/sec (cloud latency)

**Load test expectations**:
- 10 threads: ~10-20 queries/sec (minimal contention)
- 50 threads: ~30-50 queries/sec (moderate load)
- 100 threads: ~40-60 queries/sec (peak load, potential contention)

---

## ✅ Test Scenarios

### Scenario 1: Baseline (10 threads)
- Expected: Low contention, near-max throughput
- Latencies: p50 <100ms, p99 <200ms
- Error rate: <0.1%

### Scenario 2: Moderate Load (50 threads)
- Expected: Some connection pooling contention
- Latencies: p50 <150ms, p99 <300ms
- Error rate: <0.5%

### Scenario 3: Peak Load (100 threads)
- Expected: Connection pooling saturation
- Latencies: p50 <200ms, p99 <400ms
- Error rate: <1.0%

### Scenario 4: Multi-Tenant Isolation Check
- Execute Pattern #18 with different domain_id values
- Verify no data leakage between tenants
- Confirm proper isolation at high concurrency

---

## 📋 Validation Checklist

- [ ] Backend running on port 8001
- [ ] Database connection successful
- [ ] All 7 query patterns execute
- [ ] No connection timeouts
- [ ] Latencies within acceptable range
- [ ] Error rate < 1%
- [ ] Multi-tenant isolation verified
- [ ] Results are consistent
- [ ] No database locks or deadlocks
- [ ] Memory usage stable (no leaks)

---

## 📈 Metrics to Capture

For each load level (10, 50, 100 threads):

1. **Throughput**
   - Queries per second
   - Total requests processed

2. **Latency**
   - Minimum
   - p50 (median)
   - p90 (90th percentile)
   - p99 (99th percentile)
   - Maximum

3. **Error Metrics**
   - Success count
   - Error count
   - Error rate (%)

4. **Resource Utilization** (if available)
   - Database connection pool usage
   - Memory consumption
   - CPU utilization

5. **Data Integrity**
   - Result accuracy
   - Multi-tenant isolation verification
   - No data corruption

---

## 🔍 Comparison vs Baseline

Compare load test results against SQLite baseline (from Task 3-2):
- Expected slower due to cloud network latency
- But should scale similarly with thread count
- Isolation should be maintained

---

## 📝 Deliverable Format

Create completion report: `task_logs/claude/YYYYMMDD_HHMM_Antigravity_Week4_LoadTest_Complete.md`

```markdown
# Antigravity Week 4: Integrated Load Tests - COMPLETE

Date: 2026-06-XX HH:MM
Status: ✅ COMPLETE

## Load Test Results

### Scenario 1: Baseline (10 threads)
- Throughput: XX queries/sec
- p50: XX ms
- p99: XX ms
- Error rate: X.X%
- Status: ✅ PASS

### Scenario 2: Moderate (50 threads)
- Throughput: XX queries/sec
- p50: XX ms
- p99: XX ms
- Error rate: X.X%
- Status: ✅ PASS

### Scenario 3: Peak (100 threads)
- Throughput: XX queries/sec
- p50: XX ms
- p99: XX ms
- Error rate: X.X%
- Status: ✅ PASS

## Multi-Tenant Isolation
- ✅ No data leakage
- ✅ Isolation maintained at peak load

## Comparison to Baseline
- PostgreSQL vs SQLite: [Comparison notes]
- Performance degradation: [Assessment]

## Issues Encountered (if any)
- [List any issues and resolution]

## Ready For
- Final integration report (Phase 5)
```

---

## 🔗 Related Documents

- [Claude E2E Results](./20260524_2130_Task3_3_PostgreSQL_Complete.md) ← PostgreSQL baseline
- [Task 3-2: API Endpoint](./PHASE2_5_TASK3_2_Claude_FastAPIIntegration_20260524_1930.md) ← API specification
- [Planning Document](../../majestic-sparking-crab.md) ← Overall Task 3-3 plan
- [Query Optimization Report](../../ont_platform/v3/QUERY_OPTIMIZATION.md) ← Performance tuning reference

---

## ✉️ Questions?

Refer to:
1. Claude's E2E test results for expected latencies
2. FastAPI endpoint specification in Task 3-2
3. PHASE2_5_Project_Status_20260524.md for timeline coordination

**Timeline**: Start 2026-06-12, Complete by 2026-06-14  
**Next**: Final integration report (2026-06-14 afternoon)
