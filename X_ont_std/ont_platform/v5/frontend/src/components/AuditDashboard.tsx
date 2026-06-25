"use client";

import { ChevronDown, ChevronRight, Download, Filter, RefreshCw, RotateCcw } from "lucide-react";
import { Fragment, useMemo, useState } from "react";
import { useChangelog } from "@/hooks/useChangelog";
import type { ChangelogEntry, ChangelogFilters } from "@/types/changelog";

interface AuditDashboardProps {
  domainId?: string;
  entityId?: string;
}

const ACTION_TYPES = ["APPROVE_PROJECT", "REJECT_PROJECT", "CHANGE_DEADLINE", "START_PAYMENT", "CANCEL_PAYMENT"];
const SYNC_STATUSES = ["PENDING", "SYNCED", "FAILED"];

function valueOrDash(value: unknown): string {
  if (value == null || value === "") return "-";
  return String(value);
}

function actionOf(item: ChangelogEntry): string {
  return item.action_type ?? item.action ?? "-";
}

function userOf(item: ChangelogEntry): string {
  return item.performed_by ?? item.user ?? "-";
}

function timeOf(item: ChangelogEntry): string {
  const raw = item.performed_at ?? item.timestamp;
  if (!raw) return "-";
  return new Date(raw).toLocaleString();
}

function statusOf(item: ChangelogEntry): string {
  return String(item.sync_status ?? "PENDING").toUpperCase();
}

function statusBadge(status: string): string {
  const normalized = status.toUpperCase();
  if (normalized === "SYNCED") return "badge-low";
  if (normalized === "FAILED") return "badge-high";
  if (normalized === "PENDING" || normalized === "SYNCING") return "badge-medium";
  return "badge-neutral";
}

function transitionOf(item: ChangelogEntry): string {
  const oldStatus = item.old_status ?? (item.old_value?.status as string | undefined);
  const newStatus = item.new_status ?? (item.new_value?.status as string | undefined);
  if (!oldStatus && !newStatus) return "-";
  return `${valueOrDash(oldStatus)} -> ${valueOrDash(newStatus)}`;
}

function toCsv(items: ChangelogEntry[]): string {
  const columns = ["action", "user", "time", "sync_status", "transition", "entity_id", "entity_type", "target_system"];
  const lines = items.map((item) =>
    [
      actionOf(item),
      userOf(item),
      timeOf(item),
      statusOf(item),
      transitionOf(item),
      item.entity_id,
      item.entity_type ?? "",
      item.target_system ?? "",
    ].map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")
  );
  return [columns.join(","), ...lines].join("\n");
}

function downloadCsv(items: ChangelogEntry[]) {
  const blob = new Blob([toCsv(items)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "audit-changelog.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function AuditDashboard({ domainId = "ai-voucher-2025", entityId }: AuditDashboardProps) {
  const [draft, setDraft] = useState<ChangelogFilters>({ domainId, entityId });
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const changelog = useChangelog({ domainId, entityId });

  const derivedStats = useMemo(() => {
    const synced = changelog.items.filter((item) => statusOf(item) === "SYNCED").length;
    const failed = changelog.items.filter((item) => statusOf(item) === "FAILED").length;
    const total = changelog.items.length;
    return {
      successRate: changelog.stats?.success_rate ?? (total ? Math.round((synced / total) * 1000) / 10 : 0),
      failedCount: changelog.stats?.failed_count ?? failed,
      pendingCount: changelog.stats?.pending_count ?? changelog.items.filter((item) => statusOf(item) === "PENDING").length,
      averageRetries:
        changelog.stats?.average_retries ??
        (total
          ? Math.round(
              (changelog.items.reduce((sum, item) => sum + (item.retry_count ?? item.attempt_count ?? 0), 0) / total) * 10
            ) / 10
          : 0),
    };
  }, [changelog.items, changelog.stats]);

  function updateDraft(key: keyof ChangelogFilters, value: string) {
    setDraft((prev) => ({ ...prev, [key]: value || undefined }));
  }

  function resetFilters() {
    const next = { domainId, entityId };
    setDraft(next);
    changelog.applyFilters(next);
  }

  return (
    <section data-testid="audit-dashboard" className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">Today sync success</div>
          <div className="mt-2 text-2xl font-bold text-emerald-700">{derivedStats.successRate}%</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">Failed items</div>
          <div className="mt-2 text-2xl font-bold text-rose-700">{derivedStats.failedCount}</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">Pending items</div>
          <div className="mt-2 text-2xl font-bold text-amber-700">{derivedStats.pendingCount}</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">Avg retries</div>
          <div className="mt-2 text-2xl font-bold text-slate-800">{derivedStats.averageRetries}</div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <h3 className="text-sm font-semibold">Audit filters</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn btn-ghost text-xs" onClick={() => changelog.reload()}>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
              Refresh
            </button>
            <button type="button" data-testid="download-csv" className="btn btn-ghost text-xs" onClick={() => downloadCsv(changelog.items)}>
              <Download className="mr-1.5 h-3.5 w-3.5" />
              CSV
            </button>
          </div>
        </div>
        <div className="panel-body grid gap-3 md:grid-cols-6">
          <input
            data-testid="filter-date-from"
            type="date"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={draft.dateFrom ?? ""}
            onChange={(event) => updateDraft("dateFrom", event.target.value)}
          />
          <input
            data-testid="filter-date-to"
            type="date"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={draft.dateTo ?? ""}
            onChange={(event) => updateDraft("dateTo", event.target.value)}
          />
          <select
            data-testid="filter-action-type"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={draft.actionType ?? ""}
            onChange={(event) => updateDraft("actionType", event.target.value)}
          >
            <option value="">All actions</option>
            {ACTION_TYPES.map((action) => <option key={action} value={action}>{action}</option>)}
          </select>
          <input
            data-testid="filter-user"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            placeholder="User"
            value={draft.user ?? ""}
            onChange={(event) => updateDraft("user", event.target.value)}
          />
          <select
            data-testid="filter-sync-status"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm"
            value={draft.syncStatus ?? ""}
            onChange={(event) => updateDraft("syncStatus", event.target.value)}
          >
            <option value="">All status</option>
            {SYNC_STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
          <div className="flex gap-2">
            <button type="button" data-testid="filter-apply" className="btn btn-primary flex-1" onClick={() => changelog.applyFilters(draft)}>
              Apply
            </button>
            <button type="button" data-testid="filter-reset" className="btn btn-ghost px-2" onClick={resetFilters} aria-label="Reset filters">
              <RotateCcw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">Action history</h3>
          <span className="text-xs text-slate-500">{changelog.total} records</span>
        </div>
        <div className="panel-body p-0">
          {changelog.error && <div className="p-3 text-sm text-rose-600">{changelog.error}</div>}
          {changelog.loading ? (
            <div className="p-8 text-center text-sm text-slate-500">Loading audit history...</div>
          ) : changelog.items.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-400">No audit records match the current filters.</div>
          ) : (
            <div className="overflow-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>User</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Status change</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {changelog.items.map((item, index) => {
                    const id = item.changelog_id ?? item.id ?? `${item.entity_id}-${index}`;
                    const expanded = expandedId === id;
                    return (
                      <Fragment key={id}>
                        <tr data-testid="table-row" className="clickable">
                          <td><span className="badge badge-neutral">{actionOf(item)}</span></td>
                          <td>{userOf(item)}</td>
                          <td className="text-xs text-slate-500">{timeOf(item)}</td>
                          <td><span className={`badge ${statusBadge(statusOf(item))}`}>{statusOf(item)}</span></td>
                          <td className="text-xs">{transitionOf(item)}</td>
                          <td>
                            <button
                              type="button"
                              data-testid="row-expand"
                              className="btn btn-ghost px-2 py-1 text-xs"
                              onClick={() => setExpandedId(expanded ? null : id)}
                              aria-label="Toggle row details"
                            >
                              {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                            </button>
                          </td>
                        </tr>
                        {expanded && (
                          <tr>
                            <td colSpan={6} data-testid="row-details" className="bg-slate-50">
                              <div className="grid gap-2 p-3 text-xs md:grid-cols-2">
                                <div>Action: <strong>{actionOf(item)}</strong></div>
                                <div>Entity: <strong>{item.entity_id}</strong></div>
                                <div>Actor: <strong>{userOf(item)}</strong></div>
                                <div>Previous status: <strong>{valueOrDash(item.old_status ?? item.old_value?.status)}</strong></div>
                                <div>New status: <strong>{valueOrDash(item.new_status ?? item.new_value?.status)}</strong></div>
                                <div>Sync status: <strong>{statusOf(item)}</strong></div>
                                <div>Synced at: <strong>{valueOrDash(item.synced_at)}</strong></div>
                                <div>Target system: <strong>{valueOrDash(item.target_system)}</strong></div>
                                <div>Retry count: <strong>{valueOrDash(item.retry_count ?? item.attempt_count ?? 0)}</strong></div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div data-testid="pagination" className="flex items-center justify-between border-t border-slate-200 px-4 py-3">
          <button
            type="button"
            data-testid="pagination-prev"
            className="btn btn-ghost text-xs"
            disabled={changelog.page <= 1}
            onClick={() => changelog.setPage(Math.max(1, changelog.page - 1))}
          >
            Previous
          </button>
          <span className="text-xs text-slate-500">Page {changelog.page} / {changelog.pageCount}</span>
          <button
            type="button"
            data-testid="pagination-next"
            className="btn btn-ghost text-xs"
            disabled={changelog.page >= changelog.pageCount}
            onClick={() => changelog.setPage(Math.min(changelog.pageCount, changelog.page + 1))}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
