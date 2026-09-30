import { describe, expect, it } from "vitest";
import {
  canonicalFilter,
  entityBase,
  entityUrl,
  isGroup,
  type FilterNode,
} from "./entityQuery";

describe("entity query helpers", () => {
  it("writes the canonical filter text: sorted keys, no spaces, nested too", () => {
    const filter: FilterNode = {
      and: [
        { value: "waitlisted", op: "eq", field: "status" },
        { not: { op: "contains", field: "note", value: "x y" } },
      ],
    };
    expect(canonicalFilter(filter)).toBe(
      '{"and":[{"field":"status","op":"eq","value":"waitlisted"},{"not":{"field":"note","op":"contains","value":"x y"}}]}',
    );
    // Same filter written in another key order is the same text (what URLs and saved views store).
    expect(canonicalFilter({ op: "eq", field: "status", value: "a" })).toBe(
      canonicalFilter({ field: "status", value: "a", op: "eq" }),
    );
  });

  it("builds the page URL from only what was asked for", () => {
    const base = entityBase("w", "e");
    expect(base).toBe("/api/v1/workspaces/w/events/e/entities/");
    expect(entityUrl(base, "applications")).toBe(`${base}applications/`);
    const url = entityUrl(base, "applications", {
      filter: { field: "status", op: "eq", value: "pending" },
      sort: "-created_at",
      columns: ["username", "status"],
      limit: 10,
      offset: 20,
    });
    const parsed = new URL(url, "http://x");
    expect(parsed.pathname).toBe(`${base}applications/`);
    expect(parsed.searchParams.get("filter")).toBe(
      '{"field":"status","op":"eq","value":"pending"}',
    );
    expect(parsed.searchParams.get("sort")).toBe("-created_at");
    expect(parsed.searchParams.get("columns")).toBe("username,status");
    expect(parsed.searchParams.get("limit")).toBe("10");
    expect(parsed.searchParams.get("offset")).toBe("20");
    // A zero offset and an empty column list are not sent.
    expect(entityUrl(base, "projects", { offset: 0, columns: [] })).toBe(
      `${base}projects/`,
    );
  });

  it("tells groups from conditions", () => {
    expect(isGroup({ and: [] })).toBe(true);
    expect(isGroup({ not: { field: "a", op: "eq", value: 1 } })).toBe(true);
    expect(isGroup({ field: "a", op: "eq", value: 1 })).toBe(false);
  });
});
