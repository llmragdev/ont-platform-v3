import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.E2E_FRONT_PORT ?? 3100);
const API_BASE = process.env.E2E_API_BASE ?? "http://localhost:8000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    headless: true,
    actionTimeout: 5_000,
    extraHTTPHeaders: {},
  },
  webServer: {
    command: `npm run start -- -p ${PORT}`,
    url: `http://localhost:${PORT}`,
    timeout: 60_000,
    reuseExistingServer: !process.env.CI,
    env: {
      NEXT_PUBLIC_API_BASE: API_BASE,
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
