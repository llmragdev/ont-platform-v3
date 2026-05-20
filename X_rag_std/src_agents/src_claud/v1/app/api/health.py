import sqlalchemy

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.schemas import HealthCheckItem, HealthCheckResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    checks: list[HealthCheckItem] = []

    # DB 연결 확인
    try:
        db.execute(sqlalchemy.text("SELECT 1"))
        checks.append(HealthCheckItem(name="database", status="ok"))
    except Exception as exc:
        checks.append(HealthCheckItem(name="database", status="error", detail=str(exc)))

    # 벡터 스토어 디렉터리 확인
    try:
        if not settings.vector_store_dir.exists():
            raise FileNotFoundError(f"vector_store_dir not found: {settings.vector_store_dir}")
        checks.append(HealthCheckItem(name="vector_store", status="ok"))
    except Exception as exc:
        checks.append(HealthCheckItem(name="vector_store", status="error", detail=str(exc)))

    # LLM 프로바이더 확인 (mock은 항상 ok)
    try:
        checks.append(
            HealthCheckItem(
                name="llm",
                status="ok",
                detail=settings.llm_provider,
            )
        )
    except Exception as exc:
        checks.append(HealthCheckItem(name="llm", status="error", detail=str(exc)))

    overall = "ok" if all(c.status == "ok" for c in checks) else "degraded"
    return HealthCheckResponse(status=overall, checks=checks)
