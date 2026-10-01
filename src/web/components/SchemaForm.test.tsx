// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { SchemaForm } from "./SchemaForm";
import { validate, type Schema } from "../lib/schema";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

const SCHEMA: Schema = {
  type: "object",
  properties: {
    name: {
      type: "string",
      title: "Name",
      maxLength: 20,
      "x-nonblank": true,
      default: "",
    },
    about: {
      type: "string",
      title: "About",
      maxLength: 200,
      "x-widget": "textarea",
      "x-help": "A line or two.",
      default: "",
    },
    mode: {
      type: "string",
      title: "Mode",
      enum: ["open", "invite_only"],
      default: "open",
    },
    public: { type: "boolean", title: "Public", default: false },
    size: {
      type: ["integer", "null"],
      title: "Size",
      minimum: 1,
      maximum: 9,
      default: null,
    },
    starts: {
      type: ["string", "null"],
      title: "Starts",
      format: "date-time",
      default: null,
    },
    kinds: {
      type: "array",
      title: "Kinds",
      items: { type: "string", enum: ["file", "image", "external_video"] },
      uniqueItems: true,
      default: [],
    },
    links: {
      type: "array",
      title: "Links",
      maxItems: 2,
      items: {
        type: "object",
        properties: {
          label: { type: "string", title: "Label", maxLength: 10, default: "" },
        },
      },
      default: [],
    },
  },
};

function Harness({
  initial,
  seen,
  timeZone,
}: {
  initial: Record<string, unknown>;
  seen: { value: Record<string, unknown> };
  timeZone?: string;
}) {
  const [value, setValue] = useState(initial);
  seen.value = value;
  return (
    <SchemaForm
      schema={SCHEMA}
      value={value}
      onChange={setValue}
      problems={validate(SCHEMA, value)}
      timeZone={timeZone}
    />
  );
}

async function mount(initial: Record<string, unknown>, timeZone?: string) {
  const seen = { value: initial };
  await act(async () =>
    root.render(<Harness initial={initial} seen={seen} timeZone={timeZone} />),
  );
  return seen;
}
const control = (label: string) =>
  [...container.querySelectorAll("label")]
    .find((l) => l.textContent?.trim().startsWith(label))!
    .querySelector("input, select, textarea") as HTMLInputElement;
async function set(
  el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
  value: string,
) {
  const proto =
    el instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : el instanceof HTMLSelectElement
        ? HTMLSelectElement.prototype
        : HTMLInputElement.prototype;
  await act(async () => {
    Object.getOwnPropertyDescriptor(proto, "value")!.set!.call(el, value);
    el.dispatchEvent(
      new Event(el instanceof HTMLSelectElement ? "change" : "input", {
        bubbles: true,
      }),
    );
  });
}

describe("SchemaForm", () => {
  it("chooses a control from each property's type, bounds and widget", async () => {
    await mount({});
    const name = control("Name");
    expect(name.tagName).toBe("INPUT");
    expect(name.getAttribute("maxlength")).toBe("20");
    expect(name.required).toBe(true);
    expect(control("About").tagName).toBe("TEXTAREA");
    expect(control("Mode").tagName).toBe("SELECT");
    expect(
      [...control("Mode").querySelectorAll("option")].map((o) => o.textContent),
    ).toEqual(["open", "invite only"]);
    expect(control("Public").type).toBe("checkbox");
    const size = control("Size");
    expect([size.type, size.min, size.max]).toEqual(["number", "1", "9"]);
    expect(control("Starts").type).toBe("datetime-local");
    expect(container.querySelector("fieldset legend")!.textContent).toBe(
      "Kinds",
    );
    expect(container.textContent).toContain("A line or two.");
    expect(container.textContent).toContain("Add item");
  });

  it("hands every change to the parent as a new value", async () => {
    const seen = await mount({});
    await set(control("Name"), "Ada");
    await set(control("Mode"), "invite_only");
    await act(async () => control("Public").click());
    await set(control("Size"), "4");
    expect(seen.value).toMatchObject({
      name: "Ada",
      mode: "invite_only",
      public: true,
      size: 4,
    });
    await set(control("Size"), ""); // a nullable number clears to null
    expect(seen.value.size).toBeNull();
  });

  it("shows the date-time on the event's clock and stores a UTC instant", async () => {
    const seen = await mount(
      { starts: "2027-03-06T15:00:00Z" },
      "America/New_York",
    );
    expect(control("Starts").value).toBe("2027-03-06T10:00");
    expect(container.textContent).toContain("(America/New_York)");
    await set(control("Starts"), "2027-03-20T10:00");
    expect(seen.value.starts).toBe("2027-03-20T14:00:00.000Z"); // daylight time by then
    await set(control("Starts"), "");
    expect(seen.value.starts).toBeNull();
  });

  it("edits an enum array as a checkbox group in the schema's order", async () => {
    const seen = await mount({ kinds: ["image"] });
    const boxes = [
      ...container.querySelectorAll<HTMLInputElement>(
        "fieldset input[type=checkbox]",
      ),
    ];
    expect(boxes.map((b) => b.checked)).toEqual([false, true, false]);
    await act(async () => boxes[0].click());
    expect(seen.value.kinds).toEqual(["file", "image"]);
    await act(async () =>
      container
        .querySelectorAll<HTMLInputElement>("fieldset input[type=checkbox]")[1]
        .click(),
    );
    expect(seen.value.kinds).toEqual(["file"]);
  });

  it("adds and removes rows up to the declared cap", async () => {
    const seen = await mount({ links: [] });
    const add = () =>
      [...container.querySelectorAll("button")].find(
        (b) => b.textContent === "Add item",
      )!;
    await act(async () => add().click());
    await act(async () => add().click());
    expect((seen.value.links as unknown[]).length).toBe(2);
    expect(add().disabled).toBe(true);
    expect(container.textContent).toContain("Item 2");
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((b) => b.textContent === "Remove")!
        .click(),
    );
    expect((seen.value.links as unknown[]).length).toBe(1);
    expect(add().disabled).toBe(false);
  });

  it("links each problem to its field for assistive technology", async () => {
    await mount({ name: "x".repeat(21), size: 99 });
    const name = control("Name");
    expect(name.getAttribute("aria-invalid")).toBe("true");
    const alert = document.getElementById(
      name.getAttribute("aria-describedby")!.split(" ").pop()!,
    )!;
    expect(alert.getAttribute("role")).toBe("alert");
    expect(alert.textContent).toContain("at most 20 characters");
    expect(control("Size").getAttribute("aria-invalid")).toBe("true");
    expect(control("About").getAttribute("aria-invalid")).toBeNull();
    const help = control("About").getAttribute("aria-describedby")!;
    expect(document.getElementById(help)!.textContent).toBe("A line or two.");
  });

  it("can be disabled as a whole and names an unsupported type instead of failing", async () => {
    await act(async () =>
      root.render(
        <SchemaForm
          schema={{
            type: "object",
            properties: {
              odd: { type: "unknown" } as Schema,
              ok: { type: "boolean", title: "Ok" },
            },
          }}
          value={{}}
          onChange={() => {}}
          disabled
        />,
      ),
    );
    expect(container.querySelector("[role=alert]")!.textContent).toBe(
      "Unsupported configuration type.",
    );
    expect(control("Ok").disabled).toBe(true);
  });
});
