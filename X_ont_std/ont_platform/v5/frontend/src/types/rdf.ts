export type RDFNodeType = "entity" | "property" | "literal" | "external";

export interface RDFGraphNode {
  id: string;
  label: string;
  type: RDFNodeType;
  uri?: string;
  source?: "local" | "dbpedia" | "wikidata" | "rdf_file";
  degree?: number;
  expanded?: boolean;
}

export interface RDFGraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  predicate?: string;
}

export interface RDFGraphData {
  nodes: RDFGraphNode[];
  edges: RDFGraphEdge[];
}

export type MappingRelationshipType =
  | "owl:sameAs"
  | "skos:exactMatch"
  | "skos:closeMatch"
  | "skos:broader"
  | "skos:narrower"
  | "relatedTo";

export interface MappingCandidate {
  id: string;
  label: string;
  type: string;
  similarity: number;
  reason: string;
}

export interface OntologyMappingRule {
  id?: string;
  externalUri: string;
  externalLabel: string;
  internalEntityId: string;
  internalLabel: string;
  relationshipType: MappingRelationshipType;
  confidence: number;
  comment?: string;
  approvalStatus?: "pending" | "approved" | "rejected";
}

export interface ImportConflict {
  id: string;
  type: "label_conflict" | "uri_conflict" | "type_conflict" | "datatype_conflict" | "domain_range_conflict";
  externalUri: string;
  externalValue: string;
  internalUri?: string;
  internalValue?: string;
  severity: "info" | "warning" | "error";
}

export interface AutoMappingSuggestion {
  externalUri: string;
  externalLabel: string;
  suggestedInternalId: string;
  suggestedInternalLabel: string;
  suggestedRelationship: MappingRelationshipType;
  confidence: number;
}

export interface ImportPreview {
  previewId: string;
  fileInfo: {
    name: string;
    size: number;
    triples: number;
  };
  statistics: {
    newClasses: number;
    newProperties: number;
    newTriples: number;
    externalUris: number;
  };
  conflicts: ImportConflict[];
  autoMappings: AutoMappingSuggestion[];
}

export type ImportSourceType = "dbpedia" | "wikidata" | "rdf_file";

export interface OntologyImportRequest {
  type: ImportSourceType;
  identifier: string;
  domain_id: string;
}

export interface OntologyImportResult {
  import_id: string;
  status: "queued" | "running" | "completed" | "failed" | string;
  source: ImportSourceType;
  identifier: string;
  domain_id: string;
  imported_entities: number;
  imported_triples: number;
  warnings?: string[];
}

export interface LinkedResource {
  uri: string;
  label: string;
  description: string;
  sources: Array<"local" | "dbpedia" | "wikidata" | "rdf_file" | string>;
  language?: string;
  properties?: Record<string, string | number | boolean | null>;
}
