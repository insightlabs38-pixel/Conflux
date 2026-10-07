import { describe, expect, it } from "vitest";
import cases from "../../../tests/fixtures/initials_cases.json";
import { initials } from "./initials";

describe("initials: the fixtures shared with the server", () => {
  it.each(
    (
      cases as {
        cases: { name: string; name_text: string; initials: string }[];
      }
    ).cases.map((c) => [c.name, c] as const),
  )("%s", (_name, c) => {
    expect(initials(c.name_text)).toBe(c.initials);
  });
  it("tolerates a missing name", () => {
    expect(initials(null)).toBe("?");
    expect(initials(undefined)).toBe("?");
  });
});
