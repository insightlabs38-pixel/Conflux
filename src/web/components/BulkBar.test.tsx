// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { BulkBar, MAX_BULK_VISIBLE, type BulkAction } from "./BulkBar";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

async function show(count: number, actions: BulkAction[]) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(<BulkBar count={count} actions={actions} />),
  );
  return { container, root };
}
const act1 = (id: string, over: Partial<BulkAction> = {}): BulkAction => ({
  id,
  label: `Action ${id}`,
  run: () => {},
  ...over,
});

describe("bulk bar", () => {
  it("shows nothing without a selection", async () => {
    const { container, root } = await show(0, [act1("a")]);
    expect(container.innerHTML).toBe("");
    await act(async () => root.unmount());
  });

  it("states the count, emphasises exactly one action, shows four and puts the rest under More", async () => {
    const run = vi.fn();
    const actions = ["a", "b", "c", "d", "e", "f"].map((id) =>
      act1(id, id === "b" ? { primary: true, run } : {}),
    );
    const { container, root } = await show(3, actions);
    expect(
      container.querySelector('[role="group"]')?.getAttribute("aria-label"),
    ).toBe("Bulk actions");
    expect(container.textContent).toContain("3 selected");
    expect(container.querySelectorAll(".cx-button--primary").length).toBe(1);
    expect(container.querySelector(".cx-button--primary")?.textContent).toBe(
      "Action b",
    );
    const inMore = container.querySelector(".cx-bulkbar__more")!;
    expect(inMore.textContent).toContain("Action e");
    expect(inMore.textContent).toContain("Action f");
    expect(MAX_BULK_VISIBLE).toBe(4);
    const visible = [...container.querySelectorAll("button")].filter(
      (b) => !inMore.contains(b),
    );
    expect(visible.map((b) => b.textContent)).toEqual([
      "Action a",
      "Action b",
      "Action c",
      "Action d",
    ]);
    await act(async () =>
      [...container.querySelectorAll("button")]
        .find((b) => b.textContent === "Action b")!
        .click(),
    );
    expect(run).toHaveBeenCalledOnce();
    await act(async () => root.unmount());
  });

  it("makes the first action primary when none is marked and says why one is unavailable", async () => {
    const { container, root } = await show(1, [
      act1("a", { disabled: true, reason: "Choose a track to move to." }),
      act1("b"),
    ]);
    const first = container.querySelector("button")!;
    expect(first.className).toContain("cx-button--primary");
    expect(first.disabled).toBe(true);
    const reason = document.getElementById(
      first.getAttribute("aria-describedby")!,
    )!;
    expect(reason.textContent).toBe("Choose a track to move to.");
    await act(async () => root.unmount());
  });
});
