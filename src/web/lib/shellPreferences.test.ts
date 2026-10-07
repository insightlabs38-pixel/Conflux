// @vitest-environment happy-dom
import { beforeEach, describe, expect, it } from "vitest";
import {
  MAX_FAVORITES,
  MAX_RECENTS,
  clearShellPreferences,
  favoriteEvents,
  recentEvents,
  rememberEvent,
  toggleFavoriteEvent,
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
});
