// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PagePreview, PREVIEW_DELAY_MS } from "./PagePreview";
import { jsonResponse } from "../../lib/test-http";
import type { ThemeConfig } from "./ThemeSettings";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  vi.useFakeTimers();
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

type Call = { url: string; body: { ref: unknown; input: unknown } };
const page = (html: string) => ({
  surface: "page",
  label: "Public page",
  summary: "Previewing the live view. Nothing is saved or sent.",
  roles: [],
  versions: [],
  resolved: { role: null, at: null, version: null, live: true },
  notices: [],
  data: { html, theme: "default", theme_config: {} },
});

function setup(route: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call = {
        url: String(url),
        body: JSON.parse(String(init?.body ?? "{}")),
      };
      calls.push(call);
      return route(call);
    }),
  );
  const draw = (config: ThemeConfig, theme = "default") =>
    act(async () =>
      root.render(
        <PagePreview
          workspaceId="w"
          eventId="e"
          theme={theme}
          config={config}
        />,
      ),
    );
  const wait = (ms = PREVIEW_DELAY_MS + 50) =>
    act(async () => {
      await vi.advanceTimersByTimeAsync(ms);
    });
  return { calls, draw, wait };
}
const frame = () => container.querySelector("iframe");

describe("PagePreview", () => {
  it("asks the page surface once for the drafted appearance and shows it in a frame without scripts", async () => {
    const { calls, draw, wait } = setup(() =>
      jsonResponse(200, page("<p>Welcome</p>")),
    );
    await draw({ hero_size: "none", accent: "", banner_focus_x: 30 }, "dark");
    expect(calls).toHaveLength(0); // waits for the changes to settle
    await wait();
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe("/api/v1/workspaces/w/preview-as/page/");
    expect(calls[0].body.ref).toEqual({ event: "e" });
    expect(calls[0].body.input).toEqual({
      theme: "dark",
      theme_config: { hero_size: "none", banner_focus_x: 30 }, // blanks are not sent
    });
    const shown = frame()!;
    expect(shown.getAttribute("sandbox")).toBe(""); // no scripts, no storage, no navigation
    expect(shown.getAttribute("srcdoc")).toBe("<p>Welcome</p>");
    expect(shown.title).toBe("Public page preview, desktop 1440px wide");
    expect(container.textContent).toContain("Nothing is saved or sent.");
  });

  it("turns many quick changes into one request for the last one", async () => {
    const { calls, draw, wait } = setup(() =>
      jsonResponse(200, page("<p>x</p>")),
    );
    for (const x of [10, 20, 30, 40]) await draw({ banner_focus_x: x });
    await wait();
    expect(calls).toHaveLength(1);
    expect(
      (calls[0].body.input as { theme_config: { banner_focus_x: number } })
        .theme_config.banner_focus_x,
    ).toBe(40);
  });

  it("shows the page at the width of the chosen device", async () => {
    const { draw, wait } = setup(() => jsonResponse(200, page("<p>x</p>")));
    await draw({});
    await wait();
    const pressed = () =>
      [...container.querySelectorAll("button[aria-pressed='true']")].map(
        (b) => b.textContent,
      );
    expect(pressed()).toEqual(["Desktop 1440px"]);
    for (const [label, width] of [
      ["Tablet 768px", "768"],
      ["Mobile 390px", "390"],
    ]) {
      await act(async () =>
        [...container.querySelectorAll("button")]
          .find((b) => b.textContent === label)!
          .click(),
      );
      expect(frame()!.getAttribute("width")).toBe(width);
      expect(pressed()).toEqual([label]);
    }
    expect(frame()!.title).toContain("mobile 390px wide");
  });

  it("explains a draft the server refuses, keeps the last good frame and says nothing was saved", async () => {
    let refuse = false;
    const { draw, wait } = setup(() =>
      refuse
        ? jsonResponse(400, {
            "input.theme_config": [
              "The immersive hero is built around artwork.",
            ],
          })
        : jsonResponse(200, page("<p>good</p>")),
    );
    await draw({});
    await wait();
    refuse = true;
    await draw({ hero_size: "immersive" });
    await wait();
    expect(container.querySelector("[role=alert]")!.textContent).toContain(
      "built around artwork",
    );
    expect(container.textContent).toContain("nothing was saved");
    expect(frame()!.getAttribute("srcdoc")).toBe("<p>good</p>");
  });
});
