const baseSparqlResponse = {
  source: "sql_translator",
  type: "SELECT",
  query_type: "SELECT",
  head: { vars: ["s", "p", "o"] },
  results: [
    { s: { type: "uri", value: "entity:one" }, p: { type: "literal", value: "name" }, o: { type: "literal", value: "Alpha" } },
  ],
  result_count: 1,
  execution_time_ms: 18,
  sql_generated: "SELECT id FROM entities LIMIT 10",
};

function visitSparql(response = baseSparqlResponse) {
  cy.intercept("GET", "/api/health", { statusCode: 200, body: { status: "ok" } });
  cy.intercept("POST", "/api/ontology/sparql", { statusCode: 200, body: response }).as("sparqlQuery");
  cy.visit("/");
  cy.get("[data-testid='nav-sparql-query']").click();
  cy.get("[data-testid='sparql-workbench']").should("be.visible");
}

function executeQuery(query = "SELECT ?s ?p ?o WHERE { ?s ?p ?o . } LIMIT 10") {
  cy.get("[data-testid='sparql-input']").clear().type(query, { parseSpecialCharSequences: false });
  cy.get("[data-testid='execute-button']").click();
  cy.wait("@sparqlQuery");
}

describe("Week 5 BugFix - SPARQL edge cases", () => {
  it("keeps execute disabled for an empty query", () => {
    visitSparql();
    cy.get("[data-testid='sparql-input']").clear();
    cy.get("[data-testid='execute-button']").should("be.disabled");
  });

  it("accepts very long SPARQL input without losing content", () => {
    visitSparql();
    const longQuery = `SELECT * WHERE { ${"?s ?p ?o . ".repeat(1200)} } LIMIT 10`;
    cy.get("[data-testid='sparql-input']").clear().type(longQuery, { parseSpecialCharSequences: false, delay: 0 });
    cy.get("[data-testid='sparql-input']").invoke("val").should("have.length.greaterThan", 10000);
  });

  it("shows client-side syntax feedback for invalid SPARQL", () => {
    visitSparql();
    cy.get("[data-testid='sparql-input']").clear().type("INVALID SPARQL QUERY", { parseSpecialCharSequences: false });
    cy.get("[data-testid='execute-button']").click();
    cy.get("[data-testid='sparql-validation-error']").should("contain", "Syntax error");
  });

  it("suggests recovery for common LIMIT mistakes", () => {
    visitSparql();
    cy.get("[data-testid='sparql-input']").clear().type("SELECT * WHERE { ?s ?p ?o . } LIMIT ten", { parseSpecialCharSequences: false });
    cy.get("[data-testid='execute-button']").click();
    cy.get("[data-testid='sparql-validation-error']").should("contain", "LIMIT 10");
  });

  it("exports successful results as JSON, CSV, and XML", () => {
    visitSparql();
    executeQuery();
    cy.get("[data-testid='export-json']").click();
    cy.get("[data-testid='export-status']").should("contain", "JSON");
    cy.get("[data-testid='export-csv']").click();
    cy.get("[data-testid='export-status']").should("contain", "CSV");
    cy.get("[data-testid='export-xml']").click();
    cy.get("[data-testid='export-status']").should("contain", "XML");
  });

  it("renders null and empty result cells as stable placeholders", () => {
    visitSparql({
      ...baseSparqlResponse,
      results: [
        { s: { type: "uri", value: "" }, p: { type: "literal", value: null }, o: null },
        { s: "", p: "", o: "" },
      ],
      result_count: 2,
    });
    executeQuery();
    cy.get("[data-empty-cell='true']").should("have.length", 6);
  });

  it("truncates extremely long values and preserves the full title", () => {
    const longValue = "x".repeat(1000);
    visitSparql({
      ...baseSparqlResponse,
      results: [{ s: { type: "literal", value: longValue }, p: "prop", o: "obj" }],
    });
    executeQuery();
    cy.get("[data-value='true']").first().should("have.attr", "title", longValue);
    cy.get("[data-value='true']").first().invoke("text").should("have.length.lessThan", 520);
  });

  it("renders special characters in result values", () => {
    visitSparql({
      ...baseSparqlResponse,
      results: [{ s: "<>&\"'", p: "日本語", o: "مرحبا" }],
    });
    executeQuery();
    cy.get("[data-testid='result-table-view']").should("contain", "<>&").and("contain", "日本語").and("contain", "مرحبا");
  });
});

describe("Week 5 BugFix - Regression coverage", () => {
  it("keeps SPARQL responsive layout available on mobile", () => {
    cy.viewport(390, 844);
    visitSparql();
    cy.get("[data-testid='sparql-workbench']").should("have.attr", "data-layout", "responsive-grid");
    cy.get("[data-testid='sparql-input']").scrollIntoView().should("be.visible");
  });

  it("handles backend failures with a visible error panel", () => {
    cy.intercept("GET", "/api/health", { statusCode: 200, body: { status: "ok" } });
    cy.intercept("POST", "/api/ontology/sparql", { statusCode: 500, body: { detail: "backend exploded" } }).as("sparqlFailure");
    cy.visit("/");
    cy.get("[data-testid='nav-sparql-query']").click();
    cy.get("[data-testid='sparql-input']").clear().type("SELECT ?s WHERE { ?s ?p ?o . }", { parseSpecialCharSequences: false });
    cy.get("[data-testid='execute-button']").click();
    cy.wait("@sparqlFailure");
    cy.get("[data-testid='query-result']").should("contain", "API 호출 실패");
  });

  it("keeps WriteBack DLQ replay regression path working", () => {
    cy.intercept("GET", "/api/health", { statusCode: 200, body: { status: "ok" } });
    cy.intercept("GET", "/api/writeback/dlq/items", {
      statusCode: 200,
      body: {
        items: [{
          id: "week5-dlq-001",
          target_system: "SAP",
          payload: { entity_id: "project-001" },
          dlq_reason: "Max retries exceeded",
          dlq_at: "2026-05-25T04:40:00Z",
          last_error_at: "2026-05-25T04:38:30Z",
          error_message: "Timeout",
          retry_count: 3,
        }],
        count: 1,
      },
    }).as("dlqItems");
    cy.intercept("GET", "/api/writeback/statistics", { statusCode: 200, body: { pending: 0, confirmed: 0, dlq: 1, failed: 0, total: 1 } });
    cy.intercept("POST", "/api/writeback/replay/week5-dlq-001", { statusCode: 200, body: { status: "replayed", queue_id: "week5-dlq-001" } }).as("replay");

    cy.visit("/");
    cy.get("[data-testid='nav-writeback-dlq']").click();
    cy.wait("@dlqItems");
    cy.get("[data-testid='replay-open-week5-dlq-001']").click();
    cy.get("[data-testid='replay-confirm']").click();
    cy.wait("@replay");
    cy.get("[data-testid='replay-success']").should("contain", "PENDING 상태로 복구");
  });
});
