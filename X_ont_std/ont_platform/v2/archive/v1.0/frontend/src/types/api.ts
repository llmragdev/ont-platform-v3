export type UserRole = "Admin" | "FinanceManager" | "AccountManager" | "Analyst" | "Viewer";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  regions: string[];
  key?: string;
}

export interface Customer {
  id: string;
  type: "Customer";
  name: string;
  segment: string;
  region: string;
  risk_tier: string;
  contract_terms?: string;
  owner?: string;
}

export interface Product {
  id: string;
  type: "Product";
  name: string;
  category: string;
  unit_price: number;
}

export interface Order {
  id: string;
  type: "Order";
  customer_id: string;
  order_date: string;
  status: "Submitted" | "Review" | "Approved" | "Rejected" | "Fulfilled" | "Closed";
  amount: number;
  product_ids: string[];
}

export interface OrderContext {
  order: Order;
  customer: Customer;
  products: Product[];
  available_actions: string[];
}

export interface Evidence {
  document_id: string;
  title: string;
  score: number;
  text: string;
  related_objects: string[];
}

export interface AskResponse {
  answer: string;
  llm_provider: "gemini" | "rule-based";
  llm_model: string;
  warning?: string;
  detected_objects: string[];
  ontology_context: { customer_id: string; order_id: string };
  context: { order: Order; customer: Customer; products: Product[] };
  evidence: Evidence[];
  available_actions: string[];
  prompt: string;
  steps: { name: string; status: string }[];
  latency_ms: number;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  actor: string;
  object_type: string;
  object_id: string;
  detail: Record<string, unknown>;
  occurred_at: string;
}

export interface WorkflowQueueRow extends Order {
  customer: Customer;
  available_actions: string[];
}

export interface ApiError {
  error: { code: string; message: string };
}

// --- RAG Ask ---
export interface RagAskResponse {
  answer: string;
  llm_provider: string;
  llm_model: string;
  warning?: string;
  evidence: Evidence[];
  steps: { name: string; status: string }[];
  latency_ms: number;
}

// --- Documents (RAG) ---
export interface DocumentInfo {
  doc_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  file_path?: string;
}

// --- Ontology Graph (Phase 3/4) ---
export interface OntologyNodeData {
  label: string;
  object_type: string;
  icon?: string;
  [key: string]: unknown;
}

export interface OntologyGraphNode {
  id: string;
  type: "ontology";
  position: { x: number; y: number };
  data: OntologyNodeData;
}

export interface OntologyGraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  data?: { relationship_type: string; values?: Record<string, unknown> };
}

export interface OntologyGraph {
  nodes: OntologyGraphNode[];
  edges: OntologyGraphEdge[];
}

export interface OntologySchemaProperty {
  name: string;
  type: string;
  required?: boolean;
  sensitive?: boolean;
  searchable?: boolean;
  enum_values?: string[];
}

export interface OntologySchemaObjectType {
  name: string;
  display_name?: string;
  id_prefix?: string;
  icon?: string;
  properties: OntologySchemaProperty[];
}

export interface OntologySchemaRelType {
  name: string;
  display_name?: string;
  reverse_display_name?: string;
  source_type: string;
  target_type: string;
  cardinality?: string;
}

export interface OntologySchema {
  object_types: OntologySchemaObjectType[];
  relationship_types: OntologySchemaRelType[];
  action_types?: { name: string; node_type_key?: string; exposed_as_graph_node?: boolean }[];
}

// --- WorkflowGraph (Phase 1 + WG-3 도메인 노드) ---
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
  prompt?: string;       // llm
  url?: string;          // http
  method?: string;       // http
  expression?: string;   // condition
  order_id?: string;     // approve_order
  customer_id?: string;  // risk_assess
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

export interface WorkflowRun {
  run_id: string;
  graph_id: string;
  status: "running" | "completed" | "failed";
  started_at: string;
  finished_at: string | null;
  triggered_by: string;
  step_count: number;
  completed_count: number;
}

// ── 하이브리드 질의 ───────────────────────────────────────────────────────────

export type HybridQueryType = "descriptive" | "filter" | "compare" | "calculate" | "hybrid";

export interface HybridClassification {
  type: HybridQueryType;
  entities: string[];
  operation: string;
  property_key: string | null;
  property_value: string | null;
  entity_type: string | null;
}

export interface HybridOntologyResult {
  mode: "filter" | "compare" | "calculate" | "relations" | "none";
  entity_type?: string;
  property_key?: string;
  property_value?: string;
  rows?: Record<string, unknown>[];
  table?: {
    headers: string[];
    rows: { id: string; name: string; type: string; props: Record<string, unknown> }[];
  };
  calc?: {
    operation: string;
    result: number | null;
    unit: string;
    operands: { name: string; value: number; unit: string }[];
    error?: string;
  };
}

export interface HybridAskResponse {
  answer: string;
  llm_provider: string;
  llm_model: string;
  warning?: string;
  query_type: HybridQueryType;
  classification: HybridClassification;
  ontology_result: HybridOntologyResult;
  evidence: Evidence[];
  steps: { name: string; status: string }[];
  latency_ms: number;
}

// ── 온톨로지 관리 (mgmt) ─────────────────────────────────────────────────────

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

export interface OntologyDocInfo {
  doc_id: string;
  filename: string;
  entity_count: number;
  relation_count: number;
}

export interface OntologyMgmtGraph {
  nodes: { id: string; label: string; type: string; properties: Record<string, unknown> }[];
  edges: { id: string; from: string; to: string; label: string }[];
}

export interface WorkflowRunStep {
  run_id: string;
  node_id: string;
  step_index: number;
  type: string;
  label: string;
  status: "running" | "success" | "error" | "skipped";
  started_at: string;
  finished_at: string;
  duration_ms: number;
  output: unknown;
  error: string | null;
}
