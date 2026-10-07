// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient } from "../lib/test-router";
import { AppShell } from "./AppShell";
import { WorkspaceNavigationProvider } from "./WorkspaceNavigation";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
beforeEach(() => window.localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

const message = (id: string, read: boolean) => ({
  public_id: id,
  subject: `Subject ${id}`,
  body: `Body of ${id}`,
  event: "e1",
  event_name: "Gauss Hack",
  created_at: "2027-03-01T09:00:00Z",
  read_at: read ? "2027-03-01T10:00:00Z" : null,
});

function Harness({ role }: { role: string }) {
  const [client] = useState(createTestQueryClient);
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/w/:workspaceId/:view"
            element={
              <WorkspaceNavigationProvider role={role} workspaceId="w">
                <AppShell role={role}>content</AppShell>
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

async function render(role: string, inbox: unknown) {
  window.history.replaceState({}, "", "/w/w/overview");
  const calls: string[] = [];
  const read = new Set<string>(); // what the server has been told is read
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const path = String(input);
      calls.push(`${init?.method ?? "GET"} ${path}`);
      if (path.includes("/accounts/me/"))
        return jsonResponse(200, { public_id: "u1", memberships: [] });
      if (path.endsWith("/inbox/"))
        return inbox instanceof Error
          ? jsonResponse(503, { detail: "down" })
          : jsonResponse(
              200,
              (inbox as ReturnType<typeof message>[]).map((item) =>
                read.has(item.public_id) ? message(item.public_id, true) : item,
              ),
            );
      if (path.includes("/read/")) {
        const id = path.split("/").at(-3)!;
        read.add(id);
        return jsonResponse(200, message(id, true));
      }
      return jsonResponse(200, []);
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<Harness role={role} />));
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 10));
  });
  return { container, root, calls };
}
const bell = (c: HTMLElement) =>
  c.querySelector<HTMLElement>(".cx-inbox summary")!;
const count = (c: HTMLElement) => c.querySelector(".cx-inbox__count");

describe("notification center", () => {
  it("counts the unread, lists the latest and marks one read through the inbox endpoint", async () => {
    const { container, root, calls } = await render("participant", [
      message("a", false),
      message("b", false),
      message("c", true),
    ]);
    expect(bell(container).getAttribute("aria-label")).toBe(
      "Notifications, 2 unread",
    );
    expect(count(container)?.textContent).toBe("2");
    const rows = [...container.querySelectorAll(".cx-inbox__panel li")];
    expect(rows).toHaveLength(3);
    expect(rows[0].textContent).toContain("Subject a");
    expect(rows[0].textContent).toContain("Body of a");
    expect(rows[0].textContent).toContain("Gauss Hack");
    expect(rows[2].textContent).not.toContain("Mark read");
    await act(async () => {
      rows[0].querySelector<HTMLButtonElement>(".cx-inbox__read")!.click();
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    expect(calls).toContain("POST /api/v1/workspaces/w/inbox/a/read/");
    expect(count(container)?.textContent).toBe("1");
    await act(async () => root.unmount());
  });

  it("opening the panel marks nothing", async () => {
    const { container, root, calls } = await render("participant", [
      message("a", false),
    ]);
    container.querySelector<HTMLDetailsElement>(".cx-inbox")!.open = true;
    expect(calls.filter((call) => call.includes("/read/"))).toEqual([]);
    expect(count(container)?.textContent).toBe("1");
    await act(async () => root.unmount());
  });

  it("says all caught up when nothing is unread, with no count shown", async () => {
    const { container, root } = await render("participant", [
      message("a", true),
    ]);
    expect(bell(container).getAttribute("aria-label")).toBe(
      "Notifications, none unread",
    );
    expect(count(container)).toBeNull();
    const none = await render("participant", []);
    expect(
      none.container.querySelector(".cx-inbox__panel")?.textContent,
    ).toContain("You are all caught up.");
    await act(async () => root.unmount());
    await act(async () => none.root.unmount());
  });

  it("caps the figure and the list", async () => {
    const many = Array.from({ length: 100 }, (_, i) => message(`m${i}`, false));
    const { container, root } = await render("participant", many);
    expect(count(container)?.textContent).toBe("99+");
    expect(container.querySelectorAll(".cx-inbox__panel li")).toHaveLength(8);
    expect(container.querySelector(".cx-inbox__panel")?.textContent).toContain(
      "Showing the latest 8 of 100.",
    );
    await act(async () => root.unmount());
  });

  it("links to all messages only for roles that have the destination, and to preferences for all", async () => {
    const participant = await render("participant", []);
    const links = (c: HTMLElement) =>
      [...c.querySelectorAll(".cx-inbox__footer a")].map((a) => a.textContent);
    expect(links(participant.container)).toEqual([
      "All messages",
      "Notification preferences",
    ]);
    const organizer = await render("organizer", []);
    expect(links(organizer.container)).toEqual(["Notification preferences"]);
    await act(async () => participant.root.unmount());
    await act(async () => organizer.root.unmount());
  });

  it("says when the inbox cannot load, keeps the button to retry", async () => {
    const { container, root } = await render("participant", new Error("down"));
    const panel = container.querySelector(".cx-inbox__panel")!;
    expect(panel.querySelector("[role=alert]")?.textContent).toContain(
      "Could not load your inbox.",
    );
    expect(panel.textContent).toContain("Try again");
    expect(panel.textContent).not.toContain("all caught up");
    await act(async () => root.unmount());
  });
});
