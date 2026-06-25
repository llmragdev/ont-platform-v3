const actions = [
  { name: "approve_project", display: "Approve project", required_params: ["approver"] },
  { name: "change_deadline", display: "Change deadline", required_params: ["new_deadline", "reason"] },
];

const queryResponseWithActions = {
  source: "sql_translator",
  type: "SELECT",
  query_type: "SELECT",
  results: [{ entity: { type: "uri", value: "project-001" }, status: { type: "literal", value: "UnderReview" } }],
  execution_time_ms: 32,
  entity_id: "project-001",
  entity_type: "Project",
  current_status: "UnderReview",
  available_actions: actions,
};

const auditItems = [
  {
    changelog_id: "chg-001",
    entity_id: "project-001",
    entity_type: "Project",
    action: "APPROVE_PROJECT",
    performed_by: "pm@example.com",
    performed_at: "2026-06-20T14:30:45Z",
    sync_status: "SYNCED",
    old_status: "UnderReview",
    new_status: "Approved",
    target_system: "SAP",
    retry_count: 0,
  },
  {
    changelog_id: "chg-002",
    entity_id: "project-002",
    entity_type: "Project",
    action: "REJECT_PROJECT",
    performed_by: "reviewer@example.com",
    performed_at: "2026-06-20T13:20:15Z",
    sync_status: "FAILED",
    old_status: "UnderReview",
    new_status: "Rejected",
    target_system: "SAP",
    retry_count: 2,
  },
];

function openSparqlWithActions() {
  cy.intercept("POST", "/api/ontology/sparql", { statusCode: 200, body: queryResponseWithActions }).as("sparqlQuery");
  cy.visit("/");
  cy.get("[data-testid='nav-sparql-query']").click();
  cy.get("[data-testid='sparql-input']").type("SELECT ?entity WHERE { ?entity ?p ?o }", { parseSpecialCharSequences: false });
  cy.get("[data-testid='execute-button']").click();
  cy.wait("@sparqlQuery");
}

describe("ActionButton", () => {
  beforeEach(() => {
    cy.intercept("POST", "/api/workflow/execute", { statusCode: 200, body: { ok: true } }).as("executeAction");
    openSparqlWithActions();
  });

  it("should render action dropdown", () => {
    cy.get("[data-testid='action-button']").should("exist");
    cy.get("[data-testid='action-select']").should("exist");
  });

  it("should show required params form", () => {
    cy.get("[data-testid='action-select']").select("approve_project");
    cy.get("[data-testid='param-approver']").should("be.visible");
  });

  it("should execute action on button click", () => {
    cy.get("[data-testid='action-select']").select("approve_project");
    cy.get("[data-testid='param-approver']").type("pm@example.com");
    cy.get("[data-testid='action-execute']").click();
    cy.wait("@executeAction");
    cy.get("[data-testid='success-toast']").should("be.visible");
  });

  it("should show error toast on failure", () => {
    cy.intercept("POST", "/api/workflow/execute", { statusCode: 400, body: { detail: "invalid action" } }).as("executeFailure");
    cy.get("[data-testid='action-select']").select("approve_project");
    cy.get("[data-testid='param-approver']").type("pm@example.com");
    cy.get("[data-testid='action-execute']").click();
    cy.wait("@executeFailure");
    cy.get("[data-testid='error-toast']").should("be.visible");
  });

  it("should disable button on loading", () => {
    cy.intercept("POST", "/api/workflow/execute", (req) => {
      req.reply({ delay: 500, statusCode: 200, body: { ok: true } });
    }).as("executeSlow");
    cy.get("[data-testid='action-select']").select("approve_project");
    cy.get("[data-testid='param-approver']").type("pm@example.com");
    cy.get("[data-testid='action-execute']").click().should("be.disabled");
  });
});

describe("QueryResult with Actions", () => {
  it("should show action button when actions available", () => {
    openSparqlWithActions();
    cy.get("[data-testid='query-result']").should("exist");
    cy.get("[data-testid='action-button']").should("exist");
  });

  it("should hide action button when no actions", () => {
    cy.intercept("POST", "/api/ontology/sparql", {
      statusCode: 200,
      body: { ...queryResponseWithActions, entity_id: undefined, available_actions: [] },
    }).as("sparqlQuery");
    cy.visit("/");
    cy.get("[data-testid='nav-sparql-query']").click();
    cy.get("[data-testid='sparql-input']").type("SELECT ?entity WHERE { ?entity ?p ?o }", { parseSpecialCharSequences: false });
    cy.get("[data-testid='execute-button']").click();
    cy.wait("@sparqlQuery");
    cy.get("[data-testid='query-result']").should("exist");
    cy.get("[data-testid='action-button']").should("not.exist");
  });

  it("should execute action and refresh result", () => {
    cy.intercept("POST", "/api/workflow/execute", { statusCode: 200, body: { ok: true } }).as("executeAction");
    openSparqlWithActions();
    cy.get("[data-testid='action-select']").select("change_deadline");
    cy.get("[data-testid='param-new_deadline']").type("2026-07-31");
    cy.get("[data-testid='param-reason']").type("Supplier dependency moved");
    cy.get("[data-testid='action-execute']").click();
    cy.wait("@executeAction");
    cy.get("[data-testid='success-toast']").should("be.visible");
  });
});

describe("AuditDashboard", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/changelog/history*", (req) => {
      const actionType = req.query.action_type;
      const items = actionType ? auditItems.filter((item) => item.action === actionType) : auditItems;
      req.reply({ statusCode: 200, body: { items, total: items.length, stats: { success_rate: 92.5, failed_count: 1, pending_count: 0, average_retries: 1.2 } } });
    }).as("history");
    cy.visit("/");
    cy.get("[data-testid='nav-audit']").click();
    cy.wait("@history");
  });

  it("should render dashboard with filter section", () => {
    cy.get("[data-testid='audit-dashboard']").should("exist");
    cy.get("[data-testid='filter-date-from']").should("exist");
    cy.get("[data-testid='filter-action-type']").should("exist");
  });

  it("should filter by action type", () => {
    cy.get("[data-testid='filter-action-type']").select("APPROVE_PROJECT");
    cy.get("[data-testid='filter-apply']").click();
    cy.wait("@history");
    cy.get("[data-testid='table-row']").each((row) => {
      cy.wrap(row).contains("APPROVE_PROJECT");
    });
  });

  it("should show pagination", () => {
    cy.get("[data-testid='pagination']").should("exist");
    cy.get("[data-testid='pagination-next']").should("exist");
  });

  it("should expand row details", () => {
    cy.get("[data-testid='row-expand']").first().click();
    cy.get("[data-testid='row-details']").should("be.visible");
  });

  it("should download CSV", () => {
    cy.get("[data-testid='download-csv']").click();
  });
});
