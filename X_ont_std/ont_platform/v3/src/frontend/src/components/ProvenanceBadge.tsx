"use client";
import type { OntologyProvenance } from "@/types/api";

interface ProvenanceBadgeProps {
  provenance: OntologyProvenance | null | undefined;
  compact?: boolean;
}

export function ProvenanceBadge({ provenance, compact = false }: ProvenanceBadgeProps) {
  if (!provenance) return null;

  const pct = Math.round(provenance.confidence * 100);
  const colorClass = pct >= 90 ? "bg-green-100 text-green-700 border-green-200"
    : pct >= 70 ? "bg-yellow-100 text-yellow-700 border-yellow-200"
    : "bg-red-100 text-red-700 border-red-200";

  if (compact) {
    return (
      <span className={`inline-flex items-center text-xs rounded px-1.5 py-0.5 border ${colorClass}`}>
        {pct}%
      </span>
    );
  }

  return (
    <div className={`inline-flex items-center gap-1.5 text-xs rounded px-2 py-1 border ${colorClass}`}>
      <span>출처:</span>
      {provenance.source_doc_id && <span>{provenance.source_doc_id}</span>}
      {provenance.source_page != null && <span>p.{provenance.source_page}</span>}
      <span>·</span>
      <span>신뢰도 {pct}%</span>
      {provenance.extracted_by && <span className="text-slate-400">({provenance.extracted_by})</span>}
    </div>
  );
}
