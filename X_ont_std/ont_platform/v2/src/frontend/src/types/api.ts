export type UserRole = "Admin" | "FinanceManager" | "AccountManager" | "Analyst" | "Viewer";

export interface TenantConfig {
  userId: string;
  companyId: string;
  projectId: string;
  role: UserRole;
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  company_id: string;
  project_id: string;
  user_id: string;
  role: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
}

// ── Workflow ────────────────────────────────────────────────────────────────

export interface WorkflowQueueRow {
  entity_id: string;
  entity_type: string;
  name: string;
  status: string;
  available_actions: string[];
  doc_id: string;
}

// ── Ontology ────────────────────────────────────────────────────────────────

export interface OntologyDocInfo {
  doc_id: string;
  filename: string;
  entity_count: number;
  relation_count: number;
}

export interface OntologyEntity {
  id: string;
  type: string;
  name: string;
  properties: Record<string, unknown>;
}

export interface OntologyRelationship {
  id: string;
  from_id: string;
  relation: string;
  to_id: string;
}

export interface OntologyMgmtEntityType {
  name: string;
  description: string;
  is_builtin: boolean;
  properties: string[];
}

export interface OntologyMgmtRelationType {
  name: string;
  from_type: string;
  to_type: string;
}

export interface OntologyMgmtSchema {
  entity_types: OntologyMgmtEntityType[];
  relation_types: OntologyMgmtRelationType[];
}

export interface OntologyMgmtGraph {
  nodes: { id: string; label: string; type: string; properties: Record<string, unknown> }[];
  edges: { id: string; from: string; to: string; label: string }[];
}

// ── Documents ────────────────────────────────────────────────────────────────

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
}

// ── Hybrid Ask ───────────────────────────────────────────────────────────────

export type HybridQueryType = "descriptive" | "filter" | "compare" | "calculate" | "hybrid";

export interface HybridAskResponse {
  intent: string;
  query_type: HybridQueryType;
  answer: string;
  sources: Array<{ source_type: string; id?: string; name?: string; type?: string; citation?: string; [key: string]: unknown }>;
  evidence: Array<{ citation: string; [key: string]: unknown }>;
  structured_data: {
    ontology?: { count: number; items: unknown[] };
    vector?: { count: number; items: unknown[] };
    [key: string]: unknown;
  };
  trace: string[];
  results?: Array<{ id: string; name?: string; type?: string }>;
  count?: number;
  llm_provider?: string;
  llm_model?: string;
  warning?: string;
  latency_ms?: number;
}

// ── WorkflowGraph ────────────────────────────────────────────────────────────

export type GraphNodeKind =
  | "start"
  | "end"
  | "llm"
  | "http"
  | "condition"
  | "approve_order"
  | "risk_assess";

export interface GraphNodeData {
  label?: string;
  prompt?: string;
  url?: string;
  method?: string;
  expression?: string;
  order_id?: string;
  customer_id?: string;
  status?: "idle" | "running" | "success" | "error" | "skipped";
  result?: unknown;
}

export interface GraphNode {
  id: string;
  type: GraphNodeKind;
  position: { x: number; y: number };
  data?: GraphNodeData;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export interface WorkflowGraph {
  id: string;
  name: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  created_at: string;
  updated_at: string;
  created_by: string;
}
