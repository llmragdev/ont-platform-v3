"use client";
import { useCallback, useEffect, useState } from "react";
import { usePermission } from "@/hooks/usePermission";
import { useUserContext } from "@/context/UserContext";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  Handle,
  MiniMap,
  Node,
  NodeProps,
  Position,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "@/lib/api";
import type { OntologyDocInfo, OntologyMgmtGraph } from "@/types/api";

// ── 타입별 색상 ──────────────────────────────────────────────
const TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  PERSON:       { bg: "#eff6ff", text: "#1d4ed8", border: "#3b82f6" },
  ORGANIZATION: { bg: "#faf5ff", text: "#7e22ce", border: "#a855f7" },
  PRODUCT:      { bg: "#f0fdf4", text: "#15803d", border: "#22c55e" },
  METRIC:       { bg: "#fffbeb", text: "#b45309", border: "#f59e0b" },
  CONCEPT:      { bg: "#ecfeff", text: "#0e7490", border: "#06b6d4" },
  CATEGORY:     { bg: "#fff7ed", text: "#c2410c", border: "#f97316" },
  EVENT:        { bg: "#fff1f2", text: "#be123c", border: "#f43f5e" },
  LOCATION:     { bg: "#f0fdfa", text: "#0f766e", border: "#14b8a6" },
};
const DEFAULT_COLOR = { bg: "#f8fafc", text: "#475569", border: "#94a3b8" };

// ── 커스텀 노드 ────────────────────────────────────────────────
function OntologyNode({ id, data, selected }: NodeProps) {
  const c = TYPE_COLORS[(data as { type?: string }).type ?? ""] ?? DEFAULT_COLOR;
  return (
    <div
      style={{
        background: c.bg,
        border: `2px solid ${selected ? "#2563eb" : c.border}`,
        borderRadius: 10,
        padding: "8px 14px",
        minWidth: 130,
        boxShadow: selected ? "0 0 0 3px #bfdbfe" : "0 1px 4px rgba(0,0,0,.08)",
        transition: "box-shadow .15s",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: c.border }} />
      <div style={{ color: c.text, fontSize: 9, fontWeight: 700, letterSpacing: 1, marginBottom: 2, textTransform: "uppercase" }}>
        {(data as { type?: string }).type ?? "?"}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#1e293b" }}>{(data as { label?: string }).label ?? id}</div>
      <div style={{ fontSize: 10, color: "#94a3b8" }}>{id}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: c.border }} />
    </div>
  );
}

const NODE_TYPES = { ontologyEdit: OntologyNode };

// ── 그래프 → ReactFlow 변환 ──────────────────────────────────
function toRFNodes(graph: OntologyMgmtGraph): Node[] {
  return graph.nodes.map((n, i) => ({
    id: n.id,
    type: "ontologyEdit",
    position: { x: (i % 5) * 200, y: Math.floor(i / 5) * 150 },
    data: { label: n.label, type: n.type, properties: n.properties },
  }));
}

function toRFEdges(graph: OntologyMgmtGraph): Edge[] {
  return graph.edges.map((e) => ({
    id: e.id,
    source: e.from,
    target: e.to,
    label: e.label,
    animated: false,
    style: { stroke: "#94a3b8" },
    labelStyle: { fontSize: 11, fill: "#475569" },
    labelBgStyle: { fill: "#f8fafc", fillOpacity: 0.8 },
  }));
}

// ── Toast ────────────────────────────────────────────────────
function Toast({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div
      className={`absolute top-2 right-2 z-20 px-3 py-2 rounded-md text-xs shadow ${
        ok ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200"
      }`}
    >
      {text}
    </div>
  );
}

// ── 메인 컴포넌트 ──────────────────────────────────────────────
export function OntologyGraphEditor() {
  const canEditDiagram = usePermission("can_edit_diagram");
  const { user: tenantUser } = useUserContext();
  const userId = tenantUser?.id;
  const [docs, setDocs] = useState<OntologyDocInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [rawGraph, setRawGraph] = useState<OntologyMgmtGraph | null>(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ ok: boolean; text: string } | null>(null);

  // 선택된 노드
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const selectedNode = rawGraph?.nodes.find((n) => n.id === selectedNodeId) ?? null;
  const outEdges = rawGraph?.edges.filter((e) => e.from === selectedNodeId) ?? [];
  const inEdges = rawGraph?.edges.filter((e) => e.to === selectedNodeId) ?? [];

  // 관계 추가 모달
  const [addModal, setAddModal] = useState(false);
  const [newRel, setNewRel] = useState({ from_id: "", relation: "", to_id: "" });
  const [addError, setAddError] = useState<string | null>(null);
  const [addSubmitting, setAddSubmitting] = useState(false);

  const showToast = (ok: boolean, text: string) => {
    setToast({ ok, text });
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    void (async () => {
      try {
        const res = await api.ontologyMgmt.listDocs();
        setDocs(res.ontologies);
        if (res.ontologies.length > 0) setSelectedDoc(res.ontologies[0].doc_id);
      } catch (err) {
        showToast(false, err instanceof Error ? err.message : String(err));
      }
    })();
  }, []);

  const loadGraph = useCallback(async (docId: string) => {
    if (!docId) return;
    setLoading(true);
    try {
      const g = await api.ontologyMgmt.getGraph(docId);
      setRawGraph(g);
      setNodes(toRFNodes(g));
      setEdges(toRFEdges(g));
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    void loadGraph(selectedDoc);
    setSelectedNodeId(null);
  }, [selectedDoc, loadGraph]);

  async function handleDeleteRelationship(relId: string) {
    if (!selectedDoc) return;
    try {
      await api.ontologyMgmt.deleteRelationship(selectedDoc, relId, userId);
      showToast(true, `관계 ${relId} 삭제됨`);
      await loadGraph(selectedDoc);
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    }
  }

  async function handleAddRelationship() {
    if (!selectedDoc) return;
    setAddError(null);
    setAddSubmitting(true);
    try {
      await api.ontologyMgmt.addRelationship(selectedDoc, newRel, userId);
      showToast(true, "관계 추가됨");
      setAddModal(false);
      setNewRel({ from_id: "", relation: "", to_id: "" });
      await loadGraph(selectedDoc);
    } catch (err) {
      setAddError(err instanceof Error ? err.message : String(err));
    } finally {
      setAddSubmitting(false);
    }
  }

  const nodeIds = rawGraph?.nodes.map((n) => n.id) ?? [];

  return (
    <div className="flex gap-4" style={{ height: 680 }}>
      {/* ── React Flow 캔버스 ── */}
      <div className="flex-1 rounded-xl border border-slate-200 overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-10 text-sm text-slate-500">
            로딩 중…
          </div>
        )}
        {toast && <Toast ok={toast.ok} text={toast.text} />}

        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => setSelectedNodeId(node.id === selectedNodeId ? null : node.id)}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e2e8f0" />
          <Controls />
          <MiniMap
            nodeColor={(n) => {
              const t = (n.data as { type?: string }).type ?? "";
              return TYPE_COLORS[t]?.border ?? "#94a3b8";
            }}
          />
        </ReactFlow>

        {/* 상단 툴바 */}
        <div className="absolute top-2 left-2 flex gap-2 z-10">
          <select
            className="border border-slate-200 rounded px-2 py-1.5 text-xs bg-white shadow-sm"
            value={selectedDoc}
            onChange={(e) => setSelectedDoc(e.target.value)}
          >
            {docs.length === 0 && <option value="">문서 없음</option>}
            {docs.map((d) => (
              <option key={d.doc_id} value={d.doc_id}>{d.filename}</option>
            ))}
          </select>
          <button
            className="bg-white border border-slate-200 text-slate-700 px-3 py-1.5 rounded text-xs shadow-sm hover:bg-slate-50"
            onClick={() => void loadGraph(selectedDoc)}
          >
            새로고침
          </button>
          <button
            className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs shadow-sm hover:bg-blue-700 disabled:opacity-50"
            onClick={() => { setAddModal(true); setAddError(null); setNewRel({ from_id: selectedNodeId ?? "", relation: "", to_id: "" }); }}
            disabled={!selectedDoc || !canEditDiagram}
            title={!canEditDiagram ? "편집 권한이 없습니다" : undefined}
          >
            + 관계 추가
          </button>
        </div>

        {/* 범례 */}
        <div className="absolute bottom-12 left-2 flex flex-wrap gap-1 z-10 max-w-xs">
          {Object.entries(TYPE_COLORS).map(([t, c]) => (
            <span
              key={t}
              className="px-1.5 py-0.5 rounded text-[10px] font-medium"
              style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* ── 상세 패널 ── */}
      <div className="w-72 shrink-0 rounded-xl border border-slate-200 bg-white overflow-y-auto p-4">
        {selectedNode ? (
          <>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-800">노드 상세</h3>
              <button className="text-slate-400 hover:text-slate-600 text-xs" onClick={() => setSelectedNodeId(null)}>✕</button>
            </div>
            <div
              className="rounded-md px-3 py-2 mb-3 text-xs font-semibold"
              style={{
                background: TYPE_COLORS[selectedNode.type]?.bg ?? "#f8fafc",
                color: TYPE_COLORS[selectedNode.type]?.text ?? "#475569",
                border: `1px solid ${TYPE_COLORS[selectedNode.type]?.border ?? "#94a3b8"}`,
              }}
            >
              {selectedNode.type} · {selectedNode.id}
            </div>
            <p className="text-sm font-medium text-slate-800 mb-3">{selectedNode.label}</p>

            {Object.keys(selectedNode.properties).length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">속성</p>
                <table className="w-full text-xs">
                  <tbody>
                    {Object.entries(selectedNode.properties).map(([k, v]) => (
                      <tr key={k} className="border-b border-slate-50">
                        <td className="py-1 pr-2 text-slate-500 font-medium">{k}</td>
                        <td className="py-1 text-slate-700 break-all">{String(v ?? "-")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Outgoing */}
            {outEdges.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">→ Outgoing ({outEdges.length})</p>
                {outEdges.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-xs text-slate-600">
                      <span className="font-medium text-blue-600">{e.label}</span> → {e.to}
                    </span>
                    {canEditDiagram && (
                      <button className="text-rose-400 hover:text-rose-600 text-xs" onClick={() => void handleDeleteRelationship(e.id)}>✕</button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Incoming */}
            {inEdges.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">← Incoming ({inEdges.length})</p>
                {inEdges.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-xs text-slate-600">
                      {e.from} → <span className="font-medium text-amber-600">{e.label}</span>
                    </span>
                    {canEditDiagram && (
                      <button className="text-rose-400 hover:text-rose-600 text-xs" onClick={() => void handleDeleteRelationship(e.id)}>✕</button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {outEdges.length === 0 && inEdges.length === 0 && (
              <p className="text-xs text-slate-400">연결된 관계 없음</p>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 text-xs text-center gap-2 py-12">
            <div className="text-3xl">🕸️</div>
            <p>노드를 클릭하면<br />상세 정보와 관계를 표시합니다.</p>
            <p className="mt-2 text-slate-300">
              {rawGraph ? `${rawGraph.nodes.length}개 노드 · ${rawGraph.edges.length}개 엣지` : ""}
            </p>
          </div>
        )}
      </div>

      {/* ── 관계 추가 모달 ── */}
      {addModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="text-sm font-bold text-slate-800 mb-4">관계 추가</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">From 엔티티</label>
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={newRel.from_id}
                  onChange={(e) => setNewRel((p) => ({ ...p, from_id: e.target.value }))}
                >
                  <option value="">선택…</option>
                  {nodeIds.map((id) => (
                    <option key={id} value={id}>
                      {rawGraph?.nodes.find((n) => n.id === id)?.label ?? id} ({id})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">관계명</label>
                <input
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  placeholder="예: BELONGS_TO"
                  value={newRel.relation}
                  onChange={(e) => setNewRel((p) => ({ ...p, relation: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">To 엔티티</label>
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={newRel.to_id}
                  onChange={(e) => setNewRel((p) => ({ ...p, to_id: e.target.value }))}
                >
                  <option value="">선택…</option>
                  {nodeIds.map((id) => (
                    <option key={id} value={id}>
                      {rawGraph?.nodes.find((n) => n.id === id)?.label ?? id} ({id})
                    </option>
                  ))}
                </select>
              </div>
              {addError && <p className="text-xs text-rose-600 bg-rose-50 rounded p-2">{addError}</p>}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                className="flex-1 bg-blue-600 text-white text-sm py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
                onClick={() => void handleAddRelationship()}
                disabled={!newRel.from_id || !newRel.relation.trim() || !newRel.to_id || addSubmitting}
              >
                {addSubmitting ? "추가 중…" : "추가"}
              </button>
              <button
                className="flex-1 bg-slate-100 text-slate-700 text-sm py-1.5 rounded hover:bg-slate-200"
                onClick={() => { setAddModal(false); setAddError(null); }}
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
