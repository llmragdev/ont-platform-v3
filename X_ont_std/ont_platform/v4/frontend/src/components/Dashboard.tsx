"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { WorkflowQueueRow } from "@/types/api";

function statusBadgeClass(status: string) {
  if (["Approved", "Fulfilled", "Closed"].includes(status)) return "badge-low";
  if (status === "Rejected") return "badge-high";
  return "badge-medium";
}

export function Dashboard() {
  const [queue, setQueue] = useState<WorkflowQueueRow[]>([]);
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

  const pending = queue.filter((r) => ["Submitted", "Review"].includes(r.status));
  const metrics = [
    { label: "전체 엔티티 큐", value: queue.length.toString() },
    { label: "승인 대기", value: pending.length.toString() },
    { label: "실행 가능 액션", value: queue.reduce((s, r) => s + r.available_actions.length, 0).toString() },
    { label: "엔티티 유형", value: [...new Set(queue.map((r) => r.entity_type))].length.toString() },
  ];

  return (
    <div className="space-y-6">
      {error && <div className="text-sm text-rose-600 bg-rose-50 rounded px-3 py-2">{error}</div>}
      <div className="grid grid-cols-4 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="panel">
            <div className="panel-body">
              <div className="text-xs text-slate-500">{m.label}</div>
              <div className="text-2xl font-bold mt-1">{m.value}</div>
            </div>
          </div>
        ))}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">액션 큐</h3>
          <div className="flex gap-2 items-center">
            <span className="text-xs text-slate-500">{queue.length}건</span>
            <button className="btn btn-ghost text-xs py-1 px-2" onClick={load}>새로고침</button>
          </div>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>유형</th>
                <th>이름</th>
                <th>상태</th>
                <th>가능한 액션</th>
                <th>문서</th>
              </tr>
            </thead>
            <tbody>
              {queue.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-6 text-slate-400">대기 중인 항목이 없습니다.</td></tr>
              ) : (
                queue.map((row) => (
                  <tr key={`${row.doc_id}:${row.entity_id}`}>
                    <td className="font-mono text-xs text-slate-500">{row.entity_id}</td>
                    <td><span className="badge badge-neutral">{row.entity_type}</span></td>
                    <td className="font-medium">{row.name}</td>
                    <td><span className={`badge ${statusBadgeClass(row.status)}`}>{row.status}</span></td>
                    <td className="text-xs text-slate-600">{row.available_actions.join(", ")}</td>
                    <td className="text-xs text-slate-400">{row.doc_id}</td>
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
