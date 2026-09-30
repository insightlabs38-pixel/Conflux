// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { withRouter } from "../lib/test-router";
import type { SavedView, ViewDefinition } from "../lib/savedViews";
import { ViewBar } from "./ViewBar";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const PENDING: ViewDefinition = {
  filter: { field: "status", op: "eq", value: "pending" },
  sort: "-created_at",
  columns: ["username"],
  density: "compact",
};
const view = (over: Partial<SavedView>): SavedView => ({
  public_id: "11111111-1111-4111-8111-111111111111",
  entity: "applications",
  name: "Pending",
  query: PENDING,
  visibility: "private",
  version: 1,
  owner: "ana",
  mine: true,
  updated_at: "2027-03-01T00:00:00Z",
  ...over,
});
const SHARED = view({
  public_id: "22222222-2222-4222-8222-222222222222",
  name: "Waiting",
  owner: "bo",
  mine: false,
  visibility: "organizers",
});

type Call = { url: string; method: string; body: unknown };

async function mount(
  initial: SavedView[],
  options: { url?: string; current?: ViewDefinition } = {},
) {
  let views = initial;
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      calls.push({ url, method, body });
      if (method === "GET") return jsonResponse(200, views);
      if (method === "POST") {
        const created = view({
          public_id: "33333333-3333-4333-8333-333333333333",
          name: body.name,
          query: body.query,
        });
        views = [...views, created];
        return jsonResponse(201, created);
      }
      if (method === "PATCH") {
        const id = url.split("/").filter(Boolean).pop()!;
        views = views.map((v) =>
          v.public_id === id ? { ...v, ...body, version: v.version + 1 } : v,
        );
        return jsonResponse(
          200,
          views.find((v) => v.public_id === id)!,
        );
      }
      const id = url.split("/").filter(Boolean).pop()!;
      views = views.filter((v) => v.public_id !== id);
      return new Response(null, { status: 204 });
    }),
  );
  const applied: (SavedView | null)[] = [];
  function Host() {
    const [current] = useState(options.current ?? PENDING);
    return (
      <ViewBar
        workspaceId="w"
        eventId="e"
        entity="applications"
        current={current}
        onApply={(v) => applied.push(v)}
      />
    );
  }
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(withRouter(<Host />, options.url ?? "/w/w/setup")),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, calls, applied, root };
}
const button = (c: HTMLElement, text: string) =>
  [...c.querySelectorAll("button")].find((b) => b.textContent === text);
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
const type = (el: HTMLInputElement, value: string) => {
  Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype,
    "value",
  )?.set?.call(el, value);
  el.dispatchEvent(new Event("input", { bubbles: true }));
};

describe("ViewBar", () => {
  it("lists my views and shared ones separately and applies the chosen one", async () => {
    const { container, applied, root } = await mount([view({}), SHARED]);
    const select = container.querySelector("select")!;
    expect(
      [...select.querySelectorAll("optgroup")].map((g) =>
        g.getAttribute("label"),
      ),
    ).toEqual(["My views", "Shared by organizers"]);
    expect(select.textContent).toContain("Waiting (bo)");
    await act(async () => {
      select.value = SHARED.public_id;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(applied.at(-1)?.name).toBe("Waiting");
    // A shared view is not mine: no Save, Rename, share toggle or Delete; Copy link is offered.
    expect(button(container, "Save")).toBeUndefined();
    expect(button(container, "Delete view")).toBeUndefined();
    expect(button(container, "Copy link")).toBeDefined();
    expect(container.textContent).toContain("Shared by bo");
    await act(async () => root.unmount());
  });

  it("opens the view named in the URL and drops an id that is not in the list", async () => {
    const opened = await mount([view({})], {
      url: `/w/w/setup?view=${view({}).public_id}`,
    });
    expect(opened.applied.at(-1)?.name).toBe("Pending");
    await act(async () => opened.root.unmount());

    const stray = await mount([view({})], {
      url: "/w/w/setup?view=99999999-9999-4999-8999-999999999999",
    });
    expect(stray.applied).toEqual([]);
    expect(stray.container.querySelector("select")!.value).toBe("");
    await act(async () => stray.root.unmount());
  });

  it("says when the list differs from the saved view and saves the change with the version", async () => {
    const { container, calls, root } = await mount([view({})], {
      url: `/w/w/setup?view=${view({}).public_id}`,
      current: { ...PENDING, sort: "username" },
    });
    expect(container.textContent).toContain("Changed since saved");
    await act(async () => button(container, "Save")!.click());
    await settle();
    const patch = calls.find((c) => c.method === "PATCH")!;
    expect(patch.body).toMatchObject({
      version: 1,
      query: { sort: "username" },
    });
    expect(container.textContent).toContain("View saved.");
    await act(async () => root.unmount());
  });

  it("saves the current list as a new named view", async () => {
    const { container, calls, applied, root } = await mount([]);
    await act(async () => button(container, "Save as new view")!.click());
    expect(button(container, "Save view")!.disabled).toBe(true);
    await act(async () =>
      type(
        container.querySelector<HTMLInputElement>("form input")!,
        "Pending first",
      ),
    );
    await act(async () => button(container, "Save view")!.click());
    await settle();
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.body).toEqual({
      entity: "applications",
      name: "Pending first",
      query: PENDING,
    });
    expect(container.textContent).toContain("View saved.");
    expect(applied).toEqual([]); // the list already shows this definition; nothing to apply twice
    await act(async () => root.unmount());
  });

  it("shares a view, renames it, and deletes it with the consequence stated", async () => {
    const { container, calls, root } = await mount([view({})], {
      url: `/w/w/setup?view=${view({}).public_id}`,
    });
    await act(async () =>
      container
        .querySelector<HTMLInputElement>("input[type=checkbox]")!
        .click(),
    );
    await settle();
    expect(calls.find((c) => c.method === "PATCH")!.body).toMatchObject({
      visibility: "organizers",
    });
    expect(container.textContent).toContain("Shared with organizers.");

    await act(async () => button(container, "Rename")!.click());
    await act(async () =>
      type(
        container.querySelector<HTMLInputElement>("form input")!,
        "Waiting list",
      ),
    );
    await act(async () => button(container, "Rename view")!.click());
    await settle();
    expect(
      calls.filter((c) => c.method === "PATCH").at(-1)!.body,
    ).toMatchObject({
      name: "Waiting list",
    });

    await act(async () => button(container, "Delete view")!.click());
    const dialog = container.querySelector("[role=alertdialog]")!;
    expect(dialog.textContent).toContain(
      "Organizers it was shared with lose it.",
    );
    expect(dialog.textContent).toContain("The data it shows is not touched.");
    await act(async () => button(container, "Delete “Waiting list”")!.click());
    await settle();
    expect(calls.some((c) => c.method === "DELETE")).toBe(true);
    expect(container.textContent).toContain("View deleted.");
    await act(async () => root.unmount());
  });

  it("shows a server refusal without losing the work, and a failed load with a retry", async () => {
    const { container, root } = await mount([view({})], {
      url: `/w/w/setup?view=${view({}).public_id}`,
      current: { ...PENDING, sort: "username" },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse(409, {
          code: "view_changed",
          detail: "This view changed since you loaded it.",
        }),
      ),
    );
    await act(async () => button(container, "Save")!.click());
    await settle();
    expect(container.querySelector("[role=alert]")?.textContent).toContain(
      "changed since you loaded",
    );
    expect(container.textContent).toContain("Changed since saved");
    await act(async () => root.unmount());

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(500, { detail: "Boom" })),
    );
    const failed = document.createElement("div");
    document.body.appendChild(failed);
    const failedRoot = createRoot(failed);
    await act(async () =>
      failedRoot.render(
        withRouter(
          <ViewBar
            workspaceId="w"
            eventId="e"
            entity="applications"
            current={PENDING}
            onApply={() => {}}
          />,
        ),
      ),
    );
    await settle();
    expect(failed.textContent).toContain("Try again");
    await act(async () => failedRoot.unmount());
  });
});
