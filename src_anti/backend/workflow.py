from typing import List, Tuple
from data import repo

class WorkflowService:
    # (Current Status, Action) -> New Status
    TRANSITIONS = {
        ("Submitted", "ApproveOrder"): "Approved",
        ("Submitted", "RejectOrder"): "Rejected",
        ("Submitted", "HoldOrder"): "Review",
        ("Review", "ApproveOrder"): "Approved",
        ("Review", "RejectOrder"): "Rejected",
    }

    @staticmethod
    def get_available_actions(status: str) -> List[str]:
        return [action for (s, action), next_s in WorkflowService.TRANSITIONS.items() if s == status]

    @staticmethod
    def validate_and_execute(order_id: str, action: str) -> Tuple[bool, str]:
        order = repo.get_order(order_id)
        if not order:
            return False, "Order not found"
        
        current_status = order["status"]
        next_status = WorkflowService.TRANSITIONS.get((current_status, action))
        
        if not next_status:
            return False, f"Action {action} is not allowed for status {current_status}"
        
        repo.update_order_status(order_id, next_status)
        return True, next_status
