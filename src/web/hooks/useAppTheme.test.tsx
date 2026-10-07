// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setThemePreference } from "../lib/shellPreferences";
import { useAppTheme } from "./useAppTheme";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let dark = false;
const listeners = new Set<() => void>();
beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  dark = false;
  vi.stubGlobal("matchMedia", () => ({
    get matches() {
      return dark;
    },
    addEventListener: (_: string, fn: () => void) => listeners.add(fn),
    removeEventListener: (_: string, fn: () => void) => listeners.delete(fn),
  }));
});
afterEach(() => vi.unstubAllGlobals());

function Probe({ user }: { user: string }) {
  useAppTheme(user);
  return null;
}
const attr = () => document.documentElement.getAttribute("data-theme");
async function mount(user: string) {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<Probe user={user} />));
  return root;
}

describe("app theme", () => {
  it("follows the operating system by default, and when it changes", async () => {
    const root = await mount("u1");
    expect(attr()).toBe("light");
    dark = true;
    await act(async () => listeners.forEach((fn) => fn()));
    expect(attr()).toBe("dark");
    await act(async () => root.unmount());
  });

  it("uses an explicit choice whatever the system says, at once", async () => {
    const root = await mount("u1");
    await act(async () => setThemePreference("u1", "dark"));
    expect(attr()).toBe("dark");
    dark = false;
    await act(async () => listeners.forEach((fn) => fn()));
    expect(attr()).toBe("dark");
    await act(async () => setThemePreference("u1", "light"));
    expect(attr()).toBe("light");
    await act(async () => root.unmount());
  });

  it("sets nothing for nobody, and puts back what it found when it leaves", async () => {
    const none = await mount("");
    expect(attr()).toBeNull();
    await act(async () => none.unmount());
    document.documentElement.setAttribute("data-theme", "dark");
    const root = await mount("u1");
    expect(attr()).toBe("light");
    await act(async () => root.unmount());
    expect(attr()).toBe("dark");
  });
});
