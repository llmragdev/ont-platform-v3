import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from app.repositories.base import BaseRepository

class AuditRepository(BaseRepository):
    """테넌트별 감사 로그를 JSONL 형식으로 기록하는 저장소 (Append-only)"""

    LOG_FILE = "audit_log.jsonl"

    def append_log(self, event_data: Dict[str, Any]):
        """새로운 감사 로그 이벤트를 파일 끝에 추가"""
        log_path = self._get_file_path(self.LOG_FILE)
        
        # 로그 엔트리 생성
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "company_id": self.company_id,
            "project_id": self.project_id,
            **event_data
        }
        
        # JSONL 형식으로 한 줄 추가
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def list_logs(self, limit: int = 100) -> list:
        """최신 로그 목록 조회 (학습/검증용)"""
        log_path = self._get_file_path(self.LOG_FILE)
        if not log_path.exists():
            return []
            
        logs = []
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                logs.append(json.loads(line))
        
        return logs[-limit:]  # 최신 N개 반환
