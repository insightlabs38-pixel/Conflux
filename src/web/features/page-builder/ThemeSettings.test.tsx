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
  expect(host.querySelectorAll("label").length).toBe(15);
  await act(async () => root.unmount());
  host.remove();
});

it("offers none, compact and standard hero sizes, defaults to compact and saves the choice", async () => {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  const save = vi.fn().mockResolvedValue(undefined);
  await act(async () =>
    root.render(
      <ThemeSettings
        theme="default"
        config={{}}
        eventId="event"
        onSave={save}
      />,
    ),
  );
  const size = [...host.querySelectorAll("label")]
    .find((label) => label.textContent === "Hero size")
    ?.closest("div")
    ?.querySelector("select") as HTMLSelectElement;
  expect([...size.options].map((option) => option.value)).toEqual([
    "compact",
    "none",
    "standard",
    "immersive",
  ]);
  // artwork-led is opt-in and needs art: it cannot be picked until a hero image URL is set
  expect(
    size.querySelector<HTMLOptionElement>('[value="immersive"]')?.disabled,
  ).toBe(true);
  expect(size.value).toBe("compact"); // what an event without the setting gets
  await act(async () => {
    size.value = "none";
    size.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await act(async () =>
    host
      .querySelector("form")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })),
  );
  expect(save).toHaveBeenCalledWith("default", { hero_size: "none" });
  await act(async () => root.unmount());
  host.remove();
});

it("offers the immersive hero once a hero image URL is set", async () => {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  await act(async () =>
    root.render(
      <ThemeSettings
        theme="default"
        config={{ banner_url: "https://art.example.org/hero.jpg" }}
        eventId="event"
        onSave={vi.fn()}
      />,
    ),
  );
  const size = [...host.querySelectorAll("label")]
    .find((label) => label.textContent === "Hero size")
    ?.closest("div")
    ?.querySelector("select") as HTMLSelectElement;
  expect(
    size.querySelector<HTMLOptionElement>('[value="immersive"]')?.disabled,
  ).toBe(false);
  await act(async () => root.unmount());
  host.remove();
});

it("keeps the crop controls behind a disclosure, saves a focal point as numbers and can centre it again", async () => {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  const save = vi.fn().mockResolvedValue(undefined);
  await act(async () =>
    root.render(
      <ThemeSettings
        theme="default"
        config={{ banner_url: "https://art.example.org/hero.jpg" }}
        eventId="event"
        onSave={save}
      />,
    ),
  );
  const details = host.querySelector("details.cx-theme-art")!;
  expect(details.hasAttribute("open")).toBe(false); // advanced: closed by default
  const slider = (name: string) =>
    [...host.querySelectorAll("label")]
      .find((label) => label.textContent === name)
      ?.closest("div")
      ?.querySelector("input") as HTMLInputElement;
  const horizontal = slider("Focal point, left to right");
  expect(horizontal.type).toBe("range");
  expect(horizontal.value).toBe("50");
  const set = async (input: HTMLInputElement, value: string) =>
    act(async () => {
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value",
      )!.set!.call(input, value);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
  await set(horizontal, "30");
  await set(slider("Focal point, top to bottom"), "70");
  const submit = () =>
    act(async () =>
      host
        .querySelector("form")!
        .dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        ),
    );
  await submit();
  expect(save).toHaveBeenLastCalledWith("default", {
    banner_url: "https://art.example.org/hero.jpg",
    banner_focus_x: 30,
    banner_focus_y: 70,
  });
  await act(async () =>
    [...host.querySelectorAll("button")]
      .find((button) => button.textContent === "Centre the crop")!
      .click(),
  );
  await submit();
  expect(save).toHaveBeenLastCalledWith("default", {
    banner_url: "https://art.example.org/hero.jpg",
    banner_focus_x: 50,
    banner_focus_y: 50,
  });
  await act(async () => root.unmount());
  host.remove();
});
