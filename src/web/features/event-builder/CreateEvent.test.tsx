// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import { CreateEvent } from "./CreateEvent";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const format = (over: Record<string, unknown>) => ({
  slug: "science_fair",
  label: "Science fair",
  description: "Evaluate research projects.",
  tracks: [],
  stages: ["Submission", "Judging"],
  version: 1,
  duration_days: 2,
  registration_mode: "application",
  min_team_size: 1,
  max_team_size: 4,
  required_artifact_kinds: ["document"],
  criteria: ["Method", "Evidence"],
  ...over,
});
const FORMATS = [
  format({}),
  format({
    slug: "hackathon",
    label: "Hackathon",
    description: "Build in a weekend.",
    registration_mode: "open",
    max_team_size: 5,
    tracks: ["Software"],
  }),
];

type Call = { url: string; method: string; body: unknown };

async function mount(
  respond: (call: Call) => Response,
  onCreated = vi.fn(),
): Promise<{
  container: HTMLDivElement;
  calls: Call[];
  root: Root;
  onCreated: typeof onCreated;
}> {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const call = {
        url: String(input),
        method: init?.method ?? "GET",
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      return respond(call);
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      withQuery(<CreateEvent workspaceId="w" onCreated={onCreated} />),
    ),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, calls, root, onCreated };
}

function type(input: HTMLInputElement | HTMLSelectElement, value: string) {
  const proto =
    input instanceof HTMLSelectElement
      ? HTMLSelectElement.prototype
      : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(input, value);
  input.dispatchEvent(
    new Event(input instanceof HTMLSelectElement ? "change" : "input", {
      bubbles: true,
    }),
  );
}
const field = (container: HTMLElement, label: string) =>
  [...container.querySelectorAll("label")]
    .find((l) => l.textContent?.trim().startsWith(label))
    ?.querySelector("input,select") as HTMLInputElement;

describe("CreateEvent", () => {
  it("creates from the first format with only what was chosen, deriving the address on the server", async () => {
    const { container, calls, root, onCreated } = await mount((call) =>
      call.method === "GET"
        ? jsonResponse(200, FORMATS)
        : jsonResponse(201, {
            public_id: "new-1",
            name: "County",
            slug: "county",
          }),
    );
    // What the format starts with is visible before anything is created.
    expect(container.textContent).toContain(
      "Starts with: 2 days, application-based registration, teams of 1–4, required evidence: document, published rubric: Method, Evidence.",
    );
    expect(container.textContent).toContain(
      "Still yours to add: judges, prize amounts and the dates.",
    );
    expect(container.textContent).not.toContain("Tracks:");
    await act(async () => type(field(container, "Name"), "County Fair"));
    await act(async () => type(field(container, "Largest team"), "3"));
    await act(async () =>
      type(field(container, "Registration"), "invite_only"),
    );
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((b) => b.textContent === "Create science fair event")!
        .click(),
    );
    await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toContain(
      "event-templates/library/science_fair/instantiate/",
    );
    expect(post.body).toMatchObject({
      name: "County Fair",
      is_public: false,
      registration_mode: "invite_only",
      max_team_size: 3,
    });
    // Unchosen values are not sent, so the format's own values apply (and stay "from the format").
    expect(post.body).not.toHaveProperty("slug");
    expect(post.body).not.toHaveProperty("min_team_size");
    expect(post.body).not.toHaveProperty("starts_at");
    expect(onCreated).toHaveBeenCalledWith("new-1");
    await act(async () => root.unmount());
  });

  it("switching format changes the summary; no format creates a blank draft", async () => {
    const { container, calls, root, onCreated } = await mount((call) =>
      call.method === "GET"
        ? jsonResponse(200, FORMATS)
        : jsonResponse(201, {
            public_id: "blank-1",
            name: "By hand",
            slug: "by-hand",
          }),
    );
    const radios = [
      ...container.querySelectorAll<HTMLInputElement>("input[type=radio]"),
    ];
    await act(async () => radios[1].click());
    expect(container.textContent).toContain("Tracks: Software.");
    expect(container.textContent).toContain("open registration");
    await act(async () => radios[2].click());
    expect(container.textContent).not.toContain("Starts with:");
    await act(async () => type(field(container, "Name"), "By hand"));
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((b) => b.textContent === "Create event")!
        .click(),
    );
    await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toMatch(/\/workspaces\/w\/events\/$/);
    expect(post.body).toEqual({ name: "By hand" });
    expect(onCreated).toHaveBeenCalledWith("blank-1");
    await act(async () => root.unmount());
  });

  it("rejects an impossible team size before asking the server and shows the server's reason otherwise", async () => {
    const { container, calls, root, onCreated } = await mount((call) =>
      call.method === "GET"
        ? jsonResponse(200, FORMATS)
        : jsonResponse(400, {
            slug: ["An event with this slug already exists."],
          }),
    );
    await act(async () => type(field(container, "Name"), "Clash"));
    await act(async () => type(field(container, "Smallest team"), "9"));
    const submit = () =>
      act(async () =>
        container
          .querySelector("form")!
          .dispatchEvent(
            new Event("submit", { bubbles: true, cancelable: true }),
          ),
      );
    await submit();
    expect(container.querySelector("[role=alert]")?.textContent).toContain(
      "Team size must be between 1 and 100, smallest first.",
    );
    expect(calls.some((c) => c.method === "POST")).toBe(false);

    await act(async () => type(field(container, "Smallest team"), ""));
    await submit();
    await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
    expect(container.querySelector("[role=alert]")?.textContent).toContain(
      "already exists",
    );
    expect(onCreated).not.toHaveBeenCalled();
    await act(async () => root.unmount());
  });

  it("explains a failed format list with a retry and still allows a blank event", async () => {
    const { container, root } = await mount(() =>
      jsonResponse(500, { detail: "Formats unavailable" }),
    );
    expect(container.querySelector("[role=alert]")).not.toBeNull();
    expect(container.textContent).toContain("Try again");
    expect(container.textContent).toContain("No format");
    await act(async () => root.unmount());
  });
});
