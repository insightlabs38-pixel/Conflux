import { describe, expect, it } from "vitest";
import { shareableHref } from "./shareLink";

const O = "https://conflux.example";

describe("shareable link", () => {
  it("rebuilds the exact operational context from a workspace location", () => {
    expect(
      shareableHref(
        "/app/w/w1/participants",
        "?section=ProjectsGrid&event=e1&view_projects=v1&sort_projects=-name&page_projects=3&size_projects=50&row_projects=r1",
        O,
      ),
    ).toBe(
      `${O}/app/w/w1/participants?event=e1&page_projects=3&row_projects=r1&size_projects=50&sort_projects=-name&view_projects=v1&section=ProjectsGrid`,
    );
  });

  it("is stable: a link opened and shared again is the same link", () => {
    const first = shareableHref(
      "/app/w/w1/judging",
      "?stage=s1&event=e1&as=judge&plan=p1",
      O,
    )!;
    const url = new URL(first);
    expect(shareableHref(url.pathname, url.search, O)).toBe(first);
  });

  it("never carries the single-use invite token, typed text or an unsafe value", () => {
    const href = shareableHref(
      "/app/w/w1/overview",
      "?event=e1&invite=SECRET&q=ada%20lovelace&x=%3Cb%3E&as=judge",
      O,
    )!;
    expect(href).not.toContain("SECRET");
    expect(href).not.toContain("ada");
    expect(href).not.toContain("%3C");
    expect(href).toContain("event=e1");
    expect(href).toContain("as=judge");
  });

  it("works without the gateway base path and returns null away from a workspace view", () => {
    expect(shareableHref("/w/w1/queue", "", O)).toBe(`${O}/w/w1/queue`);
    expect(shareableHref("/app/person/p1", "", O)).toBeNull();
    expect(shareableHref("/app/", "", O)).toBeNull();
    expect(shareableHref("/event/e1", "", O)).toBeNull();
  });
});

describe("a transient view in a shared link", () => {
  const encoded =
    "eyJmaWVsZCI6ImdhbGxlcnlfdmlzaWJsZSIsIm9wIjoiZXEiLCJ2YWx1ZSI6dHJ1ZX0".repeat(
      8,
    ); // 480 characters
  it("keeps an encoded filter of up to 1,500 URL-safe characters and drops anything else under that key", () => {
    const kept = shareableHref(
      "/app/w/w1/participants",
      `?event=e1&f_projects=${encoded}&section=ProjectsGrid`,
      O,
    )!;
    expect(kept).toContain(`f_projects=${encoded}`);
    expect(
      shareableHref(
        "/app/w/w1/participants",
        "?event=e1&f_projects=has%20space%3Cb%3E",
        O,
      ),
    ).not.toContain("f_projects");
    expect(
      shareableHref(
        "/app/w/w1/participants",
        `?event=e1&f_projects=${"a".repeat(1501)}`,
        O,
      ),
    ).not.toContain("f_projects");
    // an ordinary param keeps the short rule
    expect(
      shareableHref(
        "/app/w/w1/participants",
        `?event=e1&sort_projects=${"a".repeat(101)}`,
        O,
      ),
    ).not.toContain("sort_projects");
  });
});
