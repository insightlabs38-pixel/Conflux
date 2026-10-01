// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { VersionCompare } from "./VersionCompare";
import { jsonResponse } from "../lib/test-http";
import { withQuery } from "../lib/test-router";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

const info = (id: string, label: string, current = false) => ({
  id,
  label,
  at: current ? null : "2026-10-01T10:00:00Z",
  by: null,
  current,
});
const LIST = {
  source: "form",
  label: "Form versions",
  versions: [
    info("v1", "Version 1"),
    info("v2", "Version 2"),
    info("draft", "Current draft", true),
  ],
};
const comparison = (from: string, to: string) => ({
  source: "form",
  older: info(from, from),
  newer: info(to, to),
  diff: {
    kind: "json",
    total: 1,
    truncated: false,
    changes: [
      {
        path: "/fields/0/label",
        op: "changed",
        before: "Pitch",
        after: `${from}->${to}`,
        clipped: false,
      },
    ],
  },
});
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
async function until(check: () => boolean) {
  for (let i = 0; i < 100 && !check(); i++)
    await act(async () => new Promise((r) => setTimeout(r, 10)));
  expect(check()).toBe(true);
}

async function mount(route: (url: string) => Response) {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      urls.push(String(url));
      return route(String(url));
    }),
  );
  await act(async () =>
    root.render(
      withQuery(
        <VersionCompare
          workspaceId="w"
          source="form"
          reference={{ event: "e", form: "f" }}
          label="Compare form versions"
        />,
      ),
    ),
  );
  await settle();
  return urls;
}
const selects = () => [...container.querySelectorAll("select")];

describe("VersionCompare", () => {
  it("compares the last published version with the draft to begin with", async () => {
    const urls = await mount((url) =>
      url.includes("/diff/")
        ? jsonResponse(200, comparison("v2", "draft"))
        : jsonResponse(200, LIST),
    );
    await until(() => container.querySelector(".cx-diff") !== null);
    expect(urls[0]).toBe("/api/v1/workspaces/w/versions/form/?event=e&form=f");
    expect(urls[1]).toBe(
      "/api/v1/workspaces/w/versions/form/diff/?event=e&form=f&older=v2&newer=draft",
    );
    expect(selects().map((s) => s.value)).toEqual(["v2", "draft"]);
    expect(
      container.querySelector('[role="group"]')!.getAttribute("aria-label"),
    ).toBe("Changes from v2 to draft");
    expect(container.textContent).toContain("v2->draft");
  });

  it("compares any two versions the person picks", async () => {
    const urls = await mount((url) =>
      url.includes("/diff/")
        ? jsonResponse(
            200,
            comparison(
              new URL(url, "http://x").searchParams.get("older")!,
              new URL(url, "http://x").searchParams.get("newer")!,
            ),
          )
        : jsonResponse(200, LIST),
    );
    await until(() => container.querySelector(".cx-diff") !== null);
    const first = selects()[0];
    await act(async () => {
      first.value = "v1";
      first.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await until(() => container.textContent!.includes("v1->draft"));
    expect(urls.at(-1)).toContain("older=v1&newer=draft");
  });

  it("says there is nothing to compare with fewer than two versions", async () => {
    await mount(() =>
      jsonResponse(200, {
        ...LIST,
        versions: [info("draft", "Current draft", true)],
      }),
    );
    await until(() => container.textContent!.includes("nothing to compare"));
    expect(selects()).toHaveLength(0);
  });

  it("shows a failure with a retry, for the list and for the comparison", async () => {
    let fail = true;
    await mount((url) =>
      url.includes("/diff/")
        ? jsonResponse(500, { detail: "Compare failed." })
        : fail
          ? jsonResponse(500, { detail: "Versions failed." })
          : jsonResponse(200, LIST),
    );
    await until(() => container.textContent!.includes("Versions failed."));
    fail = false;
    const retry = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Try again",
    )!;
    await act(async () => retry.click());
    await until(() => container.textContent!.includes("Compare failed."));
    expect(selects()).toHaveLength(2);
  });
});
