// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ThreadPanel } from "./ThreadPanel";
import { jsonResponse } from "../lib/test-http";
import { withQuery } from "../lib/test-router";
import type { Subject, Thread, ThreadComment } from "../lib/threads";

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
  vi.unstubAllGlobals();
});

const SUBJECT: Subject = {
  workspaceId: "w",
  eventId: "e",
  type: "application",
  id: "a1",
  audience: "organizers",
};
const comment = (over: Partial<ThreadComment> = {}): ThreadComment => ({
  public_id: "c1",
  author: { public_id: "u1", username: "org" },
  body: "First note",
  removed: false,
  edited: false,
  mentions: [],
  created_at: "2026-10-01T10:00:00Z",
  can_edit: true,
  can_remove: true,
  replies: [],
  ...over,
});
const thread = (over: Partial<Thread> = {}): Thread => ({
  subject: { type: "application", id: "a1", label: "the application of @par" },
  audience: "organizers",
  can_post: true,
  total: 1,
  comments: [comment()],
  ...over,
});

type Call = { url: string; method: string; body?: Record<string, unknown> };
async function mount(route: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const call = {
        url: String(url),
        method: init?.method ?? "GET",
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      return route(call);
    }),
  );
  await act(async () =>
    root.render(withQuery(<ThreadPanel subject={SUBJECT} />)),
  );
  await settle();
  return calls;
}
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
const button = (text: string) =>
  [...container.querySelectorAll("button")].find(
    (b) => b.textContent === text,
  ) as HTMLButtonElement;
async function type(textarea: HTMLTextAreaElement, value: string) {
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLTextAreaElement.prototype,
      "value",
    )!.set!.call(textarea, value);
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  });
}
const box = (label: string) =>
  [...container.querySelectorAll("label")]
    .find((l) => l.textContent?.startsWith(label))!
    .querySelector("textarea") as HTMLTextAreaElement;

describe("ThreadPanel", () => {
  it("shows an empty thread and posts the first note", async () => {
    let posted = false;
    const calls = await mount((call) => {
      if (call.method === "POST") {
        posted = true;
        return jsonResponse(201, comment());
      }
      return jsonResponse(
        200,
        posted ? thread() : thread({ total: 0, comments: [] }),
      );
    });
    expect(container.textContent).toContain("No notes yet");
    expect(button("Post note").disabled).toBe(true); // nothing to post yet
    await type(box("New note"), "  Check the visa letter @org2 ");
    await act(async () => button("Post note").click());
    await settle();
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toBe(
      "/api/v1/workspaces/w/events/e/threads/application/a1/organizers/",
    );
    expect(post.body).toEqual({ body: "  Check the visa letter @org2 " });
    expect(container.textContent).toContain("First note");
    expect(box("New note").value).toBe(""); // the draft is cleared once it is posted
  });

  it("renders text as text, marks edits, tombstones and nests replies", async () => {
    await mount(() =>
      jsonResponse(
        200,
        thread({
          total: 2,
          comments: [
            comment({
              body: "<img src=x onerror=alert(1)> **not bold**",
              edited: true,
              replies: [
                comment({
                  public_id: "c2",
                  author: { public_id: "u2", username: "org2" },
                  body: "A reply",
                  can_edit: false,
                }),
              ],
            }),
            comment({ public_id: "c3", removed: true, body: "" }),
          ],
        }),
      ),
    );
    expect(container.querySelector("img")).toBeNull(); // never interpreted as markup
    expect(container.querySelector(".cx-thread__body")!.textContent).toContain(
      "<img src=x onerror=alert(1)> **not bold**",
    );
    expect(container.textContent).toContain("edited");
    expect(container.textContent).toContain("This comment was removed.");
    const replies = container.querySelector('[aria-label="Replies to @org"]')!;
    expect(replies.textContent).toContain("A reply");
    expect(replies.textContent).not.toContain("Reply"); // replies go one level deep
  });

  it("replies to a comment, edits it and removes it only after confirming", async () => {
    const calls = await mount((call) =>
      call.method === "GET"
        ? jsonResponse(200, thread())
        : jsonResponse(200, comment()),
    );
    await act(async () => button("Reply").click());
    await type(box("Reply to @org"), "Thanks");
    await act(async () => button("Post reply").click());
    await settle();
    expect(calls.find((c) => c.method === "POST")!.body).toEqual({
      body: "Thanks",
      parent: "c1",
    });

    await act(async () => button("Edit").click());
    expect(box("Edit note").value).toBe("First note"); // prefilled
    await type(box("Edit note"), "Changed");
    await act(async () => button("Save").click());
    await settle();
    const patch = calls.find((c) => c.method === "PATCH")!;
    expect(patch.url).toContain("/thread-comments/c1/");
    expect(patch.body).toEqual({ body: "Changed" });

    await act(async () => button("Remove").click());
    expect(calls.some((c) => c.method === "DELETE")).toBe(false); // asks first
    expect(container.textContent).toContain("cannot be restored");
    await act(async () => button("Keep").click());
    await act(async () => button("Remove").click());
    await act(async () => button("Remove").click()); // the confirm button
    await settle();
    expect(calls.filter((c) => c.method === "DELETE")).toHaveLength(1);
  });

  it("offers only what the server allows and says when the thread is read-only", async () => {
    await mount(() =>
      jsonResponse(
        200,
        thread({
          can_post: false,
          comments: [comment({ can_edit: false, can_remove: false })],
        }),
      ),
    );
    expect(button("Reply")).toBeUndefined();
    expect(button("Edit")).toBeUndefined();
    expect(button("Remove")).toBeUndefined();
    expect(button("Post note")).toBeUndefined();
    expect(container.textContent).toContain("read this thread but not write");
  });

  it("keeps the draft and shows the reason when the server refuses it", async () => {
    await mount((call) =>
      call.method === "POST"
        ? jsonResponse(400, { body: ["Keep a comment under 4000 characters."] })
        : jsonResponse(200, thread({ total: 0, comments: [] })),
    );
    await type(box("New note"), "too long");
    await act(async () => button("Post note").click());
    await settle();
    expect(container.querySelector("[role=alert]")!.textContent).toContain(
      "Keep a comment under 4000 characters.",
    );
    expect(box("New note").value).toBe("too long");
  });

  it("offers people already in the thread as mentions", async () => {
    await mount(() => jsonResponse(200, thread()));
    await type(box("New note"), "Hi");
    await act(async () => button("@org").click());
    expect(box("New note").value).toBe("Hi @org ");
  });

  it("shows a load failure with a retry, and no composer", async () => {
    let fail = true;
    await mount(() =>
      fail
        ? jsonResponse(500, { detail: "Server error" })
        : jsonResponse(200, thread()),
    );
    expect(container.textContent).toContain("Server error");
    expect(container.querySelector("textarea")).toBeNull();
    fail = false;
    await act(async () => button("Try again").click());
    await settle();
    expect(container.textContent).toContain("First note");
  });
});
