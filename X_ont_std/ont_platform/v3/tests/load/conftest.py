import sys
from pathlib import Path
import pytest
import asyncio

# Ensure backend source is in sys.path for importing 'app'
backend_path = Path(__file__).resolve().parents[2] / "src" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    """HTTP client targeting the local API instance"""
    async with AsyncClient(app=app, base_url="http://localhost:8001") as client:
        yield client

@pytest.fixture
def performance_metrics():
    """Collector to track performance latency percentiles and errors"""
    class MetricsCollector:
        def __init__(self):
            self.latencies = []
            self.errors = []
            self.start_time = None
        
        def record_latency(self, ms: float):
            self.latencies.append(ms)
        
        def record_error(self, error: str):
            self.errors.append(error)
        
        def get_stats(self):
            if not self.latencies:
                return {}
            
            import numpy as np
            latencies = np.array(self.latencies)
            
            return {
                "count": len(self.latencies),
                "mean": float(np.mean(latencies)),
                "median": float(np.median(latencies)),
                "p50": float(np.percentile(latencies, 50)),
                "p95": float(np.percentile(latencies, 95)),
                "p99": float(np.percentile(latencies, 99)),
                "min": float(np.min(latencies)),
                "max": float(np.max(latencies)),
                "error_count": len(self.errors)
            }
    
    return MetricsCollector()
