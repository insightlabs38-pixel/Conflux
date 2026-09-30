// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../../lib/test-http";
import { withQuery } from "../../lib/test-router";
import { GeneratedConfiguration } from "./GeneratedConfiguration";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const TEXT =
  'format: hackathon@1  # Hackathon\nsettings:\n  registration.mode: "invite_only"  # changed; the format uses "open"\n#\n# Inherited, not stated (equal to the format or default):\n#   team.min_size: 1  # preset\n';
const generated = {
  explicit: [{ key: "registration.mode" }],
  inherited: [{ key: "team.min_size" }, { key: "team.max_size" }],
  document: { format: "hackathon@1" },
  text: TEXT,
};

async function mount(respond: (url: string) => Response) {
  const fetchMock = vi.fn(async (input: unknown) => respond(String(input)));
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      withQuery(<GeneratedConfiguration workspaceId="w" eventId="e1" />),
    ),
  );
  return { container, fetchMock, root };
}
const open = async (container: HTMLElement) => {
  const details = container.querySelector("details")!;
  await act(async () => {
    details.open = true;
    details.dispatchEvent(new Event("toggle"));
  });
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
};

describe("GeneratedConfiguration", () => {
  it("loads nothing until opened, then shows the server's document with the counts", async () => {
    const { container, fetchMock, root } = await mount(() =>
      jsonResponse(200, generated),
    );
    expect(fetchMock).not.toHaveBeenCalled();
    await open(container);
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/events/e1/configuration/generated/",
    );
    expect(container.querySelector("pre")?.textContent).toBe(TEXT);
    expect(container.textContent).toContain(
      "1 stated, 2 inherited from hackathon@1.",
    );
    await act(async () => root.unmount());
  });

  it("copies the text and says so, and says so when the browser refuses", async () => {
    const { container, root } = await mount(() => jsonResponse(200, generated));
    await open(container);
    const write = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText: write } });
    const copy = () =>
      act(async () =>
        [...container.querySelectorAll("button")]
          .find((b) => b.textContent === "Copy")!
          .click(),
      );
    await copy();
    expect(write).toHaveBeenCalledWith(TEXT);
    expect(container.querySelector("[role=status]")?.textContent).toContain(
      "Copied",
    );
    write.mockRejectedValue(new Error("denied"));
    await copy();
    expect(container.querySelector("[role=status]")?.textContent).toContain(
      "Could not copy",
    );
    await act(async () => root.unmount());
  });

  it("shows a failed generation with a retry", async () => {
    const { container, root } = await mount(() =>
      jsonResponse(500, { detail: "Server exploded" }),
    );
    await open(container);
    expect(container.querySelector("[role=alert]")).not.toBeNull();
    expect(container.textContent).toContain("Try again");
    await act(async () => root.unmount());
  });
});
