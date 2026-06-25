"""Runner script executing JSON test scenarios and logging results to CSV."""
from __future__ import annotations

import os
import csv
import json
import logging
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.load.load_test import LoadTester

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LoadTestRunner")


def run_load_scenarios():
    load_dir = Path(__file__).resolve().parent
    scenarios_path = load_dir / "test_scenarios.json"
    results_dir = load_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    csv_path = results_dir / "performance_baseline.csv"

    if not scenarios_path.exists():
        logger.error("test_scenarios.json not found.")
        return

    with open(scenarios_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize tester
    tester = LoadTester()
    try:
        tester.setup_database_schema()
        # Load 1K entities as standard test footprint
        tester.populate_scale_data(scale_entities=1000)

        # Prepare CSV writing
        csv_headers = ["ScenarioId", "Category", "Concurrency", "TotalRequests", "RPS", "P50_ms", "P90_ms", "SLA_Status"]
        rows = []

        for scenario in data.get("scenarios", []):
            scenario_id = scenario["id"]
            category = scenario["category"]
            target_sla = scenario["target_latency_ms"]

            logger.info("Executing Scenario: %s (%s)", scenario_id, category)
            # Run test with concurrency 10
            metrics = tester.run_benchmark_queries(concurrency=10, total_requests=50)

            if "error" in metrics:
                logger.error("Scenario %s failed: %s", scenario_id, metrics["error"])
                continue

            p90 = metrics["p90_latency_ms"]
            sla_status = "PASS" if p90 <= target_sla else "FAIL"

            rows.append({
                "ScenarioId": scenario_id,
                "Category": category,
                "Concurrency": 10,
                "TotalRequests": 50,
                "RPS": metrics["requests_per_second"],
                "P50_ms": metrics["p50_latency_ms"],
                "P90_ms": p90,
                "SLA_Status": sla_status
            })

        # Save to CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(rows)

        logger.info("Load test completed successfully. Results saved to %s", csv_path)

    finally:
        tester.cleanup_scale_data()


if __name__ == "__main__":
    run_load_scenarios()
