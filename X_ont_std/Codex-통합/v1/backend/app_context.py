from __future__ import annotations

import os
from time import perf_counter

from .audit import AuditService
from .errors import AppError
from .ontology import OntologyService
from .policy import PolicyEngine
from .rag import LLMGateway, RAGService, extract_object_ids
from .repository import DataRepository, InMemoryDataRepository, JsonFileDataRepository
from .search import SearchService
from .workflow import WorkflowService


class AppContext:
    def __init__(self, repository: DataRepository | None = None) -> None:
        data_path = os.environ.get("ONTOLOGY_DATA_PATH")
        self.repository = repository or (JsonFileDataRepository(data_path) if data_path else InMemoryDataRepository())
        self.raw = self.repository.load()
        self.audit = AuditService()
        self.ontology = OntologyService(self.raw, self.repository.save)
        self.policy = PolicyEngine(self.audit)
        self.search = SearchService(self.raw["documents"], self.policy)
        self.rag = RAGService()
        self.llm = LLMGateway()
        self.workflow = WorkflowService(self.ontology, self.policy, self.audit)

    def user(self, user_key: str = "analyst") -> dict:
        user = self.raw["users"].get(user_key)
        if user is None:
            raise AppError("AUTH_REQUIRED", "사용자 인증이 필요합니다.", 401)
        return user

    def me(self, user_key: str) -> dict:
        user = self.user(user_key)
        self.audit.record("ME_READ", user, "User", user["id"], {})
        return user

    def order_context(self, order_id: str, user_key: str = "analyst", customer_id: str | None = None) -> dict:
        user = self.user(user_key)
        context = self.ontology.get_order_context(order_id, customer_id)
        self.policy.assert_can_read_object(user, context["order"])
        masked = {
            "order": self.policy.mask_object(user, context["order"]),
            "customer": self.policy.mask_object(user, context["customer"]),
            "products": [self.policy.mask_object(user, product) for product in context["products"]],
        }
        masked["available_actions"] = self.policy.available_actions(user, context["order"], context["customer"])
        self.audit.record("OBJECT_CONTEXT_READ", user, "Order", order_id, {"customer_id": context["customer"]["id"]})
        return masked

    def search_documents(self, query: str, user_key: str = "analyst", top_k: int = 3) -> dict:
        user = self.user(user_key)
        results = self.search.search(query, user, top_k)
        self.audit.record("DOCUMENT_SEARCHED", user, "Document", "-", {"query": query, "count": len(results)})
        return {"query": query, "results": self._present_search_results(results)}

    def ask(self, question: str, user_key: str = "analyst") -> dict:
        started = perf_counter()
        user = self.user(user_key)
        steps: list[dict] = []
        object_ids: dict[str, str | None] = {"customer_id": None, "order_id": None}
        try:
            object_ids = self._step(steps, "질문에서 객체 후보 추출", lambda: extract_object_ids(question))
            if object_ids["order_id"] is None:
                raise AppError("OBJECT_NOT_FOUND", "요청한 객체를 찾을 수 없습니다.", 404)
            context = self._step(
                steps,
                "Ontology Service에서 객체와 관계 조회",
                lambda: self.ontology.get_order_context(object_ids["order_id"], object_ids["customer_id"]),
            )
            self._step(steps, "Policy Engine에서 객체 접근 권한 확인", lambda: self.policy.assert_can_read_object(user, context["order"]))
            available_actions = self._step(
                steps,
                "Policy Engine에서 액션 권한 확인",
                lambda: self.policy.available_actions(user, context["order"], context["customer"]),
            )
            masked_context = {
                "order": self.policy.mask_object(user, context["order"]),
                "customer": self.policy.mask_object(user, context["customer"]),
                "products": [self.policy.mask_object(user, product) for product in context["products"]],
            }
            search_query = self._step(steps, "RAG Service에서 검색 질의 강화", lambda: self.rag.build_search_query(question, masked_context))
            search_results = self._step(steps, "Search Service에서 권한 필터링 문서 검색", lambda: self.search.search(search_query, user, 3))
            prompt = self._step(steps, "RAG Service에서 프롬프트 생성", lambda: self.rag.build_prompt(question, masked_context, search_results))
            answer = self._step(steps, "LLM Gateway에서 규칙 기반 답변 생성", lambda: self.llm.generate_rule_based_answer(masked_context, search_results, available_actions))
            latency_ms = round((perf_counter() - started) * 1000)
            log = {
                "question": question,
                "detected_objects": [value for value in [object_ids["customer_id"], object_ids["order_id"]] if value],
                "search_query": search_query,
                "retrieved_documents": [item["document"]["id"] for item in search_results],
                "answer_status": "ANSWERED",
                "latency_ms": latency_ms,
            }
            self.audit.record("ASK_COMPLETED", user, "Order", context["order"]["id"], log)
            return {
                "answer": answer,
                "detected_objects": log["detected_objects"],
                "ontology_context": {
                    "customer_id": context["customer"]["id"],
                    "order_id": context["order"]["id"],
                },
                "context": masked_context,
                "evidence": self._present_search_results(search_results),
                "available_actions": available_actions,
                "prompt": prompt,
                "steps": steps,
                "latency_ms": latency_ms,
            }
        except AppError as error:
            self.audit.record(
                "ASK_FAILED",
                user,
                "Order",
                object_ids["order_id"] or "-",
                {
                    "question": question,
                    "detected_objects": [value for value in [object_ids["customer_id"], object_ids["order_id"]] if value],
                    "error_code": error.code,
                    "latency_ms": round((perf_counter() - started) * 1000),
                },
            )
            raise

    def _present_search_results(self, results: list[dict]) -> list[dict]:
        return [
            {
                "document_id": item["document"]["id"],
                "title": item["document"]["title"],
                "score": item["score"],
                "text": item["document"]["text"],
                "related_objects": item["document"].get("related_objects", []),
            }
            for item in results
        ]

    @staticmethod
    def _step(steps: list[dict], name: str, fn):
        value = fn()
        steps.append({"name": name, "status": "ok"})
        return value
