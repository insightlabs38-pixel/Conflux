import { describe, expect, it } from "vitest";
import { appBasename, legacyTarget, routes } from "./routes";

describe("routes", () => {
  it("builds canonical paths and encodes ids", () => {
    expect(routes.workspace("w 1", "queue")).toBe("/w/w%201/queue");
    expect(routes.workspace("w1")).toBe("/w/w1/overview");
    expect(routes.person("p/1")).toBe("/person/p%2F1");
    expect(routes.publicEvent("e1")).toBe("/event/e1");
  });

  it("detects the gateway base path only for /app", () => {
    expect(appBasename("/app/")).toBe("/app");
    expect(appBasename("/app/w/w1/queue")).toBe("/app");
    expect(appBasename("/app")).toBe("/app");
    expect(appBasename("/")).toBe("");
    expect(appBasename("/application/x")).toBe("");
  });
});

describe("legacy URL compatibility", () => {
  it.each([
    ["?workspace=w1", "/w/w1/overview"],
    ["?workspace=w1&view=queue", "/w/w1/queue"],
    ["?workspace=w1&view=team&event=e1", "/w/w1/team?event=e1"],
    ["?workspace=w1&event=e1&invite=tok", "/w/w1/overview?event=e1&invite=tok"],
    ["?workspace=w1&view=queue&noise=1", "/w/w1/queue"],
    ["?event=e1", "/event/e1"],
    ["?person=p1", "/person/p1"],
    ["?person=p1&workspace=w1", "/person/p1"],
    ["?api=explorer", "/api-explorer"],
    ["?api=explorer&workspace=w1", "/api-explorer"],
    ["?workspace=a%20b", "/w/a%20b/overview"],
  ])("%s -> %s", (search, expected) => {
    expect(legacyTarget(search)).toBe(expected);
  });

  it.each([
    "",
    "?",
    "?view=queue",
    "?invite=tok",
    "?api=other",
    "?unrelated=1",
  ])("leaves %j alone", (search) => {
    expect(legacyTarget(search)).toBeNull();
  });
});
