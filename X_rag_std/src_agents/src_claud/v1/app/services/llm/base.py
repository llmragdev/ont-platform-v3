from abc import ABC, abstractmethod
from typing import AsyncGenerator

from app.models.schemas import RetrievedChunk


class LlmClientBase(ABC):
    @abstractmethod
    def generate_answer(self, query: str, chunks: list[RetrievedChunk]) -> str: ...

    @abstractmethod
    async def stream_answer(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> AsyncGenerator[str, None]: ...
