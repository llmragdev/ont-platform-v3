"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { OntologyEntity, OntologyMgmtGraph, WorkflowGraph, WorkflowRun, WorkflowStepRun } from "@/types/api";

const TRACE_CONFIG: Record<string, { docId: string; cardTypes: string[]; label: string }> = {
  "scenario1.customer_question_auto_reply": {
    docId: "service-requests",
    cardTypes: ["ServiceRequest", "WorkflowExecution", "AutoReply", "ExternalComment"],
    label: "고객 자동 댓글",
  },
  "factory.repeated_fault_response": {
    docId: "factory-repeated-faults",
    cardTypes: ["Factory", "ProductionLine", "ProcessStep", "Equipment", "FaultEvent", "MaintenanceTask", "QualityIssue"],
    label: "공장 반복 고장",
  },
};

const TYPE_STYLE: Record<string, string> = {
  ServiceRequest: "border-teal-200 bg-teal-50 text-teal-900",
  WorkflowExecution: "border-blue-200 bg-blue-50 text-blue-900",
  AutoReply: "border-emerald-200 bg-emerald-50 text-emerald-900",
  ExternalComment: "border-slate-200 bg-slate-50 text-slate-900",
  Factory: "border-amber-200 bg-amber-50 text-amber-900",
  ProductionLine: "border-orange-200 bg-orange-50 text-orange-900",
  ProcessStep: "border-yellow-200 bg-yellow-50 text-yellow-900",
  Equipment: "border-cyan-200 bg-cyan-50 text-cyan-900",
  FaultEvent: "border-rose-200 bg-rose-50 text-rose-900",
  MaintenanceTask: "border-indigo-200 bg-indigo-50 text-indigo-900",
  QualityIssue: "border-fuchsia-200 bg-fuchsia-50 text-fuchsia-900",
};

const TYPE_LABEL: Record<string, string> = {
  ServiceRequest: "요청",
  WorkflowExecution: "워크플로우 실행",
  AutoReply: "자동 답변",
  ExternalComment: "외부 댓글",
  Factory: "공장",
  ProductionLine: "라인",
  ProcessStep: "공정",
  Equipment: "설비",
  FaultEvent: "고장 이력",
  MaintenanceTask: "정비 지시",
  QualityIssue: "품질 이슈",
};

function formatDate(value?: string | null) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString("ko-KR");
  } catch {
    return value;
  }
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

function stepColor(status: string) {
  if (status === "succeeded") return "bg-emerald-50 text-emerald-700";
  if (status === "failed") return "bg-rose-50 text-rose-700";
  if (status === "running") return "bg-blue-50 text-blue-700";
  return "bg-slate-50 text-slate-500";
}

function getWriteback(run: WorkflowRun | null): Record<string, unknown> | null {
  const auditStep = run?.steps.find((step) => step.node_id === "audit-write");
  return (auditStep?.output?.ontology_writeback as Record<string, unknown> | undefined) ?? null;
}

function getQuestionIds(run: WorkflowRun | null): string[] {
  const wb = getWriteback(run);
  const ids = wb?.question_ids;
  return Array.isArray(ids) ? ids.map(String) : [];
}

function getPostItems(run: WorkflowRun | null): Array<Record<string, unknown>> {
  const postStep = run?.steps.find((step) => step.node_id === "post-comment");
  const items = postStep?.output?.items;
  return Array.isArray(items) ? (items as Array<Record<string, unknown>>) : [];
}

function getFactoryWritebacks(run: WorkflowRun | null): Array<Record<string, unknown>> {
  const ontologyStep = run?.steps.find((step) => step.node_id === "ontology-write");
  const items = ontologyStep?.output?.items;
  return Array.isArray(items) ? (items.filter(Boolean) as Array<Record<string, unknown>>) : [];
}

function findCommentNode(traceNodes: OntologyMgmtGraph["nodes"], traceEdges: OntologyMgmtGraph["edges"]) {
  const postedAs = traceEdges.find((edge) => edge.label === "posted_as");
  if (!postedAs) return null;
  return traceNodes.find((node) => node.id === postedAs.to) ?? null;
}

function StepList({ steps }: { steps: WorkflowStepRun[] }) {
  return (
    <div className="space-y-2">
      {steps.map((step, index) => (
        <div key={step.step_id} className="rounded-md border border-slate-200 bg-white p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-xs text-slate-400">STEP {index + 1}</div>
              <div className="font-semibold text-slate-800">{step.node_id}</div>
              <div className="text-xs text-slate-500">{step.node_type}</div>
            </div>
            <span className={`rounded px-2 py-1 text-xs ${stepColor(step.status)}`}>{step.status}</span>
          </div>
          {step.error && <div className="mt-2 text-xs text-rose-600">{step.error}</div>}
        </div>
      ))}
    </div>
  );
}

function TraceCard({
  node,
  selected,
  onSelect,
}: {
  node: OntologyMgmtGraph["nodes"][number] | null;
  selected: boolean;
  onSelect: () => void;
}) {
  if (!node) {
    return (
      <div className="min-h-28 rounded-md border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-400">
        연결 객체 없음
      </div>
    );
  }
  const style = TYPE_STYLE[node.type] ?? "border-slate-200 bg-white text-slate-900";
  return (
    <button
      type="button"
      className={`min-h-28 w-full rounded-md border p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow ${style} ${selected ? "ring-2 ring-teal-500" : ""}`}
      onClick={onSelect}
    >
      <div className="text-xs font-semibold">{TYPE_LABEL[node.type] ?? node.type}</div>
      <div className="mt-2 text-sm font-bold">{node.label}</div>
      <div className="mt-1 truncate text-xs opacity-70">{node.id}</div>
    </button>
  );
}

export function WorkflowOntologyTrace() {
  const [graphs, setGraphs] = useState<WorkflowGraph[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState("");
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [ontologyGraph, setOntologyGraph] = useState<OntologyMgmtGraph>({ nodes: [], edges: [] });
  const [entities, setEntities] = useState<OntologyEntity[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedGraph = graphs.find((graph) => graph.id === selectedGraphId) ?? null;
  const selectedExecutor = selectedGraph?.runtime?.executor ?? "";
  const selectedTraceConfig = TRACE_CONFIG[selectedExecutor] ?? TRACE_CONFIG["scenario1.customer_question_auto_reply"];

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const list = await api.workflowGraphs.list();
        const traceGraphs = (Array.isArray(list) ? list : []).filter(
          (graph) => Boolean(graph.runtime?.executor && TRACE_CONFIG[graph.runtime.executor])
        );
        setGraphs(traceGraphs);
        if (traceGraphs[0]) setSelectedGraphId(traceGraphs[0].id);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const loadRuns = useCallback(async (graphId: string) => {
    if (!graphId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.workflowGraphs.listRuns(graphId);
      const list = Array.isArray(res.runs) ? res.runs : [];
      setRuns(list);
      setSelectedRunId(list[0]?.run_id ?? "");
    } catch (err) {
      setRuns([]);
      setSelectedRunId("");
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadOntology = useCallback(async () => {
    try {
      const [graph, entityPage] = await Promise.all([
        api.ontologyMgmt.getGraph(selectedTraceConfig.docId),
        api.ontologyMgmt.listEntities(selectedTraceConfig.docId, { size: 500 }),
      ]);
      setOntologyGraph(graph);
      setEntities(entityPage.entities);
    } catch (err) {
      setOntologyGraph({ nodes: [], edges: [] });
      setEntities([]);
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [selectedTraceConfig.docId]);

  useEffect(() => { void loadRuns(selectedGraphId); }, [selectedGraphId, loadRuns]);
  useEffect(() => { void loadOntology(); }, [loadOntology]);

  const selectedRun = runs.find((run) => run.run_id === selectedRunId) ?? null;
  const writeback = getWriteback(selectedRun);
  const questionIds = getQuestionIds(selectedRun);
  const postItems = getPostItems(selectedRun);
  const factoryWritebacks = useMemo(() => getFactoryWritebacks(selectedRun), [selectedRun]);

  const trace = useMemo(() => {
    if (!selectedRun) return { nodes: [] as OntologyMgmtGraph["nodes"], edges: [] as OntologyMgmtGraph["edges"] };
    const ids = new Set<string>();
    ids.add(`wfe-${selectedRun.run_id}`);

    if (selectedExecutor === "factory.repeated_fault_response") {
      factoryWritebacks.forEach((item) => {
        const factoryEventId = String(item.factory_event_id ?? "");
        const faultEventId = String(item.fault_event_id ?? "");
        if (factoryEventId) ids.add(`sr-${factoryEventId}`);
        if (faultEventId) ids.add(faultEventId);
      });
    } else {
      questionIds.forEach((questionId) => {
        ids.add(`sr-${questionId}`);
        ids.add(`reply-${questionId}-${selectedRun.run_id}`);
      });
    }

    const seedEdges = ontologyGraph.edges.filter((edge) => ids.has(edge.from) || ids.has(edge.to));
    seedEdges.forEach((edge) => { ids.add(edge.from); ids.add(edge.to); });

    const nodes = ontologyGraph.nodes.filter((node) => ids.has(node.id));
    const nodeIds = new Set(nodes.map((node) => node.id));
    const edges = ontologyGraph.edges.filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to));
    return { nodes, edges };
  }, [factoryWritebacks, ontologyGraph, questionIds, selectedExecutor, selectedRun]);

  const nodeByType = useMemo(() => {
    const byType = new Map<string, OntologyMgmtGraph["nodes"][number]>();
    trace.nodes.forEach((node) => {
      if (!byType.has(node.type)) byType.set(node.type, node);
    });
    const commentNode = findCommentNode(trace.nodes, trace.edges);
    if (commentNode) byType.set("ExternalComment", commentNode);
    return byType;
  }, [trace]);

  const selectedNode = trace.nodes.find((node) => node.id === selectedNodeId) ?? trace.nodes[0] ?? null;
  const selectedEntity = selectedNode ? entities.find((entity) => entity.id === selectedNode.id) : null;

  useEffect(() => {
    setSelectedNodeId(null);
  }, [selectedRunId]);

  return (
    <div className="space-y-4">
      <section className="panel">
        <div className="panel-header">
          <div>
            <h3 className="text-sm font-semibold">Workflow-Ontology Trace</h3>
            <p className="text-xs text-slate-500">워크플로우 실행 결과가 어떤 온톨로지 객체와 관계로 남았는지 확인합니다.</p>
          </div>
          <button className="btn btn-ghost text-xs" onClick={() => void loadOntology()}>새로고침</button>
        </div>
        <div className="panel-body grid gap-3 md:grid-cols-[minmax(220px,0.9fr)_minmax(260px,1.1fr)]">
          <label className="block text-xs">
            <span className="mb-1 block text-slate-500">워크플로우</span>
            <select className="w-full rounded-md border border-slate-300 px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950" value={selectedGraphId} onChange={(e) => setSelectedGraphId(e.target.value)}>
              {graphs.length === 0 && <option value="">저장된 워크플로우 없음</option>}
              {graphs.map((graph) => <option key={graph.id} value={graph.id}>{graph.name}</option>)}
            </select>
          </label>
          <label className="block text-xs">
            <span className="mb-1 block text-slate-500">실행 회차</span>
            <select className="w-full rounded-md border border-slate-300 px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950" value={selectedRunId} onChange={(e) => setSelectedRunId(e.target.value)}>
              {runs.length === 0 && <option value="">실행 이력 없음</option>}
              {runs.map((run) => <option key={run.run_id} value={run.run_id}>{formatDate(run.started_at)} / {run.status} / {run.run_id}</option>)}
            </select>
          </label>
        </div>
      </section>

      {error && <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      {loading && <div className="text-sm text-slate-400">로딩 중...</div>}

      <div className="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_340px]">
        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold">실행 단계</h3>
            <span className="badge badge-neutral">{selectedRun?.steps.length ?? 0}단계</span>
          </div>
          <div className="panel-body">
            {selectedRun ? <StepList steps={selectedRun.steps} /> : <p className="text-sm text-slate-400">실행을 선택하세요.</p>}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3 className="text-sm font-semibold">온톨로지 흐름</h3>
              <p className="text-xs text-slate-500">{selectedGraph?.name ?? "-"} / {selectedTraceConfig.label} / {selectedRun?.run_id ?? "-"}</p>
            </div>
            <span className={`badge ${selectedRun?.status === "succeeded" ? "badge-low" : "badge-neutral"}`}>{selectedRun?.status ?? "-"}</span>
          </div>
          <div className="panel-body space-y-4">
            <div className="grid gap-3 lg:grid-cols-3">
              {selectedTraceConfig.cardTypes.map((typeName) => (
                <TraceCard
                  key={typeName}
                  node={nodeByType.get(typeName) ?? null}
                  selected={selectedNodeId === nodeByType.get(typeName)?.id}
                  onSelect={() => setSelectedNodeId(nodeByType.get(typeName)?.id ?? null)}
                />
              ))}
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
              <div className="font-semibold text-slate-700">관계</div>
              {trace.edges.length === 0 ? (
                <div className="mt-2 text-slate-400">연결된 관계가 없습니다.</div>
              ) : (
                <div className="mt-2 grid gap-1">
                  {trace.edges.map((edge) => (
                    <div key={edge.id}>
                      <span className="font-mono text-slate-500">{edge.from}</span>
                      <span className="mx-2 text-teal-700">{edge.label}</span>
                      <span className="font-mono text-slate-500">{edge.to}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-md border border-slate-200 bg-white p-3">
                <div className="text-xs text-slate-500">{selectedExecutor === "factory.repeated_fault_response" ? "공장 이벤트" : "질문 ID"}</div>
                <div className="mt-1 text-sm font-semibold">
                  {selectedExecutor === "factory.repeated_fault_response"
                    ? factoryWritebacks.map((item) => String(item.factory_event_id ?? "")).filter(Boolean).join(", ") || "-"
                    : questionIds.join(", ") || "-"}
                </div>
              </div>
              <div className="rounded-md border border-slate-200 bg-white p-3">
                <div className="text-xs text-slate-500">Write-back</div>
                <div className="mt-1 text-sm font-semibold">
                  {selectedExecutor === "factory.repeated_fault_response" ? `${factoryWritebacks.length}건` : String(writeback?.status ?? "-")}
                </div>
              </div>
              <div className="rounded-md border border-slate-200 bg-white p-3">
                <div className="text-xs text-slate-500">{selectedExecutor === "factory.repeated_fault_response" ? "댓글/정비" : "댓글 등록"}</div>
                <div className="mt-1 text-sm font-semibold">{selectedExecutor === "factory.repeated_fault_response" ? "s2_factory_mcp" : `${postItems.length}건`}</div>
              </div>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3 className="text-sm font-semibold">객체 상세</h3>
          </div>
          <div className="panel-body">
            {!selectedNode ? (
              <p className="text-sm text-slate-400">Trace 객체를 선택하세요.</p>
            ) : (
              <div className="space-y-3 text-sm">
                <div>
                  <div className="text-xs text-slate-500">유형</div>
                  <div className="font-semibold">{TYPE_LABEL[selectedNode.type] ?? selectedNode.type}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">이름</div>
                  <div className="font-semibold">{selectedNode.label}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">ID</div>
                  <div className="break-all font-mono text-xs">{selectedNode.id}</div>
                </div>
                <div className="border-t border-slate-100 pt-3">
                  <div className="mb-2 text-xs font-semibold text-slate-500">속성</div>
                  <div className="space-y-1">
                    {Object.entries(selectedEntity?.properties ?? selectedNode.properties ?? {}).map(([key, value]) => (
                      <div key={key} className="grid grid-cols-[90px_minmax(0,1fr)] gap-2 border-b border-slate-50 py-1 text-xs">
                        <span className="text-slate-500">{key}</span>
                        <span className="break-all text-slate-800">{formatValue(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
