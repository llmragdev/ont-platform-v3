import subprocess
import time
import os
import sys
import json
import csv
import urllib.request
import shutil
from pathlib import Path

PORT = 8001
HOST = f"http://localhost:{PORT}"
LOCUST_FILE = "performance_tests/locustfile.py"

# Absolute database path definition to avoid relative path mismatches
V3_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = V3_ROOT / "perf_test.db"
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"

ONTOLOGY_FILE = V3_ROOT / "storage" / "demo-co" / "proj-01" / "ontology" / "ai-voucher-2025.json"
ONTOLOGY_BAK = V3_ROOT / "storage" / "demo-co" / "proj-01" / "ontology" / "ai-voucher-2025.json.bak"

def setup_ontology_file():
    print(f"Setting up ontology file at: {ONTOLOGY_FILE}")
    if not ONTOLOGY_FILE.exists():
        print(f"Warning: {ONTOLOGY_FILE} does not exist.")
        return

    # Backup original file
    shutil.copy2(ONTOLOGY_FILE, ONTOLOGY_BAK)
    
    with open(ONTOLOGY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Find P001AAA and modify it
    found = False
    for entity in data.get("entities", []):
        if entity.get("id") == "P001AAA":
            entity["type"] = "PROJECT"
            entity["status"] = "Approved"
            entity["properties"] = {
                "status": "Approved",
                "deadline": "2026-12-31",
                "budget": 100000000,
                "manager": "manager@nipa.go.kr"
            }
            found = True
            break
            
    if not found:
        # Create a new entity if not found
        new_entity = {
            "id": "P001AAA",
            "type": "PROJECT",
            "name": "AI바우처 2025",
            "properties": {
                "status": "Approved",
                "deadline": "2026-12-31",
                "budget": 100000000,
                "manager": "manager@nipa.go.kr"
            },
            "created_at": "2026-05-14T09:00:00.000000+00:00",
            "created_by": "seed",
            "version": 1,
            "status": "Approved",
            "updated_at": "2026-05-14T09:00:00.000000+00:00"
        }
        if "entities" not in data:
            data["entities"] = []
        data["entities"].append(new_entity)
        
    with open(ONTOLOGY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Modified P001AAA in ontology file successfully.")

def restore_ontology_file():
    if ONTOLOGY_BAK.exists():
        print(f"Restoring ontology file from backup: {ONTOLOGY_BAK}")
        try:
            shutil.move(str(ONTOLOGY_BAK), str(ONTOLOGY_FILE))
            print("Ontology file restored.")
        except Exception as e:
            print(f"Failed to restore ontology file: {e}")

def setup_test_db():
    print(f"Setting up performance test database at: {DB_URL}")
    if DB_PATH.exists():
        try:
            os.remove(DB_PATH)
        except Exception as e:
            print(f"Could not remove old DB file: {e}")
            
    os.environ["DATABASE_URL"] = DB_URL
    
    # Add src/backend to path to import models
    sys.path.insert(0, str(V3_ROOT / "src" / "backend"))
    
    from app.db.database import init_db, SessionLocal
    from app.db.models import Entity
    
    init_db()
    
    db = SessionLocal()
    try:
        # Check if entity exists
        entity = db.query(Entity).filter(Entity.id == "P001AAA").first()
        if not entity:
            entity = Entity(
                id="P001AAA",
                entity_type="PROJECT",
                domain_id="ai-voucher-2025",
                doc_id="ai-voucher-2025",
                properties={
                    "status": "Approved",
                    "budget": 100000000,
                    "manager": "manager@nipa.go.kr",
                    "deadline": "2026-12-31"
                }
            )
            db.add(entity)
            db.commit()
            print("Inserted sample entity P001AAA successfully.")
    finally:
        db.close()

def clean_test_db():
    print("Cleaning up performance test database...")
    if DB_PATH.exists():
        try:
            os.remove(DB_PATH)
            print("Test database file removed.")
        except Exception as e:
            print(f"Failed to remove test database: {e}")

def is_server_alive():
    try:
        with urllib.request.urlopen(f"{HOST}/api/health", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False

def run_locust_headless(users, spawn_rate, duration, csv_prefix):
    print(f"\nRunning Locust: Users={users}, SpawnRate={spawn_rate}, Duration={duration}...")
    cmd = [
        "locust",
        "-f", LOCUST_FILE,
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "--run-time", duration,
        "--host", HOST,
        f"--csv={csv_prefix}"
    ]
    
    # Run locust and wait
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Locust error: {result.stderr}")
    return result.returncode == 0

def parse_locust_stats(csv_prefix):
    stats_file = f"{csv_prefix}_stats.csv"
    if not os.path.exists(stats_file):
        print(f"Stats file {stats_file} not found.")
        return {}

    results = {}
    with open(stats_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "")
            if not name:
                continue
            
            # Skip total row or non-api rows
            if name == "Aggregated":
                name = "Total"
            
            results[name] = {
                "requests": int(row.get("Request Count", 0)),
                "failures": int(row.get("Failure Count", 0)),
                "median_latency": float(row.get("50%", 0)),
                "p95_latency": float(row.get("95%", 0)),
                "p99_latency": float(row.get("99%", 0)),
                "avg_latency": float(row.get("Average Response Time", 0)),
                "min_latency": float(row.get("Min Response Time", 0)),
                "max_latency": float(row.get("Max Response Time", 0)),
                "rps": float(row.get("Current RPS", 0) or row.get("Requests/s", 0) or 0.0)
            }
    return results

def main():
    print("=== Phase 3 Performance Benchmarking & Load Testing ===")
    
    # Change working dir to v3 root
    os.chdir(V3_ROOT)
    print(f"Working Directory set to: {V3_ROOT}")
    
    # Setup test DB and sample data
    setup_test_db()
    setup_ontology_file()
    
    server_process = None
    uvicorn_log = None
    if not is_server_alive():
        print(f"Starting FastAPI server on port {PORT}...")
        env = os.environ.copy()
        env["DATABASE_URL"] = DB_URL
        log_file_path = V3_ROOT / "performance_tests" / "uvicorn.log"
        uvicorn_log = open(log_file_path, "w", encoding="utf-8")
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
            stdout=uvicorn_log,
            stderr=uvicorn_log,
            cwd="src/backend",
            env=env
        )
        
        # Wait for server to start
        for i in range(10):
            print("Waiting for server to start...")
            time.sleep(2)
            if is_server_alive():
                print("Server is healthy!")
                break
        else:
            print("Failed to start FastAPI server.")
            if server_process:
                server_process.terminate()
            if uvicorn_log:
                uvicorn_log.close()
            clean_test_db()
            restore_ontology_file()
            sys.exit(1)
    else:
        print("Server is already running! Please ensure it is using the test SQLite database configuration.")

    try:
        # Create output directory for csv results
        os.makedirs("performance_tests/results", exist_ok=True)
        
        # -------------------------------------------------------------
        # TASK 1: API Benchmarking (Baseline)
        # -------------------------------------------------------------
        print("\n--- Task 1: API Baseline Benchmarking ---")
        run_locust_headless(users=10, spawn_rate=2, duration="15s", csv_prefix="performance_tests/results/baseline")
        baseline_stats = parse_locust_stats("performance_tests/results/baseline")
        
        with open("performance_tests/benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(baseline_stats, f, indent=2, ensure_ascii=False)
        print("Task 1 completed. Saved to benchmark_results.json")

        # -------------------------------------------------------------
        # TASK 2: Load Testing (Scenarios A, B, C)
        # -------------------------------------------------------------
        print("\n--- Task 2: Load Testing (Ramp-up, Constant, Peak) ---")
        
        load_results = {}
        
        # Scenario A: Ramp Up (10 -> 50 -> 100 users)
        print("\nRunning Scenario A: Ramp-up load...")
        run_locust_headless(users=50, spawn_rate=5, duration="20s", csv_prefix="performance_tests/results/rampup")
        load_results["Scenario_A_RampUp"] = parse_locust_stats("performance_tests/results/rampup")

        # Scenario B: Constant Load (50 users)
        print("\nRunning Scenario B: Constant load...")
        run_locust_headless(users=50, spawn_rate=50, duration="20s", csv_prefix="performance_tests/results/constant")
        load_results["Scenario_B_Constant"] = parse_locust_stats("performance_tests/results/constant")

        # Scenario C: Peak Load (200 users)
        print("\nRunning Scenario C: Peak load...")
        run_locust_headless(users=200, spawn_rate=100, duration="15s", csv_prefix="performance_tests/results/peak")
        load_results["Scenario_C_Peak"] = parse_locust_stats("performance_tests/results/peak")

        with open("performance_tests/load_test_results.json", "w", encoding="utf-8") as f:
            json.dump(load_results, f, indent=2, ensure_ascii=False)
        print("Task 2 completed. Saved to load_test_results.json")
        
    finally:
        if server_process:
            print("\nShutting down FastAPI server...")
            server_process.terminate()
            server_process.wait()
            print("FastAPI server shut down successfully.")
        
        if uvicorn_log:
            uvicorn_log.close()
        
        # Clean up database file and restore ontology file
        clean_test_db()
        restore_ontology_file()

if __name__ == "__main__":
    main()
