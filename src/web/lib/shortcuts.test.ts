// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import { interpret, isTyping, type KeyInfo } from "./shortcuts";

const key = (k: string, over: Partial<KeyInfo> = {}): KeyInfo => ({
  key: k,
  ctrlKey: false,
  metaKey: false,
  altKey: false,
  target: null,
  dialogOpen: false,
  ...over,
});

describe("shortcut interpretation", () => {
  it("maps ? to help, / to the palette and g to a pending chord", () => {
    expect(interpret(key("?"), false).action).toEqual({ type: "help" });
    expect(interpret(key("/"), false).action).toEqual({ type: "palette" });
    expect(interpret(key("g"), false)).toEqual({
      action: { type: "chord" },
      pending: true,
    });
    expect(interpret(key("G"), false).pending).toBe(true);
  });

  it("goes to a place on the letter after g, once, and drops the chord on anything else", () => {
    expect(interpret(key("j"), true)).toEqual({
      action: { type: "go", letter: "j" },
      pending: false,
    });
    expect(interpret(key("J"), true).action).toEqual({
      type: "go",
      letter: "j",
    });
    expect(interpret(key("Escape"), true)).toEqual({
      action: { type: "none" },
      pending: false,
    });
    expect(interpret(key("1"), true).action).toEqual({ type: "none" });
    expect(interpret(key("j"), false).action).toEqual({ type: "none" }); // j alone is nothing
  });

  it("is silent with a modifier held, while typing and while a dialog is open", () => {
    expect(interpret(key("?", { ctrlKey: true }), false).action.type).toBe(
      "none",
    );
    expect(interpret(key("g", { metaKey: true }), false).action.type).toBe(
      "none",
    );
    expect(interpret(key("g", { altKey: true }), false).action.type).toBe(
      "none",
    );
    for (const tag of ["input", "textarea", "select"])
      expect(
        interpret(key("?", { target: document.createElement(tag) }), false)
          .action.type,
      ).toBe("none");
    const editable = document.createElement("div");
    editable.contentEditable = "true";
    Object.defineProperty(editable, "isContentEditable", { value: true });
    expect(isTyping(editable)).toBe(true);
    expect(isTyping(document.createElement("button"))).toBe(false);
    expect(interpret(key("?", { dialogOpen: true }), false).action.type).toBe(
      "none",
    );
    expect(interpret(key("j", { dialogOpen: true }), true).action.type).toBe(
      "none",
    );
  });
});
