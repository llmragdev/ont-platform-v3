export const DEFAULT_TENANT = {
  userId: "demo-user",
  companyId: "demo-co",
  projectId: "proj-01",
  role: "FinanceManager",
} as const;

export type TenantConfig = typeof DEFAULT_TENANT;

export type BackendEntity = {
  id: string;
  name: string;
  type: string;
  status?: string;
  properties?: Record<string, unknown>;
};

export type WorkflowQueueItem = BackendEntity & {
  available_actions: string[];
  doc_id: string;
  status: string;
};

export type OntologyDoc = {
  doc_id: string;
  entity_count: number;
  relationship_count: number;
};

export type AiQueryResult = {
  query_type: string;
  classification?: Record<string, unknown>;
  results?: BackendEntity[];
  count?: number;
  answer?: string;
};

function h(cfg: TenantConfig): HeadersInit {
  return {
    "Content-Type": "application/json",
    "x-user-id": cfg.userId,
    "x-company-id": cfg.companyId,
    "x-project-id": cfg.projectId,
    "x-role": cfg.role,
  };
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch("/api/health", {
      signal: AbortSignal.timeout(3000),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchWorkflowQueue(
  cfg: TenantConfig,
): Promise<WorkflowQueueItem[]> {
  const res = await fetch("/api/workflow/queue", { headers: h(cfg) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.items ?? [];
}

export async function executeWorkflowAction(
  cfg: TenantConfig,
  docId: string,
  entityId: string,
  action: string,
): Promise<BackendEntity> {
  const res = await fetch("/api/workflow/execute", {
    method: "POST",
    headers: h(cfg),
    body: JSON.stringify({ doc_id: docId, entity_id: entityId, action }),
  });
  if (!res.ok) {
    const err = await res
      .json()
      .catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export async function hybridAsk(
  cfg: TenantConfig,
  question: string,
): Promise<AiQueryResult> {
  const res = await fetch("/api/hybrid/ask", {
    method: "POST",
    headers: h(cfg),
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchOntologyDocs(
  cfg: TenantConfig,
): Promise<OntologyDoc[]> {
  const res = await fetch("/api/ontology", { headers: h(cfg) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchEntities(
  cfg: TenantConfig,
  docId: string,
): Promise<BackendEntity[]> {
  const res = await fetch(`/api/ontology/${docId}/entities`, {
    headers: h(cfg),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function createEntity(
  cfg: TenantConfig,
  docId: string,
  entity: Omit<BackendEntity, "id">,
): Promise<BackendEntity> {
  const res = await fetch(`/api/ontology/${docId}/entities`, {
    method: "POST",
    headers: h(cfg),
    body: JSON.stringify(entity),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

const DEMO_DOC_ID = "demo-orders";

export async function seedDemoData(cfg: TenantConfig): Promise<void> {
  const entities = [
    {
      name: "Order O001",
      type: "Order",
      status: "Submitted",
      properties: { customerId: "C001", amount: 3200 },
    },
    {
      name: "Order O002",
      type: "Order",
      status: "Submitted",
      properties: { customerId: "C002", amount: 8200 },
    },
    {
      name: "Order O003",
      type: "Order",
      status: "Approved",
      properties: { customerId: "C001", amount: 1500 },
    },
  ];
  for (const entity of entities) {
    await createEntity(cfg, DEMO_DOC_ID, entity);
  }
}
