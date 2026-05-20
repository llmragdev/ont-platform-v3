from __future__ import annotations

from .errors import AppError
from .models import ActionDefinition, ObjectInstance, WorkflowEvent, WorkflowTransition


class WorkflowEngine:
    def __init__(self) -> None:
        self.actions: dict[str, ActionDefinition] = {}
        self.transitions: list[WorkflowTransition] = []
        self.events: list[WorkflowEvent] = []

    def register_action(self, action: ActionDefinition) -> None:
        self.actions[action.name] = action

    def register_transition(self, transition: WorkflowTransition) -> None:
        self.transitions.append(transition)

    def get_available_actions(self, target: ObjectInstance, payload: dict) -> list[str]:
        return [
            transition.action_name
            for transition in self.transitions
            if transition.can_execute(target, payload)
        ]

    def execute(self, action_name: str, target: ObjectInstance, payload: dict) -> dict:
        action = self.actions.get(action_name)
        if action is None:
            raise AppError("ACTION_NOT_ALLOWED", "현재 상태에서는 이 액션을 실행할 수 없습니다.", 400)
        matching = None
        for transition in self.transitions:
            if transition.action_name == action_name and transition.can_execute(target, payload):
                matching = transition
                break
        if matching is None:
            raise AppError("ACTION_NOT_ALLOWED", "현재 상태에서는 이 액션을 실행할 수 없습니다.", 409)
        from_status = target.get_status()
        action_result = action.execute(target, payload)
        target.set_status(matching.to_status)
        event = WorkflowEvent(
            object_id=target.object_id,
            action_name=action_name,
            from_status=from_status,
            to_status=matching.to_status,
            actor=payload["actor"],
            payload=payload,
        )
        self.events.insert(0, event)
        return {
            "object_id": target.object_id,
            "action": action_name,
            "from_status": from_status,
            "to_status": matching.to_status,
            "action_result": action_result,
        }


class WorkflowService:
    def __init__(self, ontology, policy, audit) -> None:
        self.ontology = ontology
        self.policy = policy
        self.audit = audit
        self.engine = WorkflowEngine()
        self._build_engine()

    def _build_engine(self) -> None:
        order_type = self.ontology.registry.object_types["Order"]

        def approve_order(order: ObjectInstance, payload: dict) -> dict:
            order.values["approved_by"] = payload["actor"]
            order.values["approval_comment"] = payload.get("comment")
            return {"message": "Order approved", "approved_by": payload["actor"]}

        def reject_order(order: ObjectInstance, payload: dict) -> dict:
            order.values["rejected_by"] = payload["actor"]
            order.values["reject_reason"] = payload.get("reason", "Rejected from console")
            return {"message": "Order rejected", "rejected_by": payload["actor"]}

        def hold_order(order: ObjectInstance, payload: dict) -> dict:
            order.values["hold_by"] = payload["actor"]
            order.values["hold_reason"] = payload.get("reason", "Need more information")
            return {"message": "Order moved to review", "hold_by": payload["actor"]}

        def fulfill_order(order: ObjectInstance, payload: dict) -> dict:
            order.values["fulfilled_by"] = payload["actor"]
            return {"message": "Order fulfilled", "fulfilled_by": payload["actor"]}

        def close_order(order: ObjectInstance, payload: dict) -> dict:
            order.values["closed_by"] = payload["actor"]
            return {"message": "Order closed", "closed_by": payload["actor"]}

        for name, handler in [
            ("ApproveOrder", approve_order),
            ("RejectOrder", reject_order),
            ("HoldOrder", hold_order),
            ("FulfillOrder", fulfill_order),
            ("CloseOrder", close_order),
        ]:
            self.engine.register_action(ActionDefinition(name, order_type, handler))

        def policy_allows(order: ObjectInstance, payload: dict) -> bool:
            context = self.ontology.get_order_context(order.object_id)
            return self.policy.can_execute_action(
                payload["user"], payload["action"], context["order"], context["customer"]
            )

        self.engine.register_transition(
            WorkflowTransition("SubmitToApproved", order_type, "Submitted", "ApproveOrder", "Approved", policy_allows)
        )
        self.engine.register_transition(
            WorkflowTransition("ReviewToApproved", order_type, "Review", "ApproveOrder", "Approved", policy_allows)
        )
        self.engine.register_transition(
            WorkflowTransition("SubmitToRejected", order_type, "Submitted", "RejectOrder", "Rejected", policy_allows)
        )
        self.engine.register_transition(
            WorkflowTransition("ReviewToRejected", order_type, "Review", "RejectOrder", "Rejected", policy_allows)
        )
        self.engine.register_transition(
            WorkflowTransition("SubmitToReview", order_type, "Submitted", "HoldOrder", "Review", policy_allows)
        )
        self.engine.register_transition(
            WorkflowTransition("ApprovedToFulfilled", order_type, "Approved", "FulfillOrder", "Fulfilled")
        )
        self.engine.register_transition(
            WorkflowTransition("FulfilledToClosed", order_type, "Fulfilled", "CloseOrder", "Closed")
        )

    def queue(self, user: dict) -> list[dict]:
        rows: list[dict] = []
        for order in self.ontology.orders():
            try:
                context = self.ontology.get_order_context(order["id"])
                self.policy.assert_can_read_object(user, context["order"])
                actions = self.policy.available_actions(user, context["order"], context["customer"])
                if actions:
                    rows.append(
                        {**context["order"], "customer": context["customer"], "available_actions": actions}
                    )
            except AppError:
                continue
        return rows

    def execute(self, user: dict, action_name: str, order_id: str, payload: dict | None = None) -> dict:
        context = self.ontology.get_order_context(order_id)
        self.policy.assert_can_read_object(user, context["order"])
        available = self.policy.available_actions(user, context["order"], context["customer"])
        if action_name not in available:
            self.audit.record("ACTION_DENIED", user, "Order", order_id, {"action": action_name})
            raise AppError("ACTION_NOT_ALLOWED", "현재 상태에서는 이 액션을 실행할 수 없습니다.", 409)
        target = self.ontology.get_object(order_id)
        result = self.engine.execute(
            action_name,
            target,
            {"actor": user["email"], "user": user, "action": action_name, **(payload or {})},
        )
        self.ontology.update_order_status(order_id, result["to_status"])
        self.audit.record("ACTION_EXECUTED", user, "Order", order_id, result)
        return result
