const neighbors = {
  nodes: [
    { id: "entity:project-alpha", label: "Project Alpha", type: "entity", source: "local" },
    { id: "external:project-alpha:dbpedia", label: "DBpedia Project Alpha", type: "external", source: "dbpedia", uri: "https://dbpedia.org/resource/Project_Alpha" },
    { id: "property:project-alpha:category", label: "category", type: "property", source: "local" },
  ],
  edges: [
    { id: "week7-edge-1", source: "entity:project-alpha", target: "external:project-alpha:dbpedia", label: "skos:closeMatch" },
    { id: "week7-edge-2", source: "entity:project-alpha", target: "property:project-alpha:category", label: "has_property" },
  ],
};

const preview = {
  previewId: "preview-test-001",
  fileInfo: { name: "test-ontology.ttl", size: 4096, triples: 320 },
  statistics: { newClasses: 2, newProperties: 4, newTriples: 320, externalUris: 8 },
  conflicts: [{
    id: "conflict-test-001",
    type: "label_conflict",
    externalUri: "https://dbpedia.org/resource/Project",
    externalValue: "Project",
    internalUri: "entity-type:Project",
    internalValue: "Project",
    severity: "warning",
  }],
  autoMappings: [{
    externalUri: "https://dbpedia.org/resource/Machine_learning",
    externalLabel: "Machine Learning",
    suggestedInternalId: "entity:project-alpha",
    suggestedInternalLabel: "Project Alpha",
    suggestedRelationship: "skos:closeMatch",
    confidence: 0.84,
  }],
};

function openRdfLab() {
  cy.intercept("GET", "/api/health", { statusCode: 200, body: { status: "ok" } });
  cy.intercept("GET", "/api/sparql/describe/*", { statusCode: 200, body: { resources: [] } });
  cy.intercept("GET", "/api/ontology/mapping-candidates*", {
    statusCode: 200,
    body: {
      candidates: [
        { id: "entity:project-alpha", label: "Project Alpha", type: "Project", similarity: 0.91, reason: "Label and domain context match" },
        { id: "entity:supplier-42", label: "Daehan Materials", type: "Organization", similarity: 0.78, reason: "Connected supplier" },
      ],
    },
  }).as("mappingCandidates");
  cy.visit("/");
  cy.get("[data-testid='nav-rdf-workbench']").click();
  cy.get("[data-testid='rdf-workbench']").should("be.visible");
}

describe("Phase 4 Week 7 Ontology Extension UI", () => {
  it("expands selected RDF node and updates graph statistics", () => {
    cy.intercept("GET", "/api/rdf/neighbors/*", { statusCode: 200, body: neighbors }).as("neighbors");
    openRdfLab();

    cy.get("[data-testid='rdf-cytoscape-canvas']").click("center");
    cy.get("[data-testid='rdf-expand-selected']").click();
    cy.wait("@neighbors");
    cy.get("[data-testid='rdf-graph-stats']").should("contain", "Nodes").and("contain", "Edges");
    cy.get("[data-testid='high-degree-node']").should("exist");
  });

  it("saves external URI mapping with relationship and confidence", () => {
    cy.intercept("POST", "/api/ontology/mappings", {
      statusCode: 200,
      body: { id: "mapping-test-001", approvalStatus: "pending" },
    }).as("saveMapping");
    openRdfLab();
    cy.wait("@mappingCandidates");

    cy.get("[data-testid='ontology-mapping-panel']").should("exist");
    cy.get("[data-testid='mapping-relationship']").select("owl:sameAs");
    cy.get("[data-testid='mapping-confidence']").invoke("val", 92).trigger("input");
    cy.get("[data-testid='mapping-comment']").type("Approved by Week 7 Cypress");
    cy.get("[data-testid='mapping-save']").click();
    cy.wait("@saveMapping");
    cy.get("[data-testid='mapping-status']").should("contain", "매핑 저장 완료");
  });

  it("generates import preview with stats, conflicts, and mapping suggestions", () => {
    cy.intercept("POST", "/api/ontology/import/preview", { statusCode: 200, body: preview }).as("preview");
    openRdfLab();

    cy.get("[data-testid='preview-generate']").click();
    cy.wait("@preview");
    cy.get("[data-testid='preview-stats']").should("contain", "newTriples").and("contain", "320");
    cy.get("[data-testid='preview-tab-conflicts']").click();
    cy.get("[data-testid='preview-conflict-row']").should("contain", "label_conflict");
    cy.get("[data-testid='preview-tab-mappings']").click();
    cy.get("[data-testid='preview-mapping-row']").should("contain", "Machine Learning").and("contain", "84%");
  });
});
