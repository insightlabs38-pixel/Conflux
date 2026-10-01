# Approval gates (APPROVAL)

A second person confirms one exact operation before it runs. Code: `core/approvals.py` (contract), `core/approval_views.py` (endpoints), web `lib/approvals.ts` and `features/operations/ApprovalsPanel.tsx`. First adopter: sending a message to an audience (`communications/approvals.py`).

## What it is, and is not

A gate wraps an operation **whose effect is unchanged**. It never computes a score, a winner, a permission, a deadline or a policy outcome, and it does not decide any official result: it only holds an operation until another person with a deciding role says yes. Gates are **off by default** per event, so nothing changes until an organizer switches one on (Operations > Approvals, or the setting `approvals.message_send`, tier advanced).

## Lifecycle

```
pending -> approved | rejected | cancelled | expired
approved -> executed | cancelled | expired
```

Transitions only follow `approvals.TRANSITIONS`, under a row lock; a closed request never changes again. One pending request exists per (event, operation, digest) (a database constraint), so two people asking for the same thing share one request.

- **Digest binds the approval to the content.** `digest = sha256(action, subject, payload)`. Approvers read the request's `summary` (what the adopter chose to show: for a message the subject, recipient count, audience and text); an approval is only spendable on an operation with the same digest. A changed body or audience is a different operation and needs its own request.
- **Single use.** An approved request is consumed (`executed`) inside the operation's own transaction, so if the operation fails or rolls back the approval is still there; once it commits the approval is spent and the same operation needs a new one.
- **Who decides.** The policy names deciding roles and `min_approvals`. The asker cannot approve their own request (`requester_may_approve`, default false). A person answers once; one rejection ends the request. A participant (or anyone without a deciding role) gets 404, not 403.
- **Expiry.** A request, and an approval nobody used, is valid for the policy's `ttl` (72 h). Expiry is enforced when deciding and consuming (so it holds even before the sweep) and a beat sweep (every 5 minutes) marks them. Lists show a lapsed request as `expired`.
- **Audit.** `approval.requested`, `decision_recorded`, `approved`, `rejected`, `cancelled`, `expired`, `executed` and `approval.gate_changed` (with before and after) are all audited.

## Adopting it

```python
from core import approvals
approvals.register_policy(approvals.ApprovalPolicy(
    "my_op", "What it is called", "One sentence for the settings screen.",
    deciders=(Role.ORGANIZER, Role.ADMIN), min_approvals=1))

# inside the operation's transaction, just before the effect:
approvals.require_approval(event=event, actor=actor, action="my_op",
    payload={...exact content...}, summary=["Do X to 12 people"], subject=("event", event.public_id))
```

and in the view: `except approvals.ApprovalRequired as needed: return needed.respond(request.user)`, which opens (or finds) the pending request outside the rolled-back transaction and answers **409 `{"code": "approval_required", "detail", "approval": {...}}`**. Register in `AppConfig.ready()`, and expose the gate as a setting in `eventconfig/registry.py` (`approvals.<action>`, write `PUT .../approval-gates/<action>/`). In a preview (`approvals.dry_run()`), a needed approval is collected instead of raised, so the bulk planner shows "Another person has to approve this first" without opening anything.

## API

| Call                                                          | Notes                                                                                     |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `GET /workspaces/{w}/events/{e}/approvals/`                   | `status`, `action`, `limit`, `offset`; the asker's own plus those the caller may decide   |
| `GET .../approvals/{id}/`                                     | summary, decisions, `can_decide`, `can_cancel`                                            |
| `POST .../approvals/{id}/decision/`                           | `{decision: approve or reject, note}`; 409 `approval_closed` if already closed or expired |
| `POST .../approvals/{id}/cancel/`                             | the asker or a decider                                                                    |
| `GET .../approval-gates/`, `PUT .../approval-gates/{action}/` | organizer or admin; `{enabled}`; refused on an archived event                             |

## Adopter: messages

`create_inbox_message` (used by `POST communications/messages/` and the bulk planner's `send`) calls the gate after the audience is resolved, so the summary can say "Send “Welcome” to 120 people." and the same approval covers the message whichever door it came through. The bulk preview lists `approvals` when a gate applies; applying without one is held (409) and nothing is sent.

## Compatibility and limits

Additive: tables `core_approvalgate`, `core_approvalrequest`, `core_approvaldecision` (migration `core/0004_approvals`), new endpoints, one new setting, one optional `approvals` key in a bulk preview. With the gate off, every existing response is unchanged. `EligibilityReview` and `TemporalGate` keep their own semantics. Not built: notifying deciders (they find requests in Operations > Approvals), delegation, per-audience-size thresholds, gating the other bulk actions, and the bulk planner dialog offers no `send` yet. On a single-organizer event nobody else can approve, which is why gates are opt-in; an admin may approve.
