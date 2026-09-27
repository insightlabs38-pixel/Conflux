// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { JudgeDirectoryPanel } from "./JudgeDirectoryPanel";
import { JudgeInvitationInbox } from "./JudgeInvitationInbox";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 50; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Invitation UI did not update");
}

it("invites a directory judge to the selected event pool", async () => {
  const fetchMock = vi.fn(async (input: unknown, init?: RequestInit) => {
    const path = String(input);
    let body: unknown = [];
    if (path.endsWith("judge-directory/"))
      body = [{ judge: "j1", username: "Ada" }];
    if (path.endsWith("judge-invitations/") && init?.method === "POST") {
      expect(JSON.parse(String(init.body))).toEqual({
        pool: "p1",
        judge: "j1",
      });
      body = {
        public_id: "i1",
        pool: "p1",
        judge: "j1",
        judge_username: "Ada",
        status: "pending",
      };
    }
    return { ok: true, json: async () => body };
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(
      <JudgeDirectoryPanel workspaceId="w1" eventId="e1" poolId="p1" />,
    ),
  );
  await until(() => container.textContent?.includes("Ada") ?? false);
  const select = container.querySelector("select") as HTMLSelectElement;
  await act(async () => {
    select.value = "j1";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await act(async () =>
    (container.querySelector("button") as HTMLButtonElement).click(),
  );
  await until(() => container.textContent?.includes("Ada: pending") ?? false);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/workspaces/w1/events/e1/judge-invitations/",
    expect.objectContaining({ method: "POST" }),
  );
  await act(async () => root.unmount());
});

it("accepts a pending invitation and removes its actions", async () => {
  const fetchMock = vi.fn(async (_input: unknown, init?: RequestInit) => ({
    ok: true,
    json: async () =>
      init?.method === "POST"
        ? {
            public_id: "i1",
            event_name: "First",
            pool_name: "Panel",
            status: "accepted",
          }
        : [
            {
              public_id: "i1",
              event_name: "First",
              pool_name: "Panel",
              status: "pending",
            },
          ],
  }));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<JudgeInvitationInbox workspaceId="w1" />));
  await until(() => container.textContent?.includes("First") ?? false);
  await act(async () =>
    (container.querySelector("button") as HTMLButtonElement).click(),
  );
  await until(
    () => container.textContent?.includes("No pending invitations") ?? false,
  );
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/workspaces/w1/my-judge-invitations/i1/respond/",
    expect.objectContaining({ body: JSON.stringify({ decision: "accept" }) }),
  );
  await act(async () => root.unmount());
});
