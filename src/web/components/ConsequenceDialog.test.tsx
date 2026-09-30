// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { withQuery } from "../lib/test-router";
import { ConsequenceDialog } from "./ConsequenceDialog";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const allowed = {
  title: "Delete stage Build",
  allowed: true,
  refusal: null,
  blockers: [],
  consequences: [
    { code: "removed", message: "1 stage link will be deleted.", count: 1 },
  ],
  reversible: false,
  confirm_label: "Delete stage Build",
};
const refused = {
  ...allowed,
  title: "Delete stage Judging",
  allowed: false,
  refusal: {
    code: "published_rubric",
    message: "Its judging has 1 published rubric version, which is permanent.",
  },
  blockers: [
    {
      code: "published_rubric",
      message:
        "Its judging has 1 published rubric version, which is permanent.",
    },
  ],
  consequences: [],
  confirm_label: "Delete stage Judging",
};

async function mount(
  respond: () => Response,
  handlers: { onConfirm?: () => Promise<void>; onCancel?: () => void } = {},
) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => respond()),
  );
  const opener = document.createElement("button");
  document.body.appendChild(opener);
  opener.focus();
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  const onConfirm = handlers.onConfirm ?? vi.fn(async () => undefined);
  const onCancel = handlers.onCancel ?? vi.fn();
  await act(async () =>
    root.render(
      withQuery(
        <ConsequenceDialog
          url="/api/v1/workspaces/w/events/e/consequences/?action=stage.delete&target=s"
          onConfirm={onConfirm}
          onCancel={onCancel}
        />,
      ),
    ),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, root, opener, onConfirm, onCancel };
}
const button = (container: HTMLElement, name: string) =>
  [...container.querySelectorAll("button")].find(
    (b) => b.textContent === name,
  )!;

describe("ConsequenceDialog", () => {
  it("states what will happen and names the confirmation for the operation, not OK", async () => {
    const { container, root, onConfirm, onCancel } = await mount(() =>
      jsonResponse(200, allowed),
    );
    const dialog = container.querySelector("[role=dialog]")!;
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(dialog.textContent).toContain("1 stage link will be deleted.");
    expect(dialog.textContent).toContain("This cannot be undone.");
    expect(dialog.textContent).not.toMatch(/are you sure/i);
    await act(async () => button(container, "Delete stage Build").click());
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onCancel).not.toHaveBeenCalled();
    await act(async () => root.unmount());
  });

  it("explains a refusal and offers no confirmation", async () => {
    const { container, root } = await mount(() => jsonResponse(200, refused));
    expect(container.querySelector("[role=alert]")?.textContent).toContain(
      "cannot be done",
    );
    expect(container.textContent).toContain("permanent");
    expect(
      [...container.querySelectorAll("button")].map((b) => b.textContent),
    ).toEqual(["Close"]);
    await act(async () => root.unmount());
  });

  it("shows a failed check with a retry, and a failed operation without closing", async () => {
    const failed = await mount(() => jsonResponse(500, { detail: "Boom" }));
    expect(failed.container.querySelector("[role=alert]")).not.toBeNull();
    expect(failed.container.textContent).toContain("Try again");
    await act(async () => failed.root.unmount());

    const rejecting = await mount(() => jsonResponse(200, allowed), {
      onConfirm: async () => {
        throw new Error(
          "A stage that has ever held a participant cannot be deleted.",
        );
      },
    });
    await act(async () =>
      button(rejecting.container, "Delete stage Build").click(),
    );
    expect(rejecting.container.textContent).toContain(
      "ever held a participant",
    );
    expect(button(rejecting.container, "Delete stage Build").disabled).toBe(
      false,
    );
    await act(async () => rejecting.root.unmount());
  });

  it("Escape and Cancel change nothing, and focus returns to what opened it", async () => {
    const { container, root, opener, onConfirm, onCancel } = await mount(() =>
      jsonResponse(200, allowed),
    );
    expect(document.activeElement).toBe(
      container.querySelector("[role=dialog]"),
    );
    await act(async () =>
      container
        .querySelector("[role=dialog]")!
        .dispatchEvent(
          new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
        ),
    );
    expect(onCancel).toHaveBeenCalledTimes(1);
    await act(async () => button(container, "Cancel").click());
    expect(onCancel).toHaveBeenCalledTimes(2);
    expect(onConfirm).not.toHaveBeenCalled();
    await act(async () => root.unmount());
    expect(document.activeElement).toBe(opener);
  });

  it("keeps Tab inside the dialog", async () => {
    const { container, root } = await mount(() => jsonResponse(200, allowed));
    const confirm = button(container, "Delete stage Build");
    confirm.focus();
    const tab = new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
      cancelable: true,
    });
    await act(async () => confirm.dispatchEvent(tab));
    expect(tab.defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(button(container, "Cancel"));
    await act(async () => root.unmount());
  });
});
