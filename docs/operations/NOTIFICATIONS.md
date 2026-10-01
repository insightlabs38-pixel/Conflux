# Notification preferences (NOTIFICATIONS)

One model for "who wants which notification, on which channel". Code: `core/notifications.py` (categories, the question delivery code asks, the stored choice), `core/notification_views.py` (a person's own settings endpoint), `communications/notifications.py` (the categories the inbox delivers); web `lib/notifications.ts` and `features/profile/NotificationPreferences.tsx` (Profile > Notification preferences). Adopters: organizer broadcasts and reminders (`communications/services.py`) and mention notices (`communications/threads.py`).

## The rule

- **Two channels.** `inbox` is the in-app copy and is **always delivered**: nothing is lost whatever anyone chooses. `email` is a best-effort side channel a person may turn off per category and per workspace.
- **Essential notices cannot be turned off** on any channel (security, account and event-safety notices). An opt-out only ever removes the optional email.
- **No stored choice means the category's default**, so adding preferences changed nothing for anyone. Announcements and reminders still email everyone with an address; mention notices start email-off (they were inbox-only before) and email only people who asked for it.
- A person reads and writes only their own choices (the endpoint has no user to name). Each change is audited as `notification_preference.changed` with category, channel, before and after, never message content. A repeat of the same choice is a no-op and writes no audit row.

## Categories

| Category       | Delivered today by                                        | Email default | Can be turned off |
| -------------- | --------------------------------------------------------- | ------------- | ----------------- |
| `announcement` | organizer messages, reminders, bulk sends                 | on            | email             |
| `mention`      | "someone mentioned you" notices                           | off           | email             |
| `essential`    | (the rule for security and safety notices; no sender yet) | always        | never             |

`approval` and `job` notices are named in the contract but nothing sends them yet, so they are not registered: a toggle for something that is never sent would be a lie. The first feature that sends one registers its category with `register_category` and asks `wants`.

## Using it

```python
from core import notifications
notifications.register_category(notifications.Category(
    "digest", "Weekly digest", "A summary of the week.", email_default=False))   # in AppConfig.ready()
for user in notifications.wanting(users, workspace, "digest", notifications.EMAIL):   # one query
    send_the_email(user)          # the inbox copy is written for everyone regardless
```

`wants(user, workspace, category, channel)` is the single-person form. An unregistered category or channel raises `KeyError` (a programming error, loud in tests).

## Endpoint

`GET /api/v1/workspaces/{workspace}/notification-preferences/` returns `{categories: [{category, label, description, essential, channels: [{channel, label, enabled, locked, default, chosen}]}]}` for the caller. `PUT` with `{category, channel, enabled}` records one choice and returns the same list. 400 names the field (`category`, `channel`, `enabled`; a locked channel explains why); workspace members only (403 otherwise).

## Compatibility

One additive table, `core_notificationpreference` (`core/0006`), unique per person, workspace, category and channel, removed with the person or the workspace. No existing delivery changes for a person with no stored choice. `MessageRecipient` still records the in-app copy for everyone; an opted-out person simply has no email timestamp.

## Verification

`tests/integration/test_notifications.py` covers defaults, per-workspace scope, locked channels (even against a row written around the API), idempotency and audit, the endpoint's field errors and membership rules, both adopters through the real send path (Django's mail outbox), one-query `wanting`, and an independent feature registering its own category; `tests/integration/concurrency/test_notification_races.py` races six first choices on PostgreSQL.
