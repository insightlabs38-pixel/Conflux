// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { beforeEach, describe, expect, it } from "vitest";
import { setDensityPreference } from "../lib/shellPreferences";
import { useAppDensity } from "./useAppDensity";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-density");
});

function Probe({ user }: { user: string }) {
  useAppDensity(user);
  return null;
}
const attr = () => document.documentElement.getAttribute("data-density");
async function mount(user: string) {
  const root = createRoot(document.createElement("div"));
  await act(async () => root.render(<Probe user={user} />));
  return root;
}

describe("app density", () => {
  it("sets nothing by default, so the long-standing look is untouched", async () => {
    const root = await mount("u1");
    expect(attr()).toBeNull();
    await act(async () => root.unmount());
  });

  it("applies a choice at once, returns to nothing for the default and puts back what it found", async () => {
    document.documentElement.setAttribute("data-density", "high");
    const root = await mount("u1");
    expect(attr()).toBe("high"); // found value kept while the person has made no choice
    await act(async () => setDensityPreference("u1", "compact"));
    expect(attr()).toBe("compact");
    await act(async () => setDensityPreference("u1", "comfortable"));
    expect(attr()).toBe("high");
    await act(async () => root.unmount());
    expect(attr()).toBe("high");
  });

  it("is nobody's when nobody is signed in", async () => {
    window.localStorage.setItem("conflux:v1:u1:device:density", "high");
    const root = await mount("");
    expect(attr()).toBeNull();
    await act(async () => root.unmount());
  });
});
