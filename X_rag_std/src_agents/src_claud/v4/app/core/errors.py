from fastapi import HTTPException


class RagError(Exception):
    error_code = "rag_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DocumentParsingError(RagError):
    error_code = "document_parsing_error"


class EmbeddingError(RagError):
    error_code = "embedding_error"


class VectorDbError(RagError):
    error_code = "vector_db_error"


class LlmError(RagError):
    error_code = "llm_error"


class DocumentNotFoundError(RagError):
    error_code = "document_not_found"


class ProjectNotFoundError(RagError):
    error_code = "project_not_found"


def http_error(status_code: int, error_code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "status": "error",
            "data": None,
            "error": {"code": error_code, "message": message},
        },
    )
