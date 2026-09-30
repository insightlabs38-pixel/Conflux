// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { PublicAwards } from "./PublicAwards";
import { jsonResponse } from "../../lib/test-http";
import { until } from "../../lib/test-dom";
import { withQuery } from "../../lib/test-router";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

it("shows published winners without internal selection evidence", async () => {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => [
      {
        public_id: "a1",
        name: "Best project",
        description: "",
        winners: [{ project: "p1", project_name: "Project One" }],
      },
    ],
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(withQuery(<PublicAwards eventId="e1" />)));
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/events/e1/awards/",
    expect.objectContaining({ method: "GET" }),
  );
  for (
    let i = 0;
    i < 100 && !container.textContent?.includes("Best project");
    i++
  )
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  expect(container.textContent).toContain("Best project");
  expect(container.textContent).toContain("Project One");
  expect(container.querySelector("a")?.getAttribute("href")).toBe(
    "/e/e1/results/projects/p1/",
  );
  act(() => root.unmount());
  container.remove();
});

it("shows a retryable error instead of hiding an awards failure", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(jsonResponse(503, {}))
    .mockResolvedValueOnce({ ok: true, json: async () => [] });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(withQuery(<PublicAwards eventId="e1" />)));
  await until(
    () =>
      container.textContent?.includes("Could not load awards (503)") ?? false,
  );
  await act(async () => {
    (container.querySelector("button") as HTMLButtonElement).click();
  });
  await until(() => fetchMock.mock.calls.length === 2);
  await until(() => container.querySelector('[role="alert"]') === null);
  act(() => root.unmount());
  container.remove();
});
