const linkedResources = [
  {
    uri: "https://dbpedia.org/resource/Machine_learning",
    label: "Machine Learning",
    description: "DBpedia resource connected to AI/ML project entities.",
    sources: ["dbpedia"],
    language: "en",
    properties: { triples: 128 },
  },
  {
    uri: "https://www.wikidata.org/wiki/Q11660",
    label: "Artificial Intelligence",
    description: "Wikidata item used as an external concept anchor.",
    sources: ["wikidata"],
    language: "en",
    properties: { claims: 245 },
  },
];

function openRdfLab() {
  cy.intercept("GET", "/api/health", { statusCode: 200, body: { status: "ok", version: "v4" } });
  cy.intercept("GET", "/api/sparql/describe/*", {
    statusCode: 200,
    body: { resources: linkedResources },
  }).as("describeEntity");
  cy.visit("/");
  cy.get("[data-testid='nav-rdf-workbench']").click();
  cy.get("[data-testid='rdf-workbench']").should("be.visible");
}

describe("RDF Workbench", () => {
  it("renders RDF graph viewer and linked data resources", () => {
    openRdfLab();
    cy.wait("@describeEntity");

    cy.get("[data-testid='view-title']").should("contain", "RDF Lab");
    cy.get("[data-testid='rdf-graph-viewer']").should("contain", "6 nodes / 5 edges");
    cy.get("[data-testid='rdf-cytoscape-canvas']").should("be.visible");
    cy.get("[data-testid='linked-data-viewer']").should("contain", "Machine Learning");
    cy.get("[data-testid='linked-resource-card']").should("have.length", 2);
  });

  it("cycles highlighted RDF paths and exposes graph controls", () => {
    openRdfLab();
    cy.get("[data-testid='rdf-workbench-selected']").should("contain", "entity:project-alpha");
    cy.get("[data-testid='highlight-path-button']").click();
    cy.get("[data-testid='rdf-zoom-in']").click();
    cy.get("[data-testid='rdf-zoom-out']").click();
    cy.get("[data-testid='rdf-fit']").click();
    cy.get("[data-testid='rdf-cytoscape-canvas'] canvas").should("exist");
  });

  it("imports an external ontology source and records history", () => {
    openRdfLab();
    cy.intercept("POST", "/api/import/wikidata", {
      statusCode: 200,
      body: {
        import_id: "imp-test-001",
        status: "completed",
        source: "wikidata",
        identifier: "Q11660",
        domain_id: "ai",
        imported_entities: 12,
        imported_triples: 45,
      },
    }).as("importWikidata");

    cy.get("[data-testid='import-type-wikidata']").click();
    cy.get("[data-testid='import-identifier']").clear().type("Q11660");
    cy.get("[data-testid='import-submit']").click();
    cy.wait("@importWikidata");
    cy.get("[data-testid='import-history-item']").first().should("contain", "wikidata").and("contain", "45 triples");
  });
});
