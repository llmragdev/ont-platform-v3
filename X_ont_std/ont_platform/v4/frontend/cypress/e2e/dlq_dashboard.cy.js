const dlqItems = [
  {
    id: "wbq-dlq-001",
    target_system: "SAP",
    payload: { entity_id: "project-001", action: "APPROVE_PROJECT" },
    dlq_reason: "Max retries exceeded",
    dlq_at: "2026-05-25T04:40:00Z",
    last_error_at: "2026-05-25T04:38:30Z",
    error_message: "Connection timeout after 3 attempts",
    retry_count: 3,
  },
  {
    id: "wbq-dlq-002",
    target_system: "ERP",
    payload: { entity_id: "payment-018", action: "START_PAYMENT" },
    dlq_reason: "Permission denied",
    dlq_at: "2026-05-25T03:12:00Z",
    last_error_at: "2026-05-25T03:10:52Z",
    error_message: "External system rejected service account token",
    retry_count: 4,
  },
  {
    id: "wbq-dlq-003",
    target_system: "CRM",
    payload: { entity_id: "customer-077", action: "SYNC_PROFILE" },
    dlq_reason: "Validation failed",
    dlq_at: "2026-05-24T23:55:00Z",
    last_error_at: "2026-05-24T23:53:42Z",
    error_message: "Missing required external_customer_id",
    retry_count: 3,
  },
];

const stats = { pending: 8, confirmed: 124, dlq: 3, failed: 5, total: 140 };

function mockWritebackApi(items = dlqItems) {
  cy.intercept("GET", "/api/writeback/dlq/items", {
    statusCode: 200,
    body: { items, count: items.length },
  }).as("dlqItems");
  cy.intercept("GET", "/api/writeback/statistics", {
    statusCode: 200,
    body: { ...stats, dlq: items.length, total: 137 + items.length },
  }).as("writebackStats");
}

describe("WriteBack DLQ Dashboard", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/health", { statusCode: 200, body: { status: "ok", version: "v4" } });
  });

  it("loads DLQ rows with statistics and filters by target system", () => {
    mockWritebackApi();
    cy.visit("/");
    cy.get("[data-testid='nav-writeback-dlq']").click();
    cy.wait("@dlqItems");
    cy.wait("@writebackStats");

    cy.get("[data-testid='view-title']").should("contain", "Writeback DLQ 관리");
    cy.get("[data-testid='dlq-dashboard']").should("exist");
    cy.get("[data-testid='dlq-count']").should("contain", "3");
    cy.get("[data-testid='dlq-row']").should("have.length", 3);

    cy.get("[data-testid='filter-target-system']").select("SAP");
    cy.get("[data-testid='dlq-row']").should("have.length", 1).and("contain", "wbq-dlq-001");
    cy.get("[data-testid='filter-reset']").click();
    cy.get("[data-testid='dlq-row']").should("have.length", 3);
  });

  it("opens replay confirmation modal and posts replay request", () => {
    mockWritebackApi();
    cy.intercept("POST", "/api/writeback/replay/wbq-dlq-001", {
      statusCode: 200,
      body: { status: "replayed", queue_id: "wbq-dlq-001" },
    }).as("replayItem");

    cy.visit("/");
    cy.get("[data-testid='nav-writeback-dlq']").click();
    cy.wait("@dlqItems");

    cy.get("[data-testid='replay-open-wbq-dlq-001']").click();
    cy.get("[data-testid='replay-modal']").should("be.visible");
    cy.get("[data-testid='replay-item-id']").should("contain", "wbq-dlq-001");
    cy.get("[data-testid='replay-confirm']").click();
    cy.wait("@replayItem");
    cy.get("[data-testid='replay-success']").should("contain", "PENDING 상태로 복구");
  });

  it("auto-refreshes every 5 seconds and can open detail modal", () => {
    cy.clock(new Date("2026-05-25T05:00:00Z").getTime());
    let refreshed = false;
    cy.intercept("GET", "/api/writeback/dlq/items", (req) => {
      const items = refreshed ? [...dlqItems, {
        id: "wbq-dlq-004",
        target_system: "SAP",
        payload: { entity_id: "project-004", action: "SYNC" },
        dlq_reason: "Timeout",
        dlq_at: "2026-05-25T04:59:00Z",
        last_error_at: "2026-05-25T04:58:30Z",
        error_message: "Gateway timeout",
        retry_count: 3,
      }] : dlqItems;
      req.reply({ statusCode: 200, body: { items, count: items.length } });
    }).as("dlqItems");
    cy.intercept("GET", "/api/writeback/statistics", { statusCode: 200, body: stats }).as("writebackStats");

    cy.visit("/");
    cy.get("[data-testid='nav-writeback-dlq']").click();
    cy.wait("@dlqItems");
      cy.get("[data-testid='dlq-row']").should("have.length", 3);

    cy.then(() => {
      refreshed = true;
    });
    cy.tick(5000);
    cy.wait("@dlqItems");
    cy.get("[data-testid='dlq-row']").should("have.length", 4);

    cy.contains("[data-testid='dlq-row']", "wbq-dlq-004").click();
    cy.get("[data-testid='dlq-detail-modal']").should("be.visible").and("contain", "Gateway timeout");
    cy.get("[data-testid='detail-close']").click();
    cy.get("[data-testid='dlq-detail-modal']").should("not.exist");
  });
});
