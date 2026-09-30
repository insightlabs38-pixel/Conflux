"""Guards the test-only fast password hasher (tests/conftest.py): production configuration must
remain a strong, salted, slow hasher and must still authenticate real logins."""

import json

import config.settings as production_settings
import pytest
from django.conf import global_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import get_hashers
from django.test import Client, override_settings

STRONG_PREFIXES = ("pbkdf2_sha256$", "argon2$", "bcrypt_sha256$", "scrypt$")


def production_hashers() -> list[str]:
    return list(getattr(production_settings, "PASSWORD_HASHERS", global_settings.PASSWORD_HASHERS))


def test_production_settings_do_not_configure_a_fast_hasher():
    hashers = production_hashers()
    assert hashers, "production must configure at least one password hasher"
    assert not any("MD5" in name or "SHA1" in name or "Unsalted" in name for name in hashers[:1])
    assert "PBKDF2" in hashers[0] or "Argon2" in hashers[0] or "Scrypt" in hashers[0]


def test_the_suite_uses_the_fast_hasher_only_through_the_test_override():
    assert type(get_hashers()[0]).__name__ == "MD5PasswordHasher"
    assert "MD5" not in " ".join(production_hashers())


@pytest.mark.django_db
def test_login_works_end_to_end_with_the_production_hasher():
    User = get_user_model()
    with override_settings(PASSWORD_HASHERS=production_hashers()):
        user = User.objects.create_user(username="hash-fidelity", password="correct horse battery")
        assert user.password.startswith(STRONG_PREFIXES)
        client = Client()

        def login(password):
            return client.post(
                "/api/v1/accounts/login/",
                json.dumps({"username": "hash-fidelity", "password": password}),
                content_type="application/json",
            )

        assert login("wrong password").status_code == 401
        assert login("correct horse battery").status_code == 200
