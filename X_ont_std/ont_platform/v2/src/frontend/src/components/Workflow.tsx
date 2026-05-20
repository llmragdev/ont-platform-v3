"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { WorkflowQueueRow } from "@/types/api";

function statusBadgeClass(status: string) {
  if (["Approved", "Fulfilled", "Closed"].includes(status)) return "badge-low";
  if (status === "Rejected") return "badge-high";
  return "badge-medium";
}

function actionClass(action: string) {
  if (action.startsWith("Approve") || action.startsWith("Fulfill") || action.startsWith("Close")) return "btn-ok";
  if (action.startsWith("Reject")) return "btn-danger";
  if (action.startsWith("Hold")) return "btn-warn";
  return "btn-ghost";
}

export function Workflow() {
  const [queue, setQueue] = useState<WorkflowQueueRow[]>([]);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const res = await api.workflowQueue();
      setQueue(res.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => { void load(); }, []);

  async function execute(row: WorkflowQueueRow, action: string) {
    const key = `${row.entity_id}:${action}`;
    setBusyKey(key);
    setToast(null);
    try {
      const res = await api.workflowExecute(row.doc_id, row.entity_id, action);
      setToast({ kind: "ok", text: `${row.name} → ${res.to_status}` });
      await load();
    } catch (err) {
      setToast({ kind: "err", text: err instanceof Error ? err.message : String(err) });
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">액션 큐 (역할 기반)</h3>
        <div className="flex gap-2 items-center">
          <span className="text-xs text-slate-500">{queue.length}건</span>
          <button className="btn btn-ghost text-xs py-1 px-2" onClick={load}>새로고침</button>
        </div>
      </div>
      <div className="panel-body space-y-3">
        {error && <div className="text-sm text-rose-600 bg-rose-50 rounded px-3 py-2">{error}</div>}
        {toast && (
          <div className={`rounded-md px-3 py-2 text-sm ${
            toast.kind === "ok" ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                : "bg-rose-50 text-rose-800 border border-rose-200"
          }`}>
            {toast.text}
          </div>
        )}
        {queue.length === 0 ? (
          <div className="text-sm text-slate-400 text-center py-6">실행 가능한 액션이 없습니다.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>유형</th><th>이름</th><th>상태</th><th>문서</th><th>액션</th></tr>
            </thead>
            <tbody>
              {queue.map((row) => (
                <tr key={`${row.doc_id}:${row.entity_id}`}>
                  <td className="font-mono text-xs text-slate-500">{row.entity_id}</td>
                  <td><span className="badge badge-neutral">{row.entity_type}</span></td>
                  <td className="font-medium">{row.name}</td>
                  <td><span className={`badge ${statusBadgeClass(row.status)}`}>{row.status}</span></td>
                  <td className="text-xs text-slate-400">{row.doc_id}</td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {row.available_actions.map((action) => {
                        const key = `${row.entity_id}:${action}`;
                        return (
                          <button key={key} type="button"
                            className={`btn ${actionClass(action)} text-xs py-1 px-2`}
                            disabled={busyKey === key}
                            onClick={() => void execute(row, action)}
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
