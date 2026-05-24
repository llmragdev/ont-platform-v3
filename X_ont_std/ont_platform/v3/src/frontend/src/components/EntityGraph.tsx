"use client";

import { Network } from "lucide-react";
import type { SparqlQueryResponse } from "@/types/api";

interface GraphNode {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
}

interface GraphEdge {
  from: string;
  to: string;
  label: string;
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

  result?.triples?.forEach((triple) => {
    addNode(triple.subject);
    addNode(triple.object);
    edges.push({ from: triple.subject, to: triple.object, label: triple.predicate.replace(/^.*[#/:]/, "") });
  });

  result?.results?.forEach((row) => {
    const values = Object.fromEntries(Object.entries(row).map(([key, value]) => [key, stringValue(value)]));
    const entity = values.entity ?? values.x ?? values.subject ?? values.s;
    const target = values.target ?? values.object ?? values.o;
    const relation = values.relation ?? values.predicate ?? values.p ?? "related";
    const type = values.type ?? "Entity";
    if (entity) addNode(entity, type);
    if (entity && target) {
      addNode(target);
      edges.push({ from: entity, to: target, label: relation });
    }
  });

  return { nodes: Array.from(nodeMap.values()).slice(0, 24), edges: edges.slice(0, 32) };
}

export function EntityGraph({ result }: { result: SparqlQueryResponse | null }) {
  const { nodes, edges } = buildGraph(result);
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Network className="h-4 w-4 text-slate-500" />
          Graph View
        </div>
        <span className="text-xs text-slate-500">{nodes.length} nodes · {edges.length} edges</span>
      </div>
      <div className="relative h-[380px] overflow-hidden">
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
            {edges.map((edge, index) => {
              const from = nodeById.get(edge.from);
              const to = nodeById.get(edge.to);
              if (!from || !to) return null;
              const midX = (from.x + to.x) / 2;
              const midY = (from.y + to.y) / 2;
              return (
                <g key={`${edge.from}-${edge.to}-${index}`}>
                  <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#94a3b8" strokeWidth="1.5" markerEnd="url(#arrow)" />
                  <text x={midX} y={midY - 4} textAnchor="middle" fontSize="10" fill="#64748b">
                    {edge.label}
                  </text>
                </g>
              );
            })}
            {nodes.map((node) => (
              <g key={node.id}>
                <circle cx={node.x} cy={node.y} r="28" fill="#eff6ff" stroke="#3b82f6" strokeWidth="2" />
                <text x={node.x} y={node.y - 3} textAnchor="middle" fontSize="9" fontWeight="700" fill="#1d4ed8">
                  {node.type.slice(0, 10)}
                </text>
                <text x={node.x} y={node.y + 10} textAnchor="middle" fontSize="9" fill="#334155">
                  {node.label.slice(0, 14)}
                </text>
              </g>
            ))}
          </svg>
        )}
      </div>
    </div>
  );
}
