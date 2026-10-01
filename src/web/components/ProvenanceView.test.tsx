// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  asProvenance,
  changeSummary,
  sha256Hex,
  type Provenance,
} from "../lib/provenance";
import { ProvenanceView } from "./ProvenanceView";

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
});

const FILE = new TextEncoder().encode('{"event":"x"}');
// A digest for the display tests; the file check below computes a real one.
const SHA = "a".repeat(64);

const record = (over: Partial<Provenance> = {}): Provenance => ({
  version: 1,
  by: { public_id: "u1", username: "org" },
  at: "2026-10-01T10:00:00Z",
  source: { kind: "archive_export", id: "j1" },
  inputs: {
    digest: null,
    refs: [{ kind: "event", id: "e1", label: "Spring Jam" }],
  },
  rules: { name: "event_archive", version: 4 },
  output: { name: "spring-config-archive.json", bytes: 2048, sha256: SHA },
  summary: "Config archive of Spring Jam.",
  changes: null,
  ...over,
});
const show = (value: Provenance) =>
  act(async () => root.render(<ProvenanceView provenance={value} />));

describe("ProvenanceView", () => {
  it("shows who made it, from what, under which rules and the file's digest", async () => {
    await show(record());
    const text = container.textContent!;
    expect(text).toContain("Config archive of Spring Jam.");
    expect(text).toContain("org");
    expect(text).toContain("archive_export j1");
    expect(text).toContain("Spring Jam");
    expect(text).toContain("event_archive (version 4)");
    expect(text).toContain("spring-config-archive.json (2 KB)");
    expect(text).toContain(SHA);
    expect(container.querySelector("time")!.getAttribute("datetime")).toBe(
      "2026-10-01T10:00:00Z",
    );
  });

  it("names the system when nobody did it and hides what is absent", async () => {
    await show(
      record({
        by: null,
        output: null,
        rules: null,
        inputs: { digest: null, refs: [] },
      }),
    );
    expect(container.textContent).toContain("The system");
    expect(container.textContent).not.toContain("SHA-256");
    expect(container.textContent).not.toContain("Rules");
    expect(container.querySelector("input[type=file]")).toBeNull();
    await show(
      record({ inputs: { digest: "d".repeat(64), refs: [] }, output: null }),
    );
    expect(container.textContent).toContain("Inputs digest");
  });

  it("summarises the changes of a restore", async () => {
    const changes = { total: 3, added: 1, removed: 0, changed: 2, moved: 0 };
    expect(changeSummary(changes)).toBe("3 changes (1 added, 2 changed)");
    expect(
      changeSummary({ total: 1, added: 0, removed: 0, changed: 1, moved: 0 }),
    ).toBe("1 change (1 changed)");
    await show(record({ changes, output: null }));
    expect(container.textContent).toContain("3 changes (1 added, 2 changed)");
  });

  it("keeps text that looks like markup as text", async () => {
    await show(
      record({
        summary: "<script>alert(1)</script>",
        inputs: {
          digest: null,
          refs: [{ kind: "x", id: "1", label: "<img src=x onerror=alert(1)>" }],
        },
      }),
    );
    expect(container.querySelector("script, img")).toBeNull();
    expect(container.textContent).toContain("<script>alert(1)</script>");
  });

  it("checks a picked file against the recorded digest, locally", async () => {
    const real = await sha256Hex(FILE.buffer as ArrayBuffer);
    expect(real).toMatch(/^[0-9a-f]{64}$/);
    await show(
      record({ output: { name: "a.json", bytes: FILE.length, sha256: real! } }),
    );
    const input =
      container.querySelector<HTMLInputElement>("input[type=file]")!;
    const pick = async (bytes: Uint8Array) => {
      const file = new File([new Uint8Array(bytes)], "a.json");
      Object.defineProperty(input, "files", {
        value: [file],
        configurable: true,
      });
      await act(async () => {
        input.dispatchEvent(new Event("change", { bubbles: true }));
        await new Promise((r) => setTimeout(r, 20));
      });
    };
    await pick(FILE);
    expect(container.querySelector('[role="status"]')!.textContent).toBe(
      "This is exactly the file recorded here.",
    );
    await pick(new TextEncoder().encode('{"event":"y"}'));
    expect(container.querySelector('[role="status"]')!.textContent).toBe(
      "This is not the file recorded here.",
    );
  });
});

describe("asProvenance", () => {
  it("accepts a record and refuses anything else", () => {
    expect(asProvenance(record())).not.toBeNull();
    for (const bad of [
      null,
      undefined,
      5,
      "x",
      {},
      { summary: "s" },
      { ...record(), inputs: {} },
    ])
      expect(asProvenance(bad)).toBeNull();
  });
});
