"""Isolated browser-test fixtures (PD-B03-T02).

A fixture is an ordinary generated demo scenario (`generate_demo_event` + `demo_showcase`)
on a seed from a reserved range, so every invariant, audit row and permission still applies
and `scripts/demo-reset` / seed 7 are never involved. Only seeds at or above
`FIXTURE_SEED_BASE` can be disposed here; the DemoScenario marker still gates the purge.
"""

import secrets
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError
from django.utils import timezone

from integrations.demo_scenarios import generate_demo_event, purge_demo_scenario
from integrations.models import DemoScenario

SCENARIO = "hackathon"
FIXTURE_SEED_BASE = 10_000_000
NONCES = 10_000  # seed = BASE + nonce * SLOTS + slot; max 10_009_999_999 < 2**31
SLOTS = 1000
MAX_ATTEMPTS = 6

# Sizes come from the labels the specs use (participant-05, judge-03; participant-24 only in
# the lifecycle canary). `published` requires live=0, so it has no on-camera participants.
PROFILES = {
    "iso-min": {"participants": 6, "judges": 3, "live": 2, "checkpoint": "submitted"},
    "iso-judged": {"participants": 6, "judges": 3, "live": 2, "checkpoint": "judged"},
    "iso-published": {"participants": 6, "judges": 3, "live": 0, "checkpoint": "published"},
    "canary": {"participants": 24, "judges": 6, "live": 2, "checkpoint": "submitted"},
}


def fixture_scenarios():
    return DemoScenario.objects.filter(scenario=SCENARIO, seed__gte=FIXTURE_SEED_BASE)


def _free_seed(nonce):
    base = FIXTURE_SEED_BASE + nonce * SLOTS
    taken = set(
        DemoScenario.objects.filter(
            scenario=SCENARIO, seed__gte=base, seed__lt=base + SLOTS
        ).values_list("seed", flat=True)
    )
    for seed in range(base, base + SLOTS):
        if seed not in taken:
            return seed
    return None


def create_fixture(profile, *, nonce=None, password=None):
    """Create one isolated fixture and return its handle.

    A taken seed is never reused or purged: the generator refuses it, and we move to another
    nonce. A failure after the scenario exists (showcase) disposes the half-built fixture.
    """
    if profile not in PROFILES:
        raise ValidationError({"profile": f"Use one of {', '.join(PROFILES)}."})
    if nonce is not None and not 0 <= nonce < NONCES:
        raise ValidationError({"nonce": f"Use 0-{NONCES - 1}."})
    password = password or secrets.token_urlsafe(12)
    spec = PROFILES[profile]
    for attempt in range(MAX_ATTEMPTS):
        chosen = nonce if nonce is not None and attempt == 0 else secrets.randbelow(NONCES)
        seed = _free_seed(chosen)
        if seed is None:
            continue
        try:
            event = generate_demo_event(
                scenario=SCENARIO, seed=seed, password=password, public=True, **spec
            )
        except (ValidationError, IntegrityError):
            # Lost a race for the same seed to another process; the generator is atomic.
            if DemoScenario.objects.filter(scenario=SCENARIO, seed=seed).exists():
                continue
            raise
        slug = event.workspace.slug
        try:
            call_command("demo_showcase", slug, password=password)
        except Exception:
            purge_demo_scenario(slug)
            raise
        return {
            "profile": profile,
            "seed": seed,
            "slug": slug,
            "workspace": str(event.workspace.public_id),
            "event": str(event.public_id),
            "password": password,
        }
    raise ValidationError({"seed": f"No free fixture seed after {MAX_ATTEMPTS} attempts."})


def dispose_fixture(slug):
    marker = DemoScenario.objects.filter(workspace__slug=slug).first()
    if marker is None:
        raise ValidationError({"slug": f"{slug} is not a generated scenario."})
    if marker.scenario != SCENARIO or marker.seed < FIXTURE_SEED_BASE:
        raise ValidationError(
            {"slug": f"{slug} is not an e2e fixture (seeds >= {FIXTURE_SEED_BASE}); refusing."}
        )
    purge_demo_scenario(slug)


def sweep_fixtures(*, older_than_minutes=0):
    """Purge leftover fixtures, e.g. failed runs whose state was kept for inspection."""
    cutoff = timezone.now() - timedelta(minutes=older_than_minutes)
    slugs = list(
        fixture_scenarios()
        .filter(created_at__lte=cutoff)
        .order_by("seed")
        .values_list("workspace__slug", flat=True)
    )
    for slug in slugs:
        dispose_fixture(slug)
    return slugs
