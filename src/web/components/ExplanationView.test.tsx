import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import cases from "../../../tests/fixtures/explain_cases.json";
import type { Explanation } from "../lib/explain";
import { fixLabel } from "../lib/explain";
import { ExplanationView } from "./ExplanationView";

type Case = { name: string; adapter: string; output: Explanation };
const all = (cases as { cases: Case[] }).cases;
const draw = (e: Explanation, alert = false) =>
  renderToStaticMarkup(<ExplanationView explanation={e} alert={alert} />);
const named = (name: string) => all.find((c) => c.name === name)!.output;

describe("ExplanationView draws the explanations the server produced", () => {
  it.each(all.map((c) => [c.name, c.output] as const))("%s", (_name, e) => {
    const html = draw(e);
    expect(html).toContain(e.summary.replace(/'/g, "&#x27;"));
    expect((html.match(/<li/g) ?? []).length).toBe(e.reasons.length);
    expect(html).not.toMatch(/<(script|img|iframe)/i);
    for (const reason of e.reasons)
      expect(html).toContain(
        reason.message.replace(/&/g, "&amp;").replace(/'/g, "&#x27;"),
      );
  });

  it("names the outcome and each severity in words", () => {
    const html = draw(named("readiness: blockers first, then warnings"));
    expect(html).toContain("Blocked");
    expect(html).toContain("Blocker");
    expect(html).toContain("Warning");
    expect(draw(named("readiness: warnings need a look"))).toContain(
      "Needs attention",
    );
    expect(draw(named("readiness: nothing open"))).toContain("Allowed");
  });

  it("says where a reason is resolved", () => {
    const html = draw(named("readiness: blockers first, then warnings"));
    expect(html).toContain("Resolve in setup › Settings");
    expect(html).toContain("Resolve in judging › Rubric");
    expect(fixLabel({ destination: "operations", section: null })).toBe(
      "operations",
    );
  });

  it("announces a blocked outcome only when asked to", () => {
    const blocked = named("consequences: refused");
    expect(draw(blocked, true)).toContain('role="alert"');
    expect(draw(blocked)).not.toContain('role="alert"');
    expect(draw(named("consequences: reversible"), true)).not.toContain(
      'role="alert"',
    );
  });

  it("keeps a reason that looks like markup as text and says when reasons were left out", () => {
    const html = draw({
      outcome: "blocked",
      summary: "<b>No</b>",
      reasons: [
        {
          code: "x",
          severity: "blocker",
          message: "<script>alert(1)</script>",
        },
      ],
      total: 60,
      truncated: true,
    });
    expect(html).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
    expect(html).not.toContain("<script");
    expect(html).toContain("Showing 1 of 60 reasons.");
  });

  it("an explanation without reasons draws only its summary", () => {
    const html = draw({
      outcome: "unknown",
      summary: "Not decided yet.",
      reasons: [],
      total: 0,
      truncated: false,
    });
    expect(html).toContain("Not decided");
    expect(html).not.toContain("<ul");
  });
});
