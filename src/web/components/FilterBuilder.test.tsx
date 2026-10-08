// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it } from "vitest";
import type { EntityField, FilterNode } from "../lib/entityQuery";
import { FilterBuilder } from "./FilterBuilder";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

const field = (over: Partial<EntityField>): EntityField => ({
  key: "username",
  label: "Applicant",
  type: "text",
  operators: ["eq", "ne", "in", "contains", "startswith", "is_null"],
  choices: [],
  sortable: true,
  filterable: true,
  default: true,
  ...over,
});
const FIELDS = [
  field({}),
  field({
    key: "status",
    label: "Status",
    type: "enum",
    operators: ["eq", "ne", "in", "is_null"],
    choices: ["pending", "approved"],
  }),
  field({
    key: "waitlist_position",
    label: "Waitlist",
    type: "number",
    operators: ["eq", "gte", "between", "is_null"],
  }),
  field({
    key: "created_at",
    label: "Applied",
    type: "date",
    operators: ["gt", "between", "is_null"],
  }),
  field({
    key: "gallery_visible",
    label: "In gallery",
    type: "bool",
    operators: ["eq", "is_null"],
  }),
  field({ key: "hidden", label: "Hidden", filterable: false, operators: [] }),
];

function mount(initial: FilterNode | null) {
  const seen: (FilterNode | null)[] = [];
  function Host() {
    const [value, setValue] = useState<FilterNode | null>(initial);
    return (
      <FilterBuilder
        fields={FIELDS}
        value={value}
        onChange={(next) => {
          seen.push(next);
          setValue(next);
        }}
      />
    );
  }
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(<Host />));
  return { container, seen, root };
}
const set = (el: HTMLElement, value: string) => {
  const proto =
    el instanceof HTMLSelectElement
      ? HTMLSelectElement.prototype
      : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(el, value);
  el.dispatchEvent(
    new Event(el instanceof HTMLSelectElement ? "change" : "input", {
      bubbles: true,
    }),
  );
};
const by = (c: HTMLElement, label: string) =>
  c.querySelector<HTMLElement>(`[aria-label="${label}"]`)!;
const click = (c: HTMLElement, text: string) =>
  [...c.querySelectorAll("button")]
    .find((b) => b.textContent === text)!
    .click();

describe("FilterBuilder", () => {
  it("builds a typed condition per field type, only offering operators the type supports", async () => {
    const { container, seen, root } = mount(null);
    await act(async () => click(container, "Add condition"));
    expect(seen.at(-1)).toEqual({ field: "username", op: "eq", value: "" });
    // The non-filterable field is not offered.
    expect(
      [...by(container, "Field of condition 1").querySelectorAll("option")].map(
        (o) => o.textContent,
      ),
    ).toEqual(["Applicant", "Status", "Waitlist", "Applied", "In gallery"]);

    await act(async () => set(by(container, "Field of condition 1"), "status"));
    expect(seen.at(-1)).toEqual({ field: "status", op: "eq", value: "" });
    await act(async () =>
      set(by(container, "Value of condition 1"), "approved"),
    );
    expect(seen.at(-1)).toEqual({
      field: "status",
      op: "eq",
      value: "approved",
    });

    await act(async () =>
      set(by(container, "Field of condition 1"), "waitlist_position"),
    );
    await act(async () =>
      set(by(container, "Operator of condition 1"), "between"),
    );
    // a range is two boxes, typed as numbers for a number field
    expect(by(container, "Start of condition 1").getAttribute("type")).toBe(
      "number",
    );
    await act(async () => set(by(container, "Start of condition 1"), "2"));
    await act(async () => set(by(container, "End of condition 1"), "5"));
    expect(seen.at(-1)).toEqual({
      field: "waitlist_position",
      op: "between",
      value: [2, 5],
    });
    await act(async () => set(by(container, "Operator of condition 1"), "gte"));
    await act(async () => set(by(container, "Value of condition 1"), "3"));
    expect(seen.at(-1)).toEqual({
      field: "waitlist_position",
      op: "gte",
      value: 3,
    });

    await act(async () =>
      set(by(container, "Field of condition 1"), "gallery_visible"),
    );
    expect(seen.at(-1)).toEqual({
      field: "gallery_visible",
      op: "eq",
      value: true,
    });
    await act(async () => set(by(container, "Value of condition 1"), "false"));
    expect(seen.at(-1)).toEqual({
      field: "gallery_visible",
      op: "eq",
      value: false,
    });

    await act(async () =>
      set(by(container, "Operator of condition 1"), "is_null"),
    );
    expect(seen.at(-1)).toEqual({
      field: "gallery_visible",
      op: "is_null",
      value: true,
    });
    await act(async () => root.unmount());
  });

  it("words operators for what they compare, uses a date box for dates, checkboxes for several enum values, and keeps a value across operator changes", async () => {
    const { container, seen, root } = mount({
      field: "created_at",
      op: "gt",
      value: "2027-03-01",
    });
    const labels = () =>
      [
        ...by(container, "Operator of condition 1").querySelectorAll("option"),
      ].map((o) => o.textContent);
    expect(labels()).toEqual(["after", "between", "is empty"]);
    expect(by(container, "Value of condition 1").getAttribute("type")).toBe(
      "date",
    );
    await act(async () =>
      set(by(container, "Operator of condition 1"), "between"),
    );
    expect(seen.at(-1)).toEqual({
      field: "created_at",
      op: "between",
      value: ["2027-03-01"],
    });
    await act(async () =>
      set(by(container, "End of condition 1"), "2027-03-05"),
    );
    expect(seen.at(-1)).toEqual({
      field: "created_at",
      op: "between",
      value: ["2027-03-01", "2027-03-05"],
    });
    await act(async () => set(by(container, "Operator of condition 1"), "gt"));
    expect(seen.at(-1)).toEqual({
      field: "created_at",
      op: "gt",
      value: "2027-03-01",
    }); // the first of the pair

    await act(async () =>
      set(by(container, "Field of condition 1"), "waitlist_position"),
    );
    expect(
      [
        ...by(container, "Operator of condition 1").querySelectorAll("option"),
      ].map((o) => o.textContent),
    ).toContain("at least");

    await act(async () => set(by(container, "Field of condition 1"), "status"));
    await act(async () => set(by(container, "Operator of condition 1"), "in"));
    const boxes = () => [
      ...container.querySelectorAll<HTMLInputElement>(
        '[aria-label="Values of condition 1"] input',
      ),
    ];
    expect(boxes().length).toBe(2);
    await act(async () => boxes()[1].click());
    await act(async () => boxes()[0].click());
    expect(seen.at(-1)).toEqual({
      field: "status",
      op: "in",
      value: ["pending", "approved"],
    });
    await act(async () => boxes()[0].click());
    expect(seen.at(-1)).toEqual({
      field: "status",
      op: "in",
      value: ["approved"],
    });
    await act(async () => root.unmount());
  });

  it("combines several conditions with all or any, and removes or clears them", async () => {
    const { container, seen, root } = mount({
      and: [
        { field: "status", op: "eq", value: "pending" },
        { field: "username", op: "contains", value: "a" },
      ],
    });
    expect(container.textContent).toContain("Match");
    await act(async () => set(container.querySelector("select")!, "or"));
    expect(seen.at(-1)).toEqual({
      or: [
        { field: "status", op: "eq", value: "pending" },
        { field: "username", op: "contains", value: "a" },
      ],
    });
    await act(async () => by(container, "Remove condition 1").click());
    // One condition left: a plain condition, not a one-element group.
    expect(seen.at(-1)).toEqual({
      field: "username",
      op: "contains",
      value: "a",
    });
    await act(async () => click(container, "Clear filter"));
    expect(seen.at(-1)).toBeNull();
    await act(async () => root.unmount());
  });

  it("keeps a negation made elsewhere as it is while the rest stays editable, and reads a lone negation as read-only", async () => {
    const negation = {
      not: { field: "status", op: "eq", value: "pending" },
    } as FilterNode;
    const { container, seen, root } = mount({
      and: [negation, { field: "username", op: "eq", value: "a" }],
    });
    expect(container.textContent).toContain("not (");
    await act(async () => set(by(container, "Value of condition 1"), "b"));
    expect(seen.at(-1)).toEqual({
      and: [negation, { field: "username", op: "eq", value: "b" }], // the negation is untouched
    });
    await act(async () => click(container, "Clear filter"));
    expect(seen.at(-1)).toBeNull();
    await act(async () => root.unmount());

    const alone = mount(negation);
    expect(alone.container.textContent).toContain("cannot be edited here");
    expect(alone.container.querySelector("select")).toBeNull();
    expect(alone.seen).toEqual([]);
    await act(async () => alone.root.unmount());
  });

  it("builds nested groups: add a group, edit inside it without losing the input, switch its match, remove it", async () => {
    const { container, seen, root } = mount({
      field: "username",
      op: "eq",
      value: "a",
    });
    await act(async () => click(container, "Add group"));
    // one condition at the top, plus a group (of the other kind) holding one new condition
    expect(seen.at(-1)).toEqual({
      and: [
        { field: "username", op: "eq", value: "a" },
        { or: [{ field: "username", op: "eq", value: "" }] },
      ],
    });
    expect(container.textContent).toContain("Group 1 (match any of these)");
    const input = by(container, "Value of condition 2") as HTMLInputElement;
    await act(async () => set(input, "z"));
    // the control is the same element after typing: the tree did not remount it (focus would be lost)
    expect(by(container, "Value of condition 2")).toBe(input);
    await act(async () => click(container, "Add condition to group 1"));
    expect(seen.at(-1)).toEqual({
      and: [
        { field: "username", op: "eq", value: "a" },
        {
          or: [
            { field: "username", op: "eq", value: "z" },
            { field: "username", op: "eq", value: "" },
          ],
        },
      ],
    });
    await act(async () => set(by(container, "Match of group 1"), "and"));
    expect((seen.at(-1) as { and: FilterNode[] }).and[1]).toMatchObject({
      and: expect.any(Array),
    });
    await act(async () => click(container, "Remove group 1"));
    expect(seen.at(-1)).toEqual({ field: "username", op: "eq", value: "a" }); // back to a plain condition
    await act(async () => root.unmount());
  });

  it("stops at the group depth and at 20 conditions, and says why", async () => {
    const { container, seen, root } = mount({
      field: "username",
      op: "eq",
      value: "a",
    });
    await act(async () => click(container, "Add group"));
    await act(async () => click(container, "Add group inside group 1"));
    expect(container.textContent).toContain("Group 2");
    // depth 3 is the most: the inner group offers no further group
    expect(
      [...container.querySelectorAll("button")].some(
        (b) => b.textContent === "Add group inside group 2",
      ),
    ).toBe(false);
    await act(async () => root.unmount());

    const many: FilterNode = {
      and: Array.from({ length: 20 }, (_, i) => ({
        field: "username",
        op: "eq",
        value: String(i),
      })),
    };
    const full = mount(many);
    const add = [...full.container.querySelectorAll("button")].find(
      (b) => b.textContent === "Add condition",
    )!;
    expect(add.disabled).toBe(true);
    expect(full.container.textContent).toContain("at most 20 conditions");
    expect(full.seen).toEqual([]);
    await act(async () => full.root.unmount());
    void seen;
  });

  it("shows the server's message beside the nested condition it names", async () => {
    const found = {
      byPath: { "and[1].or[0]": "Not a valid value." },
      general: [],
    };
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    act(() =>
      root.render(
        <FilterBuilder
          fields={FIELDS}
          value={{
            and: [
              { field: "username", op: "eq", value: "a" },
              {
                or: [
                  { field: "username", op: "eq", value: "b" },
                  { field: "status", op: "eq", value: "pending" },
                ],
              },
            ],
          }}
          onChange={() => {}}
          problems={found}
        />,
      ),
    );
    expect(container.textContent).toContain("Condition 2: Not a valid value.");
    expect(
      by(container, "Value of condition 2").getAttribute("aria-invalid"),
    ).toBe("true");
    expect(
      by(container, "Value of condition 3").getAttribute("aria-invalid"),
    ).toBeNull();
    await act(async () => root.unmount());
  });
});
