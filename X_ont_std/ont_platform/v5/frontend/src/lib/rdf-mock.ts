import type { ImportPreview, LinkedResource, MappingCandidate, OntologyImportResult, RDFGraphData } from "@/types/rdf";

export const mockRDFGraph: RDFGraphData = {
  nodes: [
    { id: "entity:project-alpha", label: "Project Alpha", type: "entity", source: "local" },
    { id: "entity:supplier-42", label: "Daehan Materials", type: "entity", source: "local" },
    { id: "property:status", label: "status", type: "property", source: "local" },
    { id: "literal:approved", label: "Approved", type: "literal", source: "local" },
    { id: "dbpedia:Machine_learning", label: "Machine Learning", type: "external", source: "dbpedia", uri: "https://dbpedia.org/resource/Machine_learning" },
    { id: "wikidata:Q11660", label: "Artificial Intelligence", type: "external", source: "wikidata", uri: "https://www.wikidata.org/wiki/Q11660" },
  ],
  edges: [
    { id: "edge-1", source: "entity:project-alpha", target: "entity:supplier-42", label: "depends_on" },
    { id: "edge-2", source: "entity:project-alpha", target: "property:status", label: "has_property" },
    { id: "edge-3", source: "property:status", target: "literal:approved", label: "has_value" },
    { id: "edge-4", source: "entity:project-alpha", target: "dbpedia:Machine_learning", label: "same_domain_as" },
    { id: "edge-5", source: "dbpedia:Machine_learning", target: "wikidata:Q11660", label: "related_to" },
  ],
};

export function mockNeighborhood(nodeId: string): RDFGraphData {
  const suffix = nodeId.split(":").pop()?.replace(/[^a-zA-Z0-9]/g, "-") || "node";
  return {
    nodes: [
      { id: nodeId, label: nodeId.split(":").pop() ?? nodeId, type: nodeId.startsWith("literal") ? "literal" : "entity", source: "local", expanded: true },
      { id: `external:${suffix}:dbpedia`, label: `DBpedia ${suffix}`, type: "external", source: "dbpedia", uri: `https://dbpedia.org/resource/${suffix}` },
      { id: `property:${suffix}:category`, label: "category", type: "property", source: "local" },
      { id: `literal:${suffix}:value`, label: "Linked concept", type: "literal", source: "local" },
    ],
    edges: [
      { id: `edge-${suffix}-1`, source: nodeId, target: `external:${suffix}:dbpedia`, label: "skos:closeMatch" },
      { id: `edge-${suffix}-2`, source: nodeId, target: `property:${suffix}:category`, label: "has_property" },
      { id: `edge-${suffix}-3`, source: `property:${suffix}:category`, target: `literal:${suffix}:value`, label: "has_value" },
    ],
  };
}

export const mockMappingCandidates: MappingCandidate[] = [
  { id: "entity:project-alpha", label: "Project Alpha", type: "Project", similarity: 0.91, reason: "Label and domain context match" },
  { id: "entity:supplier-42", label: "Daehan Materials", type: "Organization", similarity: 0.78, reason: "Connected supplier in current graph" },
  { id: "wikidata:Q11660", label: "Artificial Intelligence", type: "ExternalConcept", similarity: 0.72, reason: "Semantic neighbor through AI domain" },
];

export const mockImportPreview: ImportPreview = {
  previewId: "preview-demo-001",
  fileInfo: {
    name: "ai_domain_sample.ttl",
    size: 18432,
    triples: 1280,
  },
  statistics: {
    newClasses: 6,
    newProperties: 18,
    newTriples: 1280,
    externalUris: 42,
  },
  conflicts: [
    {
      id: "conflict-001",
      type: "label_conflict",
      externalUri: "https://dbpedia.org/resource/Project",
      externalValue: "Project",
      internalUri: "entity-type:Project",
      internalValue: "Project",
      severity: "warning",
    },
    {
      id: "conflict-002",
      type: "domain_range_conflict",
      externalUri: "http://example.org/hasOwner",
      externalValue: "domain: Organization",
      internalUri: "property:owner",
      internalValue: "domain: Project",
      severity: "error",
    },
  ],
  autoMappings: [
    {
      externalUri: "https://dbpedia.org/resource/Machine_learning",
      externalLabel: "Machine Learning",
      suggestedInternalId: "entity:project-alpha",
      suggestedInternalLabel: "Project Alpha",
      suggestedRelationship: "skos:closeMatch",
      confidence: 0.84,
    },
    {
      externalUri: "https://www.wikidata.org/wiki/Q11660",
      externalLabel: "Artificial Intelligence",
      suggestedInternalId: "wikidata:Q11660",
      suggestedInternalLabel: "Artificial Intelligence",
      suggestedRelationship: "owl:sameAs",
      confidence: 0.96,
    },
  ],
};

export const mockLinkedResources: LinkedResource[] = [
  {
    uri: "https://dbpedia.org/resource/Machine_learning",
    label: "Machine Learning",
    description: "DBpedia resource connected to AI/ML project entities.",
    sources: ["dbpedia"],
    language: "en",
    properties: { category: "Computer science", triples: 128 },
  },
  {
    uri: "https://www.wikidata.org/wiki/Q11660",
    label: "Artificial Intelligence",
    description: "Wikidata item used as an external concept anchor.",
    sources: ["wikidata"],
    language: "en",
    properties: { claims: 245, aliases: 18 },
  },
  {
    uri: "urn:local:ontology:ai-voucher",
    label: "AI Voucher Domain Ontology",
    description: "Local ontology graph merged with imported linked data.",
    sources: ["local", "rdf_file"],
    language: "ko",
    properties: { triples: 1200, entities: 215 },
  },
];

export const mockImportHistory: OntologyImportResult[] = [
  {
    import_id: "imp-20260525-001",
    status: "completed",
    source: "dbpedia",
    identifier: "https://dbpedia.org/resource/Machine_learning",
    domain_id: "ai",
    imported_entities: 28,
    imported_triples: 100,
  },
  {
    import_id: "imp-20260525-002",
    status: "completed",
    source: "wikidata",
    identifier: "Q11660",
    domain_id: "ai",
    imported_entities: 12,
    imported_triples: 45,
  },
];
