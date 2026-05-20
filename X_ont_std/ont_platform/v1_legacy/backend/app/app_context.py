from __future__ import annotations

from time import perf_counter

from .audit import AuditService
from .auth import hash_password
from .errors import AppError
from .llm_gateway import LLMGateway
from .ontology import OntologyService
from .policy import PolicyEngine
from .rag import RAGService, extract_object_ids
from .repository import DataRepository, resolve_default as resolve_default_repository
from .search import SearchService
from .telemetry import span
from .workflow import WorkflowService
from .workflow_graph import WorkflowGraphService
from .vector_search import VectorSearchService
from .workflow_graph_engine import WorkflowGraphEngine


class AppContext:
    def __init__(self, repository: DataRepository | None = None) -> None:
        self.repository = repository or resolve_default_repository()
        self.raw = self.repository.load()
        self._ensure_password_hashes()
        self.audit = AuditService()
        self.ontology = OntologyService(self.raw, self.repository.save)
        self.policy = PolicyEngine(self.audit, schema=self.ontology.schema)
        self.search = SearchService(self.raw["documents"], self.policy)
        self.rag = RAGService()
        self.llm = LLMGateway()
        self.workflow = WorkflowService(self.ontology, self.policy, self.audit)
        self.workflow_graph = WorkflowGraphService(self.raw, self.repository, self.policy, self.audit)
        self.workflow_graph_engine = WorkflowGraphEngine(
            self.llm, self.audit, ontology=self.ontology, policy=self.policy
        )
        self.vector_search = VectorSearchService()

    def _ensure_password_hashes(self) -> None:
        """data.py의 평문 password → pbkdf2 해시. 영속 저장소에도 반영."""
        changed = False
        for user_key, user in self.raw.get("users", {}).items():
            plain = user.pop("password", None)
            if plain is not None and "password_hash" not in user:
                user["password_hash"] = hash_password(plain)
                changed = True
        if changed:
            self.repository.save(self.raw)

    def reset(self) -> None:
        """인메모리 상태를 초기 시드로 되돌린다 (테스트/E2E 용)."""
        from .data import fresh_raw_data
        from .audit import AuditService

        self.raw = fresh_raw_data()
        self.repository.save(self.raw)
        self.audit = AuditService()
        self.ontology = OntologyService(self.raw, self.repository.save)
        self.policy = PolicyEngine(self.audit, schema=self.ontology.schema)
        self.search = SearchService(self.raw["documents"], self.policy)
        self.workflow = WorkflowService(self.ontology, self.policy, self.audit)
        self.workflow_graph = WorkflowGraphService(self.raw, self.repository, self.policy, self.audit)
        self.workflow_graph_engine = WorkflowGraphEngine(
            self.llm, self.audit, ontology=self.ontology, policy=self.policy
        )

    def user(self, user_key: str = "analyst") -> dict:
        user = self.raw["users"].get(user_key)
        if user is None:
            raise AppError("AUTH_REQUIRED", "사용자 인증이 필요합니다.", 401)
        return user

    def me(self, user_key: str) -> dict:
        user = self.user(user_key)
        self.audit.record("ME_READ", user, "User", user["id"], {})
        return user

    def list_users(self) -> list[dict]:
        return [{"key": key, **user} for key, user in self.raw["users"].items()]

    def list_customers(self, user_key: str) -> list[dict]:
        user = self.user(user_key)
        visible = []
        for customer in self.ontology.customers():
            if self.policy.can_read_object(user, customer):
                visible.append(self.policy.mask_object(user, customer))
        return visible

    def list_orders(self, user_key: str) -> list[dict]:
        user = self.user(user_key)
        visible = []
        for order in self.ontology.orders():
            if self.policy.can_read_object(user, order):
                visible.append(self.policy.mask_object(user, order))
        return visible

    def order_context(
        self, order_id: str, user_key: str = "analyst", customer_id: str | None = None
    ) -> dict:
        user = self.user(user_key)
        context = self.ontology.get_order_context(order_id, customer_id)
        self.policy.assert_can_read_object(user, context["order"])
        masked = {
            "order": self.policy.mask_object(user, context["order"]),
            "customer": self.policy.mask_object(user, context["customer"]),
            "products": [self.policy.mask_object(user, product) for product in context["products"]],
        }
        masked["available_actions"] = self.policy.available_actions(
            user, context["order"], context["customer"]
        )
        self.audit.record(
            "OBJECT_CONTEXT_READ", user, "Order", order_id, {"customer_id": context["customer"]["id"]}
        )
        return masked

    def ask_rag(self, question: str, user_key: str = "analyst") -> dict:
        """온톨로지 컨텍스트 없이 업로드된 PDF 문서만으로 답변."""
        from time import perf_counter as _pc
        started = _pc()
        user = self.user(user_key)
        steps: list[dict] = []

        vec_results = self._step(steps, "Vector Search에서 PDF 청크 검색", lambda: self._vector_hits(question, k=5))
        if not vec_results:
            raise AppError("DOCUMENT_NOT_FOUND", "업로드된 PDF 문서가 없거나 관련 내용을 찾지 못했습니다.", 404)

        doc_context_text = "\n\n".join(
            f"[{i+1}] 출처: {r['document']['title']}\n{r['document']['text']}"
            for i, r in enumerate(vec_results)
        )
        prompt = (
            "You are a document Q&A assistant.\n"
            "Answer ONLY from the provided document excerpts below. Reply in Korean.\n\n"
            f"Question:\n{question}\n\n"
            f"Document excerpts:\n{doc_context_text}\n\n"
            "Answer format:\n- 답변:\n- 근거 문서:\n- 추가 필요 정보 (없으면 '없음'):"
        )

        llm_result = self._step(
            steps,
            f"LLM Gateway 호출 ({self.llm.provider})",
            lambda: self.llm.generate(prompt, {}, vec_results, []),
        )
        latency_ms = round((_pc() - started) * 1000)
        self.audit.record("RAG_ASK_COMPLETED", user, "Document", "-", {
            "question": question, "chunk_count": len(vec_results), "latency_ms": latency_ms,
        })
        return {
            "answer": llm_result["answer"],
            "llm_provider": llm_result.get("provider"),
            "llm_model": llm_result.get("model"),
            "warning": llm_result.get("warning"),
            "evidence": self._present_search_results(vec_results),
            "steps": steps,
            "latency_ms": latency_ms,
        }

    def search_documents(self, query: str, user_key: str = "analyst", top_k: int = 3) -> dict:
        user = self.user(user_key)
        results = self.search.search(query, user, top_k)
        self.audit.record(
            "DOCUMENT_SEARCHED", user, "Document", "-", {"query": query, "count": len(results)}
        )
        return {"query": query, "results": self._present_search_results(results)}

    def ask(self, question: str, user_key: str = "analyst") -> dict:
        started = perf_counter()
        user = self.user(user_key)
        steps: list[dict] = []
        detected_ids: list[str] = []
        primary_id: str | None = None
        primary_type: str | None = None
        try:
            schema = self.ontology.schema
            object_ids = self._step(
                steps,
                "질문에서 객체 후보 추출",
                lambda: extract_object_ids(question, schema),
            )
            detected_ids = [v for v in object_ids.values() if v]

            # 우선순위: order_id → 다른 객체 순으로 첫 번째 감지된 ID 사용
            primary_id = object_ids.get("order_id") or next(
                (v for v in object_ids.values() if v), None
            )
            if primary_id is None:
                raise AppError("OBJECT_NOT_FOUND", "질문에서 객체 ID를 찾을 수 없습니다.", 404)

            # Order 중심 질문은 기존 get_order_context 경로 (customer_id 교차 검증 포함)
            if object_ids.get("order_id"):
                primary_type = "Order"
                customer_id = object_ids.get("customer_id")
                context = self._step(
                    steps,
                    "Ontology Service에서 객체와 관계 조회",
                    lambda: self.ontology.get_order_context(primary_id, customer_id),
                )
                self._step(
                    steps,
                    "Policy Engine에서 객체 접근 권한 확인",
                    lambda: self.policy.assert_can_read_object(user, context["order"]),
                )
                available_actions = self._step(
                    steps,
                    "Policy Engine에서 액션 권한 확인",
                    lambda: self.policy.available_actions(user, context["order"], context["customer"]),
                )
                masked_context = {
                    "order": self.policy.mask_object(user, context["order"]),
                    "customer": self.policy.mask_object(user, context["customer"]),
                    "products": [self.policy.mask_object(user, p) for p in context["products"]],
                }
                primary_object_id = context["order"]["id"]
            else:
                # 범용 객체 컨텍스트 (Customer/Product/기타)
                raw_ctx = self._step(
                    steps,
                    "Ontology Service에서 객체와 관계 조회",
                    lambda: self.ontology.object_context(primary_id),
                )
                primary_type = raw_ctx["object_type"]
                primary_object_id = raw_ctx["object"]["id"]
                self._step(
                    steps,
                    "Policy Engine에서 객체 접근 권한 확인",
                    lambda: self.policy.assert_can_read_object(user, raw_ctx["object"]),
                )
                masked_obj = self.policy.mask_object(user, raw_ctx["object"])
                available_actions = self._step(
                    steps,
                    "Policy Engine에서 액션 권한 확인",
                    lambda: self.policy.available_actions(user, raw_ctx["object"], {}),
                )
                context = raw_ctx
                masked_context = {
                    "object": masked_obj,
                    "object_type": primary_type,
                    "outgoing": raw_ctx["outgoing"],
                    "incoming": raw_ctx["incoming"],
                }

            search_query = self._step(
                steps, "RAG Service에서 검색 질의 강화", lambda: self.rag.build_search_query(question, masked_context)
            )
            search_results = self._step(
                steps, "Search Service에서 권한 필터링 문서 검색", lambda: self.search.search(search_query, user, 3)
            )
            vec_results = self._step(
                steps, "Vector Search에서 PDF 청크 검색", lambda: self._vector_hits(search_query)
            )
            search_results = search_results + vec_results
            prompt = self._step(
                steps, "RAG Service에서 프롬프트 생성", lambda: self.rag.build_prompt(question, masked_context, search_results)
            )
            llm_result = self._step(
                steps,
                f"LLM Gateway 호출 ({self.llm.provider})",
                lambda: self.llm.generate(prompt, masked_context, search_results, available_actions),
            )
            latency_ms = round((perf_counter() - started) * 1000)
            log = {
                "question": question,
                "detected_objects": detected_ids,
                "search_query": search_query,
                "retrieved_documents": [item["document"]["id"] for item in search_results],
                "answer_status": "ANSWERED",
                "latency_ms": latency_ms,
                "llm_provider": llm_result.get("provider"),
            }
            self.audit.record("ASK_COMPLETED", user, primary_type or "Object", primary_object_id, log)
            return {
                "answer": llm_result["answer"],
                "llm_provider": llm_result.get("provider"),
                "llm_model": llm_result.get("model"),
                "warning": llm_result.get("warning"),
                "detected_objects": detected_ids,
                "ontology_context": masked_context,
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
                primary_type or "Object",
                primary_id or "-",
                {
                    "question": question,
                    "detected_objects": detected_ids,
                    "error_code": error.code,
                    "latency_ms": round((perf_counter() - started) * 1000),
                },
            )
            raise

    # ── hybrid ask ────────────────────────────────────────────────────────

    def ask_hybrid(self, question: str, user_key: str = "analyst", doc_ids: list[str] | None = None) -> dict:
        """질문 유형을 분류한 뒤 온톨로지 + RAG를 혼합해 답변."""
        from time import perf_counter as _pc
        from . import query_classifier, ontology_query_engine
        started = _pc()
        user = self.user(user_key)
        steps: list[dict] = []

        # 1. 질문 유형 분류
        classification = self._step(steps, "질문 유형 분류 (LLM)", lambda: query_classifier.classify(question))
        q_type = classification.get("type", "descriptive")

        ontology_result: dict = {}
        rag_evidence: list[dict] = []

        # 2. 온톨로지 구조형 처리
        if q_type in ("filter", "compare", "calculate", "hybrid"):
            def _run_ontology():
                entities = classification.get("entities") or []
                entity_type = classification.get("entity_type") or ""
                operation = classification.get("operation") or "list"
                prop_key = classification.get("property_key")
                prop_val = classification.get("property_value")

                if q_type == "filter" and entity_type and prop_key:
                    rows = ontology_query_engine.filter_by_property(
                        entity_type, prop_key, prop_val or "", doc_ids
                    )
                    return {"mode": "filter", "entity_type": entity_type, "rows": rows, "property_key": prop_key, "property_value": prop_val}
                elif q_type == "compare" and entities:
                    table = ontology_query_engine.compare_entities(entities, doc_ids)
                    return {"mode": "compare", "table": table}
                elif q_type == "calculate" and entities:
                    calc = ontology_query_engine.calculate(entities, operation, doc_ids)
                    return {"mode": "calculate", "calc": calc}
                elif q_type == "filter" and entity_type:
                    hint = (prop_val or prop_key or entities[0] if entities else "")
                    rows = ontology_query_engine.find_by_category(entity_type, hint, doc_ids)
                    return {"mode": "filter", "entity_type": entity_type, "rows": rows}
                else:
                    # hybrid 또는 분류 결과 불충분 → 관계 검색
                    if entities:
                        rels = ontology_query_engine.search_relations(entities[0], None, doc_ids)
                        return {"mode": "relations", "entity": entities[0], "rows": rels}
                    return {"mode": "none", "rows": []}

            ontology_result = self._step(steps, "온톨로지 구조형 질의", _run_ontology)

        # 3. RAG 처리 (descriptive, hybrid)
        if q_type in ("descriptive", "hybrid"):
            vec_results = self._step(
                steps, "Vector Search에서 PDF 청크 검색", lambda: self._vector_hits(question, k=5)
            )
            if vec_results:
                rag_evidence = self._present_search_results(vec_results)

        # 4. LLM 최종 답변 생성
        def _build_final_prompt() -> str:
            parts = [
                f"사용자 질문: {question}\n",
                f"질문 유형: {q_type}\n",
            ]
            if ontology_result.get("rows") or ontology_result.get("table") or ontology_result.get("calc"):
                parts.append("## 온톨로지에서 추출한 구조형 데이터\n")
                import json as _json
                parts.append(_json.dumps(ontology_result, ensure_ascii=False, indent=2) + "\n")
            if rag_evidence:
                parts.append("\n## 문서 검색 결과 (관련 PDF 청크)\n")
                for i, ev in enumerate(rag_evidence[:3]):
                    parts.append(f"[{i+1}] {ev['title']}\n{ev['text'][:600]}\n")
            parts.append(
                "\n위 데이터를 바탕으로 사용자의 질문에 한국어로 명확하게 답변하세요.\n"
                "구조형 데이터가 있으면 표나 목록으로 먼저 제시하고, 이후 서술형 설명을 덧붙이세요.\n"
                "모르면 모른다고 하고 추측하지 마세요."
            )
            return "".join(parts)

        prompt = self._step(steps, "최종 답변 프롬프트 생성", _build_final_prompt)
        llm_result = self._step(
            steps,
            f"LLM Gateway 호출 ({self.llm.provider})",
            lambda: self.llm.generate_text(prompt),
        )

        latency_ms = round((_pc() - started) * 1000)
        self.audit.record("HYBRID_ASK_COMPLETED", user, "HybridQuery", "-", {
            "question": question, "q_type": q_type, "latency_ms": latency_ms,
        })
        return {
            "answer": llm_result["answer"],
            "llm_provider": llm_result.get("provider"),
            "llm_model": llm_result.get("model"),
            "warning": llm_result.get("warning"),
            "query_type": q_type,
            "classification": classification,
            "ontology_result": ontology_result,
            "evidence": rag_evidence,
            "steps": steps,
            "latency_ms": latency_ms,
        }

    # ── document upload helpers ────────────────────────────────────────────

    def upload_document(self, file_bytes: bytes, filename: str) -> dict:
        from .vector_search import UPLOAD_DIR
        dest = UPLOAD_DIR / filename
        dest.write_bytes(file_bytes)
        return self.vector_search.ingest(dest, filename)

    def list_uploaded_documents(self) -> list[dict]:
        return self.vector_search.list_documents()

    def delete_uploaded_document(self, doc_id: str) -> bool:
        return self.vector_search.delete(doc_id)

    def _vector_hits(self, query: str, k: int = 3) -> list[dict]:
        """벡터 검색 결과를 BM25 결과와 동일한 형식으로 변환."""
        chunks = self.vector_search.search(query, k=k)
        return [
            {
                "document": {
                    "id": f"vec-{c['doc_id']}-p{c['page']}",
                    "title": f"[PDF] {c['filename']} (p.{c['page'] + 1})",
                    "text": c["text"],
                    "related_objects": [],
                },
                "score": max(0.0, 1.0 - c["score"]),
            }
            for c in chunks
        ]

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
        with span(f"ask.{_slug(name)}"):
            value = fn()
        steps.append({"name": name, "status": "ok"})
        return value


def _slug(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_")[:64]
