// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useOperation, type OperationContext } from "./useOperation";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: ReturnType<typeof createRoot>;
let op: ReturnType<typeof useOperation<string, string>>;

function Harness({
  run,
}: {
  run: (args: string, context: OperationContext) => Promise<string>;
}) {
  op = useOperation<string, string>(run);
  return null;
}
const mount = (run: (args: string, c: OperationContext) => Promise<string>) =>
  act(() => root.render(<Harness run={run} />));

/** A run the test resolves or rejects by hand. */
function deferred() {
  const calls: {
    args: string;
    context: OperationContext;
    resolve: (value: string) => void;
    reject: (error: unknown) => void;
  }[] = [];
  const run = (args: string, context: OperationContext) =>
    new Promise<string>((resolve, reject) => {
      calls.push({ args, context, resolve, reject });
    });
  return { run, calls };
}

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

describe("useOperation", () => {
  it("goes idle, pending, success with the result", async () => {
    const d = deferred();
    mount(d.run);
    expect(op.state).toEqual({ status: "idle" });
    let started!: Promise<boolean>;
    act(() => {
      started = op.start("a");
    });
    expect(op.state).toMatchObject({ status: "pending", cancellable: true });
    expect(op.busy).toBe(true);
    await act(async () => d.calls[0].resolve("done"));
    expect(await started).toBe(true);
    expect(op.state).toEqual({ status: "success", result: "done" });
    expect(op.busy).toBe(false);
  });

  it("ignores a second start while one is running (no double submit)", async () => {
    const d = deferred();
    mount(d.run);
    act(() => void op.start("a"));
    let second = true;
    await act(async () => {
      second = await op.start("b");
    });
    expect(second).toBe(false);
    expect(d.calls).toHaveLength(1);
  });

  it("fails with the error message, keeps the arguments, and retries only on request", async () => {
    const d = deferred();
    mount(d.run);
    act(() => void op.start("args-1"));
    await act(async () => d.calls[0].reject(new Error("Disk full.")));
    expect(op.state).toMatchObject({ status: "failed", error: "Disk full." });
    // a failure with no refusal from the server does not claim the data is safe
    expect(op.state).toHaveProperty(
      "kept",
      expect.stringContaining("could not confirm"),
    );
    expect(d.calls).toHaveLength(1); // never retried by itself
    act(() => void op.retry());
    expect(d.calls).toHaveLength(2);
    expect(d.calls[1].args).toBe("args-1");
    await act(async () => d.calls[1].resolve("ok"));
    expect(op.state).toEqual({ status: "success", result: "ok" });
  });

  it("uses a generic message when the failure has none", async () => {
    const d = deferred();
    mount(d.run);
    act(() => void op.start("a"));
    await act(async () => d.calls[0].reject(undefined));
    expect(op.state).toMatchObject({
      status: "failed",
      error: "The operation failed.",
    });
  });

  it("cancels: aborts the signal, ends cancelled (not failed) and ignores the late outcome", async () => {
    const d = deferred();
    mount(d.run);
    act(() => void op.start("a"));
    const { context } = d.calls[0];
    act(() => op.cancel());
    expect(context.signal.aborted).toBe(true);
    expect(op.state).toEqual({ status: "cancelled" });
    await act(async () =>
      d.calls[0].reject(new DOMException("aborted", "AbortError")),
    );
    expect(op.state).toEqual({ status: "cancelled" });
    // a run that ignores the abort and still resolves cannot flip the state either
    act(() => void op.retry());
    act(() => op.cancel());
    await act(async () => d.calls[1].resolve("late"));
    expect(op.state).toEqual({ status: "cancelled" });
  });

  it("stops offering cancel after commit and ignores cancel then", async () => {
    const d = deferred();
    mount(d.run);
    act(() => void op.start("a"));
    act(() => d.calls[0].context.commit());
    expect(op.state).toMatchObject({ status: "pending", cancellable: false });
    act(() => op.cancel());
    expect(d.calls[0].context.signal.aborted).toBe(false);
    expect(op.state.status).toBe("pending");
    await act(async () => d.calls[0].resolve("finished"));
    expect(op.state).toEqual({ status: "success", result: "finished" });
  });

  it("reports progress while pending and never after the run ended", async () => {
    const d = deferred();
    mount(d.run);
    act(() => void op.start("a"));
    act(() =>
      d.calls[0].context.report({ label: "Part 2 of 4", done: 1, total: 4 }),
    );
    expect(op.state).toMatchObject({
      status: "pending",
      progress: { label: "Part 2 of 4", done: 1, total: 4 },
    });
    act(() => op.cancel());
    act(() => d.calls[0].context.report({ label: "ghost" }));
    expect(op.state).toEqual({ status: "cancelled" });
  });

  it("aborts on unmount and never updates state afterwards", async () => {
    const d = deferred();
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    mount(d.run);
    act(() => void op.start("a"));
    const { context } = d.calls[0];
    act(() => root.unmount());
    expect(context.signal.aborted).toBe(true);
    await act(async () => d.calls[0].resolve("late"));
    expect(errors).not.toHaveBeenCalled();
    errors.mockRestore();
    root = createRoot(container); // for afterEach
  });

  it("reset clears a finished operation but not a running one", async () => {
    const d = deferred();
    mount(d.run);
    act(() => void op.start("a"));
    act(() => op.reset());
    expect(op.state.status).toBe("pending");
    await act(async () => d.calls[0].resolve("x"));
    act(() => op.reset());
    expect(op.state).toEqual({ status: "idle" });
  });
});
