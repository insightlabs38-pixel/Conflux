// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { ProjectStoryEditor } from "./ProjectStoryEditor";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());
it("saves the project story through the existing scoped PATCH and reports the returned identity", async () => {
  const project = {
    public_id: "p",
    name: "Actual project",
    description: "Original story",
    team: null,
    track: null,
  };
  const fetchMock = vi.fn(async (_url: string, _options?: RequestInit) => ({
    ok: true,
    json: async () => project,
  }));
  vi.stubGlobal("fetch", fetchMock);
  const onSaved = vi.fn();
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(
      <ProjectStoryEditor
        project={project}
        base="/api/v1/workspaces/w/events/e/"
        onSaved={onSaved}
      />,
    ),
  );
  expect(container.querySelector("button")?.getAttribute("type")).toBe(
    "submit",
  );
  await act(async () =>
    container
      .querySelector("form")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })),
  );
  expect(fetchMock.mock.calls[0][0]).toBe(
    "/api/v1/workspaces/w/events/e/projects/p/",
  );
  const options = (
    fetchMock.mock.calls[0] as unknown as [string, RequestInit]
  )[1];
  expect(options.method).toBe("PATCH");
  expect(JSON.parse(String(options.body))).toEqual({
    name: "Actual project",
    description: "Original story",
  });
  expect(onSaved).toHaveBeenCalledWith(project);
  expect(container.textContent).toContain("Project story saved.");
  await act(async () => root.unmount());
});
