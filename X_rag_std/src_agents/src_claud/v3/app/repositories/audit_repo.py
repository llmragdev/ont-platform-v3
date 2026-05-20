from sqlalchemy.orm import Session

from app.models.db_models import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        action: str,
        tenant_id: str,
        user_id: str | None = None,
        resource: str | None = None,
    ) -> None:
        entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
        )
        self.db.add(entry)
        self.db.commit()
