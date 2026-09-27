// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { RegistrationPanel } from "./RegistrationPanel";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => vi.unstubAllGlobals());

async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 50; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Registration UI did not update");
}

it("lets an organizer decide a pending application", async () => {
  let decided = false;
  const fetchMock = vi.fn(async (url: unknown, init?: RequestInit) => ({
    ok: true,
    json: async () => {
      const path = String(url);
      if (path.endsWith("registration-settings/"))
        return { mode: "application", capacity: null, waitlist_enabled: false };
      if (path.endsWith("registration-invite-codes/")) return [];
      if (path.endsWith("/decide/")) {
        expect(JSON.parse(String(init?.body))).toEqual({
          decision: "approved",
        });
        decided = true;
        return {
          public_id: "a1",
          username: "alice",
          status: "approved",
          note: "",
          waitlist_position: null,
        };
      }
      if (path.endsWith("applications/"))
        return decided
          ? []
          : [
              {
                public_id: "a1",
                username: "alice",
                status: "pending",
                note: "let me in",
                waitlist_position: null,
              },
            ];
      throw new Error(`Unexpected fetch: ${path}`);
    },
  }));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () =>
    root.render(<RegistrationPanel workspaceId="w1" eventId="e1" />),
  );
  await until(() => container.textContent?.includes("alice") ?? false);
  expect(container.textContent).toContain("let me in");

  await act(async () => {
    [...container.querySelectorAll("button")]
      .find((button) => button.textContent === "Approve")
      ?.click();
  });
  await until(() => decided);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/workspaces/w1/events/e1/applications/a1/decide/",
    expect.objectContaining({ method: "POST" }),
  );
  await act(async () => root.unmount());
});
