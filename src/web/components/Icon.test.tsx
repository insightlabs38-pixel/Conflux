// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it } from "vitest";
import { Alert } from "./Foundation";
import { ErrorState } from "./ErrorState";
import { DeniedState } from "./DeniedState";
import { ICON_NAMES, Icon } from "./Icon";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function render(node: React.ReactNode) {
  const host = document.createElement("div");
  await act(async () => createRoot(host).render(node));
  return host;
}

it("is decorative by default and an image only when it stands alone with a name", async () => {
  const beside = (await render(<Icon name="check" />)).querySelector("svg")!;
  expect(beside.getAttribute("aria-hidden")).toBe("true");
  expect(beside.getAttribute("role")).toBeNull();
  const alone = (
    await render(<Icon name="lock" label="Locked" />)
  ).querySelector("svg")!;
  expect(alone.getAttribute("role")).toBe("img");
  expect(alone.getAttribute("aria-label")).toBe("Locked");
  expect(alone.getAttribute("aria-hidden")).toBeNull();
});

it("draws every icon on the 24 grid at 16px with currentColor and at least one shape", async () => {
  for (const name of ICON_NAMES) {
    const svg = (await render(<Icon name={name} />)).querySelector("svg")!;
    expect(svg.getAttribute("viewBox"), name).toBe("0 0 24 24");
    expect(svg.getAttribute("width"), name).toBe("16");
    expect(svg.getAttribute("stroke"), name).toBe("currentColor");
    expect(
      svg.querySelectorAll("path,circle,rect").length,
      name,
    ).toBeGreaterThan(0);
  }
});

it("pairs every status with an icon and its words, never colour alone", async () => {
  for (const tone of ["info", "warning", "danger", "success"] as const) {
    const host = await render(<Alert tone={tone}>Saved to the plan.</Alert>);
    expect(host.querySelector("svg"), tone).not.toBeNull();
    expect(host.textContent).toContain("Saved to the plan.");
  }
  expect(
    (await render(<ErrorState message="No." />)).querySelector("svg"),
  ).not.toBeNull();
  expect((await render(<DeniedState />)).querySelector("svg")).not.toBeNull();
});
