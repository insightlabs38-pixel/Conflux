"""The Ed25519 keypair that signs verifiable records (REC-002).

Derived deterministically from `settings.RECORD_SIGNING_KEY_SEED` so the
same keypair is available on every process/replica without persisting key
material anywhere -- restarting the app (or scaling it out) never changes
what a previously issued record verifies against. There is exactly one
active key; v1 has no rotation or multi-key support (see
docs/architecture/VERIFIABLE_RECORDS.md).
"""

import hashlib
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.conf import settings


@lru_cache(maxsize=1)
def private_key():
    seed_bytes = hashlib.sha256(settings.RECORD_SIGNING_KEY_SEED.encode()).digest()
    return Ed25519PrivateKey.from_private_bytes(seed_bytes)


def public_key():
    return private_key().public_key()


def public_key_pem():
    return (
        public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )
