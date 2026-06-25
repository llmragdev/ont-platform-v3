"use client";

import { AlertTriangle, Filter, RefreshCw, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { mockDLQItems, mockWriteBackStatistics } from "@/lib/writeback-mock";
import type { DLQFilters, DLQItem, WriteBackStatistics } from "@/types/writeback";
import { DLQDetailModal } from "./DLQDetailModal";
import { DLQItemTable } from "./DLQItemTable";

const ERROR_TYPES = ["Max retries exceeded", "Permission denied", "Validation failed", "Timeout"];

function contains(value: string | null | undefined, needle: string | undefined): boolean {
  if (!needle) return true;
  return (value ?? "").toLowerCase().includes(needle.toLowerCase());
}

function withinDate(value: string | null | undefined, from?: string, to?: string): boolean {
  if (!value) return true;
  const time = new Date(value).getTime();
  if (from && time < new Date(`${from}T00:00:00`).getTime()) return false;
  if (to && time > new Date(`${to}T23:59:59`).getTime()) return false;
  return true;
}

function applyFilters(items: DLQItem[], filters: DLQFilters): DLQItem[] {
  return items.filter((item) =>
    contains(item.target_system, filters.targetSystem) &&
    contains(`${item.dlq_reason ?? ""} ${item.error_message ?? ""}`, filters.errorType) &&
    withinDate(item.dlq_at, filters.dateFrom, filters.dateTo)
  );
}

function recentCount(items: DLQItem[]): number {
  const oneHourAgo = Date.now() - 60 * 60 * 1000;
  return items.filter((item) => item.dlq_at && new Date(item.dlq_at).getTime() >= oneHourAgo).length;
}

export function DLQDashboard() {
  const [items, setItems] = useState<DLQItem[]>([]);
  const [stats, setStats] = useState<WriteBackStatistics | null>(null);
  const [filters, setFilters] = useState<DLQFilters>({});
  const [selected, setSelected] = useState<DLQItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("-");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [dlqResponse, statistics] = await Promise.all([
        api.writeback.getDLQItems(),
        api.writeback.getWritebackStatistics(),
      ]);
      setItems(dlqResponse.items);
      setStats(statistics);
      setError(null);
    } catch (err) {
      setItems(mockDLQItems);
      setStats(mockWriteBackStatistics);
      setError(err instanceof Error ? `백엔드 연결 실패로 데모 데이터를 표시합니다: ${err.message}` : "데모 데이터를 표시합니다.");
    } finally {
      setLastUpdated(new Date().toLocaleTimeString());
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 5000);
    return () => window.clearInterval(timer);
  }, [load]);

  const filteredItems = useMemo(() => applyFilters(items, filters), [items, filters]);
  const maxRetryCount = filteredItems.filter((item) => item.retry_count >= 3).length;

  function updateFilter(key: keyof DLQFilters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  }

  return (
    <section data-testid="dlq-dashboard" className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">DLQ items</div>
          <div data-testid="dlq-count" className="mt-2 text-2xl font-bold text-rose-700">{filteredItems.length}</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">Max retries</div>
          <div className="mt-2 text-2xl font-bold text-amber-700">{maxRetryCount}</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">Recent DLQ</div>
          <div className="mt-2 text-2xl font-bold text-blue-700">{recentCount(filteredItems)}</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase text-slate-500">Queue total</div>
          <div className="mt-2 text-2xl font-bold text-slate-800 dark:text-slate-100">{stats?.total ?? filteredItems.length}</div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <h3 className="text-sm font-semibold">Writeback DLQ 관리</h3>
          </div>
          <div className="flex items-center gap-2">
            <span data-testid="last-updated" className="text-xs text-slate-500">마지막 갱신 {lastUpdated}</span>
            <button type="button" data-testid="dlq-refresh" className="btn btn-ghost text-xs" onClick={() => void load()}>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
              Refresh
            </button>
          </div>
        </div>
        <div className="panel-body grid gap-3 md:grid-cols-6">
          <select
            data-testid="filter-target-system"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
            value={filters.targetSystem ?? ""}
            onChange={(event) => updateFilter("targetSystem", event.target.value)}
          >
            <option value="">All systems</option>
            <option value="SAP">SAP</option>
            <option value="ERP">ERP</option>
            <option value="CRM">CRM</option>
          </select>
          <input
            data-testid="filter-date-from"
            type="date"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
            value={filters.dateFrom ?? ""}
            onChange={(event) => updateFilter("dateFrom", event.target.value)}
          />
          <input
            data-testid="filter-date-to"
            type="date"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
            value={filters.dateTo ?? ""}
            onChange={(event) => updateFilter("dateTo", event.target.value)}
          />
          <select
            data-testid="filter-error-type"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
            value={filters.errorType ?? ""}
            onChange={(event) => updateFilter("errorType", event.target.value)}
          >
            <option value="">All errors</option>
            {ERROR_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
          <button
            type="button"
            data-testid="filter-reset"
            className="btn btn-ghost md:col-span-2"
            onClick={() => setFilters({})}
          >
            <RotateCcw className="mr-1.5 h-4 w-4" />
            필터 초기화
          </button>
        </div>
        {error && (
          <div data-testid="dlq-error" className="mx-4 mb-4 flex items-center gap-2 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}
      </div>

      <div className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">DLQ 아이템 리스트</h3>
          <span className="text-xs text-slate-500">{filteredItems.length} records</span>
        </div>
        <div className="panel-body p-0">
          <DLQItemTable
            items={filteredItems}
            loading={loading}
            onReplaySuccess={() => void load()}
            onSelectItem={setSelected}
          />
        </div>
      </div>

      <DLQDetailModal item={selected} onClose={() => setSelected(null)} />
    </section>
  );
}
