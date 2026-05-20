from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.models.schemas import RetrievedChunk


class LlmClientBase(ABC):
    @abstractmethod
    def generate_answer(self, query: str, chunks: list[RetrievedChunk]) -> str: ...

    @abstractmethod
    def stream_answer(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]: ...
