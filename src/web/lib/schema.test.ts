import { describe, expect, it } from "vitest";
import cases from "../../../tests/fixtures/schema_cases.json";
import {
  defaults,
  firstError,
  normalize,
  problemsByPath,
  sentence,
  validate,
  type Schema,
} from "./schema";

type Case = {
  name: string;
  schema: Schema;
  value: unknown;
  problems?: { path: string; code: string }[];
  normalized?: unknown;
};

describe("schema subset: the fixtures shared with the server", () => {
  it.each((cases as { cases: Case[] }).cases.map((c) => [c.name, c] as const))(
    "%s",
    (_name, c) => {
      const found = validate(c.schema, c.value).map(({ path, code }) => ({
        path,
        code,
      }));
      expect(found).toEqual(c.problems ?? []);
      if (!c.problems)
        expect(normalize(c.schema, c.value).value).toEqual(c.normalized);
    },
  );
});

describe("schema subset", () => {
  const hero: Schema = {
    type: "object",
    additionalProperties: true,
    properties: {
      title: {
        type: "string",
        title: "Title",
        maxLength: 200,
        default: "",
        "x-nonblank": true,
        "x-create-default": "New hero",
      },
      limit: {
        type: "integer",
        title: "Limit",
        minimum: 1,
        maximum: 24,
        default: 12,
      },
    },
  };

  it("reads each problem as a sentence about its field", () => {
    expect(firstError(hero, { title: " " })).toBe("Title is required.");
    expect(firstError(hero, { title: "x".repeat(201) })).toBe(
      "Title must be at most 200 characters.",
    );
    expect(firstError(hero, { title: "ok", limit: 99 })).toBe(
      "Limit must be an integer from 1 to 24.",
    );
    expect(firstError(hero, { title: "ok", limit: 3 })).toBe("");
    expect(sentence(validate({ type: "unsupported" }, 1)[0])).toBe(
      "Unsupported configuration type.",
    );
  });

  it("fills defaults, with create defaults first when creating", () => {
    expect(defaults(hero)).toEqual({ title: "", limit: 12 });
    expect(defaults(hero, true)).toEqual({ title: "New hero", limit: 12 });
    const copy = defaults(hero);
    copy.title = "changed";
    expect(hero.properties!.title.default).toBe("");
  });

  it("groups problems by path for showing each beside its field", () => {
    const problems = validate(
      {
        type: "object",
        properties: { a: { type: "string", maxLength: 1, default: "" } },
      },
      { a: "xx" },
    );
    expect(problemsByPath(problems)).toEqual({
      a: ["Must be at most 1 characters."],
    });
  });

  it("never throws on hostile input", () => {
    for (const value of [
      null,
      undefined,
      NaN,
      Infinity,
      [[[]]],
      { a: { b: [] } },
      "x".repeat(10),
    ])
      expect(() => validate(hero, value)).not.toThrow();
  });
});
