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
  WorkflowGraph,
  WorkflowQueueRow,
  WorkflowRun,
} from "@/types/api";

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
    const code = (err?.code ?? "UNKNOWN") as string;
    const message = (err?.message ?? data?.detail ?? text ?? response.statusText) as string;
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

  // ── Audit ──────────────────────────────────────────────────────────────────

  auditEvents: (limit = 200) =>
    request<{ events: AuditEvent[] }>(`/api/audit/events?limit=${limit}`),

  // ── Documents ─────────────────────────────────────────────────────────────

  documents: {
    list: () =>
      request<{ documents: DocumentInfo[] }>("/api/documents"),

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
        const nodes = (raw.nodes ?? []).map((n: { id: string; data?: { label?: string; object_type?: string; [k: string]: unknown }; [k: string]: unknown }) => ({
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
  },

  // ── Hybrid Ask ────────────────────────────────────────────────────────────

  hybridAsk: (question: string, docIds?: string[]) =>
    request<HybridAskResponse>("/api/hybrid/ask", {
      method: "POST",
      body: JSON.stringify({ question, doc_ids: docIds ?? null }),
    }),

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
};
