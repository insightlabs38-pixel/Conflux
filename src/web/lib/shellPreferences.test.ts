// @vitest-environment happy-dom
import { beforeEach, describe, expect, it } from "vitest";
import {
  MAX_FAVORITES,
  MAX_RECENTS,
  clearShellPreferences,
  favoriteEvents,
  recentCommands,
  recentEvents,
  densityPreference,
  MAX_PINS,
  pinnedViews,
  rememberCommand,
  rememberEvent,
  setDensityPreference,
  setThemePreference,
  themePreference,
  toggleFavoriteEvent,
  togglePinnedView,
} from "./shellPreferences";

beforeEach(() => window.localStorage.clear());

describe("shell preferences", () => {
  it("stores favorites per person and workspace, in the order starred", () => {
    toggleFavoriteEvent("u1", "w1", "e1");
    toggleFavoriteEvent("u1", "w1", "e2");
    toggleFavoriteEvent("u2", "w1", "e9");
    expect(favoriteEvents("u1", "w1")).toEqual(["e1", "e2"]);
    expect(favoriteEvents("u1", "w2")).toEqual([]);
    expect(favoriteEvents("u2", "w1")).toEqual(["e9"]);
    toggleFavoriteEvent("u1", "w1", "e1");
    expect(favoriteEvents("u1", "w1")).toEqual(["e2"]);
  });

  it("refuses a thirteenth favorite and says so", () => {
    for (let i = 0; i < MAX_FAVORITES; i++)
      expect(toggleFavoriteEvent("u", "w", `e${i}`)).toBe(true);
    expect(toggleFavoriteEvent("u", "w", "extra")).toBe(false);
    expect(favoriteEvents("u", "w")).toHaveLength(MAX_FAVORITES);
  });

  it("keeps the newest recents first, once each, capped", () => {
    for (let i = 0; i < MAX_RECENTS + 3; i++) rememberEvent("u", "w", `e${i}`);
    rememberEvent("u", "w", "e5");
    const recents = recentEvents("u", "w");
    expect(recents).toHaveLength(MAX_RECENTS);
    expect(recents[0]).toBe("e5");
    expect(new Set(recents).size).toBe(recents.length);
  });

  it("reads damaged or hostile storage as empty and never stores a non-id", () => {
    window.localStorage.setItem("conflux:v1:u:w:favorite-events", "{not json");
    expect(favoriteEvents("u", "w")).toEqual([]);
    window.localStorage.setItem(
      "conflux:v1:u:w:recent-events",
      JSON.stringify(["ok", "has space", 5, { a: 1 }, "<b>x</b>", "ok"]),
    );
    expect(recentEvents("u", "w")).toEqual(["ok"]);
    rememberEvent("u", "w", "not an id");
    toggleFavoriteEvent("u", "w", "a@b.example");
    expect(favoriteEvents("u", "w")).toEqual([]);
    expect(recentEvents("u", "w")).toEqual(["ok"]);
  });

  it("remembers nothing without a person or a workspace", () => {
    rememberEvent("", "w", "e1");
    toggleFavoriteEvent("u", "", "e1");
    expect(window.localStorage.length).toBe(0);
  });

  it("is cleared at sign-out, only its own keys", () => {
    toggleFavoriteEvent("u", "w", "e1");
    rememberEvent("u2", "w2", "e2");
    window.localStorage.setItem("something-else", "kept");
    clearShellPreferences();
    expect(favoriteEvents("u", "w")).toEqual([]);
    expect(recentEvents("u2", "w2")).toEqual([]);
    expect(window.localStorage.getItem("something-else")).toBe("kept");
  });

  it("keeps the theme per person, defaulting to the system, and forgets it at sign-out", () => {
    expect(themePreference("u")).toBe("system");
    setThemePreference("u", "dark");
    expect(themePreference("u")).toBe("dark");
    expect(themePreference("other")).toBe("system");
    setThemePreference("u", "system"); // the default is stored as nothing at all
    expect(window.localStorage.length).toBe(0);
    setThemePreference("u", "light");
    clearShellPreferences();
    expect(themePreference("u")).toBe("system");
  });

  it("reads an unknown stored theme as the system and refuses to store one", () => {
    window.localStorage.setItem("conflux:v1:u:device:theme", "purple");
    expect(themePreference("u")).toBe("system");
    setThemePreference("u", "purple" as never);
    setThemePreference("", "dark");
    expect(window.localStorage.getItem("conflux:v1:u:device:theme")).toBe(
      "purple",
    );
    expect(themePreference("")).toBe("system");
  });

  it("keeps the last five commands run, newest first, once each, and only command-like ids", () => {
    for (const id of ["go.a", "go.b", "go.c", "go.d", "go.e", "go.f"])
      rememberCommand("u", "w", id);
    rememberCommand("u", "w", "go.c");
    expect(recentCommands("u", "w")).toEqual([
      "go.c",
      "go.f",
      "go.e",
      "go.d",
      "go.b",
    ]);
    rememberCommand("u", "w", "has space");
    rememberCommand("u", "w", "<script>");
    expect(recentCommands("u", "w")).toHaveLength(5);
    window.localStorage.setItem(
      "conflux:v1:u:w:recent-commands",
      JSON.stringify(["1bad", "go.ok"]),
    );
    expect(recentCommands("u", "w")).toEqual(["go.ok"]);
  });

  it("keeps the table density per person, comfortable by default, and forgets it at sign-out", () => {
    expect(densityPreference("u")).toBe("comfortable");
    setDensityPreference("u", "high");
    expect(densityPreference("u")).toBe("high");
    expect(densityPreference("other")).toBe("comfortable");
    setDensityPreference("u", "comfortable"); // the default is stored as nothing
    expect(window.localStorage.length).toBe(0);
    setDensityPreference("u", "compact");
    clearShellPreferences();
    expect(densityPreference("u")).toBe("comfortable");
    window.localStorage.setItem("conflux:v1:u:device:density", "tiny");
    expect(densityPreference("u")).toBe("comfortable");
    setDensityPreference("u", "tiny" as never);
    expect(window.localStorage.getItem("conflux:v1:u:device:density")).toBe(
      "tiny",
    );
  });

  it("pins a saved view as three ids, per person and workspace, once, capped, and unpins it", () => {
    const pin = { event: "e1", entity: "projects", view: "v1" };
    expect(togglePinnedView("u", "w", pin)).toBe(true);
    expect(togglePinnedView("u", "w", { ...pin, view: "v2" })).toBe(true);
    expect(pinnedViews("u", "w")).toEqual([pin, { ...pin, view: "v2" }]);
    expect(pinnedViews("u", "w2")).toEqual([]);
    expect(pinnedViews("other", "w")).toEqual([]);
    expect(togglePinnedView("u", "w", pin)).toBe(true); // a second toggle unpins
    expect(pinnedViews("u", "w")).toEqual([{ ...pin, view: "v2" }]);
    for (let i = 0; i < MAX_PINS; i++)
      togglePinnedView("u", "w", { ...pin, view: `x${i}` });
    expect(pinnedViews("u", "w")).toHaveLength(MAX_PINS);
    expect(togglePinnedView("u", "w", { ...pin, view: "overflow" })).toBe(
      false,
    );
  });

  it("reads damaged pins as nothing and refuses a pin with a non-id part", () => {
    window.localStorage.setItem(
      "conflux:v1:u:w:pinned-views",
      JSON.stringify(["e1:projects:v1", "just-one", "a:b", "a:b:c:d", 5]),
    );
    expect(pinnedViews("u", "w")).toEqual([
      { event: "e1", entity: "projects", view: "v1" },
    ]);
    expect(
      togglePinnedView("u", "w", { event: "e 1", entity: "p", view: "v" }),
    ).toBe(false);
  });
});
