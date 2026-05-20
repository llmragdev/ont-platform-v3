from __future__ import annotations

import re

from .errors import AppError


def extract_object_ids(question: str) -> dict[str, str | None]:
    customer_match = re.search(r"\bC\d{3}\b", question.upper())
    order_match = re.search(r"\bO\d{3}\b", question.upper())
    return {
        "customer_id": customer_match.group(0) if customer_match else None,
        "order_id": order_match.group(0) if order_match else None,
    }


class RAGService:
    def build_search_query(self, question: str, context: dict) -> str:
        customer = context["customer"]
        order = context["order"]
        product_names = " ".join(product["name"] for product in context["products"])
        return " ".join(
            [
                question,
                customer["segment"],
                customer["risk_tier"],
                order["status"],
                str(order["amount"]),
                product_names,
                "approval contract policy risk support finance",
            ]
        )

    def build_prompt(self, question: str, context: dict, search_results: list[dict]) -> str:
        document_context = "\n\n".join(
            f"Document: {item['document']['title']}\nScore: {item['score']}\nText: {item['document']['text']}"
            for item in search_results
        )
        products = "\n".join(f"- {product['name']} ({product['category']})" for product in context["products"])
        ontology_context = f"""
Customer:
- id: {context['customer']['id']}
- name: {context['customer']['name']}
- segment: {context['customer']['segment']}
- region: {context['customer']['region']}
- risk_tier: {context['customer']['risk_tier']}

Order:
- id: {context['order']['id']}
- status: {context['order']['status']}
- amount: {context['order']['amount']}
- products:
{products}
""".strip()
        return f"""
You are an order approval assistant.
Answer only from the provided ontology context and document context.
If the evidence is insufficient, say what is missing.

Question:
{question}

Ontology Context:
{ontology_context}

Document Context:
{document_context}

Answer format:
- Decision:
- Evidence:
- Required follow-up:
""".strip()


class LLMGateway:
    def generate_rule_based_answer(self, context: dict, search_results: list[dict], available_actions: list[str]) -> str:
        if not search_results:
            raise AppError("DOCUMENT_NOT_FOUND", "답변에 필요한 근거 문서를 찾지 못했습니다.", 404)
        customer = context["customer"]
        order = context["order"]
        if order["status"] not in ["Submitted", "Review"]:
            decision = "Not ready"
            evidence = f"Order status is {order['status']}."
        elif customer["risk_tier"] == "High":
            decision = "Additional review required"
            evidence = "Customer risk tier is High."
        elif order["amount"] >= 5000:
            decision = "Finance manager approval required"
            evidence = "Order amount is equal to or above 5000."
        else:
            decision = "Approval is likely allowed"
            evidence = "Order is Submitted, customer risk is Low, and amount is below 5000."

        action_text = ", ".join(available_actions) if available_actions else "No executable action for current user."
        docs = ", ".join(item["document"]["title"] for item in search_results)
        return (
            f"Decision: {decision}\n"
            f"Evidence: {evidence} Retrieved documents: {docs}.\n"
            f"Required follow-up: Enterprise customers should validate contract terms before fulfillment.\n"
            f"Available actions: {action_text}"
        )

