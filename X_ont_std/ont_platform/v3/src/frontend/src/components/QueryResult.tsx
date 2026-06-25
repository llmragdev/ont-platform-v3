"use client";

import { AlertTriangle, Braces, CheckCircle2, Database, Table2 } from "lucide-react";
import { useMemo, useState } from "react";
import { ActionButton } from "@/components/ActionButton";
import { EntityGraph } from "@/components/EntityGraph";
import type { SparqlBindingValue, SparqlQueryResponse } from "@/types/api";

type TabKey = "table" | "json" | "graph" | "debug";

function unwrapValue(value: SparqlBindingValue | string | number | boolean | null | undefined): string {
  if (value == null) return "";
  if (typeof value === "object" && "value" in value) return String(value.value ?? "");
  return String(value);
}

function normalizeRows(result: SparqlQueryResponse | null): Array<Record<string, string>> {
  if (!result) return [];
  if (Array.isArray(result.results)) {
    return result.results.map((row) =>
      Object.fromEntries(Object.entries(row).map(([key, value]) => [key, unwrapValue(value)]))
    );
  }
  if (Array.isArray(result.bindings)) {
    return result.bindings.map((row) =>
      Object.fromEntries(Object.entries(row).map(([key, value]) => [key, unwrapValue(value)]))
    );
  }
  if (Array.isArray(result.triples)) {
    return result.triples.map((triple) => ({
      subject: triple.subject,
      predicate: triple.predicate,
      object: triple.object,
    }));
  }
  if (typeof result.boolean === "boolean") return [{ result: String(result.boolean) }];
  return [];
}

function durationTone(ms?: number): string {
  if (ms == null) return "badge-neutral";
  if (ms <= 50) return "badge-low";
  if (ms <= 300) return "bg-blue-100 text-blue-700";
  if (ms <= 1000) return "badge-medium";
  return "badge-high";
}

export function QueryResult({
  result,
  error,
  durationMs,
}: {
  result: SparqlQueryResponse | null;
  error?: string | null;
  durationMs?: number | null;
}) {
  const [tab, setTab] = useState<TabKey>("table");
  const rows = useMemo(() => normalizeRows(result), [result]);
  const columns = useMemo(() => Array.from(new Set(rows.flatMap((row) => Object.keys(row)))), [rows]);
  const displayMs = result?.query_time_ms ?? result?.execution_time_ms ?? durationMs ?? undefined;
  const queryType = result?.query_type ?? result?.type ?? "UNKNOWN";
  const sourceLabel =
    result?.source === "sql_translator" ? "SQL Translator" :
    result?.source === "rdflib" ? "rdflib Fallback" :
    result?.source === "demo" ? "Demo" : "Unknown";
  const hasActions = Boolean(result?.entity_id && result?.available_actions?.length);

  return (
    <section data-testid="query-result" className="panel min-h-[420px]">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Table2 className="h-4 w-4 text-slate-500" />
          <h3 className="text-sm font-semibold">쿼리 결과</h3>
        </div>
        <div className="flex items-center gap-2">
          {result?.source === "sql_translator" && <span className="badge badge-low">SQL</span>}
          {result?.source === "rdflib" && <span className="badge badge-medium">RDFLIB</span>}
          {result?.source === "demo" && <span className="badge badge-medium">DEMO</span>}
          {typeof displayMs === "number" && (
            <span className={`badge ${durationTone(displayMs)}`}>{displayMs}ms</span>
          )}
          <span className="text-xs text-slate-500">{rows.length} rows</span>
        </div>
      </div>

      <div className="border-b border-slate-200 px-4 pt-3">
        <div className="flex gap-1">
          {[
            { key: "table" as const, label: "Table", icon: Table2 },
            { key: "json" as const, label: "JSON", icon: Braces },
            { key: "graph" as const, label: "Graph", icon: Database },
            { key: "debug" as const, label: "Debug", icon: Database },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                type="button"
                data-testid={`result-tab-${item.key}`}
                onClick={() => setTab(item.key)}
                className={`inline-flex items-center gap-1.5 rounded-t-md px-3 py-2 text-xs font-semibold ${
                  tab === item.key ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-100"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {item.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="panel-body">
        {error && (
          <div className="mb-3 flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div className="font-semibold">API 호출 실패</div>
              <div className="text-xs">{error}</div>
            </div>
          </div>
        )}

        {(result?.warning || (result?.warnings?.length ?? 0) > 0) && (
          <div className="mb-3 flex items-start gap-2 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            <div>{result?.warning ?? result?.warnings?.join(" ")}</div>
          </div>
        )}

        {hasActions && (
          <div className="mb-4 rounded-md border border-blue-100 bg-blue-50 p-3">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="text-sm font-semibold text-slate-900">Recommended actions</div>
                <div className="text-xs text-slate-500">
                  {result?.entity_type ?? "entity"} {result?.entity_id}
                </div>
              </div>
              {result?.current_status && <span className="badge badge-medium">{result.current_status}</span>}
            </div>
            <ActionButton
              entityId={result!.entity_id!}
              entityType={result?.entity_type ?? "entity"}
              currentStatus={result?.current_status}
              availableActions={result?.available_actions ?? []}
              onSuccess={() => {
                window.dispatchEvent(new CustomEvent("query-result-action-success", { detail: result?.entity_id }));
              }}
            />
          </div>
        )}

        {tab === "table" && (
          <div data-testid="result-table-view" className="overflow-auto rounded-md border border-slate-200">
            {rows.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-400">아직 표시할 결과가 없습니다.</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={index}>
                      {columns.map((column) => (
                        <td key={column} className="max-w-[260px] truncate font-mono text-xs" title={row[column]}>
                          {row[column]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {tab === "json" && (
          <pre data-testid="result-json-view" className="max-h-[520px] overflow-auto rounded-md bg-slate-950 p-4 text-xs text-slate-100">
            {JSON.stringify(result ?? {}, null, 2)}
          </pre>
        )}

        {tab === "graph" && <div data-testid="result-graph-view"><EntityGraph result={result} /></div>}

        {tab === "debug" && (
          <div data-testid="result-debug-view" className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-md bg-slate-50 px-3 py-2">
                <div className="text-xs text-slate-500">Query Type</div>
                <div className="font-semibold">{queryType}</div>
              </div>
              <div className="rounded-md bg-slate-50 px-3 py-2">
                <div className="text-xs text-slate-500">Source</div>
                <div className="font-semibold">{sourceLabel}</div>
              </div>
            </div>
            <div>
              <div className="mb-1 text-xs font-semibold text-slate-500">Generated SQL</div>
              <pre className="overflow-auto rounded-md bg-slate-100 p-3 text-xs text-slate-700">
                {result?.sql_generated ?? "No SQL debug output."}
              </pre>
            </div>
            <div>
              <div className="mb-1 text-xs font-semibold text-slate-500">Explain</div>
              <pre className="overflow-auto rounded-md bg-slate-100 p-3 text-xs text-slate-700">
                {result?.explain ?? "No explain output."}
              </pre>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
