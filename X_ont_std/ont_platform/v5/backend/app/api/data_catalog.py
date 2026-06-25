from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.models.data_catalog import CatalogTableResponse, QueryExecuteRequest, QueryExecuteResponse
from app.services.data_catalog_service import DataCatalogService

router = APIRouter(prefix="/api/data-catalog", tags=["data-catalog"])

_service_instance = None


def get_catalog_service() -> DataCatalogService:
    """데이터 카탈로그 서비스 싱글톤 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = DataCatalogService()
    return _service_instance


@router.get("/tables", response_model=List[CatalogTableResponse])
async def get_tables_metadata(
    service: DataCatalogService = Depends(get_catalog_service)
) -> List[CatalogTableResponse]:
    """메달리온 아키텍처 테이블 스키마 정보 조회"""
    try:
        return service.get_tables_metadata()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tables metadata: {str(e)}"
        )


@router.post("/query/execute", response_model=QueryExecuteResponse)
async def execute_catalog_query(
    request: QueryExecuteRequest,
    service: DataCatalogService = Depends(get_catalog_service)
) -> QueryExecuteResponse:
    """데이터 카탈로그 콘솔에서 SQL 쿼리 안전 실행"""
    try:
        return service.execute_query(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute query: {str(e)}"
        )
