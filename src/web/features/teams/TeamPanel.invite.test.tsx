// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { useLocation } from "react-router";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { TeamPanel } from "./TeamPanel";
import { withRouter } from "../../lib/test-router";
import { jsonResponse } from "../../lib/test-http";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;
let search = "";
function Where() {
  search = useLocation().search;
  return null;
}
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

it("prefills the invite token from the link and removes it from the URL once redeemed", async () => {
  let redeemed = false;
  const fetchMock = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("team-invites/redeem/")) {
      redeemed = true;
      return jsonResponse(200, {});
    }
    return jsonResponse(
      200,
      redeemed
        ? {
            team: { public_id: "t", name: "Team", members: [] },
            my_role: "member",
          }
        : { team: null, my_role: null },
    );
  });
  vi.stubGlobal("fetch", fetchMock);
  await act(async () =>
    root.render(
      withRouter(
        <>
          <Where />
          <TeamPanel workspaceId="w" eventId="e" />
        </>,
        "/w/w/team?event=e&invite=tok-123",
      ),
    ),
  );
  const input = () =>
    [...container.querySelectorAll("input")].find(
      (field) => field.value === "tok-123",
    );
  for (let i = 0; i < 100 && !input(); i++)
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  expect(input()).toBeDefined();
  expect(search).toBe("?event=e&invite=tok-123");
  await act(async () =>
    [...container.querySelectorAll("button")]
      .find((button) => button.textContent === "Join team")
      ?.click(),
  );
  for (let i = 0; i < 100 && search !== "?event=e"; i++)
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  expect(search).toBe("?event=e");
  const call = fetchMock.mock.calls.find(([url]) =>
    String(url).endsWith("team-invites/redeem/"),
  );
  expect(JSON.parse(String(call?.[1]?.body))).toEqual({ token: "tok-123" });
});
