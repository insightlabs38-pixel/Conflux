import hashlib
import secrets

from core.models import PublicIdModel
from django.conf import settings
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


def digest_api_token(token):
    return hashlib.sha256(f"{settings.SECRET_KEY}:{token}".encode()).hexdigest()


class ApiCredential(PublicIdModel):
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", null=True, blank=True, on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    token_digest = models.CharField(max_length=64, unique=True, db_index=True)
    allowed_actions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        return self.revoked_at is None and self.expires_at > timezone.now() and self.owner.is_active


class LoginFailure(models.Model):
    """One failed password attempt, kept only to throttle guessing per account.
    Stores the normalized username, never the password or the client address.
    """

    username = models.CharField(max_length=150, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
