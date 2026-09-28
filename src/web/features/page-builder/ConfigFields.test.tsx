// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, expect, it, vi } from "vitest";
import { blockTypes } from "./blockSchemas.generated";
import { configDefaults, configError, type ConfigSchema } from "./configSchema";
import { ConfigFields } from "./ConfigFields";
import { PageBuilder } from "./PageBuilder";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

it("uses declared controls and bounds for strings, integers and arrays", () => {
  const hero = renderToStaticMarkup(
    <ConfigFields
      schema={blockTypes.hero.schema}
      config={{ title: "Welcome" }}
      onChange={() => {}}
    />,
  );
  expect(hero).toContain("Title");
  expect(hero).toContain('maxLength="200"');
  expect(hero).toContain("required");
  const rich = renderToStaticMarkup(
    <ConfigFields
      schema={blockTypes.rich_text.schema}
      config={{ html: "<p>Hi</p>" }}
      onChange={() => {}}
    />,
  );
  expect(rich).toContain("<textarea");
  expect(rich).not.toContain("<p>Hi</p>");
  const gallery = renderToStaticMarkup(
    <ConfigFields
      schema={blockTypes.gallery.schema}
      config={{ limit: 6 }}
      onChange={() => {}}
    />,
  );
  expect(gallery).toContain('min="1"');
  expect(gallery).toContain('max="24"');
});

it("validates schema semantics before sending edits", () => {
  expect(
    configError(blockTypes.hero.schema, { title: "Hello", subtitle: null }),
  ).toContain("text");
  expect(configError(blockTypes.hero.schema, { title: " " })).toContain(
    "required",
  );
  expect(
    configError(blockTypes.hero.schema, { title: "x".repeat(201) }),
  ).toContain("200");
  for (const limit of [true, "", 0, 25, 1.5])
    expect(configError(blockTypes.gallery.schema, { limit })).toContain(
      "integer",
    );
  expect(configError(blockTypes.gallery.schema, { limit: 24 })).toBe("");
  expect(
    configError(blockTypes.faq.schema, { items: [{ unknown: "x" }] }),
  ).toContain("unknown");
  expect(
    configError(blockTypes.faq.schema, { items: Array(21).fill({}) }),
  ).toContain("20");
  expect(
    configError(blockTypes.faq.schema, {
      items: [{ question: "Q", answer: 3 }],
    }),
  ).toContain("text");
  expect(
    configError({ type: "unsupported" } as unknown as ConfigSchema, {}),
  ).toContain("Unsupported");
  expect(configDefaults(blockTypes.hero.schema).title).toBe("");
  for (const definition of Object.values(blockTypes))
    expect(
      configError(definition.schema, configDefaults(definition.schema, true)),
    ).toBe("");
});

it("generates editable list rows and enforces their declared cap", async () => {
  const schema: ConfigSchema = {
    ...blockTypes.faq.schema,
    properties: {
      items: { ...blockTypes.faq.schema.properties.items, maxItems: 1 },
    },
  };
  function Editor() {
    const [config, setConfig] = useState(configDefaults(schema));
    return (
      <ConfigFields schema={schema} config={config} onChange={setConfig} />
    );
  }
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<Editor />));
  await act(async () => container.querySelector("button")!.click());
  expect(container.querySelectorAll("input")).toHaveLength(2);
  expect(container.textContent).toContain("question");
  const add = [...container.querySelectorAll("button")].find(
    (button) => button.textContent === "Add item",
  )!;
  expect(add.disabled).toBe(true);
  await act(async () =>
    [...container.querySelectorAll("button")]
      .find((button) => button.textContent === "Remove")!
      .click(),
  );
  expect(container.querySelectorAll("input")).toHaveLength(0);
  expect(add.disabled).toBe(false);
  await act(async () => root.unmount());
});

it("creates a block with schema-declared creation values and renders its editor", async () => {
  let blocks: unknown[] = [];
  const fetchMock = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("accessibility-audit/"))
      return { ok: true, json: async () => [] };
    if (url.endsWith("blocks/")) {
      if (init?.method === "POST") {
        const data = JSON.parse(String(init.body));
        expect(data.kind).toBe("hero");
        expect(data.config.title).toBe("New hero");
        blocks = [{ public_id: "b1", position: 0, ...data }];
      }
      return { ok: true, json: async () => blocks };
    }
    return {
      ok: true,
      json: async () => ({ public_id: "p1", theme: "default" }),
    };
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(<PageBuilder workspaceId="w" eventId="e" />),
  );
  await act(async () =>
    [...container.querySelectorAll("button")]
      .find((button) => button.textContent === "Add")!
      .click(),
  );
  expect(container.querySelector('input[value="New hero"]')).not.toBeNull();
  expect(container.textContent).toContain("Save block");
  await act(async () => root.unmount());
});
