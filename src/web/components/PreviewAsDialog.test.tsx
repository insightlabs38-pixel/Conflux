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
afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

const FIELDS = [
  { id: "pitch", label: "Pitch", type: "text", required: true },
  { id: "repo", label: "Repository", type: "url", required: false },
];
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
                <AppShell role={role}>x</AppShell>
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
type Opts = { forms?: unknown; form?: unknown; page?: unknown };
async function render(role: string, url: string, opts: Opts = {}) {
  window.history.replaceState({}, "", url);
  const calls: { path: string; body: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const path = String(input);
      calls.push({
        path,
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      });
      if (path.includes("/accounts/me/"))
        return jsonResponse(200, {
          public_id: "u1",
          username: "pat",
          memberships: [],
        });
      if (path.endsWith("/forms/"))
        return jsonResponse(
          200,
          opts.forms ?? [{ public_id: "f1", name: "Application form" }],
        );
      if (path.includes("/preview-as/form/"))
        return opts.form instanceof Error
          ? jsonResponse(400, { form: ["No published version yet."] })
          : jsonResponse(
              200,
              opts.form ?? {
                surface: "form",
                label: "Application form",
                summary: "Previewing as a participant, live.",
                roles: [],
                versions: [],
                resolved: {
                  role: "participant",
                  at: null,
                  version: null,
                  live: true,
                },
                notices: [],
                data: { fields: FIELDS.slice(0, 1), total: 2, hidden: 1 },
              },
            );
      if (path.includes("/preview-as/page/"))
        return jsonResponse(
          200,
          opts.page ?? {
            surface: "page",
            label: "Public page",
            summary: "Previewing the live view.",
            roles: [],
            versions: [],
            resolved: { role: null, at: null, version: null, live: true },
            notices: [],
            data: { html: "<h1>Gauss Hack</h1>" },
          },
        );
      if (path.endsWith("/events/") || path.includes("-events/"))
        return jsonResponse(200, [{ public_id: "e1", name: "Gauss Hack" }]);
      return jsonResponse(200, { modules: [] });
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
const openMenu = async (who: string) => {
  await act(async () => {
    [
      ...document.querySelectorAll<HTMLButtonElement>(
        ".cx-account__roles button",
      ),
    ]
      .find((b) => b.textContent === who)!
      .click();
  });
  for (let i = 0; i < 40 && !document.querySelector('[role="dialog"]'); i++)
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 60));
  });
};
const dialog = () => document.querySelector('[role="dialog"]');

describe("preview as", () => {
  it("is offered to organizers and admins only", async () => {
    const organizer = await render("organizer", "/w/w/overview?event=e1");
    expect(document.querySelector(".cx-account__roles")?.textContent).toContain(
      "Preview as",
    );
    await act(async () => organizer.root.unmount());
    document.body.innerHTML = "";
    const judge = await render("judge", "/w/w/overview?event=e1");
    expect(document.body.textContent).not.toContain("Preview as");
    await act(async () => judge.root.unmount());
  });

  it("asks the server for the saved form as that role, says nothing is saved, and lists what is shown", async () => {
    const { root, calls } = await render("organizer", "/w/w/overview?event=e1");
    await openMenu("Participant");
    expect(dialog()!.querySelector("h2")!.textContent).toBe(
      "Preview as participant",
    );
    const asked = calls.find((c) => c.path.includes("/preview-as/form/"))!;
    expect(asked.body).toEqual({
      ref: { event: "e1", form: "f1" },
      context: { role: "participant" },
    });
    expect(dialog()!.textContent).toContain("Nothing is saved or sent");
    expect(dialog()!.textContent).toContain("signed in as pat");
    expect(dialog()!.textContent).toContain(
      "Previewing as a participant, live.",
    );
    expect(
      [...dialog()!.querySelectorAll("tbody tr")].map(
        (r) => r.firstChild?.textContent,
      ),
    ).toEqual(["Pitch"]);
    expect(dialog()!.textContent).toContain(
      "1 of 2 fields are not shown to a participant.",
    );
    expect(dialog()!.querySelector('[aria-label="Public page"]')).toBeNull();
    await act(async () => root.unmount());
  });

  it("shows the public page in a frame that cannot run anything, only for the public", async () => {
    const { root } = await render("organizer", "/w/w/overview?event=e1");
    await openMenu("Public");
    const frame = dialog()!.querySelector("iframe")!;
    expect(frame.getAttribute("sandbox")).toBe(""); // no scripts, no forms, no navigation
    expect(frame.getAttribute("srcdoc")).toBe("<h1>Gauss Hack</h1>");
    await act(async () => root.unmount());
  });

  it("says what is missing instead of guessing: no event, no forms, a form with nothing published", async () => {
    const none = await render("organizer", "/w/w/overview");
    await openMenu("Judge");
    expect(dialog()!.textContent).toContain("Choose an event first");
    await act(async () => none.root.unmount());
    document.body.innerHTML = "";
    const noForms = await render("organizer", "/w/w/overview?event=e1", {
      forms: [],
    });
    await openMenu("Participant");
    expect(dialog()!.textContent).toContain("This event has no forms yet.");
    await act(async () => noForms.root.unmount());
    document.body.innerHTML = "";
    const failing = await render("organizer", "/w/w/overview?event=e1", {
      form: new Error("x"),
    });
    await openMenu("Participant");
    expect(dialog()!.textContent).toContain("No published version yet.");
    await act(async () => failing.root.unmount());
  });

  it("changes the role without leaving, and is also a command", async () => {
    const { root, calls } = await render("organizer", "/w/w/overview?event=e1");
    await openMenu("Participant");
    const radios = [
      ...dialog()!.querySelectorAll<HTMLInputElement>('input[type="radio"]'),
    ];
    expect(radios.map((r) => r.checked)).toEqual([true, false, false]);
    await act(async () => radios[1].click());
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 60));
    });
    expect(dialog()!.querySelector("h2")!.textContent).toBe("Preview as judge");
    expect(
      calls
        .filter((c) => c.path.includes("/preview-as/form/"))
        .map((c) => (c.body as { context: { role: string } }).context.role),
    ).toEqual(["participant", "judge"]);
    await act(async () => root.unmount());
  });
});
