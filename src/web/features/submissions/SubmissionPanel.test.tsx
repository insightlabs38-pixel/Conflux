// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { SubmissionPanel } from "./SubmissionPanel";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function waitFor(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 15));
    });
  }
  throw new Error("Timed out waiting for submission state");
}

describe("participant submission", () => {
  it("autosaves a draft and displays the finalized receipt", async () => {
    let revision = 0;
    const fetchMock = vi
      .fn()
      .mockImplementation(async (url: string, options?: RequestInit) => {
        const path = String(url);
        let body: unknown = [];
        let status = 200;
        if (path.endsWith("submissions/") && options?.method === "GET") {
          body = [{ public_id: "stage", name: "Build", submission: null }];
        } else if (options?.method === "PUT") {
          const draft = JSON.parse(String(options.body));
          revision += 1;
          body = {
            status: "draft",
            draft_revision: revision,
            draft_payload: draft.draft_payload,
            current_version: null,
            versions: [],
          };
        } else if (path.endsWith("finalize/")) {
          status = 201;
          body = {
            receipt: "receipt-1",
            submission: {
              status: "finalized",
              draft_revision: revision,
              draft_payload: { notes: "Demo", artifact_ids: [] },
              current_version: "receipt-1",
              versions: [
                {
                  public_id: "receipt-1",
                  number: 1,
                  digest: "a".repeat(64),
                  finalized_at: new Date().toISOString(),
                  snapshot: { draft: { notes: "Demo", artifact_ids: [] } },
                },
              ],
            },
          };
        }
        return { ok: true, status, json: async () => body };
      });
    vi.stubGlobal("fetch", fetchMock);
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () => {
      root.render(
        <SubmissionPanel workspaceId="w" eventId="e" projectId="p" />,
      );
    });
    await waitFor(
      () => container.querySelector("select option[value='stage']") !== null,
    );
    await act(async () => {
      const select = container.querySelector("select") as HTMLSelectElement;
      select.value = "stage";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await act(async () => {
      const notes = container.querySelector("textarea") as HTMLTextAreaElement;
      Object.getOwnPropertyDescriptor(
        HTMLTextAreaElement.prototype,
        "value",
      )?.set?.call(notes, "Demo");
      notes.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      (container.querySelector("button") as HTMLButtonElement).click();
    });
    await waitFor(
      () => container.textContent?.includes("Receipt: receipt-1") ?? false,
    );
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url).endsWith("/submissions/stage/") &&
          options?.method === "PUT",
      ),
    ).toBe(true);
    expect(container.textContent).toContain("SHA-256");
    await act(async () => root.unmount());
    container.remove();
    vi.unstubAllGlobals();
  });
});
