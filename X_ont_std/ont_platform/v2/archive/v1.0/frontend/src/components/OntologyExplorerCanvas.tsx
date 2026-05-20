"use client";
import { useCallback, useEffect, useState } from "react";
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
} from "reactflow";
import "reactflow/dist/style.css";
import { api, ApiClientError } from "@/lib/api";
import type { OntologyGraphEdge, OntologyGraphNode, OntologySchema } from "@/types/api";

// ── 타입별 색상 ──────────────────────────────────────────────
const TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Customer: { bg: "#eff6ff", text: "#1d4ed8", border: "#3b82f6" },
  Order:    { bg: "#fffbeb", text: "#b45309", border: "#f59e0b" },
  Product:  { bg: "#f0fdf4", text: "#15803d", border: "#22c55e" },
};
const DEFAULT_COLOR = { bg: "#f8fafc", text: "#475569", border: "#94a3b8" };

// ── 커스텀 노드 ───────────────────────────────────────────────
function OntologyNodeComp({ id, data }: NodeProps) {
  const c = TYPE_COLORS[data.object_type as string] ?? DEFAULT_COLOR;
  return (
    <div
      style={{
        background: c.bg,
        border: `2px solid ${c.border}`,
        borderRadius: 8,
        padding: "8px 14px",
        minWidth: 140,
        boxShadow: "0 1px 4px rgba(0,0,0,.08)",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: c.border }} />
      <div style={{ color: c.text, fontSize: 10, fontWeight: 700, letterSpacing: 1, marginBottom: 2 }}>
        {data.object_type as string}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#1e293b" }}>{(data.label as string) || id}</div>
      <div style={{ fontSize: 11, color: "#94a3b8" }}>{id}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: c.border }} />
    </div>
  );
}

const NODE_TYPES = { ontology: OntologyNodeComp };

// ── 메인 컴포넌트 ─────────────────────────────────────────────
export function OntologyExplorerCanvas({ user }: { user: string }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [rawNodes, setRawNodes] = useState<OntologyGraphNode[]>([]);
  const [rawEdges, setRawEdges] = useState<OntologyGraphEdge[]>([]);
  const [schema, setSchema] = useState<OntologySchema | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ ok: boolean; text: string } | null>(null);

  // 관계 추가 모달
  const [addModal, setAddModal] = useState(false);
  const [newRel, setNewRel] = useState({ rel_type: "", source_id: "", target_id: "" });
  const [addError, setAddError] = useState<string | null>(null);

  // 그래프 로딩
  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [g, s] = await Promise.all([api.ontology.graph(), api.ontology.schema()]);
      setRawNodes(g.nodes);
      setRawEdges(g.edges);
      setSchema(s);
      setNodes(
        g.nodes.map((n) => ({
          id: n.id,
          type: "ontology",
          position: n.position,
          data: n.data,
        }))
      );
      setEdges(
        g.edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label ?? "",
          animated: false,
          style: { stroke: "#94a3b8" },
          labelStyle: { fontSize: 11, fill: "#64748b" },
          data: e.data,
        }))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadGraph();
  }, [loadGraph]);

  // 선택된 노드 정보 계산
  const selectedNode = rawNodes.find((n) => n.id === selectedId) ?? null;
  const outgoingEdges = rawEdges.filter((e) => e.source === selectedId);
  const incomingEdges = rawEdges.filter((e) => e.target === selectedId);

  function showToast(ok: boolean, text: string) {
    setToast({ ok, text });
    setTimeout(() => setToast(null), 3000);
  }

  // 관계 추가 제출
  async function handleAddRel() {
    setAddError(null);
    try {
      await api.ontology.createRelationship({
        relationship_type: newRel.rel_type,
        source_id: newRel.source_id,
        target_id: newRel.target_id,
      });
      setAddModal(false);
      setNewRel({ rel_type: "", source_id: "", target_id: "" });
      showToast(true, "관계가 추가되었습니다.");
      await loadGraph();
    } catch (err) {
      setAddError(err instanceof ApiClientError ? `[${err.code}] ${err.message}` : String(err));
    }
  }

  // 관계 삭제
  async function handleDeleteRel(relId: string) {
    try {
      await api.ontology.deleteRelationship(relId);
      showToast(true, `관계 ${relId} 삭제됨`);
      await loadGraph();
    } catch (err) {
      showToast(false, err instanceof ApiClientError ? `[${err.code}] ${err.message}` : String(err));
    }
  }

  return (
    <div className="flex gap-4 h-[680px]">
      {/* ── React Flow 캔버스 ── */}
      <div className="flex-1 rounded-xl border border-slate-200 overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-10 text-sm text-slate-500">
            로딩 중…
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-10 text-sm text-rose-600 p-4 text-center">
            {error}
          </div>
        )}
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          onNodeClick={(_, node) => setSelectedId(node.id === selectedId ? null : node.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e2e8f0" />
          <Controls />
          <MiniMap nodeColor={(n) => {
            const ot = (n.data as { object_type?: string }).object_type ?? "";
            return TYPE_COLORS[ot]?.border ?? "#94a3b8";
          }} />
        </ReactFlow>

        {/* 상단 툴바 */}
        <div className="absolute top-2 left-2 flex gap-2 z-10">
          <button
            className="btn-sm bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 px-3 py-1.5 rounded-md text-xs shadow-sm"
            onClick={() => void loadGraph()}
          >
            새로고침
          </button>
          <button
            className="btn-sm bg-blue-600 text-white hover:bg-blue-700 px-3 py-1.5 rounded-md text-xs shadow-sm"
            onClick={() => { setAddModal(true); setAddError(null); }}
          >
            + 관계 추가
          </button>
        </div>

        {/* 범례 */}
        <div className="absolute bottom-12 left-2 flex gap-2 z-10">
          {Object.entries(TYPE_COLORS).map(([t, c]) => (
            <span
              key={t}
              className="px-2 py-0.5 rounded text-xs font-medium"
              style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
            >
              {t}
            </span>
          ))}
        </div>

        {/* 토스트 */}
        {toast && (
          <div
            className={`absolute top-2 right-2 z-20 px-3 py-2 rounded-md text-xs shadow ${
              toast.ok ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200"
            }`}
          >
            {toast.text}
          </div>
        )}
      </div>

      {/* ── 상세 패널 ── */}
      <div className="w-72 shrink-0 rounded-xl border border-slate-200 bg-white overflow-y-auto p-4">
        {selectedNode ? (
          <>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-800">객체 상세</h3>
              <button className="text-slate-400 hover:text-slate-600 text-xs" onClick={() => setSelectedId(null)}>
                ✕
              </button>
            </div>
            {/* 속성 */}
            <div className="mb-4">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">속성</div>
              <table className="w-full text-xs">
                <tbody>
                  {Object.entries(selectedNode.data)
                    .filter(([k]) => !["label", "icon"].includes(k))
                    .map(([k, v]) => (
                      <tr key={k} className="border-b border-slate-50">
                        <td className="py-1 pr-2 text-slate-500 font-medium whitespace-nowrap">{k}</td>
                        <td className="py-1 text-slate-800 break-all">{String(v ?? "-")}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            {/* Outgoing */}
            {outgoingEdges.length > 0 && (
              <div className="mb-4">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                  → Outgoing ({outgoingEdges.length})
                </div>
                {outgoingEdges.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-xs text-slate-600">
                      <span className="font-medium text-blue-600">{e.label}</span> → {e.target}
                    </span>
                    <button
                      className="text-rose-400 hover:text-rose-600 text-xs ml-1"
                      title="관계 삭제"
                      onClick={() => void handleDeleteRel(e.id)}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
            {/* Incoming */}
            {incomingEdges.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                  ← Incoming ({incomingEdges.length})
                </div>
                {incomingEdges.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-xs text-slate-600">
                      {e.source} → <span className="font-medium text-amber-600">{e.label}</span>
                    </span>
                    <button
                      className="text-rose-400 hover:text-rose-600 text-xs ml-1"
                      title="관계 삭제"
                      onClick={() => void handleDeleteRel(e.id)}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
            {outgoingEdges.length === 0 && incomingEdges.length === 0 && (
              <p className="text-xs text-slate-400">연결된 관계 없음</p>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 text-xs text-center gap-2">
            <span className="text-3xl">🔗</span>
            <p>노드를 클릭하면<br />객체 상세와 관계가 표시됩니다.</p>
            <p className="mt-2 text-slate-300">
              총 {rawNodes.length}개 객체 · {rawEdges.length}개 관계
            </p>
          </div>
        )}
      </div>

      {/* ── 관계 추가 모달 ── */}
      {addModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="text-sm font-bold text-slate-800 mb-4">관계 인스턴스 추가</h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs text-slate-500 mb-1">관계 타입</label>
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={newRel.rel_type}
                  onChange={(e) => setNewRel((p) => ({ ...p, rel_type: e.target.value }))}
                >
                  <option value="">선택...</option>
                  {schema?.relationship_types.map((r) => (
                    <option key={r.name} value={r.name}>
                      {r.display_name ? `${r.name} (${r.display_name})` : r.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Source 객체 ID</label>
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={newRel.source_id}
                  onChange={(e) => setNewRel((p) => ({ ...p, source_id: e.target.value }))}
                >
                  <option value="">선택...</option>
                  {rawNodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.id} ({n.data.object_type})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Target 객체 ID</label>
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={newRel.target_id}
                  onChange={(e) => setNewRel((p) => ({ ...p, target_id: e.target.value }))}
                >
                  <option value="">선택...</option>
                  {rawNodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.id} ({n.data.object_type})
                    </option>
                  ))}
                </select>
              </div>
              {addError && (
                <p className="text-xs text-rose-600 bg-rose-50 rounded p-2">{addError}</p>
              )}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                className="flex-1 bg-blue-600 text-white text-sm py-1.5 rounded hover:bg-blue-700"
                onClick={() => void handleAddRel()}
                disabled={!newRel.rel_type || !newRel.source_id || !newRel.target_id}
              >
                추가
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
