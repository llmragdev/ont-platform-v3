# Query Planner Analysis & Optimization Report

## 1. Introduction

This document provides a technical walkthrough of the query planning characteristics of multi-hop join queries within our PostgreSQL-based ontology platform. It identifies specific bottleneck areas (sequential table scans during multi-join paths) and proposes optimization techniques including early filter pushdowns and index nested-loop scans.

---

## 2. Bottleneck Query: Two-Hop Joins

The primary bottleneck occurs during two-hop traversals over relationships (e.g., finding the manager of a department where a specific employee works).

### 2.1. Unoptimized Translated SQL Query
```sql
SELECT r2.to_entity_id 
FROM relationships r1
JOIN relationships r2 ON r1.to_entity_id = r2.from_entity_id
WHERE r1.from_entity_id = 'entity_999' 
  AND r1.relation_type = 'works_at'
  AND r2.relation_type = 'managed_by';
```

### 2.2. Query Planner Analysis (`EXPLAIN`)
Without composite indexes, the execution plan looks like this:

```
Nested Loop (cost=45.20..15200.40 rows=2 width=64) (actual time=25.40..1380.20 ms)
  -> Bitmap Heap Scan on relationships r1 (cost=12.20..250.30 rows=15 width=64)
       Recheck Cond: (from_entity_id = 'entity_999'::text)
       Filter: (relation_type = 'works_at'::text)
       -> Bitmap Index Scan on idx_relationships_from (cost=0.00..8.20 rows=50)
  -> Hash Join (cost=33.00..980.50 rows=2 width=64) (actual time=0.20..75.20 ms)
       Hash Cond: (r2.from_entity_id = r1.to_entity_id)
       -> Seq Scan on relationships r2 (cost=0.00..850.00 rows=45000 width=64) <-- CRITICAL BOTTLENECK
            Filter: (relation_type = 'managed_by'::text)
```

#### Problem Analysis
1. **Hash Join with Sequential Scan**: Because the database does not have a single index grouping `from_entity_id` and `relation_type`, it falls back to a full sequential table scan on `r2` (`Seq Scan on relationships r2`).
2. **High Memory/Disk Overhead**: As the size of `relationships` approaches 1M rows, the hash table size exceeds `work_mem`, forcing PostgreSQL to dump execution traces to temporary disk cache.

---

## 3. Query Optimization Strategies

To reduce execution latency from **1.4s to <400ms**, we implement two key query design patterns:

### 3.1. Early Filter Pushdown (Subquery Isolation)
Instead of executing a flat join that evaluates all rows, we isolate the first hop inside a subquery or Common Table Expression (CTE) to force the database planner to compute a tiny set of intermediate keys first.

```sql
WITH first_hop AS (
    SELECT to_entity_id 
    FROM relationships 
    WHERE from_entity_id = 'entity_999' 
      AND relation_type = 'works_at'
)
SELECT r2.to_entity_id 
FROM relationships r2
JOIN first_hop fh ON r2.from_entity_id = fh.to_entity_id
WHERE r2.relation_type = 'managed_by';
```

### 3.2. Join Reordering (Cardinality-based)
If one part of the multi-hop join is heavily filtered (e.g., filtering on a very rare relationship type or a specific tenant domain), we structure the SPARQL translator engine to output the SQL starting with the most restrictive filter first, avoiding massive intermediate cartesian products.

---

## 4. Index-Only Scans
By defining composite indexes that match the query's projecting columns (e.g., creating an index on both `(from_entity_id, relation_type, to_entity_id)`), we enable **Index-Only Scans**. This allows PostgreSQL to resolve the entire join sequence directly within the memory index leaf-nodes, avoiding slow heap-table reads entirely.
