"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ChangelogEntry, ChangelogFilters, ChangelogHistoryResponse } from "@/types/changelog";

const PAGE_SIZE = 50;

export function useChangelog(initialFilters: ChangelogFilters = {}) {
  const [filters, setFilters] = useState<ChangelogFilters>(initialFilters);
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<ChangelogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<ChangelogHistoryResponse["stats"]>();

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.domainId) params.set("domain_id", filters.domainId);
    if (filters.entityId) params.set("entity_id", filters.entityId);
    if (filters.actionType) params.set("action_type", filters.actionType);
    if (filters.user) params.set("user", filters.user);
    if (filters.syncStatus) params.set("sync_status", filters.syncStatus);
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));
    return params.toString();
  }, [filters, page]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/changelog/history?${queryString}`, { cache: "no-store" });
      const data = (await response.json().catch(() => ({}))) as ChangelogHistoryResponse;
      if (!response.ok) throw new Error((data as any)?.detail ?? (data as any)?.error?.message ?? response.statusText);

      const nextItems = data.items ?? data.changelogs ?? [];
      setItems(nextItems);
      setTotal(data.total ?? nextItems.length);
      setStats(data.stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setItems([]);
      setTotal(0);
      setStats(undefined);
    } finally {
      setLoading(false);
    }
  }, [queryString]);

  useEffect(() => {
    void load();
  }, [load]);

  function applyFilters(nextFilters: ChangelogFilters) {
    setPage(1);
    setFilters(nextFilters);
  }

  return {
    items,
    total,
    page,
    pageSize: PAGE_SIZE,
    pageCount: Math.max(1, Math.ceil(total / PAGE_SIZE)),
    loading,
    error,
    stats,
    filters,
    setPage,
    applyFilters,
    reload: load,
  };
}
