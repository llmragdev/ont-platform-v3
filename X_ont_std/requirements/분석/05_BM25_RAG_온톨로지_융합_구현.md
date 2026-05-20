# BM25, RAG, 온톨로지 융합 구현

## 1. 목표

이 문서는 BM25 검색, RAG, 객체기반 온톨로지를 하나의 흐름으로 연결하는 방법을 직접 구현합니다.

핵심 목표는 다음 질문에 답하는 것입니다.

```text
C001 고객의 O001 주문을 승인해도 될까?
```

이 질문을 처리하려면 단순 문서 검색만으로는 부족합니다.

- `C001`이 어떤 고객인지 알아야 합니다.
- `O001`이 어떤 주문인지 알아야 합니다.
- 주문과 고객의 관계가 맞는지 확인해야 합니다.
- 관련 계약, 정책, 지원 문서를 검색해야 합니다.
- 객체 정보와 문서 근거를 함께 사용해 답변해야 합니다.

## 2. 왜 세 가지를 융합하는가

| 요소 | 역할 |
| --- | --- |
| BM25 | 키워드 기반 문서 검색 |
| RAG | 검색된 문서를 답변 생성 컨텍스트로 사용 |
| 온톨로지 | 고객, 주문, 제품 같은 업무 객체와 관계 제공 |

BM25는 단어 일치에 강하고, 온톨로지는 구조화된 업무 맥락에 강합니다. RAG는 두 컨텍스트를 합쳐 자연어 답변을 만들 수 있습니다.

좋은 구조는 다음과 같습니다.

```text
사용자 질문
  -> 객체 식별
  -> 온톨로지 조회
  -> BM25 문서 검색
  -> 객체 컨텍스트 + 문서 컨텍스트 결합
  -> RAG 프롬프트 생성
  -> 답변 생성
```

## 3. 예제 시나리오

업무 도메인은 고객 주문 승인입니다.

객체:

- Customer
- Order
- Product

문서:

- 고객 계약 조건
- 주문 승인 정책
- 지원 정책
- 리스크 관리 가이드

질문:

```text
C001 고객의 O001 주문을 승인해도 될까?
```

기대 답변:

```text
승인 가능성이 높습니다.
O001 주문은 C001 고객의 주문이며 금액은 3200입니다.
정책 문서에 따르면 5000 미만 주문은 담당자 승인으로 처리할 수 있습니다.
단, Enterprise 고객은 계약 조건을 확인해야 하며 C001의 계약 문서에는 표준 지원 조건이 적용됩니다.
```

## 4. 예제 데이터

```python
customers = {
    "C001": {
        "type": "Customer",
        "name": "Alpha Manufacturing",
        "segment": "Enterprise",
        "region": "Seoul",
        "risk_tier": "Low",
    },
    "C002": {
        "type": "Customer",
        "name": "Beta Retail",
        "segment": "SMB",
        "region": "Busan",
        "risk_tier": "Medium",
    },
}

orders = {
    "O001": {
        "type": "Order",
        "customer_id": "C001",
        "status": "Submitted",
        "amount": 3200.0,
        "product_ids": ["P001", "P003"],
    },
    "O002": {
        "type": "Order",
        "customer_id": "C002",
        "status": "Submitted",
        "amount": 8200.0,
        "product_ids": ["P002"],
    },
}

products = {
    "P001": {
        "type": "Product",
        "name": "Industrial Sensor",
        "category": "Hardware",
    },
    "P002": {
        "type": "Product",
        "name": "Analytics License",
        "category": "Software",
    },
    "P003": {
        "type": "Product",
        "name": "Support Package",
        "category": "Service",
    },
}
```

## 5. 문서 데이터

```python
documents = [
    {
        "id": "D001",
        "title": "Order Approval Policy",
        "text": (
            "Orders below 5000 can be approved by the account manager. "
            "Orders equal to or above 5000 require finance manager approval."
        ),
    },
    {
        "id": "D002",
        "title": "Enterprise Customer Contract Policy",
        "text": (
            "Enterprise customers require contract validation before fulfillment. "
            "Standard support terms apply unless a custom contract is registered."
        ),
    },
    {
        "id": "D003",
        "title": "Risk Review Guideline",
        "text": (
            "Low risk customers can proceed through normal approval. "
            "Medium or high risk customers require additional review."
        ),
    },
    {
        "id": "D004",
        "title": "Support Package Policy",
        "text": (
            "Support packages can be included in approved orders. "
            "Premium support requires service manager confirmation."
        ),
    },
]
```

## 6. 간단한 온톨로지 저장소 구현

```python
class OntologyStore:
    def __init__(
        self,
        customers: dict,
        orders: dict,
        products: dict,
    ) -> None:
        self.customers = customers
        self.orders = orders
        self.products = products

    def get_customer(self, customer_id: str) -> dict | None:
        return self.customers.get(customer_id)

    def get_order(self, order_id: str) -> dict | None:
        return self.orders.get(order_id)

    def get_product(self, product_id: str) -> dict | None:
        return self.products.get(product_id)

    def get_order_context(self, order_id: str) -> dict:
        order = self.get_order(order_id)

        if order is None:
            raise ValueError(f"Unknown order: {order_id}")

        customer = self.get_customer(order["customer_id"])
        products = [
            self.get_product(product_id)
            for product_id in order["product_ids"]
        ]

        return {
            "order": order,
            "customer": customer,
            "products": products,
        }
```

온톨로지 저장소는 단순 조회를 넘어서 객체 간 관계를 따라 컨텍스트를 구성합니다.

## 7. BM25 검색기 구현

실습에서는 외부 라이브러리 없이 간단한 BM25 검색기를 구현합니다.

```python
import math
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


class BM25Search:
    def __init__(
        self,
        documents: list[dict],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(doc["text"]) for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        self.term_frequencies = [Counter(tokens) for tokens in self.doc_tokens]
        self.document_frequency = self._build_document_frequency()

    def _build_document_frequency(self) -> Counter:
        document_frequency = Counter()

        for tokens in self.doc_tokens:
            for token in set(tokens):
                document_frequency[token] += 1

        return document_frequency

    def _idf(self, term: str) -> float:
        total_docs = len(self.documents)
        doc_freq = self.document_frequency.get(term, 0)

        return math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def _score_document(self, query_terms: list[str], index: int) -> float:
        score = 0.0
        term_frequency = self.term_frequencies[index]
        doc_length = self.doc_lengths[index]

        for term in query_terms:
            frequency = term_frequency.get(term, 0)

            if frequency == 0:
                continue

            numerator = frequency * (self.k1 + 1)
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * doc_length / self.avg_doc_length
            )
            score += self._idf(term) * numerator / denominator

        return score

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        query_terms = tokenize(query)
        scored_documents = []

        for index, document in enumerate(self.documents):
            score = self._score_document(query_terms, index)
            scored_documents.append(
                {
                    "score": score,
                    "document": document,
                }
            )

        return sorted(
            scored_documents,
            key=lambda item: item["score"],
            reverse=True,
        )[:top_k]
```

## 8. 질문에서 객체 식별

질문에서 고객 ID와 주문 ID를 찾아냅니다. 실제 시스템에서는 NER, LLM, 정규식, 검색 후보 매칭을 함께 사용할 수 있습니다.

```python
def extract_object_ids(question: str) -> dict[str, str | None]:
    customer_match = re.search(r"\bC\d{3}\b", question)
    order_match = re.search(r"\bO\d{3}\b", question)

    return {
        "customer_id": customer_match.group(0) if customer_match else None,
        "order_id": order_match.group(0) if order_match else None,
    }
```

## 9. 온톨로지 컨텍스트 구성

```python
def build_ontology_context(
    store: OntologyStore,
    question: str,
) -> dict:
    object_ids = extract_object_ids(question)

    if object_ids["order_id"] is None:
        raise ValueError("Question does not include an order id")

    context = store.get_order_context(object_ids["order_id"])

    if (
        object_ids["customer_id"] is not None
        and context["order"]["customer_id"] != object_ids["customer_id"]
    ):
        raise ValueError("The requested customer does not own this order")

    return context
```

이 단계에서 온톨로지는 중요한 검증을 수행합니다. 질문에 등장한 고객과 주문의 관계가 실제로 맞는지 확인합니다.

## 10. 검색 질의 강화

온톨로지에서 얻은 객체 정보를 사용해 BM25 검색 질의를 강화합니다.

```python
def build_search_query(
    question: str,
    ontology_context: dict,
) -> str:
    customer = ontology_context["customer"]
    order = ontology_context["order"]
    products = ontology_context["products"]
    product_names = " ".join(product["name"] for product in products)

    return " ".join(
        [
            question,
            customer["segment"],
            customer["risk_tier"],
            order["status"],
            str(order["amount"]),
            product_names,
            "approval contract policy risk support",
        ]
    )
```

단순히 사용자 질문만 검색하는 것보다 객체 정보를 추가하면 관련 문서를 더 잘 찾을 수 있습니다.

## 11. RAG 컨텍스트 생성

```python
def format_ontology_context(context: dict) -> str:
    customer = context["customer"]
    order = context["order"]
    products = context["products"]

    product_lines = [
        f"- {product['name']} ({product['category']})"
        for product in products
    ]

    return f"""
Customer:
- name: {customer["name"]}
- segment: {customer["segment"]}
- region: {customer["region"]}
- risk_tier: {customer["risk_tier"]}

Order:
- status: {order["status"]}
- amount: {order["amount"]}
- products:
{chr(10).join(product_lines)}
""".strip()


def format_document_context(search_results: list[dict]) -> str:
    chunks = []

    for result in search_results:
        document = result["document"]
        chunks.append(
            f"""
Document: {document["title"]}
Score: {result["score"]:.4f}
Text: {document["text"]}
""".strip()
        )

    return "\n\n".join(chunks)
```

## 12. RAG 프롬프트 생성

```python
def build_rag_prompt(
    question: str,
    ontology_context_text: str,
    document_context_text: str,
) -> str:
    return f"""
You are an order approval assistant.
Answer only from the provided ontology context and document context.
If the evidence is insufficient, say what is missing.

Question:
{question}

Ontology Context:
{ontology_context_text}

Document Context:
{document_context_text}

Answer format:
- Decision:
- Evidence:
- Required follow-up:
""".strip()
```

이 프롬프트는 LLM API에 전달할 수 있습니다. 실습에서는 LLM 호출 대신 규칙 기반 답변 생성기를 만들어 전체 흐름을 확인합니다.

## 13. 규칙 기반 답변 생성

```python
def generate_rule_based_answer(context: dict) -> str:
    customer = context["customer"]
    order = context["order"]

    if order["status"] != "Submitted":
        return "Decision: Not ready\nEvidence: Order is not in Submitted status."

    if customer["risk_tier"] != "Low":
        return (
            "Decision: Additional review required\n"
            f"Evidence: Customer risk tier is {customer['risk_tier']}."
        )

    if order["amount"] >= 5000:
        return (
            "Decision: Finance manager approval required\n"
            "Evidence: Order amount is equal to or above 5000."
        )

    return (
        "Decision: Approval is likely allowed\n"
        "Evidence: Order is Submitted, customer risk is Low, "
        "and order amount is below 5000.\n"
        "Required follow-up: Validate enterprise contract terms before fulfillment."
    )
```

## 14. 전체 실행 코드

```python
question = "C001 고객의 O001 주문을 승인해도 될까?"

store = OntologyStore(customers, orders, products)
search = BM25Search(documents)

ontology_context = build_ontology_context(store, question)
search_query = build_search_query(question, ontology_context)
search_results = search.search(search_query, top_k=3)

ontology_context_text = format_ontology_context(ontology_context)
document_context_text = format_document_context(search_results)
prompt = build_rag_prompt(
    question,
    ontology_context_text,
    document_context_text,
)

print("=== Search Query ===")
print(search_query)

print("\n=== Ontology Context ===")
print(ontology_context_text)

print("\n=== Document Context ===")
print(document_context_text)

print("\n=== RAG Prompt ===")
print(prompt)

print("\n=== Rule-Based Answer ===")
print(generate_rule_based_answer(ontology_context))
```

## 15. LLM 연결 지점

실제 LLM을 붙일 때는 `prompt`를 모델 호출에 전달하면 됩니다.

```python
def call_llm(prompt: str) -> str:
    raise NotImplementedError("Connect your LLM provider here")


answer = call_llm(prompt)
print(answer)
```

중요한 것은 LLM이 모든 것을 추론하게 두지 않는 것입니다. 온톨로지 조회, 관계 검증, 문서 검색은 LLM 호출 전에 결정적으로 처리하는 것이 좋습니다.

## 16. 융합 패턴 정리

| 패턴 | 설명 |
| --- | --- |
| 객체 우선 검색 | 질문에서 객체를 찾고 객체 정보로 검색 질의를 강화 |
| 검색 후 객체 연결 | 검색된 문서의 고객명, 주문번호, 제품명을 객체와 연결 |
| 규칙 + RAG | 결정적 규칙은 코드로 처리하고 설명은 RAG로 생성 |
| 관계 검증 | 질문 속 객체들이 실제 관계를 가지는지 확인 |
| 액션 연결 | 답변 이후 승인, 반려, 보류 같은 워크플로우 액션 실행 |

## 17. 화면으로 확장할 때의 구성

화면에서는 다음 영역을 나누면 좋습니다.

- 질문 입력
- 식별된 객체
- 온톨로지 컨텍스트
- 검색된 문서
- 생성된 프롬프트
- 최종 답변
- 실행 가능한 워크플로우 액션

이 구성을 사용하면 사용자는 AI 답변만 보는 것이 아니라, 답변이 어떤 객체와 문서 근거에서 나왔는지 확인할 수 있습니다.

## 18. 확장 과제

다음 기능을 추가해 볼 수 있습니다.

- 한국어 형태소 분석 기반 BM25
- 벡터 검색과 BM25 하이브리드 검색
- 문서 청크 분할
- 객체별 문서 접근 권한
- 답변 근거 문장 하이라이트
- 워크플로우 액션 실행
- Snowflake Cortex Search 또는 Elasticsearch 연결
- Next.js 화면 구현

## 19. 요약

BM25, RAG, 온톨로지를 융합하면 단순 질의응답보다 훨씬 업무적인 AI 시스템을 만들 수 있습니다. BM25는 문서를 찾고, 온톨로지는 객체와 관계를 검증하며, RAG는 두 컨텍스트를 결합해 설명 가능한 답변을 생성합니다.

