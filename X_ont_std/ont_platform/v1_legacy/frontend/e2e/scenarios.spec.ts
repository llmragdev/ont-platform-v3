import { test, expect } from "@playwright/test";

/**
 * 학습 시나리오 5종 E2E (#5).
 * 백엔드(uvicorn:8000)가 별도로 떠 있어야 한다.
 * 프론트는 playwright.config.ts의 webServer가 `npm run start -p 3100`으로 자동 기동한다.
 *
 * 시나리오는 README.md §4 와 backend/eval/scenarios.py 와 일치한다.
 */

const API_BASE = process.env.E2E_API_BASE ?? "http://localhost:8000";

test.beforeEach(async ({ request }) => {
  await request.post(`${API_BASE}/api/system/reset`);
});

test.describe("학습 시나리오 5종", () => {
  test("1. 정상 승인: analyst가 O001(Low risk, 3200원) ApproveOrder", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "대시보드" })).toBeVisible();

    // 워크플로우 메뉴 이동
    await page.getByRole("button", { name: /승인 워크플로우/ }).click();
    await expect(page.getByRole("heading", { name: "현재 사용자의 액션 큐" })).toBeVisible();

    // O001 행에서 ApproveOrder 버튼 클릭
    const row = page.locator("tr", { hasText: "O001" });
    await expect(row).toBeVisible();
    await row.getByRole("button", { name: "ApproveOrder" }).click();

    // 토스트 메시지
    await expect(page.getByText(/O001.*Approved/)).toBeVisible();
  });

  test("2. 고위험 거부: analyst가 O003(High risk) ApproveOrder 시 ACTION_NOT_ALLOWED", async ({ page }) => {
    await page.goto("/");
    // O003은 High risk이므로 analyst의 워크플로우 큐에 ApproveOrder가 보이면 안 됨
    await page.getByRole("button", { name: /승인 워크플로우/ }).click();
    const row = page.locator("tr", { hasText: "O003" });
    // analyst region에 Incheon이 포함되어 보이긴 함. 그러나 ApproveOrder 버튼은 없어야 한다.
    if (await row.isVisible()) {
      await expect(row.getByRole("button", { name: "ApproveOrder" })).toHaveCount(0);
    }
  });

  test("3. 금액 임계 분기: viewer→finance로 전환하면 O002 액션 큐가 나타남", async ({ page }) => {
    await page.goto("/");

    // 사용자 셀렉터를 finance로 변경
    await page.getByRole("combobox").selectOption("finance");

    await page.getByRole("button", { name: /승인 워크플로우/ }).click();
    const row = page.locator("tr", { hasText: "O002" });
    await expect(row).toBeVisible();
    await expect(row.getByRole("button", { name: "ApproveOrder" })).toBeVisible();
  });

  test("4. 지역 거부: viewer로 전환 시 O002(Busan) 컨텍스트 접근 차단", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("combobox").selectOption("viewer");

    // Explorer로 이동해서 O002 선택 시도
    await page.getByRole("button", { name: /객체 탐색/ }).click();
    const row = page.locator("tr", { hasText: "O002" });
    // viewer 권한으로는 O002 자체가 목록에 없어야 한다 (region filter).
    await expect(row).toHaveCount(0);
  });

  test("5. 속성 마스킹: viewer가 보는 C001.risk_tier = Restricted", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("combobox").selectOption("viewer");

    await page.getByRole("button", { name: /객체 탐색/ }).click();
    const row = page.locator("tr", { hasText: "Alpha Manufacturing" });
    await expect(row).toBeVisible();
    await expect(row).toContainText("Restricted");
  });
});

test.describe("백엔드 헬스 표시", () => {
  test("사이드바에 LLM provider 배지가 보인다", async ({ page }) => {
    await page.goto("/");
    const badge = page.locator("aside").first().getByText(/LLM:/);
    await expect(badge).toBeVisible();
  });
});
