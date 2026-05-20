#!/usr/bin/env python3
"""직접 find_by_name 테스트"""
import sys
import os
import logging
from pathlib import Path

# 환경 설정
os.environ["GEMINI_API_KEY"] = "AIzaSyAMt7L0OVBzarSLn-Tn-3RyNbaIKg4RKPA"
os.environ["LLM_MODEL_NAME"] = "gemini-2.5-flash-lite"

# sys.path 설정
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path.parent.parent))
sys.path.insert(0, str(backend_path))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from app.services.ontology import OntologyService
from app.models.tenant_context import TenantContext

# 테스트
svc = OntologyService()
ctx = TenantContext(company_id="demo-co", project_id="proj-01", user_id="test-user", role="admin")

test_queries = [
    "2025년 AI바우처",
    "AI바우처",
    "2025",
    "과학기술정보통신부",
    "NIPA",
    "AI반도체분과",
]

print("[TEST] find_by_name 직접 테스트")
print("=" * 60)

for query in test_queries:
    results = svc.find_by_name(ctx, query)
    print(f"\nQuery: {query}")
    print(f"Results: {len(results)}")
    for r in results[:3]:
        print(f"  - {r.get('name')} (type={r.get('type')})")
