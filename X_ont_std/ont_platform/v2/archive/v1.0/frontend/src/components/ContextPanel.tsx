"use client";
import type { OrderContext } from "@/types/api";

function riskBadgeClass(tier: string) {
  if (tier === "Low") return "badge-low";
  if (tier === "Medium") return "badge-medium";
  if (tier === "High") return "badge-high";
  return "badge-neutral";
}

function statusBadgeClass(status: string) {
  if (status === "Approved" || status === "Fulfilled" || status === "Closed") return "badge-low";
  if (status === "Rejected") return "badge-high";
  return "badge-medium";
}

export function ContextPanel({ context, loading, error }: {
  context: OrderContext | null;
  loading: boolean;
  error: string | null;
}) {
  return (
    <aside className="w-80 shrink-0 border-l border-slate-200 bg-white p-4 space-y-4 overflow-y-auto">
      <h2 className="text-sm font-semibold text-slate-700">컨텍스트 패널</h2>
      {loading && <div className="text-xs text-slate-500">불러오는 중…</div>}
      {error && <div className="text-xs text-rose-600">{error}</div>}
      {!loading && !error && context && (
        <>
          <section className="panel">
            <div className="panel-body">
              <div className="text-xs text-slate-500">선택 객체</div>
              <div className="text-base font-semibold mt-0.5">Order {context.order.id}</div>
              <div className="text-xs mt-2 space-y-0.5">
                <div>
                  Status: <span className={`badge ${statusBadgeClass(context.order.status)}`}>{context.order.status}</span>
                </div>
                <div>Amount: {context.order.amount.toLocaleString()}</div>
                <div>Date: {context.order.order_date}</div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-body">
              <div className="text-xs text-slate-500">고객 정보</div>
              <div className="text-base font-semibold mt-0.5">{context.customer.name}</div>
              <div className="text-xs mt-2 space-y-0.5">
                <div>Segment: {context.customer.segment}</div>
                <div>Region: {context.customer.region}</div>
                <div>
                  Risk: <span className={`badge ${riskBadgeClass(context.customer.risk_tier)}`}>{context.customer.risk_tier}</span>
                </div>
                {context.customer.contract_terms && (
                  <div className="mt-1 text-slate-500">계약: {context.customer.contract_terms}</div>
                )}
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-body">
              <div className="text-xs text-slate-500">관련 제품</div>
              <ul className="text-xs mt-2 space-y-1">
                {context.products.map((product) => (
                  <li key={product.id} className="flex justify-between">
                    <span>· {product.name} ({product.category})</span>
                    <span className="text-slate-500">{product.unit_price.toLocaleString()}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="panel">
            <div className="panel-body">
              <div className="text-xs text-slate-500">실행 가능 액션</div>
              {context.available_actions.length === 0 ? (
                <div className="text-xs text-slate-400 mt-2">현재 사용자에게 허용된 액션이 없습니다.</div>
              ) : (
                <div className="flex flex-wrap gap-1 mt-2">
                  {context.available_actions.map((action) => (
                    <span key={action} className="badge badge-neutral">{action}</span>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </aside>
  );
}
