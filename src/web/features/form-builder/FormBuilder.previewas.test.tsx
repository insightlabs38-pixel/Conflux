// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FormBuilder } from "./FormBuilder";
import { jsonResponse } from "../../lib/test-http";

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

const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
const FORM = {
  public_id: "f1",
  name: "Application",
  draft_schema: { fields: [] },
};

describe("form builder: the saved form as someone else", () => {
  it("asks the server only once the section is opened and shows what it answers", async () => {
    const posts: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (init?.method === "POST") {
          posts.push(String(url));
          return jsonResponse(200, {
            surface: "form",
            label: "Application form",
            summary: "Previewing the live view. Nothing is saved or sent.",
            roles: ["participant"],
            versions: [],
            resolved: { role: null, at: null, version: null, live: true },
            notices: [],
            data: { fields: [], total: 0, hidden: 0 },
          });
        }
        return jsonResponse(
          200,
          String(url).endsWith("versions/") ? [] : [FORM],
        );
      }),
    );
    await act(async () =>
      root.render(<FormBuilder workspaceId="w" eventId="e" />),
    );
    await settle();
    const select = container.querySelector("select")!;
    await act(async () => {
      select.value = "f1";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await settle();
    const summary = [...container.querySelectorAll("summary")].find((s) =>
      s.textContent?.startsWith("Preview the saved form"),
    )!;
    expect(summary).toBeDefined();
    expect(posts).toEqual([]); // closed by default, nothing is requested
    await act(async () => {
      const details = summary.parentElement as HTMLDetailsElement;
      details.open = true;
      details.dispatchEvent(new Event("toggle"));
    });
    await settle();
    expect(posts).toEqual(["/api/v1/workspaces/w/preview-as/form/"]);
    expect(container.textContent).toContain(
      "Previewing the live view. Nothing is saved or sent.",
    );
  });
});
