"use client";

import type { RDFGraphData } from "@/types/rdf";

export function RDFGraphStats({ data, maxVisibleNodes }: { data: RDFGraphData; maxVisibleNodes: number }) {
  const degreeMap = new Map<string, number>();
  data.nodes.forEach((node) => degreeMap.set(node.id, 0));
  data.edges.forEach((edge) => {
    degreeMap.set(edge.source, (degreeMap.get(edge.source) ?? 0) + 1);
    degreeMap.set(edge.target, (degreeMap.get(edge.target) ?? 0) + 1);
  });
  const highDegree = [...degreeMap.entries()]
    .map(([id, degree]) => ({ id, degree, label: data.nodes.find((node) => node.id === id)?.label ?? id }))
    .sort((a, b) => b.degree - a.degree)
    .slice(0, 5);

  return (
    <section data-testid="rdf-graph-stats" className="panel">
      <div className="panel-header">
        <h3 className="text-sm font-semibold">Graph statistics</h3>
        <span className="badge badge-neutral">limit {maxVisibleNodes}</span>
      </div>
      <div className="panel-body space-y-3 text-sm">
        <div className="grid grid-cols-3 gap-2">
          <div>
            <div className="text-xs font-semibold uppercase text-slate-500">Nodes</div>
            <div className="text-xl font-bold">{data.nodes.length}</div>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase text-slate-500">Edges</div>
            <div className="text-xl font-bold">{data.edges.length}</div>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase text-slate-500">Headroom</div>
            <div className="text-xl font-bold">{Math.max(0, maxVisibleNodes - data.nodes.length)}</div>
          </div>
        </div>
        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-slate-500">High-degree nodes</div>
          <div className="space-y-1">
            {highDegree.map((node) => (
              <div key={node.id} data-testid="high-degree-node" className="flex items-center justify-between rounded-md bg-slate-50 px-2 py-1 text-xs">
                <span className="truncate">{node.label}</span>
                <span className="badge badge-neutral">{node.degree}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
