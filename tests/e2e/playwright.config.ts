import { defineConfig, devices } from "@playwright/test";

// Runs against a live stack seeded by `scripts/demo-reset` (see docs/operations/DEMO.md).
// `scripts/e2e-tiers` sets E2E_GROUP so concurrent groups keep separate outputs (outside
// testDir, so one group's cleanup never races another's test discovery).
// Capture is failure-first (PD-B03-T07). A routine run records nothing: Playwright keeps only a
// screenshot and the page snapshot (error-context.md) of failing tests. Recording a trace for every
// test just to discard it on success cost ~20% of run time, so scripts/e2e-tiers re-runs the failing
// spec files once with `E2E_TRACE=on` (diagnostic only; it never turns a failure into a pass).
// `E2E_CAPTURE=visual` (design/demo campaigns; `make demo-e2e`) records video and enables the
// explicit screenshots in the specs; `E2E_TRACE=on|retain-on-failure` and `E2E_VIDEO=on|
// retain-on-failure` switch one knob on while debugging a local run.
const visual = process.env.E2E_CAPTURE === "visual";
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
    trace:
      (process.env.E2E_TRACE as "on" | "off" | "retain-on-failure") ?? "off",
    screenshot: "only-on-failure",
    video:
      (process.env.E2E_VIDEO as "on" | "off" | "retain-on-failure") ??
      (visual ? "on" : "off"),
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
