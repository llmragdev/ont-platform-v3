"use client";

import { Network, Pointer } from "lucide-react";
import { useMemo, useState } from "react";
import type { SparqlQueryResponse } from "@/types/api";

interface GraphNode {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
}

interface GraphEdge {
  id: string;
  from: string;
  to: string;
  label: string;
}

const TYPE_STYLES: Record<string, { fill: string; stroke: string; text: string }> = {
  Project: { fill: "#eff6ff", stroke: "#3b82f6", text: "#1d4ed8" },
  Person: { fill: "#f0fdfa", stroke: "#14b8a6", text: "#0f766e" },
  Supplier: { fill: "#fef3c7", stroke: "#f59e0b", text: "#b45309" },
  Drawing: { fill: "#f5f3ff", stroke: "#8b5cf6", text: "#6d28d9" },
  Equipment: { fill: "#fff1f2", stroke: "#f43f5e", text: "#be123c" },
  Entity: { fill: "#f8fafc", stroke: "#64748b", text: "#334155" },
};

function styleFor(type: string) {
  return TYPE_STYLES[type] ?? TYPE_STYLES.Entity;
}

function stringValue(value: unknown): string {
  if (value && typeof value === "object" && "value" in value) {
    return String((value as { value?: unknown }).value ?? "");
  }
  return String(value ?? "");
}

function buildGraph(result: SparqlQueryResponse | null): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodeMap = new Map<string, GraphNode>();
  const edges: GraphEdge[] = [];

  const addNode = (id: string, type = "Entity") => {
    if (!id || nodeMap.has(id)) return;
    const index = nodeMap.size;
    const angle = (index / Math.max(1, 8)) * Math.PI * 2;
    const radius = 165;
    nodeMap.set(id, {
      id,
      label: id.replace(/^entity:/, "").replace(/^.*\//, ""),
      type,
      x: 240 + Math.cos(angle) * radius,
      y: 190 + Math.sin(angle) * radius,
    });
  };

  result?.triples?.forEach((triple, index) => {
    addNode(triple.subject);
    addNode(triple.object);
    edges.push({
      id: `triple-${index}`,
      from: triple.subject,
      to: triple.object,
      label: triple.predicate.replace(/^.*[#/:]/, ""),
    });
  });

  result?.results?.forEach((row, index) => {
    const values = Object.fromEntries(Object.entries(row).map(([key, value]) => [key, stringValue(value)]));
    const entity = values.entity ?? values.x ?? values.subject ?? values.s;
    const target = values.target ?? values.object ?? values.o;
    const relation = values.relation ?? values.predicate ?? values.p ?? "related";
    const type = values.type ?? "Entity";
    if (entity) addNode(entity, type);
    if (entity && target) {
      addNode(target);
      edges.push({ id: `row-${index}`, from: entity, to: target, label: relation });
    }
  });

  return { nodes: Array.from(nodeMap.values()).slice(0, 24), edges: edges.slice(0, 32) };
}

export function EntityGraph({ result }: { result: SparqlQueryResponse | null }) {
  const { nodes, edges } = useMemo(() => buildGraph(result), [result]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const selectedNode = selectedId ? nodeById.get(selectedId) ?? null : null;
  const relatedEdges = selectedId
    ? edges.filter((edge) => edge.from === selectedId || edge.to === selectedId)
    : [];

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Network className="h-4 w-4 text-slate-500" />
          Graph View
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>{nodes.length} nodes · {edges.length} edges</span>
          <span className="inline-flex items-center gap-1">
            <Pointer className="h-3.5 w-3.5" />
            click node
          </span>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_260px]">
        <div className="relative h-[420px] overflow-hidden">
        {nodes.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            관계형 결과가 있으면 그래프로 표시됩니다.
          </div>
        ) : (
          <svg className="h-full w-full" viewBox="0 0 480 380" role="img" aria-label="SPARQL result graph">
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
              </marker>
            </defs>
            {edges.map((edge) => {
              const from = nodeById.get(edge.from);
              const to = nodeById.get(edge.to);
              if (!from || !to) return null;
              const midX = (from.x + to.x) / 2;
              const midY = (from.y + to.y) / 2;
              const highlighted = selectedId === edge.from || selectedId === edge.to;
              return (
                <g key={edge.id}>
                  <line
                    x1={from.x}
                    y1={from.y}
                    x2={to.x}
                    y2={to.y}
                    stroke={highlighted ? "#2563eb" : "#94a3b8"}
                    strokeWidth={highlighted ? "2.5" : "1.5"}
                    markerEnd="url(#arrow)"
                  />
                  <text x={midX} y={midY - 4} textAnchor="middle" fontSize="10" fill={highlighted ? "#1d4ed8" : "#64748b"}>
                    {edge.label}
                  </text>
                </g>
              );
            })}
            {nodes.map((node) => {
              const style = styleFor(node.type);
              const selected = selectedId === node.id;
              return (
              <g
                key={node.id}
                role="button"
                tabIndex={0}
                className="cursor-pointer"
                onClick={() => setSelectedId(selected ? null : node.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") setSelectedId(selected ? null : node.id);
                }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={selected ? "32" : "28"}
                  fill={style.fill}
                  stroke={selected ? "#111827" : style.stroke}
                  strokeWidth={selected ? "3" : "2"}
                />
                <text x={node.x} y={node.y - 3} textAnchor="middle" fontSize="9" fontWeight="700" fill={style.text}>
                  {node.type.slice(0, 10)}
                </text>
                <text x={node.x} y={node.y + 10} textAnchor="middle" fontSize="9" fill="#334155">
                  {node.label.slice(0, 14)}
                </text>
              </g>
            );})}
          </svg>
        )}
        </div>

        <aside className="border-t border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 lg:border-l lg:border-t-0">
          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Selected Node</div>
                <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">{selectedNode.label}</div>
                <div className="mt-1 break-all font-mono text-xs text-slate-500">{selectedNode.id}</div>
                <span className="mt-2 inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                  {selectedNode.type}
                </span>
              </div>

              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                  Related Edges ({relatedEdges.length})
                </div>
                <div className="mt-2 space-y-2">
                  {relatedEdges.length === 0 && <div className="text-xs text-slate-400">연결된 관계가 없습니다.</div>}
                  {relatedEdges.map((edge) => (
                    <div key={edge.id} className="rounded-md border border-slate-200 bg-slate-50 p-2 text-xs dark:border-slate-800 dark:bg-slate-950">
                      <div className="font-semibold text-blue-700 dark:text-blue-300">{edge.label}</div>
                      <div className="mt-1 break-all text-slate-500">
                        {edge.from === selectedId ? "out" : "in"} · {edge.from} → {edge.to}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-full min-h-40 items-center justify-center text-center text-xs text-slate-400">
              노드를 선택하면 상세 정보와 관계가 표시됩니다.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
