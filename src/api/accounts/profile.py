"""Privacy-aware reusable identity, without participation or scoring disclosures."""

import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from workspaces.models import Membership


def safe_profile_url(value, *, allow_blank=False):
    if value == "" and allow_blank:
        return value
    if not isinstance(value, str) or len(value) > 2048 or re.search(r'[\s\\<>"\x00-\x1f]', value):
        raise ValidationError("Use an absolute HTTP(S) URL without credentials or markup.")
    try:
        url = urlsplit(value)
        valid = url.scheme in ("http", "https") and url.hostname and url.username is None
    except ValueError:
        valid = False
    if not valid:
        raise ValidationError("Use an absolute HTTP(S) URL without credentials or markup.")
    return value


def clean_links(value):
    if not isinstance(value, list) or len(value) > 6:
        raise ValidationError("Use at most six structured links.")
    for link in value:
        if not isinstance(link, dict) or set(link) != {"label", "url"}:
            raise ValidationError("Each link needs a label and URL.")
        if not isinstance(link["label"], str) or not 1 <= len(link["label"].strip()) <= 50:
            raise ValidationError("Link labels must contain 1–50 characters.")
        safe_profile_url(link["url"])
    return [{"label": item["label"].strip(), "url": item["url"]} for item in value]


def clean_tags(value):
    if not isinstance(value, list) or len(value) > 12:
        raise ValidationError("Use at most twelve tags.")
    if any(
        not isinstance(tag, str)
        or not 1 <= len(tag.strip()) <= 40
        or re.search(r"[\x00-\x1f]", tag)
        for tag in value
    ):
        raise ValidationError("Tags need 1–40 characters without control characters.")
    if len({tag.strip().casefold() for tag in value}) != len(value):
        raise ValidationError("Tags must be unique, ignoring case.")
    return [tag.strip() for tag in value]


def identity_for(user, *, viewer=None, workspace=None):
    profile = getattr(user, "profile", None)
    identity = {
        "user_public_id": str(user.public_id),
        "username": user.username,
        "display_name": user.username,
        "avatar_url": "",
        "bio": "",
        "location": "",
        "links": [],
        "profile_url": "",
        "skills": [],
        "interests": [],
        "preferred_roles": [],
    }
    if profile is None:
        return identity
    allowed = profile.visibility == "public" or (viewer is not None and viewer.pk == user.pk)
    if profile.visibility == "members" and not allowed:
        if workspace is not None:
            allowed = Membership.objects.filter(user=user, workspace=workspace).exists()
        elif viewer is not None and viewer.is_authenticated:
            allowed = Membership.objects.filter(
                user=user,
                workspace__in=Membership.objects.filter(user=viewer).values("workspace_id"),
            ).exists()
    if allowed:
        identity.update(
            {
                name: getattr(profile, name)
                for name in (
                    "avatar_url",
                    "bio",
                    "location",
                    "links",
                    "skills",
                    "interests",
                    "preferred_roles",
                )
            }
        )
        identity["display_name"] = profile.display_name or user.username
        identity["profile_url"] = f"/app/?person={user.public_id}"
    return identity
