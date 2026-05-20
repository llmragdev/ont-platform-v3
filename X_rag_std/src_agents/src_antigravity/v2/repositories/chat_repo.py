import json
from sqlalchemy.orm import Session
from models.db_models import DialogHistory
from models.schemas import RetrievedChunk
from typing import List

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_dialog(self, query: str, answer: str, used_chunks: List[RetrievedChunk]) -> DialogHistory:
        # Pydantic 모델 리스트를 JSON 문자열로 직렬화하여 저장
        chunks_json = json.dumps([chunk.model_dump() for chunk in used_chunks], ensure_ascii=False)
        
        history = DialogHistory(
            query=query,
            answer=answer,
            used_chunks_meta=chunks_json
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history
