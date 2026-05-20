from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


ERROR_MESSAGES = {
    "OBJECT_NOT_FOUND": "요청한 객체를 찾을 수 없습니다.",
    "RELATION_MISMATCH": "고객과 주문의 연결 관계가 일치하지 않습니다.",
    "RELATION_MISSING": "주문과 연결된 고객 관계를 찾을 수 없습니다.",
    "FORBIDDEN": "이 정보에 접근할 권한이 없습니다.",
    "DOCUMENT_NOT_FOUND": "답변에 필요한 근거 문서를 찾지 못했습니다.",
    "ACTION_NOT_ALLOWED": "현재 상태에서는 이 액션을 실행할 수 없습니다.",
    "MODEL_ERROR": "답변 생성 중 문제가 발생했습니다. 다시 시도하세요.",
    "AUTH_REQUIRED": "사용자 인증이 필요합니다.",
}
