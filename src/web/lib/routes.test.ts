import { describe, expect, it } from "vitest";
import {
  appBasename,
  legacyTarget,
  parseWorkspaceLocation,
  routes,
} from "./routes";

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

describe("route targets", () => {
  it("builds one URL per place, in a fixed order", () => {
    expect(routes.target("w1", { view: "queue" })).toBe("/w/w1/queue");
    expect(
      routes.target("w1", {
        view: "judging",
        section: "rubrics",
        event: "e1",
        params: { stage: "s1", plan: "p1" },
      }),
    ).toBe("/w/w1/judging?event=e1&stage=s1&plan=p1&section=rubrics");
    expect(
      routes.target("w1", {
        view: "judging",
        params: { stage: "s1", plan: "p1" },
        event: "e1",
      }),
    ).toBe(
      routes.target("w1", {
        view: "judging",
        event: "e1",
        params: { plan: "p1", stage: "s1" },
      }),
    );
    expect(routes.target("a b", { view: "overview", event: "" })).toBe(
      "/w/a%20b/overview",
    );
  });

  it("refuses typed text, personal data and reserved names in a URL", () => {
    expect(() =>
      routes.target("w1", { view: "x", params: { q: "ada lovelace" } }),
    ).toThrow(TypeError);
    expect(() =>
      routes.target("w1", { view: "x", event: "a@b.example" }),
    ).toThrow(TypeError);
    expect(() =>
      routes.target("w1", { view: "x", params: { Name: "v" } }),
    ).toThrow(TypeError);
    expect(() =>
      routes.target("w1", { view: "x", params: { section: "s" } }),
    ).toThrow(TypeError);
  });

  it("reads a workspace location back into the same target", () => {
    const target = {
      view: "judging",
      section: "rubrics",
      event: "e1",
      params: { plan: "p1", stage: "s1" },
    };
    const url = routes.target("w 1", target);
    const [path, search] = url.split("?");
    expect(parseWorkspaceLocation(path, `?${search}`)).toEqual({
      workspaceId: "w 1",
      target,
    });
  });

  it("treats the bare workspace as its overview and ignores unsafe params and other pages", () => {
    expect(parseWorkspaceLocation("/w/w1", "")?.target).toEqual({
      view: "overview",
    });
    expect(
      parseWorkspaceLocation("/w/w1/queue", "?q=ada%20lovelace&event=e1")
        ?.target,
    ).toEqual({ view: "queue", event: "e1" });
    expect(parseWorkspaceLocation("/person/p1", "")).toBeNull();
    expect(parseWorkspaceLocation("/w/%E0%A4%A/queue", "")).toBeNull();
    expect(parseWorkspaceLocation("/w/w1/queue/extra", "")).toBeNull();
  });
});
