# ont_platform v1.0 Archive

**Archived**: 2026-05-13  
**Source**: `E:\ontology_edu\claud_통합`  
**Status**: Feature-complete Sprint 06 (Multi-tenant permission management)

## What's in this archive

| Module | Description |
|--------|-------------|
| `backend/app/main.py` | 54 FastAPI endpoints |
| `backend/app/tenant.py` | TenantManager + require_permission Depends |
| `backend/app/ontology_store.py` | JSON-based entity/relationship CRUD |
| `backend/app/vector_search.py` | Single Chroma instance (company_id soft filter) |
| `backend/app/app_context.py` | Mixed: workflow demo + ontology context |
| `backend/tests/test_sprint06_dod.py` | 14 DoD tests — all passing |
| `frontend/src/context/UserContext.tsx` | Tenant user state |
| `frontend/src/components/TenantUserSwitcher.tsx` | Company-grouped dropdown |

## Sprint completion (v1.0)

- Sprint 01-04: Core ontology + RAG + hybrid query
- Sprint 05: Integration test automation (15 scenarios)
- Sprint 06: Multi-tenant, multi-project, permission management ✅

## Known limitations (addressed in v2.0)

1. Single Chroma instance — no V-ID sharding, size will become bottleneck
2. `app_context.py` mixes workflow domain logic with generic ontology
3. Physical storage not isolated — all tenants share same directory
4. `storage_config` not abstracted — paths hardcoded throughout

## How to run (v1.0)

```powershell
# Backend
conda activate claud_be
cd E:\ontology_edu\claud_통합\backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend
conda activate claud_fe
cd E:\ontology_edu\claud_통합\frontend
npm run dev
```
