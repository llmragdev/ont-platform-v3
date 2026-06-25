describe("Metadata Workspace", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/entities/*/metadata", { statusCode: 404, body: {} });
    cy.intercept("GET", "/api/entities/*/versions", { statusCode: 404, body: {} });
    cy.intercept("GET", "/api/entities/*/data-quality", { statusCode: 404, body: {} });
    cy.intercept("GET", "/api/entities/*/lineage", { statusCode: 404, body: {} });
    cy.intercept("GET", "/api/entities/*/impact", { statusCode: 404, body: {} });
    cy.intercept("GET", "/api/audit/logs*", { statusCode: 404, body: {} });
    cy.visit("/");
    cy.get("[data-testid='nav-metadata']").click();
  });

  it("renders metadata, lineage, and audit mock panels", () => {
    cy.get("[data-testid='metadata-workspace']").should("be.visible");
    cy.get("[data-testid='metadata-panel']").should("contain", "entity-123");
    cy.get("[data-testid='lineage-viewer']").should("contain", "Quality Chain");
    cy.get("[data-testid='audit-log-table']").should("contain", "audit-001");
  });

  it("loads a different entity id from the selector", () => {
    cy.get("[data-testid='metadata-entity-input']").clear().type("entity-67");
    cy.get("[data-testid='metadata-entity-apply']").click();
    cy.get("[data-testid='metadata-panel']").should("contain", "entity-67");
  });
});
