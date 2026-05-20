from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import server
from backend.app_context import AppContext


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        server.APP = AppContext()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def test_get_me(self) -> None:
        payload = self.get_json("/api/me?user=analyst")

        self.assertEqual(payload["role"], "AccountManager")
        self.assertEqual(payload["email"], "kim.ops@example.com")

    def test_post_ask(self) -> None:
        payload = self.post_json(
            "/api/ask?user=analyst",
            {"question": "C001 고객의 O001 주문을 승인해도 될까?"},
        )

        self.assertEqual(payload["ontology_context"]["order_id"], "O001")
        self.assertIn("ApproveOrder", payload["available_actions"])
        self.assertGreaterEqual(len(payload["evidence"]), 1)

    def test_workflow_execute_then_queue_refreshes(self) -> None:
        payload = self.post_json(
            "/api/workflow/execute?user=analyst",
            {"order_id": "O001", "action": "ApproveOrder", "payload": {"comment": "api test"}},
        )

        self.assertEqual(payload["result"]["to_status"], "Approved")
        self.assertNotIn("O001", {item["id"] for item in payload["queue"]})

    def test_relation_mismatch_returns_json_error(self) -> None:
        error = self.get_error("/api/objects/orders/O002/context?user=finance&customer_id=C001")

        self.assertEqual(error["error"]["code"], "RELATION_MISMATCH")

    def get_json(self, path: str) -> dict:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def post_json(self, path: str, body: dict) -> dict:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def get_error(self, path: str) -> dict:
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(f"{self.base_url}{path}", timeout=5)
        return json.loads(raised.exception.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

