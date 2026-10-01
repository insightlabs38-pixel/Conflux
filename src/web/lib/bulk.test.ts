import { describe, expect, it } from "vitest";
import { ApiError } from "./api";
import { bulkUrl, describeEffect, isRefusal, isStale } from "./bulk";

describe("bulk helpers", () => {
  it("points at the event's planner and classifies failures", () => {
    expect(bulkUrl("w", "e")).toBe(
      "/api/v1/workspaces/w/events/e/operations/bulk/",
    );
    expect(isStale(new ApiError(409, "changed"))).toBe(true);
    expect(isStale(new ApiError(400, "bad"))).toBe(false);
    expect(isRefusal(new ApiError(400, "bad"))).toBe(true);
    expect(isRefusal(new ApiError(403, "no"))).toBe(true);
    // A server error or a dropped connection is not a refusal: retrying may be right.
    expect(isRefusal(new ApiError(503, "down"))).toBe(false);
    expect(isRefusal(new Error("network"))).toBe(false);
  });

  it("describes a track move with names and where the projects came from", () => {
    const effect = {
      action: "move",
      changes: [
        { project: "a", before: null, after: "t2" },
        { project: "b", before: "t1", after: "t2" },
        { project: "c", before: "t1", after: "t2" },
      ],
    };
    expect(
      describeEffect(effect, { tracks: { t1: "Software", t2: "Hardware" } }),
    ).toBe("Move 3 projects to Hardware (1 from no track, 2 from Software).");
    expect(
      describeEffect(
        {
          action: "move",
          changes: [{ project: "a", before: "zz", after: "t2" }],
        },
        {
          tracks: { t2: "Hardware" },
        },
      ),
    ).toBe("Move 1 project to Hardware (1 from another track).");
  });

  it("describes the other built-in actions and still says something honest for an unknown one", () => {
    expect(describeEffect({ action: "advance", advanced: [1, 2] })).toBe(
      "Advance 2 entries to the next stage.",
    );
    expect(describeEffect({ action: "extend", changes: [1] })).toBe(
      "Extend 1 gate.",
    );
    expect(describeEffect({ action: "assign", pairs: [1, 2, 3] })).toBe(
      "Assign judges to projects: 3 pairings.",
    );
    expect(describeEffect({ action: "send", recipient_count: 1 })).toBe(
      "Send a message to 1 recipient.",
    );
    expect(describeEffect({ action: "hide_projects" })).toBe(
      "Run hide projects.",
    );
  });
});
