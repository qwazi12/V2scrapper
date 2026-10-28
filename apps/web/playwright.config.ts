import { defineConfig } from "@playwright/test";
const remote = !!process.env.SCOS_E2E_URL?.startsWith("https:");
export default defineConfig({
  testDir: "../../tests/e2e",
  timeout: 300000,
  workers: 1,
  fullyParallel: false,
  use: {
    baseURL: process.env.SCOS_E2E_URL || "http://127.0.0.1:3101",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    trace: remote ? "off" : "retain-on-failure",
    screenshot: "only-on-failure",
    storageState: process.env.SCOS_E2E_STORAGE_STATE || undefined,
  },
  outputDir: "../../artifacts/browser",
  reporter: [
    ["list"],
    ["json", { outputFile: "../../artifacts/browser-results.json" }],
  ],
});
