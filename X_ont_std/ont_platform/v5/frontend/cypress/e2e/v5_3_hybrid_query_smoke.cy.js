describe("v5.3 hybrid query UI smoke", () => {
  const page = "/hybrid-query";

  function runQuery(query, modeLabel) {
    cy.visit(page);
    cy.contains("질의를 입력하세요", { timeout: 20000 }).should("be.visible");
    cy.get("textarea").clear().type(query, { delay: 0 });
    cy.get("select").select(modeLabel);
    cy.contains("button", "질의 실행").click();
    cy.contains("답변 생성 중", { timeout: 10000 }).should("be.visible");
    cy.contains("v5.3", { timeout: 90000 }).should("be.visible");
  }

  it("shows Snowflake as blocked with 0 percent confidence and filtered RAG", () => {
    runQuery(
      "Snowflake 기반 RAG 평가에서 문서 저장소와 근거 페이지를 왜 함께 관리해야 하는가?",
      "📄 문서만 (보수적)"
    );

    cy.contains("v5.3 NO_ANSWER / blocked", { timeout: 90000 }).should("be.visible");
    cy.contains("신뢰도:").parent().contains("0%").should("be.visible");
    cy.contains("RAG (5)").should("be.visible");
    cy.contains("필터링된 문서 (5)").should("be.visible");
    cy.contains("필터됨 (답변 차단)").should("be.visible");
  });

  it("shows expert mode as conservative GENERAL_ONLY rather than blocked", () => {
    runQuery(
      "DB 스키마를 온톨로지로 변환할 때 어떤 절차가 필요한가?",
      "🎯 전문가모드 (지식통합)"
    );

    cy.contains("v5.3 GENERAL_ONLY / partial", { timeout: 90000 }).should("be.visible");
    cy.contains("신뢰도:").parent().contains("55%").should("be.visible");
    cy.contains("RAG (5)").should("be.visible");
    cy.contains("필터링된 문서 (5)").should("not.exist");
  });
});
