// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it, vi } from "vitest";
import { ThemeSettings } from "./ThemeSettings";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
it("saves mode and constrained settings together and retains the draft on rejection", async () => {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  const save = vi
    .fn()
    .mockRejectedValueOnce(new Error("Accent needs contrast."))
    .mockResolvedValueOnce(undefined);
  await act(async () =>
    root.render(
      <ThemeSettings
        theme="default"
        config={{ hero: "poster", accent: "#a32918" }}
        eventId="event"
        onSave={save}
      />,
    ),
  );
  const form = host.querySelector("form")!;
  await act(async () =>
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    ),
  );
  expect(save).toHaveBeenCalledWith("default", {
    hero: "poster",
    accent: "#a32918",
  });
  expect(host.querySelector('[role="alert"]')?.textContent).toBe(
    "Accent needs contrast.",
  );
  expect(
    host.querySelector<HTMLInputElement>('input[placeholder="#126454"]')?.value,
  ).toBe("#a32918");
  await act(async () =>
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    ),
  );
  expect(host.querySelector('[role="status"]')?.textContent).toBe(
    "Event appearance saved.",
  );
  expect(host.querySelector("a")?.getAttribute("href")).toBe("/e/event/");
  expect(host.querySelectorAll("label").length).toBe(11);
  await act(async () => root.unmount());
  host.remove();
});
