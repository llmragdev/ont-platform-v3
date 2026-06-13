"""BaseRepositoryInterface — ABC for repository pattern (v3.0).

Concrete implementations:
  - JsonOntologyRepository (this module, JSON files)
  - SqliteOntologyRepository (future v4.0)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.models.tenant_context import TenantContext

T = TypeVar("T")


class BaseRepositoryInterface(ABC, Generic[T]):
    @abstractmethod
    def get(self, id: str, ctx: TenantContext) -> T | None: ...

    @abstractmethod
    def list(self, ctx: TenantContext, **filters) -> list[T]: ...

    @abstractmethod
    def save(self, item: T, ctx: TenantContext) -> T: ...

    @abstractmethod
    def delete(self, id: str, ctx: TenantContext) -> bool: ...
