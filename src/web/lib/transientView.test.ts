import { describe, expect, it } from "vitest";
import type { EntityField, FilterNode } from "./entityQuery";
import { decodeFilter, encodeFilter, isShareable } from "./transientView";

const f = (over: Partial<EntityField>): EntityField => ({
  key: "name",
  label: "Name",
  type: "text",
  operators: ["eq", "ne", "in", "contains", "is_null"],
  choices: [],
  sortable: true,
  filterable: true,
  default: true,
  ...over,
});
const FIELDS = [
  f({}),
  f({
    key: "status",
    type: "enum",
    operators: ["eq", "ne", "in", "is_null"],
    choices: ["pending", "approved"],
  }),
  f({ key: "gallery", type: "bool", operators: ["eq", "is_null"] }),
  f({
    key: "waitlist",
    type: "number",
    operators: ["eq", "gte", "between", "in", "is_null"],
  }),
  f({
    key: "created_at",
    type: "date",
    operators: ["gt", "between", "is_null"],
  }),
  f({ key: "team_id", type: "uuid", operators: ["eq", "in"] }),
  f({ key: "hidden", filterable: false, operators: [] }),
];
const roundTrip = (tree: FilterNode) => {
  const encoded = encodeFilter(tree, FIELDS);
  expect(encoded.kind).toBe("ok");
  return decodeFilter((encoded as { text: string }).text, FIELDS);
};

describe("transient view in the address", () => {
  it("round-trips a structured filter with groups, ranges and lists", () => {
    const tree: FilterNode = {
      and: [
        { field: "status", op: "in", value: ["pending", "approved"] },
        {
          or: [
            { field: "gallery", op: "eq", value: true },
            { field: "waitlist", op: "between", value: [2, 5] },
          ],
        },
        { field: "created_at", op: "gt", value: "2027-03-01" },
        { field: "name", op: "is_null", value: false },
      ],
    };
    expect(roundTrip(tree)).toEqual(tree);
  });

  it("never encodes free text or an id: a filter holding one is not for a link", () => {
    expect(
      encodeFilter(
        { field: "name", op: "contains", value: "ada lovelace" },
        FIELDS,
      ),
    ).toEqual({ kind: "text" });
    expect(
      encodeFilter(
        {
          field: "team_id",
          op: "eq",
          value: "11111111-1111-4111-8111-111111111111",
        },
        FIELDS,
      ),
    ).toEqual({ kind: "text" });
    // one unsafe value anywhere keeps the whole filter out, nothing is partly encoded
    expect(
      encodeFilter(
        {
          and: [
            { field: "gallery", op: "eq", value: true },
            { field: "name", op: "eq", value: "x" },
          ],
        },
        FIELDS,
      ),
    ).toEqual({ kind: "text" });
    expect(encodeFilter(null, FIELDS)).toEqual({ kind: "empty" });
    expect(
      isShareable({ field: "status", op: "eq", value: "not-a-choice" }, FIELDS),
    ).toBe(false);
  });

  it("refuses a link that does not decode, names a field the list lacks, or carries a value it should not", () => {
    const text = (node: unknown) =>
      btoa(JSON.stringify(node))
        .replaceAll("+", "-")
        .replaceAll("/", "_")
        .replace(/=+$/, "");
    expect(decodeFilter("!!notbase64!!", FIELDS)).toBeNull();
    expect(decodeFilter("", FIELDS)).toBeNull();
    expect(
      decodeFilter(text({ field: "hidden", op: "eq", value: true }), FIELDS),
    ).toBeNull();
    expect(
      decodeFilter(text({ field: "nothing", op: "eq", value: "x" }), FIELDS),
    ).toBeNull();
    expect(
      decodeFilter(
        text({ field: "name", op: "eq", value: "typed text" }),
        FIELDS,
      ),
    ).toBeNull();
    expect(
      decodeFilter(
        text({ field: "status", op: "gt", value: "pending" }),
        FIELDS,
      ),
    ).toBeNull(); // operator not offered
    expect(
      decodeFilter(
        text({ field: "status", op: "eq", value: "approved", extra: 1 }),
        FIELDS,
      ),
    ).toBeNull();
    expect(decodeFilter(text({ and: [] }), FIELDS)).toBeNull();
    expect(
      decodeFilter(
        text({ field: "status", op: "eq", value: "approved" }),
        FIELDS,
      ),
    ).toEqual({
      field: "status",
      op: "eq",
      value: "approved",
    });
  });

  it("bounds depth, the number of conditions and the length", () => {
    let deep: FilterNode = { field: "gallery", op: "eq", value: true };
    for (let i = 0; i < 5; i++) deep = { and: [deep] };
    expect(encodeFilter(deep, FIELDS)).toEqual({ kind: "text" });
    const many: FilterNode = {
      and: Array.from({ length: 21 }, () => ({
        field: "gallery",
        op: "eq",
        value: true,
      })),
    };
    expect(isShareable(many, FIELDS)).toBe(false);
    const wide: FilterNode = {
      field: "waitlist",
      op: "in",
      value: Array.from({ length: 50 }, (_, i) => i * 1000003),
    };
    expect(["ok", "long"]).toContain(encodeFilter(wide, FIELDS).kind);
  });
});
