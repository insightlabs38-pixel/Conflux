"""Verifier for the `privacy` property (PD-F003-B03-T02): what happens to a person's data.

The platform has one subject-export, erasure and retention service (`integrations.privacy`): a
person's rows in an event are either erased (`_personal`), retained as evidence with a stated reason
(`_retained`) or, for private files, purged in two phases (`_private_artifacts`). A feature either
holds data about a person and says what becomes of it, or says it holds none, and a claim is held
to that service and to the model:

- `erased:<bucket>`, `retained:<bucket>`, `purged:<bucket>` (zero or more): the bucket is one of
  the service's, of that kind, and its model is the feature's own model or one that reaches it by
  at most two foreign keys; no bucket is claimed by two features, and every bucket whose model *is*
  the feature's own must be claimed;
- `person:<field>=<fate>[@<reason>]` (one per user column of the feature's model, derived): what
  becomes of the person a column names. `erased` needs an erased bucket on the feature's own model,
  `purged` a purged one, and `retained` and `staff` (an organizer acting in their role) a reason of
  at least 20 characters. A user column that is not claimed fails, so a new one cannot be missed;
- `no_personal_data@<reason>`: the model holds no user column and no bucket, and why;
- `test:<path>::<name>`: the proof, a test that exports and erases a real subject (CI checks it
  exists).

A bucket no feature owns is named in `OUTSIDE` (`tests/integration/test_feature_privacy.py`, which
also proves the claims by exporting and erasing a real subject: erased rows are gone, retained rows
are kept and reported, purged files are marked and the other person's data is untouched). The
report lists each bucket and the fate of each person column.
"""

import re

from . import features
from .features import problem

MIN_REASON = 20
SERVICE = "integrations.privacy"
KINDS = ("erased", "retained", "purged")
FATES = ("erased", "retained", "purged", "staff")

OUTSIDE = {
    "marketplace_profiles": "a team-matching profile, not a feature of the registry yet",
    "saved_searches": "a person's saved public search, not a feature of the registry yet",
    "check_ins": "an on-site check-in of a participant, not a feature of the registry yet",
    "attendance": "an on-site attendance record, not a feature of the registry yet",
    "person_labels": "a label an organizer gave a person, not a feature of the registry yet",
}


def parse(claim):
    buckets = {k: [] for k in KINDS}
    persons, tests, reasons, other = [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind in KINDS:
            buckets[kind].append(rest)
        elif kind == "person":
            body, _, why = rest.partition("@")
            field, _, fate = body.partition("=")
            persons.append((field, fate, why))
        elif kind == "test":
            tests.append(rest)
        elif head == "no_personal_data":
            reasons.append(reason)
        else:
            other.append(ref)
    return buckets, persons, tests, reasons, other


def service_buckets(system) -> dict[str, tuple[str, str]]:
    """bucket -> (kind, model label), read from the service's own query builders."""
    event_model, user_model = system.model("events.Event"), system.model("accounts.User")
    personal = system.resolve(f"{SERVICE}:_personal")
    retained = system.resolve(f"{SERVICE}:_retained")
    private = system.resolve(f"{SERVICE}:_private_artifacts")
    if not (event_model and user_model and personal and retained and private):
        return {}
    event, user = event_model(pk=1), user_model(pk=1)
    found = {n: ("erased", q.model._meta.label) for n, q in personal(event, user).items()}
    found |= {n: ("retained", q.model._meta.label) for n, q in retained(event, user).items()}
    found["private_artifacts"] = ("purged", private(event, user).model._meta.label)
    return found


def user_columns(feature, system) -> list[str]:
    model, user = system.model(feature.model), system.model("accounts.User")
    if model is None or user is None:
        return []
    return sorted(
        f.name
        for f in model._meta.get_fields()
        if f.is_relation and f.many_to_one and f.related_model is user
    )


def facts(feature, system) -> dict:
    claim = feature.claims.get("privacy")
    if claim is None or claim.state != "provided":
        return {}
    buckets, persons, _, reasons, _ = parse(claim)
    if reasons:
        return {"privacy": "no personal data", "why": reasons[0]}
    found = {kind: names for kind, names in buckets.items() if names}
    if persons:
        found["people"] = [f"{field}: {fate}" for field, fate, _ in persons]
    return found


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="privacy"))

    buckets, persons, tests, reasons, other = parse(claim)
    for ref in other:
        bad(
            "bad_ref",
            f"'{ref}' is not erased:, retained:, purged:, person:, test: or no_personal_data@.",
        )
    table = service_buckets(system)
    if not table:
        bad("service_missing", f"The privacy service '{SERVICE}' cannot be read.")
        return found
    columns = user_columns(feature, system)
    exact = {n: k for n, (k, label) in table.items() if label == feature.model}
    if reasons:
        if any(buckets.values()) or persons or tests:
            bad("both", "A feature cannot hold personal data and say it holds none.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why it holds none (a short sentence).")
        for column in columns:
            bad("personal_exists", f"{feature.model}.{column} names a person; claim its fate.")
        for name in sorted(exact):
            bad(
                "personal_exists", f"The privacy service handles the bucket '{name}' of this model."
            )
        return found
    if not any(buckets.values()) and not persons:
        bad(
            "no_answer",
            "Name what becomes of the data (erased:, retained:, purged:, person:) or say none.",
        )
    if not tests:
        bad("no_test", "Name the test that exports and erases a subject (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    claimed = set()
    for kind, names in buckets.items():
        for name in names:
            if name in claimed:
                bad("bucket_twice", f"'{name}' is claimed twice.")
            claimed.add(name)
            if name not in table:
                bad("bucket_unknown", f"'{name}' is not a bucket of the privacy service.")
                continue
            if table[name][0] != kind:
                bad("bucket_kind", f"'{name}' is {table[name][0]}, not {kind}.")
            label = table[name][1]
            if (
                label != feature.model
                and system.fk_path(system.model(label), feature.model, 2) is None
            ):
                bad("bucket_foreign", f"'{name}' ({label}) does not reach {feature.model}.")
            for other_feature in features.FEATURES.values():
                other_claim = other_feature.claims.get("privacy")
                if (
                    other_feature.key != feature.key
                    and other_claim is not None
                    and other_claim.state == "provided"
                    and name in {n for names_ in parse(other_claim)[0].values() for n in names_}
                ):
                    bad("bucket_shared", f"'{name}' is also claimed by '{other_feature.key}'.")
    for name in sorted(set(exact) - claimed):
        bad("bucket_unclaimed", f"The privacy service handles '{name}' of this model; claim it.")
    named = [field for field, _, _ in persons]
    for field in sorted(set(columns) - set(named)):
        bad("person_unclaimed", f"{feature.model}.{field} names a person; claim its fate.")
    for field, fate, why in persons:
        if field not in columns:
            bad("person_unknown", f"{feature.model} has no user column '{field}'.")
        if named.count(field) > 1:
            bad("person_twice", f"'{field}' is claimed twice.")
        if fate not in FATES:
            bad("person_fate", f"'{fate}' is not one of {', '.join(FATES)}.")
        elif fate in ("erased", "purged") and fate not in {exact.get(n) for n in claimed}:
            bad(
                "person_unbacked",
                f"'{field}' is {fate}, but no {fate} bucket of this model is claimed.",
            )
        elif fate in ("retained", "staff") and len(why.strip()) < MIN_REASON:
            bad("no_reason", f"Say why {field} is {fate} (a short sentence after @).")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "privacy")


features.register_verifier("privacy", verify, facts=facts, static=static)
