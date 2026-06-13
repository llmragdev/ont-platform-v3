"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePermission } from "@/hooks/usePermission";
import ReactFlow, {
  addEdge,
  Background,
  BackgroundVariant,
  Connection,
  Controls,
  Edge,
  Handle,
  MiniMap,
  Node,
  NodeProps,
  Position,
  useEdgesState,
  useNodesState,
  useReactFlow,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "@/lib/api";
import type { OntologyDocInfo, OntologyMgmtGraph } from "@/types/api";

// ── 타입별 색상 ──────────────────────────────────────────────────────────────

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
const getColor = (type: string) => TYPE_COLORS[type?.toUpperCase()] ?? DEFAULT_COLOR;

// ── ReactFlow 노드 컴포넌트 ──────────────────────────────────────────────────

function OntologyNode({ id, data, selected }: NodeProps) {
  const c = getColor((data as { type?: string }).type ?? "");
  return (
    <div style={{
      background: c.bg,
      border: `2px solid ${selected ? "#2563eb" : c.border}`,
      borderRadius: 10, padding: "8px 14px", minWidth: 130,
      boxShadow: selected ? "0 0 0 3px #bfdbfe" : "0 1px 4px rgba(0,0,0,.08)",
    }}>
      <Handle type="target" position={Position.Top} style={{ background: c.border }} />
      <div style={{ color: c.text, fontSize: 9, fontWeight: 700, letterSpacing: 1, marginBottom: 2, textTransform: "uppercase" }}>
        {(data as { type?: string }).type ?? "?"}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#1e293b" }}>
        {(data as { label?: string }).label ?? id}
      </div>
      <div style={{ fontSize: 10, color: "#94a3b8" }}>{id}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: c.border }} />
    </div>
  );
}

const NODE_TYPES = { ontologyEdit: OntologyNode };

// ── 유틸 ─────────────────────────────────────────────────────────────────────

const LAYOUT_KEY = (docId: string) => `ont-layout-${docId}`;

function loadSavedPositions(docId: string): Record<string, { x: number; y: number }> {
  try {
    return JSON.parse(localStorage.getItem(LAYOUT_KEY(docId)) ?? "{}");
  } catch { return {}; }
}

function savePositions(docId: string, nodes: Node[]) {
  const pos: Record<string, { x: number; y: number }> = {};
  nodes.forEach((n) => { pos[n.id] = n.position; });
  localStorage.setItem(LAYOUT_KEY(docId), JSON.stringify(pos));
}

function toRFNodes(graph: OntologyMgmtGraph, docId: string): Node[] {
  const saved = loadSavedPositions(docId);
  return graph.nodes.map((n, i) => ({
    id: n.id,
    type: "ontologyEdit",
    position: saved[n.id] ?? { x: (i % 5) * 220, y: Math.floor(i / 5) * 160 },
    data: { label: n.label, type: n.type, properties: n.properties },
  }));
}

function toRFEdges(graph: OntologyMgmtGraph): Edge[] {
  return graph.edges.map((e) => ({
    id: e.id, source: e.from, target: e.to, label: e.label,
    animated: false,
    style: { stroke: "#94a3b8" },
    labelStyle: { fontSize: 11, fill: "#475569" },
    labelBgStyle: { fill: "#f8fafc", fillOpacity: 0.8 },
  }));
}

// ── Toast ────────────────────────────────────────────────────────────────────

function Toast({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div className={`absolute top-2 right-2 z-20 px-3 py-2 rounded-md text-xs shadow ${
      ok ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
         : "bg-rose-50 text-rose-700 border border-rose-200"}`}>
      {text}
    </div>
  );
}

// ── 메인 컴포넌트 (ReactFlowProvider로 감쌈) ──────────────────────────────────

export function OntologyGraphEditor() {
  return (
    <ReactFlowProvider>
      <OntologyGraphEditorInner />
    </ReactFlowProvider>
  );
}

function OntologyGraphEditorInner() {
  const canEdit = usePermission("can_edit_diagram");
  const { screenToFlowPosition } = useReactFlow();

  // ── 데이터 상태 ──────────────────────────────────────────────────────────
  const [docs, setDocs] = useState<OntologyDocInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [allTypes, setAllTypes] = useState<string[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [rawGraph, setRawGraph] = useState<OntologyMgmtGraph | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ ok: boolean; text: string } | null>(null);

  // ── 모달 상태 ─────────────────────────────────────────────────────────────
  // 노드 추가
  const [nodeModal, setNodeModal] = useState(false);
  const [nodeType, setNodeType] = useState("");
  const [nodeName, setNodeName] = useState("");
  const [nodeProps, setNodeProps] = useState("");
  const [nodeSubmitting, setNodeSubmitting] = useState(false);
  const [nodeError, setNodeError] = useState<string | null>(null);

  // 엣지(관계) 추가 — onConnect 트리거
  const [edgeModal, setEdgeModal] = useState(false);
  const [pendingConn, setPendingConn] = useState<Connection | null>(null);
  const [relName, setRelName] = useState("");
  const [relSubmitting, setRelSubmitting] = useState(false);
  const [relError, setRelError] = useState<string | null>(null);

  // 새 문서 네임스페이스
  const [newDocInput, setNewDocInput] = useState("");

  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const showToast = (ok: boolean, text: string) => {
    setToast({ ok, text });
    setTimeout(() => setToast(null), 3000);
  };

  // ── 초기 로드 ─────────────────────────────────────────────────────────────
  useEffect(() => {
    void (async () => {
      try {
        const [docList, schema] = await Promise.all([
          api.ontologyMgmt.listDocs(),
          api.ontologyMgmt.getSchema(),
        ]);
        const arr = Array.isArray(docList) ? docList : [];
        setDocs(arr);
        if (arr.length > 0) setSelectedDoc(arr[0].doc_id);
        const types = schema.entity_types.map((t) => t.name);
        setAllTypes(types.length > 0 ? types : Object.keys(TYPE_COLORS));
      } catch (err) {
        showToast(false, err instanceof Error ? err.message : String(err));
        setAllTypes(Object.keys(TYPE_COLORS));
      }
    })();
  }, []);

  // ── 그래프 불러오기 ────────────────────────────────────────────────────────
  const loadGraph = useCallback(async (docId: string) => {
    if (!docId) return;
    setLoading(true);
    try {
      const g = await api.ontologyMgmt.getGraph(docId);
      setRawGraph(g);
      setNodes(toRFNodes(g, docId));
      setEdges(toRFEdges(g));
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    if (selectedDoc) {
      void loadGraph(selectedDoc);
      setSelectedNodeId(null);
    }
  }, [selectedDoc, loadGraph]);

  // ── 레이아웃 저장 ──────────────────────────────────────────────────────────
  function handleSaveLayout() {
    if (!selectedDoc) return;
    savePositions(selectedDoc, nodes);
    showToast(true, "레이아웃 저장 완료");
  }

  // ── 새 문서 네임스페이스 생성 ──────────────────────────────────────────────
  async function handleCreateDoc() {
    const id = newDocInput.trim();
    if (!id) return;
    try {
      await api.ontologyMgmt.createDoc(id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      if (!msg.includes("이미 존재")) { showToast(false, msg); return; }
    }
    const arr = await api.ontologyMgmt.listDocs();
    setDocs(Array.isArray(arr) ? arr : []);
    setSelectedDoc(id);
    setNewDocInput("");
    showToast(true, `문서 '${id}' 생성됨`);
  }

  // ── 노드(엔티티) 추가 ─────────────────────────────────────────────────────
  function openNodeModal(type: string) {
    if (!selectedDoc) { showToast(false, "먼저 온톨로지 문서를 선택하세요"); return; }
    setNodeType(type);
    setNodeName("");
    setNodeProps("");
    setNodeError(null);
    setNodeModal(true);
  }

  async function handleAddNode() {
    if (!nodeName.trim()) { setNodeError("이름을 입력하세요"); return; }
    setNodeSubmitting(true);
    setNodeError(null);
    try {
      let props: Record<string, unknown> = {};
      if (nodeProps.trim()) {
        try { props = JSON.parse(nodeProps) as Record<string, unknown>; }
        catch { setNodeError("속성은 JSON 형식이어야 합니다 (예: {\"key\": \"value\"})"); setNodeSubmitting(false); return; }
      }
      await api.ontologyMgmt.createEntity(selectedDoc, { type: nodeType, name: nodeName.trim(), properties: props });
      showToast(true, `${nodeType} 엔티티 추가됨`);
      setNodeModal(false);
      await loadGraph(selectedDoc);
    } catch (err) {
      setNodeError(err instanceof Error ? err.message : String(err));
    } finally {
      setNodeSubmitting(false);
    }
  }

  // ── 엣지(관계) 연결 ───────────────────────────────────────────────────────
  const onConnect = useCallback((conn: Connection) => {
    if (!canEdit) { showToast(false, "편집 권한이 없습니다"); return; }
    setPendingConn(conn);
    setRelName("");
    setRelError(null);
    setEdgeModal(true);
  }, [canEdit]);

  async function handleConfirmEdge() {
    if (!relName.trim()) { setRelError("관계명을 입력하세요"); return; }
    if (!pendingConn?.source || !pendingConn?.target) return;
    setRelSubmitting(true);
    setRelError(null);
    try {
      await api.ontologyMgmt.addRelationship(selectedDoc, {
        from_id: pendingConn.source,
        relation: relName.trim().toUpperCase(),
        to_id: pendingConn.target,
      });
      showToast(true, "관계 추가됨");
      setEdgeModal(false);
      setPendingConn(null);
      await loadGraph(selectedDoc);
    } catch (err) {
      setRelError(err instanceof Error ? err.message : String(err));
    } finally {
      setRelSubmitting(false);
    }
  }

  // ── 관계 삭제 ─────────────────────────────────────────────────────────────
  async function handleDeleteRelationship(relId: string) {
    if (!selectedDoc) return;
    try {
      await api.ontologyMgmt.deleteRelationship(selectedDoc, relId);
      showToast(true, "관계 삭제됨");
      await loadGraph(selectedDoc);
    } catch (err) {
      showToast(false, err instanceof Error ? err.message : String(err));
    }
  }

  // ── JSON 내보내기 ──────────────────────────────────────────────────────────
  function handleExport() {
    if (!rawGraph) return;
    const blob = new Blob([JSON.stringify(rawGraph, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${selectedDoc}-graph.json`;
    a.click();
  }

  const selectedNode = rawGraph?.nodes.find((n) => n.id === selectedNodeId) ?? null;
  const outEdges = rawGraph?.edges.filter((e) => e.from === selectedNodeId) ?? [];
  const inEdges  = rawGraph?.edges.filter((e) => e.to   === selectedNodeId) ?? [];

  // ── 렌더 ──────────────────────────────────────────────────────────────────
  return (
    <div className="flex gap-3" style={{ height: 700 }}>

      {/* ── 왼쪽: 타입 팔레트 ──────────────────────────────────────────── */}
      <div className="w-44 shrink-0 flex flex-col gap-2 overflow-y-auto">
        {/* 문서 선택 */}
        <div className="rounded-lg border border-slate-200 bg-white p-2 space-y-1.5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">문서</p>
          <select
            className="w-full border border-slate-200 rounded px-1.5 py-1 text-xs"
            value={selectedDoc}
            onChange={(e) => setSelectedDoc(e.target.value)}
          >
            {docs.length === 0 && <option value="">없음</option>}
            {docs.map((d) => <option key={d.doc_id} value={d.doc_id}>{d.doc_id}</option>)}
          </select>
          <div className="flex gap-1">
            <input
              className="flex-1 border border-slate-200 rounded px-1.5 py-1 text-xs min-w-0"
              placeholder="새 문서 ID"
              value={newDocInput}
              onChange={(e) => setNewDocInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") void handleCreateDoc(); }}
            />
            <button
              className="shrink-0 bg-slate-100 text-slate-600 rounded px-1.5 py-1 text-xs hover:bg-slate-200"
              onClick={() => void handleCreateDoc()}
            >+</button>
          </div>
        </div>

        {/* 엔티티 타입 팔레트 */}
        <div className="rounded-lg border border-slate-200 bg-white p-2 space-y-1">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1">타입 팔레트</p>
          <p className="text-[10px] text-slate-400 leading-tight mb-2">클릭 → 캔버스에 추가</p>
          {allTypes.map((t) => {
            const c = getColor(t);
            return (
              <button
                key={t}
                className="w-full text-left rounded px-2 py-1.5 text-xs font-medium transition hover:opacity-80 disabled:opacity-40"
                style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
                onClick={() => openNodeModal(t)}
                disabled={!canEdit || !selectedDoc}
                title={!canEdit ? "편집 권한 없음" : !selectedDoc ? "문서를 먼저 선택하세요" : `${t} 엔티티 추가`}
              >
                {t}
              </button>
            );
          })}
        </div>

        {/* 범례 */}
        <div className="rounded-lg border border-slate-200 bg-white p-2 space-y-1">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1">사용법</p>
          <p className="text-[10px] text-slate-500 leading-relaxed">
            1. 타입 클릭 → 노드 생성<br />
            2. 노드 핸들 드래그 → 관계 연결<br />
            3. 저장 버튼 → 위치 보존<br />
            4. 노드 클릭 → 상세·삭제
          </p>
        </div>
      </div>

      {/* ── 중앙: 캔버스 ────────────────────────────────────────────────── */}
      <div className="flex-1 rounded-xl border border-slate-200 overflow-hidden relative" ref={reactFlowWrapper}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-10 text-sm text-slate-500">
            로딩 중…
          </div>
        )}
        {toast && <Toast ok={toast.ok} text={toast.text} />}

        {/* 툴바 */}
        <div className="absolute top-2 left-2 flex gap-1.5 z-10 flex-wrap">
          <button
            className="bg-white border border-slate-200 text-slate-700 px-2.5 py-1.5 rounded text-xs shadow-sm hover:bg-slate-50"
            onClick={() => void loadGraph(selectedDoc)}
          >새로고침</button>
          <button
            className="bg-blue-600 text-white px-2.5 py-1.5 rounded text-xs shadow-sm hover:bg-blue-700 disabled:opacity-50"
            onClick={handleSaveLayout}
            disabled={!selectedDoc || nodes.length === 0}
            title="노드 위치를 브라우저에 저장"
          >💾 저장</button>
          <button
            className="bg-white border border-slate-200 text-slate-600 px-2.5 py-1.5 rounded text-xs shadow-sm hover:bg-slate-50 disabled:opacity-40"
            onClick={handleExport}
            disabled={!rawGraph}
            title="그래프 JSON 내보내기"
          >⬇ 내보내기</button>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => setSelectedNodeId(node.id === selectedNodeId ? null : node.id)}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          proOptions={{ hideAttribution: true }}
          deleteKeyCode={null}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e2e8f0" />
          <Controls />
          <MiniMap
            nodeColor={(n) => getColor((n.data as { type?: string }).type ?? "").border}
          />
        </ReactFlow>

        {/* 빈 캔버스 안내 */}
        {!loading && nodes.length === 0 && selectedDoc && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 pointer-events-none">
            <p className="text-sm font-medium">온톨로지가 비어 있습니다</p>
            <p className="text-xs mt-1">왼쪽 팔레트에서 타입을 클릭해 첫 노드를 추가하세요</p>
          </div>
        )}
      </div>

      {/* ── 오른쪽: 노드 상세 ───────────────────────────────────────────── */}
      <div className="w-64 shrink-0 rounded-xl border border-slate-200 bg-white overflow-y-auto p-4">
        {selectedNode ? (
          <>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-800">노드 상세</h3>
              <button className="text-slate-400 hover:text-slate-600 text-xs" onClick={() => setSelectedNodeId(null)}>✕</button>
            </div>
            <div
              className="rounded-md px-3 py-2 mb-3 text-xs font-semibold"
              style={{
                background: getColor(selectedNode.type).bg,
                color: getColor(selectedNode.type).text,
                border: `1px solid ${getColor(selectedNode.type).border}`,
              }}
            >
              {selectedNode.type} · {selectedNode.id}
            </div>
            <p className="text-sm font-medium text-slate-800 mb-3">{selectedNode.label}</p>

            {Object.keys(selectedNode.properties).length > 0 && (
              <div className="mb-4">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1">속성</p>
                <table className="w-full text-xs"><tbody>
                  {Object.entries(selectedNode.properties).map(([k, v]) => (
                    <tr key={k} className="border-b border-slate-50">
                      <td className="py-1 pr-2 text-slate-500 font-medium">{k}</td>
                      <td className="py-1 text-slate-700 break-all">{String(v ?? "-")}</td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
            )}

            {outEdges.length > 0 && (
              <div className="mb-3">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1">→ Outgoing ({outEdges.length})</p>
                {outEdges.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-xs text-slate-600">
                      <span className="font-medium text-blue-600">{e.label}</span> → {e.to}
                    </span>
                    {canEdit && (
                      <button className="text-rose-400 hover:text-rose-600 text-xs ml-1"
                        onClick={() => void handleDeleteRelationship(e.id)}>✕</button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {inEdges.length > 0 && (
              <div className="mb-3">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1">← Incoming ({inEdges.length})</p>
                {inEdges.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-xs text-slate-600">
                      {e.from} → <span className="font-medium text-amber-600">{e.label}</span>
                    </span>
                    {canEdit && (
                      <button className="text-rose-400 hover:text-rose-600 text-xs ml-1"
                        onClick={() => void handleDeleteRelationship(e.id)}>✕</button>
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
            <p>노드를 클릭하면<br />상세 정보와 관계를<br />표시합니다.</p>
            {rawGraph && (
              <p className="mt-2 text-slate-300">{rawGraph.nodes.length}개 노드 · {rawGraph.edges.length}개 엣지</p>
            )}
          </div>
        )}
      </div>

      {/* ── 노드 추가 모달 ──────────────────────────────────────────────── */}
      {nodeModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="text-sm font-bold text-slate-800 mb-4">
              <span
                className="inline-block rounded px-2 py-0.5 text-xs mr-2"
                style={{ background: getColor(nodeType).bg, color: getColor(nodeType).text, border: `1px solid ${getColor(nodeType).border}` }}
              >{nodeType}</span>
              엔티티 추가
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">이름 *</label>
                <input
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-300"
                  placeholder={`예: 삼성전자`}
                  value={nodeName}
                  onChange={(e) => setNodeName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") void handleAddNode(); }}
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">속성 (JSON, 선택)</label>
                <textarea
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-blue-300"
                  placeholder={`{"department": "개발팀"}`}
                  rows={3}
                  value={nodeProps}
                  onChange={(e) => setNodeProps(e.target.value)}
                />
              </div>
              {nodeError && <p className="text-xs text-rose-600 bg-rose-50 rounded p-2">{nodeError}</p>}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                className="flex-1 bg-blue-600 text-white text-sm py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
                onClick={() => void handleAddNode()}
                disabled={nodeSubmitting}
              >
                {nodeSubmitting ? "추가 중…" : "추가"}
              </button>
              <button
                className="flex-1 bg-slate-100 text-slate-700 text-sm py-1.5 rounded hover:bg-slate-200"
                onClick={() => { setNodeModal(false); setNodeError(null); }}
              >취소</button>
            </div>
          </div>
        </div>
      )}

      {/* ── 관계 추가 모달 (onConnect 트리거) ────────────────────────── */}
      {edgeModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="text-sm font-bold text-slate-800 mb-1">관계 연결</h3>
            <p className="text-xs text-slate-400 mb-4">
              {pendingConn?.source} → {pendingConn?.target}
            </p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">관계명 *</label>
                <input
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-300"
                  placeholder="예: BELONGS_TO"
                  value={relName}
                  onChange={(e) => setRelName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") void handleConfirmEdge(); }}
                  autoFocus
                />
              </div>
              {relError && <p className="text-xs text-rose-600 bg-rose-50 rounded p-2">{relError}</p>}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                className="flex-1 bg-blue-600 text-white text-sm py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
                onClick={() => void handleConfirmEdge()}
                disabled={relSubmitting}
              >
                {relSubmitting ? "연결 중…" : "연결"}
              </button>
              <button
                className="flex-1 bg-slate-100 text-slate-700 text-sm py-1.5 rounded hover:bg-slate-200"
                onClick={() => { setEdgeModal(false); setPendingConn(null); setRelError(null); }}
              >취소</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
