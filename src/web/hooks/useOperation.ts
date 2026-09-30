import { useCallback, useEffect, useRef, useState } from "react";

/**
 * The async-operation contract (PD-B04-T05) for anything a user starts that is not an immediate
 * read: a write that takes a moment, a multi-step transfer, a server-side job. Every such action
 * shares one lifecycle and one surface (`components/OperationStatus.tsx`).
 *
 *   idle -> pending (+ optional progress) -> success | failed | cancelled
 *
 * Rules (each has a test in `useOperation.test.tsx`)
 * - One run at a time: `start` while pending is ignored, so a double click cannot submit twice.
 * - Cancel aborts the run's `AbortSignal` and ends in `cancelled` (never an error). A run can end
 *   its cancellable window with `commit()` once continuing is safer than stopping (e.g. after the
 *   server accepted the upload); cancel is then not offered.
 * - A cancelled, superseded or unmounted run can never change state or report progress later.
 * - Failure keeps the arguments; `retry()` re-runs the same request on the user's say-so. There is
 *   never an automatic retry: a write may not be idempotent (automatic retry belongs to reads, see
 *   lib/query.ts).
 * - Outcomes are announced: pending/success/cancelled in a polite live region, failure as an alert
 *   with the server's message and a retry.
 * - Progress is honest: determinate only when `done` and `total` are known, otherwise a label.
 * - The result of the server remains authority; the hook never marks success optimistically. For a
 *   durable server job (ASYNC_JOB, planned) `run` polls the job and reports its progress.
 */
export type Progress = { label: string; done?: number; total?: number };

export type OperationState<T> =
  | { status: "idle" }
  | { status: "pending"; progress: Progress | null; cancellable: boolean }
  | { status: "success"; result: T }
  | { status: "failed"; error: string }
  | { status: "cancelled" };

export type OperationContext = {
  signal: AbortSignal;
  report: (progress: Progress) => void;
  /** The point of no return: cancel is no longer offered and the run finishes. */
  commit: () => void;
};

function messageOf(error: unknown): string {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string" && error) return error;
  return "The operation failed.";
}

export function useOperation<A, T>(
  run: (args: A, context: OperationContext) => Promise<T>,
) {
  const [state, setState] = useState<OperationState<T>>({ status: "idle" });
  const latestRun = useRef(run);
  latestRun.current = run;
  const current = useRef<{ token: number; controller: AbortController } | null>(
    null,
  );
  const token = useRef(0);
  const lastArgs = useRef<{ args: A } | null>(null);
  const cancellable = useRef(true);
  const pending = useRef(false);

  useEffect(
    () => () => {
      // Unmount: stop the work and make sure nothing reports afterwards.
      token.current += 1;
      current.current?.controller.abort();
    },
    [],
  );

  const start = useCallback(async (args: A): Promise<boolean> => {
    if (pending.current) return false;
    pending.current = true;
    cancellable.current = true;
    lastArgs.current = { args };
    const mine = ++token.current;
    const controller = new AbortController();
    current.current = { token: mine, controller };
    const live = () => token.current === mine;
    setState({ status: "pending", progress: null, cancellable: true });
    try {
      const result = await latestRun.current(args, {
        signal: controller.signal,
        report: (progress) => {
          if (live())
            setState({
              status: "pending",
              progress,
              cancellable: cancellable.current,
            });
        },
        commit: () => {
          cancellable.current = false;
          if (live())
            setState((now) =>
              now.status === "pending" ? { ...now, cancellable: false } : now,
            );
        },
      });
      if (!live()) return false;
      pending.current = false;
      setState({ status: "success", result });
      return true;
    } catch (error) {
      if (!live()) return false;
      pending.current = false;
      setState({ status: "failed", error: messageOf(error) });
      return false;
    }
  }, []);

  const cancel = useCallback(() => {
    if (!pending.current || !cancellable.current) return;
    token.current += 1; // invalidates the run before its abort rejection arrives
    current.current?.controller.abort();
    pending.current = false;
    setState({ status: "cancelled" });
  }, []);

  const retry = useCallback(
    () =>
      lastArgs.current ? start(lastArgs.current.args) : Promise.resolve(false),
    [start],
  );

  const reset = useCallback(() => {
    if (pending.current) return;
    setState({ status: "idle" });
  }, []);

  return {
    state,
    busy: state.status === "pending",
    start,
    cancel,
    retry,
    reset,
  };
}
