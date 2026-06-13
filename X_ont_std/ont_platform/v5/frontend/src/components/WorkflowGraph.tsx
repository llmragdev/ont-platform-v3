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
import { Copy, Play, RotateCcw, Save, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type { GraphNodeData, GraphNodeKind, WorkflowGraph, WorkflowOntologyMapping, WorkflowRun } from "@/types/api";
import { WorkflowRunHistory } from "@/components/WorkflowRunHistory";

type NodePaletteItem = { kind: GraphNodeKind; label: string; color: string };

const FACTORY_NODE_LABELS: Record<string, string> = {
  "request-input": "현장 요청 입력",
  "category-classify": "고장/품질 분류",
  "asset-map": "공장-라인-설비 매핑",
  "recurrence-check": "반복 여부 확인",
  "fault-register": "고장 상황 등록",
  "maintenance-task": "정비팀 확인 건 생성",
  "quality-link": "품질 문제 연결",
  "draft-response": "현장 안내 답변 생성",
  "notify-teams": "정비/품질팀 알림",
  "ontology-write": "온톨로지 저장",
};

const PALETTE: NodePaletteItem[] = [
  { kind: "request_input", label: "Request Input", color: "#0f766e" },
  { kind: "intent_classify", label: "Intent Classify", color: "#2563eb" },
  { kind: "equipment_map", label: "Asset Map", color: "#0d9488" },
  { kind: "recurrence_check", label: "Repeat Check", color: "#a16207" },
  { kind: "knowledge_lookup", label: "Knowledge Lookup", color: "#7c3aed" },
  { kind: "policy_search", label: "Policy Search", color: "#4f46e5" },
  { kind: "evidence_gate", label: "Evidence Gate", color: "#ca8a04" },
  { kind: "approval_check", label: "Approval Check", color: "#ea580c" },
  { kind: "action_plan", label: "Action Plan", color: "#0891b2" },
  { kind: "draft_response", label: "Draft Response", color: "#0e7490" },
  { kind: "customer_mcp_comment_create", label: "MCP Comment", color: "#059669" },
  { kind: "maintenance_task", label: "Maintenance", color: "#b45309" },
  { kind: "quality_link", label: "Quality Link", color: "#be185d" },
  { kind: "ontology_write", label: "Ontology Write", color: "#475569" },
  { kind: "human_handoff", label: "Human Handoff", color: "#be123c" },
  { kind: "notify_user", label: "Notify User", color: "#16a34a" },
  { kind: "start", label: "Start", color: "#10b981" },
  { kind: "condition", label: "Condition", color: "#f59e0b" },
  { kind: "llm", label: "LLM", color: "#6366f1" },
  { kind: "http", label: "HTTP", color: "#0ea5e9" },
  { kind: "end", label: "End", color: "#ef4444" },
];

interface StepResult {
  node_id: string;
  label: string;
  type: string;
  status: "running" | "success" | "error" | "skipped";
  output: string;
  started_at: string;
  duration_ms: number;
}

interface SimulationResult {
  category: string;
  route: "auto_reply" | "wait_approval" | "manual_handoff";
  evidence: string[];
  answer: string;
}

function newId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 8)}`;
}

function nodeStyle(kind: GraphNodeKind) {
  const item = PALETTE.find((p) => p.kind === kind) ?? PALETTE[0];
  return {
    background: "#fff",
    border: `2px solid ${item.color}`,
    borderRadius: 8,
    padding: 8,
    fontWeight: 600,
    fontSize: 12,
  };
}

function toFlowNode(node: WorkflowGraph["nodes"][number]): Node {
  return {
    id: node.id,
    type: "default",
    position: node.position,
    data: { ...node.data, kind: node.type, label: node.data?.label ?? node.type, status: "idle" },
    style: nodeStyle(node.type),
  };
}

function normalizeNodeForExecutor(
  node: WorkflowGraph["nodes"][number],
  executor?: string
): WorkflowGraph["nodes"][number] {
  if (executor !== "factory.repeated_fault_response") return node;
  const label = FACTORY_NODE_LABELS[node.id];
  if (!label) return node;
  return { ...node, data: { ...node.data, label } };
}

function simulateRequest(text: string): SimulationResult {
  const normalized = text.toLowerCase();
  if (text.includes("비밀번호") || normalized.includes("password")) {
    const needsApproval = text.includes("결재") || text.includes("승인");
    return {
      category: "account_action / password_reset",
      route: needsApproval ? "wait_approval" : "manual_handoff",
      evidence: ["계정 운영 규정", "승인 후 계정 조치 템플릿", "ITSM 처리 매뉴얼"],
      answer: needsApproval
        ? "비밀번호 초기화 요청으로 분류했습니다. 승인 상태를 확인한 뒤 계정 담당자 처리 단계로 이관합니다."
        : "비밀번호 초기화는 계정 조치에 해당하므로 자동 완료하지 않고 담당자 수동 처리로 이관합니다.",
    };
  }
  if (text.includes("VPN") || normalized.includes("vpn")) {
    return {
      category: "incident / vpn",
      route: "auto_reply",
      evidence: ["VPN 장애 FAQ", "최근 장애 공지", "네트워크 운영 매뉴얼"],
      answer: "VPN 접속 장애로 분류했습니다. 1차 조치 안내를 자동 답변으로 생성하고, 지속 시 헬프데스크 이관 조건을 적용합니다.",
    };
  }
  if (text.includes("권한") || text.includes("SAP")) {
    return {
      category: "permission_request",
      route: "auto_reply",
      evidence: ["권한 신청 정책", "조직별 승인자 매핑", "SAP 권한 신청 양식"],
      answer: "권한 요청 안내로 분류했습니다. 신청 경로와 승인 조건을 근거 기반 답변으로 제공합니다.",
    };
  }
  return {
    category: "unknown",
    route: "manual_handoff",
    evidence: ["근거 부족"],
    answer: "자동 분류 신뢰도가 낮습니다. 담당자 검토로 이관하는 것이 안전합니다.",
  };
}

export function WorkflowGraphPanel() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [graphId, setGraphId] = useState<string | null>(null);
  const [graphName, setGraphName] = useState("New Workflow");
  const [graphsList, setGraphsList] = useState<WorkflowGraph[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<StepResult[]>([]);
  const [toast, setToast] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [graphMeta, setGraphMeta] = useState<Partial<WorkflowGraph>>({});
  const [scenarioMode, setScenarioMode] = useState<"dry_run" | "post">("post");
  const [batchStatus, setBatchStatus] = useState("open");
  const [batchLimit, setBatchLimit] = useState(10);
  const [forceReprocess, setForceReprocess] = useState(false);
  const [ontologyMappings, setOntologyMappings] = useState<WorkflowOntologyMapping[]>([]);
  const [selectedMappingId, setSelectedMappingId] = useState("scenario1.customer_question_auto_reply.v1");
  const [mappingInstalling, setMappingInstalling] = useState(false);
  const [requestText, setRequestText] = useState("결재 후 비밀번호 초기화를 요청합니다.");
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId]
  );
  const selectedOntologyMapping = useMemo(
    () => ontologyMappings.find((item) => item.mapping_id === selectedMappingId) ?? ontologyMappings[0] ?? null,
    [ontologyMappings, selectedMappingId]
  );

  const refreshList = useCallback(async () => {
    try {
      const res = await api.workflowGraphs.list();
      setGraphsList(Array.isArray(res) ? res : []);
      return Array.isArray(res) ? res : [];
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
      return [];
    }
  }, []);

  const loadRuns = useCallback(async (gId: string) => {
    setRunsLoading(true);
    try {
      const res = await api.workflowGraphs.listRuns(gId);
      setRuns(Array.isArray(res.runs) ? res.runs : []);
    } catch {
      setRuns([]);
    } finally {
      setRunsLoading(false);
    }
  }, []);

  const handleLoad = useCallback(async (id: string) => {
    setToast(null);
    try {
      const g = await api.workflowGraphs.get(id);
      setGraphId(g.id);
      setGraphName(g.name);
      setGraphMeta(g);
      setScenarioMode(
        g.runtime?.executor === "scenario1.customer_question_auto_reply" ||
        g.runtime?.executor === "factory.repeated_fault_response"
          ? "post"
          : (g.runtime?.default_mode ?? "dry_run")
      );
      const matchedMapping = ontologyMappings.find((item) => item.workflow_executor === g.runtime?.executor);
      if (matchedMapping) setSelectedMappingId(matchedMapping.mapping_id);
      setBatchStatus(g.runtime?.batch_status ?? "open");
      setBatchLimit(g.runtime?.batch_limit ?? 10);
      setNodes(g.nodes.map((node) => toFlowNode(normalizeNodeForExecutor(node, g.runtime?.executor))));
      setEdges(g.edges.map((e) => ({ id: e.id, source: e.source, target: e.target, label: e.label, animated: true })));
      setResults([]);
      setSelectedNodeId(null);
      void loadRuns(id);
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    }
  }, [loadRuns, ontologyMappings]);

  useEffect(() => {
    void refreshList().then((items) => {
      const clonedId = typeof window !== "undefined" ? window.localStorage.getItem("workflow:lastClonedGraphId") : null;
      if (clonedId && items.some((g) => g.id === clonedId)) {
        window.localStorage.removeItem("workflow:lastClonedGraphId");
        void handleLoad(clonedId);
        setToast({ kind: "ok", text: "복제한 템플릿을 Builder로 불러왔습니다." });
      }
    });
  }, [handleLoad, refreshList]);

  useEffect(() => {
    api.workflowOntologyMappings.list()
      .then((res) => {
        const items = Array.isArray(res.items) ? res.items : [];
        setOntologyMappings(items);
        if (items[0]) setSelectedMappingId(items[0].mapping_id);
      })
      .catch(() => setOntologyMappings([]));
  }, []);

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
      setEdges((eds) => addEdge({ ...conn, id: newId("e"), animated: true }, eds)),
    []
  );

  function addNode(kind: GraphNodeKind) {
    const id = newId("n");
    const item = PALETTE.find((p) => p.kind === kind) ?? PALETTE[0];
    const newNode: Node = {
      id,
      type: "default",
      position: { x: 80 + Math.random() * 300, y: 80 + Math.random() * 200 },
      data: { label: `${item.label} ${id.slice(2, 5)}`, kind, status: "idle" } as GraphNodeData & { kind: GraphNodeKind },
      style: nodeStyle(kind),
    };
    setNodes((nds) => nds.concat(newNode));
  }

  function updateNodeData(id: string, patch: Partial<GraphNodeData>) {
    setNodes((nds) => nds.map((n) => n.id === id ? { ...n, data: { ...(n.data as object), ...patch } } : n));
  }

  async function handleSave() {
    setToast(null);
    try {
      const payload = {
        id: graphId ?? undefined,
        name: graphName,
        nodes: nodes.map((n) => ({
          id: n.id,
          type: ((n.data as { kind?: GraphNodeKind })?.kind ?? "start") as GraphNodeKind,
          position: n.position,
          data: {
            label: (n.data as { label?: string })?.label,
            prompt: (n.data as { prompt?: string })?.prompt,
            url: (n.data as { url?: string })?.url,
            method: (n.data as { method?: string })?.method,
            expression: (n.data as { expression?: string })?.expression,
          },
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: typeof e.label === "string" ? e.label : undefined,
        })),
        scenario_id: graphMeta.scenario_id,
        scenario_version: graphMeta.scenario_version,
        template_id: graphMeta.template_id,
        template_version: graphMeta.template_version,
        graph_kind: graphMeta.graph_kind,
        execution_mode: graphMeta.execution_mode,
        runtime: graphMeta.runtime,
        tenant_scope: graphMeta.tenant_scope,
        source: graphMeta.source,
      };
      const saved = await api.workflowGraphs.save(payload as Partial<WorkflowGraph>);
      setGraphId(saved.id);
      setToast({ kind: "ok", text: `????꾨즺: ${saved.id}` });
      await refreshList();
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    }
  }

  function handleNew() {
    setGraphId(null);
    setGraphName("New Workflow");
    setNodes([]);
    setEdges([]);
    setResults([]);
    setRuns([]);
    setGraphMeta({});
    setSelectedNodeId(null);
    setToast(null);
  }

  async function handleDelete() {
    if (!graphId) return;
    if (!window.confirm(`${graphId} 洹몃옒?꾨? ??젣?좉퉴??`)) return;
    try {
      await api.workflowGraphs.remove(graphId);
      setToast({ kind: "ok", text: "??젣 ?꾨즺" });
      handleNew();
      await refreshList();
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    }
  }

  async function handleClone() {
    if (!graphId) {
      setToast({ kind: "err", text: "Select a saved workflow first." });
      return;
    }
    try {
      const cloned = await api.workflowGraphs.clone(graphId, `${graphName} Copy`);
      setToast({ kind: "ok", text: `Clone saved: ${cloned.id}` });
      await refreshList();
      await handleLoad(cloned.id);
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    }
  }

  async function handleRun() {
    setResults([]);
    if (!graphId) {
      setToast({ kind: "err", text: "癒쇱? ?뚰겕?뚮줈?곕? ??ν븳 ???ㅽ뻾?섏꽭??" });
      return;
    }
    if (nodes.length === 0) {
      setToast({ kind: "err", text: "노드가 없습니다." });
      return;
    }
    setRunning(true);
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...(n.data as object), status: "idle" } })));

    let response: Response;
    try {
      response = await fetch(api.workflowGraphs.runStreamUrl(graphId), {
        method: "POST",
        headers: { ...api.workflowGraphs.runStreamHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          execution_mode: graphMeta.runtime?.executor ? "batch" : "simulation",
          mode: scenarioMode,
          status: batchStatus,
          limit: batchLimit,
          force_reprocess: forceReprocess,
        }),
      });
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
      setRunning(false);
      return;
    }
    if (!response.ok || !response.body) {
      const text = await response.text().catch(() => "");
      setToast({ kind: "err", text: `?ㅽ뻾 ?ㅽ뙣: ${response.status} ${text}` });
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
      if (graphId) void loadRuns(graphId);
    }
  }

  async function handleInstallOntologyMapping() {
    if (!selectedMappingId) return;
    setMappingInstalling(true);
    try {
      const result = await api.workflowOntologyMappings.installSchema(selectedMappingId);
      setToast({
        kind: "ok",
        text: `Ontology schema installed: +${result.entity_types_added} types, +${result.relation_types_added} relations`,
      });
    } catch (e) {
      setToast({ kind: "err", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setMappingInstalling(false);
    }
  }

  function handleSseFrame(frame: string) {
    const lines = frame.split("\n").map((line) => line.trim()).filter(Boolean);
    let eventType = "";
    let dataLine = "";
    for (const line of lines) {
      if (line.startsWith("event:")) eventType = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLine = line.slice(5).trim();
    }
    if (!eventType || !dataLine) return;
    let data: Record<string, unknown>;
    try { data = JSON.parse(dataLine); } catch { return; }

    if (eventType === "node_started") {
      setNodes((nds) => nds.map((n) => n.id === data.node_id ? { ...n, data: { ...(n.data as object), status: "running" } } : n));
    } else if (eventType === "node_finished") {
      const outputStr = typeof data.output === "string" ? data.output : JSON.stringify(data.output);
      setNodes((nds) => nds.map((n) => n.id === data.node_id ? { ...n, data: { ...(n.data as object), status: data.status, result: outputStr } } : n));
      setResults((rs) => rs.concat({
        node_id: String(data.node_id),
        label: String(data.label ?? data.node_id),
        type: String(data.type ?? "?"),
        status: (data.status as StepResult["status"]) ?? "success",
        output: outputStr ?? String(data.error ?? ""),
        started_at: String(data.started_at),
        duration_ms: Number(data.duration_ms ?? 0),
      }));
    } else if (eventType === "run_finished") {
      setToast({ kind: data.status === "completed" ? "ok" : "err", text: `?ㅽ뻾 ${data.status} (${data.completed_count} ?④퀎)` });
    } else if (eventType === "run_failed") {
      setToast({ kind: "err", text: `?ㅽ뻾 ?ㅽ뙣: ${data.error}` });
    }
  }

  function runLocalSimulation() {
    setSimulation(simulateRequest(requestText));
  }

  return (
    <div className="space-y-4">
      <section className="panel">
        <div className="panel-header gap-3">
          <div className="flex min-w-0 flex-wrap items-center gap-3">
            <h3 className="text-sm font-semibold text-slate-950 dark:text-slate-100">Workflow Builder</h3>
            <input
              value={graphName}
              onChange={(e) => setGraphName(e.target.value)}
              className="w-60 rounded-md border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-950"
              placeholder="?뚰겕?뚮줈???대쫫"
            />
            <span className="text-xs text-slate-400">{graphId ?? "?좉퇋"}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              className="rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-950"
              value={graphId ?? ""}
              onChange={(e) => { const value = e.target.value; if (value) void handleLoad(value); else handleNew(); }}
            >
              <option value="">遺덈윭?ㅺ린</option>
              {graphsList.map((g) => (
                <option key={g.id} value={g.id}>{g.name} ({g.id.slice(0, 10)})</option>
              ))}
            </select>
            <button className="btn btn-ghost text-xs" onClick={handleNew}><RotateCcw className="mr-1 h-3 w-3" />New</button>
            <button className="btn btn-primary bg-teal-700 text-xs hover:bg-teal-800" onClick={() => void handleSave()}><Save className="mr-1 h-3 w-3" />Save</button>
            <button className="btn btn-ghost text-xs" onClick={() => void handleClone()} disabled={!graphId}><Copy className="mr-1 h-3 w-3" />Clone</button>
            <button className="btn btn-ok text-xs" onClick={() => void handleRun()} disabled={running}><Play className="mr-1 h-3 w-3" />{running ? "Running" : "Run"}</button>
            <button className="btn btn-danger text-xs" onClick={() => void handleDelete()} disabled={!graphId}><Trash2 className="mr-1 h-3 w-3" />Delete</button>
          </div>
        </div>
        {toast && (
          <div className="px-3 py-2 text-xs">
            <span className={toast.kind === "ok" ? "text-emerald-700" : "text-rose-700"}>{toast.text}</span>
          </div>
        )}
        {graphMeta.runtime?.executor === "scenario1.customer_question_auto_reply" && (
          <div className="border-t border-slate-200 px-3 py-3 text-xs dark:border-slate-800">
            <div className="flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-slate-500">Comment mode</span>
                <select className="rounded-md border border-slate-300 px-2 py-1 dark:border-slate-700 dark:bg-slate-950" value={scenarioMode} onChange={(e) => setScenarioMode(e.target.value as "dry_run" | "post")}>
                  <option value="dry_run">dry_run</option>
                  <option value="post">post</option>
                </select>
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-slate-500">Status</span>
                <input className="w-24 rounded-md border border-slate-300 px-2 py-1 dark:border-slate-700 dark:bg-slate-950" value={batchStatus} onChange={(e) => setBatchStatus(e.target.value)} />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-slate-500">Limit</span>
                <input type="number" min={1} max={100} className="w-20 rounded-md border border-slate-300 px-2 py-1 dark:border-slate-700 dark:bg-slate-950" value={batchLimit} onChange={(e) => setBatchLimit(Number(e.target.value || 10))} />
              </label>
              <label className="flex items-center gap-2 pb-1 text-slate-600 dark:text-slate-300">
                <input type="checkbox" checked={forceReprocess} onChange={(e) => setForceReprocess(e.target.checked)} />
                Force reprocess
              </label>
              <span className="pb-1 text-slate-400">Executor: {graphMeta.runtime.executor}</span>
            </div>
            <div className="mt-3 grid gap-3 rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950 lg:grid-cols-[minmax(220px,0.8fr)_minmax(0,1.2fr)]">
              <div className="space-y-2">
                <div className="font-semibold text-slate-700 dark:text-slate-200">Ontology mapping</div>
                <select
                  className="w-full rounded-md border border-slate-300 px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
                  value={selectedMappingId}
                  onChange={(e) => setSelectedMappingId(e.target.value)}
                >
                  {ontologyMappings.map((mapping) => (
                    <option key={mapping.mapping_id} value={mapping.mapping_id}>{mapping.name}</option>
                  ))}
                </select>
                <button className="btn btn-ghost text-xs" onClick={() => void handleInstallOntologyMapping()} disabled={!selectedMappingId || mappingInstalling}>
                  {mappingInstalling ? "Installing..." : "Install schema"}
                </button>
              </div>
              <div className="space-y-2 text-slate-600 dark:text-slate-300">
                <div>{selectedOntologyMapping?.summary ?? "No mapping template loaded."}</div>
                <div className="flex flex-wrap gap-2">
                  {(selectedOntologyMapping?.entity_types ?? []).map((item) => (
                    <span key={item.name} className="badge badge-neutral">{item.name}</span>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {(selectedOntologyMapping?.relation_types ?? []).map((item) => (
                    <span key={item.name} className="badge badge-low">{item.from_type} - {item.name} - {item.to_type}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        <div className="flex flex-col lg:flex-row" style={{ minHeight: 520 }}>
          <div className="flex shrink-0 gap-1 overflow-x-auto border-b border-slate-200 p-2 lg:w-44 lg:flex-col lg:overflow-x-visible lg:border-b-0 lg:border-r dark:border-slate-800">
            <div className="mb-1 text-[10px] uppercase text-slate-400">노드 추가</div>
            {PALETTE.map((p) => (
              <button key={p.kind} className="btn btn-ghost shrink-0 justify-start text-xs" style={{ borderColor: p.color }} onClick={() => addNode(p.kind)}>
                + {p.label}
              </button>
            ))}
          </div>
          <div className="relative min-h-[520px] flex-1">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, node) => setSelectedNodeId(node.id)}
              onPaneClick={() => setSelectedNodeId(null)}
              fitView
            >
              <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
              <Controls />
              <MiniMap pannable zoomable />
            </ReactFlow>
          </div>
          <div className="shrink-0 border-t border-slate-200 p-3 lg:w-80 lg:border-l lg:border-t-0 dark:border-slate-800">
            {selectedNode ? (
              <div className="space-y-3 text-xs">
                <div>
                  <div className="font-semibold text-sm text-slate-950 dark:text-slate-100">노드 속성</div>
                  <div className="text-slate-400">{selectedNode.id}</div>
                </div>
                <label className="block">
                  <span className="text-slate-500">Label</span>
                  <input
                    className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 dark:border-slate-700 dark:bg-slate-950"
                    value={(selectedNode.data as { label?: string })?.label ?? ""}
                    onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
                  />
                </label>
                <label className="block">
                  <span className="text-slate-500">Prompt / Rule</span>
                  <textarea
                    rows={4}
                    className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 dark:border-slate-700 dark:bg-slate-950"
                    value={(selectedNode.data as { prompt?: string })?.prompt ?? ""}
                    onChange={(e) => updateNodeData(selectedNode.id, { prompt: e.target.value })}
                    placeholder="노드별 실행 조건, 프롬프트, 정책을 적습니다."
                  />
                </label>
                {(selectedNode.data as { status?: string })?.status && (
                  <div className="text-slate-500">
                    상태: <span className="badge badge-neutral">{(selectedNode.data as { status?: string }).status}</span>
                  </div>
                )}
                {!!(selectedNode.data as { result?: unknown })?.result && (
                  <div className="break-words text-slate-600 dark:text-slate-300">
                    결과: <code>{String((selectedNode.data as { result?: unknown }).result)}</code>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs leading-5 text-slate-400">노드를 선택하면 속성 편집 패널이 표시됩니다. 템플릿을 복제한 뒤 여기에서 라벨, 규칙, 프롬프트를 수정할 수 있습니다.</div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3 className="text-sm font-semibold text-slate-950 dark:text-slate-100">Service Request Simulation</h3>
            <p className="text-xs text-slate-500">Local mock preview. Real Scenario 1 execution runs through the graph executor.</p>
          </div>
          <button className="btn btn-primary bg-teal-700 text-xs hover:bg-teal-800" onClick={runLocalSimulation}>Simulate</button>
        </div>
        <div className="panel-body grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.8fr)]">
          <textarea
            className="min-h-28 rounded-md border border-slate-300 p-3 text-sm dark:border-slate-700 dark:bg-slate-950"
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
          />
          <div className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800">
            {!simulation ? (
              <div className="text-slate-500">Enter a request sentence and run simulation.</div>
            ) : (
              <div className="space-y-2">
                <div><span className="font-semibold">Category:</span> {simulation.category}</div>
                <div><span className="font-semibold">Route:</span> <span className="badge badge-neutral">{simulation.route}</span></div>
                <div><span className="font-semibold">Evidence:</span> {simulation.evidence.join(" / ")}</div>
                <div className="rounded-md bg-slate-50 p-3 leading-6 dark:bg-slate-950">{simulation.answer}</div>
              </div>
            )}
          </div>
        </div>
      </section>

      <WorkflowRunHistory runs={runs} loading={runsLoading} />

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">Node Execution Results</h3>
          <span className="text-xs text-slate-500">{results.length} items</span>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead><tr><th>#</th><th>Node</th><th>Type</th><th>Status</th><th>Duration</th><th>Output</th><th>Started</th></tr></thead>
            <tbody>
              {results.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-6 text-slate-400">아직 실행 결과가 없습니다.</td></tr>
              ) : (
                results.map((result, index) => (
                  <tr key={`${result.node_id}-${index}`}>
                    <td>{index + 1}</td>
                    <td className="font-semibold">{result.label}</td>
                    <td>{result.type}</td>
                    <td><span className={`badge ${result.status === "success" ? "badge-low" : result.status === "error" ? "badge-high" : "badge-medium"}`}>{result.status}</span></td>
                    <td>{result.duration_ms}ms</td>
                    <td className="max-w-[300px] break-words text-slate-600 dark:text-slate-300">{result.output}</td>
                    <td className="text-xs text-slate-400">{new Date(result.started_at).toLocaleTimeString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
