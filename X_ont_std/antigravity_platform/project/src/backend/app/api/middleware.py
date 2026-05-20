from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.identity import UserIdentity, PermissionSet

class IdentityMiddleware(BaseHTTPMiddleware):
    """
    모든 요청의 Authorization 헤더를 검사하여 테넌트 사용자 정보를 추출하는 미들웨어.
    추출된 정보는 request.state.identity에 저장되어 API 전역에서 공유됨.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. 헤더 추출
        auth_header = request.headers.get("Authorization")
        identity = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # 2. JWT 디코딩
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                
                # 3. Identity 모델 생성 (Payload 기반)
                # 실제 운영 시에는 이 단계에서 DB 조회가 필요할 수 있으나, 
                # MVP에서는 토큰 내 정보를 신뢰하거나 캐시된 정보를 사용함.
                identity = UserIdentity(
                    user_id=payload.get("sub"),
                    username=payload.get("name"),
                    company_id=payload.get("company_id"),
                    current_project_id=payload.get("project_id", "default"),
                    role=payload.get("role", "viewer"),
                    permissions=PermissionSet(**payload.get("permissions", {})),
                    project_ids=payload.get("project_ids", [])
                )
            except (JWTError, Exception):
                identity = None
        
        # 4. Request State에 주입 (Context 역할)
        request.state.identity = identity
        
        response = await call_next(request)
        return response
