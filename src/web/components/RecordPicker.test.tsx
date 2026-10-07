// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { withQuery } from "../lib/test-router";
import { RecordPicker } from "./RecordPicker";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function mount(rows: unknown[], total = rows.length) {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (path: string) => {
      urls.push(String(path));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          entity: "teams",
          total,
          limit: 100,
          offset: 0,
          rows,
        }),
      };
    }),
  );
  const chosen: string[] = [];
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      withQuery(
        <RecordPicker
          base="/api/v1/workspaces/w/events/e/entities/"
          entity="teams"
          field="name"
          label="Team"
          noun="team"
          value=""
          onChange={(id) => chosen.push(id)}
        />,
      ),
    ),
  );
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 20));
  });
  return { container, chosen, urls, root };
}

describe("record picker", () => {
  it("lists records by name and reports the chosen id", async () => {
    const { container, chosen, urls, root } = await mount([
      { id: "t-1", name: "Alpha" },
      { id: "t-2", name: "Beta" },
    ]);
    const select = container.querySelector("select")!;
    expect([...select.options].map((o) => o.textContent)).toEqual([
      "Choose a team…",
      "Alpha",
      "Beta",
    ]);
    expect(container.textContent).not.toContain("t-1");
    expect(urls[0]).toContain("/entities/teams/");
    await act(async () => {
      select.value = "t-2";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(chosen).toEqual(["t-2"]);
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });

  it("says when nothing matches and when the list is longer than shown", async () => {
    const empty = await mount([]);
    expect(empty.container.textContent).toContain("No team matches.");
    await act(async () => empty.root.unmount());
    empty.container.remove();
    const long = await mount([{ id: "t-1", name: "Alpha" }], 250);
    expect(long.container.textContent).toContain(
      "Showing 1 of 250; type to narrow.",
    );
    await act(async () => long.root.unmount());
    long.container.remove();
    vi.unstubAllGlobals();
  });
});
