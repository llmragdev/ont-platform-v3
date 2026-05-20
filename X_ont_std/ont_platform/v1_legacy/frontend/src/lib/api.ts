import type {
  AskResponse,
  AuditEvent,
  Customer,
  DocumentInfo,
  HybridAskResponse,
  OntologyDocInfo,
  OntologyEntity,
  OntologyMgmtEntityType,
  OntologyMgmtGraph,
  OntologyMgmtRelationType,
  OntologyMgmtSchema,
  OntologyGraph,
  OntologyRelationship,
  OntologySchema,
  Order,
  OrderContext,
  RagAskResponse,
  User,
  WorkflowGraph,
  WorkflowQueueRow,
  WorkflowRun,
  WorkflowRunStep,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("claud_token");
}

async function request<T>(path: string, init: RequestInit & { user?: string } = {}): Promise<T> {
  const { user, ...rest } = init;
  const url = new URL(`${API_BASE}${path}`);
  // 하위호환: JWT가 없으면 ?user= 쿼리, 있으면 Authorization 헤더가 우선됨
  if (user) url.searchParams.set("user", user);
  const token = readToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json; charset=utf-8",
    ...((rest.headers as Record<string, string>) ?? {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const response = await fetch(url.toString(), {
    ...rest,
    headers,
    cache: "no-store",
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const code = data?.error?.code ?? "UNKNOWN";
    const message = data?.error?.message ?? data?.detail ?? response.statusText;
    throw new ApiClientError(code, message, response.status);
  }
  return data as T;
}

export class ApiClientError extends Error {
  constructor(public code: string, message: string, public status: number) {
    super(message);
  }
}

export const api = {
  health: () => request<{ status: string; llm_provider: string; llm_model: string }>("/api/health"),
  users: () => request<{ users: User[] }>("/api/users"),
  me: (user: string) => request<User>("/api/me", { user }),
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string; user: User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  customers: (user: string) => request<{ customers: Customer[] }>("/api/objects/customers", { user }),
  orders: (user: string) => request<{ orders: Order[] }>("/api/objects/orders", { user }),
  orderContext: (user: string, orderId: string, customerId?: string) => {
    const query = customerId ? `?customer_id=${encodeURIComponent(customerId)}` : "";
    return request<OrderContext>(`/api/objects/orders/${orderId}/context${query}`, { user });
  },
  ask: (user: string, question: string) =>
    request<AskResponse>("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
      user,
    }),
  workflowQueue: (user: string) => request<{ queue: WorkflowQueueRow[] }>("/api/workflow/queue", { user }),
  workflowExecute: (user: string, orderId: string, action: string) =>
    request<{ result: { to_status: string }; queue: WorkflowQueueRow[] }>("/api/workflow/execute", {
      method: "POST",
      body: JSON.stringify({ order_id: orderId, action }),
      user,
    }),
  auditEvents: () => request<{ events: AuditEvent[] }>("/api/audit/events"),

  // Ontology (Phase 3/4)
  ontology: {
    schema: () => request<OntologySchema>("/api/ontology/schema"),
    graph: () => request<OntologyGraph>("/api/ontology/graph"),
    createRelationship: (body: { relationship_type: string; source_id: string; target_id: string; values?: Record<string, unknown> }) =>
      request<{ status: string; rel_id: string }>("/api/ontology/relationships", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    deleteRelationship: (relId: string) =>
      request<{ status: string; rel_id: string }>(`/api/ontology/relationships/${relId}`, {
        method: "DELETE",
      }),
  },

  // Hybrid 질의 (온톨로지 + RAG)
  hybridAsk: (user: string, question: string, docIds?: string[]) =>
    request<HybridAskResponse>("/api/hybrid/ask", {
      method: "POST",
      body: JSON.stringify({ question, doc_ids: docIds ?? null }),
      user,
    }),

  // RAG 전용 질의 (온톨로지 컨텍스트 불필요)
  ragAsk: (user: string, question: string) =>
    request<RagAskResponse>("/api/rag/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
      user,
    }),

  // Documents (RAG)
  documents: {
    list: (user: string) =>
      request<{ documents: DocumentInfo[]; vector_search: { available: boolean; document_count: number } }>(
        "/api/documents",
        { user }
      ),
    upload: async (user: string, file: File): Promise<DocumentInfo & { status: string }> => {
      const url = new URL(`${API_BASE}/api/documents/upload`);
      if (user) url.searchParams.set("user", user);
      const token = readToken();
      const form = new FormData();
      form.append("file", file);
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(url.toString(), { method: "POST", body: form, headers, cache: "no-store" });
      const data = await res.json();
      if (!res.ok) throw new ApiClientError(data?.error?.code ?? "UPLOAD_ERROR", data?.error?.message ?? res.statusText, res.status);
      return data;
    },
    remove: (user: string, docId: string) =>
      request<{ status: string; doc_id: string }>(`/api/documents/${docId}`, { method: "DELETE", user }),
  },

  // Ontology Management (새 mgmt 엔드포인트)
  ontologyMgmt: {
    listDocs: () => request<{ ontologies: OntologyDocInfo[] }>("/api/ontology"),
    getSchema: () => request<OntologyMgmtSchema>("/api/ontology/mgmt/schema"),
    addEntityType: (body: { name: string; description: string; properties: string[] }, user?: string) =>
      request<OntologyMgmtEntityType>("/api/ontology/mgmt/schema/entity-types", {
        method: "POST", body: JSON.stringify(body), user,
      }),
    deleteEntityType: (name: string, user?: string) =>
      request<{ status: string; name: string }>(`/api/ontology/mgmt/schema/entity-types/${encodeURIComponent(name)}`, {
        method: "DELETE", user,
      }),
    addRelationType: (body: { name: string; from_type: string; to_type: string }, user?: string) =>
      request<OntologyMgmtRelationType>("/api/ontology/mgmt/schema/relation-types", {
        method: "POST", body: JSON.stringify(body), user,
      }),
    deleteRelationType: (name: string, user?: string) =>
      request<{ status: string; name: string }>(`/api/ontology/mgmt/schema/relation-types/${encodeURIComponent(name)}`, {
        method: "DELETE", user,
      }),
    listEntities: (docId: string, params?: { entity_type?: string; page?: number; size?: number }) => {
      const qs = new URLSearchParams();
      if (params?.entity_type) qs.set("entity_type", params.entity_type);
      if (params?.page) qs.set("page", String(params.page));
      if (params?.size) qs.set("size", String(params.size));
      const q = qs.toString();
      return request<{ entities: OntologyEntity[]; total: number; page: number }>(
        `/api/ontology/${encodeURIComponent(docId)}/entities${q ? "?" + q : ""}`
      );
    },
    createEntity: (docId: string, body: { type: string; name: string; properties: Record<string, unknown> }, user?: string) =>
      request<OntologyEntity>(`/api/ontology/${encodeURIComponent(docId)}/entities`, {
        method: "POST", body: JSON.stringify(body), user,
      }),
    updateEntity: (docId: string, entityId: string, body: { name?: string; properties?: Record<string, unknown> }, user?: string) =>
      request<OntologyEntity>(`/api/ontology/${encodeURIComponent(docId)}/entities/${encodeURIComponent(entityId)}`, {
        method: "PUT", body: JSON.stringify(body), user,
      }),
    deleteEntity: (docId: string, entityId: string, user?: string) =>
      request<{ status: string; entity_id: string }>(`/api/ontology/${encodeURIComponent(docId)}/entities/${encodeURIComponent(entityId)}`, {
        method: "DELETE", user,
      }),
    listRelationships: (docId: string) =>
      request<{ relationships: OntologyRelationship[] }>(`/api/ontology/${encodeURIComponent(docId)}/relationships`),
    addRelationship: (docId: string, body: { from_id: string; relation: string; to_id: string }, user?: string) =>
      request<OntologyRelationship>(`/api/ontology/${encodeURIComponent(docId)}/relationships`, {
        method: "POST", body: JSON.stringify(body), user,
      }),
    deleteRelationship: (docId: string, relId: string, user?: string) =>
      request<{ status: string; rel_id: string }>(`/api/ontology/${encodeURIComponent(docId)}/relationships/${encodeURIComponent(relId)}`, {
        method: "DELETE", user,
      }),
    getGraph: (docId: string) =>
      request<OntologyMgmtGraph>(`/api/ontology/${encodeURIComponent(docId)}/graph`),
    extractOntology: (docId: string, user?: string) =>
      request<{ status: string; doc_id: string; entity_count: number; relation_count: number }>(
        "/api/documents/extract-ontology", { method: "POST", body: JSON.stringify({ doc_id: docId }), user }
      ),
  },

  // WorkflowGraph (Phase 1 + 2)
  workflowGraphs: {
    list: (user: string) =>
      request<{ graphs: WorkflowGraph[] }>("/api/workflow-graphs", { user }),
    get: (user: string, id: string) =>
      request<WorkflowGraph>(`/api/workflow-graphs/${id}`, { user }),
    save: (user: string, payload: Partial<WorkflowGraph>) =>
      request<WorkflowGraph>("/api/workflow-graphs", {
        method: "POST",
        body: JSON.stringify(payload),
        user,
      }),
    remove: (user: string, id: string) =>
      request<{ status: string; id: string }>(`/api/workflow-graphs/${id}`, {
        method: "DELETE",
        user,
      }),
    runStreamUrl: (user: string, id: string) => {
      const url = new URL(`${API_BASE}/api/workflow-graphs/${id}/run`);
      if (user) url.searchParams.set("user", user);
      return url.toString();
    },
    listRuns: (user: string, id: string) =>
      request<{ runs: WorkflowRun[] }>(`/api/workflow-graphs/${id}/runs`, { user }),
    getRun: (user: string, runId: string) =>
      request<{ run: WorkflowRun; steps: WorkflowRunStep[] }>(
        `/api/workflow-runs/${runId}`,
        { user }
      ),
  },
};
