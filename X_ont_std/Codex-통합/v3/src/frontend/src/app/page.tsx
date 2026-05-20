"use client";

import { useEffect, useState } from "react";
import {
  orders as initialOrders,
  workflowEvents,
  documents as mockDocuments,
} from "@/lib/mock-data";
import type { KnowledgeDocument, Order } from "@/types/ontology";
import {
  DEFAULT_TENANT,
  checkHealth,
  fetchWorkflowQueue,
  executeWorkflowAction,
  hybridAsk,
  seedDemoData,
  type WorkflowQueueItem,
  type AiQueryResult,
} from "@/lib/api";

// ── Unified display type (works for both backend entities and mock orders) ────

type DisplayOrder = {
  id: string;
  name: string;
  type: string;
  status: string;
  customerId: string;
  amount: number;
  availableActions: string[];
  provenance?: any;
};

type BackendStatus = "checking" | "online" | "offline";

// ── Helpers ───────────────────────────────────────────────────────────────────

const ACTIONS_FOR_STATUS: Record<string, string[]> = {
  Submitted: ["ApproveOrder", "RejectOrder", "HoldOrder"],
  Review: ["ApproveOrder", "RejectOrder"],
  Approved: ["FulfillOrder"],
  Fulfilled: ["CloseOrder"],
};

const STATUS_BY_ACTION: Record<string, string> = {
  ApproveOrder: "Approved",
  RejectOrder: "Rejected",
  HoldOrder: "Review",
  FulfillOrder: "Fulfilled",
  CloseOrder: "Closed",
};

function mockToDisplay(order: Order): DisplayOrder {
  return {
    id: order.id,
    name: `Order ${order.id}`,
    status: order.status,
    customerId: order.customerId,
    amount: order.amount,
    availableActions: ACTIONS_FOR_STATUS[order.status] ?? [],
  };
}

function entityToDisplay(entity: WorkflowQueueItem): DisplayOrder {
  const props = (entity.values ?? {}) as Record<string, unknown>;
  return {
    id: entity.id,
    name: entity.name,
    type: entity.type,
    status: entity.status,
    customerId: String(props.customerId ?? props.customer_id ?? "—"),
    amount: Number(props.amount ?? 0),
    availableActions: entity.available_actions,
    provenance: entity.provenance,
  };
}

function formatAiResult(result: AiQueryResult): string {
  if (result.query_type === "filter") {
    const count = result.count ?? result.results?.length ?? 0;
    if (count === 0) return "조건에 맞는 엔티티를 찾지 못했습니다.";
    const names = (result.results ?? [])
      .slice(0, 5)
      .map((e) => e.name ?? e.id)
      .join(", ");
    return `${count}개 항목을 찾았습니다: ${names}`;
  }
  if (result.query_type === "descriptive") {
    return (
      result.answer ??
      `분석 완료 — 질의 유형: ${result.query_type}`
    );
  }
  return "현재 해당 질의 유형은 지원되지 않습니다 (compare/calculate/hybrid 준비 중).";
}

// ── Component ─────────────────────────────────────────────────────────────────

const menus = ["대시보드", "객체 탐색", "AI 질의", "승인 워크플로우"];

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [displayOrders, setDisplayOrders] = useState<DisplayOrder[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState<string>("");
  const [isSeeding, setIsSeeding] = useState(false);
  const [activeMenu, setActiveMenu] = useState("대시보드");
  const [question, setQuestion] = useState(
    "Submitted 상태인 Order를 찾아줘",
  );
  const [answer, setAnswer] = useState("");
  const [evidence, setEvidence] = useState<KnowledgeDocument[]>([]);
  const [isAskLoading, setIsAskLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [wcDate, setWcDate] = useState("2026-06-01");

  const tenantCfg = DEFAULT_TENANT;

  async function loadQueue(): Promise<DisplayOrder[]> {
    try {
      const items = await fetchWorkflowQueue(tenantCfg);
      return items.map(entityToDisplay);
    } catch {
      return [];
    }
  }

  useEffect(() => {
    checkHealth().then((online) => {
      setBackendStatus(online ? "online" : "offline");
      if (online) {
        loadQueue().then((orders) => {
          setDisplayOrders(orders);
          if (orders.length > 0) setSelectedOrderId(orders[0].id);
        });
      } else {
        const mock = initialOrders.map(mockToDisplay);
        setDisplayOrders(mock);
        setSelectedOrderId(mock[0]?.id ?? "");
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedOrder =
    displayOrders.find((o) => o.id === selectedOrderId) ?? displayOrders[0];

  const pendingOrders = displayOrders.filter(
    (o) => o.status === "Submitted" || o.status === "Review",
  );

  async function ask() {
    if (backendStatus === "online") {
      setIsAskLoading(true);
      try {
        const result = await hybridAsk(tenantCfg, question);
        setAnswer(formatAiResult(result));
        setEvidence([]);
      } catch (e) {
        setAnswer(`오류: ${(e as Error).message}`);
      } finally {
        setIsAskLoading(false);
      }
    } else {
      // demo mode — local mock answer
      setAnswer(
        "[데모 모드] 백엔드 없이 샘플 답변입니다. 승인 가능성이 높습니다. 주문은 Submitted 상태이며 금액 조건을 만족합니다.",
      );
      setEvidence(mockDocuments.slice(0, 2));
    }
  }

  async function executeAction(action: string) {
    setActionError(null);
    if (backendStatus === "online" && selectedOrder) {
      try {
        const params = action === "CHANGE_WC_DATE" ? { new_date: wcDate } : {};
        await executeWorkflowAction(
          tenantCfg,
          action,
          selectedOrder.id,
          params
        );
        const refreshed = await loadQueue();
        setDisplayOrders(refreshed);
      } catch (e) {
        setActionError((e as Error).message);
      }
    } else {
      setDisplayOrders((prev) =>
        prev.map((o) => {
          if (o.id !== selectedOrderId) return o;
          const newStatus = STATUS_BY_ACTION[action] ?? o.status;
          return {
            ...o,
            status: newStatus,
            availableActions: ACTIONS_FOR_STATUS[newStatus] ?? [],
          };
        }),
      );
    }
  }

  async function handleSeed() {
    setIsSeeding(true);
    try {
      await seedDemoData(tenantCfg);
      const orders = await loadQueue();
      setDisplayOrders(orders);
      if (orders.length > 0) setSelectedOrderId(orders[0].id);
    } catch (e) {
      console.error("Seed failed:", e);
    } finally {
      setIsSeeding(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950 font-sans">
      {backendStatus === "checking" && (
        <div className="fixed inset-0 bg-white/80 flex items-center justify-center z-50">
          <span className="text-slate-500 text-sm font-medium animate-pulse">
            백엔드 연결 확인 중...
          </span>
        </div>
      )}

      <div className="grid min-h-screen grid-cols-[240px_1fr_340px]">
        {/* Sidebar */}
        <aside className="border-r border-slate-200 bg-white px-4 py-6 flex flex-col">
          <div className="mb-10">
            <div className="text-xl font-bold tracking-tight text-slate-900">
              Ontology AI
            </div>
            <div className="text-xs font-medium text-slate-400 uppercase mt-1">
              Workbench v2.0
            </div>
          </div>
          <nav className="space-y-1">
            {menus.map((menu) => (
              <button
                key={menu}
                onClick={() => setActiveMenu(menu)}
                className={`w-full rounded-lg px-4 py-2.5 text-left text-sm font-medium transition-all ${
                  activeMenu === menu
                    ? "bg-slate-900 text-white shadow-lg shadow-slate-200"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                {menu}
              </button>
            ))}
          </nav>

          <div className="mt-auto pt-6 border-t border-slate-100">
            <div className="text-[10px] font-bold text-slate-400 uppercase mb-3">
              테넌트 설정
            </div>
            <div className="space-y-1.5 text-[11px] text-slate-500">
              <div className="flex justify-between">
                <span>Company</span>
                <span className="font-mono text-slate-700">
                  {tenantCfg.companyId}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Project</span>
                <span className="font-mono text-slate-700">
                  {tenantCfg.projectId}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Role</span>
                <span className="font-mono text-slate-700">
                  {tenantCfg.role}
                </span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <section className="px-8 py-8 overflow-y-auto">
          <header className="mb-8 flex items-end justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">
                {activeMenu}
              </h1>
              <p className="text-slate-500 mt-1">
                지능형 객체 기반 의사결정 지원 시스템
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 rounded-full bg-white border border-slate-200 px-4 py-1.5 shadow-sm">
                <span
                  className={`w-2 h-2 rounded-full ${
                    backendStatus === "online"
                      ? "bg-emerald-500 animate-pulse"
                      : backendStatus === "offline"
                        ? "bg-amber-400"
                        : "bg-slate-300 animate-pulse"
                  }`}
                />
                <span className="text-xs font-bold text-slate-700">
                  {backendStatus === "online"
                    ? "LIVE"
                    : backendStatus === "offline"
                      ? "DEMO"
                      : "..."}
                </span>
              </div>
              {selectedOrder && (
                <div className="flex items-center gap-2 rounded-full bg-white border border-slate-200 px-4 py-1.5 shadow-sm">
                  <span className="text-xs font-bold text-slate-700">
                    {selectedOrder.name}
                  </span>
                  <span className="text-xs text-slate-300">|</span>
                  <span className="text-xs font-medium text-slate-500 uppercase">
                    {selectedOrder.status}
                  </span>
                </div>
              )}
            </div>
          </header>

          {/* Empty backend banner with seed button */}
          {backendStatus === "online" && displayOrders.length === 0 && (
            <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 flex items-center justify-between">
              <div>
                <div className="text-sm font-bold text-amber-800">
                  백엔드 데이터가 없습니다
                </div>
                <div className="text-xs text-amber-600 mt-0.5">
                  데모용 Order 엔티티를 생성해 기능을 확인하세요.
                </div>
              </div>
              <button
                onClick={handleSeed}
                disabled={isSeeding}
                className="rounded-xl bg-amber-600 px-5 py-2 text-sm font-bold text-white hover:bg-amber-700 disabled:opacity-50 transition-all"
              >
                {isSeeding ? "생성 중..." : "데모 데이터 생성"}
              </button>
            </div>
          )}

          <div className="space-y-6">
            {activeMenu === "대시보드" && (
              <>
                <div className="grid grid-cols-4 gap-4">
                  <Metric
                    label="승인 대기"
                    value={pendingOrders.length.toString()}
                    trend={
                      pendingOrders.length > 0
                        ? `+${pendingOrders.length}`
                        : "—"
                    }
                  />
                  <Metric
                    label="전체 엔티티"
                    value={displayOrders.length.toString()}
                    trend="Tracked"
                  />
                  <Metric
                    label="처리된 이벤트"
                    value={workflowEvents.length.toString()}
                    trend="+5"
                  />
                  <Metric
                    label="백엔드"
                    value={backendStatus === "online" ? "LIVE" : "DEMO"}
                    trend={backendStatus === "online" ? "v2.0" : "Mock"}
                  />
                </div>
                <Panel title="우선 처리 대상 (Pending)">
                  {pendingOrders.length > 0 ? (
                    <OrderTable
                      orders={pendingOrders}
                      onSelect={setSelectedOrderId}
                      selectedId={selectedOrderId}
                    />
                  ) : (
                    <p className="text-sm text-slate-400 italic py-4 text-center">
                      처리 대기 중인 엔티티가 없습니다.
                    </p>
                  )}
                </Panel>
              </>
            )}

            {activeMenu === "객체 탐색" && (
              <Panel title={`전체 엔티티 탐색 (${displayOrders.length}개)`}>
                {displayOrders.length > 0 ? (
                  <OrderTable
                    orders={displayOrders}
                    onSelect={setSelectedOrderId}
                    selectedId={selectedOrderId}
                  />
                ) : (
                  <p className="text-sm text-slate-400 italic py-4 text-center">
                    엔티티가 없습니다. 데모 데이터를 생성하거나 문서를
                    업로드하세요.
                  </p>
                )}
              </Panel>
            )}

            {activeMenu === "AI 질의" && (
              <div className="space-y-6">
                <div className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200">
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-3">
                    업무 질의 입력
                  </label>
                  <div className="flex gap-3">
                    <input
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && ask()}
                      placeholder="예: Submitted 상태인 Order를 찾아줘"
                      className="h-12 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 transition-all"
                    />
                    <button
                      onClick={ask}
                      disabled={isAskLoading}
                      className="rounded-xl bg-slate-900 px-8 font-bold text-white hover:bg-slate-800 transition-all shadow-lg shadow-slate-200 disabled:opacity-50"
                    >
                      {isAskLoading ? "분석 중..." : "AI 분석 실행"}
                    </button>
                  </div>
                  {backendStatus === "offline" && (
                    <p className="text-[11px] text-amber-600 mt-2">
                      데모 모드: 백엔드 없이 샘플 답변을 표시합니다.
                    </p>
                  )}
                </div>

                {answer && (
                  <Panel title="AI 분석 결과">
                    <div className="bg-slate-50 rounded-xl p-5 border-l-4 border-slate-900">
                      <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-wrap">
                        {answer}
                      </p>
                    </div>
                  </Panel>
                )}

                {evidence.length > 0 && (
                  <Panel title="결정 근거 (RAG 검색 결과)">
                    <div className="grid gap-4">
                      {evidence.map((doc) => (
                        <div
                          key={doc.id}
                          className="group rounded-xl border border-slate-100 bg-slate-50/50 p-4 hover:bg-white hover:border-slate-200 transition-all"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h3 className="font-bold text-slate-900">
                              {doc.title}
                            </h3>
                          </div>
                          <p className="text-xs leading-relaxed text-slate-500">
                            {doc.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </Panel>
                )}
              </div>
            )}

            {activeMenu === "승인 워크플로우" && (
              <div className="space-y-6">
                <Panel title="워크플로우 액션 실행">
                  {actionError && (
                    <div className="mb-4 rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700 font-medium">
                      오류: {actionError}
                    </div>
                  )}
                  <div className="flex flex-wrap gap-3">
                    {(selectedOrder?.availableActions?.length ?? 0) > 0 ? (
                      (selectedOrder?.availableActions ?? []).map((action) => (
                        <button
                          key={action}
                          onClick={() => executeAction(action)}
                          className="rounded-xl bg-white border border-slate-200 px-6 py-3 text-sm font-bold text-slate-900 hover:bg-slate-900 hover:text-white transition-all shadow-sm"
                        >
                          {action}
                        </button>
                      ))
                    ) : (
                      <div className="text-sm text-slate-400 italic">
                        이 상태에서 실행 가능한 액션이 없습니다.
                      </div>
                    )}
                  </div>
                </Panel>
                <Panel title="대상 엔티티 정보">
                  <div className="bg-slate-50 rounded-xl p-4">
                    {selectedOrder && (
                      <OrderTable
                        orders={[selectedOrder]}
                        onSelect={() => {}}
                        selectedId={selectedOrderId}
                      />
                    )}
                  </div>
                </Panel>
              </div>
            )}
          </div>
        </section>

        {/* Right Context Panel */}
        <aside className="border-l border-slate-200 bg-white px-6 py-8 overflow-y-auto">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-lg font-bold text-slate-900">객체 컨텍스트</h2>
            <span
              className={`text-[10px] font-bold border px-2 py-0.5 rounded ${
                backendStatus === "online"
                  ? "text-emerald-600 border-emerald-200 bg-emerald-50"
                  : "text-amber-600 border-amber-200 bg-amber-50"
              }`}
            >
              {backendStatus === "online" ? "LIVE" : "DEMO"}
            </span>
          </div>

          {selectedOrder ? (
            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                  Entity Details
                </label>
                <div className="rounded-2xl bg-slate-50 p-5 space-y-3 border border-slate-100">
                  <ContextItem label="ID" value={selectedOrder.id} />
                  <ContextItem label="Name" value={selectedOrder.name} />
                  <ContextItem
                    label="Status"
                    value={selectedOrder.status}
                    isStatus
                  />
                  <ContextItem
                    label="Amount"
                    value={
                      selectedOrder.amount > 0
                        ? `$${selectedOrder.amount.toLocaleString()}`
                        : "—"
                    }
                  />
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                  Customer
                </label>
                <div className="rounded-2xl bg-slate-50 p-5 border border-slate-100">
                  <ContextItem
                    label="Customer ID"
                    value={selectedOrder.customerId}
                  />
                </div>
              </div>

              {selectedOrder.availableActions.length > 0 && (
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Action Parameters
                  </label>
                  <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                    <label className="text-[10px] text-slate-500 mb-1 block">WC Date</label>
                    <input 
                      type="date" 
                      value={wcDate}
                      onChange={(e) => setWcDate(e.target.value)}
                      className="w-full text-xs p-2 rounded border border-slate-200"
                    />
                  </div>
                </div>
              )}

              {selectedOrder.provenance && (
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Provenance (출처)
                  </label>
                  <div className="rounded-2xl bg-indigo-50 p-5 border border-indigo-100 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-indigo-600 font-bold uppercase">Source</span>
                      <span className="text-xs font-bold text-indigo-900">{selectedOrder.provenance.source_kind}</span>
                    </div>
                    {selectedOrder.provenance.doc_id && (
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] text-indigo-400 font-bold">Doc ID</span>
                        <span className="text-xs font-medium text-indigo-800">{selectedOrder.provenance.doc_id}</span>
                      </div>
                    )}
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-indigo-400 font-bold">Confidence</span>
                      <span className="text-xs font-bold text-emerald-600">{(selectedOrder.provenance.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="pt-2 border-t border-indigo-100 mt-2">
                      <p className="text-[10px] text-indigo-400 italic">
                        Palantir Principle: Every entity must have a traceable origin.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic">
              엔티티를 선택하세요.
            </p>
          )}
        </aside>
      </div>
    </main>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Metric({
  label,
  value,
  trend,
}: {
  label: string;
  value: string;
  trend: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="text-xs font-bold text-slate-400 uppercase tracking-tight">
        {label}
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <div className="text-3xl font-black text-slate-900">{value}</div>
        <div
          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
            trend.startsWith("+")
              ? "bg-emerald-100 text-emerald-700"
              : "bg-slate-100 text-slate-500"
          }`}
        >
          {trend}
        </div>
      </div>
    </div>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-5 text-sm font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
        <span className="w-1.5 h-1.5 bg-slate-900 rounded-full" />
        {title}
      </h2>
      {children}
    </section>
  );
}

function ContextItem({
  label,
  value,
  isStatus,
}: {
  label: string;
  value: string;
  isStatus?: boolean;
}) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-xs text-slate-500">{label}</span>
      <span
        className={`text-xs font-bold ${isStatus ? "text-indigo-600" : "text-slate-900"}`}
      >
        {value}
      </span>
    </div>
  );
}

function OrderTable({
  orders,
  onSelect,
  selectedId,
}: {
  orders: DisplayOrder[];
  onSelect: (id: string) => void;
  selectedId: string;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-100">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">
          <tr>
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3">Customer</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Amount</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {orders.map((order) => (
            <tr
              key={order.id}
              onClick={() => onSelect(order.id)}
              className={`cursor-pointer transition-colors hover:bg-slate-50 ${
                selectedId === order.id
                  ? "bg-slate-50/80 ring-1 ring-inset ring-slate-200"
                  : ""
              }`}
            >
              <td className="px-4 py-3 font-bold text-slate-900">
                {order.name}
              </td>
              <td className="px-4 py-3 text-slate-500 font-medium">
                {order.customerId}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                    order.status === "Approved"
                      ? "bg-emerald-100 text-emerald-700"
                      : order.status === "Rejected"
                        ? "bg-rose-100 text-rose-700"
                        : order.status === "Fulfilled"
                          ? "bg-blue-100 text-blue-700"
                          : order.status === "Closed"
                            ? "bg-slate-200 text-slate-600"
                            : "bg-amber-100 text-amber-700"
                  }`}
                >
                  {order.status}
                </span>
              </td>
              <td className="px-4 py-3 font-mono font-bold text-slate-700">
                {order.amount > 0 ? `$${order.amount.toLocaleString()}` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
