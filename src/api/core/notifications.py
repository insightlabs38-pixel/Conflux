"""Who wants which notification, on which channel (NOTIFICATIONS, PD-F002-B02-T04).

A feature that tells people things registers a **category** once; delivery code asks one question
before it sends, and the profile shows one list. No feature adds a notification table or its own
opt-out flag:

    notifications.register_category(notifications.Category(
        "mention", "Mentions", "Someone mentioned you in a comment.", email_default=False))
    ...
    for user in notifications.wanting(users, workspace, "mention", "email"):
        send_the_email(user)

Rules
- Two channels. `inbox` is the in-app copy and is **always delivered**: nothing is lost whatever
  anyone chooses. `email` is a best-effort side channel a person may turn off, per category and
  workspace.
- An **essential** category (security, account and safety notices) cannot be turned off on any
  channel. An opt-out only ever removes the optional email.
- A person with no stored choice gets the category's default, so adding this changed nothing for
  anyone: broadcasts still email as before, and a category new to email starts off.
- A person reads and writes only their own choices. Each change is audited (category, channel,
  before and after; never message content).
- `wants` and `wanting` decide delivery only; they never decide who is in an audience.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from audit.services import record_mutation
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from .models import NotificationPreference

INBOX = "inbox"
EMAIL = "email"
CHANNELS = {
    INBOX: "In-app inbox",
    EMAIL: "Email",
}


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    description: str
    essential: bool = False
    email_default: bool = True


CATEGORIES: dict[str, Category] = {}


def register_category(category: Category) -> None:
    if category.key in CATEGORIES and CATEGORIES[category.key] != category:
        raise ValueError(f"Notification category '{category.key}' is already registered.")
    CATEGORIES[category.key] = category


def category(key: str) -> Category:
    try:
        return CATEGORIES[key]
    except KeyError:
        raise KeyError(f"Notification category '{key}' is not registered.") from None


def locked(cat: Category, channel: str) -> bool:
    """True when the person cannot change this channel for this category."""
    return channel == INBOX or cat.essential


def default(cat: Category, channel: str) -> bool:
    return True if channel == INBOX or cat.essential else cat.email_default


def _stored(user_ids, workspace, key, channel):
    return dict(
        NotificationPreference.objects.filter(
            user_id__in=user_ids, workspace=workspace, category=key, channel=channel
        ).values_list("user_id", "enabled")
    )


def wanting(users: Iterable, workspace, key: str, channel: str) -> list:
    """The users who want `key` on `channel`, in their original order (one query)."""
    cat = category(key)
    if channel not in CHANNELS:
        raise KeyError(f"Unknown channel '{channel}'.")
    users = list(users)
    if locked(cat, channel):
        return users
    stored = _stored([u.pk for u in users], workspace, key, channel)
    fallback = default(cat, channel)
    return [u for u in users if stored.get(u.pk, fallback)]


def wants(user, workspace, key: str, channel: str) -> bool:
    return bool(wanting([user], workspace, key, channel))


def describe(user, workspace) -> list[dict]:
    """Every category with each channel's current value, for the person's own settings page."""
    rows = {
        (p.category, p.channel): p.enabled
        for p in NotificationPreference.objects.filter(user=user, workspace=workspace)
    }
    out = []
    for cat in sorted(CATEGORIES.values(), key=lambda c: (c.essential, c.label)):
        channels = []
        for channel, label in CHANNELS.items():
            fixed = locked(cat, channel)
            value = True if fixed else rows.get((cat.key, channel), default(cat, channel))
            channels.append(
                {
                    "channel": channel,
                    "label": label,
                    "enabled": value,
                    "locked": fixed,
                    "default": default(cat, channel),
                    "chosen": (cat.key, channel) in rows and not fixed,
                }
            )
        out.append(
            {
                "category": cat.key,
                "label": cat.label,
                "description": cat.description,
                "essential": cat.essential,
                "channels": channels,
            }
        )
    return out


def set_preference(user, workspace, key: str, channel: str, enabled: bool) -> bool:
    """Record the person's choice. Returns True when it changed anything. Idempotent."""
    if key not in CATEGORIES:
        raise ValidationError({"category": [f"There is no notification category '{key}'."]})
    cat = CATEGORIES[key]
    if channel not in CHANNELS:
        raise ValidationError({"channel": [f"Use one of: {', '.join(CHANNELS)}."]})
    if locked(cat, channel):
        reason = (
            "Essential notices are always delivered."
            if cat.essential
            else "The in-app inbox copy is always kept."
        )
        raise ValidationError({"channel": [reason]})
    with transaction.atomic():
        lookup = {"user": user, "workspace": workspace, "category": key, "channel": channel}
        row = (
            NotificationPreference.objects.select_for_update(of=("self",)).filter(**lookup).first()
        )
        before = row.enabled if row else default(cat, channel)
        if row is None:
            try:
                with transaction.atomic():
                    row = NotificationPreference.objects.create(**lookup, enabled=enabled)
            except IntegrityError:  # a concurrent first choice won the race
                row = NotificationPreference.objects.select_for_update(of=("self",)).get(**lookup)
                before = row.enabled
                if row.enabled == enabled:
                    return False
                row.enabled = enabled
                row.save()
        elif row.enabled == enabled:
            return False
        else:
            row.enabled = enabled
            row.save()
        record_mutation(
            actor=user,
            workspace=workspace,
            action="notification_preference.changed",
            target=row,
            metadata={"category": key, "channel": channel, "before": before, "after": enabled},
        )
    return True
