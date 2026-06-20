"use client";
import type {
  AuditEvent,
  DocumentInfo,
  HybridAskResponse,
  IntegrationTestProject,
  IntegrationTestRun,
  IntegrationTestRunMeta,
  OntologyDocInfo,
  OntologyEntity,
  OntologyMgmtGraph,
  OntologyMgmtRelationType,
  OntologyMgmtSchema,
  TenantConfig,
  Skill,
  AssistantChatRequest,
  AssistantChatResponse,
  WorkflowGraph,
  WorkflowOntologyMapping,
  WorkflowOntologyMappingInstallResult,
  WorkflowQueueRow,
  WorkflowRun,
  WorkflowTemplate,
  SparqlQueryResponse,
} from "@/types/api";
import type {
  ImportPreview,
  LinkedResource,
  MappingCandidate,
  OntologyImportRequest,
  OntologyImportResult,
  OntologyMappingRule,
  RDFGraphData,
} from "@/types/rdf";
import type { DLQItemsResponse, DLQItem, ReplayResponse, WriteBackStatistics } from "@/types/writeback";

// ── Global tenant state ───────────────────────────────────────────────────────

export const DEFAULT_TENANT: TenantConfig = {
  userId: "demo-user",
  companyId: "demo-co",
  projectId: "proj-01",
  role: "FinanceManager",
};

let _currentTenant: TenantConfig = { ...DEFAULT_TENANT };

export function setCurrentTenant(cfg: TenantConfig) {
  _currentTenant = cfg;
}

export function getCurrentTenant(): TenantConfig {
  return _currentTenant;
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

function tenantHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const t = _currentTenant;
  return {
    "Content-Type": "application/json",
    "x-user-id": t.userId,
    "x-company-id": t.companyId,
    "x-project-id": t.projectId,
    "x-role": t.role,
    ...extra,
  };
}

export class ApiClientError extends Error {
  constructor(public code: string, message: string, public status: number) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const hdrs = tenantHeaders(
    (init.headers as Record<string, string>) ?? {}
  );
  delete (hdrs as Record<string, string>)["Content-Type"];
  if (init.body) hdrs["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: hdrs,
    cache: "no-store",
  });
  const text = await response.text();
  let data: Record<string, unknown> | null = null;
  try { data = text ? (JSON.parse(text) as Record<string, unknown>) : null; } catch { /* non-JSON response */ }
  if (!response.ok) {
    const err = data?.error as Record<string, unknown> | undefined;
    const detail = data?.detail as Record<string, unknown> | string | undefined;
    const detailError = typeof detail === "object" ? (detail.error as Record<string, unknown> | undefined) : undefined;
    const code = (err?.code ?? "UNKNOWN") as string;
    const message = (err?.message ?? detailError?.message ?? (typeof detail === "string" ? detail : undefined) ?? text ?? response.statusText) as string;
    throw new ApiClientError(code, message, response.status);
  }
  return data as T;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

// ── API object ────────────────────────────────────────────────────────────────

export const api = {
  health: () => request<{ status: string; version: string }>("/api/health"),

  demo: {
    resetBoards: (payload?: any) => request<any>("/api/demo/reset", { method: "POST", body: JSON.stringify(payload) }),
  },

  dataEngineering: {
    listDatabases: () => request<any>("/api/data-engineering/databases"),
    listTables: (db?: string) => request<any>(`/api/data-engineering/tables?db=${db}`),
    listQueries: (arg1?: any, arg2?: any) => request<any>("/api/data-engineering/queries"),
    executeQuery: (payload: any) => request<any>("/api/data-engineering/query", { method: "POST", body: JSON.stringify(payload) }),
    getExecutionStatus: (id: string, arg2?: any, arg3?: any) => request<any>(`/api/data-engineering/execution/${id}`),
    saveQuery: (payload: any) => request<any>(`/api/data-engineering/queries`, { method: "POST", body: JSON.stringify(payload) })
  },

  dataCatalog: {
    getTables: () => request<any>("/api/data-catalog/tables"),
    executeQuery: (payload: any) => request<any>("/api/data-catalog/query", { method: "POST", body: JSON.stringify(payload) }),
    search: (q: string) => request<any>(`/api/data-catalog/search?q=${encodeURIComponent(q)}`),
  },

  // ── Platform AI Assistant ────────────────────────────────────────────────

  assistant: {
    chat: (body: AssistantChatRequest) =>
      request<AssistantChatResponse>("/api/assistant/chat", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },

  // ── Streamlit Apps ─────────────────────────────────────────────────────────

  streamlitApps: {
    save: (body: { app_id: string; folder_name: string; file_name: string; code: string }) =>
      request<{
        app_id: string;
        status: "saved";
        file_path: string;
        message: string;
      }>("/api/streamlit-apps/save", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    run: (body: { app_id: string; folder_name: string; file_name: string; code: string }) =>
      request<{
        app_id: string;
        status: "running" | "fallback" | "error";
        mode: "streamlit" | "fallback";
        url: string;
        file_path: string;
        port: number;
        message: string;
      }>("/api/streamlit-apps/run", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    stop: (appId: string) =>
      request<{ app_id: string; status: string; message: string }>(
        `/api/streamlit-apps/stop/${encodeURIComponent(appId)}`,
        { method: "POST" }
      ),

    list: () => request<{ programs: any[] }>("/api/streamlit-apps"),
    duplicate: (appId: string, payload?: any) => request<any>(`/api/streamlit-apps/duplicate`, { method: "POST", body: JSON.stringify(payload || appId) }),
    remove: (appId: string) => request<{ status: string }>(`/api/streamlit-apps/${encodeURIComponent(appId)}`, { method: "DELETE" }),
  },

  // ── Audit ──────────────────────────────────────────────────────────────────

  auditEvents: (limit = 200) =>
    request<{ events: AuditEvent[] }>(`/api/audit/events?limit=${limit}`),

  // ── Documents ─────────────────────────────────────────────────────────────

  documents: {
    list: (projectId?: string) =>
      request<{ documents: DocumentInfo[] }>(`/api/documents${projectId ? `?project_id=${projectId}` : ""}`),

    upload: async (file: File): Promise<DocumentInfo & { status: string }> => {
      const t = _currentTenant;
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/api/documents/upload`, {
        method: "POST",
        headers: {
          "x-user-id": t.userId,
          "x-company-id": t.companyId,
          "x-project-id": t.projectId,
          "x-role": t.role,
        },
        body: form,
        cache: "no-store",
      });
      const text = await res.text();
      let data: Record<string, unknown> | null = null;
      try { data = text ? (JSON.parse(text) as Record<string, unknown>) : null; } catch { /* not JSON */ }
      if (!res.ok) {
        const errObj = data?.error as Record<string, unknown> | undefined;
        const msg = (data?.detail ?? errObj?.message ?? text ?? res.statusText) as string;
        throw new ApiClientError((errObj?.code ?? "UPLOAD_ERROR") as string, msg, res.status);
      }
      return data as unknown as DocumentInfo & { status: string };
    },

    remove: (docId: string) =>
      request<{ deleted: string }>(`/api/documents/${encodeURIComponent(docId)}`, { method: "DELETE" }),
  },

  // ── Ontology Management ───────────────────────────────────────────────────

  ontologyMgmt: {
    listDocs: () =>
      request<OntologyDocInfo[]>("/api/ontology").then((data) =>
        Array.isArray(data) ? data : (data as { ontologies?: OntologyDocInfo[] }).ontologies ?? (data as unknown as OntologyDocInfo[])
      ),

    createDoc: (docId: string) =>
      request<OntologyDocInfo>("/api/ontology", {
        method: "POST",
        body: JSON.stringify({ doc_id: docId }),
      }),

    getSchema: async (): Promise<OntologyMgmtSchema> => {
      const raw = await request<{
        builtin_entity_types?: Array<{ name: string; description: string; properties?: string[] }>;
        domain_entity_types?: Array<{ name: string; description: string; properties?: string[] }>;
        domain_relation_types?: Array<{ name: string; from_type?: string; to_type?: string }>;
      }>("/api/ontology/schema");
      const entity_types = [
        ...(raw.builtin_entity_types ?? []).map((t) => ({ name: t.name, description: t.description, is_builtin: true, properties: t.properties ?? [] })),
        ...(raw.domain_entity_types ?? []).map((t) => ({ name: t.name, description: t.description, is_builtin: false, properties: t.properties ?? [] })),
      ];
      const relation_types = (raw.domain_relation_types ?? []).map((r) => ({
        name: r.name,
        from_type: r.from_type ?? "",
        to_type: r.to_type ?? "",
      }));
      return { entity_types, relation_types };
    },

    addEntityType: (body: { name: string; description: string; properties: string[] }) =>
      request<{ name: string; description: string; is_builtin: boolean; properties: string[] }>(
        "/api/ontology/mgmt/schema/entity-types",
        { method: "POST", body: JSON.stringify(body) }
      ),

    deleteEntityType: (name: string) =>
      request<{ status: string; name: string }>(
        `/api/ontology/mgmt/schema/entity-types/${encodeURIComponent(name)}`,
        { method: "DELETE" }
      ),

    addRelationType: (body: { name: string; from_type: string; to_type: string }) =>
      request<OntologyMgmtRelationType>(
        "/api/ontology/mgmt/schema/relation-types",
        { method: "POST", body: JSON.stringify(body) }
      ),

    deleteRelationType: (name: string) =>
      request<{ status: string; name: string }>(
        `/api/ontology/mgmt/schema/relation-types/${encodeURIComponent(name)}`,
        { method: "DELETE" }
      ),

    listEntities: (docId: string, params?: { entity_type?: string; page?: number; size?: number }) => {
      const qs = new URLSearchParams();
      if (params?.entity_type) qs.set("type_filter", params.entity_type);
      if (params?.page && params.page > 1) qs.set("offset", String((params.page - 1) * (params.size ?? 20)));
      if (params?.size) qs.set("limit", String(params.size));
      const q = qs.toString();
      return request<OntologyEntity[]>(`/api/ontology/${encodeURIComponent(docId)}/entities${q ? "?" + q : ""}`)
        .then((items) => ({
          entities: Array.isArray(items) ? items : [],
          total: Array.isArray(items) ? items.length : 0,
          page: params?.page ?? 1,
        }));
    },

    createEntity: (docId: string, body: { type: string; name: string; properties: Record<string, unknown>; provenance?: Record<string, unknown> }) =>
      request<OntologyEntity>(`/api/ontology/${encodeURIComponent(docId)}/entities`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    updateEntity: (docId: string, entityId: string, body: { name?: string; properties?: Record<string, unknown>; provenance?: Record<string, unknown> }) =>
      request<OntologyEntity>(`/api/ontology/${encodeURIComponent(docId)}/entities/${encodeURIComponent(entityId)}`, {
        method: "PUT",
        body: JSON.stringify(body),
      }),

    deleteEntity: (docId: string, entityId: string) =>
      request<{ deleted: string }>(`/api/ontology/${encodeURIComponent(docId)}/entities/${encodeURIComponent(entityId)}`, {
        method: "DELETE",
      }),

    listRelationships: (docId: string) =>
      request<OntologyMgmtGraph["edges"]>(`/api/ontology/${encodeURIComponent(docId)}/relationships`)
        .then((data) => ({ relationships: Array.isArray(data) ? data : [] })),

    addRelationship: (docId: string, body: { from_id: string; relation: string; to_id: string }) =>
      request<{ id: string; from_id: string; relation: string; to_id: string }>(
        `/api/ontology/${encodeURIComponent(docId)}/relationships`,
        { method: "POST", body: JSON.stringify(body) }
      ),

    deleteRelationship: (docId: string, relId: string) =>
      request<{ deleted: string }>(
        `/api/ontology/${encodeURIComponent(docId)}/relationships/${encodeURIComponent(relId)}`,
        { method: "DELETE" }
      ),

    getGraph: (docId: string) =>
      request<{ nodes: OntologyMgmtGraph["nodes"]; edges: OntologyMgmtGraph["edges"] }>(
        `/api/ontology/${encodeURIComponent(docId)}/graph`
      ).then((raw): OntologyMgmtGraph => {
        const nodes = (raw.nodes ?? []).map((n: { id: string; data?: { label?: string; object_type?: string;[k: string]: unknown };[k: string]: unknown }) => ({
          id: n.id,
          label: n.data?.label ?? (n as { name?: string }).name ?? n.id,
          type: n.data?.object_type ?? (n as { type?: string }).type ?? "UNKNOWN",
          properties: (n.data ?? {}) as Record<string, unknown>,
        }));
        const edges = (raw.edges ?? []).map((e: { id: string; source?: string; target?: string; from_id?: string; to_id?: string; label?: string; relation?: string }) => ({
          id: e.id,
          from: e.source ?? e.from_id ?? "",
          to: e.target ?? e.to_id ?? "",
          label: e.label ?? e.relation ?? "",
        }));
        return { nodes, edges };
      }),

    seedOrderExample: () =>
      request<{ doc_id: string; entity_count: number; query: string; message: string }>(
        "/api/ontology/examples/order-submitted",
        { method: "POST" }
      ),
  },

  // ── Hybrid Ask ────────────────────────────────────────────────────────────

  hybridAsk: (question: string, docIds?: string[]) =>
    request<HybridAskResponse>("/api/hybrid/ask", {
      method: "POST",
      body: JSON.stringify({ question, doc_ids: docIds ?? null }),
    }),

  // ── Query Stream (SSE) ─────────────────────────────────────────────────
  // Author: Claude
  // Purpose: 실제 FastAPI Backend와 SSE 스트리밍 연결

  queryStream: (projectId: string, sessionId: string, query: string, mode: 'document_only' | 'document_with_limits' | 'expert_mode', options: {
    hide_irrelevant?: boolean;
    allow_partial?: boolean;
    separate_sources?: boolean;
    allow_general?: boolean;
    onSources?: (sources: any) => void;
    onToken?: (token: string) => void;
    onLimitations?: (limitations: string[]) => void;
    onFollowUps?: (suggestions: any[]) => void;
    onComplete?: (meta: any) => void;
    onError?: (error: Error) => void;
  }) => {
    const callbacks = options || {};
    const params = new URLSearchParams({
      project_id: projectId,
      session_id: sessionId,
      query: query,
      mode: mode,
      hide_irrelevant: (options?.hide_irrelevant ?? true).toString(),
      allow_partial: (options?.allow_partial ?? false).toString(),
      separate_sources: (options?.separate_sources ?? true).toString(),
      allow_general: (options?.allow_general ?? false).toString(),
    });

    const url = `${API_BASE}/api/v1/projects/${projectId}/query/stream?${params}`;

    const eventSource = new EventSource(url);

    eventSource.addEventListener('sources', (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📊 Sources received:', data);
        callbacks.onSources?.(data);
      } catch (err) {
        console.error('Failed to parse sources:', err);
      }
    });

    eventSource.addEventListener('answer_chunk', (event) => {
      try {
        const data = JSON.parse(event.data);
        const token = data.token || '';
        callbacks.onToken?.(token);
      } catch (err) {
        console.error('Failed to parse answer chunk:', err);
      }
    });

    eventSource.addEventListener('limitations', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.limitations && Array.isArray(data.limitations)) {
          callbacks.onLimitations?.(data.limitations);
        }
      } catch (err) {
        console.error('Failed to parse limitations:', err);
      }
    });

    eventSource.addEventListener('follow_ups', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.follow_up_suggestions && Array.isArray(data.follow_up_suggestions)) {
          callbacks.onFollowUps?.(data.follow_up_suggestions);
        }
      } catch (err) {
        console.error('Failed to parse follow-ups:', err);
      }
    });

    eventSource.addEventListener('complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('✅ Query complete:', data);
        callbacks.onComplete?.(data);
        eventSource.close();
      } catch (err) {
        console.error('Failed to parse complete:', err);
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (event) => {
      console.error('SSE Error:', event);
      callbacks.onError?.(new Error('쿼리 처리 중 오류가 발생했습니다.'));
      eventSource.close();
    });

    return eventSource;
  },

  // ── SPARQL Workbench ──────────────────────────────────────────────────────

  sparql: {
    query: (query: string, signal?: AbortSignal) =>
      request<SparqlQueryResponse>("/api/ontology/sparql", {
        method: "POST",
        body: JSON.stringify({ query }),
        signal,
      }),
  },

  // ── RDF + External Ontology ───────────────────────────────────────────────

  rdf: {
    graph: (entityId: string) =>
      request<RDFGraphData>(`/api/rdf/graph/${encodeURIComponent(entityId)}`),

    subgraph: (entityId: string, depth = 1, limit = 30) =>
      request<RDFGraphData>(
        `/api/rdf/subgraph?entity_id=${encodeURIComponent(entityId)}&depth=${depth}&limit=${limit}`
      ),

    neighbors: (entityId: string, limit = 30) =>
      request<RDFGraphData>(`/api/rdf/neighbors/${encodeURIComponent(entityId)}?limit=${limit}`),

    describeEntity: (entityId: string) =>
      request<{ resources: LinkedResource[] }>(`/api/sparql/describe/${encodeURIComponent(entityId)}`),

    importOntology: (payload: OntologyImportRequest) => {
      const endpoint = {
        dbpedia: "/api/import/dbpedia",
        wikidata: "/api/import/wikidata",
        rdf_file: "/api/import/rdf-file",
      }[payload.type];
      return request<OntologyImportResult>(endpoint, {
        method: "POST",
        body: JSON.stringify({
          identifier: payload.identifier,
          domain_id: payload.domain_id,
        }),
      });
    },

    mappingCandidates: (externalUri: string, externalLabel: string) =>
      request<{ candidates: MappingCandidate[] }>(
        `/api/ontology/mapping-candidates?external_uri=${encodeURIComponent(externalUri)}&external_label=${encodeURIComponent(externalLabel)}`
      ),

    saveMapping: (payload: OntologyMappingRule) =>
      request<OntologyMappingRule>("/api/ontology/mappings", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    importPreview: (payload: { type: string; identifier: string; domain_id: string }) =>
      request<ImportPreview>("/api/ontology/import/preview", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  // ── RAG vector search ─────────────────────────────────────────────────────

  ragAsk: (question: string) =>
    request<HybridAskResponse>("/api/hybrid/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  // ── Workflow ──────────────────────────────────────────────────────────────

  workflowQueue: () =>
    request<{ count: number; items: WorkflowQueueRow[] }>("/api/workflow/queue"),

  workflowExecute: (docId: string, entityId: string, action: string) =>
    request<{ entity_id: string; action: string; from_status: string; to_status: string }>(
      "/api/workflow/execute",
      { method: "POST", body: JSON.stringify({ doc_id: docId, entity_id: entityId, action }) }
    ),

  // ── WriteBack DLQ ─────────────────────────────────────────────────────────

  writeback: {
    getDLQItems: () =>
      request<DLQItemsResponse>("/api/writeback/dlq/items").then((data) => ({
        items: data.items ?? [],
        count: data.count ?? data.items?.length ?? 0,
      })),

    getDLQItem: (queueId: string) =>
      request<DLQItem>(`/api/writeback/dlq/items/${encodeURIComponent(queueId)}`),

    replayDLQItem: (queueId: string) =>
      request<ReplayResponse>(`/api/writeback/replay/${encodeURIComponent(queueId)}`, {
        method: "POST",
      }),

    getWritebackStatistics: () =>
      request<WriteBackStatistics>("/api/writeback/statistics"),
  },

  // ── WorkflowGraphs ────────────────────────────────────────────────────────

  workflowGraphs: {
    list: () =>
      request<WorkflowGraph[]>("/api/workflow-graphs"),

    get: (id: string) =>
      request<WorkflowGraph>(`/api/workflow-graphs/${id}`),

    save: (payload: Partial<WorkflowGraph>) =>
      request<WorkflowGraph>("/api/workflow-graphs", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    clone: (id: string, name?: string) =>
      request<WorkflowGraph>(`/api/workflow-graphs/${encodeURIComponent(id)}/clone`, {
        method: "POST",
        body: JSON.stringify({ name }),
      }),

    remove: (id: string) =>
      request<{ deleted: string }>(`/api/workflow-graphs/${id}`, { method: "DELETE" }),

    runStreamUrl: (id: string): string => {
      const base = API_BASE || (typeof window !== "undefined" ? window.location.origin : "http://localhost:3001");
      const url = new URL(`${base}/api/workflow-graphs/${id}/run`);
      return url.toString();
    },

    runStreamHeaders: (): Record<string, string> => {
      const t = _currentTenant;
      return {
        "Accept": "text/event-stream",
        "x-user-id": t.userId,
        "x-company-id": t.companyId,
        "x-project-id": t.projectId,
        "x-role": t.role,
      };
    },

    // v3.0 Run history
    listRuns: (graphId: string) =>
      request<{ graph_id: string; runs: WorkflowRun[] }>(`/api/workflow-graphs/${encodeURIComponent(graphId)}/runs`),

    getRun: (graphId: string, runId: string) =>
      request<WorkflowRun>(`/api/workflow-graphs/${encodeURIComponent(graphId)}/runs/${encodeURIComponent(runId)}`),
  },

  workflowTemplates: {
    list: () =>
      request<{ items: WorkflowTemplate[] }>("/api/workflow-templates"),

    get: (templateId: string) =>
      request<WorkflowTemplate>(`/api/workflow-templates/${encodeURIComponent(templateId)}`),

    clone: (templateId: string, payload?: { name?: string; default_mode?: "dry_run" | "post" }) =>
      request<WorkflowGraph>(`/api/workflow-templates/${encodeURIComponent(templateId)}/clone`, {
        method: "POST",
        body: JSON.stringify(payload ?? {}),
      }),
  },

  workflowOntologyMappings: {
    list: () =>
      request<{ items: WorkflowOntologyMapping[] }>("/api/workflow-ontology-mappings"),

    get: (mappingId: string) =>
      request<WorkflowOntologyMapping>(`/api/workflow-ontology-mappings/${encodeURIComponent(mappingId)}`),

    installSchema: (mappingId: string) =>
      request<WorkflowOntologyMappingInstallResult>(
        `/api/workflow-ontology-mappings/${encodeURIComponent(mappingId)}/install-schema`,
        { method: "POST" }
      ),
  },

  skills: {
    list: () =>
      request<{ builtinSkills: Skill[]; customSkills: Skill[]; total: number }>("/api/skills"),

    get: (skillId: string) =>
      request<Skill>(`/api/skills/${encodeURIComponent(skillId)}`),

    createCustom: (skill: Skill) =>
      request<{ skillId: string; created: boolean }>("/api/skills/custom", {
        method: "POST",
        body: JSON.stringify(skill),
      }),

    updateCustom: (skillId: string, skill: Skill) =>
      request<{ skillId: string; updated: boolean }>(`/api/skills/custom/${encodeURIComponent(skillId)}`, {
        method: "PUT",
        body: JSON.stringify(skill),
      }),

    deleteCustom: (skillId: string) =>
      request<{ skillId: string; deleted: boolean }>(`/api/skills/custom/${encodeURIComponent(skillId)}`, {
        method: "DELETE",
      }),
  },

  // ── Integration Test ─────────────────────────────────────────────────────

  integrationTest: {
    listProjects: () =>
      request<IntegrationTestProject[]>("/api/integration-test/projects"),

    run: (project: string) =>
      request<IntegrationTestRun>("/api/integration-test/run", {
        method: "POST",
        body: JSON.stringify({ project }),
      }),

    listRuns: (project: string) =>
      request<{ project: string; runs: IntegrationTestRunMeta[] }>(
        `/api/integration-test/${encodeURIComponent(project)}/runs`
      ),

    getRun: (project: string, runId: string) =>
      request<IntegrationTestRun>(
        `/api/integration-test/${encodeURIComponent(project)}/runs/${encodeURIComponent(runId)}`
      ),
  },

  // ── v3.0 Metrics ──────────────────────────────────────────────────────────

  metrics: {
    query: (limit = 200) =>
      request<{
        total_queries: number;
        llm_used_rate: number;
        fallback_rate: number;
        by_intent: Record<string, number>;
        vector_hits_avg: number;
        ontology_hits_avg: number;
      }>(`/api/metrics/query?limit=${limit}`),
  },

  // ── Monitoring (v5) ────────────────────────────────────────────────────────

  monitoring: {
    health: () => request<any>("/api/v5/monitoring/health"),
    topQueries: (limit = 10) => request<any>(`/api/v5/monitoring/queries/top?limit=${limit}`),
    searchStats: () => request<any>("/api/v5/monitoring/search/stats"),
    recentErrors: (limit = 10) => request<any>(`/api/v5/monitoring/errors/recent?limit=${limit}`),
    throughput: (window = 5) => request<any>(`/api/v5/monitoring/throughput?window_minutes=${window}`),
  },

  // ── Backup (v5) ────────────────────────────────────────────────────────────

  backup: {
    list: () => request<any[]>("/api/v5/backup/list"),
    create: () => request<{ success: boolean; message: string; filename?: string }>("/api/v5/backup/create", { method: "POST" }),
    restore: (filename: string) => request<{ success: boolean; message: string }>(`/api/v5/backup/restore/${encodeURIComponent(filename)}`, { method: "POST" }),
  },

  // ── Encore PoC (v5) ────────────────────────────────────────────────────────

  poc: {
    task5: {
      bomMatching: (payload: any) => request<any>("/api/poc/task5/bom-matching", { method: "POST", body: JSON.stringify(payload) }),
      getMaterial: (materialId: string) => request<any>(`/api/poc/task5/materials/${encodeURIComponent(materialId)}`),
    },
    task6: {
      generateReport: (payload: any) => request<any>("/api/poc/task6/generate-report", { method: "POST", body: JSON.stringify(payload) }),
      getTemplates: () => request<any>("/api/poc/task6/templates"),
    },
    task9: {
      searchDocuments: (payload: any) => request<any>("/api/poc/task9/search-documents", { method: "POST", body: JSON.stringify(payload) }),
      ragQuery: (payload: any) => request<any>("/api/poc/task9/rag-query", { method: "POST", body: JSON.stringify(payload) }),
    },
    ontology: {
      extractPipeline: (payload: any) => request<any>("/api/poc/ontology/extract", { method: "POST", body: JSON.stringify(payload) }),
    }
  },

  // ── Projects (Week 4 Dashboard) ───────────────────────────────────────

  projects: {
    list: () => request<{ projects: any[] }>("/api/v1/projects"),

    get: (projectId: string) =>
      request<any>(`/api/v1/projects/${encodeURIComponent(projectId)}`),

    create: (name: string, description: string) =>
      request<any>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify({ project_name: name, description }),
      }),
  },

  // ── ActionDefinition (Phase 3 Mock) ──────────────────────────────────────

  actions: {
    getAvailable: async (entityId: string, entityType: string) => {
      // Mocked response for Phase 3 UI development
      console.log("Mock getAvailable", entityId, entityType);
      return {
        actions: ["APPROVE", "REJECT", "CHANGE_DEADLINE", "REQUEST_INFO", "PROCESS_PAYMENT", "COMPLETE"]
      };
    },

    execute: async (actionName: string, payload: any) => {
      // Mocked response for Phase 3 UI development
      console.log("Mock execute", actionName, payload);
      await new Promise((resolve) => setTimeout(resolve, 800)); // simulate network delay
      return {
        status: "success",
        result: {
          action: actionName,
          payload,
          executedAt: new Date().toISOString()
        }
      };
    },
  },
};
