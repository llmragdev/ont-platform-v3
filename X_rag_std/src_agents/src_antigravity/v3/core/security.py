from fastapi import Header, HTTPException, Request

def get_tenant_id(x_tenant_id: str = Header(None)) -> str:
    """
    X-Tenant-ID 헤더를 검증하고 반환합니다.
    표준 v1.3에 따라 필수값이며, 누락 시 400 에러를 발생시킵니다.
    """
    if not x_tenant_id:
        raise HTTPException(
            status_code=400, 
            detail="X-Tenant-ID header is required for multi-tenant isolation."
        )
    return x_tenant_id

def get_org_id(x_org_id: str = Header(None)) -> str | None:
    """
    X-Org-ID 헤더를 반환합니다. (선택사항)
    누락 시 None을 반환하며, 이는 전사 범위 검색/소유를 의미합니다.
    """
    return x_org_id
