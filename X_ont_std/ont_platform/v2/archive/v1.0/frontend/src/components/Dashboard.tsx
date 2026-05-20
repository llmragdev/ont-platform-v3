"use client";
import type { Order, WorkflowQueueRow } from "@/types/api";

function statusBadgeClass(status: string) {
  if (status === "Approved" || status === "Fulfilled" || status === "Closed") return "badge-low";
  if (status === "Rejected") return "badge-high";
  return "badge-medium";
}

export function Dashboard({
  orders,
  queue,
  onSelect,
  selectedId,
}: {
  orders: Order[];
  queue: WorkflowQueueRow[];
  onSelect: (orderId: string) => void;
  selectedId: string | null;
}) {
  const pending = orders.filter((order) => order.status === "Submitted" || order.status === "Review");
  const totalAmount = orders.reduce((sum, order) => sum + order.amount, 0);

  const metrics = [
    { label: "전체 주문", value: orders.length.toString() },
    { label: "승인 대기", value: pending.length.toString() },
    { label: "내 액션 큐", value: queue.length.toString() },
    { label: "총 주문 금액", value: totalAmount.toLocaleString() },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="panel">
            <div className="panel-body">
              <div className="text-xs text-slate-500">{metric.label}</div>
              <div className="text-2xl font-bold mt-1">{metric.value}</div>
            </div>
          </div>
        ))}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">승인 대기 주문</h3>
          <span className="text-xs text-slate-500">{pending.length}건</span>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {pending.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-6 text-slate-400">대기 중인 주문이 없습니다.</td>
                </tr>
              ) : (
                pending.map((order) => (
                  <tr
                    key={order.id}
                    className={`clickable ${selectedId === order.id ? "active" : ""}`}
                    onClick={() => onSelect(order.id)}
                  >
                    <td className="font-semibold">{order.id}</td>
                    <td>{order.customer_id}</td>
                    <td>{order.order_date}</td>
                    <td>{order.amount.toLocaleString()}</td>
                    <td><span className={`badge ${statusBadgeClass(order.status)}`}>{order.status}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
