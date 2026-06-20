from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_tenant_context
from app.models.streamlit_app import StreamlitRunRequest, StreamlitRunResponse, StreamlitSaveRequest, StreamlitSaveResponse
from app.models.tenant_context import TenantContext
from app.services.streamlit_app_service import StreamlitAppService


router = APIRouter(prefix="/api/streamlit-apps", tags=["streamlit-apps"])

_service_instance = None


def get_streamlit_service() -> StreamlitAppService:
    """Streamlit 앱 서비스 싱글톤 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = StreamlitAppService()
    return _service_instance


@router.post("/run", response_model=StreamlitRunResponse)
async def run_streamlit_app(
    request: StreamlitRunRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    service: StreamlitAppService = Depends(get_streamlit_service),
) -> StreamlitRunResponse:
    """
    Streamlit 앱 저장 및 실행

    - 코드를 파일로 저장
    - Streamlit 서버 실행 (설치 여부에 따라 실제 또는 fallback)
    - 실행 가능한 URL 반환
    """
    try:
        response = service.run_app(request, ctx)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run streamlit app: {str(e)}"
        )


@router.post("/save", response_model=StreamlitSaveResponse)
async def save_streamlit_app(
    request: StreamlitSaveRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    service: StreamlitAppService = Depends(get_streamlit_service),
) -> StreamlitSaveResponse:
    """Streamlit 앱 소스를 실행 없이 파일로 저장"""
    try:
        return service.save_app(request, ctx)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save streamlit app: {str(e)}"
        )


@router.post("/stop/{app_id}")
async def stop_streamlit_app(
    app_id: str,
    service: StreamlitAppService = Depends(get_streamlit_service),
) -> dict:
    """Streamlit 앱 중지"""
    try:
        success = service.stop_app(app_id)
        return {
            "app_id": app_id,
            "status": "stopped" if success else "not_running",
            "message": "App stopped successfully" if success else "App was not running"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop streamlit app: {str(e)}"
        )
