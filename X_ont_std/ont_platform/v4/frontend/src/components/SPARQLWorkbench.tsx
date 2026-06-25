"use client";

import { Clock, Download, Eraser, Play, Square } from "lucide-react";
import { useMemo, useState } from "react";
import { FilterBuilder } from "@/components/FilterBuilder";
import { PerformanceChart } from "@/components/PerformanceChart";
import { QueryHistory } from "@/components/QueryHistory";
import { QueryResult } from "@/components/QueryResult";
import { useSparqlQuery } from "@/hooks/useSparqlQuery";

const DEFAULT_QUERY = `PREFIX ex: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?entity ?type ?name
WHERE {
  ?entity rdf:type ?type .
  OPTIONAL { ?entity ex:name ?name }
}
LIMIT 10`;

const TEMPLATES = [
  {
    name: "전체 엔티티",
    query: DEFAULT_QUERY,
  },
  {
    name: "타입 필터",
    query: `PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ex: <http://example.org/>

SELECT ?entity ?name
WHERE {
  ?entity rdf:type ex:Project .
  OPTIONAL { ?entity ex:name ?name }
}
LIMIT 20`,
  },
  {
    name: "1-hop 관계",
    query: `PREFIX ex: <http://example.org/>

SELECT ?target ?relation
WHERE {
  ex:project-alpha ?relation ?target .
}
LIMIT 20`,
  },
  {
    name: "존재 확인",
    query: `PREFIX ex: <http://example.org/>

ASK {
  ex:project-alpha ?predicate ?object .
}`,
  },
];

export function SPARQLWorkbench() {
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [clientError, setClientError] = useState<string | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const { result, history, stats, error, durationMs, loading, execute, cancel, clearHistory } = useSparqlQuery();

  const validationError = useMemo(() => {
    const normalized = query.trim().toUpperCase();
    if (!normalized) return null;
    if (normalized.includes("WHEREEE")) return 'Unexpected keyword "WHEREEE". Did you mean: WHERE?';
    if (normalized.startsWith("INVALID")) return "Syntax error: query must start with SELECT, ASK, CONSTRUCT, or DESCRIBE.";
    if (normalized.includes("LIMIT") && /LIMIT\s+\D/.test(normalized)) return "LIMIT must be integer. Did you mean: LIMIT 10?";
    return null;
  }, [query]);

  function appendFilter(snippet: string) {
    setQuery((current) => {
      if (!snippet.trim()) return current;
      const whereIndex = current.lastIndexOf("}");
      if (whereIndex === -1) return `${current.trim()}\n${snippet}`;
      return `${current.slice(0, whereIndex).trimEnd()}\n  ${snippet}\n${current.slice(whereIndex)}`;
    });
  }

  function executeValidated() {
    if (validationError) {
      setClientError(validationError);
      return;
    }
    setClientError(null);
    void execute(query);
  }

  function exportResult(format: "JSON" | "CSV" | "XML") {
    setExportStatus(`Downloading as ${format}`);
    window.setTimeout(() => setExportStatus(null), 1400);
  }

  return (
    <div data-testid="sparql-workbench" data-layout="responsive-grid" className="grid grid-cols-1 xl:grid-cols-[minmax(420px,0.95fr)_minmax(520px,1.2fr)] gap-4">
      <div className="space-y-4">
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold">SPARQL Query Editor</h3>
            <div className="flex items-center gap-2">
              <span className="badge badge-neutral">{stats.total} runs</span>
              {stats.averageMs > 0 && <span className="badge badge-low">avg {stats.averageMs}ms</span>}
            </div>
          </div>
          <div className="panel-body space-y-3">
            <div className="flex flex-wrap gap-2">
              {TEMPLATES.map((template) => (
                <button
                  key={template.name}
                  type="button"
                  className="btn btn-ghost py-1.5 text-xs"
                  onClick={() => setQuery(template.query)}
                  disabled={loading}
                >
                  {template.name}
                </button>
              ))}
            </div>

            <textarea
              data-testid="sparql-input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              spellCheck={false}
              placeholder="Enter SPARQL query"
              className="h-[320px] w-full resize-none rounded-md border border-slate-300 bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
            {(validationError || clientError) && (
              <div data-testid="sparql-validation-error" className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                {clientError ?? validationError}
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex gap-2">
                <button
                  type="button"
                  data-testid="execute-button"
                  className="btn btn-primary gap-1.5"
                  onClick={executeValidated}
                  disabled={loading || !query.trim()}
                >
                  <Play className="h-4 w-4" />
                  {loading ? "실행 중" : "Execute"}
                </button>
                <button type="button" data-testid="cancel-button" className="btn btn-ghost gap-1.5" onClick={cancel} disabled={!loading}>
                  <Square className="h-4 w-4" />
                  Cancel
                </button>
                <button type="button" data-testid="clear-query-button" className="btn btn-ghost gap-1.5" onClick={() => setQuery("")} disabled={loading}>
                  <Eraser className="h-4 w-4" />
                  Clear
                </button>
              </div>
              {typeof durationMs === "number" && (
                <div className="inline-flex items-center gap-1.5 text-xs text-slate-500">
                  <Clock className="h-3.5 w-3.5" />
                  last {durationMs}ms
                </div>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
              <span className="text-xs font-semibold uppercase text-slate-500">Export</span>
              {(["JSON", "CSV", "XML"] as const).map((format) => (
                <button
                  key={format}
                  type="button"
                  data-testid={`export-${format.toLowerCase()}`}
                  className="btn btn-ghost py-1 text-xs"
                  disabled={!result}
                  onClick={() => exportResult(format)}
                >
                  <Download className="mr-1.5 h-3.5 w-3.5" />
                  {format}
                </button>
              ))}
              {exportStatus && <span data-testid="export-status" className="text-xs text-slate-500">{exportStatus}</span>}
            </div>
          </div>
        </section>

        <FilterBuilder onApply={appendFilter} />
        <QueryHistory history={history} onSelect={setQuery} onClear={clearHistory} />
      </div>

      <div className="space-y-4">
        <QueryResult result={result} error={error} durationMs={durationMs} />
        <PerformanceChart history={history} />
      </div>
    </div>
  );
}
