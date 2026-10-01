"""Verifier for the `identity` property (PD-F003-B01-T01): a stable public identity and a clear
lifecycle.

Identity: the model has a unique, non-editable UUID public id; every route named in the claim
(`route:<name>`) addresses records by public id and never by a sequential number. Lifecycle: the
declared states and graph agree with the model, every state is reachable, terminal states have no
way out and what performs the transitions exists.
"""

from django.db import models

from . import features
from .features import Lifecycle, problem

STATE_FIELDS = ("status", "state", "phase")


def _life_problems(feature, life: Lifecycle, model, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="identity"))

    kind_fields = {"choice": None, "timestamp": models.DateTimeField, "flag": models.BooleanField}
    if life.kind == "none":
        if not life.note:
            bad("lifecycle_note", "A feature without a lifecycle says how its records change.")
        for field in model._meta.get_fields():
            if getattr(field, "concrete", False) and field.name in STATE_FIELDS and field.choices:
                bad(
                    "lifecycle_hidden",
                    f"The model has a choice field '{field.name}' but no lifecycle is declared.",
                )
        return found
    if life.kind not in kind_fields:
        bad(
            "lifecycle_kind",
            f"Lifecycle kind '{life.kind}' is not choice, timestamp, flag or none.",
        )
        return found
    try:
        field = model._meta.get_field(life.field)
    except Exception:  # noqa: BLE001
        bad("lifecycle_field", f"The model has no field '{life.field}'.")
        return found
    if life.kind == "choice":
        if not field.choices:
            bad("lifecycle_field", f"'{life.field}' has no choices to read states from.")
            return found
        states = {str(value) for value, _ in field.choices}
    else:
        expected = kind_fields[life.kind]
        if not isinstance(field, expected):
            bad("lifecycle_field", f"'{life.field}' must be a {expected.__name__}.")
        if len(life.states) != 2:
            bad("lifecycle_states", "A timestamp or flag lifecycle names its two states.")
            return found
        states = {value for value, _ in life.states}
    graph = features.transition_graph(life, system)
    mentioned = set(graph) | {t for targets in graph.values() for t in targets}
    for state in sorted(mentioned - states):
        bad("lifecycle_unknown_state", f"The graph names '{state}', which is not a state.")
    for state in sorted(set(life.initial) - states):
        bad("lifecycle_unknown_state", f"Initial state '{state}' is not a state.")
    if not life.initial:
        bad("lifecycle_initial", "A lifecycle names where records start.")
    for state in sorted(set(life.terminal) - states):
        bad("lifecycle_unknown_state", f"Terminal state '{state}' is not a state.")
    for state in life.terminal:
        if graph.get(state):
            bad("lifecycle_terminal", f"Terminal state '{state}' has a way out.")
    reachable = set(life.initial)
    frontier = list(life.initial)
    while frontier:
        for target in graph.get(frontier.pop(), ()):
            if target not in reachable:
                reachable.add(target)
                frontier.append(target)
    for state in sorted(states - reachable):
        bad("lifecycle_unreachable", f"State '{state}' cannot be reached from the start.")
    if life.kind == "choice" and not isinstance(field.default, type(models.NOT_PROVIDED)):
        if field.default not in life.initial:
            bad("lifecycle_initial", f"The model starts records as '{field.default}'.")
    if not life.via:
        bad("lifecycle_via", "A lifecycle names what performs its transitions.")
    for dotted in life.via:
        if system.resolve(dotted) is None:
            bad("lifecycle_via", f"'{dotted}' does not resolve.")
    if isinstance(life.transitions, str) and system.resolve(life.transitions) is None:
        bad("lifecycle_via", f"The transition table '{life.transitions}' does not resolve.")
    return found


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="identity"))

    model = system.model(feature.model)
    if model is None:
        return found
    try:
        field = model._meta.get_field(feature.id_field)
    except Exception:  # noqa: BLE001
        bad("id_missing", f"The model has no field '{feature.id_field}'.")
    else:
        if not isinstance(field, models.UUIDField):
            bad("id_type", f"'{feature.id_field}' must be a UUID, not {type(field).__name__}.")
        if not field.unique:
            bad("id_unique", f"'{feature.id_field}' must be unique.")
        if field.editable:
            bad("id_editable", f"'{feature.id_field}' must not be editable.")
    if feature.id_field not in " ".join(
        r.partition(":")[2] for r in claim.refs if r.startswith("field:")
    ):
        bad("id_ref", f"The claim names the field 'field:{feature.id_field}'.")
    for ref in claim.refs:
        kind, _, name = ref.partition(":")
        if kind == "field":
            continue
        if kind != "route":
            bad("bad_ref", f"'{ref}' is not field:<name> or route:<url name>.")
            continue
        if name not in system.routes():
            bad("route_missing", f"There is no route named '{name}'.")
            continue
        converters = system.converters(name)
        if not any(c == "uuid" and n.endswith("_public_id") for c, n in converters):
            bad("route_id", f"Route '{name}' does not address records by a public id.")
        if any(c == "int" or n in ("pk", "id") for c, n in converters):
            bad("route_sequential", f"Route '{name}' addresses a record by a sequential number.")
    if feature.lifecycle is None:
        bad("lifecycle_missing", "Declare the lifecycle, or say there is none.")
    else:
        found += _life_problems(feature, feature.lifecycle, model, system)
    return found


features.register_verifier("identity", verify)
