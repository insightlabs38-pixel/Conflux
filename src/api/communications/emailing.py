"""The email delivery seam referenced (and deliberately deferred) by
community.models.EmailVoteToken: the first real `django.core.mail` usage in
this codebase. `settings.EMAIL_BACKEND` defaults to Django's console backend
(no network, no external dependency) so offline runs stay fully functional;
a deployment that wants real delivery sets `DJANGO_EMAIL_BACKEND` to the
SMTP backend and supplies `EMAIL_HOST`/etc. Either way, email is a
best-effort side channel on top of the in-app inbox (communications.models
.MessageRecipient), never the only copy of a message.
"""

from django.conf import settings
from django.core.mail import get_connection, send_mail


def deliver_email(*, to_email: str, subject: str, body: str) -> str | None:
    """Send one email. Returns None on success, or an error string on
    failure -- never raises, since a broken/unconfigured transport must
    not block the in-app delivery it accompanies.
    """
    try:
        connection = get_connection()
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            connection=connection,
            fail_silently=False,
        )
        return None
    except Exception as exc:  # any transport failure is recorded, never raised
        return str(exc)[:300]
