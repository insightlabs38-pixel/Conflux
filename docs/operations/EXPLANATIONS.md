# Explanations (POLICY_EXPLAIN)

One shape for "why did this come out the way it did": a policy check, event readiness, what a delete would do, and whatever refuses something next. Code: `core/explain.py` (the shape, the builders and the three adapters), `core/explain_schema.py` (OpenAPI); web `lib/explain.ts` and `components/ExplanationView.tsx`. Adopters: the policy debugger (Setup > Policies > Check policy), the consequence dialog (every destructive or status action) and the readiness checklist (API).

## What it does and does not do

An explanation **reports a decision the domain already made; it never decides.** Nothing here computes a score, a winner, a permission, a deadline or a policy outcome, and an adapter only reads the payload the domain produced. It is derived on every read and never stored, pure, and deterministic: the same payload gives the same words in the same order. The existing endpoints keep every key they had; the explanation is added beside them as `explanation`.

## The shape

```
{outcome: allowed | blocked | needs_action | unknown,
 summary: "One sentence.",
 reasons: [{code, severity: info | warning | blocker, message, facts?: {...}, fix?: {destination, section}}],
 total, truncated}
```

`outcome` is the answer in a word (`needs_action` is for advisory warnings the person should look at; `unknown` is for "nothing was decided yet"). `facts` are short scalar values behind a message for tools, the message already states them. `fix` says where the reason is resolved. Bounds: 50 reasons (`total` counts all), messages 500 characters, 10 facts a reason, fact text 200 characters; every string is data for a text node.

## Builders and adapters

`reason(code, message, severity=, facts=, fix=)`, `explanation(outcome, summary, reasons)` and `unknown(summary)` are all a feature needs to explain its own refusal. The three adapters read existing payloads:

| Adapter                                     | Reads                                         | Says                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `from_policy_debug(payload, detailed=True)` | the policy debug result (`policies.debugger`) | allowed or blocked; the checks that decided it, named as in `team_size is 1, but it must be at least 2.`; a closed time window as a window; an `or` names every branch that failed, an `and` the first that failed, a `not` turns the requirement around; an exception grant is named and the unmet checks become notes; a policy that cannot be evaluated is blocked (fail closed) |
| `from_readiness(readiness)`                 | `eventconfig.readiness.compute_readiness`     | blocked (blockers first, then warnings) / needs attention (warnings only) / allowed; each open item with its detail and where to fix it                                                                                                                                                                                                                                             |
| `from_consequences(shown)`                  | `eventconfig.consequences.preview`            | blocked with each blocker, or allowed with each effect, and a warning `irreversible` when it cannot be undone                                                                                                                                                                                                                                                                       |

**Facts respect the reader.** `detailed=False` is for anyone not allowed to read the policy and the facts it checked: no fact value appears anywhere, only the sentence the domain chose to show that person. The policy debugger is organizer-only and uses the detailed form.

## Where it appears

- `POST .../policy-debug/` adds `explanation`; the policy builder draws it above the raw trace, which stays available under "Policy trace".
- `GET .../consequences/` adds `explanation`; the consequence dialog draws it (a blocked outcome is announced as an alert, the confirmation is still offered only when allowed).
- `GET .../readiness/`, the legacy `operations/checklist/` and the launch checklist all carry the same `explanation` (they are projections of one function and stay identical).

## Compatibility

Stateless and additive: no table, no migration. Every existing key of the three payloads is unchanged (asserted for the debugger); an older client ignores the new key.

## Verification

`tests/fixtures/explain_cases.json` holds 29 cases built from real evaluator traces and real payload shapes; pytest checks the adapters and vitest draws each result. A property test runs 600 random policies against the real evaluator and requires the explanation to agree with the decision (blocked exactly when denied, a blocker exactly when blocked, deterministic, never an exception, no facts when hidden). It also checks malformed policies, the legacy keys, the three endpoints and an independent feature building an explanation with no adapter.
