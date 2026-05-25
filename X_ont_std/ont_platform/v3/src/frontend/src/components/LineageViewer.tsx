"use client";

import { GitBranch, Loader2, Network } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { fallbackImpact, fallbackLineage } from "@/lib/metadata-mock";
import type { ImpactInfo, LineageInfo } from "@/types/metadata";

function statusClass(status: string): string {
  if (status === "completed") return "badge-low";
  if (status === "failed") return "badge-high";
  return "badge-medium";
}

export function LineageViewer({
  entityId,
  onEntityClick,
}: {
  entityId: string;
  onEntityClick?: (entityId: string) => void;
}) {
  const [lineage, setLineage] = useState<LineageInfo | null>(null);
  const [impact, setImpact] = useState<ImpactInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setUsingMock(false);
      try {
        const [lineageRes, impactRes] = await Promise.all([
          api.metadata.getLineage(entityId),
          api.metadata.getImpact(entityId),
        ]);
        if (!cancelled) {
          setLineage(lineageRes);
          setImpact(impactRes);
        }
      } catch {
        if (!cancelled) {
          setLineage(fallbackLineage(entityId));
          setImpact(fallbackImpact(entityId));
          setUsingMock(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [entityId]);

  return (
    <section data-testid="lineage-viewer" className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-emerald-600" />
          <h3 className="text-sm font-semibold">Lineage Viewer</h3>
        </div>
        {loading && <Loader2 className="h-4 w-4 animate-spin text-slate-400" />}
      </div>

      <div className="panel-body space-y-4">
        {usingMock && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            Using mock lineage until the v4 API is available.
          </div>
        )}

        {lineage && (
          <>
            <div>
              <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Source Entities</div>
              <div className="flex flex-wrap gap-2">
                {lineage.source_entities.map((source) => (
                  <button
                    key={source}
                    type="button"
                    className="rounded-md border border-slate-200 bg-white px-2 py-1 font-mono text-xs text-slate-700 hover:bg-slate-50"
                    onClick={() => onEntityClick?.(source)}
                  >
                    {source}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {lineage.transformations.map((transformation, index) => (
                <div key={transformation.transformation_id} className="grid grid-cols-[28px_1fr] gap-3">
                  <div className="flex flex-col items-center">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700">
                      {index + 1}
                    </div>
                    {index < lineage.transformations.length - 1 && <div className="h-full w-px bg-slate-200" />}
                  </div>
                  <div className="rounded-md border border-slate-200 bg-white p-3">
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Network className="h-4 w-4 text-slate-400" />
                        <span className="text-sm font-semibold">{transformation.operation_type}</span>
                      </div>
                      <span className={`badge ${statusClass(transformation.status)}`}>{transformation.status}</span>
                    </div>
                    <div className="grid gap-2 text-xs md:grid-cols-2">
                      <div>
                        <span className="text-slate-500">Input: </span>
                        {transformation.input_entity_ids.map((id) => (
                          <button key={id} type="button" className="mr-1 font-mono text-blue-600" onClick={() => onEntityClick?.(id)}>
                            {id}
                          </button>
                        ))}
                      </div>
                      <div>
                        <span className="text-slate-500">Output: </span>
                        <button type="button" className="font-mono text-blue-600" onClick={() => onEntityClick?.(transformation.output_entity_id)}>
                          {transformation.output_entity_id}
                        </button>
                      </div>
                      <div>By {transformation.performed_by}</div>
                      <div>{new Date(transformation.performed_at).toLocaleString()}</div>
                    </div>
                    <pre className="mt-2 overflow-auto rounded-md bg-slate-50 p-2 text-[11px] text-slate-600">
                      {JSON.stringify(transformation.transformation_rule, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>

            <div>
              <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Quality Chain</div>
              <div className="flex flex-wrap items-center gap-2">
                {lineage.data_quality_chain.map((score, index) => (
                  <div key={`${score}-${index}`} className="flex items-center gap-2">
                    <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">{score}</span>
                    {index < lineage.data_quality_chain.length - 1 && <span className="text-slate-300">-&gt;</span>}
                  </div>
                ))}
              </div>
            </div>

            {impact && (
              <div>
                <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Impact Radius</div>
                <div className="grid gap-2 md:grid-cols-3">
                  {impact.affected_entities.map((entity) => (
                    <button
                      key={entity.id}
                      type="button"
                      className="rounded-md border border-slate-200 bg-white px-3 py-2 text-left hover:bg-slate-50"
                      onClick={() => onEntityClick?.(entity.id)}
                    >
                      <div className="text-sm font-semibold">{entity.name}</div>
                      <div className="font-mono text-xs text-slate-500">{entity.id} / {entity.type}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
