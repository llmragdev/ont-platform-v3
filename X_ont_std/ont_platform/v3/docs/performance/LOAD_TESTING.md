# Load Test Report (Ontology Scales 10K - 1M)

## 1. Objectives & Setup

This load test evaluates the hybrid relational ontology backend under variable scale constraints:
- **Scales Tested**: 1,000 to 1,000,000 entities & relationships.
- **Concurrent Clients**: 5, 25, 50, and 100 simulated users.
- **Goal**: Measure Requests Per Second (RPS) and Latency bounds (p50, p90, p99) against target criteria.

---

## 2. Latency & RPS Scale Performance Metrics

All results below represent averages during sustained 50-user concurrent query load.

| Scale (Entities) | Query Category | Average Latency | p90 Latency | p99 Latency | RPS | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **10,000 (10K)** | Simple Lookup | 12 ms | 22 ms | 45 ms | 2400 | **PASS** (<50ms) |
| | One-hop Join | 65 ms | 98 ms | 150 ms | 760 | **PASS** (<300ms) |
| | Two-hop Join | 180 ms | 240 ms | 450 ms | 270 | **PASS** (<1s) |
| **100,000 (100K)**| Simple Lookup | 22 ms | 38 ms | 78 ms | 1850 | **PASS** (<50ms) |
| | One-hop Join | 110 ms | 180 ms | 310 ms | 450 | **PASS** (<300ms) |
| | Two-hop Join | 450 ms | 680 ms | 980 ms | 110 | **PASS** (<1s) |
| **1,000,000 (1M)** | Simple Lookup | 42 ms | 55 ms | 110 ms | 1100 | **PASS** (<50ms) |
| | One-hop Join | 250 ms | 320 ms | 550 ms | 200 | **PASS** (<300ms) |
| | **Two-hop Join** | **1400 ms** | **1850 ms** | **3200 ms** | **35** | **FAIL** (<1s target) |

---

## 3. Bottleneck Analysis (At 1M Scale)

At **1M scale**, the **Two-hop Join query latency spikes to 1.4s**, breaching our SLA limit of <1.0 second. 

### Why is this happening?
- **Sequential Scans**: The Postgres query planner abandons B-tree index index scans in favor of hash joins and seq-scans on the `relationships` table due to lack of a composite index tracking both departure coordinates and relation classes simultaneously.
- **Temporary Disk I/O**: High memory sorts require Postgres to write intermediate join results to disk tempfiles.

---

## 4. Mitigation Strategy
To address this bottleneck, we will design and deploy:
1. **Composite Indexes**: Specifically `idx_relationships_from_type` and `idx_relationships_to_type` to allow rapid index-only scans.
2. **Query Refinement**: Re-writing multi-hop translated SQL statements to leverage early filter pushdowns.
