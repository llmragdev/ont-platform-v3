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
        company_id: str = "default",
    ) -> DialogHistory:
        chunks_json = json.dumps(
            [c.model_dump() for c in used_chunks],
            ensure_ascii=False,
            default=str,
        )
        record = DialogHistory(
            company_id=company_id,
            query=query,
            answer=answer,
            used_chunks=chunks_json,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
