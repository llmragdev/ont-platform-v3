# Next.js 온톨로지 AI 업무화면 구현

## 1. 목표

이 문서는 Next.js로 온톨로지 AI 업무화면의 MVP를 구현하는 핸즈온입니다.

구현할 화면은 다음과 같습니다.

- 대시보드
- 객체 탐색
- AI 질의
- 승인 워크플로우
- 우측 컨텍스트 패널

초기 버전은 목 데이터를 사용합니다. 이후 BM25, RAG, 워크플로우 API와 연결할 수 있도록 구조를 잡습니다.

## 2. 프로젝트 생성

```bash
npx create-next-app@latest ontology-ai-ui
```

권장 선택:

```text
TypeScript: Yes
ESLint: Yes
Tailwind CSS: Yes
src directory: Yes
App Router: Yes
Turbopack: Yes
Import alias: Yes
```

프로젝트로 이동합니다.

```bash
cd ontology-ai-ui
npm run dev
```

브라우저에서 확인합니다.

```text
http://localhost:3000
```

## 3. 추천 폴더 구조

```text
src/
  app/
    page.tsx
    globals.css
  components/
    app-shell.tsx
    sidebar.tsx
    topbar.tsx
    dashboard.tsx
    object-explorer.tsx
    ai-ask.tsx
    workflow-board.tsx
    context-panel.tsx
  lib/
    mock-data.ts
    ontology.ts
    rag.ts
    workflow.ts
  types/
    ontology.ts
```

핸즈온에서는 한 파일에 모두 작성해도 되지만, 교육 자료에서는 위처럼 나누는 것이 이해하기 좋습니다.

## 4. 타입 정의

`src/types/ontology.ts`

```typescript
export type RiskTier = "Low" | "Medium" | "High";
export type OrderStatus = "Submitted" | "Approved" | "Rejected" | "Fulfilled" | "Closed";

export type Customer = {
  id: string;
  name: string;
  segment: string;
  region: string;
  riskTier: RiskTier;
};

export type Product = {
  id: string;
  name: string;
  category: string;
};

export type Order = {
  id: string;
  customerId: string;
  status: OrderStatus;
  amount: number;
  productIds: string[];
};

export type KnowledgeDocument = {
  id: string;
  title: string;
  text: string;
  score?: number;
};

export type WorkflowEvent = {
  id: string;
  objectId: string;
  action: string;
  fromStatus: string;
  toStatus: string;
  actor: string;
  occurredAt: string;
};
```

## 5. 목 데이터

`src/lib/mock-data.ts`

```typescript
import type { Customer, KnowledgeDocument, Order, Product, WorkflowEvent } from "@/types/ontology";

export const customers: Customer[] = [
  {
    id: "C001",
    name: "Alpha Manufacturing",
    segment: "Enterprise",
    region: "Seoul",
    riskTier: "Low",
  },
  {
    id: "C002",
    name: "Beta Retail",
    segment: "SMB",
    region: "Busan",
    riskTier: "Medium",
  },
];

export const products: Product[] = [
  { id: "P001", name: "Industrial Sensor", category: "Hardware" },
  { id: "P002", name: "Analytics License", category: "Software" },
  { id: "P003", name: "Support Package", category: "Service" },
];

export const orders: Order[] = [
  {
    id: "O001",
    customerId: "C001",
    status: "Submitted",
    amount: 3200,
    productIds: ["P001", "P003"],
  },
  {
    id: "O002",
    customerId: "C002",
    status: "Submitted",
    amount: 8200,
    productIds: ["P002"],
  },
];

export const documents: KnowledgeDocument[] = [
  {
    id: "D001",
    title: "Order Approval Policy",
    text: "Orders below 5000 can be approved by the account manager. Orders equal to or above 5000 require finance manager approval.",
  },
  {
    id: "D002",
    title: "Enterprise Customer Contract Policy",
    text: "Enterprise customers require contract validation before fulfillment. Standard support terms apply unless a custom contract is registered.",
  },
  {
    id: "D003",
    title: "Risk Review Guideline",
    text: "Low risk customers can proceed through normal approval. Medium or high risk customers require additional review.",
  },
];

export const workflowEvents: WorkflowEvent[] = [
  {
    id: "E001",
    objectId: "O003",
    action: "ApproveOrder",
    fromStatus: "Submitted",
    toStatus: "Approved",
    actor: "manager@example.com",
    occurredAt: "2026-05-07T09:10:00",
  },
];
```

## 6. 온톨로지 조회 함수

`src/lib/ontology.ts`

```typescript
import { customers, orders, products } from "@/lib/mock-data";

export function getOrderContext(orderId: string) {
  const order = orders.find((item) => item.id === orderId);

  if (!order) {
    return null;
  }

  const customer = customers.find((item) => item.id === order.customerId);
  const orderProducts = products.filter((item) => order.productIds.includes(item.id));

  return {
    order,
    customer,
    products: orderProducts,
  };
}
```

## 7. 간단한 검색 함수

`src/lib/rag.ts`

```typescript
import { documents } from "@/lib/mock-data";

function tokenize(text: string) {
  return text.toLowerCase().match(/[a-zA-Z0-9]+/g) ?? [];
}

export function searchDocuments(query: string) {
  const queryTerms = tokenize(query);

  return documents
    .map((document) => {
      const textTerms = tokenize(`${document.title} ${document.text}`);
      const score = queryTerms.reduce((total, term) => {
        return total + textTerms.filter((item) => item === term).length;
      }, 0);

      return {
        ...document,
        score,
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
}

export function answerQuestion(question: string) {
  const orderId = question.match(/\bO\d{3}\b/)?.[0] ?? "O001";
  const customerId = question.match(/\bC\d{3}\b/)?.[0] ?? null;

  return {
    orderId,
    customerId,
    answer:
      "승인 가능성이 높습니다. 주문은 Submitted 상태이고 금액은 5000 미만이며 고객 리스크가 낮습니다. 단, Enterprise 고객이므로 fulfillment 전 계약 조건 확인이 필요합니다.",
    evidence: searchDocuments(`${question} approval policy risk contract`),
  };
}
```

## 8. 워크플로우 함수

`src/lib/workflow.ts`

```typescript
import type { Order, OrderStatus } from "@/types/ontology";

export function getAvailableActions(order: Order) {
  if (order.status === "Submitted") {
    return ["ApproveOrder", "RejectOrder", "HoldOrder"];
  }

  if (order.status === "Approved") {
    return ["FulfillOrder"];
  }

  if (order.status === "Fulfilled") {
    return ["CloseOrder"];
  }

  return [];
}

export function getNextStatus(action: string): OrderStatus {
  const statusByAction: Record<string, OrderStatus> = {
    ApproveOrder: "Approved",
    RejectOrder: "Rejected",
    FulfillOrder: "Fulfilled",
    CloseOrder: "Closed",
    HoldOrder: "Submitted",
  };

  return statusByAction[action] ?? "Submitted";
}
```

## 9. 단일 페이지 MVP 구현

`src/app/page.tsx`

```tsx
"use client";

import { useMemo, useState } from "react";
import { customers, orders as initialOrders, workflowEvents } from "@/lib/mock-data";
import { answerQuestion } from "@/lib/rag";
import { getOrderContext } from "@/lib/ontology";
import { getAvailableActions, getNextStatus } from "@/lib/workflow";
import type { KnowledgeDocument, Order } from "@/types/ontology";

const menus = ["대시보드", "객체 탐색", "AI 질의", "승인 워크플로우"];

export default function Home() {
  const [activeMenu, setActiveMenu] = useState("대시보드");
  const [orders, setOrders] = useState<Order[]>(initialOrders);
  const [selectedOrderId, setSelectedOrderId] = useState("O001");
  const [question, setQuestion] = useState("C001 고객의 O001 주문을 승인해도 될까?");
  const [answer, setAnswer] = useState<string>("");
  const [evidence, setEvidence] = useState<KnowledgeDocument[]>([]);

  const selectedOrder = orders.find((order) => order.id === selectedOrderId) ?? orders[0];
  const selectedContext = useMemo(() => getOrderContext(selectedOrder.id), [selectedOrder.id]);
  const pendingOrders = orders.filter((order) => order.status === "Submitted");

  function ask() {
    const result = answerQuestion(question);
    setAnswer(result.answer);
    setEvidence(result.evidence);

    if (result.orderId) {
      setSelectedOrderId(result.orderId);
    }
  }

  function executeAction(action: string) {
    setOrders((currentOrders) =>
      currentOrders.map((order) =>
        order.id === selectedOrder.id
          ? { ...order, status: getNextStatus(action) }
          : order
      )
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <div className="grid min-h-screen grid-cols-[240px_1fr_340px]">
        <aside className="border-r border-slate-200 bg-white px-4 py-5">
          <div className="mb-8">
            <div className="text-lg font-semibold">Ontology Workbench</div>
            <div className="text-sm text-slate-500">AI 업무 의사결정</div>
          </div>
          <nav className="space-y-1">
            {menus.map((menu) => (
              <button
                key={menu}
                onClick={() => setActiveMenu(menu)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm ${
                  activeMenu === menu
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {menu}
              </button>
            ))}
          </nav>
        </aside>

        <section className="px-6 py-5">
          <header className="mb-5 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">{activeMenu}</h1>
              <p className="text-sm text-slate-500">객체, 문서, AI 답변, 워크플로우를 연결합니다.</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
              {selectedOrder.id} · {selectedOrder.status}
            </div>
          </header>

          {activeMenu === "대시보드" && (
            <div className="space-y-5">
              <div className="grid grid-cols-4 gap-3">
                <Metric label="승인 대기" value={pendingOrders.length.toString()} />
                <Metric label="고객 수" value={customers.length.toString()} />
                <Metric label="최근 이벤트" value={workflowEvents.length.toString()} />
                <Metric label="AI 질의" value="48" />
              </div>
              <Panel title="승인 대기 주문">
                <OrderTable orders={pendingOrders} onSelect={setSelectedOrderId} />
              </Panel>
            </div>
          )}

          {activeMenu === "객체 탐색" && (
            <Panel title="Order 객체">
              <OrderTable orders={orders} onSelect={setSelectedOrderId} />
            </Panel>
          )}

          {activeMenu === "AI 질의" && (
            <div className="space-y-4">
              <Panel title="질문">
                <div className="flex gap-2">
                  <input
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    className="h-10 flex-1 rounded-md border border-slate-300 px-3 text-sm"
                  />
                  <button onClick={ask} className="rounded-md bg-slate-900 px-4 text-sm text-white">
                    질의
                  </button>
                </div>
              </Panel>
              {answer && (
                <Panel title="AI 답변">
                  <p className="text-sm leading-6">{answer}</p>
                </Panel>
              )}
              {evidence.length > 0 && (
                <Panel title="검색 근거">
                  <div className="space-y-3">
                    {evidence.map((document) => (
                      <div key={document.id} className="rounded-md border border-slate-200 p-3">
                        <div className="font-medium">{document.title}</div>
                        <div className="text-xs text-slate-500">Score: {document.score}</div>
                        <p className="mt-2 text-sm text-slate-600">{document.text}</p>
                      </div>
                    ))}
                  </div>
                </Panel>
              )}
            </div>
          )}

          {activeMenu === "승인 워크플로우" && (
            <div className="space-y-4">
              <Panel title="승인 대상">
                <OrderTable orders={pendingOrders} onSelect={setSelectedOrderId} />
              </Panel>
              <Panel title="액션">
                <div className="flex gap-2">
                  {getAvailableActions(selectedOrder).map((action) => (
                    <button
                      key={action}
                      onClick={() => executeAction(action)}
                      className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white"
                    >
                      {action}
                    </button>
                  ))}
                </div>
              </Panel>
            </div>
          )}
        </section>

        <aside className="border-l border-slate-200 bg-white px-4 py-5">
          <h2 className="mb-4 text-base font-semibold">컨텍스트</h2>
          <div className="space-y-4">
            <Panel title="선택 객체">
              <div className="space-y-1 text-sm">
                <div>Order: {selectedOrder.id}</div>
                <div>Status: {selectedOrder.status}</div>
                <div>Amount: {selectedOrder.amount}</div>
              </div>
            </Panel>
            <Panel title="고객">
              <div className="space-y-1 text-sm">
                <div>{selectedContext?.customer?.name}</div>
                <div>{selectedContext?.customer?.segment}</div>
                <div>Risk: {selectedContext?.customer?.riskTier}</div>
              </div>
            </Panel>
            <Panel title="제품">
              <div className="space-y-2 text-sm">
                {selectedContext?.products.map((product) => (
                  <div key={product.id}>
                    {product.name} · {product.category}
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </aside>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function OrderTable({
  orders,
  onSelect,
}: {
  orders: Order[];
  onSelect: (orderId: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-md border border-slate-200">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500">
          <tr>
            <th className="px-3 py-2">Order</th>
            <th className="px-3 py-2">Customer</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Amount</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr
              key={order.id}
              onClick={() => onSelect(order.id)}
              className="cursor-pointer border-t border-slate-200 hover:bg-slate-50"
            >
              <td className="px-3 py-2 font-medium">{order.id}</td>
              <td className="px-3 py-2">{order.customerId}</td>
              <td className="px-3 py-2">{order.status}</td>
              <td className="px-3 py-2">{order.amount.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

## 10. 구현 시 주의점

`page.tsx`에서 `React.ReactNode` 타입을 사용하므로, 프로젝트 설정에 따라 아래 import가 필요할 수 있습니다.

```tsx
import type { ReactNode } from "react";
```

그 경우 `Panel` 타입을 다음처럼 바꿉니다.

```tsx
function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold">{title}</h2>
      {children}
    </section>
  );
}
```

## 11. 확장 구현

MVP 이후에는 다음 순서로 확장합니다.

1. `POST /api/ask` 추가
2. `POST /api/search` 추가
3. `POST /api/workflow/execute` 추가
4. BM25 검색기를 서버 API로 이동
5. LLM API 연결
6. 객체 상세 페이지 라우팅 추가
7. 문서 검색 전용 화면 추가
8. 온톨로지 관리 화면 추가

## 12. API Route 예시

`src/app/api/ask/route.ts`

```typescript
import { NextResponse } from "next/server";
import { answerQuestion } from "@/lib/rag";

export async function POST(request: Request) {
  const body = await request.json();
  const question = body.question as string;

  return NextResponse.json(answerQuestion(question));
}
```

프론트엔드에서는 다음처럼 호출합니다.

```typescript
const response = await fetch("/api/ask", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ question }),
});

const result = await response.json();
```

## 13. 화면 완성 기준

다음이 동작하면 MVP 완성으로 봅니다.

- 메뉴 전환 가능
- 주문 목록 선택 가능
- 우측 컨텍스트 패널 갱신
- AI 질의 실행 가능
- 검색 근거 표시
- 승인 워크플로우 액션 실행 가능
- 주문 상태 변경 반영

## 14. 요약

Next.js 구현은 온톨로지 AI 시스템을 업무자가 만질 수 있는 화면으로 바꾸는 단계입니다. 처음부터 완전한 백엔드를 붙이기보다, 목 데이터 기반으로 객체 탐색, AI 질의, 근거 확인, 워크플로우 액션의 사용자 경험을 먼저 완성하는 것이 좋습니다.

