import { describe, expect, it } from "vitest";
import { countOf, currentSelection, publishSelection } from "./selection";

const snap = (entity: string, count: number) => ({
  entity,
  noun: entity,
  count,
  commands: [],
});

describe("selection", () => {
  it("offers the most recently changed non-empty list and withdraws an emptied one", () => {
    publishSelection("a", snap("projects", 2));
    publishSelection("b", snap("applications", 1));
    expect(currentSelection()?.entity).toBe("applications");
    publishSelection("a", snap("projects", 3));
    expect(currentSelection()?.entity).toBe("projects");
    publishSelection("a", null);
    expect(currentSelection()?.entity).toBe("applications");
    publishSelection("b", snap("applications", 0)); // empty counts as nothing
    expect(currentSelection()).toBeNull();
  });

  it("fits the list's name to a count", () => {
    expect(countOf(1, "Projects")).toBe("1 project");
    expect(countOf(3, "Projects")).toBe("3 projects");
    expect(countOf(1, "Staff")).toBe("1 staff");
  });
});
