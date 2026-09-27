// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { PublicAwards } from "./PublicAwards";

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
  await act(async () => root.render(<PublicAwards eventId="e1" />));
  expect(fetchMock).toHaveBeenCalledWith("/api/v1/events/e1/awards/");
  expect(container.textContent).toContain("Best project");
  expect(container.textContent).toContain("Project One");
  act(() => root.unmount());
  container.remove();
});

it("shows a retryable error instead of hiding an awards failure", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({}) })
    .mockResolvedValueOnce({ ok: true, json: async () => [] });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<PublicAwards eventId="e1" />));
  expect(container.textContent).toContain("Could not load awards (503)");
  await act(async () => {
    (container.querySelector("button") as HTMLButtonElement).click();
  });
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(container.querySelector('[role="alert"]')).toBeNull();
  act(() => root.unmount());
  container.remove();
});
