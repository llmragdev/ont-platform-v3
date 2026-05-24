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

// ── v3.0 Provenance ──────────────────────────────────────────────────────────

export interface OntologyProvenance {
  source_doc_id?: string | null;
  source_page?: number | null;
  source_chunk_id?: string | null;
  source_text?: string | null;
  confidence: number;
  extracted_by?: string | null;
}

export interface OntologyEntity {
  id: string;
  type: string;
  name: string;
  properties: Record<string, unknown>;
  // v3.0 fields (all optional for backward compat)
  provenance?: OntologyProvenance | null;
  status?: "active" | "review" | "deprecated";
  version?: number;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
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

// ── v3.0 Quality Metrics ─────────────────────────────────────────────────────

export interface QualityMetrics {
  llm_used: boolean;
  fallback_used: boolean;
  vector_hits: number;
  ontology_hits: number;
  latency_ms?: number;
}

export interface OntologyEvidence {
  node_id: string;
  node_type: string;
  label: string;
  source_doc_id?: string | null;
  source_page?: number | null;
  confidence: number;
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
  // v3.0 new fields
  ontology_evidence?: OntologyEvidence[];
  quality_metrics?: QualityMetrics;
  llm_provider?: string;
  llm_model?: string;
  warning?: string;
  latency_ms?: number;
}

// ── SPARQL Workbench ─────────────────────────────────────────────────────────

export interface SparqlBindingValue {
  type?: "uri" | "literal" | "bnode" | string;
  value: string | null;
  datatype?: string;
  lang?: string;
}

export interface SparqlQueryResponse {
  type?: "SELECT" | "ASK" | "CONSTRUCT" | "DESCRIBE" | string;
  query_type?: "SELECT" | "ASK" | "CONSTRUCT" | "DESCRIBE" | string;
  head?: { vars?: string[] };
  select_vars?: string[];
  patterns?: number;
  pattern_ids?: Array<number | string>;
  results?: Array<Record<string, SparqlBindingValue | string | number | boolean | null>>;
  bindings?: Array<Record<string, SparqlBindingValue>>;
  triples?: Array<{ subject: string; predicate: string; object: string }>;
  boolean?: boolean;
  count?: number;
  result_count?: number;
  query_time_ms?: number;
  execution_time_ms?: number;
  translator_used?: boolean;
  sql_generated?: string;
  explain?: string;
  error?: string | { code?: string; message: string; type?: string | null };
  warning?: string;
  warnings?: string[];
  cache_hit?: boolean;
  source?: "sql_translator" | "rdflib" | "demo" | "error";
  entity_id?: string;
  entity_type?: string;
  current_status?: string;
  available_actions?: Array<{
    name: string;
    display: string;
    required_params: string[];
  }>;
  answer?: string;
  quality_metrics?: {
    relevance?: number;
    completeness?: number;
    [key: string]: unknown;
  };
}

export interface SparqlHistoryItem {
  id: string;
  query: string;
  timestamp: string;
  durationMs: number;
  rowCount: number;
  status: "success" | "error";
  queryType: string;
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

// ── Integration Test ─────────────────────────────────────────────────────────

export type IntegrationTestSource = "ontology" | "vector" | "hybrid" | "no_evidence";

export interface IntegrationTestEvidence {
  type: "ontology" | "vector";
  entity?: string;
  entity_type?: string;
  doc_id?: string;
  score?: number;
  text?: string;
}

export interface IntegrationTestCase {
  id: string;
  tags: string[];
  question: string;
  expected_source: IntegrationTestSource;
  expected_keywords: string[];
  match_mode: "any" | "all";
  actual_source: IntegrationTestSource;
  actual_answer: string;
  ontology_hits: number;
  vector_hits: number;
  llm_used: boolean;
  source_matched: boolean;
  keyword_matched: boolean;
  passed: boolean;
  evidence: IntegrationTestEvidence[];
  duration_ms: number;
  note: string;
}

export interface IntegrationTestBySourceStat {
  total: number;
  passed: number;
}

export interface IntegrationTestSummary {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  duration_sec: number;
  by_source: Record<string, IntegrationTestBySourceStat>;
}

export interface IntegrationTestRun {
  run_id: string;
  project: string;
  timestamp: string;
  summary: IntegrationTestSummary;
  cases: IntegrationTestCase[];
}

export interface IntegrationTestRunMeta {
  run_id: string;
  timestamp: string;
  total: number;
  passed: number;
  pass_rate: number;
  duration_sec: number;
}

export interface IntegrationTestProject {
  project: string;
  run_count: number;
  last_run: string | null;
  last_pass_rate: number | null;
}

// ── v3.0 WorkflowRun ─────────────────────────────────────────────────────────

export type StepStatusType = "pending" | "running" | "succeeded" | "failed" | "skipped" | "waiting_approval";

export interface WorkflowStepRun {
  step_id: string;
  node_id: string;
  node_type: string;
  status: StepStatusType;
  started_at?: string | null;
  finished_at?: string | null;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error?: string | null;
}

export interface WorkflowRun {
  run_id: string;
  graph_id: string;
  status: StepStatusType;
  triggered_by: string;
  started_at: string;
  finished_at?: string | null;
  steps: WorkflowStepRun[];
  user_trace: string[];
  tech_trace: string[];
}
