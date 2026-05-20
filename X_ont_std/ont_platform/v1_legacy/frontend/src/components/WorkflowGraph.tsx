"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Background,
  BackgroundVariant,
  Connection,
  Controls,
  Edge,
  EdgeChange,
  MiniMap,
  Node,
  NodeChange,
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "@/lib/api";
import type { GraphNodeData, GraphNodeKind, WorkflowGraph } from "@/types/api";
// Phase 2: WorkflowRun 타입은 향후 실행 이력 UI 확장에서 사용 예정

type NodePaletteItem = { kind: GraphNodeKind; label: string; color: string };

const PALETTE: NodePaletteItem[] = [
  { kind: "start", label: "Start", color: "#10b981" },
  { kind: "llm", label: "LLM", color: "#6366f1" },
  { kind: "http", label: "HTTP", color: "#0ea5e9" },
  { kind: "condition", label: "Condition", color: "#f59e0b" },
  // WG-3 도메인 노드 — Ontology + PolicyEngine과 결합
  { kind: "approve_order", label: "ApproveOrder", color: "#22c55e" },
  { kind: "risk_assess", label: "RiskAssess", color: "#a855f7" },
  { kind: "end", label: "End", color: "#ef4444" },
];

function newId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 8)}`;
}

interface StepResult {
  node_id: string;
  label: string;
  type: string;
  status: "running" | "success" | "error" | "skipped";
  output: string;
  started_at: string;
  duration_ms: number;
}

export function WorkflowGraphPanel({ user }: { user: string }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [graphId, setGraphId] = useState<string | null>(null);
  const [graphName, setGraphName] = useState("새 워크플로우");
  const [graphsList, setGraphsList] = useState<WorkflowGraph[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<StepResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId]
  );

  const refreshList = useCallback(async () => {
    try {
      const res = await api.workflowGraphs.list(user);
      setGraphsList(res.graphs);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [user]);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  // --- 캔버스 핸들러 ---

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );
  const onConnect = useCallback(
    (conn: Connection) =>
      setEdges((eds) =>
        addEdge({ ...conn, id: newId("e"), animated: true }, eds)
      ),
    []
  );

  function addNode(kind: GraphNodeKind) {
    const id = newId("n");
    const item = PALETTE.find((p) => p.kind === kind)!;
    const newNode: Node = {
      id,
      type: "default",
      position: { x: 80 + Math.random() * 300, y: 80 + Math.random() * 200 },
      data: { label: `${item.label} ${id.slice(2, 5)}`, kind, status: "idle" } satisfies GraphNodeData & {
        kind: GraphNodeKind;
      },
      style: {
        background: "#fff",
        border: `2px solid ${item.color}`,
        borderRadius: 8,
        padding: 8,
        fontWeight: 600,
        fontSize: 12,
      },
    };
    setNodes((nds) => nds.concat(newNode));
  }

  function updateNodeData(id: string, patch: Partial<GraphNodeData>) {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === id ? { ...n, data: { ...(n.data as any), ...patch } } : n
      )
    );
  }

  // --- 저장 / 불러오기 ---

  async function handleSave() {
    setError(null);
    setToast(null);
    try {
      const payload = {
        id: graphId ?? undefined,
        name: graphName,
        nodes: nodes.map((n) => ({
          id: n.id,
          type: ((n.data as any)?.kind ?? "start") as GraphNodeKind,
          position: n.position,
          data: {
            label: (n.data as any)?.label,
            prompt: (n.data as any)?.prompt,
            url: (n.data as any)?.url,
            method: (n.data as any)?.method,
            expression: (n.data as any)?.expression,
            order_id: (n.data as any)?.order_id,
            customer_id: (n.data as any)?.customer_id,
          },
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: typeof e.label === "string" ? e.label : undefined,
        })),
      };
      const saved = await api.workflowGraphs.save(user, payload as any);
      setGraphId(saved.id);
      setToast({ kind: "ok", text: `저장 완료: ${saved.id}` });
      await refreshList();
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    }
  }

  async function handleLoad(id: string) {
    setError(null);
    setToast(null);
    try {
      const g = await api.workflowGraphs.get(user, id);
      setGraphId(g.id);
      setGraphName(g.name);
      setNodes(
        g.nodes.map((n) => {
          const item = PALETTE.find((p) => p.kind === n.type) ?? PALETTE[0];
          return {
            id: n.id,
            type: "default",
            position: n.position,
            data: { ...n.data, kind: n.type, label: n.data?.label ?? item.label, status: "idle" },
            style: {
              background: "#fff",
              border: `2px solid ${item.color}`,
              borderRadius: 8,
              padding: 8,
              fontWeight: 600,
              fontSize: 12,
            },
          } as Node;
        })
      );
      setEdges(
        g.edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
          animated: true,
        }))
      );
      setResults([]);
      setSelectedNodeId(null);
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    }
  }

  function handleNew() {
    setGraphId(null);
    setGraphName("새 워크플로우");
    setNodes([]);
    setEdges([]);
    setResults([]);
    setSelectedNodeId(null);
    setToast(null);
  }

  async function handleDelete() {
    if (!graphId) return;
    if (!window.confirm(`${graphId} 를 삭제할까요? (Admin 권한 필요)`)) return;
    try {
      await api.workflowGraphs.remove(user, graphId);
      setToast({ kind: "ok", text: "삭제 완료" });
      handleNew();
      await refreshList();
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    }
  }

  // --- 실행 (Phase 2: 서버 SSE 스트리밍) ---

  async function handleRun() {
    setError(null);
    setResults([]);
    if (!graphId) {
      setToast({ kind: "err", text: "먼저 워크플로우를 저장한 뒤 실행하세요." });
      return;
    }
    if (nodes.length === 0) {
      setToast({ kind: "err", text: "노드가 없습니다." });
      return;
    }
    setRunning(true);
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...(n.data as any), status: "idle" } })));

    const url = api.workflowGraphs.runStreamUrl(user, graphId);
    let response: Response;
    try {
      response = await fetch(url, { method: "POST", headers: { Accept: "text/event-stream" } });
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
      setRunning(false);
      return;
    }
    if (!response.ok || !response.body) {
      const text = await response.text().catch(() => "");
      setToast({ kind: "err", text: `실행 실패: ${response.status} ${text}` });
      setRunning(false);
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";
        for (const frame of frames) handleSseFrame(frame);
      }
      if (buffer.trim()) handleSseFrame(buffer);
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setRunning(false);
    }
  }

  function handleSseFrame(frame: string) {
    const lines = frame.split("\n").map((l) => l.trim()).filter(Boolean);
    let eventType = "";
    let dataLine = "";
    for (const line of lines) {
      if (line.startsWith("event:")) eventType = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLine = line.slice(5).trim();
    }
    if (!eventType || !dataLine) return;
    let data: any;
    try {
      data = JSON.parse(dataLine);
    } catch {
      return;
    }
    if (eventType === "node_started") {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === data.node_id ? { ...n, data: { ...(n.data as any), status: "running" } } : n
        )
      );
    } else if (eventType === "node_finished") {
      const outputStr =
        typeof data.output === "string" ? data.output : JSON.stringify(data.output);
      setNodes((nds) =>
        nds.map((n) =>
          n.id === data.node_id
            ? {
                ...n,
                data: { ...(n.data as any), status: data.status, result: outputStr },
              }
            : n
        )
      );
      setResults((rs) =>
        rs.concat({
          node_id: data.node_id,
          label: data.label ?? data.node_id,
          type: data.type ?? "?",
          status: data.status,
          output: outputStr ?? data.error ?? "",
          started_at: data.started_at,
          duration_ms: data.duration_ms ?? 0,
        })
      );
    } else if (eventType === "run_finished") {
      setToast({
        kind: data.status === "completed" ? "ok" : "err",
        text: `실행 ${data.status} (${data.completed_count} 단계)`,
      });
    } else if (eventType === "run_failed") {
      setToast({ kind: "err", text: `실행 실패: ${data.error}` });
    }
  }

  // --- 렌더 ---

  return (
    <div className="space-y-3">
      <section className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-3">
            <h3 className="text-sm font-semibold">워크플로우 캔버스</h3>
            <input
              value={graphName}
              onChange={(e) => setGraphName(e.target.value)}
              className="rounded-md border border-slate-300 px-2 py-1 text-sm w-56"
              placeholder="워크플로우 이름"
            />
            <span className="text-xs text-slate-400">{graphId ?? "신규"}</span>
          </div>
          <div className="flex gap-2">
            <select
              className="rounded-md border border-slate-300 px-2 py-1 text-xs"
              value={graphId ?? ""}
              onChange={(e) => {
                const v = e.target.value;
                if (v) void handleLoad(v);
                else handleNew();
              }}
            >
              <option value="">— 불러오기 —</option>
              {graphsList.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.id.slice(0, 10)})
                </option>
              ))}
            </select>
            <button className="btn btn-ghost text-xs py-1 px-2" onClick={handleNew}>
              새로
            </button>
            <button className="btn btn-primary text-xs py-1 px-2" onClick={handleSave}>
              저장
            </button>
            <button className="btn btn-ok text-xs py-1 px-2" onClick={handleRun} disabled={running}>
              {running ? "실행 중…" : "실행"}
            </button>
            <button className="btn btn-danger text-xs py-1 px-2" onClick={handleDelete} disabled={!graphId}>
              삭제
            </button>
          </div>
        </div>
        {toast && (
          <div className="px-3 py-2 text-xs">
            <span
              className={
                toast.kind === "ok"
                  ? "text-emerald-700"
                  : "text-rose-700"
              }
            >
              {toast.text}
            </span>
          </div>
        )}
        <div className="flex" style={{ height: 480 }}>
          {/* 좌측 팔레트 */}
          <div className="w-32 shrink-0 border-r border-slate-200 p-2 flex flex-col gap-1">
            <div className="text-[10px] uppercase text-slate-400 mb-1">노드 추가</div>
            {PALETTE.map((p) => (
              <button
                key={p.kind}
                className="btn btn-ghost text-xs py-1 px-2"
                style={{ borderColor: p.color }}
                onClick={() => addNode(p.kind)}
              >
                + {p.label}
              </button>
            ))}
          </div>

          {/* 캔버스 */}
          <div className="flex-1 relative">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, n) => setSelectedNodeId(n.id)}
              onPaneClick={() => setSelectedNodeId(null)}
              fitView
            >
              <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
              <Controls />
              <MiniMap pannable zoomable />
            </ReactFlow>
          </div>

          {/* 우측 속성 패널 */}
          <div className="w-72 shrink-0 border-l border-slate-200 p-3 overflow-y-auto">
            {selectedNode ? (
              <div className="space-y-2 text-xs">
                <div className="font-semibold text-sm">속성 편집</div>
                <div className="text-slate-400">{selectedNode.id}</div>
                <label className="block">
                  <span className="text-slate-500">Label</span>
                  <input
                    className="w-full rounded-md border border-slate-300 px-2 py-1"
                    value={(selectedNode.data as any)?.label ?? ""}
                    onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
                  />
                </label>
                {(selectedNode.data as any)?.kind === "llm" && (
                  <label className="block">
                    <span className="text-slate-500">Prompt</span>
                    <textarea
                      rows={4}
                      className="w-full rounded-md border border-slate-300 px-2 py-1"
                      value={(selectedNode.data as any)?.prompt ?? ""}
                      onChange={(e) => updateNodeData(selectedNode.id, { prompt: e.target.value })}
                    />
                  </label>
                )}
                {(selectedNode.data as any)?.kind === "http" && (
                  <>
                    <label className="block">
                      <span className="text-slate-500">URL</span>
                      <input
                        className="w-full rounded-md border border-slate-300 px-2 py-1"
                        value={(selectedNode.data as any)?.url ?? ""}
                        onChange={(e) => updateNodeData(selectedNode.id, { url: e.target.value })}
                      />
                    </label>
                    <label className="block">
                      <span className="text-slate-500">Method</span>
                      <select
                        className="w-full rounded-md border border-slate-300 px-2 py-1"
                        value={(selectedNode.data as any)?.method ?? "GET"}
                        onChange={(e) => updateNodeData(selectedNode.id, { method: e.target.value })}
                      >
                        {["GET", "POST", "PUT", "DELETE"].map((m) => (
                          <option key={m}>{m}</option>
                        ))}
                      </select>
                    </label>
                  </>
                )}
                {(selectedNode.data as any)?.kind === "condition" && (
                  <label className="block">
                    <span className="text-slate-500">Expression</span>
                    <input
                      className="w-full rounded-md border border-slate-300 px-2 py-1"
                      value={(selectedNode.data as any)?.expression ?? ""}
                      onChange={(e) => updateNodeData(selectedNode.id, { expression: e.target.value })}
                      placeholder='예: risk_tier == "High"'
                    />
                  </label>
                )}
                {(selectedNode.data as any)?.kind === "approve_order" && (
                  <label className="block">
                    <span className="text-slate-500">Order ID</span>
                    <input
                      className="w-full rounded-md border border-slate-300 px-2 py-1"
                      value={(selectedNode.data as any)?.order_id ?? ""}
                      onChange={(e) => updateNodeData(selectedNode.id, { order_id: e.target.value })}
                      placeholder="O001"
                    />
                  </label>
                )}
                {(selectedNode.data as any)?.kind === "risk_assess" && (
                  <label className="block">
                    <span className="text-slate-500">Customer ID</span>
                    <input
                      className="w-full rounded-md border border-slate-300 px-2 py-1"
                      value={(selectedNode.data as any)?.customer_id ?? ""}
                      onChange={(e) => updateNodeData(selectedNode.id, { customer_id: e.target.value })}
                      placeholder="C001"
                    />
                  </label>
                )}
                {(selectedNode.data as any)?.status && (
                  <div className="text-slate-500">
                    상태: <span className="badge badge-neutral">{(selectedNode.data as any).status}</span>
                  </div>
                )}
                {(selectedNode.data as any)?.result && (
                  <div className="text-slate-600 break-words">
                    결과: <code>{String((selectedNode.data as any).result)}</code>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-400">노드를 선택하면 속성 편집 패널이 표시됩니다.</div>
            )}
          </div>
        </div>
      </section>

      {/* 실행 결과 테이블 */}
      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">노드별 실행 결과</h3>
          <span className="text-xs text-slate-500">{results.length}건</span>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Node</th>
                <th>Type</th>
                <th>Status</th>
                <th>Duration (ms)</th>
                <th>Output</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">
                    아직 실행 결과가 없습니다. '실행' 버튼을 눌러주세요.
                  </td>
                </tr>
              ) : (
                results.map((r, i) => (
                  <tr key={`${r.node_id}-${i}`}>
                    <td>{i + 1}</td>
                    <td className="font-semibold">{r.label}</td>
                    <td>{r.type}</td>
                    <td>
                      <span
                        className={`badge ${
                          r.status === "success"
                            ? "badge-low"
                            : r.status === "error"
                            ? "badge-high"
                            : r.status === "skipped"
                            ? "badge-neutral"
                            : "badge-medium"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td>{r.duration_ms}</td>
                    <td className="text-slate-600 break-words max-w-[300px]">{r.output}</td>
                    <td className="text-xs text-slate-400">{new Date(r.started_at).toLocaleTimeString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
      {error && <div className="text-sm text-rose-600">{error}</div>}
    </div>
  );
}
