"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditEvent } from "@/types/api";

interface ChangelogRecord {
  changelog_id: string;
  entity_id: string;
  entity_type: string;
  action: string;
  old_value: any;
  new_value: any;
  performed_by: string;
  performed_at: string;
  sync_status: "pending" | "syncing" | "synced" | "failed" | "skipped";
  synced_at?: string;
}

interface WriteBackRecord {
  write_back_id: string;
  changelog_id: string;
  target_system: string;
  entity_id: string;
  action: string;
  status: "pending" | "syncing" | "synced" | "failed" | "skipped";
  created_at: string;
  last_attempt_at?: string;
  attempt_count: number;
  errors: any[];
}

export function Audit() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [changelogs, setChangelogs] = useState<ChangelogRecord[]>([]);
  const [writebacks, setWritebacks] = useState<WriteBackRecord[]>([]);
  const [activeTab, setActiveTab] = useState<"events" | "changelog" | "writeback">("events");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [eventsRes, changelogRes, writebackRes] = await Promise.all([
        api.auditEvents().catch(() => ({ events: [] })),
        fetch("/api/changelogs").then(r => r.json()).catch(() => ({ changelogs: [] })),
        fetch("/api/writebacks").then(r => r.json()).catch(() => ({ writebacks: [] })),
      ]);
      setEvents(eventsRes.events ?? []);
      setChangelogs(changelogRes.changelogs ?? []);
      setWritebacks(writebackRes.writebacks ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => { void load(); }, []);

  function syncStatusBadge(status: string) {
    const variants: Record<string, string> = {
      pending: "badge-medium",
      syncing: "badge-medium",
      synced: "badge-low",
      failed: "badge-high",
      skipped: "badge-neutral",
    };
    return variants[status] || "badge-neutral";
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">감사 로그</h3>
        <button className="btn btn-ghost text-xs py-1 px-2" onClick={load}>새로고침</button>
      </div>

      {/* Tab buttons */}
      <div className="flex border-b border-slate-200">
        {(["events", "changelog", "writeback"] as const).map((tab) => (
          <button
            key={tab}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "events" && `이벤트 (${events.length})`}
            {tab === "changelog" && `변경로그 (${changelogs.length})`}
            {tab === "writeback" && `WriteBack (${writebacks.length})`}
          </button>
        ))}
      </div>

      <div className="panel-body p-0">
        {error && <div className="p-3 text-sm text-rose-600">{error}</div>}

        {/* Events tab */}
        {activeTab === "events" && (
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
        )}

        {/* Changelog tab */}
        {activeTab === "changelog" && (
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>Entity</th><th>Action</th><th>Status</th><th>User</th><th>Time</th><th>Changes</th></tr>
            </thead>
            <tbody>
              {changelogs.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-6 text-slate-400">변경로그가 없습니다.</td></tr>
              ) : (
                changelogs.map((log) => (
                  <tr key={log.changelog_id}>
                    <td className="font-mono text-xs text-slate-500">{log.changelog_id}</td>
                    <td className="text-xs">{log.entity_type} {log.entity_id}</td>
                    <td><span className="badge badge-neutral">{log.action}</span></td>
                    <td><span className={`badge ${syncStatusBadge(log.sync_status)}`}>{log.sync_status}</span></td>
                    <td className="text-xs">{log.performed_by}</td>
                    <td className="text-xs text-slate-500">{new Date(log.performed_at).toLocaleString()}</td>
                    <td className="text-xs">
                      {Object.keys(log.new_value).length > 0 && (
                        <code className="text-[10px] text-slate-600">
                          {Object.entries(log.new_value).map(([k, v]) => `${k}: ${v}`).join(", ")}
                        </code>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        {/* WriteBack tab */}
        {activeTab === "writeback" && (
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>System</th><th>Entity</th><th>Status</th><th>Attempts</th><th>Created</th><th>Errors</th></tr>
            </thead>
            <tbody>
              {writebacks.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-6 text-slate-400">WriteBack 기록이 없습니다.</td></tr>
              ) : (
                writebacks.map((wb) => (
                  <tr key={wb.write_back_id}>
                    <td className="font-mono text-xs text-slate-500">{wb.write_back_id}</td>
                    <td className="text-xs">{wb.target_system}</td>
                    <td className="text-xs">{wb.entity_id}</td>
                    <td><span className={`badge ${syncStatusBadge(wb.status)}`}>{wb.status}</span></td>
                    <td className="text-center text-xs">{wb.attempt_count}</td>
                    <td className="text-xs text-slate-500">{new Date(wb.created_at).toLocaleString()}</td>
                    <td className="text-xs">
                      {wb.errors.length > 0 && (
                        <div className="max-w-xs truncate text-rose-600">
                          {wb.errors[wb.errors.length - 1]?.message}
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
