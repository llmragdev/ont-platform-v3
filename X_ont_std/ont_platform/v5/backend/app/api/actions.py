"""액션 API 엔드포인트"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.action_executor import ActionExecutor
from app.services.permission_checker import PermissionChecker


router = APIRouter(prefix="/api/actions", tags=["actions"])

permission_checker = PermissionChecker()


@router.get("/{action_id}/permission-check")
async def check_permission(
    action_id: str,
    user_role: str = "PM",
    amount: float = 0,
    db: Session = Depends(get_db)
):
    """액션 실행 권한 확인"""
    context = {"amount": amount} if amount > 0 else None
    allowed, reason = permission_checker.check_action(user_role, action_id, context)

    return {
        "action_id": action_id,
        "user_role": user_role,
        "allowed": allowed,
        "reason": reason
    }


@router.get("/available")
async def get_available_actions(
    user_role: str = "PM",
    db: Session = Depends(get_db)
):
    """사용자가 실행할 수 있는 액션 목록"""
    allowed_actions = permission_checker.get_allowed_actions(user_role)

    return {
        "user_role": user_role,
        "available_actions": allowed_actions
    }


@router.post("/{action_id}/execute")
async def execute_action(
    action_id: str,
    request: dict = Body(...),
    user_role: str = "PM",
    user_id: str = "unknown",
    db: Session = Depends(get_db)
):
    """
    액션 실행

    요청 본문:
    {
        "entity_id": "proj_123",
        "approver": "john@example.com",  # action에 따라 다른 필드
        "amount": 1500000  # start_payment의 경우
    }
    """

    # 1. 권한 확인
    context = {"amount": request.get("amount", 0)} if request.get("amount") else None
    allowed, reason = permission_checker.check_action(user_role, action_id, context)

    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    # 2. 필수 필드 확인
    entity_id = request.get("entity_id")
    if not entity_id:
        raise HTTPException(status_code=400, detail="Missing required field: entity_id")

    # 3. 액션 실행
    executor = ActionExecutor(db)

    # 액션별 추가 매개변수
    kwargs = {
        "user_role": user_role,
        "user_id": user_id,
    }

    # 액션별 필드 추가
    if action_id == "approve_project":
        kwargs["approver"] = request.get("approver", user_id)
    elif action_id == "reject_project":
        kwargs["reason"] = request.get("reason", "")
        kwargs["rejected_by"] = request.get("rejected_by", user_id)
    elif action_id == "change_deadline":
        kwargs["new_deadline"] = request.get("new_deadline")
        kwargs["changed_by"] = request.get("changed_by", user_id)
    elif action_id == "request_more_info":
        kwargs["info_needed"] = request.get("info_needed", "")
        kwargs["requested_by"] = request.get("requested_by", user_id)
    elif action_id == "start_payment":
        kwargs["amount"] = request.get("amount")
        kwargs["approved_by"] = request.get("approved_by", user_id)
    elif action_id == "complete_project":
        kwargs["completed_by"] = request.get("completed_by", user_id)

    result = executor.execute(action_id, entity_id, **kwargs)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or result.message)

    return {
        "status": "success",
        "message": result.message,
        "data": result.data
    }


@router.get("/available-actions")
async def list_available_actions(db: Session = Depends(get_db)):
    """모든 사용 가능한 액션 목록"""
    executor = ActionExecutor(db)
    actions = executor.get_available_actions()

    return {
        "actions": [
            {
                "id": action_id,
                "name": name
            }
            for action_id, name in actions.items()
        ]
    }
