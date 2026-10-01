// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Modal } from "./Modal";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => (document.body.innerHTML = ""));

function Harness({ onClose }: { onClose: () => void }) {
  const [confirming, setConfirming] = useState(false);
  return (
    <Modal titleId="t" onClose={onClose}>
      <h2 id="t">Title</h2>
      {confirming ? (
        <button onClick={() => setConfirming(false)}>Done</button>
      ) : (
        <button onClick={() => setConfirming(true)}>Ask</button>
      )}
    </Modal>
  );
}

describe("Modal", () => {
  it("closes on Escape from inside, and still after its focused button went away", async () => {
    const onClose = vi.fn();
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () => root.render(<Harness onClose={onClose} />));
    const ask = container.querySelector("button")!;
    ask.focus();
    await act(async () => ask.click());
    await act(async () => {
      container.querySelector("button")!.click(); // the confirmation vanishes with focus on it
    });
    (document.activeElement as HTMLElement | null)?.blur();
    await act(async () => {
      document.body.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
      );
    });
    expect(onClose).toHaveBeenCalledTimes(1);
    await act(async () => root.unmount());
  });
});
