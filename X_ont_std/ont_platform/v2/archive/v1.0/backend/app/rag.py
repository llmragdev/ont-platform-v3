from __future__ import annotations

import re


def extract_object_ids(question: str, schema: dict | None = None) -> dict[str, str | None]:
    """질문 텍스트에서 객체 ID를 추출한다.

    schema가 주어지면 ontology.default.json의 id_prefix를 읽어 동적 정규식을 생성한다.
    schema가 없으면 하위호환 고정 정규식(C/O prefix)을 사용한다.
    """
    upper = question.upper()
    result: dict[str, str | None] = {}

    if schema is not None:
        for type_def in schema.get("object_types", []):
            prefix = type_def.get("id_prefix")
            if not prefix:
                continue
            type_name = type_def["name"]
            key = f"{type_name.lower()}_id"
            match = re.search(rf"\b{re.escape(prefix.upper())}\d{{3}}\b", upper)
            result[key] = match.group(0) if match else None
    else:
        customer_match = re.search(r"\bC\d{3}\b", upper)
        order_match = re.search(r"\bO\d{3}\b", upper)
        result = {
            "customer_id": customer_match.group(0) if customer_match else None,
            "order_id": order_match.group(0) if order_match else None,
        }

    return result


class RAGService:
    """온톨로지 컨텍스트와 검색 결과를 LLM 프롬프트로 결합한다."""

    def build_search_query(self, question: str, context: dict) -> str:
        customer = context.get("customer", {})
        order = context.get("order", {})
        products = context.get("products", [])
        product_names = " ".join(p.get("name", "") for p in products)
        parts = [question]
        if customer.get("segment"):
            parts.append(customer["segment"])
        if customer.get("risk_tier"):
            parts.append(customer["risk_tier"])
        if order.get("status"):
            parts.append(order["status"])
        if order.get("amount"):
            parts.append(str(order["amount"]))
        if product_names:
            parts.append(product_names)
        parts.append("approval contract policy risk support finance")
        return " ".join(parts)

    def build_prompt(self, question: str, context: dict, search_results: list[dict]) -> str:
        document_context = "\n\n".join(
            f"Document: {item['document']['title']}\nScore: {item['score']}\nText: {item['document']['text']}"
            for item in search_results
        )

        # Order+Customer+Product 중심 컨텍스트 (기존 호환)
        if "order" in context and "customer" in context:
            products = context.get("products", [])
            products_text = "\n".join(
                f"- {p.get('name', p.get('id', '?'))} ({p.get('category', '')})" for p in products
            )
            ontology_context = f"""
Customer:
- id: {context['customer'].get('id', '-')}
- name: {context['customer'].get('name', '-')}
- segment: {context['customer'].get('segment', '-')}
- region: {context['customer'].get('region', '-')}
- risk_tier: {context['customer'].get('risk_tier', '-')}

Order:
- id: {context['order'].get('id', '-')}
- status: {context['order'].get('status', '-')}
- amount: {context['order'].get('amount', '-')}
- products:
{products_text}
""".strip()
        else:
            # 범용 객체 컨텍스트
            obj = context.get("object", context)
            obj_type = context.get("object_type", obj.get("type", "Object"))
            obj_lines = "\n".join(f"- {k}: {v}" for k, v in obj.items() if k not in ("type",))
            outgoing_text = ""
            for rel in context.get("outgoing", []):
                target = rel.get("target", {})
                outgoing_text += f"\n  [{rel.get('display_name', rel['relationship_type'])}] → {rel['target_id']} ({target.get('type', '')})"
            incoming_text = ""
            for rel in context.get("incoming", []):
                source = rel.get("source", {})
                incoming_text += f"\n  [{rel.get('reverse_display_name', rel['relationship_type'])}] ← {rel['source_id']} ({source.get('type', '')})"
            ontology_context = f"""
{obj_type}:
{obj_lines}
Outgoing relationships:{outgoing_text or ' (없음)'}
Incoming relationships:{incoming_text or ' (없음)'}
""".strip()

        return f"""
You are an order approval assistant.
Answer only from the provided ontology context and document context.
If the evidence is insufficient, say what is missing. Reply in Korean.

Question:
{question}

Ontology Context:
{ontology_context}

Document Context:
{document_context}

Answer format:
- Decision (승인/반려/추가검토):
- Evidence (근거):
- Required follow-up (후속 조치):
""".strip()
