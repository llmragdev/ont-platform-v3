# Frontend E2E Scenarios

> Team: Codex  
> Scope: Phase 2.5 Week 4 e2e design  
> Status: Scenario definitions only. Cypress dependency is not installed in this workspace.

## Setup When Node/npm Is Available

```bash
cd ont_platform/v3/src/frontend
npm install -D cypress
npm pkg set scripts.cypress:open="cypress open"
npm pkg set scripts.cypress:run="cypress run"
```

Then create `cypress.config.ts`:

```ts
import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3001",
    supportFile: false,
    video: false,
    viewportWidth: 1280,
    viewportHeight: 800,
  },
});
```

## Scenario 1: SPARQL Console

```ts
describe("SPARQL console", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.contains("SPARQL 콘솔").click();
  });

  it("runs a query and renders table output", () => {
    cy.contains("Execute").click();
    cy.contains("쿼리 결과");
    cy.contains("Table");
    cy.contains("rows");
  });

  it("shows JSON and debug tabs", () => {
    cy.contains("Execute").click();
    cy.contains("JSON").click();
    cy.contains("query_time_ms");
    cy.contains("Debug").click();
    cy.contains("Generated SQL");
  });

  it("stores query history and restores a previous query", () => {
    cy.contains("타입 필터").click();
    cy.contains("Execute").click();
    cy.contains("쿼리 히스토리");
    cy.contains("SELECT").click();
    cy.get("textarea").should("contain.value", "rdf:type");
  });
});
```

## Scenario 2: Visualization

```ts
describe("SPARQL visualization", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.contains("SPARQL 콘솔").click();
    cy.contains("Execute").click();
  });

  it("renders graph view", () => {
    cy.contains("Graph").click();
    cy.contains("Graph View");
    cy.get("svg[aria-label='SPARQL result graph']").should("exist");
  });

  it("applies filter builder output to the query", () => {
    cy.contains("필터 빌더");
    cy.contains("Apply").click();
    cy.get("textarea").should("contain.value", "FILTER");
  });

  it("renders the response time chart", () => {
    cy.contains("응답 시간");
    cy.contains("Lookup");
    cy.contains("One-hop");
    cy.contains("Two-hop");
  });
});
```

## Scenario 3: Responsive Layout And Theme

```ts
describe("Responsive layout and theme", () => {
  it("renders SPARQL console on mobile viewport", () => {
    cy.viewport(390, 844);
    cy.visit("/");
    cy.contains("SPARQL 콘솔").click();
    cy.contains("SPARQL Query Editor");
    cy.contains("Execute");
  });

  it("toggles dark mode", () => {
    cy.visit("/");
    cy.get("button[aria-label='Toggle theme']").click();
    cy.get("html").should("have.class", "dark");
    cy.get("button[aria-label='Toggle theme']").click();
    cy.get("html").should("not.have.class", "dark");
  });
});
```

