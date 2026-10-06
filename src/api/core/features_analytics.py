"""Verifier for the `analytics` property (PD-F003-B03-T01): a feature's place in the event summary.

The platform has one analytics summary (`communications.analytics.compute_analytics`, served at
`operations/analytics/`): sections of counts and rates over an event, computed from the domain's own
tables and never stored. A feature either is counted in it or says why it is not, and a claim is
held to the module:

- `section:<name>`: the section of the summary (a field of `EventAnalyticsResponse`) that counts
  the feature's records, and the feature's own model is one the analytics module works on, so a
  feature cannot claim a section it has no part in;
- `measure:<section.key>` (one or more): a number, rate or list in that section the feature owns;
- `dimension:<field>=<section.key>` (optional): the summary breaks a measure down by a field of the
  feature's model (`status`), and the breakdown's keys are the field's own choices;
- `test:<path>::<name>`: the proof, a test that computes the summary for a real event and finds
  every measure and breakdown (CI checks it exists);
- `no_analytics@<reason>`: the summary does not count the feature, and why; a feature whose
  measures are owed is `planned` with the owning task.

A section no feature owns and a counted model no feature covers are named in `OUTSIDE_SECTIONS`
and `OUTSIDE_MODELS`, so a new section cannot appear unowned
(`tests/integration/test_feature_analytics.py`, which also proves every claimed measure and
breakdown against a real event). The report lists each section, its measures and the dimensions it
breaks them down by.
"""

import importlib
import re

from django.db.models import Model

from . import features
from .features import problem

MIN_REASON = 20
MODULE = "communications.analytics"
SERIALIZER = "communications.analytics_views:EventAnalyticsResponse"
ENVELOPE = {"event", "generated_at"}  # the response fields that are not sections

OUTSIDE_SECTIONS = {
    "voting": "community voting is not a feature of the registry yet",
}
OUTSIDE_MODELS = {
    "participation.TeamMembership": "a member row, counted only to say whether a team has members",
    "projects.SubmissionVersion": "an immutable copy of a submission, counted under its submission",
    "evaluations.Ballot": "a judge's scores, counted under the evaluation plan it belongs to",
    "evaluations.PairwiseComparison": "a judge's comparison, counted under its evaluation plan",
    "community.Vote": "a vote of the community, which is not a feature of the registry yet",
    "community.VotingPlan": "the setup of community voting, not a feature of the registry yet",
}


def parse(claim):
    sections, measures, dimensions, tests, reasons, other = [], [], [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "section":
            sections.append(rest)
        elif kind == "measure":
            measures.append(rest)
        elif kind == "dimension":
            field, _, path = rest.partition("=")
            dimensions.append((field, path))
        elif kind == "test":
            tests.append(rest)
        elif head == "no_analytics":
            reasons.append(reason)
        else:
            other.append(ref)
    return sections, measures, dimensions, tests, reasons, other


def sections(system) -> set[str]:
    serializer = system.resolve(SERIALIZER)
    return set(serializer().fields) - ENVELOPE if serializer else set()


def counted_models() -> set[str]:
    """The models the analytics module works on: the model classes it imports."""
    try:
        module = importlib.import_module(MODULE)
    except ImportError:
        return set()
    return {
        value._meta.label
        for value in vars(module).values()
        if isinstance(value, type) and issubclass(value, Model) and not value._meta.abstract
    }


def facts(feature, system) -> dict:
    claim = feature.claims.get("analytics")
    if claim is None or claim.state != "provided":
        return {}
    named, measures, dimensions, _, reasons, _ = parse(claim)
    if reasons:
        return {"analytics": "not counted", "why": reasons[0]}
    found = {"summary": named, "measures": measures}
    if dimensions:
        found["dimensions"] = [f"{field} → {path}" for field, path in dimensions]
    return found


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="analytics"))

    named, measures, dimensions, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not section:, measure:, dimension:, test: or no_analytics@.")
    counted = feature.model in counted_models()
    if reasons:
        if named or measures or dimensions or tests:
            bad("both", "A feature cannot be counted and say it is not.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why the summary does not count it (a short sentence).")
        if counted:
            bad("analytics_exists", f"The analytics module works on {feature.model}; claim it.")
        return found
    if len(named) != 1:
        bad("one_section", "Name the one summary section that counts the feature (section:).")
    if not measures:
        bad("no_measure", "Name each measure the feature owns (measure:<section.key>).")
    if not tests:
        bad("no_test", "Name the test that computes the summary (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    known = sections(system)
    if not known:
        bad("summary_missing", f"The analytics summary '{SERIALIZER}' cannot be read.")
        return found
    if not counted:
        bad("model_not_counted", f"The analytics module does not work on {feature.model}.")
    section = named[0] if named else None
    if section is not None and section not in known:
        bad("section_unknown", f"'{section}' is not a section of the summary.")
    for path in (*measures, *(p for _, p in dimensions)):
        if not re.fullmatch(r"[a-z_]+(?:\.[a-z_]+)+", path):
            bad("path_shape", f"'{path}' is not a section.key path.")
        elif section is not None and path.partition(".")[0] != section:
            bad("path_foreign", f"'{path}' is not in the section '{section}'.")
    if len(set(measures)) != len(measures):
        bad("measure_twice", "A measure is claimed twice.")
    model = system.model(feature.model)
    for field, _ in dimensions:
        try:
            column = model._meta.get_field(field)
        except Exception:
            bad("dimension_field", f"{feature.model} has no field '{field}'.")
            continue
        if not getattr(column, "choices", None):
            bad("dimension_choices", f"'{field}' has no fixed choices to break a measure down by.")
    for other_feature in features.FEATURES.values():
        other_claim = other_feature.claims.get("analytics")
        if (
            other_feature.key != feature.key
            and other_claim is not None
            and other_claim.state == "provided"
        ):
            shared = set(measures) & set(parse(other_claim)[1])
            for path in sorted(shared):
                bad("measure_shared", f"'{path}' is also claimed by '{other_feature.key}'.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "analytics")


features.register_verifier("analytics", verify, facts=facts, static=static)
