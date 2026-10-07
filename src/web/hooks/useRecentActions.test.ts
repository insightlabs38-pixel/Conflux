import { describe, expect, it } from "vitest";
import { actionWords, ago } from "./useRecentActions";

describe("recent actions", () => {
  it("reads an audit action as words", () => {
    expect(actionWords("event.status_changed")).toBe("Event status changed");
    expect(actionWords("membership.granted")).toBe("Membership granted");
    expect(actionWords("")).toBe("Action");
    expect(actionWords("__x__")).toBe("X");
  });

  it("says how long ago in the coarsest honest unit", () => {
    const now = Date.parse("2027-03-10T12:00:00Z");
    const at = (ms: number) => new Date(now - ms).toISOString();
    expect(ago(at(10_000), now)).toBe("just now");
    expect(ago(at(5 * 60_000), now)).toBe("5 min ago");
    expect(ago(at(3 * 3_600_000), now)).toBe("3 h ago");
    expect(ago(at(2 * 86_400_000), now)).toBe("2 d ago");
    expect(ago(at(30 * 86_400_000), now)).toMatch(/Feb/);
    expect(ago("not a date", now)).toBe("");
    expect(ago(at(-5000), now)).toBe("just now"); // a clock a little ahead is not the future
  });
});
