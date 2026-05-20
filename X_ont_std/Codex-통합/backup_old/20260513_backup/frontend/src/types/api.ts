export interface PropertyDef {
  name: string;
  type: string;
  required?: boolean;
  searchable?: boolean;
  sensitive?: boolean;
  values?: string[];
}

export interface ObjectTypeDef {
  name: string;
  display_name?: string;
  id_prefix?: string;
  properties: PropertyDef[];
}

export interface RelationshipTypeDef {
  name: string;
  display_name?: string;
  reverse_display_name?: string;
  source_type: string;
  target_type: string;
  cardinality: string;
  properties: PropertyDef[];
}

export interface ActionTypeDef {
  name: string;
  display_name?: string;
  target_type: string;
  description?: string;
  exposed_as_graph_node?: boolean;
}

export interface OntologySchema {
  object_types: ObjectTypeDef[];
  relationship_types: RelationshipTypeDef[];
  action_types: ActionTypeDef[];
}

export interface OntologyObject {
  id: string;
  type: string;
  [key: string]: unknown;
}

export interface Relationship {
  id: string;
  type: string;
  source_id: string;
  target_id: string;
  properties: Record<string, unknown>;
}

export interface ObjectContext {
  object: OntologyObject;
  incoming: Array<{ relationship: string; display_name?: string; source: OntologyObject; properties: Record<string, unknown> }>;
  outgoing: Array<{ relationship: string; display_name?: string; target: OntologyObject; properties: Record<string, unknown> }>;
  documents: Array<{ id: string; title: string; text: string }>;
  available_actions: ActionTypeDef[];
}

export interface AskResponse {
  question: string;
  detected_object_id: string;
  answer: string;
  ontology_context: ObjectContext;
  evidence: Array<{ id: string; title: string; text: string; score: number }>;
  trace: string[];
}

export interface StructuredData {
  headers: string[];
  rows: string[][];
}

export interface HybridAskResponse {
  question: string;
  query_type: "object_context" | "compare" | "calculate" | "filter";
  plan: Record<string, unknown>;
  answer: string;
  structured_data: StructuredData;
  ontology_nodes: string[];
  ontology_contexts: ObjectContext[];
  vector_evidence: Array<{ id: string; title: string; text: string; score: number }>;
  trace: string[];
}
