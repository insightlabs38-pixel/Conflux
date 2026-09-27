"""Vote casting per identity mode (COM-001/002/003): window enforcement is
server-side and identical across modes; only how the voter's identity is
established (and therefore what `voter_key` becomes) differs.

Abuse signaling (ABUSE-001/002) lives inline here rather than bolted on
after: every rejected attempt (rate limit, token replay, invalid token,
duplicate vote) is exactly the moment that has the facts worth recording.
Every AbuseSignal write happens strictly *after* the atomic block that
detected the problem has already exited/rolled back -- an exception raised
from inside a `with transaction.atomic()` unwinds that block before
reaching an enclosing `except`, so recording the signal there (rather than
inside the block) is what keeps the signal itself from being rolled back
along with the failed vote.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import abuse
from .models import (
    AbuseSignalType,
    EmailVoteToken,
    Vote,
    VoteIdentityMode,
    VoteToken,
    _generate_token,
)

EMAIL_TOKEN_LIFETIME = timedelta(hours=24)
EMAIL_TOKEN_REQUEST_LIMIT = (3, timedelta(minutes=10))  # per (plan, email)
EMAIL_TOKEN_REQUEST_IP_LIMIT = (
    20,
    timedelta(hours=1),
)  # per (plan, client ip): catches enumeration
VOTE_ATTEMPT_IP_LIMIT = (30, timedelta(hours=1))  # per (plan, client ip)


class _InvalidToken(Exception):
    pass


class _TokenReplay(Exception):
    pass


def require_open(plan, at=None):
    at = at or timezone.now()
    if at < plan.opens_at:
        raise ValidationError("Voting has not opened yet.")
    if at >= plan.closes_at:
        raise ValidationError("Voting has closed.")


def cast_authenticated_vote(plan, user, project, *, client_ip=None):
    if plan.identity_mode != VoteIdentityMode.AUTHENTICATED:
        raise ValidationError("This event does not use authenticated voting.")
    require_open(plan)
    if client_ip:
        limit, window = VOTE_ATTEMPT_IP_LIMIT
        abuse.enforce_rate_limit(plan, "vote_attempt", client_ip, limit=limit, window=window)
    try:
        with transaction.atomic():
            vote = Vote(plan=plan, project=project, voter_key=f"user:{user.public_id}")
            vote.full_clean(validate_unique=False, validate_constraints=False)
            vote.save()
    except IntegrityError as exc:
        abuse.record_signal(
            plan,
            AbuseSignalType.DUPLICATE_VOTE_ATTEMPT,
            "A voter who already cast a ballot attempted to vote again.",
        )
        raise ValidationError("You have already voted in this event.") from exc
    return vote


def normalize_vote_email(email):
    if not isinstance(email, str):
        raise ValidationError({"email": "Enter a valid email address."})
    email = email.strip().casefold()
    validate_email(email)
    return email


def enforce_email_request_limits(plan, email, client_ip=None):
    limit, window = EMAIL_TOKEN_REQUEST_LIMIT
    abuse.enforce_rate_limit(
        plan, "email_token_request_by_email", email, limit=limit, window=window
    )
    if client_ip:
        ip_limit, ip_window = EMAIL_TOKEN_REQUEST_IP_LIMIT
        abuse.enforce_rate_limit(
            plan, "email_token_request_by_ip", client_ip, limit=ip_limit, window=ip_window
        )


def request_email_vote_token(plan, email, *, client_ip=None, limits_checked=False):
    if plan.identity_mode != VoteIdentityMode.EMAIL_LINK:
        raise ValidationError("This event does not use email-link voting.")
    require_open(plan)
    email = normalize_vote_email(email)
    if not limits_checked:
        enforce_email_request_limits(plan, email, client_ip)
    token, _ = EmailVoteToken.objects.update_or_create(
        plan=plan,
        email=email,
        defaults={
            "token": _generate_token(),
            "expires_at": timezone.now() + EMAIL_TOKEN_LIFETIME,
            "redeemed_at": None,
        },
    )
    return token


def cast_email_vote(plan, token_value, project, *, client_ip=None):
    if plan.identity_mode != VoteIdentityMode.EMAIL_LINK:
        raise ValidationError("This event does not use email-link voting.")
    require_open(plan)
    if client_ip:
        limit, window = VOTE_ATTEMPT_IP_LIMIT
        abuse.enforce_rate_limit(plan, "vote_attempt", client_ip, limit=limit, window=window)
    try:
        with transaction.atomic():
            token = (
                EmailVoteToken.objects.select_for_update()
                .filter(plan=plan, token=token_value)
                .first()
            )
            if token is None:
                raise _InvalidToken
            if not token.is_valid():
                raise _TokenReplay
            vote = Vote(plan=plan, project=project, voter_key=f"email:{token.email}")
            vote.full_clean(validate_unique=False, validate_constraints=False)
            vote.save()
            token.redeemed_at = timezone.now()
            token.save(update_fields=["redeemed_at"])
    except _InvalidToken:
        abuse.record_signal(
            plan,
            AbuseSignalType.INVALID_TOKEN_ATTEMPT,
            "An unrecognized email vote token was used.",
        )
        raise ValidationError("This voting link is invalid or has expired.") from None
    except _TokenReplay:
        abuse.record_signal(
            plan,
            AbuseSignalType.TOKEN_REPLAY_ATTEMPT,
            "An already-used or expired email vote token was used again.",
        )
        raise ValidationError("This voting link is invalid or has expired.") from None
    except IntegrityError as exc:
        abuse.record_signal(
            plan,
            AbuseSignalType.DUPLICATE_VOTE_ATTEMPT,
            "A voter who already cast a ballot attempted to vote again.",
        )
        raise ValidationError("You have already voted in this event.") from exc
    return vote


def cast_token_vote(plan, token_value, project, *, client_ip=None):
    if plan.identity_mode != VoteIdentityMode.TOKEN:
        raise ValidationError("This event does not use token voting.")
    require_open(plan)
    if client_ip:
        limit, window = VOTE_ATTEMPT_IP_LIMIT
        abuse.enforce_rate_limit(plan, "vote_attempt", client_ip, limit=limit, window=window)
    try:
        with transaction.atomic():
            token = (
                VoteToken.objects.select_for_update().filter(plan=plan, token=token_value).first()
            )
            if token is None:
                raise _InvalidToken
            if token.redeemed_at is not None:
                raise _TokenReplay
            vote = Vote(plan=plan, project=project, voter_key=f"token:{token.public_id}")
            vote.full_clean(validate_unique=False, validate_constraints=False)
            vote.save()
            token.redeemed_at = timezone.now()
            token.save(update_fields=["redeemed_at"])
    except _InvalidToken:
        abuse.record_signal(
            plan, AbuseSignalType.INVALID_TOKEN_ATTEMPT, "An unrecognized voting token was used."
        )
        raise ValidationError("Invalid voting token.") from None
    except _TokenReplay:
        abuse.record_signal(
            plan,
            AbuseSignalType.TOKEN_REPLAY_ATTEMPT,
            "An already-redeemed voting token was used again.",
        )
        raise ValidationError("This voting token has already been used.") from None
    except IntegrityError as exc:
        abuse.record_signal(
            plan,
            AbuseSignalType.DUPLICATE_VOTE_ATTEMPT,
            "A voter who already cast a ballot attempted to vote again.",
        )
        raise ValidationError("You have already voted in this event.") from exc
    return vote
