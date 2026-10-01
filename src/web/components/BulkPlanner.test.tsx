// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { BulkPlanner } from "./BulkPlanner";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const OPS = [{ action: "move", projects: ["a", "b"], track: "t2" }];
const EFFECT = {
  action: "move",
  changes: [
    { project: "a", before: null, after: "t2" },
    { project: "b", before: "t1", after: "t2" },
  ],
};
const PREVIEW = {
  applied: false,
  effects: [EFFECT],
  preview_token: "tok",
  expires_in: 600,
};
const NAMES = { tracks: { t1: "Software", t2: "Hardware" } };

type Call = {
  method: string;
  body: { operations: unknown; preview_token?: string };
};
async function mount(
  respond: (call: Call, n: number) => Response | Promise<Response>,
) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_url: unknown, init?: RequestInit) => {
      const call = {
        method: init?.method ?? "GET",
        body: JSON.parse(String(init?.body)),
      };
      calls.push(call);
      return respond(call, calls.length);
    }),
  );
  const opener = document.createElement("button");
  document.body.appendChild(opener);
  opener.focus();
  const onApplied = vi.fn();
  const onClose = vi.fn();
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      <BulkPlanner
        workspaceId="w"
        eventId="e"
        title="Move 2 projects to Hardware"
        applyLabel="Move to Hardware"
        operations={OPS}
        names={NAMES}
        onApplied={onApplied}
        onClose={onClose}
      />,
    ),
  );
  await act(async () => new Promise((r) => setTimeout(r, 0)));
  return { container, calls, onApplied, onClose, root, opener };
}
const button = (c: HTMLElement, text: string) =>
  [...c.querySelectorAll("button")].find((b) => b.textContent === text)!;
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));

describe("BulkPlanner", () => {
  it("previews first, states the effects in plain language, then applies with the preview's token", async () => {
    const { container, calls, onApplied, root } = await mount((call) =>
      call.body.preview_token
        ? jsonResponse(200, { applied: true, effects: [EFFECT] })
        : jsonResponse(200, PREVIEW),
    );
    expect(calls).toHaveLength(1);
    expect(calls[0].body).toEqual({ operations: OPS }); // a dry run carries no token
    expect(container.textContent).toContain(
      "Move 2 projects to Hardware (1 from no track, 1 from Software).",
    );
    expect(container.textContent).toContain("All or nothing");
    expect(container.textContent).toContain("valid for 10 minutes");
    expect(container.textContent).not.toMatch(/are you sure/i);

    await act(async () => button(container, "Move to Hardware").click());
    await settle();
    expect(calls[1].body).toEqual({ operations: OPS, preview_token: "tok" });
    expect(container.textContent).toContain("Applied.");
    expect(
      container.querySelector('[aria-label="Receipt"]')?.textContent,
    ).toContain("Move 2 projects");
    expect(onApplied).toHaveBeenCalledTimes(1);
    expect(button(container, "Close")).toBeDefined();
    await act(async () => root.unmount());
  });

  it("asks for a new preview when the old one is stale, and never applies what was not seen", async () => {
    let previews = 0;
    const { container, calls, onApplied, root } = await mount((call) => {
      if (call.body.preview_token)
        return jsonResponse(409, {
          detail: "Preview effects changed; preview again.",
        });
      previews += 1;
      return jsonResponse(200, { ...PREVIEW, preview_token: `tok${previews}` });
    });
    await act(async () => button(container, "Move to Hardware").click());
    await settle();
    expect(container.querySelector("[role=alert]")?.textContent).toContain(
      "nothing was applied",
    );
    expect(onApplied).not.toHaveBeenCalled();
    await act(async () => button(container, "Preview again").click());
    await settle();
    expect(calls.at(-1)!.body).toEqual({ operations: OPS });
    expect(container.textContent).toContain("This will:");
    expect(button(container, "Move to Hardware")).toBeDefined();
    await act(async () => root.unmount());
  });

  it("explains a refusal without offering to apply", async () => {
    const { container, root } = await mount(() =>
      jsonResponse(400, {
        detail: ["One or more targets are unavailable in this event."],
      }),
    );
    expect(container.querySelector("[role=alert]")?.textContent).toContain(
      "Cannot be done",
    );
    expect(container.textContent).toContain("unavailable in this event");
    expect(
      [...container.querySelectorAll("button")].map((b) => b.textContent),
    ).toEqual(["Cancel", "Preview again"]);
    await act(async () => root.unmount());
  });

  it("after a lost connection, retries with the same preview because a replay is safe", async () => {
    let applying = 0;
    const { container, calls, onApplied, root } = await mount((call) => {
      if (!call.body.preview_token) return jsonResponse(200, PREVIEW);
      applying += 1;
      return applying === 1
        ? jsonResponse(503, { detail: "Service unavailable" })
        : jsonResponse(200, { applied: true, effects: [EFFECT] });
    });
    await act(async () => button(container, "Move to Hardware").click());
    await settle();
    expect(container.textContent).toContain("Could not confirm the result");
    expect(container.textContent).toContain("never applied twice");
    expect(onApplied).not.toHaveBeenCalled();
    await act(async () => button(container, "Try again").click());
    await settle();
    const applies = calls.filter((c) => c.body.preview_token);
    expect(applies).toHaveLength(2);
    expect(applies[1].body.preview_token).toBe("tok"); // the same preview, not a new one
    expect(container.textContent).toContain("Applied.");
    expect(onApplied).toHaveBeenCalledTimes(1);
    await act(async () => root.unmount());
  });

  it("closes with Escape or Cancel, changes nothing, and returns focus", async () => {
    const { container, calls, onClose, root, opener } = await mount(() =>
      jsonResponse(200, PREVIEW),
    );
    await act(async () =>
      container
        .querySelector("[role=dialog]")!
        .dispatchEvent(
          new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
        ),
    );
    expect(onClose).toHaveBeenCalledTimes(1);
    await act(async () => button(container, "Cancel").click());
    expect(onClose).toHaveBeenCalledTimes(2);
    expect(calls.filter((c) => c.body.preview_token)).toEqual([]);
    await act(async () => root.unmount());
    expect(document.activeElement).toBe(opener);
  });
});
