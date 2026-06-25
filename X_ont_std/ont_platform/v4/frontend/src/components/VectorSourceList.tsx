"use client";

interface VectorSource {
  source_type: string;
  citation?: string;
  doc_id?: string;
  filename?: string;
  page?: number;
  score?: number;
  text?: string;
}

interface VectorSourceListProps {
  sources: VectorSource[];
}

export function VectorSourceList({ sources }: VectorSourceListProps) {
  const vectorSources = sources.filter((s) => s.source_type === "vector");
  if (vectorSources.length === 0) return null;

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">문서 출처</h3>
        <span className="badge badge-neutral">{vectorSources.length}건</span>
      </div>
      <div className="panel-body divide-y divide-slate-100">
        {vectorSources.map((s, i) => (
          <div key={i} className="py-2.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-700">
                {s.filename || s.doc_id || "문서"}
                {s.page != null && <span className="text-slate-400 ml-1">p.{s.page}</span>}
              </span>
              {s.score != null && (
                <span className="text-xs text-slate-500">score {s.score.toFixed(3)}</span>
              )}
            </div>
            {s.text && (
              <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">{s.text}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
