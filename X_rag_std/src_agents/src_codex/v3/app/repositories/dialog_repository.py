import json

from sqlalchemy.orm import Session

from app.models.db_models import DialogHistory
from app.models.schemas import RetrievedChunk


class DialogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(
        self,
        query: str,
        answer: str,
        used_chunks: list[RetrievedChunk],
        tenant_id: str,
        org_id: str | None = None,
    ) -> DialogHistory:
        record = DialogHistory(
            tenant_id=tenant_id,
            org_id=org_id,
            query=query,
            answer=answer,
            used_chunks=json.dumps(
                [chunk.model_dump(mode="json") for chunk in used_chunks],
                ensure_ascii=False,
            ),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
