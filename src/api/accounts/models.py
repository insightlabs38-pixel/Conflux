import hashlib
import hmac
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


def digest_session_token(token):
    """Keyed one-way digest used to look sessions up. Session tokens are
    256-bit random values, so a fast HMAC (not a password hash) is sufficient;
    the key means a leaked database row cannot be checked against guesses.
    """
    key = f"conflux-session-token:{settings.SECRET_KEY}".encode()
    return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()


class Session(PublicIdModel):
    """A server-side, DB-backed login session addressed by an opaque cookie
    token. Deliberately not Django's contrib.sessions: acceptance credentials
    need a session that can be created out-of-band (seeded, with a fixed
    token) without ever exercising the password check, while an interactive
    login goes through the exact same table and cookie mechanism.

    Only `token_digest` is persisted. The raw token exists once, as the
    transient `token` attribute of the instance returned by `issue()`, and is
    handed to the client in the cookie; a database reader cannot replay it.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    token_digest = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    seed_label = models.CharField(max_length=64, blank=True, default="")

    def is_expired(self):
        return self.expires_at is not None and self.expires_at < timezone.now()

    @classmethod
    def issue(cls, user, *, token=None, ttl=None, seed_label=""):
        expires_at = timezone.now() + ttl if ttl else None
        token = token or _generate_token()
        session = cls.objects.create(
            user=user,
            token_digest=digest_session_token(token),
            expires_at=expires_at,
            seed_label=seed_label,
        )
        session.token = token  # transient: never saved
        return session

    @classmethod
    def lookup(cls, token):
        return cls.objects.filter(token_digest=digest_session_token(token))


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


class ExternalIdentity(PublicIdModel):
    """A user's stable identity at an external OpenID Connect provider,
    keyed by (issuer, subject) -- never by email, which providers may reuse.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="external_identities"
    )
    issuer = models.CharField(max_length=300)
    subject = models.CharField(max_length=255)
    email = models.CharField(max_length=254, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["issuer", "subject"], name="unique_external_identity")
        ]


class OidcLoginState(models.Model):
    """One in-flight sign-in. Single use: the callback deletes the row before
    doing anything else, so a replayed `state` finds nothing. `browser_hash`
    ties the attempt to the browser that started it (login-CSRF defence).
    """

    state_hash = models.CharField(max_length=64, unique=True)
    browser_hash = models.CharField(max_length=64)
    nonce = models.CharField(max_length=64)
    code_verifier = models.CharField(max_length=128)
    next_path = models.CharField(max_length=500, default="/")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class UserProfile(PublicIdModel):
    """Reusable opt-in identity; event matching and expertise stay in their domain models."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    display_name = models.CharField(max_length=120, blank=True)
    avatar_url = models.CharField(max_length=2048, blank=True)
    bio = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=120, blank=True)
    links = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    preferred_roles = models.JSONField(default=list, blank=True)
    visibility = models.CharField(
        max_length=10,
        choices=(
            ("private", "Private"),
            ("members", "Shared workspace members"),
            ("public", "Public"),
        ),
        default="private",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from .profile import clean_links, clean_tags, safe_profile_url

        self.links = clean_links(self.links)
        for name in ("skills", "interests", "preferred_roles"):
            setattr(self, name, clean_tags(getattr(self, name)))
        safe_profile_url(self.avatar_url, allow_blank=True)
