"""Portable Ed25519 envelope for a canonical event archive."""

import base64
import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.core.exceptions import ValidationError
from presentation.keys import private_key, public_key_pem

ENVELOPE_VERSION = 1


def _canonical(value):
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValidationError({"archive": "Archive must contain JSON values."}) from exc


def _sha256(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _key_id(key):
    raw = key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


def sign_archive(archive):
    if not isinstance(archive, dict):
        raise ValidationError({"archive": "Archive must be an object."})
    key = private_key()
    manifest = {
        "envelope_version": ENVELOPE_VERSION,
        "archive_sha256": _sha256(archive),
        "checksums": {name: _sha256(value) for name, value in sorted(archive.items())},
        "signing_key_sha256": _key_id(key.public_key()),
    }
    signature = base64.urlsafe_b64encode(key.sign(_canonical(manifest))).decode("ascii")
    return {
        "manifest": manifest,
        "archive": archive,
        "public_key_pem": public_key_pem(),
        "signature": signature,
    }


def verify_signed_archive(envelope, *, trusted_public_key_pem=None):
    if not isinstance(envelope, dict) or set(envelope) != {
        "manifest",
        "archive",
        "public_key_pem",
        "signature",
    }:
        raise ValidationError({"envelope": "Invalid signed archive envelope."})
    manifest = envelope["manifest"]
    archive = envelope["archive"]
    if not isinstance(manifest, dict) or set(manifest) != {
        "envelope_version",
        "archive_sha256",
        "checksums",
        "signing_key_sha256",
    }:
        raise ValidationError({"manifest": "Invalid signed archive manifest."})
    if manifest["envelope_version"] != ENVELOPE_VERSION:
        raise ValidationError({"manifest": "Unsupported signed archive envelope version."})
    if not isinstance(archive, dict) or not isinstance(manifest["checksums"], dict):
        raise ValidationError({"archive": "Invalid signed archive content."})
    if manifest["archive_sha256"] != _sha256(archive) or manifest["checksums"] != {
        name: _sha256(value) for name, value in sorted(archive.items())
    }:
        raise ValidationError({"archive": "Signed archive checksum mismatch."})
    try:
        key = serialization.load_pem_public_key(envelope["public_key_pem"].encode("ascii"))
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError("Expected Ed25519 public key")
        if manifest["signing_key_sha256"] != _key_id(key):
            raise ValueError("Signing key fingerprint mismatch")
        signature = base64.b64decode(envelope["signature"], altchars=b"-_", validate=True)
        key.verify(signature, _canonical(manifest))
    except (InvalidSignature, ValueError, TypeError, AttributeError, UnicodeError) as exc:
        raise ValidationError(
            {"signature": "Invalid signed archive signature or public key."}
        ) from exc
    if trusted_public_key_pem is not None and envelope["public_key_pem"] != trusted_public_key_pem:
        raise ValidationError({"signature": "Signed archive key is not trusted."})
    return archive
