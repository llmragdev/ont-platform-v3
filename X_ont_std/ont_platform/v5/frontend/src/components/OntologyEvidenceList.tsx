"use client";
import type { OntologyEvidence } from "@/types/api";

interface OntologyEvidenceListProps {
  evidence: OntologyEvidence[];
}

export function OntologyEvidenceList({ evidence }: OntologyEvidenceListProps) {
  if (!evidence || evidence.length === 0) return null;

  return (
    <section className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">온톨로지 근거</h3>
        <span className="badge badge-neutral">{evidence.length}건</span>
      </div>
      <div className="panel-body divide-y divide-slate-100">
        {evidence.map((e, i) => (
          <div key={i} className="py-2.5 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs bg-slate-100 text-slate-600 rounded px-1.5 py-0.5 font-mono">
                {e.node_type}
              </span>
              <span className="text-sm font-medium">{e.label}</span>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-slate-500">
              {e.source_doc_id && <span>출처: {e.source_doc_id}</span>}
              {e.source_page != null && <span>· p.{e.source_page}</span>}
              <span>· 신뢰도 {Math.round(e.confidence * 100)}%</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
