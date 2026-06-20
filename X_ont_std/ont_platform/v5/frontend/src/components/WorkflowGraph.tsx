"use client";

import { useCallback, useEffect, useMemo, useState, type ComponentType, type CSSProperties } from "react";
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
  Handle,
  MarkerType,
  MiniMap,
  Node,
  NodeChange,
  Position,
  type NodeProps,
} from "reactflow";
import "reactflow/dist/style.css";
import {
  Bell,
  CheckCircle2,
  Copy,
  Database,
  FileInput,
  GitBranch,
  ListChecks,
  MessageSquareText,
  Network,
  Play,
  RotateCcw,
  Save,
  Search,
  ShieldCheck,
  Tag,
  Trash2,
  Wrench,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { GraphNodeData, GraphNodeKind, Skill, WorkflowGraph, WorkflowOntologyMapping, WorkflowRun } from "@/types/api";
import { InputMappingEditor } from "./InputMappingEditor";

type SideTab = "run" | "properties" | "input_output" | "skills" | "ontology" | "history";
type WorkflowNodeStatus = NonNullable<GraphNodeData["status"]>;
type WorkflowNodeData = GraphNodeData & {
  kind?: GraphNodeKind;
  label?: string;
  status?: WorkflowNodeStatus;
  result?: unknown;
};
type NodePaletteItem = {
  kind: GraphNodeKind;
  label: string;
  shortLabel: string;
  description: string;
  color: string;
  icon: ComponentType<{ className?: string }>;
};

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

const FACTORY_NODE_LAYOUT: Record<string, { x: number; y: number }> = {
  "request-input": { x: 80, y: 260 },
  "category-classify": { x: 370, y: 260 },
  "asset-map": { x: 660, y: 260 },
  "recurrence-check": { x: 950, y: 260 },
  "fault-register": { x: 1240, y: 260 },
  "maintenance-task": { x: 1530, y: 130 },
  "quality-link": { x: 1530, y: 390 },
  "draft-response": { x: 1820, y: 260 },
  "notify-teams": { x: 2110, y: 260 },
  "ontology-write": { x: 2400, y: 260 },
};

const CUSTOMER_NODE_LAYOUT: Record<string, { x: number; y: number }> = {
  "request-input": { x: 80, y: 260 },
  "intent-classify": { x: 360, y: 260 },
  "category-classify": { x: 360, y: 260 },
  "rag-search": { x: 640, y: 260 },
  "knowledge-lookup": { x: 640, y: 260 },
  "evidence-gate": { x: 920, y: 260 },
  "draft-response": { x: 1200, y: 130 },
  "human-handoff": { x: 1200, y: 390 },
  "post-comment": { x: 1480, y: 130 },
  "notify-user": { x: 1480, y: 130 },
  "audit-write": { x: 1760, y: 130 },
  "ontology-write": { x: 1760, y: 260 },
  "end": { x: 2040, y: 130 },
};

const PALETTE: NodePaletteItem[] = [
  { kind: "request_input", label: "Request Input", shortLabel: "입력", description: "외부 요청을 받아 실행 컨텍스트를 만듭니다.", color: "#0f766e", icon: FileInput },
  { kind: "intent_classify", label: "Intent Classify", shortLabel: "분류", description: "요청 의도와 업무 카테고리를 판정합니다.", color: "#2563eb", icon: Tag },
  { kind: "equipment_map", label: "Asset Map", shortLabel: "자산 매핑", description: "공장, 라인, 설비를 온톨로지 객체와 연결합니다.", color: "#0d9488", icon: Network },
  { kind: "recurrence_check", label: "Repeat Check", shortLabel: "반복 확인", description: "동일 설비나 증상의 반복 발생 여부를 확인합니다.", color: "#a16207", icon: ListChecks },
  { kind: "knowledge_lookup", label: "Knowledge Lookup", shortLabel: "지식 조회", description: "관련 문서와 온톨로지 근거를 찾습니다.", color: "#7c3aed", icon: Search },
  { kind: "policy_search", label: "Policy Search", shortLabel: "정책 조회", description: "처리 기준과 승인 규칙을 찾습니다.", color: "#4f46e5", icon: ShieldCheck },
  { kind: "evidence_gate", label: "Evidence Gate", shortLabel: "근거 검증", description: "자동 처리에 충분한 근거가 있는지 확인합니다.", color: "#ca8a04", icon: CheckCircle2 },
  { kind: "approval_check", label: "Approval Check", shortLabel: "승인 확인", description: "승인이 필요한 단계인지 판정합니다.", color: "#ea580c", icon: ShieldCheck },
  { kind: "action_plan", label: "Action Plan", shortLabel: "조치 계획", description: "처리 계획과 다음 액션을 구성합니다.", color: "#0891b2", icon: GitBranch },
  { kind: "draft_response", label: "Draft Response", shortLabel: "답변 생성", description: "근거 기반 답변 초안을 생성합니다.", color: "#0e7490", icon: MessageSquareText },
  { kind: "customer_mcp_comment_create", label: "MCP Comment", shortLabel: "댓글 등록", description: "MCP 중계 서버를 통해 외부 댓글을 등록합니다.", color: "#059669", icon: MessageSquareText },
  { kind: "maintenance_task", label: "Maintenance", shortLabel: "정비 지시", description: "정비팀 확인 건이나 작업 지시를 생성합니다.", color: "#b45309", icon: Wrench },
  { kind: "quality_link", label: "Quality Link", shortLabel: "품질 연결", description: "품질 이슈와 설비 증상을 연결합니다.", color: "#be185d", icon: GitBranch },
  { kind: "ontology_write", label: "Ontology Write", shortLabel: "온톨로지 저장", description: "실행 결과를 온톨로지 객체와 관계로 남깁니다.", color: "#475569", icon: Database },
  { kind: "human_handoff", label: "Human Handoff", shortLabel: "담당자 이관", description: "자동 처리 대신 담당자 확인으로 넘깁니다.", color: "#be123c", icon: Bell },
  { kind: "notify_user", label: "Notify User", shortLabel: "알림", description: "처리 결과를 사용자나 담당팀에 알립니다.", color: "#16a34a", icon: Bell },
  { kind: "start", label: "Start", shortLabel: "시작", description: "워크플로우 시작점입니다.", color: "#10b981", icon: Play },
  { kind: "condition", label: "Condition", shortLabel: "조건", description: "조건에 따라 실행 경로를 나눕니다.", color: "#f59e0b", icon: GitBranch },
  { kind: "llm", label: "LLM", shortLabel: "AI 생성", description: "LLM으로 요약, 분류, 답변을 생성합니다.", color: "#6366f1", icon: MessageSquareText },
  { kind: "http", label: "HTTP", shortLabel: "API 호출", description: "외부 API나 MCP 도구를 호출합니다.", color: "#0ea5e9", icon: Network },
  { kind: "end", label: "End", shortLabel: "종료", description: "워크플로우 종료점입니다.", color: "#ef4444", icon: CheckCircle2 },
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

interface WorkflowRunSummary {
  status?: string;
  checked?: number;
  started?: number;
  skipped?: number;
  errors?: number;
}

function newId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 8)}`;
}

function getNodeMeta(kind?: GraphNodeKind) {
  return PALETTE.find((p) => p.kind === kind) ?? PALETTE[0];
}

function statusLabel(status?: WorkflowNodeStatus) {
  if (status === "running") return "실행 중";
  if (status === "success") return "완료";
  if (status === "error") return "실패";
  if (status === "skipped") return "미실행";
  return "대기";
}

function statusIcon(status?: WorkflowNodeStatus) {
  if (status === "success") return <CheckCircle2 className="h-3.5 w-3.5" />;
  if (status === "error") return <XCircle className="h-3.5 w-3.5" />;
  return null;
}

function normalizeWorkflowStatus(status: unknown): WorkflowNodeStatus {
  if (status === "succeeded" || status === "success" || status === "completed") return "success";
  if (status === "failed" || status === "error") return "error";
  if (status === "skipped") return "skipped";
  if (status === "running") return "running";
  return "idle";
}

function parseRunSummary(value: unknown): WorkflowRunSummary | null {
  if (!value || typeof value !== "object") return null;
  const item = value as Record<string, unknown>;
  return {
    status: typeof item.status === "string" ? item.status : undefined,
    checked: typeof item.checked === "number" ? item.checked : undefined,
    started: typeof item.started === "number" ? item.started : undefined,
    skipped: typeof item.skipped === "number" ? item.skipped : undefined,
    errors: typeof item.errors === "number" ? item.errors : undefined,
  };
}

function formatRunSummary(summary: WorkflowRunSummary | null) {
  if (!summary) return "";
  const parts = [
    typeof summary.checked === "number" ? `확인 ${summary.checked}` : null,
    typeof summary.started === "number" ? `신규처리 ${summary.started}` : null,
    typeof summary.skipped === "number" ? `스킵 ${summary.skipped}` : null,
    typeof summary.errors === "number" ? `오류 ${summary.errors}` : null,
  ].filter(Boolean);
  return parts.join(" / ");
}

function expectedRunStepCount(executor?: string, nodeCount = 0) {
  if (executor === "scenario1.customer_question_auto_reply") return 4;
  if (executor === "factory.repeated_fault_response") return 10;
  return nodeCount;
}

function WorkflowNodeCard({ data, selected }: NodeProps<WorkflowNodeData>) {
  const kind = data.kind;
  const meta = getNodeMeta(kind);
  const Icon = meta.icon;
  const status = data.status ?? "idle";
  const result = data.result ? String(data.result) : "";

  return (
    <div
      className={`workflow-node-card ${status} ${selected ? "selected" : ""}`}
      style={{ "--node-color": meta.color } as CSSProperties}
    >
      <Handle type="target" position={Position.Left} className="workflow-handle" />
      <div className="flex items-start gap-2">
        <div className="workflow-node-icon">
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div className="truncate text-[11px] font-semibold text-slate-500 dark:text-slate-400">{meta.shortLabel}</div>
            <span className="workflow-node-status">
              {status === "running" ? <span className="workflow-node-status-dot" /> : statusIcon(status)}
              {statusLabel(status)}
            </span>
          </div>
          <div className="mt-1 line-clamp-2 text-sm font-bold leading-5 text-slate-950 dark:text-slate-100">
            {data.label ?? meta.label}
          </div>
          <div className="mt-1 line-clamp-2 text-[11px] leading-4 text-slate-500 dark:text-slate-400">
            {meta.description}
          </div>
          {result && (
            <div className="mt-2 truncate rounded bg-slate-50 px-2 py-1 text-[10px] text-slate-500 dark:bg-slate-950 dark:text-slate-400">
              {result}
            </div>
          )}
          {status === "running" && (
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-blue-100">
              <div className="workflow-node-progress h-full w-2/3 rounded-full bg-blue-600" />
            </div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="workflow-handle" />
    </div>
  );
}

function toFlowNode(node: WorkflowGraph["nodes"][number]): Node {
  return {
    id: node.id,
    type: "workflowNode",
    position: node.position,
    data: { ...node.data, kind: node.type, label: node.data?.label ?? node.type, status: "idle" },
  };
}

function normalizeNodeForExecutor(
  node: WorkflowGraph["nodes"][number],
  executor?: string
): WorkflowGraph["nodes"][number] {
  const layout =
    executor === "factory.repeated_fault_response"
      ? FACTORY_NODE_LAYOUT
      : executor === "scenario1.customer_question_auto_reply"
        ? CUSTOMER_NODE_LAYOUT
        : {};
  const label = executor === "factory.repeated_fault_response" ? FACTORY_NODE_LABELS[node.id] : undefined;
  return {
    ...node,
    position: layout[node.id] ?? node.position,
    data: label ? { ...node.data, label } : node.data,
  };
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
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [sideTab, setSideTab] = useState<SideTab>("run");
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<StepResult[]>([]);
  const [lastRunSummary, setLastRunSummary] = useState<WorkflowRunSummary | null>(null);
  const [toast, setToast] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [graphMeta, setGraphMeta] = useState<Partial<WorkflowGraph>>({});
  const [scenarioMode, setScenarioMode] = useState<"dry_run" | "post">("post");
  const [batchStatus, setBatchStatus] = useState("open");
  const [batchLimit, setBatchLimit] = useState(10);
  const [forceReprocess, setForceReprocess] = useState(true);
  const [ontologyMappings, setOntologyMappings] = useState<WorkflowOntologyMapping[]>([]);
  const [selectedMappingId, setSelectedMappingId] = useState("scenario1.customer_question_auto_reply.v1");
  const [mappingInstalling, setMappingInstalling] = useState(false);
  const [requestText, setRequestText] = useState("결재 후 비밀번호 초기화를 요청합니다.");
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);
  const [builtinSkills, setBuiltinSkills] = useState<Skill[]>([]);
  const [customSkills, setCustomSkills] = useState<Skill[]>([]);
  const [skillsLoading, setSkillsLoading] = useState(false);
  const [selectedNodeSkill, setSelectedNodeSkill] = useState<Skill | null>(null);
  const [selectedNodeSkillLoading, setSelectedNodeSkillLoading] = useState(false);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId]
  );
  const selectedOntologyMapping = useMemo(
    () => ontologyMappings.find((item) => item.mapping_id === selectedMappingId) ?? ontologyMappings[0] ?? null,
    [ontologyMappings, selectedMappingId]
  );
  const nodeTypes = useMemo(() => ({ workflowNode: WorkflowNodeCard }), []);
  const activeResult = useMemo(
    () => [...results].reverse().find((item) => item.node_id === activeNodeId) ?? null,
    [activeNodeId, results]
  );
  const selectedResult = useMemo(
    () => [...results].reverse().find((item) => item.node_id === selectedNodeId) ?? null,
    [results, selectedNodeId]
  );
  const completedNodeIds = useMemo(() => new Set(results.map((item) => item.node_id)), [results]);
  const selectedEdge = useMemo(() => edges.find((edge) => edge.id === selectedEdgeId) ?? null, [edges, selectedEdgeId]);
  const executionStepCount = expectedRunStepCount(graphMeta.runtime?.executor, nodes.length);
  const progressTotal = Math.max(executionStepCount, results.length, 1);
  const progressPercent = results.length === 0 ? 0 : (!running ? 100 : Math.min(100, Math.round((results.length / progressTotal) * 100)));
  const renderedEdges = useMemo(
    () => edges.map((edge) => {
      const activeEdge = edge.source === activeNodeId || edge.target === activeNodeId;
      const completedEdge = completedNodeIds.has(edge.source) && completedNodeIds.has(edge.target);
      const selectedEdge = edge.id === selectedEdgeId;
      return {
        ...edge,
        type: edge.type ?? "smoothstep",
        selected: selectedEdge,
        animated: running && (activeEdge || completedEdge),
        interactionWidth: 26,
        zIndex: selectedEdge || activeEdge ? 30 : completedEdge ? 20 : 10,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: selectedEdge ? "#38bdf8" : activeEdge ? "#2563eb" : completedEdge ? "#16a34a" : "#64748b",
          width: 18,
          height: 18,
        },
        style: {
          ...(edge.style ?? {}),
          stroke: selectedEdge ? "#38bdf8" : activeEdge ? "#2563eb" : completedEdge ? "#16a34a" : "#64748b",
          strokeWidth: selectedEdge ? 4 : activeEdge ? 3.5 : completedEdge ? 2.5 : 1.8,
          filter: selectedEdge ? "drop-shadow(0 0 6px rgba(56,189,248,0.65))" : undefined,
        },
        labelStyle: {
          ...(edge.labelStyle ?? {}),
          fill: selectedEdge ? "#7dd3fc" : activeEdge ? "#93c5fd" : "#94a3b8",
          fontWeight: selectedEdge || activeEdge ? 800 : 600,
        },
        labelBgStyle: { fill: "#ffffff", fillOpacity: 0.94 },
        labelBgPadding: [8, 4] as [number, number],
        labelBgBorderRadius: 8,
      };
    }),
    [activeNodeId, completedNodeIds, edges, running, selectedEdgeId]
  );
  const selectedMappingNode = useMemo(() => {
    if (!selectedNode) return null;
    return selectedOntologyMapping?.workflow_node_mappings?.find((item) => item.node_id === selectedNode.id) ?? null;
  }, [selectedNode, selectedOntologyMapping]);

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
      setBatchLimit(
        g.runtime?.executor === "factory.repeated_fault_response" ||
        g.runtime?.executor === "scenario1.customer_question_auto_reply"
          ? 1
          : (g.runtime?.batch_limit ?? 10)
      );
      setNodes(g.nodes.map((node) => toFlowNode(normalizeNodeForExecutor(node, g.runtime?.executor))));
      setEdges(g.edges.map((e) => ({ id: e.id, source: e.source, target: e.target, label: e.label, type: "smoothstep", animated: true })));
      setResults([]);
      setLastRunSummary(null);
      setSelectedNodeId(null);
      setSelectedEdgeId(null);
      setActiveNodeId(null);
      setSideTab("run");
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

  useEffect(() => {
    setSkillsLoading(true);
    api.skills.list()
      .then((res) => {
        setBuiltinSkills(Array.isArray(res.builtinSkills) ? res.builtinSkills : []);
        setCustomSkills(Array.isArray(res.customSkills) ? res.customSkills : []);
      })
      .catch(() => {
        setBuiltinSkills([]);
        setCustomSkills([]);
      })
      .finally(() => setSkillsLoading(false));
  }, []);

  // Load selected node's skill details
  useEffect(() => {
    if (!selectedNode || selectedNode.type !== "skill") {
      setSelectedNodeSkill(null);
      return;
    }

    const skillId = (selectedNode.data as GraphNodeData).skillId;
    if (!skillId) {
      setSelectedNodeSkill(null);
      return;
    }

    setSelectedNodeSkillLoading(true);
    api.skills.get(skillId)
      .then((skill) => setSelectedNodeSkill(skill))
      .catch(() => setSelectedNodeSkill(null))
      .finally(() => setSelectedNodeSkillLoading(false));
  }, [selectedNode]);

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
      setEdges((eds) => addEdge({ ...conn, id: newId("e"), type: "smoothstep", animated: true }, eds)),
    []
  );

  function addNode(kind: GraphNodeKind) {
    const id = newId("n");
    const item = PALETTE.find((p) => p.kind === kind) ?? PALETTE[0];
    const newNode: Node = {
      id,
      type: "workflowNode",
      position: { x: 80 + Math.random() * 300, y: 80 + Math.random() * 200 },
      data: { label: `${item.label} ${id.slice(2, 5)}`, kind, status: "idle" } as GraphNodeData & { kind: GraphNodeKind },
    };
    setNodes((nds) => nds.concat(newNode));
  }

  function installSkillNode(skill: Skill) {
    const id = newId("skill");
    const newNode: Node = {
      id,
      type: "workflowNode",
      position: { x: 120 + Math.random() * 320, y: 120 + Math.random() * 220 },
      data: {
        label: skill.name,
        kind: "skill",
        status: "idle",
        skillId: skill.id,
        skillVersion: skill.version,
        skillConfig: {
          inputMapping: {},
          outputMapping: {},
          parameters: {},
        },
      } as GraphNodeData & { kind: GraphNodeKind },
    };
    setNodes((nds) => nds.concat(newNode));
    setSelectedNodeId(id);
    setSelectedEdgeId(null);
    setSideTab("properties");
    setToast({ kind: "ok", text: `스킬 노드 추가: ${skill.name}` });
  }

  function updateNodeData(id: string, patch: Partial<GraphNodeData>) {
    setNodes((nds) => nds.map((n) => n.id === id ? { ...n, data: { ...(n.data as object), ...patch } } : n));
  }

  function deleteSelectedElement() {
    if (selectedEdgeId) {
      const deletedEdgeId = selectedEdgeId;
      setEdges((eds) => eds.filter((edge) => edge.id !== deletedEdgeId));
      setSelectedEdgeId(null);
      setToast({ kind: "ok", text: "연결선을 삭제했습니다." });
      return;
    }

    if (selectedNodeId) {
      const deletedNodeId = selectedNodeId;
      setNodes((nds) => nds.filter((node) => node.id !== deletedNodeId));
      setEdges((eds) => eds.filter((edge) => edge.source !== deletedNodeId && edge.target !== deletedNodeId));
      setResults((items) => items.filter((item) => item.node_id !== deletedNodeId));
      if (activeNodeId === deletedNodeId) setActiveNodeId(null);
      setSelectedNodeId(null);
      setToast({ kind: "ok", text: "블록과 연결선을 삭제했습니다." });
    }
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
            skillId: (n.data as { skillId?: string })?.skillId,
            skillVersion: (n.data as { skillVersion?: string })?.skillVersion,
            skillConfig: (n.data as { skillConfig?: GraphNodeData["skillConfig"] })?.skillConfig,
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
      setToast({ kind: "ok", text: `저장 완료: ${saved.id}` });
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
    setLastRunSummary(null);
    setRuns([]);
    setGraphMeta({});
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    setActiveNodeId(null);
    setSideTab("run");
    setToast(null);
  }

  async function handleDelete() {
    if (!graphId) return;
    if (!window.confirm(`${graphId} 워크플로우를 삭제할까요?`)) return;
    try {
      await api.workflowGraphs.remove(graphId);
      setToast({ kind: "ok", text: "삭제 완료" });
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
    setLastRunSummary(null);
    setActiveNodeId(null);
    setSideTab("run");
    if (!graphId) {
      setToast({ kind: "err", text: "먼저 워크플로우를 저장한 뒤 실행하세요." });
      return;
    }
    if (nodes.length === 0) {
      setToast({ kind: "err", text: "노드가 없습니다." });
      return;
    }
    setRunning(true);
    const firstNodeId = nodes[0]?.id ?? null;
    setActiveNodeId(firstNodeId);
    setSelectedNodeId(firstNodeId);
    setNodes((nds) => nds.map((n, index) => ({
      ...n,
      data: { ...(n.data as object), status: index === 0 ? "running" : "idle" },
    })));

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
      const nodeId = String(data.node_id);
      setSelectedNodeId(nodeId);
      setActiveNodeId(nodeId);
      setSideTab("run");
      setNodes((nds) => nds.map((n) => n.id === data.node_id ? { ...n, data: { ...(n.data as object), status: "running" } } : n));
    } else if (eventType === "node_finished") {
      const outputStr = typeof data.output === "string" ? data.output : JSON.stringify(data.output);
      const status = normalizeWorkflowStatus(data.status);
      setNodes((nds) => nds.map((n) => n.id === data.node_id ? { ...n, data: { ...(n.data as object), status, result: outputStr } } : n));
      setResults((rs) => rs.concat({
        node_id: String(data.node_id),
        label: String(data.label ?? data.node_id),
        type: String(data.type ?? "?"),
        status: status === "idle" ? "success" : status,
        output: outputStr ?? String(data.error ?? ""),
        started_at: String(data.started_at),
        duration_ms: Number(data.duration_ms ?? 0),
      }));
    } else if (eventType === "run_finished") {
      setRunning(false);
      setActiveNodeId(null);
      const summary = parseRunSummary(data.summary);
      setLastRunSummary(summary);
      setNodes((nds) => nds.map((node) => {
        const status = (node.data as WorkflowNodeData).status;
        if (status === "running") {
          return { ...node, data: { ...(node.data as object), status: "success" } };
        }
        if (data.status === "completed" && status === "idle") {
          return { ...node, data: { ...(node.data as object), status: "skipped" } };
        }
        return node;
      }));
      const summaryText = formatRunSummary(summary);
      const noNewItems = summary && summary.started === 0 && (summary.skipped ?? 0) > 0;
      setToast({
        kind: data.status === "completed" ? "ok" : "err",
        text: noNewItems
          ? `실행 완료: 신규 댓글 없음 (${summaryText}). 이미 처리된 요청은 중복 방지로 스킵됩니다.`
          : `실행 ${data.status} (${data.completed_count} 단계)${summaryText ? ` - ${summaryText}` : ""}`,
      });
    } else if (eventType === "run_failed") {
      setRunning(false);
      setToast({ kind: "err", text: `실행 실패: ${data.error}` });
    }
  }

  function runLocalSimulation() {
    setSimulation(simulateRequest(requestText));
  }

  return (
    <div className="space-y-4">
      <section className="panel">
        <div className="panel-header gap-3 rounded-t-xl bg-white px-4 py-3">
          <div className="flex min-w-0 flex-1 flex-wrap items-center gap-3">
            <input
              value={graphName}
              onChange={(e) => setGraphName(e.target.value)}
              className="premium-input w-72 max-w-full placeholder-slate-400 font-bold"
              placeholder="워크플로우 이름"
            />
            <span className="font-mono text-[10px] tracking-wide text-slate-500 bg-slate-50 border border-slate-200 px-2.5 py-0.5 rounded-md">{graphId ?? "NEW"}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="premium-input w-56 text-xs font-bold"
              value={graphId ?? ""}
              onChange={(e) => { const value = e.target.value; if (value) void handleLoad(value); else handleNew(); }}
            >
              <option value="">불러오기...</option>
              {graphsList.map((g) => (
                <option key={g.id} value={g.id}>{g.name} ({g.id.slice(0, 10)})</option>
              ))}
            </select>
            <button className="btn btn-ghost text-xs py-1.5 px-3" onClick={handleNew}><RotateCcw className="mr-1 h-3.5 w-3.5" />New</button>
            <button className="btn btn-primary text-xs py-1.5 px-3" onClick={() => void handleSave()}><Save className="mr-1 h-3.5 w-3.5" />Save</button>
            <button className="btn btn-ghost text-xs py-1.5 px-3" onClick={() => void handleClone()} disabled={!graphId}><Copy className="mr-1 h-3.5 w-3.5" />Clone</button>
            <button className="btn btn-ok text-xs py-1.5 px-3" onClick={() => void handleRun()} disabled={running}><Play className="mr-1 h-3.5 w-3.5" />{running ? "실행 중..." : "Run"}</button>
            <button className="btn btn-ghost text-xs py-1.5 px-3" onClick={deleteSelectedElement} disabled={!selectedNodeId && !selectedEdgeId}><Trash2 className="mr-1 h-3.5 w-3.5" />선택 삭제</button>
            <button className="btn btn-danger text-xs py-1.5 px-3" onClick={() => void handleDelete()} disabled={!graphId}><Trash2 className="mr-1 h-3.5 w-3.5" />Delete</button>
          </div>
        </div>
        {toast && (
          <div className="border-b border-slate-200 bg-slate-50 px-5 py-2.5 text-xs">
            <span className={`font-bold ${toast.kind === "ok" ? "text-emerald-700" : "text-rose-700"}`}>
              {toast.kind === "ok" ? "✓ " : "✗ "} {toast.text}
            </span>
          </div>
        )}
        <div className="flex flex-col lg:flex-row" style={{ minHeight: 680 }}>
          <div className="flex shrink-0 gap-2 overflow-x-auto border-b border-slate-200 bg-slate-50 p-3 lg:w-40 lg:flex-col lg:overflow-x-visible lg:border-b-0 lg:border-r">
            <div className="mb-2 px-1 text-[10px] font-extrabold uppercase tracking-wider text-slate-500">노드 추가</div>
            <div className="flex flex-wrap gap-1.5 lg:flex-col lg:gap-2">
              {PALETTE.map((p) => {
                const Icon = p.icon;
                return (
                  <button
                    key={p.kind}
                    className="group flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs font-bold text-slate-700 shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 hover:text-slate-950"
                    style={{ borderLeft: `3px solid ${p.color}` }}
                    onClick={() => addNode(p.kind)}
                    title={p.description}
                  >
                    <span className="shrink-0 flex items-center justify-center" style={{ color: p.color }}>
                      <Icon className="h-3.5 w-3.5 transition-transform group-hover:scale-110" />
                    </span>
                    <span className="truncate">{p.shortLabel}</span>
                  </button>
                );
              })}
            </div>
          </div>
          <div className="relative min-h-[680px] flex-1 bg-slate-50">
            <ReactFlow
              nodes={nodes}
              edges={renderedEdges}
              nodeTypes={nodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, node) => {
                setSelectedNodeId(node.id);
                setSelectedEdgeId(null);
                const nodeResult = results.find(r => r.node_id === node.id);
                setSideTab(nodeResult ? "input_output" : "properties");
              }}
              onEdgeClick={(_, edge) => { setSelectedEdgeId(edge.id); setSelectedNodeId(null); setSideTab("properties"); }}
              onPaneClick={() => { setSelectedNodeId(null); setSelectedEdgeId(null); }}
              fitView
              fitViewOptions={{ padding: 0.18 }}
              elementsSelectable
              nodesDraggable
              nodesConnectable
              edgesFocusable
              deleteKeyCode={["Backspace", "Delete"]}
              onNodesDelete={(deleted) => {
                const deletedIds = new Set(deleted.map((node) => node.id));
                if (selectedNodeId && deletedIds.has(selectedNodeId)) setSelectedNodeId(null);
                if (activeNodeId && deletedIds.has(activeNodeId)) setActiveNodeId(null);
                setResults((items) => items.filter((item) => !deletedIds.has(item.node_id)));
              }}
              onEdgesDelete={(deleted) => {
                const deletedIds = new Set(deleted.map((edge) => edge.id));
                if (selectedEdgeId && deletedIds.has(selectedEdgeId)) setSelectedEdgeId(null);
              }}
              defaultEdgeOptions={{
                type: "smoothstep",
                interactionWidth: 26,
                markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
              }}
            >
              <Background variant={BackgroundVariant.Lines} gap={24} size={1} color="#d9e2ee" />
              <Controls />
              <MiniMap pannable zoomable />
            </ReactFlow>
            {running && (
              <div className="pointer-events-none absolute left-4 top-4 rounded-lg border border-blue-200 bg-blue-50 px-3.5 py-2 text-xs font-bold text-blue-700 shadow-sm animate-pulse">
                실행 중: 블록과 연결선이 순서대로 강조됩니다.
              </div>
            )}
          </div>
          <aside className="flex shrink-0 flex-col border-t border-slate-200 bg-white lg:w-[380px] lg:border-l lg:border-t-0">
            <div className="border-b border-slate-200 p-3">
              <div className="flex rounded-lg bg-slate-100 p-1 text-xs flex-wrap gap-1">
                {[
                  ["run", "실행 현황"],
                  ["properties", "선택 항목"],
                  ["input_output", "입출력"],
                  ["skills", "스킬"],
                  ["ontology", "온톨로지"],
                  ["history", "이력"],
                ].map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    className={`rounded-lg px-2.5 py-2 font-bold tracking-wide uppercase transition-all duration-150 ${
                      sideTab === key
                        ? "bg-white text-teal-800 shadow-sm"
                        : "text-slate-500 hover:text-slate-900"
                    }`}
                    onClick={() => setSideTab(key as SideTab)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="max-h-[680px] overflow-auto p-4 text-xs flex-1 space-y-4">
              {sideTab === "run" && (
                <div className="space-y-4">
                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-bold text-slate-900">워크플로우 실행 현황</div>
                        <div className="text-slate-500 font-mono text-[10px] mt-0.5">{graphMeta.runtime?.executor ?? "simulation"}</div>
                      </div>
                      <span className={`badge ${running ? "badge-medium" : "badge-neutral"}`}>{running ? "Running" : "Ready"}</span>
                    </div>
                    {graphMeta.runtime?.executor && (
                      <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
                        <label className="flex flex-col gap-1">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">실행 모드</span>
                          <select className="premium-input text-xs font-semibold" value={scenarioMode} onChange={(e) => setScenarioMode(e.target.value as "dry_run" | "post")}>
                            <option value="dry_run">dry_run</option>
                            <option value="post">post</option>
                          </select>
                        </label>
                        <label className="flex flex-col gap-1">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">Status</span>
                          <input className="premium-input text-xs font-mono" value={batchStatus} onChange={(e) => setBatchStatus(e.target.value)} />
                        </label>
                        <label className="flex flex-col gap-1">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">처리 건수</span>
                          <input type="number" min={1} max={100} className="premium-input text-xs font-mono" value={batchLimit} onChange={(e) => setBatchLimit(Number(e.target.value || 10))} />
                        </label>
                        <label className="flex items-end gap-2 pb-1 text-xs font-bold text-slate-600 cursor-pointer select-none">
                          <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-600 cursor-pointer" checked={forceReprocess} onChange={(e) => setForceReprocess(e.target.checked)} />
                          <span>재수행</span>
                        </label>
                      </div>
                    )}
                    <div className="mt-4">
                      <div className="mb-1.5 flex items-center justify-between text-[11px] font-bold text-slate-400">
                        <span>진행률</span>
                        <span className="font-mono">{progressPercent}%</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full border border-slate-200 bg-slate-100">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${running ? "bg-blue-600 shadow-[0_0_8px_#2563eb]" : "bg-emerald-600 shadow-[0_0_8px_#059669]"}`}
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                        <div className="text-base font-bold text-slate-900 font-mono">{results.length}</div>
                        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mt-0.5">완료 단계</div>
                      </div>
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                        <div className="text-base font-bold text-slate-900 font-mono">{executionStepCount}</div>
                        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mt-0.5">실행 단계</div>
                      </div>
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                        <div className="text-xs font-bold text-slate-900 truncate mt-1">{scenarioMode}</div>
                        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mt-1">모드</div>
                      </div>
                    </div>
                    {lastRunSummary && (
                      <div className={`mt-3.5 rounded-lg border p-3.5 ${
                        lastRunSummary.started === 0 && (lastRunSummary.skipped ?? 0) > 0
                          ? "border-amber-200 bg-amber-50 text-amber-800"
                          : "border-emerald-200 bg-emerald-50 text-emerald-800"
                      }`}>
                        <div className="font-bold flex items-center gap-1">
                          <span className={`h-1.5 w-1.5 rounded-full ${lastRunSummary.started === 0 && (lastRunSummary.skipped ?? 0) > 0 ? "bg-amber-400" : "bg-emerald-400"}`} />
                          마지막 배치 결과
                        </div>
                        <div className="mt-1.5 font-mono text-[11px] leading-5">{formatRunSummary(lastRunSummary)}</div>
                        {lastRunSummary.started === 0 && (lastRunSummary.skipped ?? 0) > 0 && (
                          <div className="mt-1.5 leading-5 text-[10px] text-amber-700">이미 처리된 요청으로 중복이 방지되어 처리되지 않고 스킵되었습니다.</div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="mb-2.5 text-xs font-extrabold uppercase tracking-wider text-slate-400">현재 실행 블록</div>
                    {activeNodeId ? (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-xs text-slate-500">{activeNodeId}</span>
                          <span className="badge badge-neutral">{(selectedNode?.data as WorkflowNodeData | undefined)?.status ?? "running"}</span>
                        </div>
                        <div className="font-bold text-sm text-slate-900">
                          {(selectedNode?.data as WorkflowNodeData | undefined)?.label ?? activeNodeId}
                        </div>
                        {activeResult && (
                          <div className="terminal-box max-h-48">
                            {activeResult.output}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="leading-5 text-slate-500 font-medium">Run을 누르면 실행 중인 블록이 자동으로 선택되고 상세 처리 로그가 이 창에 실시간 출력됩니다.</div>
                    )}
                  </div>

                  <div className="space-y-2.5">
                    <div className="text-xs font-extrabold uppercase tracking-wider text-slate-400">최근 완료된 단계</div>
                    {results.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-slate-500 text-center font-medium">아직 완료된 단계가 없습니다.</div>
                    ) : (
                      [...results].reverse().slice(0, 6).map((result) => (
                        <button
                          key={`${result.node_id}-${result.started_at}`}
                          type="button"
                          className="w-full rounded-xl border border-slate-200 bg-white p-3.5 text-left shadow-sm transition hover:border-slate-300 hover:bg-slate-50"
                          onClick={() => { setSelectedNodeId(result.node_id); setSelectedEdgeId(null); setActiveNodeId(result.node_id); setSideTab("input_output"); }}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-bold text-slate-800">{result.label}</span>
                            <span className={`badge ${result.status === "success" ? "badge-low" : result.status === "error" ? "badge-high" : "badge-medium"}`}>{result.status}</span>
                          </div>
                          <div className="mt-1.5 line-clamp-2 text-slate-500 font-mono text-[10px] bg-slate-50 rounded p-1.5 border border-slate-200">{result.output}</div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}

              {sideTab === "properties" && (
                selectedEdge ? (
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm font-bold text-slate-900">선택한 연결선</div>
                      <div className="font-mono text-slate-500 text-[10px] mt-0.5">{selectedEdge.id}</div>
                    </div>
                    <button className="btn btn-danger w-full py-2.5 text-xs" onClick={deleteSelectedElement}>
                      <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                      연결선 삭제
                    </button>
                    <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
                      <div className="text-[10px] font-extrabold uppercase tracking-wider text-sky-700">Connection</div>
                      <div className="mt-2 font-mono text-xs text-slate-700">
                        {selectedEdge.source} <span className="text-sky-400">→</span> {selectedEdge.target}
                      </div>
                    </div>
                    <label className="block">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-450">연결선 라벨</span>
                      <input
                        className="mt-1.5 w-full premium-input font-bold"
                        value={String(selectedEdge.label ?? "")}
                        onChange={(e) => setEdges((eds) => eds.map((edge) => edge.id === selectedEdge.id ? { ...edge, label: e.target.value } : edge))}
                        placeholder="예: 근거 충분, 정비 필요"
                      />
                    </label>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-5 text-slate-600">
                      연결선을 클릭하면 파란색으로 강조됩니다. 연결선 라벨은 저장 시 워크플로우 그래프에 함께 저장됩니다.
                    </div>
                  </div>
                ) : selectedNode ? (
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm font-bold text-slate-900">선택한 블록</div>
                      <div className="font-mono text-slate-500 text-[10px] mt-0.5">{selectedNode.id}</div>
                    </div>
                    <button className="btn btn-danger w-full py-2.5 text-xs" onClick={deleteSelectedElement}>
                      <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                      블록 삭제
                    </button>
                    <label className="block">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-450">노드 이름 (Label)</span>
                      <input
                        className="mt-1.5 w-full premium-input font-bold"
                        value={(selectedNode.data as { label?: string })?.label ?? ""}
                        onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
                      />
                    </label>
                    <label className="block">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-455">Prompt / Rule 조건 설정</span>
                      <textarea
                        rows={6}
                        className="mt-1.5 w-full premium-input font-mono text-xs"
                        value={(selectedNode.data as { prompt?: string })?.prompt ?? ""}
                        onChange={(e) => updateNodeData(selectedNode.id, { prompt: e.target.value })}
                        placeholder="이 노드에서 수행할 프롬프트 템플릿, 분기 규칙 등을 작성합니다."
                      />
                    </label>
                    {selectedNode.type === "skill" && !!(selectedNode.data as WorkflowNodeData).skillId && selectedNodeSkill && (
                      <div className="rounded-xl border border-teal-200 bg-teal-50 p-3 mb-4">
                        <InputMappingEditor
                          skillId={(selectedNode.data as WorkflowNodeData).skillId!}
                          skill={selectedNodeSkill}
                          inputMapping={(selectedNode.data as WorkflowNodeData).skillConfig?.inputMapping ?? {}}
                          onUpdateMapping={(mapping) => {
                            updateNodeData(selectedNode.id, {
                              skillConfig: {
                                ...(selectedNode.data as WorkflowNodeData).skillConfig,
                                inputMapping: mapping,
                              },
                            });
                          }}
                          previousNodeOutputs={
                            results
                              .filter((r) => nodes.some((n) => n.id === r.node_id))
                              .reduce((acc, result) => {
                                const nodeId = result.node_id;
                                if (!acc[nodeId]) acc[nodeId] = {};
                                acc[nodeId] = (typeof result.output === 'object' ? result.output : {}) || {};
                                return acc;
                              }, {} as Record<string, Record<string, any>>)
                          }
                        />
                      </div>
                    )}

                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <div className="mb-2 font-bold text-slate-400 text-xs">최종 실행 상태 및 결과</div>
                      <span className="badge badge-neutral">{(selectedNode.data as WorkflowNodeData).status ?? "idle"}</span>
                      {!!(selectedNode.data as WorkflowNodeData).skillId && (
                        <div className="mt-2 rounded-lg border border-teal-200 bg-white px-2.5 py-2 text-[10px] leading-4 text-teal-800">
                          <div className="font-bold">연결된 스킬</div>
                          <div className="font-mono">{(selectedNode.data as WorkflowNodeData).skillId}</div>
                        </div>
                      )}
                      {!!(selectedNode.data as WorkflowNodeData).result && (
                        <div className="mt-3 terminal-box max-h-48">
                          {String((selectedNode.data as WorkflowNodeData).result)}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="leading-5 text-slate-500 font-medium py-6 text-center">작업 캔버스에서 노드나 연결선을 선택하면 상세 속성을 편집할 수 있습니다.</div>
                )
              )}

              {sideTab === "skills" && (
                <div className="space-y-4">
                  <div>
                    <div className="text-sm font-bold text-slate-900">스킬 갤러리</div>
                    <div className="mt-1 text-xs leading-5 text-slate-600">
                      Built-in 또는 Custom 스킬을 워크플로우 노드로 추가합니다.
                    </div>
                  </div>
                  {skillsLoading ? (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center font-medium text-slate-500">스킬 목록을 불러오는 중...</div>
                  ) : (
                    <>
                      <div className="space-y-2">
                        <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Built-in Skills</div>
                        {builtinSkills.length === 0 ? (
                          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center font-medium text-slate-500">등록된 Built-in 스킬이 없습니다.</div>
                        ) : (
                          builtinSkills.map((skill) => (
                            <button
                              key={skill.id}
                              type="button"
                              className="w-full rounded-xl border border-slate-200 bg-white p-3 text-left shadow-sm transition hover:border-teal-200 hover:bg-teal-50"
                              onClick={() => installSkillNode(skill)}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                  <div className="truncate text-xs font-extrabold text-slate-900">{skill.name}</div>
                                  <div className="mt-1 line-clamp-2 text-[10px] leading-4 text-slate-500">{skill.description}</div>
                                </div>
                                <span className="badge badge-neutral shrink-0">{skill.implementation.type}</span>
                              </div>
                              <div className="mt-2 flex flex-wrap gap-1">
                                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[9px] font-bold text-slate-500">{skill.category}</span>
                                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[9px] font-mono text-slate-500">{skill.id}</span>
                              </div>
                            </button>
                          ))
                        )}
                      </div>

                      <div className="space-y-2">
                        <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Custom Skills</div>
                        {customSkills.length === 0 ? (
                          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center font-medium text-slate-500">프로젝트 커스텀 스킬이 없습니다.</div>
                        ) : (
                          customSkills.map((skill) => (
                            <button
                              key={skill.id}
                              type="button"
                              className="w-full rounded-xl border border-slate-200 bg-white p-3 text-left shadow-sm transition hover:border-teal-200 hover:bg-teal-50"
                              onClick={() => installSkillNode(skill)}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                  <div className="truncate text-xs font-extrabold text-slate-900">{skill.name}</div>
                                  <div className="mt-1 line-clamp-2 text-[10px] leading-4 text-slate-500">{skill.description}</div>
                                </div>
                                <span className="badge badge-medium shrink-0">{skill.implementation.type}</span>
                              </div>
                              <div className="mt-2 rounded-md bg-amber-50 px-2 py-1 text-[10px] font-semibold text-amber-800">
                                Custom Code는 Phase 1에서 저장/편집만 가능하고 실행은 제한됩니다.
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              {sideTab === "ontology" && (
                <div className="space-y-4">
                  <div>
                    <div className="text-sm font-bold text-slate-900">워크플로우 온톨로지 매핑</div>
                    <div className="mt-1.5 leading-5 text-slate-600 text-xs font-semibold">{selectedOntologyMapping?.summary ?? "매핑 템플릿이 없습니다."}</div>
                  </div>
                  {selectedMappingNode && (
                    <div className="rounded-xl border border-teal-200 bg-teal-50 p-4 text-teal-800 shadow-sm">
                      <div className="font-bold flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-teal-400" />
                        선택 노드 매핑 정보
                      </div>
                      <div className="mt-2 text-xs font-bold text-slate-900">{selectedMappingNode.node_label ?? selectedNode?.id}</div>
                      <div className="mt-1.5 font-mono text-[10px] text-teal-700 bg-white p-1.5 rounded border border-teal-200">{selectedMappingNode.creates_or_updates}</div>
                    </div>
                  )}
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="mb-2.5 font-extrabold uppercase tracking-wider text-slate-400 text-[10px]">객체 엔티티 타입</div>
                    <div className="flex flex-wrap gap-1.5">
                      {(selectedOntologyMapping?.entity_types ?? []).map((item) => (
                        <span key={item.name} className="badge badge-neutral">{item.label ?? item.name}</span>
                      ))}
                    </div>
                  </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="mb-2.5 font-extrabold uppercase tracking-wider text-slate-400 text-[10px]">객체간 관계 타입</div>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                      {(selectedOntologyMapping?.relation_types ?? []).map((item) => (
                        <div key={item.name} className="rounded-lg bg-white border border-slate-200 px-2.5 py-1.5 font-mono text-[10px] text-slate-600">
                          {item.from_type} → <span className="text-teal-400 font-bold">{item.label ?? item.name}</span> → {item.to_type}
                        </div>
                      ))}
                    </div>
                  </div>
                  <button className="btn btn-ghost w-full py-2.5 text-xs font-bold" onClick={() => void handleInstallOntologyMapping()} disabled={!selectedMappingId || mappingInstalling}>
                    {mappingInstalling ? "설치 중..." : "온톨로지 스키마 강제 동기화"}
                  </button>
                </div>
              )}

              {sideTab === "input_output" && (
                selectedNode ? (
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm font-bold text-slate-900">노드 입출력</div>
                      <div className="font-mono text-slate-500 text-[10px] mt-0.5">{selectedNode.id}</div>
                    </div>
                    {selectedResult ? (
                      <div className="space-y-4">
                        {/* Status and Metadata */}
                        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                          <div className="flex items-center justify-between mb-2.5">
                            <div className="font-bold text-emerald-900 text-xs">실행 상태</div>
                            <span className={`badge ${selectedResult.status === "success" ? "badge-low" : selectedResult.status === "error" ? "badge-high" : "badge-medium"}`}>
                              {selectedResult.status === "success" ? "✓ 성공" : selectedResult.status === "error" ? "✗ 실패" : selectedResult.status}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-[10px]">
                            <div>
                              <div className="text-emerald-700 font-semibold mb-0.5">소요 시간</div>
                              <div className="font-mono text-emerald-900">{selectedResult.duration_ms}ms</div>
                            </div>
                            <div>
                              <div className="text-emerald-700 font-semibold mb-0.5">시작 시간</div>
                              <div className="font-mono text-emerald-900">{new Date(selectedResult.started_at).toLocaleTimeString("ko-KR")}</div>
                            </div>
                          </div>
                        </div>

                        {/* Skill-specific details */}
                        {selectedNode.type === "skill" && (selectedNode.data as WorkflowNodeData).skillId && (
                          <div className="rounded-xl border border-teal-200 bg-teal-50 p-4 text-[10px]">
                            <div className="font-bold text-teal-900 mb-2">스킬 실행 정보</div>
                            <div className="space-y-2 font-mono text-teal-800">
                              <div className="flex justify-between">
                                <span className="text-teal-700">Skill ID:</span>
                                <span className="font-semibold">{(selectedNode.data as WorkflowNodeData).skillId}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-teal-700">Type:</span>
                                <span className="font-semibold">{selectedNodeSkill?.implementation.type || "unknown"}</span>
                              </div>
                              {selectedNodeSkill?.version && (
                                <div className="flex justify-between">
                                  <span className="text-teal-700">Version:</span>
                                  <span className="font-semibold">{selectedNodeSkill.version}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Output Data */}
                        <div>
                          <div className="mb-2 font-bold text-slate-700 text-xs">Output Data</div>
                          <div className="terminal-box max-h-48 bg-slate-900 text-emerald-400 text-xs font-mono p-3 rounded border border-slate-700 overflow-auto">
                            {typeof selectedResult.output === "string" ? (
                              selectedResult.output.startsWith("{") || selectedResult.output.startsWith("[") ? (
                                <pre>{JSON.stringify(JSON.parse(selectedResult.output), null, 2)}</pre>
                              ) : (
                                selectedResult.output
                              )
                            ) : (
                              JSON.stringify(selectedResult.output, null, 2)
                            )}
                          </div>
                        </div>

                        {/* Node Info */}
                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-5 text-slate-600">
                          <div className="font-bold mb-1.5">노드 정보</div>
                          <div className="space-y-1 font-mono text-[10px]">
                            <div><span className="text-slate-500">Node ID:</span> {selectedResult.node_id}</div>
                            <div><span className="text-slate-500">Type:</span> {selectedResult.type}</div>
                            <div><span className="text-slate-500">Label:</span> {selectedResult.label}</div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-slate-500 text-center font-medium text-sm">
                        <div>이 노드는 아직 실행되지 않았습니다.</div>
                        <div className="text-xs mt-1">워크플로우를 실행하면 입출력 데이터가 여기 표시됩니다.</div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="leading-5 text-slate-500 font-medium py-6 text-center">캔버스에서 노드를 선택하면 입출력 데이터를 확인할 수 있습니다.</div>
                )
              )}

              {sideTab === "history" && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-bold text-slate-900">워크플로우별 실행 이력</div>
                      <div className="mt-0.5 max-w-[250px] truncate font-mono text-[10px] text-slate-500">{graphName || graphId || "선택된 워크플로우 없음"}</div>
                    </div>
                    <span className="badge badge-neutral font-mono">{runs.length} Runs</span>
                  </div>
                  {runsLoading ? (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-slate-500 text-center font-medium">데이터 불러오는 중...</div>
                  ) : runs.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-slate-500 text-center font-medium">과거 실행 이력이 없습니다.</div>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                      {runs.slice(0, 8).map((run) => (
                        <button
                          key={run.run_id}
                          type="button"
                          onClick={() => { setActiveNodeId(null); setSideTab("run"); }}
                          className="w-full rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 text-left"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-mono text-xs text-slate-455">{run.run_id.slice(0, 16)}</span>
                            <span className={`badge ${run.status === "succeeded" ? "badge-low" : run.status === "failed" ? "badge-high" : "badge-neutral"}`}>
                              {run.status === "succeeded" ? "✓ 성공" : run.status === "failed" ? "✗ 실패" : run.status}
                            </span>
                          </div>
                          <div className="mt-2 text-slate-500 text-[10px] font-semibold">{new Date(run.started_at).toLocaleString("ko-KR")}</div>
                          <div className="mt-1.5 space-y-1">
                            {run.steps.slice(0, 5).map((step) => (
                              <div key={step.step_id} className="flex items-center justify-between gap-2 px-2 py-1 bg-slate-50 rounded border border-slate-100 text-[10px]">
                                <span className="truncate font-mono text-slate-500">{step.node_id}</span>
                                <span className={`shrink-0 font-bold ${
                                  step.status === "succeeded" ? "text-green-600" :
                                  step.status === "failed" ? "text-red-600" :
                                  "text-slate-400"
                                }`}>
                                  {step.status === "succeeded" ? "✓" : step.status === "failed" ? "✗" : "-"}
                                </span>
                              </div>
                            ))}
                            {run.steps.length > 5 && (
                              <div className="text-[9px] text-slate-400 px-2 font-semibold">외 {run.steps.length - 5}개 단계</div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </aside>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header gap-3 rounded-t-xl bg-white px-5 py-3.5">
          <div>
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-900">Service Request Simulation</h3>
            <p className="text-[10px] text-slate-500 font-semibold mt-0.5">Local mock NLP interpreter. Full workflows run using graph engines.</p>
          </div>
          <button className="btn btn-primary text-xs px-4" onClick={runLocalSimulation}>Simulate</button>
        </div>
        <div className="panel-body grid gap-4 bg-slate-50 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.8fr)]">
          <textarea
            className="premium-input min-h-28 w-full font-mono text-xs p-3.5"
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            placeholder="시뮬레이션할 입력 문장을 여기에 타이핑하세요."
          />
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            {!simulation ? (
              <div className="text-slate-500 text-xs leading-5">요청 문장을 입력하고 Simulate 버튼을 누르면 이쪽에 근거 정보 및 가상 처리 경로가 출력됩니다.</div>
            ) : (
              <div className="space-y-2.5 text-xs">
                <div><span className="font-bold text-slate-500">분류 카테고리:</span> <span className="font-mono text-slate-800">{simulation.category}</span></div>
                <div><span className="font-bold text-slate-450">분기 처리 경로:</span> <span className="badge badge-neutral">{simulation.route}</span></div>
                <div><span className="font-bold text-slate-500">참조 근거 문서:</span> <span className="font-mono text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">{simulation.evidence.join(" / ")}</span></div>
                <div className="terminal-box max-h-36 mt-2">{simulation.answer}</div>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header gap-3 rounded-t-xl bg-white px-5 py-3.5">
          <h3 className="text-sm font-semibold">Node Execution Results</h3>
          <span className="font-mono text-[10px] tracking-wide text-slate-500 bg-slate-50 border border-slate-200 px-2.5 py-0.5 rounded-md">{results.length} items</span>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead>
              <tr className="bg-slate-50">
                <th className="py-3 px-5 text-center w-12">#</th>
                <th className="py-3 px-4">Node</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4 w-24">Status</th>
                <th className="py-3 px-4 w-28">Duration</th>
                <th className="py-3 px-4">Output Log</th>
                <th className="py-3 px-4 w-32">Started</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-8 text-slate-500 font-medium">아직 실행된 노드가 없습니다. 워크플로우를 먼저 실행(Run)해주세요.</td></tr>
              ) : (
                results.map((result, index) => (
                  <tr key={`${result.node_id}-${index}`} className="hover:bg-slate-50 transition-colors">
                    <td className="text-center font-mono text-slate-500 font-bold px-5">{index + 1}</td>
                    <td className="font-bold text-slate-800">{result.label}</td>
                    <td className="font-mono text-[10px] text-slate-450">{result.type}</td>
                    <td><span className={`badge ${result.status === "success" ? "badge-low" : result.status === "error" ? "badge-high" : "badge-medium"}`}>{result.status}</span></td>
                    <td className="font-mono text-slate-400">{result.duration_ms}ms</td>
                    <td className="max-w-[340px]">
                      <div className="font-mono text-[10px] truncate bg-slate-50 border border-slate-200 px-2 py-1.5 rounded text-sky-700 cursor-pointer" title={result.output} onClick={() => { setSelectedNodeId(result.node_id); setActiveNodeId(result.node_id); setSideTab("input_output"); }}>
                        {result.output}
                      </div>
                    </td>
                    <td className="font-mono text-slate-500 text-[10px]">{new Date(result.started_at).toLocaleTimeString()}</td>
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
