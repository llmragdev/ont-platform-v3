from fastapi import Request, HTTPException, status, Depends
from app.models.identity import UserIdentity

def get_current_identity(request: Request) -> UserIdentity:
    """미들웨어에서 주입된 현재 사용자 정보를 반환"""
    identity = getattr(request.state, "identity", None)
    if not identity:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid authentication token required"
        )
    return identity

class PermissionChecker:
    """특정 권한을 요구하는 의존성 클래스"""
    def __init__(self, permission_name: str):
        self.permission_name = permission_name

    def __call__(self, identity: UserIdentity = Depends(get_current_identity)):
        # 권한 셋에서 해당 권한이 True인지 확인
        has_permission = getattr(identity.permissions, self.permission_name, False)
        
        # admin 롤은 모든 권한 허용 (슈퍼유저 정책)
        if identity.role == "admin":
            has_permission = True
            
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission: {self.permission_name}"
            )
        return identity

# 사용 예시: 
# @app.post("/ontology/entities", dependencies=[Depends(PermissionChecker("can_edit_ontology"))])
