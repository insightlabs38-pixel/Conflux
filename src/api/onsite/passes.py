"""Stateless attendee passes: a signed (event, person) pair, verifiable offline
at the door. Nothing is stored, so a pass can be reprinted any time.
"""

import hashlib
import hmac
import uuid

from django.conf import settings

PREFIX = "cfx1"


def _sign(event_id, user_id):
    key = hashlib.sha256(b"onsite-pass|" + settings.SECRET_KEY.encode()).digest()
    message = f"{event_id.hex}.{user_id.hex}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()[:32]


def issue(event, user):
    signature = _sign(event.public_id, user.public_id)
    return f"{PREFIX}.{event.public_id.hex}.{user.public_id.hex}.{signature}"


def verify(token, event):
    """The person's public id (hex) if `token` is a valid pass for `event`."""
    parts = token.strip().split(".") if isinstance(token, str) else []
    if len(parts) != 4 or parts[0] != PREFIX or parts[1] != event.public_id.hex:
        return None
    try:
        user_id = uuid.UUID(hex=parts[2])
    except ValueError:
        return None
    if not hmac.compare_digest(parts[3], _sign(event.public_id, user_id)):
        return None
    return user_id
