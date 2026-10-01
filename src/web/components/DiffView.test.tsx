import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import cases from "../../../tests/fixtures/diff_cases.json";
import type { Diff } from "../lib/versions";
import { pathLabel, summary } from "../lib/versions";
import { DiffView } from "./DiffView";

type Case = { name: string; kind: string; diff: Diff };
const all = (cases as { cases: Case[] }).cases;
const draw = (diff: Diff) => renderToStaticMarkup(<DiffView diff={diff} />);
const named = (name: string) => all.find((c) => c.name === name)!.diff;

describe("DiffView draws the diffs the server produced", () => {
  it.each(all.map((c) => [c.name, c.diff] as const))("%s", (_name, diff) => {
    const html = draw(diff);
    expect(html).toContain(summary(diff));
    expect(html).not.toMatch(/<(script|img|iframe)/i);
    if (diff.kind === "json")
      expect((html.match(/cx-diff__change /g) ?? []).length).toBe(
        diff.changes.length,
      );
  });

  it("says what happened in words, not only by colour", () => {
    const html = draw(named("keys added and removed in key order"));
    expect(html).toContain('<span class="cx-diff__op">Added</span>');
    expect(html).toContain('<span class="cx-diff__op">Removed</span>');
    expect(html).toContain(">a<");
    expect(html).toContain("2 changes.");
  });

  it("shows a changed value as before and after for assistive technology", () => {
    const html = draw(named("a scalar changed"));
    expect(html).toContain("<del>");
    expect(html).toContain("Before: ");
    expect(html).toContain("&quot;A&quot;");
    expect(html).toContain("<ins>");
    expect(html).toContain("After: ");
    expect(html).toContain("&quot;B&quot;");
  });

  it("reads a pointer as a path and a move as positions", () => {
    expect(pathLabel("/fields/2/label")).toBe("fields › 2 › label");
    expect(pathLabel("/a~1b/c~0d")).toBe("a/b › c~d");
    expect(pathLabel("")).toBe("(whole value)");
    const html = draw(named("keyed list: one item moved to the front"));
    expect(html).toContain("Moved");
    expect(html).toContain("from position 3 to 1");
  });

  it("draws text hunks with line numbers, marks and Added and Removed for assistive technology", () => {
    const html = draw(named("one line changed"));
    expect(html).toContain("<del");
    expect(html).toContain("Removed: ");
    expect(html).toContain("<ins");
    expect(html).toContain("Added: ");
    expect(html).toContain('tabindex="0"');
    expect(html).toContain("1 added, 1 removed.");
  });

  it("keeps text that looks like markup as text", () => {
    const diff: Diff = {
      kind: "text",
      added: 1,
      removed: 0,
      truncated: false,
      hunks: [
        {
          lines: [
            {
              op: "add",
              text: "<script>alert(1)</script>",
              before_line: null,
              after_line: 1,
            },
          ],
        },
      ],
    };
    const html = draw(diff);
    expect(html).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
    expect(html).not.toContain("<script");
  });

  it("says when a value was shortened and when a list of changes is cut off", () => {
    const html = draw({
      kind: "json",
      total: 600,
      truncated: true,
      changes: [
        {
          path: "/v",
          op: "changed",
          before: "aaa…",
          after: "bbb…",
          clipped: true,
        },
      ],
    });
    expect(html).toContain("(shortened)");
    expect(html).toContain("Showing 1 of 600 changes.");
  });

  it("names the group for assistive technology", () => {
    expect(
      renderToStaticMarkup(
        <DiffView diff={named("nothing changed")} label="Changes to name" />,
      ),
    ).toContain('role="group" aria-label="Changes to name"');
    expect(summary(named("nothing changed"))).toBe("No differences.");
  });
});
