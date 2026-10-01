import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import cases from "../../../tests/fixtures/rich_cases.json";
import { RichDoc } from "../components/RichDoc";
import { plainText, safeHref, type RichTree } from "./rich";

type Case = { name: string; profile: string; source: string; tree: RichTree };
const all = (cases as { cases: Case[] }).cases;
const draw = (tree: RichTree) => renderToStaticMarkup(<RichDoc tree={tree} />);
const named = (name: string) => all.find((c) => c.name === name)!;

describe("rich content: the server's trees, drawn", () => {
  it.each(all.map((c) => [c.name, c] as const))(
    "%s draws nothing active",
    (_name, c) => {
      const html = draw(c.tree);
      expect(html).not.toMatch(/<(script|iframe|img|svg|style)/i);
      expect(html).not.toMatch(/<[^>]*\son\w+=/i);
      for (const [, href] of html.matchAll(/href="([^"]*)"/g))
        expect(safeHref(href.replace(/&amp;/g, "&"))).toBe(true);
    },
  );

  it("draws the structure the tree names", () => {
    expect(draw(named("table with alignment").tree)).toBe(
      '<div class="cx-rich"><div class="cx-rich__table" role="region" tabindex="0" aria-label="Table"><table>' +
        '<thead><tr><th scope="col" style="text-align:left">T</th><th scope="col" style="text-align:right">R</th></tr></thead>' +
        '<tbody><tr><td style="text-align:left">a</td><td style="text-align:right">b</td></tr></tbody></table></div></div>',
    );
    expect(draw(named("loose ordered list from 3").tree)).toContain(
      '<ol start="3"><li><p>one</p></li>',
    );
    expect(draw(named("nested list").tree)).toContain(
      "<li>a<ul><li>b</li></ul></li>",
    );
    expect(draw(named("headings are demoted").tree)).toBe(
      '<div class="cx-rich"><h2>One</h2><h3>Two</h3><h6>Six</h6></div>',
    );
    expect(draw(named("hard break and rule").tree)).toContain(
      "<p>a<br/>b</p><hr/>",
    );
  });

  it("draws code as highlighted text in a focusable group, never as markup", () => {
    const html = draw(named("fenced code with language").tree);
    expect(html).toContain('role="group" aria-label="python code"');
    expect(html).toContain('tabindex="0"');
    expect(html).toContain('<span class="cx-tok cx-tok-nb">print</span>');
    const hostile = draw(named("fenced code in an unknown language").tree);
    expect(hostile).toContain("&lt;img src=x onerror=alert(1)&gt;");
  });

  it("keeps text that looks like markup as text", () => {
    expect(draw(named("raw html stays text").tree)).toContain(
      "&lt;script&gt;alert(1)&lt;/script&gt; &lt;b&gt;x&lt;/b&gt;",
    );
  });

  it("links open safely and only on the three schemes", () => {
    const html = draw(named("safe links").tree);
    expect(html.match(/rel="noopener noreferrer nofollow"/g)).toHaveLength(4);
    expect(draw(named("ftp link is text").tree)).not.toContain("<a ");
  });

  it("does not draw a node it does not know, and unsafe links as plain text", () => {
    const tree = {
      type: "doc",
      children: [
        { type: "script", text: "x" },
        {
          type: "paragraph",
          children: [
            {
              type: "link",
              href: "javascript:alert(1)",
              children: [{ type: "text", text: "go" }],
            },
          ],
        },
      ],
    } as unknown as RichTree;
    expect(draw(tree)).toBe('<div class="cx-rich"><p>go</p></div>');
  });

  it("names a standalone region and leaves an embedded one alone", () => {
    const tree = named("plain paragraph").tree;
    expect(
      renderToStaticMarkup(<RichDoc tree={tree} label="Story preview" />),
    ).toContain('role="region" aria-label="Story preview"');
    expect(draw(tree)).not.toContain("role=");
  });

  it("reads the plain text of a tree", () => {
    expect(plainText(named("inline marks").tree)).toBe(
      "Uses pytest, em and strong.\n",
    );
  });
});

describe("safeHref", () => {
  it.each([
    ["https://e.com", true],
    ["HTTP://e.com", true],
    ["mailto:a@e.com", true],
    ["/relative", true],
    ["#anchor", true],
    ["javascript:alert(1)", false],
    [" JavaScript:alert(1)", false],
    ["data:text/html,x", false],
    ["ftp://e.com", false],
  ])("%s", (href, safe) => expect(safeHref(href)).toBe(safe));
});
