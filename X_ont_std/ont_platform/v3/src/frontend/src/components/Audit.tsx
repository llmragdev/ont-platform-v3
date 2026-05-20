"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditEvent } from "@/types/api";

export function Audit() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const res = await api.auditEvents();
      setEvents(res.events ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => { void load(); }, []);

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">감사 로그</h3>
        <button className="btn btn-ghost text-xs py-1 px-2" onClick={load}>새로고침</button>
      </div>
      <div className="panel-body p-0">
        {error && <div className="p-3 text-sm text-rose-600">{error}</div>}
        <table className="data-table">
          <thead>
            <tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th><th>Detail</th></tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-6 text-slate-400">기록된 이벤트가 없습니다.</td></tr>
            ) : (
              events.map((ev) => (
                <tr key={ev.event_id}>
                  <td className="text-xs text-slate-500">{new Date(ev.timestamp).toLocaleString()}</td>
                  <td>{ev.user_id}</td>
                  <td><span className="badge badge-neutral">{ev.action}</span></td>
                  <td className="text-xs">{ev.resource_type} {ev.resource_id}</td>
                  <td className="text-xs text-slate-600">
                    <code className="text-[10px]">{JSON.stringify(ev.details)}</code>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
