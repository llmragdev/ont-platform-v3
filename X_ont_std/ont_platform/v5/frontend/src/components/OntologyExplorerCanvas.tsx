"use client";
import { useCallback, useEffect, useState } from "react";
import ReactFlow, {
  applyNodeChanges,
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  Handle,
  MiniMap,
  Node,
  NodeChange,
  NodeProps,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "@/lib/api";
import type { OntologyDocInfo, OntologyMgmtGraph } from "@/types/api";

const TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  PERSON:       { bg: "#eff6ff", text: "#1d4ed8", border: "#3b82f6" },
  ORGANIZATION: { bg: "#faf5ff", text: "#7e22ce", border: "#a855f7" },
  PRODUCT:      { bg: "#f0fdf4", text: "#15803d", border: "#22c55e" },
  METRIC:       { bg: "#fffbeb", text: "#b45309", border: "#f59e0b" },
  CONCEPT:      { bg: "#ecfeff", text: "#0e7490", border: "#06b6d4" },
  CATEGORY:     { bg: "#fff7ed", text: "#c2410c", border: "#f97316" },
  EVENT:        { bg: "#fff1f2", text: "#be123c", border: "#f43f5e" },
  LOCATION:     { bg: "#f0fdfa", text: "#0f766e", border: "#14b8a6" },
  Order:        { bg: "#fffbeb", text: "#b45309", border: "#f59e0b" },
  Customer:     { bg: "#eff6ff", text: "#1d4ed8", border: "#3b82f6" },
  Product:      { bg: "#f0fdf4", text: "#15803d", border: "#22c55e" },
};
const DEFAULT_COLOR = { bg: "#f8fafc", text: "#475569", border: "#94a3b8" };
const TYPE_ORDER: Record<string, number> = {
  ServiceRequest: 0,
  WorkflowExecution: 1,
  AutoReply: 2,
  ExternalComment: 3,
};
const TYPE_LABELS: Record<string, string> = {
  ServiceRequest: "서비스 요청",
  WorkflowExecution: "워크플로우 실행",
  AutoReply: "자동 답변",
  ExternalComment: "외부 댓글",
};
const getColor = (type: string) => TYPE_COLORS[type] ?? TYPE_COLORS[type?.toUpperCase()] ?? DEFAULT_COLOR;

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "object") {
    try { return JSON.stringify(value); } catch { return String(value); }
  }
  return String(value);
}

function layoutNodes(graph: OntologyMgmtGraph): Node[] {
  const outgoing = new Map<string, OntologyMgmtGraph["edges"]>();
  const incoming = new Map<string, OntologyMgmtGraph["edges"]>();
  graph.edges.forEach((edge) => {
    outgoing.set(edge.from, [...(outgoing.get(edge.from) ?? []), edge]);
    incoming.set(edge.to, [...(incoming.get(edge.to) ?? []), edge]);
  });

  const serviceRequestIds = graph.nodes
    .filter((node) => node.type === "ServiceRequest")
    .map((node) => node.id);
  const orderedIds = new Set<string>();
  const rows = new Map<string, number>();

  serviceRequestIds.forEach((id, index) => {
    const baseRow = index * 4;
    rows.set(id, baseRow);
    orderedIds.add(id);
    const handled = outgoing.get(id)?.filter((edge) => edge.label === "handled_by") ?? [];
    handled.forEach((edge, offset) => {
      rows.set(edge.to, baseRow + offset);
      orderedIds.add(edge.to);
      const generated = outgoing.get(edge.to)?.filter((child) => child.label === "generated") ?? [];
      generated.forEach((child, childOffset) => {
        rows.set(child.to, baseRow + offset + childOffset);
        orderedIds.add(child.to);
        const posted = outgoing.get(child.to)?.filter((grandChild) => grandChild.label === "posted_as") ?? [];
        posted.forEach((grandChild, grandChildOffset) => {
          rows.set(grandChild.to, baseRow + offset + childOffset + grandChildOffset);
          orderedIds.add(grandChild.to);
        });
      });
    });
  });

  const fallbackByType = new Map<string, number>();
  return graph.nodes.map((node, index) => {
    const typeRank = TYPE_ORDER[node.type] ?? 4;
    const fallbackRow = fallbackByType.get(node.type) ?? 0;
    fallbackByType.set(node.type, fallbackRow + 1);
    const row = rows.get(node.id) ?? fallbackRow + (orderedIds.has(node.id) ? 0 : serviceRequestIds.length * 4);
    return {
      id: node.id,
      type: "ontology",
      position: {
        x: typeRank * 260 + (typeRank >= 4 ? (index % 2) * 260 : 0),
        y: row * 120,
      },
      data: { label: node.label, type: node.type, properties: node.properties },
    };
  });
}

function OntologyNodeComp({ id, data }: NodeProps) {
  const c = getColor((data as { type?: string }).type ?? "");
  return (
    <div style={{ background: c.bg, border: `2px solid ${c.border}`, borderRadius: 8, padding: "8px 14px", width: 190, minHeight: 66, boxShadow: "0 1px 4px rgba(0,0,0,.08)" }}>
      <Handle type="target" position={Position.Top} style={{ background: c.border }} />
      <div style={{ color: c.text, fontSize: 10, fontWeight: 700, marginBottom: 2 }}>{TYPE_LABELS[(data as { type?: string }).type ?? ""] ?? (data as { type?: string }).type ?? "?"}</div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#1e293b", whiteSpace: "normal", wordBreak: "keep-all" }}>{(data as { label?: string }).label ?? id}</div>
      <div style={{ fontSize: 10, color: "#94a3b8", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{id}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: c.border }} />
    </div>
  );
}

const NODE_TYPES = { ontology: OntologyNodeComp };

export function OntologyExplorerCanvas() {
  const [docs, setDocs] = useState<OntologyDocInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [rawGraph, setRawGraph] = useState<OntologyMgmtGraph | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const list = await api.ontologyMgmt.listDocs();
        const arr = Array.isArray(list) ? list : [];
        setDocs(arr);
        if (arr.length > 0) setSelectedDoc(arr[0].doc_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    })();
  }, []);

  const loadGraph = useCallback(async (docId: string) => {
    if (!docId) return;
    setLoading(true);
    setError(null);
    try {
      const g = await api.ontologyMgmt.getGraph(docId);
      setRawGraph(g);
      setNodes(layoutNodes(g));
      setEdges(g.edges.map((e) => ({
        id: e.id,
        source: e.from,
        target: e.to,
        label: e.label,
        animated: false,
        style: { stroke: "#94a3b8" },
        labelStyle: { fontSize: 11, fill: "#64748b" },
        labelBgStyle: { fill: "#f8fafc", fillOpacity: 0.9 },
      })));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  useEffect(() => { void loadGraph(selectedDoc); }, [selectedDoc, loadGraph]);

  const selectedNode = rawGraph?.nodes.find((n) => n.id === selectedId) ?? null;
  const outEdges = rawGraph?.edges.filter((e) => e.from === selectedId) ?? [];
  const inEdges = rawGraph?.edges.filter((e) => e.to === selectedId) ?? [];
  const visibleTypes = Array.from(new Set(rawGraph?.nodes.map((node) => node.type).filter(Boolean) ?? []));

  return (
    <div className="flex gap-4 h-[680px]">
      <div className="flex-1 rounded-xl border border-slate-200 overflow-hidden relative">
        {loading && <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-10 text-sm text-slate-500">로딩 중…</div>}
        {error && <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-10 text-sm text-rose-600 p-4 text-center">{error}</div>}
        <ReactFlow
          nodes={nodes} edges={edges} nodeTypes={NODE_TYPES}
          fitView fitViewOptions={{ padding: 0.2 }}
          onNodesChange={onNodesChange}
          onNodeClick={(_, node) => setSelectedId(node.id === selectedId ? null : node.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e2e8f0" />
          <Controls />
          <MiniMap nodeColor={(n) => getColor((n.data as { type?: string }).type ?? "").border} />
        </ReactFlow>
        <div className="absolute top-2 left-2 flex gap-2 z-10">
          <select className="border border-slate-200 rounded px-2 py-1.5 text-xs bg-white shadow-sm" value={selectedDoc} onChange={(e) => setSelectedDoc(e.target.value)}>
            {docs.length === 0 && <option value="">문서 없음</option>}
            {docs.map((d) => <option key={d.doc_id} value={d.doc_id}>{d.doc_id}</option>)}
          </select>
          <button className="bg-white border border-slate-200 text-slate-700 px-3 py-1.5 rounded text-xs shadow-sm hover:bg-slate-50" onClick={() => void loadGraph(selectedDoc)}>새로고침</button>
        </div>
        <div className="absolute bottom-12 left-2 right-52 flex flex-wrap gap-1 z-10">
          {visibleTypes.map((t) => {
            const c = getColor(t);
            return (
              <span key={t} className="px-2 py-0.5 rounded text-xs font-medium" style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}>
                {TYPE_LABELS[t] ?? t}
              </span>
            );
          })}
        </div>
        <div className="absolute bottom-2 left-2 z-10 rounded bg-white/90 px-2 py-1 text-[11px] text-slate-500 shadow-sm">
          조회 화면입니다. 노드는 임시로 이동할 수 있고, 추가/연결/위치 저장은 "관계 그래프 편집" 메뉴에서 합니다.
        </div>
      </div>

      <div className="w-72 shrink-0 rounded-xl border border-slate-200 bg-white overflow-y-auto p-4">
        {selectedNode ? (
          <>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-800">객체 상세</h3>
              <button className="text-slate-400 hover:text-slate-600 text-xs" onClick={() => setSelectedId(null)}>✕</button>
            </div>
            <div className="mb-4">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">속성</div>
              <table className="w-full text-xs"><tbody>
                <tr className="border-b border-slate-50"><td className="py-1 pr-2 text-slate-500 font-medium">ID</td><td className="py-1 text-slate-800">{selectedNode.id}</td></tr>
                <tr className="border-b border-slate-50"><td className="py-1 pr-2 text-slate-500 font-medium">유형</td><td className="py-1 text-slate-800">{selectedNode.type}</td></tr>
                <tr className="border-b border-slate-50"><td className="py-1 pr-2 text-slate-500 font-medium">이름</td><td className="py-1 text-slate-800">{selectedNode.label}</td></tr>
                {Object.entries(selectedNode.properties).map(([k, v]) => (
                  <tr key={k} className="border-b border-slate-50">
                    <td className="py-1 pr-2 text-slate-500 font-medium whitespace-nowrap">{k}</td>
                    <td className="py-1 text-slate-800 break-all">{formatValue(v)}</td>
                  </tr>
                ))}
              </tbody></table>
            </div>
            {outEdges.length > 0 && (
              <div className="mb-4">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">→ Outgoing ({outEdges.length})</div>
                {outEdges.map((e) => (
                  <div key={e.id} className="flex items-center py-1 border-b border-slate-50 text-xs text-slate-600">
                    <span className="font-medium text-blue-600">{e.label}</span><span className="mx-1">→</span><span>{e.to}</span>
                  </div>
                ))}
              </div>
            )}
            {inEdges.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">← Incoming ({inEdges.length})</div>
                {inEdges.map((e) => (
                  <div key={e.id} className="flex items-center py-1 border-b border-slate-50 text-xs text-slate-600">
                    <span>{e.from}</span><span className="mx-1">→</span><span className="font-medium text-amber-600">{e.label}</span>
                  </div>
                ))}
              </div>
            )}
            {outEdges.length === 0 && inEdges.length === 0 && <p className="text-xs text-slate-400">연결된 관계 없음</p>}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 text-xs text-center gap-2">
            <p>노드를 클릭하면<br />객체 상세와 관계가 표시됩니다.</p>
            <p className="mt-2 text-slate-300">총 {rawGraph?.nodes.length ?? 0}개 객체 · {rawGraph?.edges.length ?? 0}개 관계</p>
          </div>
        )}
      </div>
    </div>
  );
}
