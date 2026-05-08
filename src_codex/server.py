from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from backend.app_context import AppContext
from backend.errors import AppError

ROOT = Path(__file__).resolve().parent
APP = AppContext()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                self.handle_api_get(parsed.path, parse_qs(parsed.query))
                return
            self.serve_static(parsed.path)
        except AppError as error:
            self.send_json({"error": {"code": error.code, "message": error.message}}, error.status)
        except Exception as error:
            self.send_json({"error": {"code": "MODEL_ERROR", "message": str(error)}}, 500)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            body = self.read_json()
            query = parse_qs(parsed.query)
            user_key = query.get("user", ["analyst"])[0]
            if parsed.path == "/api/search":
                self.send_json(APP.search_documents(body.get("query", ""), user_key, int(body.get("top_k", 3))))
                return
            if parsed.path == "/api/ask":
                self.send_json(APP.ask(body.get("question", ""), user_key))
                return
            if parsed.path == "/api/workflow/execute":
                user = APP.user(user_key)
                result = APP.workflow.execute(user, body["action"], body["order_id"], body.get("payload", {}))
                self.send_json({"result": result, "queue": APP.workflow.queue(user)})
                return
            self.send_json({"error": {"code": "NOT_FOUND", "message": "Unknown API"}}, 404)
        except AppError as error:
            self.send_json({"error": {"code": error.code, "message": error.message}}, error.status)
        except Exception as error:
            self.send_json({"error": {"code": "MODEL_ERROR", "message": str(error)}}, 500)

    def handle_api_get(self, path: str, query: dict[str, list[str]]) -> None:
        user_key = query.get("user", ["analyst"])[0]
        user = APP.user(user_key)
        if path == "/api/me":
            self.send_json(APP.me(user_key))
            return
        if path == "/api/ontology/object-types":
            self.send_json({"object_types": APP.ontology.object_types()})
            return
        if path == "/api/objects/customers":
            visible = []
            for customer in APP.ontology.customers():
                if APP.policy.can_read_object(user, customer):
                    visible.append(APP.policy.mask_object(user, customer))
            self.send_json({"customers": visible})
            return
        if path == "/api/objects/orders":
            visible = []
            for order in APP.ontology.orders():
                if APP.policy.can_read_object(user, order):
                    visible.append(APP.policy.mask_object(user, order))
            self.send_json({"orders": visible})
            return
        if path.startswith("/api/objects/orders/") and path.endswith("/context"):
            order_id = path.split("/")[-2]
            customer_id = query.get("customer_id", [None])[0]
            self.send_json(APP.order_context(order_id, user_key, customer_id))
            return
        if path.startswith("/api/objects/orders/"):
            order_id = path.split("/")[-1]
            context = APP.order_context(order_id, user_key)
            self.send_json(context["order"])
            return
        if path == "/api/workflow/queue":
            self.send_json({"queue": APP.workflow.queue(user)})
            return
        if path == "/api/audit/events":
            self.send_json({"events": APP.audit.list_events()})
            return
        self.send_json({"error": {"code": "NOT_FOUND", "message": "Unknown API"}}, 404)

    def serve_static(self, path: str) -> None:
        if path in ["", "/"]:
            path = "/index.html"
        target = (ROOT / path.lstrip("/")).resolve()
        if ROOT not in target.parents and target != ROOT:
            self.send_json({"error": {"code": "FORBIDDEN", "message": "Forbidden"}}, 403)
            return
        if not target.exists() or target.is_dir():
            self.send_json({"error": {"code": "NOT_FOUND", "message": "Not found"}}, 404)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Operational Ontology Console: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()

