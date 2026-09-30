import { describe, expect, it } from "vitest";
import {
  definitionQuery,
  EMPTY_DEFINITION,
  sameDefinition,
  viewsBase,
} from "./savedViews";

describe("saved view helpers", () => {
  it("points at the event's views and turns a definition into an entity query", () => {
    expect(viewsBase("w", "e")).toBe("/api/v1/workspaces/w/events/e/views/");
    expect(
      definitionQuery({
        filter: { field: "a", op: "eq", value: 1 },
        sort: "-a",
        columns: ["a"],
        density: "compact",
      }),
    ).toEqual({
      filter: { field: "a", op: "eq", value: 1 },
      sort: "-a",
      columns: ["a"],
    });
  });

  it("compares definitions by meaning, not by key order", () => {
    const a = {
      ...EMPTY_DEFINITION,
      filter: { op: "eq", field: "status", value: "x" },
    };
    const b = {
      ...EMPTY_DEFINITION,
      filter: { field: "status", value: "x", op: "eq" },
    };
    expect(sameDefinition(a, b)).toBe(true);
    expect(sameDefinition(a, { ...b, sort: "status" })).toBe(false);
    expect(sameDefinition(a, { ...b, columns: ["status"] })).toBe(false);
    expect(sameDefinition(a, { ...b, density: "compact" })).toBe(false);
    expect(sameDefinition(EMPTY_DEFINITION, a)).toBe(false);
  });
});
