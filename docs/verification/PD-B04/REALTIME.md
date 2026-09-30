# PD-B04-T06 — realtime subscription boundary

Source of truth: `src/web/lib/realtime.ts` (hub, transports, rules in its header) and `src/web/hooks/useRealtime.tsx` (React binding). Screens depend on these two files only; the transport is a plug (`RealtimeTransport.open(topic, deliver, setStatus)`), so the app shell is coupled to no protocol.

| Piece                                                         | Role                                                                                                                                                                                                                              |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RealtimeHub`                                                 | ref-counted topic subscriptions (one transport subscription per topic, closed with the last subscriber), burst coalescing (`coalesceMs`, default 250), handler isolation, per-topic `ConnectionStatus`, `reset()` for the session |
| `pollingTransport`                                            | the transport that works against today's API: a periodic hint (default 60 s), paused while the tab is hidden or offline, one hint on resume/online; status `polling` / `offline`                                                  |
| `manualTransport`                                             | driven by hand for tests and demos                                                                                                                                                                                                |
| `useRealtime`, `useRealtimeInvalidate`, `useConnectionStatus` | subscribe while mounted and enabled; the standard consumer turns a hint into a server-state refetch                                                                                                                               |
| `RealtimeProvider`                                            | one hub per `App` (injectable); no provider means every hook is a no-op                                                                                                                                                           |

Rules: a hint is never data (it triggers an authorized refetch, so a spoofed or replayed hint costs one read); topics are `<scope>:<id>:<resource>`; live updates never touch drafts (only server state is invalidated); the hub is reset on sign-in and sign-out like the query cache; transport trouble is a status, never a user-facing error. A push transport (SSE/WebSocket) is one more `RealtimeTransport`; there is no push channel in the API yet, so none is built (would be speculative).

## Applied now

The inbox (`features/communications/Inbox.tsx`, shown in participant, judge and staff workspaces) moved onto the server-state layer (`queryKeys.inbox`) and subscribes to `workspace:<id>:inbox`: a new message appears within one poll interval instead of only after a reload, and marking read updates the cached list from the server's answer. Traffic cost: one small GET per minute per visible tab with an inbox mounted.

## Evidence

`lib/realtime.test.ts` (ref-count, coalescing, handler isolation, status, reset, polling interval, hidden/visible pause and resume, offline), `hooks/useRealtime.test.tsx` (hint refetches and status, no-op without hub or when disabled, latest handler, unsubscribe on unmount, session reset), `Inbox.test.tsx` (hint shows the server's new list and the topic closes with the screen), browser `realtime.spec.ts` (Playwright clock: one inbox GET per 60 s interval, none after sign-out).

## Not covered

No push transport or reconnect/backoff policy (needs a server channel; the interface already carries `connecting`/`live`); other candidates (operator console counts, judge assignments) adopt `useRealtimeInvalidate` when they move to the server-state layer (T07).
