const BASE_URL = "http://localhost:8003";

export const DEFAULT_TENANT = {
  userId: "demo-user",
  companyId: "acme",
  projectId: "proj-001",
  role: "FinanceManager",
} as const;

export type TenantConfig = typeof DEFAULT_TENANT;

export type OntologyProvenance = {
  source_kind: string;
  doc_id?: string;
  page_no?: number;
  confidence: number;
  created_by?: string;
  created_at?: string;
};

export type BackendEntity = {
  id: string;
  name: string;
  type: string;
  status: string;
  values?: Record<string, any>;
  provenance?: OntologyProvenance;
};

export type WorkflowQueueItem = BackendEntity & {
  available_actions: string[];
};

function h(cfg: TenantConfig): HeadersInit {
  return {
    "Content-Type": "application/json",
    "x-tenant-id": cfg.companyId,
    "x-user-id": cfg.userId,
    "x-role": cfg.role,
  };
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/health`, {
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
  // Use the v1 objects endpoint as a queue
  const res = await fetch(`${BASE_URL}/api/v1/ontology/objects?include_disabled=true`, { headers: h(cfg) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const objects = data.objects ?? [];
  
  // Map to include available_actions based on type/status
  return objects.map((obj: any) => ({
    ...obj,
    name: obj.values?.name || obj.values?.order_no || obj.id,
    available_actions: obj.type === "Order" ? ["APPROVE_ORDER", "CHANGE_WC_DATE"] : []
  }));
}

export async function executeWorkflowAction(
  cfg: TenantConfig,
  action: string,
  targetId: string,
  params: Record<string, any> = {}
): Promise<any> {
  const url = `${BASE_URL}/api/v1/ontology/actions/execute?action_name=${action}&target_id=${targetId}`;
  const res = await fetch(url, {
    method: "POST",
    headers: h(cfg),
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: `HTTP ${res.status}` } }));
    throw new Error(err.error?.message || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function hybridAsk(
  cfg: TenantConfig,
  question: string,
): Promise<any> {
  const res = await fetch(`${BASE_URL}/api/hybrid/ask`, {
    method: "POST",
    headers: h(cfg),
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
