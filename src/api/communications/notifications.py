"""The notification categories the inbox and its email side channel deliver (PD-F002-B02-T04).

`core.notifications` owns the rule (the inbox copy is always kept, an essential category is never
optional, an unset choice is the default); this module only names what communications sends.
"""

from core import notifications

# Organizer broadcasts and reminders: emailed to everyone with an address, as always, until a
# person turns the email off.
ANNOUNCEMENT = "announcement"
# "Someone mentioned you" (core threads): inbox only until a person asks for email too.
MENTION = "mention"
# Security, account and event-safety notices: always delivered, on every channel.
ESSENTIAL = "essential"

notifications.register_category(
    notifications.Category(
        ANNOUNCEMENT,
        "Announcements and reminders",
        "Messages and reminders from the organizers of this workspace's events.",
    )
)
notifications.register_category(
    notifications.Category(
        MENTION,
        "Mentions",
        "Someone mentioned you in a comment. The notice never contains the comment itself.",
        email_default=False,
    )
)
notifications.register_category(
    notifications.Category(
        ESSENTIAL,
        "Account and safety notices",
        "Security, account and event-safety notices. These are always delivered.",
        essential=True,
    )
)
