// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { ProfilePanel } from "./ProfilePanel";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());
const profile = {
  user_public_id: "u1",
  username: "alex",
  display_name: "Alex Rivera",
  avatar_url: "",
  bio: "Build useful tools",
  location: "Berlin",
  links: [],
  visibility: "private",
  event_profiles: [
    {
      event: "e1",
      event_name: "Builders",
      skills: ["Python"],
      roles: ["Builder"],
      interests: ["Climate"],
      team_seeking: true,
      availability_hours_per_week: 10,
    },
  ],
  judge_expertise: [],
  mentoring: [],
};
async function waitFor(check: () => boolean) {
  for (let i = 0; i < 100; i++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Profile did not settle");
}
it("retains an editable identity after a rejected save, then shows the confirmed identity", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: true, json: async () => profile })
    .mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ avatar_url: ["Invalid URL"] }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...profile, display_name: "Alex Confirmed" }),
    });
  vi.stubGlobal("fetch", fetchMock);
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  await act(async () => root.render(<ProfilePanel />));
  await waitFor(() => Boolean(host.querySelector("form")));
  expect(host.textContent).toContain("Python");
  expect(host.textContent).toContain("Looking for a team");
  const form = host.querySelector("form")!;
  await act(async () =>
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    ),
  );
  expect(host.querySelector('[role="alert"]')?.textContent).toContain(
    "Invalid URL",
  );
  expect(
    [...host.querySelectorAll("input")].some(
      (input) => input.value === "Alex Rivera",
    ),
  ).toBe(true);
  await act(async () =>
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    ),
  );
  expect(host.querySelector('[role="status"]')?.textContent).toBe(
    "Profile saved.",
  );
  expect(host.querySelector("h3")?.textContent).toBe("Alex Confirmed");
  const payload = JSON.parse(fetchMock.mock.calls[1][1].body);
  expect(payload.visibility).toBe("private");
  expect(payload).not.toHaveProperty("event_profiles");
  expect(payload).not.toHaveProperty("username");
  await act(async () => root.unmount());
  host.remove();
});
it("contains malformed profile responses in a retryable error instead of throwing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }),
  );
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  await act(async () => root.render(<ProfilePanel />));
  await waitFor(() => Boolean(host.querySelector('[role="alert"]')));
  expect(host.textContent).toContain("Invalid profile response.");
  expect(host.querySelector("button")?.textContent).toBe("Try again");
  await act(async () => root.unmount());
  host.remove();
});
