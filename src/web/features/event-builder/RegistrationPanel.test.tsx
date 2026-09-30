// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { jsonResponse } from "../../lib/test-http";
import { withRouter } from "../../lib/test-router";
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

const CATALOGUE = [
  {
    key: "applications",
    label: "Applications",
    default_sort: [],
    fields: [
      ["username", "Applicant", "text"],
      ["status", "Status", "enum"],
      ["note", "Note", "text"],
    ].map(([key, label, type]) => ({
      key,
      label,
      type,
      operators: ["eq"],
      choices: type === "enum" ? ["pending", "approved"] : [],
      sortable: true,
      filterable: true,
      default: true,
    })),
  },
];

it("lets an organizer decide a pending application from the applications grid", async () => {
  let decided = false;
  const fetchMock = vi.fn(async (url: unknown, init?: RequestInit) => {
    const path = String(url);
    if (path.endsWith("registration-settings/"))
      return jsonResponse(200, {
        mode: "application",
        capacity: null,
        waitlist_enabled: false,
      });
    if (path.endsWith("registration-invite-codes/"))
      return jsonResponse(200, []);
    if (path.endsWith("/decide/")) {
      expect(JSON.parse(String(init?.body))).toEqual({ decision: "approved" });
      decided = true;
      return jsonResponse(200, { public_id: "a1", status: "approved" });
    }
    if (path.endsWith("/entities/")) return jsonResponse(200, CATALOGUE);
    if (path.includes("/entities/applications/"))
      return jsonResponse(200, {
        entity: "applications",
        total: decided ? 0 : 1,
        limit: 25,
        offset: 0,
        filter: null,
        sort: [],
        columns: ["username", "status", "note"],
        rows: decided
          ? []
          : [
              {
                id: "a1",
                username: "alice",
                status: "pending",
                note: "let me in",
              },
            ],
      });
    if (path.includes("/views/")) return jsonResponse(200, []);
    throw new Error(`Unexpected fetch: ${path}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      withRouter(<RegistrationPanel workspaceId="w1" eventId="e1" />),
    ),
  );
  await until(() => container.textContent?.includes("alice") ?? false);
  expect(container.textContent).toContain("let me in");
  expect(container.querySelector("table")).not.toBeNull();

  await act(async () => {
    [...container.querySelectorAll("button")]
      .find((button) => button.getAttribute("aria-label") === "Approve alice")
      ?.click();
  });
  await until(() => decided);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/workspaces/w1/events/e1/applications/a1/decide/",
    expect.objectContaining({ method: "POST" }),
  );
  // The grid reloads after the decision: the decided row is gone from the pending list.
  await until(() => !(container.textContent?.includes("alice") ?? true));
  await act(async () => root.unmount());
});
