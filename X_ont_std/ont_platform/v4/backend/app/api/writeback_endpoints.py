"""Write-back API endpoints for DLQ management and replay"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.models import WriteBackQueue
from app.dependencies import get_db

router = APIRouter(prefix="/api/writeback", tags=["writeback"])


@router.post("/replay/{queue_id}")
async def replay_queue_item(
    queue_id: str,
    db: Session = Depends(get_db)
):
    """
    실패한 (DLQ) 아이템을 다시 큐에 투입

    Args:
        queue_id: 재실행할 아이템 ID
        db: 데이터베이스 세션

    Returns:
        {status: "replayed", queue_id: "..."}

    Errors:
        - 400: Item not in DLQ
        - 404: Item not found
    """
    # 아이템 조회
    item = db.query(WriteBackQueue).filter(
        WriteBackQueue.id == queue_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.status != "DLQ":
        raise HTTPException(
            status_code=400,
            detail=f"Item is {item.status}, not DLQ"
        )

    # 상태 재설정
    item.status = "PENDING"
    item.retry_count = 0
    item.next_retry_at = None
    item.dlq_reason = None
    item.dlq_at = None

    db.commit()

    return {
        "status": "replayed",
        "queue_id": queue_id
    }


@router.get("/dlq/items")
async def get_dlq_items(db: Session = Depends(get_db)):
    """
    DLQ 상태의 모든 아이템 조회

    Returns:
        {items: [...], count: int}
    """
    items = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "DLQ"
    ).order_by(WriteBackQueue.dlq_at.desc()).all()

    return {
        "items": [
            {
                "id": item.id,
                "target_system": item.target_system,
                "payload": item.payload,
                "dlq_reason": item.dlq_reason,
                "dlq_at": item.dlq_at.isoformat() if item.dlq_at else None,
                "last_error_at": item.last_error_at.isoformat() if item.last_error_at else None,
                "error_message": item.error_message,
                "retry_count": item.retry_count,
            }
            for item in items
        ],
        "count": len(items)
    }


@router.get("/dlq/items/{queue_id}")
async def get_dlq_item(
    queue_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 DLQ 아이템 상세 조회

    Args:
        queue_id: 아이템 ID

    Returns:
        아이템 상세 정보
    """
    item = db.query(WriteBackQueue).filter(
        WriteBackQueue.id == queue_id,
        WriteBackQueue.status == "DLQ"
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")

    return {
        "id": item.id,
        "target_system": item.target_system,
        "payload": item.payload,
        "dlq_reason": item.dlq_reason,
        "dlq_at": item.dlq_at.isoformat() if item.dlq_at else None,
        "last_error_at": item.last_error_at.isoformat() if item.last_error_at else None,
        "error_message": item.error_message,
        "retry_count": item.retry_count,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/statistics")
async def get_writeback_statistics(db: Session = Depends(get_db)):
    """
    Write-back 큐 통계

    Returns:
        {pending: int, confirmed: int, dlq: int, failed: int}
    """
    pending = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "PENDING"
    ).count()

    confirmed = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "CONFIRMED"
    ).count()

    dlq = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "DLQ"
    ).count()

    failed = db.query(WriteBackQueue).filter(
        WriteBackQueue.status == "FAILED"
    ).count()

    return {
        "pending": pending,
        "confirmed": confirmed,
        "dlq": dlq,
        "failed": failed,
        "total": pending + confirmed + dlq + failed
    }
