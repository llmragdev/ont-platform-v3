"use client";

import { useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { SparqlHistoryItem, SparqlQueryResponse } from "@/types/api";

const HISTORY_KEY = "ont_platform_sparql_history_v1";
const ENABLE_DEMO_FALLBACK = process.env.NEXT_PUBLIC_ENABLE_SPARQL_DEMO_FALLBACK === "true";

function detectQueryType(query: string): string {
  const normalized = query
    .replace(/#[^\n\r]*/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toUpperCase();
  const match = normalized.match(/\b(SELECT|ASK|CONSTRUCT|DESCRIBE)\b/);
  return match?.[1] ?? "UNKNOWN";
}

function countRows(result: SparqlQueryResponse | null): number {
  if (!result) return 0;
  if (Array.isArray(result.results)) return result.results.length;
  if (Array.isArray(result.bindings)) return result.bindings.length;
  if (Array.isArray(result.triples)) return result.triples.length;
  if (typeof result.result_count === "number") return result.result_count;
  if (typeof result.count === "number") return result.count;
  if (typeof result.boolean === "boolean") return 1;
  return 0;
}

function demoResponse(query: string, durationMs: number): SparqlQueryResponse {
  const type = detectQueryType(query);
  if (type === "ASK") {
    return {
      type: "ASK",
      boolean: true,
      query_time_ms: durationMs,
      translator_used: false,
      source: "demo",
      warning: "Backend SPARQL endpoint is not ready; showing demo output.",
    };
  }

  return {
    type: "SELECT",
    query_time_ms: durationMs,
    translator_used: false,
    source: "demo",
    warning: "Backend SPARQL endpoint is not ready; showing demo output.",
    sql_generated:
      "SELECT e.id, e.entity_type, e.properties FROM entities e WHERE e.domain_id = $1 LIMIT 10",
    results: [
      {
        entity: { type: "uri", value: "entity:project-alpha" },
        type: { type: "literal", value: "Project" },
        name: { type: "literal", value: "Project Alpha" },
      },
      {
        entity: { type: "uri", value: "entity:supplier-42" },
        type: { type: "literal", value: "Supplier" },
        name: { type: "literal", value: "Daehan Materials" },
      },
      {
        entity: { type: "uri", value: "entity:drawing-a17" },
        type: { type: "literal", value: "Drawing" },
        name: { type: "literal", value: "Hull Block A17" },
      },
    ],
  };
}

function loadHistory(): SparqlHistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    return raw ? (JSON.parse(raw) as SparqlHistoryItem[]) : [];
  } catch {
    return [];
  }
}

function saveHistory(items: SparqlHistoryItem[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, 20)));
}

export function useSparqlQuery() {
  const [result, setResult] = useState<SparqlQueryResponse | null>(null);
  const [history, setHistory] = useState<SparqlHistoryItem[]>(() => loadHistory());
  const [error, setError] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const stats = useMemo(() => {
    const successful = history.filter((item) => item.status === "success");
    const average = successful.length
      ? Math.round(successful.reduce((sum, item) => sum + item.durationMs, 0) / successful.length)
      : 0;
    return {
      total: history.length,
      successCount: successful.length,
      averageMs: average,
      latest: history[0],
    };
  }, [history]);

  async function execute(query: string) {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setResult(null);
    const startedAt = performance.now();
    let response: SparqlQueryResponse | null = null;
    let status: SparqlHistoryItem["status"] = "success";

    try {
      response = await api.sparql.query(trimmed, controller.signal);
    } catch (err) {
      if (controller.signal.aborted) {
        setLoading(false);
        return;
      }
      const elapsed = Math.round(performance.now() - startedAt);
      setError(err instanceof Error ? err.message : String(err));
      status = "error";
      response = ENABLE_DEMO_FALLBACK ? demoResponse(trimmed, elapsed) : null;
    } finally {
      const elapsed = Math.round(performance.now() - startedAt);
      const finalResponse = response ? { ...response, query_time_ms: response.query_time_ms ?? elapsed } : null;
      setResult(finalResponse);
      setDurationMs(elapsed);
      setLoading(false);

      const nextItem: SparqlHistoryItem = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        query: trimmed,
        timestamp: new Date().toISOString(),
        durationMs: elapsed,
        rowCount: countRows(finalResponse),
        status,
        queryType: detectQueryType(trimmed),
      };
      setHistory((prev) => {
        const next = [nextItem, ...prev].slice(0, 20);
        saveHistory(next);
        return next;
      });
    }
  }

  function cancel() {
    abortRef.current?.abort();
    setLoading(false);
  }

  function clearHistory() {
    setHistory([]);
    saveHistory([]);
  }

  return {
    result,
    history,
    stats,
    error,
    durationMs,
    loading,
    execute,
    cancel,
    clearHistory,
  };
}
