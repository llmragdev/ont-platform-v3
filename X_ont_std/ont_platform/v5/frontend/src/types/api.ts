export type UserRole = "Admin" | "FinanceManager" | "AccountManager" | "Analyst" | "Viewer";

export interface TenantConfig {
  userId: string;
  companyId: string;
  projectId: string;
  role: UserRole;
}

// ── Platform AI Assistant ───────────────────────────────────────────────────

export type AssistantIntent =
  | "explain_current_view"
  | "generate_ontology_query"
  | "create_app"
  | "edit_streamlit_program"
  | "analyze_failure"
  | "suggest_workflow_change"
  | "general_help";

export interface AssistantContext {
  current_view?: string | null;
  view_title?: string | null;
  company_id?: string | null;
  project_id?: string | null;
  user_id?: string | null;
  role?: string | null;
  selected_object_id?: string | null;
  selected_workflow_id?: string | null;
  selected_workflow_name?: string | null;
  selected_node_id?: string | null;
  selected_node_label?: string | null;
  selected_app_id?: string | null;
  selected_app_name?: string | null;
  selected_folder_id?: string | null;
  selected_folder_name?: string | null;
  selected_file_path?: string | null;
  selected_file_name?: string | null;
  selected_language?: string | null;
}

export interface GeneratedQuery {
  query_id: string;
  language: "SPARQL" | "SQL" | "ONTOLOGY";
  title: string;
  description: string;
  query: string;
  safe_to_execute: boolean;
  warnings: string[];
}

export interface AppWidgetSpec {
  type: "metric" | "table" | "chart" | "graph" | "text";
  title: string;
  query_id?: string | null;
  description?: string | null;
}

export interface AppSpecPreview {
  app_id: string;
  title: string;
  description: string;
  layout: AppWidgetSpec[];
}

export interface AssistantAction {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}

export interface AssistantChatRequest {
  message: string;
  context: AssistantContext;
}

export interface AssistantChatResponse {
  conversation_id: string;
  created_at: string;
  intent: AssistantIntent;
  summary: string;
  answer: string;
  generated_queries: GeneratedQuery[];
  app_spec_preview?: AppSpecPreview | null;
  suggested_actions: AssistantAction[];
  trace: string[];
  context_used: AssistantContext;
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
  | "risk_assess"
  | "request_input"
  | "request_register"
  | "intent_classify"
  | "equipment_map"
  | "recurrence_check"
  | "precondition_check"
  | "artifact_change_check"
  | "knowledge_lookup"
  | "policy_search"
  | "evidence_gate"
  | "approval_check"
  | "action_plan"
  | "draft_response"
  | "human_handoff"
  | "validate_response"
  | "complete_request"
  | "notify_user"
  | "customer_mcp_comment_create"
  | "maintenance_task"
  | "quality_link"
  | "ontology_write"
  | "end_pending"
  | "end_failed"
  | "skill"
  | "custom_code";

export interface GraphNodeData {
  label?: string;
  prompt?: string;
  url?: string;
  method?: string;
  expression?: string;
  api?: string;
  mode?: "dry_run" | "post";
  source?: string;
  order_id?: string;
  customer_id?: string;
  status?: "idle" | "running" | "success" | "error" | "skipped";
  result?: unknown;
  // Skill 필드
  skillId?: string;
  skillVersion?: string;
  skillConfig?: {
    inputMapping?: Record<string, string>;
    outputMapping?: Record<string, string>;
    parameters?: Record<string, unknown>;
  };
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
  scenario_id?: string;
  scenario_version?: string;
  template_id?: string;
  template_version?: string;
  graph_kind?: "system_template" | "scenario" | "custom" | "template_copy";
  execution_mode?: "simulation" | "batch" | "manual_event" | "webhook";
  runtime?: {
    executor?: string;
    default_mode?: "dry_run" | "post";
    allow_post?: boolean;
    batch_status?: string;
    batch_limit?: number;
  };
  tenant_scope?: {
    company_id: string;
    project_id: string;
  };
  source?: {
    type?: "system_template" | "project_graph";
    source_graph_id?: string | null;
    cloned_from?: string | null;
    template_id?: string | null;
  };
  nodes: GraphNode[];
  edges: GraphEdge[];
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface WorkflowTemplate {
  template_id: string;
  template_version: string;
  name: string;
  category?: string;
  summary?: string;
  scenario_id?: string;
  scenario_version?: string;
  graph_kind?: string;
  execution_mode?: string;
  runtime?: WorkflowGraph["runtime"];
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface WorkflowGraphRunOptions {
  execution_mode?: "simulation" | "batch" | "manual_event" | "webhook";
  mode?: "dry_run" | "post";
  status?: string;
  limit?: number;
  force_reprocess?: boolean;
}

export interface WorkflowOntologyMapping {
  mapping_id: string;
  mapping_version?: string;
  name: string;
  summary?: string;
  scenario_id?: string;
  workflow_template_id?: string;
  workflow_executor?: string;
  ontology_document?: { doc_id: string; domain?: string };
  entity_types?: Array<{ name: string; label?: string; description?: string; properties?: string[] }>;
  relation_types?: Array<{ name: string; label?: string; from_type?: string; to_type?: string; description?: string }>;
  workflow_node_mappings?: Array<{ node_id: string; node_label?: string; creates_or_updates?: string; key?: string; field_map?: Record<string, string> }>;
  relationship_mappings?: Array<{ from: string; relation: string; to: string }>;
  setup_steps?: string[];
}

export interface WorkflowOntologyMappingInstallResult {
  status: string;
  mapping_id: string;
  schema_path: string;
  entity_types_added: number;
  relation_types_added: number;
  entity_types_total: number;
  relation_types_total: number;
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

// ── Skill System ──────────────────────────────────────────────────────────────

export type SkillImplementationType = "builtin" | "http" | "mcp_http" | "custom";

export interface MCPHttpConfig {
  transport?: "stdio" | "sse";
  callStyle?: "tool_endpoint" | "jsonrpc_proxy";
  server?: string;
  tool?: string;
  endpoint: string;
  method?: string;
  command?: string;
  args?: string[];
  cwd?: string;
  url?: string;
  headers?: Record<string, string>;
  env?: Record<string, string>;
  timeout?: number;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  author: string;
  tags?: string[];
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
  requiredCredentials?: string[];
  implementation: {
    type: SkillImplementationType;
    endpoint?: string;
    code?: string;
    mcpConfig?: MCPHttpConfig;
    credentialMapping?: Record<string, string>;
    auth?: {
      type?: "basic" | "bearer" | "custom";
      username?: string;
      password?: string;
    };
  };
  createdAt?: string;
  updatedAt?: string;
}
