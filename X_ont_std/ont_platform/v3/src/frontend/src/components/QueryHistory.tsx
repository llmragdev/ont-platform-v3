"use client";

import { RotateCcw, Star } from "lucide-react";
import type { SparqlHistoryItem } from "@/types/api";

export function QueryHistory({
  history,
  onSelect,
  onClear,
}: {
  history: SparqlHistoryItem[];
  onSelect: (query: string) => void;
  onClear: () => void;
}) {
  return (
    <section data-testid="query-history" className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">쿼리 히스토리</h3>
        <button type="button" className="btn btn-ghost py-1 text-xs gap-1" onClick={onClear}>
          <RotateCcw className="h-3.5 w-3.5" />
          Reset
        </button>
      </div>
      <div className="panel-body p-0">
        {history.length === 0 ? (
          <div className="p-4 text-sm text-slate-400">최근 실행한 쿼리가 없습니다.</div>
        ) : (
          <div className="max-h-[300px] overflow-auto divide-y divide-slate-100">
            {history.map((item, index) => (
              <button
                key={item.id}
                type="button"
                data-testid="history-item"
                className="block w-full px-4 py-3 text-left hover:bg-slate-50"
                onClick={() => onSelect(item.query)}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                    {index < 3 && <Star className="h-3 w-3 fill-amber-300 text-amber-400" />}
                    {item.queryType}
                  </span>
                  <span className={`badge ${item.status === "success" ? "badge-low" : "badge-medium"}`}>
                    {item.durationMs}ms · {item.rowCount}
                  </span>
                </div>
                <div className="mt-1 truncate font-mono text-xs text-slate-500">{item.query}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
