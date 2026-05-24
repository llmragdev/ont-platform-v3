"use client";

import type { SparqlHistoryItem } from "@/types/api";

const TARGETS = [
  { label: "Lookup", ms: 50, className: "bg-emerald-500" },
  { label: "One-hop", ms: 300, className: "bg-blue-500" },
  { label: "Two-hop", ms: 1000, className: "bg-amber-500" },
];

function toneFor(ms: number): string {
  if (ms <= 50) return "bg-emerald-500";
  if (ms <= 300) return "bg-blue-500";
  if (ms <= 1000) return "bg-amber-500";
  return "bg-rose-500";
}

export function PerformanceChart({ history }: { history: SparqlHistoryItem[] }) {
  const items = history.slice(0, 20).reverse();
  const maxMs = Math.max(1000, ...items.map((item) => item.durationMs));
  const averageMs = items.length
    ? Math.round(items.reduce((sum, item) => sum + item.durationMs, 0) / items.length)
    : 0;

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">응답 시간</h3>
        <span className="text-xs text-slate-500">최근 {items.length}개 평균 {averageMs}ms</span>
      </div>
      <div className="panel-body space-y-4">
        <div className="flex items-center gap-2 text-[11px] text-slate-500">
          {TARGETS.map((target) => (
            <span key={target.label} className="inline-flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${target.className}`} />
              {target.label} {target.ms}ms
            </span>
          ))}
        </div>

        <div className="h-32 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 flex items-end gap-1 overflow-hidden">
          {items.length === 0 && (
            <div className="m-auto text-xs text-slate-400">쿼리를 실행하면 성능 히스토리가 표시됩니다.</div>
          )}
          {items.map((item) => {
            const height = Math.max(6, Math.round((item.durationMs / maxMs) * 110));
            return (
              <div key={item.id} className="flex-1 min-w-[6px] flex flex-col items-center justify-end gap-1">
                <div
                  className={`w-full rounded-t ${toneFor(item.durationMs)}`}
                  style={{ height }}
                  title={`${item.queryType}: ${item.durationMs}ms`}
                />
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-3 gap-2">
          {TARGETS.map((target) => {
            const count = history.filter((item) => item.durationMs <= target.ms).length;
            return (
              <div key={target.label} className="rounded-md border border-slate-200 bg-white px-3 py-2">
                <div className="text-[11px] text-slate-500">{target.label}</div>
                <div className="mt-1 text-lg font-semibold text-slate-900">{count}</div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
