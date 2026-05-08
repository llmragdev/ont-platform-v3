from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app_context import AppContext
from backend.errors import AppError
from backend.repository import JsonFileDataRepository


class ServiceFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = AppContext()

    def test_ask_returns_grounded_answer_evidence_and_actions(self) -> None:
        result = self.app.ask("C001 고객의 O001 주문을 승인해도 될까?", "analyst")

        self.assertEqual(result["ontology_context"], {"customer_id": "C001", "order_id": "O001"})
        self.assertIn("Approval is likely allowed", result["answer"])
        self.assertIn("ApproveOrder", result["available_actions"])
        self.assertGreaterEqual(len(result["evidence"]), 1)
        self.assertIn("D001", {item["document_id"] for item in result["evidence"]})
        self.assertTrue(all(step["status"] == "ok" for step in result["steps"]))

    def test_relation_mismatch_stops_before_answer_generation(self) -> None:
        with self.assertRaises(AppError) as raised:
            self.app.ask("C001 고객과 O002 주문은 연결되어 있어?", "finance")

        self.assertEqual(raised.exception.code, "RELATION_MISMATCH")

    def test_order_context_uses_registry_relationships(self) -> None:
        order = self.app.ontology.get_object("O001")
        order.values["customer_id"] = "C999"
        order.values["product_ids"] = []

        context = self.app.ontology.get_order_context("O001", "C001")

        self.assertEqual(context["customer"]["id"], "C001")
        self.assertEqual({product["id"] for product in context["products"]}, {"P001", "P003"})

    def test_registry_can_traverse_relationships_in_both_directions(self) -> None:
        related_orders = self.app.ontology.registry.find_related("C001", "PLACED_ORDER")
        source_customers = self.app.ontology.registry.find_sources("O001", "PLACED_ORDER")
        relationships = self.app.ontology.registry.find_relationships("ORDER_CONTAINS_PRODUCT", source_id="O001")

        self.assertEqual({order.object_id for order in related_orders}, {"O001"})
        self.assertEqual([customer.object_id for customer in source_customers], ["C001"])
        self.assertEqual({relationship.target_id for relationship in relationships}, {"P001", "P003"})

    def test_unknown_order_returns_object_not_found(self) -> None:
        with self.assertRaises(AppError) as raised:
            self.app.ask("O999 주문 상태를 알려줘.", "analyst")

        self.assertEqual(raised.exception.code, "OBJECT_NOT_FOUND")
        self.assertIn("ASK_FAILED", {event["event_type"] for event in self.app.audit.list_events()})

    def test_document_permission_filters_finance_only_document(self) -> None:
        analyst_result = self.app.search_documents("custom pricing agreement finance", "analyst", 5)
        finance_result = self.app.search_documents("custom pricing agreement finance", "finance", 5)

        analyst_docs = {item["document_id"] for item in analyst_result["results"]}
        finance_docs = {item["document_id"] for item in finance_result["results"]}
        self.assertNotIn("D004", analyst_docs)
        self.assertIn("D004", finance_docs)

    def test_customer_sensitive_fields_are_masked_for_account_manager(self) -> None:
        context = self.app.order_context("O001", "analyst")

        self.assertEqual(context["customer"]["contract_terms"], "Custom discount rate: ***")

    def test_workflow_execute_rechecks_permission_and_updates_status(self) -> None:
        user = self.app.user("analyst")
        result = self.app.workflow.execute(user, "ApproveOrder", "O001", {"comment": "test"})
        context = self.app.order_context("O001", "analyst")

        self.assertEqual(result["from_status"], "Submitted")
        self.assertEqual(result["to_status"], "Approved")
        self.assertEqual(context["order"]["status"], "Approved")
        self.assertIn("ACTION_EXECUTED", {event["event_type"] for event in self.app.audit.list_events()})

    def test_high_risk_order_does_not_offer_approve_to_account_manager(self) -> None:
        result = self.app.ask("고위험 고객 주문을 자동 승인해도 돼? C003 O003", "analyst")

        self.assertNotIn("ApproveOrder", result["available_actions"])
        self.assertIn("RejectOrder", result["available_actions"])

    def test_json_repository_persists_order_status_updates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = JsonFileDataRepository(Path(temp_dir) / "ontology-data.json")
            first_app = AppContext(repository)
            first_app.workflow.execute(first_app.user("analyst"), "ApproveOrder", "O001", {"comment": "persist"})

            second_app = AppContext(JsonFileDataRepository(Path(temp_dir) / "ontology-data.json"))
            context = second_app.order_context("O001", "analyst")

        self.assertEqual(context["order"]["status"], "Approved")


if __name__ == "__main__":
    unittest.main()
