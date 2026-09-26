import secrets

from core.models import PublicIdModel
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(PublicIdModel, AbstractUser):
    """Identity record. Seeded acceptance identities set an unusable password
    (see `seed_acceptance_identities`) so a pre-issued Session token never
    doubles as a guessable normal-login credential.
    """


def _generate_token():
    return secrets.token_urlsafe(32)


class Session(PublicIdModel):
    """A server-side, DB-backed login session addressed by an opaque cookie
    token. Deliberately not Django's contrib.sessions: acceptance credentials
    need a session that can be created out-of-band (seeded, with a fixed
    token) without ever exercising the password check, while an interactive
    login goes through the exact same table and cookie mechanism.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    token = models.CharField(max_length=64, unique=True, db_index=True, default=_generate_token)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    seed_label = models.CharField(max_length=64, blank=True, default="")

    def is_expired(self):
        return self.expires_at is not None and self.expires_at < timezone.now()

    @classmethod
    def issue(cls, user, *, token=None, ttl=None, seed_label=""):
        expires_at = timezone.now() + ttl if ttl else None
        kwargs = {"user": user, "expires_at": expires_at, "seed_label": seed_label}
        if token:
            kwargs["token"] = token
        return cls.objects.create(**kwargs)
