import { defineConfig, devices } from "@playwright/test";

// Runs against a live stack seeded by `scripts/demo-reset` (see docs/operations/DEMO.md).
// `scripts/e2e-fast` sets E2E_GROUP so concurrent groups keep separate outputs (outside
// testDir, so one group's cleanup never races another's test discovery), and
// drops per-test video (lifecycle/scenes still record their own demo clips).
const group = process.env.E2E_GROUP ?? "";
export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  testIgnore: ["artifacts/**"],
  outputDir: group
    ? `../../artifacts/e2e-fast/${group}/results`
    : "artifacts/results",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile: group
          ? `../../artifacts/e2e-fast/${group}/report.json`
          : "artifacts/report.json",
      },
    ],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8080",
    locale: "en-US",
    timezoneId: "UTC",
    reducedMotion: "reduce",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: group ? "off" : "retain-on-failure",
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
