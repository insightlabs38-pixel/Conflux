// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { withQuery } from "../lib/test-router";
import {
  RecordPicker,
  entitySource,
  participantSource,
  type PickerSource,
} from "./RecordPicker";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function mount(
  rows: unknown[],
  total = rows.length,
  source: PickerSource = entitySource("/e/", "projects", "team", "team_id"),
  shape: (rows: unknown[], total: number) => unknown = (r, t) => ({
    total: t,
    rows: r,
  }),
) {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (path: string) => {
      urls.push(String(path));
      return {
        ok: true,
        status: 200,
        json: async () => shape(rows, total),
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
          source={source}
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
    // a team is found through its project: the project row's own id is not the team's
    const { container, chosen, urls, root } = await mount([
      { id: "p-1", team: "Alpha", team_id: "t-1" },
      { id: "p-2", team: "Beta", team_id: "t-2" },
      { id: "p-3", team: "Beta", team_id: "t-2" },
    ]);
    const select = container.querySelector("select")!;
    expect([...select.options].map((o) => o.textContent)).toEqual([
      "Choose a team…",
      "Alpha",
      "Beta",
    ]);
    expect(container.textContent).not.toContain("t-1"); // beta listed once
    expect(container.textContent).not.toContain("p-1");
    expect(urls[0]).toContain("/e/projects/");
    expect(decodeURIComponent(urls[0])).toContain("columns=team,team_id");
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
    const long = await mount(
      [{ id: "p-1", team: "Alpha", team_id: "t-1" }],
      250,
    );
    expect(long.container.textContent).toContain(
      "Showing 1 of 250; type to narrow.",
    );
    await act(async () => long.root.unmount());
    long.container.remove();
    vi.unstubAllGlobals();
  });

  it("lists the workspace's participants by username and sends what was typed", async () => {
    const { container, chosen, urls, root } = await mount(
      [{ user: "u-1", username: "ada" }],
      1,
      participantSource("w"),
      (rows, total) => ({ total, results: rows }),
    );
    const select = container.querySelector("select")!;
    expect([...select.options].map((o) => o.textContent)).toEqual([
      "Choose a team…",
      "ada",
    ]);
    expect(urls[0]).toBe(
      "/api/v1/workspaces/w/portfolio/participants/?limit=100",
    );
    await act(async () => {
      select.value = "u-1";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(chosen).toEqual(["u-1"]);
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });
});
