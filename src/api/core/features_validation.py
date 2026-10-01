"""Verifier for the `validation` property (PD-F003-B01-T02): backend validation and invariants.

Validation is server-side and keyed: a record the domain refuses is refused with a message naming
the part that is wrong. A `provided` claim names where it is enforced and what proves it:

- `check:<dotted path>`: the function, class or model method that enforces an invariant;
- `constraint:<app.Model>.<name>`: a database or model constraint, read from the model's own meta;
- `test:<path>::<name>`: a test that sends something invalid and sees it refused (a CI check
  confirms the file and the test exist).

Derived, not declared: an unsaved blank record is refused with a message per required field
(`clean_fields`), and a blank record never crashes the model's own `clean()`.
"""

import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models

from . import features
from .features import problem

TEST_REF = re.compile(r"^tests/[\w/]+\.py::test_\w+$|^src/api/[\w/]+\.py::test_\w+$")


def _blank_fields(model) -> list[str] | None:
    try:
        model().clean_fields()
    except ValidationError as error:
        return sorted(getattr(error, "message_dict", {}))
    except Exception:  # noqa: BLE001
        return None
    return []


def _blank_full_clean(model) -> str:
    """`ok`, or the name of what a blank record's `full_clean` raised instead of a keyed error."""
    try:
        model().full_clean(validate_unique=False, validate_constraints=False)
    except ValidationError:
        return "ok"
    except Exception as error:  # noqa: BLE001
        return type(error).__name__
    return "ok"


def facts(feature, system) -> dict:
    model = system.model(feature.model)
    if model is None:
        return {}
    return {
        "blank_refused": _blank_fields(model) or [],
        "constraints": sorted(c.name for c in model._meta.constraints),
        "own_clean": getattr(model, "clean", None) is not models.Model.clean,
    }


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="validation"))

    model = system.model(feature.model)
    if model is None:
        return found
    kinds = {"check": 0, "constraint": 0, "test": 0}
    for ref in claim.refs:
        kind, _, value = ref.partition(":")
        if kind not in kinds:
            bad("bad_ref", f"'{ref}' is not check:, constraint: or test:.")
            continue
        kinds[kind] += 1
        if (
            kind == "check"
            and system.resolve(value) is None
            and system.resolve_method(value) is None
        ):
            bad("check_missing", f"'{value}' does not resolve.")
        elif kind == "constraint":
            label, _, name = value.rpartition(".")
            owner = system.model(label)
            if owner is None or name not in {c.name for c in owner._meta.constraints}:
                bad("constraint_missing", f"'{value}' is not a constraint of that model.")
        elif kind == "test" and not TEST_REF.match(value):
            bad("test_ref", f"'{value}' is not <tests path>.py::test_name.")
    if kinds["check"] + kinds["constraint"] == 0:
        bad("no_enforcement", "Name where the invariants are enforced (check: or constraint:).")
    if kinds["test"] == 0:
        bad("no_test", "Name a test that sends something invalid and sees it refused.")
    blank = _blank_fields(model)
    if blank is None:
        bad("blank_error", "Validating a blank record raised something other than a keyed error.")
    elif not blank:
        bad(
            "blank_accepted", "A blank record passes field validation; a required field is missing."
        )
    crash = _blank_full_clean(model)
    if crash != "ok":
        bad("blank_crashes", f"A blank record's full_clean raised {crash} instead of keyed errors.")
    return found


def static(feature, claim, root) -> list[dict]:
    """CI: every `test:` ref names a file and a test function that exist."""
    found = []
    for ref in claim.refs:
        if not ref.startswith("test:"):
            continue
        path, _, name = ref[5:].partition("::")
        file = Path(root) / path
        if not file.is_file():
            found.append(
                problem(
                    "test_file", f"'{path}' does not exist.", feature=feature.key, prop="validation"
                )
            )
        elif not re.search(rf"^(?:async )?def {re.escape(name)}\b", file.read_text(), flags=re.M):
            found.append(
                problem(
                    "test_name",
                    f"'{name}' is not in '{path}'.",
                    feature=feature.key,
                    prop="validation",
                )
            )
    return found


features.register_verifier("validation", verify, facts=facts, static=static)
