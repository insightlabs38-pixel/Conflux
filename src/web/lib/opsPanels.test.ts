import { afterEach, describe, expect, it } from "vitest";
import { firstOpsPanel, opsPanelsFor, registerOpsPanel } from "./opsPanels";

const Nothing = () => null;
const added: (() => void)[] = [];
afterEach(() => added.splice(0).forEach((remove) => remove()));

describe("operations panels", () => {
  it("offers a panel only to who it is for, and a later workflow can register one", () => {
    added.push(
      registerOpsPanel({
        id: "t-org",
        label: "Org",
        when: (w) => w.organizer,
        Panel: Nothing,
      }),
      registerOpsPanel({ id: "t-all", label: "All", Panel: Nothing }),
    );
    const org = opsPanelsFor({ organizer: true }).map((p) => p.id);
    const other = opsPanelsFor({ organizer: false }).map((p) => p.id);
    expect(org).toContain("t-org");
    expect(other).not.toContain("t-org");
    expect(other).toContain("t-all");
    expect(firstOpsPanel({ organizer: false })).toBe(other[0]);
  });
});
