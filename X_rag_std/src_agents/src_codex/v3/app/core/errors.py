from fastapi import HTTPException


class RagError(Exception):
    error_code = "rag_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DocumentParsingError(RagError):
    error_code = "document_parsing_error"


class EmbeddingApiTimeout(RagError):
    error_code = "embedding_api_timeout"


class VectorDbConnectionError(RagError):
    error_code = "vector_db_connection_error"


def http_error(status_code: int, error_code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "status": "error",
            "data": None,
            "error": {"error_code": error_code, "message": message},
        },
    )
