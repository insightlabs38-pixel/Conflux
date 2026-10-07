import { describe, expect, it } from "vitest";
import { pickRole, rolesIn, roleLabel } from "./roles";

const memberships = [
  { workspace: "w1", role: "participant" },
  { workspace: "w1", role: "judge" },
  { workspace: "w2", role: "organizer" },
  { workspace: "w1", role: "judge" },
  { workspace: "w1", role: "wizard" },
];

describe("roles", () => {
  it("lists the roles held in one workspace, once each, most privileged first", () => {
    expect(rolesIn(memberships, "w1")).toEqual(["judge", "participant"]);
    expect(rolesIn(memberships, "w2")).toEqual(["organizer"]);
    expect(rolesIn(memberships, "w3")).toEqual([]);
    expect(rolesIn(undefined, "w1")).toEqual([]);
  });

  it("shows the requested role only when it is held, else the most privileged", () => {
    const roles = rolesIn(memberships, "w1");
    expect(pickRole(roles, "participant")).toEqual({
      role: "participant",
      requestedUnheld: false,
    });
    expect(pickRole(roles, "")).toEqual({
      role: "judge",
      requestedUnheld: false,
    });
    expect(pickRole(roles, "organizer")).toEqual({
      role: "judge",
      requestedUnheld: true,
    });
    expect(pickRole(roles, "wizard")).toEqual({
      role: "judge",
      requestedUnheld: true,
    });
    expect(pickRole([], "judge")).toEqual({
      role: null,
      requestedUnheld: true,
    });
  });

  it("names a role for people", () => {
    expect(roleLabel("judge")).toBe("Judge");
    expect(roleLabel("admin")).toBe("Organizer (admin)");
  });
});
