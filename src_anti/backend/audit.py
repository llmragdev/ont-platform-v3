from datetime import datetime
import uuid
from data import repo

class AuditService:
    @staticmethod
    def log_event(user: str, event_type: str, description: str, metadata: dict = None):
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {}
        }
        repo.add_audit_event(event)
        print(f"[AUDIT] {event['timestamp']} - {user} - {event_type}: {description}")
