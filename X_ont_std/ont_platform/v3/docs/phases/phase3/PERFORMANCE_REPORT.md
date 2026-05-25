# Phase 3 Week 4 Performance Benchmarking & Load Testing Report

This report presents the findings from the Phase 3 Week 4 Performance Benchmarking and Load Testing executed on `ont_platform v3.0`. The evaluation targets the core workflow execution engine, the changelog query engine, and the writeback monitoring system.

---

## 1. Executive Summary

- **Testing Period**: 2026-05-25
- **Tooling Used**: Locust (Headless Mode), Python-based test orchestrator, FastAPI (Uvicorn), SQLite local performance configuration.
- **Key Objectives**:
  1. Determine the baseline performance metrics (RPS, Latency) for core APIs.
  2. Evaluate system behavior and reliability under high concurrent user scenarios (Ramp-Up, Constant, and Peak loads).
  3. Identify critical architectural bottlenecks and provide concrete optimization paths.

---

## 2. API Performance Benchmarks (Baseline)

The baseline benchmarking was executed with **10 concurrent users** and a spawn rate of **2 users/second** over a duration of 15 seconds.

| API Endpoint | Request Count | Failure Count (Rate) | Median Latency (ms) | Average Latency (ms) | Max Latency (ms) | RPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/changelog/history` | 63 | 0 (0.0%) | 20.0 | 184.6 | 2086.6 | 4.75 |
| `POST /api/workflow/execute` | 63 | 12 (19.0%) | 100.0 | 275.6 | 2194.6 | 4.75 |
| `GET /api/writeback/statistics` | 23 | 0 (0.0%) | 25.0 | 31.5 | 121.8 | 1.73 |
| **Aggregated Total** | **149** | **12 (8.05%)** | **37.0** | **199.5** | **2194.6** | **11.22** |

> [!NOTE]
> Even under low baseline loads, the `/api/workflow/execute` endpoint showed a **19.0% failure rate** with maximum latencies exceeding 2 seconds. In contrast, the read-heavy SQL database endpoints (`changelog` and `writeback statistics`) remained stable with 0% failures.

---

## 3. Load Testing Scenarios (Scenarios A, B, C)

### Scenario A: Ramp-Up Load (50 Users, Spawn Rate = 5/s, Duration = 20s)
Simulates a rapid traffic increase up to a moderate concurrent user limit.

| API Endpoint | Request Count | Failure Count (Rate) | Median Latency (ms) | Average Latency (ms) | Max Latency (ms) | RPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/changelog/history` | 446 | 0 (0.0%) | 32.0 | 167.1 | 2130.3 | 24.29 |
| `POST /api/workflow/execute` | 300 | 105 (35.0%) | 120.0 | 323.5 | 2251.6 | 16.34 |
| `GET /api/writeback/statistics` | 151 | 0 (0.0%) | 44.0 | 182.7 | 2132.1 | 8.22 |
| **Total** | **897** | **105 (11.7%)** | **51.0** | **222.1** | **2251.6** | **48.86** |

### Scenario B: Constant Load (50 Users, Spawn Rate = 50/s, Duration = 20s)
Simulates a sustained load over a period of time with mixed API actions.

| API Endpoint | Request Count | Failure Count (Rate) | Median Latency (ms) | Average Latency (ms) | Max Latency (ms) | RPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/changelog/history` | 348 | 0 (0.0%) | 210.0 | 459.7 | 2958.7 | 19.47 |
| `POST /api/workflow/execute` | 288 | 129 (44.8%) | 540.0 | 749.4 | 3194.8 | 16.11 |
| `GET /api/writeback/statistics` | 101 | 0 (0.0%) | 240.0 | 397.4 | 2912.3 | 5.65 |
| **Total** | **737** | **129 (17.5%)** | **330.0** | **564.4** | **3194.8** | **41.23** |

### Scenario C: Peak Load (200 Users, Spawn Rate = 100/s, Duration = 15s)
Simulates an extreme spike representing peak usage (e.g. system-wide updates, batch actions).

| API Endpoint | Request Count | Failure Count (Rate) | Median Latency (ms) | Average Latency (ms) | Max Latency (ms) | RPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/changelog/history` | 179 | 0 (0.0%) | 2900.0 | 3215.0 | 10971.8 | 14.43 |
| `POST /api/workflow/execute` | 110 | 50 (45.5%) | 4000.0 | 4393.1 | 11020.8 | 8.87 |
| `GET /api/writeback/statistics` | 60 | 0 (0.0%) | 2600.0 | 3704.6 | 11002.7 | 4.84 |
| **Total** | **349** | **50 (14.3%)** | **3100.0** | **3670.5** | **11020.8** | **28.14** |

---

## 4. Performance Bottlenecks & Analysis

### 4.1. Core Bottleneck: Concurrent File I/O Lock (Windows OS specific)
During high concurrent loads, `/api/workflow/execute` encounters major concurrency failures. The FastAPI server logs captured the following exceptions:
- `[WinError 32] 다른 프로세스가 파일을 사용 중이므로 프로세스가 액세스할 수 없습니다` (Process cannot access the file because it is being used by another process)
- `[WinError 5] 액세스가 거부되었습니다` (Access denied during atomic rename from `.tmp` to `.json`)
- `[WinError 2] 지정된 파일을 찾을 수 없습니다` (File not found due to a race condition during rename/delete)
- `[Errno 13] Permission denied` (Read-lock block on `ai-voucher-2025.json`)

**Mechanism**:
The `OntologyService` implements database operations over raw JSON files in the `storage/{company_id}/{project_id}/ontology/{doc_id}.json` directory. To perform an action, the service:
1. Loads the JSON file.
2. Updates properties in-memory.
3. Writes the updated content to a `.tmp` file and performs an atomic rename (using `os.replace` or `shutil.move`).

Under Windows, file locks are strictly enforced. When multiple greenlets attempt to write or read this single JSON file concurrently:
- Atomic renames fail because another greenlet has the file open for reading or writing.
- Failing to write or read leads to:
  - **403 Forbidden**: Tenant authorization schema or metadata cannot be loaded, defaulting permissions to unauthorized (`PermissionError`).
  - **400 Bad Request**: File is corrupted or empty during read, causing entities to be missing (`KeyError`) or preconditions to fail.
  - **500 Internal Server Error**: Unhandled OS exceptions (`PermissionError`, `FileNotFoundError`) bubble up to the top level.

### 4.2. Database & SQL Query Execution
- The SQLite (and by extension Neon PostgreSQL) integration endpoints (`/api/changelog/history` and `/api/writeback/statistics`) performed with **0% failure rates** throughout all load scenarios.
- However, under Peak Load (200 users), SQL endpoints suffered from latency inflation (average ~3.2s to ~3.7s). This is caused by the FastAPI event loop being blocked by the file I/O operations of the workflow execute endpoints running in the same process, rather than database-level locks.

---

## 5. Optimization Recommendations

To prepare the platform for production and achieve true multi-tenant concurrency, the following structural improvements are recommended:

### Recommendation 1: Migrate Transactional Data to Relational Database (OLTP)
- **Problem**: Storing business/entity states in JSON files prevents concurrency and transaction safety.
- **Solution**: Move entity schemas, dynamic states, and property updates from JSON files directly into the PostgreSQL/Neon database. Keep JSON files only for static import/export templates or cold-storage document configurations. Database-level row locking (`SELECT FOR UPDATE`) will eliminate OS file-lock race conditions.

### Recommendation 2: Introduce Distributed Locking (Mutex)
- **Problem**: Concurrent writes to the same resource.
- **Solution**: If JSON files must be kept, implement a memory lock (using Python's `asyncio.Lock` or standard thread `Lock` in a multi-threaded server) or a distributed lock using **Redis** (e.g. `redlock`) for specific document IDs:
  ```python
  # Conceptual Redis lock implementation
  with redis_client.lock(f"lock:ontology:{doc_id}", timeout=5):
      # Load, modify, and save ontology JSON safely
  ```

### Recommendation 3: Queue-based Write-Back (Asynchronous Workers)
- **Problem**: Direct, synchronous file operations on the API hot path.
- **Solution**: Decouple state transitions from the API thread. When a user requests a workflow action, push the event to a message queue (e.g., Redis Queue, RabbitMQ, or a DB queue). An asynchronous, single-threaded background worker processes the queue and writes to the ontology store sequentially, removing atomic rename lockups from the HTTP request cycle.

### Recommendation 4: Optimize SQLite Connection Pool (For Local Testing)
- **Problem**: SQLite database locks during concurrent tests (`WinError 32` when cleaning up database files).
- **Solution**: Configure uvicorn to close all database connections cleanly during shutdown by specifying pool pre-ping and explicitly calling `engine.dispose()` on server shutdown event handlers.
