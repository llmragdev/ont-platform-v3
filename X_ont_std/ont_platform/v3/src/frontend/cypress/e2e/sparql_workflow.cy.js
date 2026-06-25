const sampleResponse = {
  source: "sql_translator",
  type: "SELECT",
  query_type: "SELECT",
  select_vars: ["?entity", "?type", "?name"],
  head: { vars: ["entity", "type", "name"] },
  patterns: 2,
  pattern_ids: [19],
  results: [
    {
      entity: { type: "uri", value: "entity:project-alpha" },
      type: { type: "literal", value: "Project" },
      name: { type: "literal", value: "Project Alpha" },
      target: { type: "uri", value: "entity:supplier-42" },
      relation: { type: "literal", value: "depends_on" },
    },
  ],
  result_count: 1,
  execution_time_ms: 24,
  sql_generated: "SELECT id, properties FROM entities WHERE domain_id = $1 LIMIT 10",
  cache_hit: false,
  warnings: [],
  translator_used: true,
};

function openSparql() {
  cy.visit("/");
  cy.get("[data-testid='nav-sparql-query']").click();
  cy.get("[data-testid='sparql-workbench']").should("be.visible");
}

function stubSparql(response = sampleResponse) {
  cy.intercept("POST", "/api/ontology/sparql", {
    statusCode: 200,
    body: response,
  }).as("sparqlQuery");
}

function runQuery() {
  cy.get("[data-testid='sparql-input']").clear();
  cy.get("[data-testid='sparql-input']").type(
    "PREFIX ex: <http://example.org/>\nSELECT ?entity ?type ?name WHERE { ?entity ex:name ?name . } LIMIT 10",
    { parseSpecialCharSequences: false }
  );
  cy.get("[data-testid='execute-button']").click();
  cy.wait("@sparqlQuery");
}

describe("SPARQL Query Workflow", () => {
  beforeEach(() => {
    window.localStorage.clear();
    stubSparql();
  });

  it("executes a SPARQL query and renders table results", () => {
    openSparql();
    runQuery();

    cy.get("[data-testid='query-result']").should("be.visible");
    cy.get("[data-testid='result-table-view']").should("contain", "Project Alpha");
  });

  it("switches between table, JSON, graph, and debug views", () => {
    openSparql();
    runQuery();

    cy.get("[data-testid='result-tab-json']").click();
    cy.get("[data-testid='result-json-view']").should("contain", "sql_translator");

    cy.get("[data-testid='result-tab-graph']").click();
    cy.get("[data-testid='result-graph-view']").should("be.visible").and("contain", "Graph View");

    cy.get("[data-testid='result-tab-debug']").click();
    cy.get("[data-testid='result-debug-view']").should("contain", "SQL Translator");
    cy.get("[data-testid='result-debug-view']").should("contain", "SELECT id");
  });

  it("updates the performance chart after query execution", () => {
    openSparql();
    cy.get("[data-testid='performance-chart']").scrollIntoView().should("exist");
    runQuery();

    cy.get("[data-testid='performance-chart']").scrollIntoView().should("contain", "Lookup");
    cy.get("[data-testid='query-history']").should("contain", "SELECT");
  });

  it("restores a query from history", () => {
    openSparql();
    runQuery();

    cy.get("[data-testid='clear-query-button']").click();
    cy.get("[data-testid='sparql-input']").should("have.value", "");
    cy.get("[data-testid='history-item']").first().click();
    cy.get("[data-testid='sparql-input']").should("contain.value", "SELECT ?entity");
  });

  it("applies a filter builder snippet to the editor", () => {
    openSparql();

    cy.get("[data-testid='filter-property-input']").clear().type("status");
    cy.get("[data-testid='filter-operator-select']").select("=");
    cy.get("[data-testid='filter-value-input']").clear().type("active");
    cy.get("[data-testid='filter-preview']").should("contain", "FILTER");
    cy.get("[data-testid='filter-apply-button']").click();

    cy.get("[data-testid='sparql-input']").should("contain.value", 'FILTER (?status = "active")');
  });

  it("renders the SPARQL workflow on a mobile viewport", () => {
    cy.viewport(390, 844);
    openSparql();

    cy.get("[data-testid='sparql-input']").scrollIntoView().should("be.visible");
    cy.get("[data-testid='execute-button']").scrollIntoView().should("exist");
    cy.get("[data-testid='query-result']").scrollIntoView().should("exist");
  });

  it("toggles dark mode", () => {
    openSparql();

    cy.get("html").then(($html) => {
      const wasDark = $html.hasClass("dark");
      cy.get("[data-testid='theme-toggle']").click();
      cy.get("html").should(wasDark ? "not.have.class" : "have.class", "dark");
    });
  });

  it("exposes baseline keyboard and accessibility hooks", () => {
    openSparql();

    cy.get("[data-testid='theme-toggle']").should("have.attr", "aria-label");
    cy.get("[data-testid='sparql-input']").focus().should("be.focused");
    cy.get("[data-testid='execute-button']").should("not.be.disabled");
    cy.get("[data-testid='result-tab-table']").focus().type("{rightarrow}");
  });
});
