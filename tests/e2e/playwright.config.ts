import { defineConfig, devices } from "@playwright/test";

// Runs against a live stack seeded by `scripts/demo-reset` (see docs/operations/DEMO.md).
export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  outputDir: "artifacts/results",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["json", { outputFile: "artifacts/report.json" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8080",
    locale: "en-US",
    timezoneId: "UTC",
    reducedMotion: "reduce",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 800 },
      },
    },
    {
      name: "mobile",
      use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 } },
      testIgnore: /scenes\.spec\.ts/,
    },
  ],
});
