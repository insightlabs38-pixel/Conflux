import { describe, expect, it } from "vitest";
import {
  currentMonth,
  dayConditions,
  isMonth,
  monthTitle,
  monthWeeks,
  nextDay,
  shiftMonth,
} from "./calendar";

describe("calendar month arithmetic", () => {
  it("accepts only a real month in the supported years", () => {
    expect(isMonth("2027-03")).toBe(true);
    for (const bad of ["2027-13", "2027-00", "March", "1500-01", "2027-3", ""])
      expect(isMonth(bad)).toBe(false);
  });
  it("steps across year ends and refuses the unsupported", () => {
    expect(shiftMonth("2027-12", 1)).toBe("2028-01");
    expect(shiftMonth("2027-01", -1)).toBe("2026-12");
    expect(shiftMonth("2027-03", 0)).toBe("2027-03");
    expect(shiftMonth("1970-01", -1)).toBeNull();
    expect(shiftMonth("nope", 1)).toBeNull();
  });
  it("reads the current month in UTC", () => {
    expect(currentMonth(new Date("2027-03-31T23:59:59Z"))).toBe("2027-03");
    expect(currentMonth(new Date("2027-04-01T00:00:00Z"))).toBe("2027-04");
  });
  it("lays a month out in Monday-first weeks of seven", () => {
    const march = monthWeeks("2027-03"); // 1 March 2027 is a Monday
    expect(march[0][0]).toBe("2027-03-01");
    expect(march.every((week) => week.length === 7)).toBe(true);
    expect(march.flat().filter(Boolean)).toHaveLength(31);
    const may = monthWeeks("2027-05"); // 1 May 2027 is a Saturday
    expect(may[0].slice(0, 5)).toEqual([null, null, null, null, null]);
    expect(may[0][5]).toBe("2027-05-01");
    const feb = monthWeeks("2028-02"); // leap year
    expect(feb.flat().filter(Boolean)).toHaveLength(29);
  });
  it("names months and days without the browser's zone", () => {
    expect(monthTitle("2027-03")).toBe("March 2027");
    expect(nextDay("2027-02-28")).toBe("2027-03-01");
    expect(nextDay("2027-12-31")).toBe("2028-01-01");
  });
  it("opens a day as two ordinary conditions", () => {
    expect(dayConditions("created_at", "2027-03-03")).toEqual([
      { field: "created_at", op: "gte", value: "2027-03-03" },
      { field: "created_at", op: "lt", value: "2027-03-04" },
    ]);
  });
});
