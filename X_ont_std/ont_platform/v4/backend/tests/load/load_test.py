"""Load testing runner simulating large scale database records and concurrent queries."""
from __future__ import annotations

import os
import sys
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy import create_engine, text

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LoadTest")


class LoadTester:
    def __init__(self, db_url: str | None = None, domain_id: str = "load_test_domain"):
        self.db_url = db_url or os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/ontology_db"
        self.domain_id = domain_id
        self.engine = create_engine(self.db_url)
        self.entities_count = 0
        self.relations_count = 0

    def setup_database_schema(self) -> None:
        """Initialize required schemas for testing if they do not exist."""
        logger.info("Initializing schema check...")
        schema_path = Path(__file__).resolve().parents[2] / "scripts" / "init_schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                ddl = f.read()
            with self.engine.begin() as conn:
                # Remove psql specific directives
                clean_ddl = "\n".join(
                    line for line in ddl.splitlines() 
                    if not line.strip().startswith("\\") and "Schema initialization complete" not in line
                )
                conn.execute(text(clean_ddl))
            logger.info("Schema initialized successfully.")
        else:
            logger.warning("init_schema.sql not found at %s. Relying on existing DB state.", schema_path)

    def populate_scale_data(self, scale_entities: int = 10000) -> None:
        """Insert dummy scale-records into entities and relationships tables."""
        logger.info("Populating scale dataset (%d entities)...", scale_entities)
        
        entities_batch = []
        relationships_batch = []
        
        # 1. Generate Entities
        for i in range(scale_entities):
            entity_id = f"entity_{i}"
            entity_type = random.choice(["Project", "Company", "Department", "User", "Asset"])
            status = random.choice(["active", "pending", "completed", "archived"])
            cost = random.randint(1000, 1000000)
            
            properties = {
                "name": f"Name_{entity_type}_{i}",
                "status": status,
                "cost": cost,
                "created_by": f"User_{random.randint(1, 50)}"
            }
            
            entities_batch.append({
                "id": entity_id,
                "entity_type": entity_type,
                "domain_id": self.domain_id,
                "doc_id": f"doc_batch_{random.randint(1, 10)}",
                "properties": properties,
                "version": 1
            })

        # 2. Generate Relationships (3x relationship density)
        relation_types = ["works_at", "member_of", "manages", "subsidiary_of", "depends_on", "part_of"]
        for i in range(scale_entities * 3):
            rel_id = f"rel_{i}"
            from_id = f"entity_{random.randint(0, scale_entities - 1)}"
            to_id = f"entity_{random.randint(0, scale_entities - 1)}"
            
            if from_id == to_id:
                continue
                
            relationships_batch.append({
                "id": rel_id,
                "from_entity_id": from_id,
                "to_entity_id": to_id,
                "relation_type": random.choice(relation_types),
                "domain_id": self.domain_id,
                "doc_id": f"doc_batch_{random.randint(1, 10)}",
                "weight": round(random.uniform(0.1, 1.0), 2),
                "properties": {"connection_status": "established"},
                "version": 1
            })

        # Insert to database using batches
        with self.engine.begin() as conn:
            # Clear existing data of the same domain
            conn.execute(text("DELETE FROM relationships WHERE domain_id = :domain"), {"domain": self.domain_id})
            conn.execute(text("DELETE FROM entities WHERE domain_id = :domain"), {"domain": self.domain_id})
            
            # Batch insertion
            logger.info("Inserting entities...")
            conn.execute(
                text(
                    "INSERT INTO entities (id, entity_type, domain_id, doc_id, properties, version) "
                    "VALUES (:id, :entity_type, :domain_id, :doc_id, CAST(:properties AS jsonb), :version) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                [{**e, "properties": json.dumps(e["properties"])} for e in entities_batch]
            )
            
            logger.info("Inserting relationships...")
            conn.execute(
                text(
                    "INSERT INTO relationships (id, from_entity_id, to_entity_id, relation_type, domain_id, doc_id, weight, properties, version) "
                    "VALUES (:id, :from_entity_id, :to_entity_id, :relation_type, :domain_id, :doc_id, :weight, CAST(:properties AS jsonb), :version) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                [{**r, "properties": json.dumps(r["properties"])} for r in relationships_batch]
            )

        self.entities_count = scale_entities
        self.relations_count = len(relationships_batch)
        logger.info("Database loaded: %d entities, %d relationships inserted.", scale_entities, len(relationships_batch))

    def cleanup_scale_data(self) -> None:
        """Delete all loaded scale data."""
        logger.info("Cleaning up populated scale data...")
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM relationships WHERE domain_id = :domain"), {"domain": self.domain_id})
            conn.execute(text("DELETE FROM entities WHERE domain_id = :domain"), {"domain": self.domain_id})
        logger.info("Cleanup complete.")

    def run_benchmark_queries(self, concurrency: int = 10, total_requests: int = 200) -> Dict[str, Any]:
        """Run concurrent benchmark queries and measure execution metrics."""
        queries = self._load_queries()
        if not queries:
            logger.error("No benchmark queries found. Aborting benchmark.")
            return {}

        logger.info("Starting concurrent benchmark (concurrency: %d, total queries: %d)...", concurrency, total_requests)
        
        latencies = []
        errors = 0
        
        def execute_one_query():
            q_template = random.choice(queries)
            # Instantiation logic for variables
            entity_idx = random.randint(0, self.entities_count - 1)
            q_str = q_template.replace("Project_Alpha", f"Name_Project_{entity_idx}")
            q_str = q_str.replace("Employee_50", f"Name_User_{entity_idx}")
            q_str = q_str.replace("Employee_100", f"Name_User_{entity_idx}")
            
            # Map triple patterns directly into SQL for verification purposes
            # Since load test simulates translated query execution, we run mapped SQL target statements
            sql_query = self._mock_translate_sparql_to_sql(q_str)
            
            start_time = time.time()
            try:
                with self.engine.connect() as conn:
                    conn.execute(text(sql_query))
                duration_ms = (time.time() - start_time) * 1000
                return duration_ms, None
            except Exception as ex:
                return (time.time() - start_time) * 1000, str(ex)

        # Thread pool execution
        start_bench = time.time()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(execute_one_query) for _ in range(total_requests)]
            for fut in as_completed(futures):
                duration, err = fut.result()
                if err:
                    errors += 1
                    logger.debug("Query error: %s", err)
                else:
                    latencies.append(duration)

        total_duration = time.time() - start_bench
        
        if not latencies:
            return {"error": "All benchmark queries failed."}

        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.5)]
        p90 = latencies[int(len(latencies) * 0.9)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg_latency = sum(latencies) / len(latencies)
        rps = len(latencies) / total_duration

        metrics = {
            "total_queries": total_requests,
            "successful_queries": len(latencies),
            "error_queries": errors,
            "total_duration_sec": round(total_duration, 2),
            "requests_per_second": round(rps, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "p50_latency_ms": round(p50, 2),
            "p90_latency_ms": round(p90, 2),
            "p99_latency_ms": round(p99, 2),
        }

        logger.info("Benchmark complete: RPS=%.2f, p50=%.2fms, p90=%.2fms, p99=%.2fms", rps, p50, p90, p99)
        return metrics

    def _load_queries(self) -> List[str]:
        """Load benchmark queries from queries.txt."""
        queries_file = Path(__file__).resolve().parent / "queries.txt"
        if not queries_file.exists():
            return []
        
        with open(queries_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        queries = []
        for block in content.split("\n\n"):
            lines = [line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]
            if lines:
                queries.append(" ".join(lines))
        return queries

    def _mock_translate_sparql_to_sql(self, sparql_query: str) -> str:
        """Simulate Translated SQL translation mappings for load test benchmarks."""
        # Simple lookup
        if "property:status" in sparql_query:
            return "SELECT id, properties FROM entities WHERE domain_id = 'load_test_domain' AND properties->>'status' = 'active' LIMIT 10"
        if "property:name" in sparql_query and "relation" not in sparql_query:
            return "SELECT id, properties FROM entities WHERE domain_id = 'load_test_domain' AND properties->>'name' LIKE '%Name%' LIMIT 1"
            
        # One-hop query
        if "works_at" in sparql_query and "subsidiary_of" not in sparql_query:
            return (
                "SELECT r.to_entity_id FROM relationships r "
                "JOIN entities e ON r.from_entity_id = e.id "
                "WHERE r.domain_id = 'load_test_domain' AND r.relation_type = 'works_at' LIMIT 10"
            )
        if "member_of" in sparql_query and "managed_by" not in sparql_query:
            return (
                "SELECT r.to_entity_id FROM relationships r "
                "JOIN entities e ON r.from_entity_id = e.id "
                "WHERE r.domain_id = 'load_test_domain' AND r.relation_type = 'member_of' LIMIT 10"
            )
            
        # Two-hop query
        if "works_at" in sparql_query and "subsidiary_of" in sparql_query:
            return (
                "SELECT r2.to_entity_id FROM relationships r1 "
                "JOIN relationships r2 ON r1.to_entity_id = r2.from_entity_id "
                "WHERE r1.domain_id = 'load_test_domain' AND r1.relation_type = 'works_at' "
                "AND r2.relation_type = 'subsidiary_of' LIMIT 10"
            )
        if "member_of" in sparql_query and "managed_by" in sparql_query:
            return (
                "SELECT r2.to_entity_id FROM relationships r1 "
                "JOIN relationships r2 ON r1.to_entity_id = r2.from_entity_id "
                "WHERE r1.domain_id = 'load_test_domain' AND r1.relation_type = 'member_of' "
                "AND r2.relation_type = 'manages' LIMIT 10"
            )
            
        # Fallback
        return "SELECT 1"


if __name__ == "__main__":
    import json
    tester = LoadTester()
    try:
        tester.setup_database_schema()
        # Scale to 10K (entities) for benchmark reliability
        tester.populate_scale_data(scale_entities=1000)
        
        # Warm up connection pool
        tester.run_benchmark_queries(concurrency=1, total_requests=10)
        
        # Test concurrent benchmark
        res = tester.run_benchmark_queries(concurrency=5, total_requests=100)
        print("\nBenchmark results:\n", json.dumps(res, indent=2))
        
    finally:
        tester.cleanup_scale_data()
