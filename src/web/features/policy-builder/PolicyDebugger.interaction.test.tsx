// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { PolicyBuilder } from "./PolicyBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

describe("policy debugger", () => {
  it("requests a decision and shows the failing fact in its trace", async () => {
    const fetcher = vi
      .fn()
      .mockImplementation(async (path: string, options?: RequestInit) => ({
        ok: true,
        status: 200,
        json: async () =>
          path.endsWith("policy-debug/") && options?.method === "POST"
            ? {
                allowed: false,
                policy_allowed: false,
                policy: { name: "Window" },
                reason: "Denied by policy 'Window'.",
                exception_grant_reason: null,
                error: null,
                trace: {
                  path: [],
                  op: "eq",
                  status: "evaluated",
                  result: false,
                  fact: "gate_open:submit",
                  actual: false,
                  expected: true,
                  children: [],
                },
                explanation: {
                  outcome: "blocked",
                  summary: "Denied by policy 'Window'.",
                  reasons: [
                    {
                      code: "gate_closed",
                      severity: "blocker",
                      message: "The submit window is not open.",
                    },
                  ],
                  total: 1,
                  truncated: false,
                },
              }
            : path.endsWith("policy-presets/")
              ? {}
              : [],
      }));
    vi.stubGlobal("fetch", fetcher);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () =>
      root.render(<PolicyBuilder workspaceId="w" eventId="e" />),
    );
    const form = [...container.querySelectorAll("form")].find((item) =>
      item.textContent?.includes("Check policy"),
    ) as HTMLFormElement;
    await act(async () =>
      form.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      ),
    );
    expect(
      fetcher.mock.calls.some(
        ([path, options]) =>
          String(path).endsWith("policy-debug/") &&
          JSON.parse(options.body).action === "submit",
      ),
    ).toBe(true);
    expect(container.textContent).toContain("Denied by policy");
    expect(container.textContent).toContain(
      "gate_open:submit = false; expected true",
    );
    // The explanation names the outcome in words and each blocking reason.
    const why = container.querySelector('[aria-label="Why this decision"]')!;
    expect(why.textContent).toContain("Blocked");
    expect(why.textContent).toContain("Blocker");
    expect(why.textContent).toContain("The submit window is not open.");
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });
});
