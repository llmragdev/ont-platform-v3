from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TenantContext:
    user_id: str
    company_id: str
    project_id: str
    role: str
    permissions: dict[str, bool] = field(default_factory=dict)

    def can(self, flag: str) -> bool:
        return self.permissions.get(flag, False)

    def assert_can(self, flag: str) -> None:
        if not self.can(flag):
            raise PermissionError(f"Permission denied: {flag}")
