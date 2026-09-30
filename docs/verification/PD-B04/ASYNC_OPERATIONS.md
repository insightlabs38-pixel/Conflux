# PD-B04-T05 — async-operation UI contract

Source of truth: `src/web/hooks/useOperation.ts` (lifecycle and rules, in its header comment) and `src/web/components/OperationStatus.tsx` (the one surface). Use it for anything a user starts that is not an immediate read: a write that takes a moment, a multi-step transfer, a server job. Short single-request saves may keep a plain busy flag until their panel migrates (T07), but must not invent another lifecycle.

```
idle -> pending (+ optional progress) -> success | failed | cancelled
```

| Rule               | Behavior                                                                                                                                                                                                            | Proof                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| One run at a time  | `start` while pending is ignored: no double submit                                                                                                                                                                  | `useOperation.test.tsx`                                                           |
| Cancel             | aborts the run's `AbortSignal`; ends `cancelled` (never an error, no alert); the late outcome of that run cannot change state                                                                                       | hook test; browser: the held storage request is aborted, `complete/` never called |
| Point of no return | `commit()` ends the cancellable window (Cancel is no longer rendered) once finishing is safer than stopping, e.g. after every part is stored                                                                        | hook test; `ArtifactPanel.operation.test.tsx`                                     |
| Failure and retry  | failure keeps the arguments and shows the server's message as an alert with Try again; retry is always a user action, never automatic (a write may not be idempotent; automatic retry is for reads, `lib/query.ts`) | hook test; browser retry starts a fresh attempt                                   |
| Progress           | reported with `report({ label, done?, total? })`; a bar only when `done` and `total` are both known, otherwise the label                                                                                            | `OperationStatus.test.tsx`; browser `<progress max=2>`                            |
| Announcement       | pending/success/cancelled: polite `role=status` (pending also `aria-busy`); failure: `role=alert`                                                                                                                   | component tests; axe clean while pending                                          |
| Unmount            | aborts the work and never sets state afterwards                                                                                                                                                                     | hook test                                                                         |
| Authority          | never optimistic: success is what the server confirmed. A durable server job (ASYNC_JOB, planned) is polled inside `run`, reporting its progress                                                                    | n/a until that primitive exists                                                   |

## Adopted now

`ArtifactPanel` (the only genuinely long, multi-step user operation today): evidence upload (prepare, per-part upload with a determinate bar, verify) and link check. Cancel aborts presigned PUTs; from "all parts stored" onwards it is committed and Cancel disappears. Failed part: alert with the reason and Try again (a fresh upload intent; abandoned intents expire on the server as before).

## Not yet on the contract

The remaining panels' `run(action)` helpers (busy flag plus inline error) are single-request writes; they move with the T07 workspace migration. Server-side long jobs (imports, bulk apply, exports) arrive with ASYNC_JOB and consume this contract as is.
