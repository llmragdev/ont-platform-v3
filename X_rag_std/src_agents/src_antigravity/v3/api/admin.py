from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from services.admin_service import AdminService
from core.security import get_tenant_id

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/projects/{project_code}/swap")
def trigger_index_swap(
    project_code: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    특정 프로젝트의 인덱스 스왑을 트리거합니다. (관리자 권한 필요)
    """
    admin_service = AdminService(db)
    try:
        result = admin_service.perform_index_swap(tenant_id, project_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index swap failed: {str(e)}")
