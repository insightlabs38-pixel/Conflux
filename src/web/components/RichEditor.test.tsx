// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RichEditor } from "./RichEditor";
import { jsonResponse } from "../lib/test-http";

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

const tree = (text: string) => ({
  type: "doc",
  children: [{ type: "paragraph", children: [{ type: "text", text }] }],
});

async function show(value: string, onChange = vi.fn()) {
  await act(async () => {
    root.render(
      <RichEditor
        label="Project description"
        profile="story"
        workspaceId="w1"
        value={value}
        onChange={onChange}
      />,
    );
  });
  return onChange;
}
const toggle = () =>
  container.querySelector<HTMLButtonElement>("button[aria-expanded]")!;
const settle = () =>
  act(async () => void (await vi.advanceTimersByTimeAsync(400)));

describe("RichEditor", () => {
  it("is a labelled text box with the preview closed", async () => {
    await show("# Hi");
    expect(container.querySelector("textarea")!.value).toBe("# Hi");
    expect(container.querySelector("label")!.textContent).toBe(
      "Project description",
    );
    expect(toggle().getAttribute("aria-expanded")).toBe("false");
    expect(
      container.querySelector<HTMLElement>(".cx-rich-editor__preview")!.hidden,
    ).toBe(true);
  });

  it("hands every edit to the parent", async () => {
    const onChange = await show("a");
    const box = container.querySelector("textarea")!;
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(
        HTMLTextAreaElement.prototype,
        "value",
      )!.set!;
      setter.call(box, "ab");
      box.dispatchEvent(new Event("input", { bubbles: true }));
    });
    expect(onChange).toHaveBeenCalledWith("ab");
  });

  it("asks the server to render and draws the answer", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(200, {
        profile: "story",
        length: 4,
        max_length: 100000,
        tree: tree("Rendered by the server"),
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await show("# Hi");
    await act(async () => toggle().click());
    expect(container.textContent).toContain("Rendering preview…");
    await settle();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(String(url)).toContain("/api/v1/workspaces/w1/rich/preview/");
    expect(JSON.parse(String(init.body))).toEqual({
      profile: "story",
      source: "# Hi",
    });
    const region = container.querySelector('[role="region"]')!;
    expect(region.getAttribute("aria-label")).toBe(
      "Project description preview",
    );
    expect(region.textContent).toBe("Rendered by the server");
    expect(toggle().textContent).toBe("Hide preview");
  });

  it("shows the server's refusal and keeps the text box", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse(400, {
          source: ["The text is 100,001 characters; the limit is 100,000."],
        }),
      ),
    );
    await show("long");
    await act(async () => toggle().click());
    await settle();
    expect(container.querySelector('[role="alert"]')!.textContent).toContain(
      "100,001 characters",
    );
    expect(container.querySelector("textarea")!.value).toBe("long");
  });

  it("says there is nothing to preview for blank text, without calling the server", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    await show("  ");
    await act(async () => toggle().click());
    await settle();
    expect(container.textContent).toContain("Nothing to preview yet.");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("sends only the last text after a burst of edits", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(200, {
        profile: "story",
        length: 1,
        max_length: 1,
        tree: tree("x"),
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await show("a");
    await act(async () => toggle().click());
    await show("ab");
    await show("abc");
    await settle();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(
      JSON.parse(
        String(
          (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1].body,
        ),
      ).source,
    ).toBe("abc");
  });
});
