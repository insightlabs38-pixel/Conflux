"""Vote casting per identity mode (COM-001/002/003): window enforcement is
server-side and identical across modes; only how the voter's identity is
established (and therefore what `voter_key` becomes) differs.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import EmailVoteToken, Vote, VoteIdentityMode, VoteToken, _generate_token

EMAIL_TOKEN_LIFETIME = timedelta(hours=24)


def require_open(plan, at=None):
    at = at or timezone.now()
    if at < plan.opens_at:
        raise ValidationError("Voting has not opened yet.")
    if at >= plan.closes_at:
        raise ValidationError("Voting has closed.")


def _cast(plan, project, voter_key):
    vote = Vote(plan=plan, project=project, voter_key=voter_key)
    vote.full_clean()
    vote.save()
    return vote


def cast_authenticated_vote(plan, user, project):
    if plan.identity_mode != VoteIdentityMode.AUTHENTICATED:
        raise ValidationError("This event does not use authenticated voting.")
    require_open(plan)
    return _cast(plan, project, f"user:{user.public_id}")


def request_email_vote_token(plan, email):
    if plan.identity_mode != VoteIdentityMode.EMAIL_LINK:
        raise ValidationError("This event does not use email-link voting.")
    require_open(plan)
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


def cast_email_vote(plan, token_value, project):
    if plan.identity_mode != VoteIdentityMode.EMAIL_LINK:
        raise ValidationError("This event does not use email-link voting.")
    require_open(plan)
    with transaction.atomic():
        token = (
            EmailVoteToken.objects.select_for_update().filter(plan=plan, token=token_value).first()
        )
        if token is None or not token.is_valid():
            raise ValidationError("This voting link is invalid or has expired.")
        vote = _cast(plan, project, f"email:{token.email}")
        token.redeemed_at = timezone.now()
        token.save(update_fields=["redeemed_at"])
    return vote


def cast_token_vote(plan, token_value, project):
    if plan.identity_mode != VoteIdentityMode.TOKEN:
        raise ValidationError("This event does not use token voting.")
    require_open(plan)
    with transaction.atomic():
        token = VoteToken.objects.select_for_update().filter(plan=plan, token=token_value).first()
        if token is None:
            raise ValidationError("Invalid voting token.")
        if token.redeemed_at is not None:
            raise ValidationError("This voting token has already been used.")
        vote = _cast(plan, project, f"token:{token.public_id}")
        token.redeemed_at = timezone.now()
        token.save(update_fields=["redeemed_at"])
    return vote
