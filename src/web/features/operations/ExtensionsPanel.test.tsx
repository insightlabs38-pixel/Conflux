// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ExtensionsPanel } from "./ExtensionsPanel";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import { requirementText, type Extensions } from "../../lib/extensions";

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

const INVENTORY: Extensions = {
  api_version: 1,
  supported_api_versions: [1],
  manifests: [
    {
      id: "core",
      version: "1.0.0",
      label: "Platform core",
      api_version: 1,
      provides: [
        { kind: "rich_profile", id: "page", label: "Page", state: "live" },
      ],
      requires: [],
    },
    {
      id: "presentation",
      version: "1.0.0",
      label: "Presentation",
      api_version: 1,
      provides: [
        { kind: "page_block", id: "hero", label: "Hero", state: "live" },
        {
          kind: "archive_exporter",
          id: "full",
          label: "full",
          state: "declared",
        },
      ],
      requires: [{ kind: "manifest", id: "core" }],
    },
  ],
  capabilities: [
    {
      kind: "page_block",
      label: "Page block",
      description: "A block organizers place on the public page.",
      declared_only: false,
      entries: [{ id: "hero", label: "Hero", manifest: "presentation" }],
    },
    {
      kind: "archive_exporter",
      label: "Archive exporter",
      description: "A format the archive exports to.",
      declared_only: true,
      entries: [{ id: "full", label: "full", manifest: "presentation" }],
    },
  ],
  problems: [],
  ok: true,
};

const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
async function mount(response: () => Response) {
  const urls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      urls.push(String(url));
      return response();
    }),
  );
  await act(async () =>
    root.render(withQuery(<ExtensionsPanel workspaceId="w" />)),
  );
  await settle();
  return urls;
}

describe("ExtensionsPanel", () => {
  it("lists the sources and capabilities read-only and says they agree", async () => {
    const urls = await mount(() => jsonResponse(200, INVENTORY));
    expect(urls).toEqual(["/api/v1/workspaces/w/extensions/"]);
    expect(container.textContent).toContain("Consistent");
    expect(container.textContent).toContain("Platform core");
    expect(container.textContent).toContain("Presentation");
    expect(container.textContent).toContain("Page block (1)");
    expect(container.textContent).toContain(
      "Archive exporter (1) · declared only",
    );
    expect(container.textContent).toContain("Hero (hero) · presentation");
    expect(container.querySelector("button")).toBeNull(); // nothing to install or change
    expect(container.querySelector("input")).toBeNull();
  });

  it("reports errors as an alert and warnings as a status, each with the source", async () => {
    await mount(() =>
      jsonResponse(200, {
        ...INVENTORY,
        ok: false,
        problems: [
          {
            code: "not_registered",
            severity: "error",
            manifest: "presentation",
            message: "Declares 'page_block:ghost' but nothing is registered.",
          },
          {
            code: "unclaimed",
            severity: "warning",
            manifest: null,
            message:
              "'page_block:x' is registered but no manifest declares it.",
          },
        ],
      }),
    );
    const alert = container.querySelector('[role="alert"]')!;
    expect(alert.textContent).toContain("Inconsistent");
    expect(alert.textContent).toContain("2 findings");
    const items = [...alert.querySelectorAll("li")].map((li) => li.textContent);
    expect(items[0]).toContain("presentation: Declares 'page_block:ghost'");
    expect(items[1]).toContain("warning");
  });

  it("shows warnings alone as something to look at rather than a failure", async () => {
    await mount(() =>
      jsonResponse(200, {
        ...INVENTORY,
        problems: [
          {
            code: "unclaimed",
            severity: "warning",
            manifest: null,
            message:
              "'page_block:x' is registered but no manifest declares it.",
          },
        ],
      }),
    );
    expect(container.querySelector('[role="alert"]')).toBeNull();
    expect(container.querySelector('[role="status"]')!.textContent).toContain(
      "Needs a look",
    );
    expect(container.textContent).toContain("1 finding.");
  });

  it("shows a retryable error when the inventory cannot be read", async () => {
    await mount(() => jsonResponse(403, { detail: "no" }));
    expect(container.querySelector('[role="alert"]')).not.toBeNull();
    expect(container.textContent).not.toContain("Consistent");
  });

  it("names a requirement on another source plainly and on a capability with its kind", () => {
    expect(requirementText({ kind: "manifest", id: "core" })).toBe("core");
    expect(requirementText({ kind: "page_block", id: "hero" })).toBe(
      "page_block: hero",
    );
  });
});
