"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import type { WorkflowQueueRow } from "@/types/api";

function statusBadgeClass(status: string) {
  if (status === "Approved" || status === "Fulfilled" || status === "Closed") return "badge-low";
  if (status === "Rejected") return "badge-high";
  return "badge-medium";
}

function actionClass(action: string) {
  if (action.startsWith("Approve") || action.startsWith("Fulfill") || action.startsWith("Close")) return "btn-ok";
  if (action.startsWith("Reject")) return "btn-danger";
  if (action.startsWith("Hold")) return "btn-warn";
  return "btn-ghost";
}

export function Workflow({
  user,
  queue,
  onAfterExecute,
}: {
  user: string;
  queue: WorkflowQueueRow[];
  onAfterExecute: () => Promise<void>;
}) {
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  async function execute(orderId: string, action: string) {
    const key = `${orderId}:${action}`;
    setBusyKey(key);
    setToast(null);
    try {
      const response = await api.workflowExecute(user, orderId, action);
      setToast({ kind: "ok", text: `${orderId} → ${response.result.to_status}` });
      await onAfterExecute();
    } catch (err) {
      setToast({ kind: "err", text: err instanceof Error ? err.message : String(err) });
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">현재 사용자의 액션 큐</h3>
        <span className="text-xs text-slate-500">{queue.length}건</span>
      </div>
      <div className="panel-body space-y-3">
        {toast && (
          <div
            className={`rounded-md px-3 py-2 text-sm ${
              toast.kind === "ok"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-rose-50 text-rose-800 border border-rose-200"
            }`}
          >
            {toast.text}
          </div>
        )}
        {queue.length === 0 ? (
          <div className="text-sm text-slate-400 text-center py-6">실행 가능한 액션이 없습니다. (역할/지역/리스크에 따라 비어 있을 수 있습니다.)</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Amount</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((row) => (
                <tr key={row.id}>
                  <td className="font-semibold">{row.id}</td>
                  <td>{row.customer.name}</td>
                  <td><span className={`badge ${statusBadgeClass(row.status)}`}>{row.status}</span></td>
                  <td>{row.amount.toLocaleString()}</td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {row.available_actions.map((action) => {
                        const key = `${row.id}:${action}`;
                        return (
                          <button
                            key={key}
                            type="button"
                            className={`btn ${actionClass(action)} text-xs py-1 px-2`}
                            disabled={busyKey === key}
                            onClick={() => execute(row.id, action)}
                          >
                            {busyKey === key ? "…" : action}
                          </button>
                        );
                      })}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
