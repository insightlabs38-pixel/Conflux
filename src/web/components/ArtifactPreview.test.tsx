// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ArtifactPreview, PreviewLoader } from "./ArtifactPreview";
import { factRow, humanSize, previewUrl, type Preview } from "../lib/preview";
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

const preview = (over: Partial<Preview> = {}): Preview => ({
  source: "test",
  ref: {},
  name: "Notes.txt",
  content_type: "text/plain",
  size: 1536,
  kind: "text",
  detected_type: "text",
  state: "ready",
  reason: null,
  facts: {},
  findings: [],
  findings_total: 0,
  text: "",
  entries: [],
  entries_total: 0,
  media: null,
  link: null,
  inspected_at: null,
  ...over,
});
const show = (value: Preview, showDownload?: boolean) =>
  act(async () =>
    root.render(
      <ArtifactPreview preview={value} showDownload={showDownload} />,
    ),
  );
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
async function until(check: () => boolean) {
  for (let i = 0; i < 100 && !check(); i++)
    await act(async () => new Promise((r) => setTimeout(r, 10)));
  expect(check()).toBe(true);
}

describe("ArtifactPreview", () => {
  it("names the kind and size and shows an excerpt as text, never markup", async () => {
    await show(preview({ text: "<script>alert(1)</script>\nline two" }));
    expect(container.textContent).toContain("Text · 1.5 KB");
    expect(container.textContent).toContain("Detected type: text");
    const pre = container.querySelector("pre")!;
    expect(pre.getAttribute("aria-label")).toBe("Preview of Notes.txt");
    expect(pre.tabIndex).toBe(0);
    expect(pre.textContent).toBe("<script>alert(1)</script>\nline two");
    expect(container.querySelector("script")).toBeNull();
  });

  it("lists findings with their level and counts the ones it left out", async () => {
    await show(
      preview({
        findings: [
          { level: "blocked", code: "a", message: "Withheld thing" },
          { level: "warning", code: "b", message: "Careful thing" },
        ],
        findings_total: 5,
      }),
    );
    const list = container.querySelector(
      'ul[aria-label="Findings for Notes.txt"]',
    )!;
    expect(list.textContent).toContain("blocked Withheld thing");
    expect(list.textContent).toContain("warning Careful thing");
    expect(list.textContent).toContain("and 3 more");
  });

  it("shows facts with readable labels and sizes", async () => {
    await show(
      preview({
        facts: { bytes: 2048, width: 640, uncompressed_bytes: 5, ok: true },
      }),
    );
    const rows = [...container.querySelectorAll("dl > div")].map((row) => [
      row.querySelector("dt")!.textContent,
      row.querySelector("dd")!.textContent,
    ]);
    expect(rows).toEqual([
      ["Size", "2 KB"],
      ["Width", "640"],
      ["Uncompressed size", "5 B"],
      ["Ok", "true"],
    ]);
  });

  it("lists archive entries and says how many are not shown", async () => {
    await show(
      preview({
        kind: "archive",
        name: "code.zip",
        entries: [
          { name: "a.py", size: 10 },
          { name: "b.py", size: null },
        ],
        entries_total: 80,
      }),
    );
    const region = container.querySelector('[aria-label="Files in code.zip"]')!;
    expect(region.querySelectorAll("tbody tr")).toHaveLength(2);
    expect(region.textContent).toContain("Showing 2 of 80 files.");
    expect(region.querySelector('th[scope="col"]')).not.toBeNull();
  });

  it("explains why a thing has no preview and still offers the download", async () => {
    await show(
      preview({
        kind: "unavailable",
        state: "unavailable",
        reason: {
          code: "no_preview",
          message: "There is no preview for this kind of file.",
        },
        media: { url: "https://store/x", filename: "blob.bin" },
      }),
    );
    expect(container.querySelector('[role="note"]')!.textContent).toContain(
      "no preview for this kind",
    );
    const link = container.querySelector<HTMLAnchorElement>("a")!;
    expect(link.getAttribute("href")).toBe("https://store/x");
    expect(link.textContent).toBe("Download blob.bin");
    await show(
      preview({ media: { url: "https://store/x", filename: "blob.bin" } }),
      false,
    );
    expect(container.querySelector("a")).toBeNull();
  });

  it("says a withheld thing is withheld and never offers a download that was not given", async () => {
    await show(
      preview({
        kind: "unavailable",
        state: "unavailable",
        reason: {
          code: "active_content",
          message: "Withheld from preview: it can run scripts.",
        },
      }),
    );
    expect(container.textContent).toContain("Withheld from preview");
    expect(container.querySelector("a")).toBeNull();
  });

  it("opens only web links, in a new tab without the opener", async () => {
    await show(preview({ kind: "link", link: "https://demo.example/" }));
    const link = container.querySelector<HTMLAnchorElement>("a")!;
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
    expect(link.target).toBe("_blank");
    await show(preview({ kind: "link", link: "javascript:alert(1)" }));
    expect(container.querySelector("a")).toBeNull();
  });

  it("marks an uninspected thing as pending", async () => {
    await show(
      preview({
        state: "pending",
        kind: "unavailable",
        detected_type: "",
        reason: { code: "not_inspected", message: "Run the safe inspection." },
      }),
    );
    expect(container.textContent).toContain("not inspected yet");
    expect(container.textContent).toContain("Run the safe inspection.");
  });
});

describe("PreviewLoader", () => {
  const mount = (fetchMock: ReturnType<typeof vi.fn>) => {
    vi.stubGlobal("fetch", fetchMock);
    return act(async () =>
      root.render(
        withQuery(
          <PreviewLoader
            workspaceId="w"
            source="job_output"
            reference={{ job: "j", name: "a b.csv" }}
          />,
        ),
      ),
    );
  };

  it("asks the server for the descriptor and draws it", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(200, preview({ text: "hello" })),
    );
    await mount(fetchMock);
    expect(container.textContent).toContain("Loading preview");
    await until(() => container.querySelector("pre") !== null);
    expect(String((fetchMock.mock.calls[0] as unknown[])[0])).toBe(
      "/api/v1/workspaces/w/previews/job_output/?job=j&name=a+b.csv",
    );
  });

  it("says there is nothing to preview when the server does not show it to this person", async () => {
    await mount(vi.fn(async () => jsonResponse(404, { detail: "Not found." })));
    await until(() => container.querySelector('[role="note"]') !== null);
    expect(container.textContent).toContain("nothing here you can preview");
  });

  it("shows a failure with Try again", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(500, { detail: "Server error." }))
      .mockResolvedValue(jsonResponse(200, preview({ text: "back" })));
    await mount(fetchMock);
    await until(() => container.textContent!.includes("Try again"));
    const retry = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Try again",
    )!;
    await act(async () => retry.click());
    await until(() => container.querySelector("pre") !== null);
    await settle();
    expect(container.querySelector("pre")!.textContent).toBe("back");
  });
});

describe("helpers", () => {
  it.each([
    [0, "0 B"],
    [1023, "1023 B"],
    [1024, "1 KB"],
    [1536, "1.5 KB"],
    [5 * 1024 * 1024, "5 MB"],
    [3 * 1024 ** 3, "3 GB"],
    [5000 * 1024 ** 3, "5000 GB"],
  ])("humanSize(%s)", (bytes, text) => expect(humanSize(bytes)).toBe(text));

  it("builds the preview address from the reference", () => {
    expect(
      previewUrl("w", "project_artifact", { event: "e", project: "p" }),
    ).toBe("/api/v1/workspaces/w/previews/project_artifact/?event=e&project=p");
    expect(factRow("pages", 2)).toEqual(["Pages", "2"]);
  });
});
