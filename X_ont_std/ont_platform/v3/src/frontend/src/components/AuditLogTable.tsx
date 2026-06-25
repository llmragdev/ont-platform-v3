"use client";

import { Download, Loader2, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { mockAuditLogs } from "@/lib/metadata-mock";
import type { AuditLog, AuditQuery } from "@/types/metadata";

const ACTIONS: Array<AuditLog["action"]> = ["create", "update", "delete", "import", "merge"];

function csvEscape(value: unknown): string {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function downloadCsv(items: AuditLog[]) {
  const rows = items.map((item) => [
    item.audit_id,
    item.entity_id ?? "",
    item.action,
    item.performed_by,
    item.performed_at,
    item.status,
    item.retention_days,
  ].map(csvEscape).join(","));
  const csv = [
    ["audit_id", "entity_id", "action", "performed_by", "performed_at", "status", "retention_days"].join(","),
    ...rows,
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "metadata-audit-logs.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function AuditLogTable({
  entityId,
  filters,
  onExport,
}: {
  entityId?: string;
  filters?: AuditQuery;
  onExport?: () => void;
}) {
  const [draft, setDraft] = useState<AuditQuery>({ entity_id: entityId, ...filters });
  const [applied, setApplied] = useState<AuditQuery>({ entity_id: entityId, ...filters });
  const [items, setItems] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(false);

  useEffect(() => {
    setDraft((prev) => ({ ...prev, entity_id: entityId ?? prev.entity_id }));
    setApplied((prev) => ({ ...prev, entity_id: entityId ?? prev.entity_id }));
  }, [entityId]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setUsingMock(false);
      try {
        const response = await api.metadata.getAuditLogs({ ...applied, page_size: 50 });
        if (!cancelled) {
          setItems(response.items);
          setTotal(response.total);
        }
      } catch {
        const filtered = mockAuditLogs.filter((item) => {
          if (applied.entity_id && item.entity_id !== applied.entity_id) return false;
          if (applied.action && item.action !== applied.action) return false;
          if (applied.performed_by && !item.performed_by.includes(applied.performed_by)) return false;
          return true;
        });
        if (!cancelled) {
          setItems(filtered);
          setTotal(filtered.length);
          setUsingMock(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [applied]);

  const statusCounts = useMemo(() => ({
    success: items.filter((item) => item.status === "success").length,
    failed: items.filter((item) => item.status === "failed").length,
  }), [items]);

  function updateDraft(key: keyof AuditQuery, value: string) {
    setDraft((prev) => ({ ...prev, [key]: value || undefined }));
  }

  function handleExport() {
    onExport?.();
    downloadCsv(items);
  }

  return (
    <section data-testid="audit-log-table" className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-slate-500" />
          <h3 className="text-sm font-semibold">Audit Log Table</h3>
        </div>
        <button type="button" className="btn btn-ghost text-xs" onClick={handleExport}>
          <Download className="mr-1.5 h-3.5 w-3.5" />
          CSV
        </button>
      </div>

      <div className="panel-body space-y-4">
        {usingMock && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            Using mock audit logs until the v4 API is available.
          </div>
        )}

        <div className="grid gap-2 md:grid-cols-[1fr_160px_1fr_auto]">
          <input
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            placeholder="Entity ID"
            value={draft.entity_id ?? ""}
            onChange={(event) => updateDraft("entity_id", event.target.value)}
          />
          <select
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={draft.action ?? ""}
            onChange={(event) => updateDraft("action", event.target.value)}
          >
            <option value="">All actions</option>
            {ACTIONS.map((action) => <option key={action} value={action}>{action}</option>)}
          </select>
          <input
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            placeholder="Actor"
            value={draft.performed_by ?? ""}
            onChange={(event) => updateDraft("performed_by", event.target.value)}
          />
          <button type="button" className="btn btn-primary" onClick={() => setApplied(draft)}>
            Apply
          </button>
        </div>

        <div className="flex flex-wrap gap-2 text-xs">
          <span className="badge badge-neutral">{total} total</span>
          <span className="badge badge-low">{statusCounts.success} success</span>
          <span className="badge badge-high">{statusCounts.failed} failed</span>
        </div>

        <div className="overflow-auto rounded-md border border-slate-200">
          {loading ? (
            <div className="flex items-center justify-center gap-2 p-8 text-sm text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading audit logs...
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Audit ID</th>
                  <th>Entity</th>
                  <th>Action</th>
                  <th>Actor</th>
                  <th>Time</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={6} className="py-8 text-center text-slate-400">No audit logs match the current filters.</td></tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.audit_id}>
                      <td className="font-mono text-xs">{item.audit_id}</td>
                      <td className="font-mono text-xs">{item.entity_id ?? "-"}</td>
                      <td><span className="badge badge-neutral">{item.action}</span></td>
                      <td>{item.performed_by}</td>
                      <td className="text-xs text-slate-500">{new Date(item.performed_at).toLocaleString()}</td>
                      <td>
                        <span className={`badge ${item.status === "success" ? "badge-low" : "badge-high"}`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </section>
  );
}
