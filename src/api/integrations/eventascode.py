"""Declarative event configuration (PVS05): export a human-editable document,
validate it, plan the difference against the live event, and apply it.

Identity is by name, never by database id, so a document is portable between
events. A section that is absent is unmanaged and untouched; one that is
present is managed. Resources missing from a managed section are only removed
when `prune` is set, and immutable evidence (published rubric versions,
published awards) is never rewritten. Planning is a rolled-back trial apply,
so a plan reports exactly what apply would do and every model rule that
would reject it.
"""

import hashlib
import json
from dataclasses import dataclass, field

from awards.models import Award, PrizeComponent, PrizePackage
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils.dateparse import parse_datetime
from evaluations.models import EvaluationPlan, RubricVersion
from events.models import BasePrize, Event, EventStatus, Track
from forms.models import FormDefinition
from policies.models import Policy, PolicyBinding, TemporalGate
from presentation.models import Page, PageBlock
from projects.models import Project
from stages.models import Stage, StageTransition

DOCUMENT_VERSION = 1
SECTIONS = (
    "tracks",
    "base_prizes",
    "stages",
    "stage_transitions",
    "forms",
    "policies",
    "temporal_gates",
    "policy_bindings",
    "evaluation_plans",
    "awards",
    "page",
)
EVENT_FIELDS = ("description", "timezone", "starts_at", "ends_at")


class ConfigError(Exception):
    def __init__(self, section, key, message):
        super().__init__(message)
        self.section, self.key, self.message = section, key, message


@dataclass
class Result:
    changes: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    unmanaged: dict = field(default_factory=dict)

    def change(self, section, key, action, fields=None):
        self.changes.append(
            {"section": section, "key": key, "action": action, "fields": fields or {}}
        )

    def error(self, section, key, message):
        self.errors.append({"section": section, "key": key, "message": message})


def _iso(value):
    return value.isoformat() if value is not None else None


def _parse_dt(value):
    if value is None:
        return None
    parsed = parse_datetime(value) if isinstance(value, str) else None
    if parsed is None or parsed.tzinfo is None:
        raise ValueError("Use an ISO 8601 timestamp with an explicit UTC offset.")
    return parsed


def _dec(value):
    return None if value is None else str(value)


def _plain(value):
    return json.loads(json.dumps(value, default=str))


# ---- export -------------------------------------------------------------


def export_document(event):
    tracks = list(event.tracks.order_by("position", "name", "pk"))
    stages = list(event.stages.order_by("position", "name", "pk"))
    document = {
        "eventascode": DOCUMENT_VERSION,
        "event": {
            "description": event.description,
            "timezone": event.timezone,
            "starts_at": _iso(event.starts_at),
            "ends_at": _iso(event.ends_at),
        },
        "tracks": [
            {"name": t.name, "description": t.description, "position": t.position} for t in tracks
        ],
        "base_prizes": [
            {
                "name": p.name,
                "track": p.track.name if p.track_id else None,
                "description": p.description,
                "kind": p.kind,
                "amount": _dec(p.amount),
                "currency": p.currency,
                "position": p.position,
            }
            for p in event.base_prizes.select_related("track").order_by("position", "name", "pk")
        ],
        "stages": [
            {
                "name": s.name,
                "position": s.position,
                "is_initial": s.is_initial,
                "participation_mode": s.participation_mode,
            }
            for s in stages
        ],
        "stage_transitions": [
            {"from": t.from_stage.name, "to": t.to_stage.name}
            for t in StageTransition.objects.filter(from_stage__event=event)
            .select_related("from_stage", "to_stage")
            .order_by("from_stage__position", "to_stage__position", "pk")
        ],
        "forms": [
            {
                "name": f.name,
                "stage": f.stage.name if f.stage_id else None,
                "draft_schema": f.draft_schema,
            }
            for f in event.forms.select_related("stage").order_by("name", "pk")
        ],
        "policies": [{"name": p.name, "ast": p.ast} for p in event.policies.order_by("name", "pk")],
        "temporal_gates": [
            {"name": g.name, "opens_at": _iso(g.opens_at), "closes_at": _iso(g.closes_at)}
            for g in event.temporal_gates.order_by("name", "pk")
        ],
        "policy_bindings": [
            {"action": b.action, "policy": b.policy.name}
            for b in event.policy_bindings.select_related("policy").order_by("action", "pk")
        ],
        "evaluation_plans": [
            {
                "stage": p.stage.name,
                "name": p.name,
                "candidate_type": p.candidate_type,
                "pool_strategy": p.pool_strategy,
                "results_visible_to_participants": p.results_visible_to_participants,
                "rubric_versions": [
                    {"number": v.number, "criteria": v.criteria}
                    for v in p.rubric_versions.order_by("number")
                ],
            }
            for p in EvaluationPlan.objects.filter(stage__event=event)
            .select_related("stage")
            .order_by("stage__position", "name", "pk")
        ],
        "awards": [_award_doc(a) for a in event.awards.order_by("name", "pk")],
        "page": _page_doc(event),
    }
    return _plain(document)


def _award_doc(award):
    package = PrizePackage.objects.filter(award=award).first()
    components = package.components.order_by("position", "pk").all() if package is not None else []
    return {
        "name": award.name,
        "description": award.description,
        "eligibility_track": award.eligibility_track.name if award.eligibility_track_id else None,
        "require_finalized_submission": award.require_finalized_submission,
        "selection_source": award.selection_source,
        "evaluation_plan": (
            f"{award.evaluation_plan.stage.name}/{award.evaluation_plan.name}"
            if award.evaluation_plan_id
            else None
        ),
        "winner_count": award.winner_count,
        "allow_stacking": award.allow_stacking,
        "conflict_group": award.conflict_group,
        "components": [
            {
                "name": c.name,
                "kind": c.kind,
                "description": c.description,
                "quantity": c.quantity,
                "amount": _dec(c.amount),
                "currency": c.currency,
                "position": c.position,
            }
            for c in components
        ],
    }


def _page_doc(event):
    page = Page.objects.filter(event=event).first()
    if page is None:
        return None
    return {
        "theme": page.theme,
        "theme_config": page.theme_config,
        "blocks": [
            {"kind": b.kind, "position": b.position, "config": b.config}
            for b in page.blocks.order_by("position", "pk")
        ],
    }


def digest(event):
    payload = json.dumps(export_document(event), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


# ---- schema validation --------------------------------------------------

_ITEM_KEYS: dict[str, tuple[set, set]] = {
    "tracks": ({"name"}, {"description", "position"}),
    "base_prizes": (
        {"name", "kind"},
        {"track", "description", "amount", "currency", "position"},
    ),
    "stages": ({"name", "participation_mode"}, {"position", "is_initial"}),
    "stage_transitions": ({"from", "to"}, set()),
    "forms": ({"name"}, {"stage", "draft_schema"}),
    "policies": ({"name", "ast"}, set()),
    "temporal_gates": ({"name"}, {"opens_at", "closes_at"}),
    "policy_bindings": ({"action", "policy"}, set()),
    "evaluation_plans": (
        {"stage", "name", "candidate_type", "pool_strategy"},
        {"results_visible_to_participants", "rubric_versions"},
    ),
    "awards": (
        {"name", "selection_source"},
        {
            "description",
            "eligibility_track",
            "require_finalized_submission",
            "evaluation_plan",
            "winner_count",
            "allow_stacking",
            "conflict_group",
            "components",
        },
    ),
}
_KEY_OF = {
    "tracks": lambda i: i["name"],
    "base_prizes": lambda i: i["name"],
    "stages": lambda i: i["name"],
    "stage_transitions": lambda i: f"{i['from']} -> {i['to']}",
    "forms": lambda i: i["name"],
    "policies": lambda i: i["name"],
    "temporal_gates": lambda i: i["name"],
    "policy_bindings": lambda i: i["action"],
    "evaluation_plans": lambda i: f"{i['stage']}/{i['name']}",
    "awards": lambda i: i["name"],
}


def schema_errors(document):
    """Structural problems only; nothing here touches the database."""
    errors = []
    if not isinstance(document, dict):
        return [{"section": "document", "key": "", "message": "Document must be an object."}]
    if document.get("eventascode") != DOCUMENT_VERSION:
        errors.append(
            {
                "section": "document",
                "key": "eventascode",
                "message": f"Set eventascode to {DOCUMENT_VERSION}.",
            }
        )
    for name in set(document) - {"eventascode", "event", *SECTIONS}:
        errors.append({"section": name, "key": "", "message": "Unknown section."})
    event = document.get("event")
    if event is not None and (not isinstance(event, dict) or set(event) - set(EVENT_FIELDS)):
        errors.append(
            {
                "section": "event",
                "key": "",
                "message": f"Event may only set {', '.join(EVENT_FIELDS)}.",
            }
        )
    for section, (required, optional) in _ITEM_KEYS.items():
        items = document.get(section)
        if items is None:
            continue
        if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
            errors.append({"section": section, "key": "", "message": "Must be a list of objects."})
            continue
        seen = set()
        for item in items:
            missing = sorted(required - set(item))
            unknown = sorted(set(item) - required - optional)
            label = str(item.get("name") or item.get("action") or item.get("from") or "?")
            if missing or unknown:
                errors.append(
                    {
                        "section": section,
                        "key": label,
                        "message": f"Missing {missing}; unknown {unknown}.".replace(
                            "Missing []; ", ""
                        ).replace("; unknown []", ""),
                    }
                )
                continue
            key = _KEY_OF[section](item)
            if key in seen:
                errors.append({"section": section, "key": key, "message": "Duplicate key."})
            seen.add(key)
    page = document.get("page")
    if page is not None and (
        not isinstance(page, dict)
        or set(page) - {"theme", "theme_config", "blocks"}
        or not isinstance(page.get("blocks", []), list)
    ):
        errors.append({"section": "page", "key": "", "message": "Page needs theme and blocks."})
    return errors


# ---- apply --------------------------------------------------------------


def _model_value(model, name, value):
    kind = model._meta.get_field(name).get_internal_type()
    if kind == "DateTimeField":
        return _parse_dt(value)
    if kind == "JSONField":
        return value
    return model._meta.get_field(name).to_python(value)


def _defaults(model, item, names):
    return {n: _model_value(model, n, item[n]) for n in names if n in item}


def _set_scalars(obj, model, values):
    changed = {}
    for name, value in values.items():
        new = _model_value(model, name, value)
        old = getattr(obj, name)
        if new != old:
            changed[name] = {"before": _plain(old), "after": _plain(new)}
            setattr(obj, name, new)
    return changed


def _step(result, section, key, function):
    """Run one resource inside a savepoint so one failure never hides another."""
    try:
        with transaction.atomic():
            function()
    except ConfigError as exc:
        result.error(exc.section, exc.key, exc.message)
    except ValidationError as exc:
        if hasattr(exc, "error_dict"):
            message = "; ".join(f"{k}: {' '.join(v)}" for k, v in exc.message_dict.items())
        else:
            message = "; ".join(exc.messages)
        result.error(section, key, message)
    except ValueError as exc:
        result.error(section, key, str(exc))
    except (ProtectedError, IntegrityError) as exc:
        result.error(section, key, f"Blocked by existing data: {str(exc)[:200]}")


def _lookup(mapping, name, section, key):
    if name is None:
        return None
    if name not in mapping:
        raise ConfigError(section, key, f"Unknown reference {name!r}.")
    return mapping[name]


def _upsert(
    result, section, existing, items, model, build, scalars, prune,
    references=None, guard=None, after=None, protect_delete=None,
):  # fmt: skip
    """Create/update `items` against `existing` ({key: instance}); optionally delete extras.

    `references(obj, item)` applies name-referenced foreign keys and returns their
    changes; `guard(obj)` raises before an existing object is modified.
    """
    key_of = _KEY_OF[section]
    desired = {key_of(item): item for item in items}
    for key, item in desired.items():
        obj = existing.get(key)

        def work(key=key, item=item, obj=obj):
            if obj is None:
                instance = build(item)
                instance.full_clean()
                instance.save()
                result.change(section, key, "create")
                existing[key] = instance
                if after:
                    after(instance, item)
                return
            changed = _set_scalars(obj, model, {n: item[n] for n in scalars if n in item})
            if references:
                changed.update(references(obj, item))
            if changed:
                if guard:
                    guard(obj)
                obj.full_clean()
                obj.save()
                result.change(section, key, "update", changed)
            if after:
                after(obj, item)

        _step(result, section, key, work)
    extras = sorted(set(existing) - set(desired))
    if extras and not prune:
        result.unmanaged[section] = extras
    if prune:
        for key in extras:

            def remove(key=key):
                if protect_delete:
                    protect_delete(existing[key])
                existing[key].delete()
                result.change(section, key, "delete")

            _step(result, section, key, remove)


def _fk_reference(section, attr, name_of, mapping, item_key):
    def references(obj, item):
        wanted = item.get(item_key)
        if item_key not in item:
            return {}
        current = getattr(obj, attr)
        label = name_of(current) if current is not None else None
        if label == wanted:
            return {}
        setattr(obj, attr, _lookup(mapping, wanted, section, str(obj)))
        return {attr: {"before": label, "after": wanted}}

    return references


def apply_document(event, document, *, prune=False):
    """Mutate `event` to match `document` (managed sections only). Must run in a
    transaction the caller controls; returns a `Result`.
    """
    result = Result()

    def managed(section):
        return document.get(section) is not None

    def by(queryset, attr="name"):
        return {getattr(o, attr): o for o in queryset}

    if isinstance(document.get("event"), dict):
        try:
            changed = _set_scalars(event, Event, document["event"])
        except ValueError as exc:
            changed = {}
            result.error("event", "event", str(exc))
        if changed:
            try:
                event.full_clean()
            except ValidationError as exc:
                result.error("event", "event", "; ".join(exc.messages))
            else:
                event.save()
                result.change("event", "event", "update", changed)

    if managed("tracks"):
        _upsert(
            result, "tracks", by(event.tracks.all()), document["tracks"], Track,
            lambda i: Track(
                event=event, name=i["name"], **_defaults(Track, i, ("description", "position"))
            ),
            ("description", "position"), prune,
            protect_delete=lambda t: _refuse_if(
                Project.objects.filter(track=t).exists(), "tracks", t.name,
                "Projects are assigned to this track.",
            ),
        )  # fmt: skip
    tracks = by(event.tracks.all())

    if managed("stages"):
        _upsert(
            result, "stages", by(event.stages.all()), document["stages"], Stage,
            lambda i: Stage(
                event=event, name=i["name"], participation_mode=i["participation_mode"],
                **_defaults(Stage, i, ("position", "is_initial")),
            ),
            ("participation_mode", "position", "is_initial"), prune,
        )  # fmt: skip
    stages = by(event.stages.all())

    if managed("stage_transitions"):
        _sync_transitions(result, event, document["stage_transitions"], stages, prune)

    if managed("base_prizes"):
        _upsert(
            result, "base_prizes", by(event.base_prizes.select_related("track")),
            document["base_prizes"], BasePrize,
            lambda i: BasePrize(
                event=event, name=i["name"], kind=i["kind"],
                track=_lookup(tracks, i.get("track"), "base_prizes", i["name"]),
                **_defaults(BasePrize, i, ("description", "amount", "currency", "position")),
            ),
            ("kind", "description", "amount", "currency", "position"), prune,
            references=_fk_reference("base_prizes", "track", lambda t: t.name, tracks, "track"),
        )  # fmt: skip

    if managed("forms"):
        _upsert(
            result, "forms", by(event.forms.select_related("stage")), document["forms"],
            FormDefinition,
            lambda i: FormDefinition(
                event=event, name=i["name"],
                stage=_lookup(stages, i.get("stage"), "forms", i["name"]),
                draft_schema=i.get("draft_schema", {}),
            ),
            ("draft_schema",), prune,
            references=_fk_reference("forms", "stage", lambda s: s.name, stages, "stage"),
        )  # fmt: skip

    if managed("policies"):
        _upsert(
            result, "policies", by(event.policies.all()), document["policies"], Policy,
            lambda i: Policy(event=event, name=i["name"], ast=i["ast"]), ("ast",), prune,
        )  # fmt: skip
    policies = by(event.policies.all())

    if managed("temporal_gates"):
        _upsert(
            result, "temporal_gates", by(event.temporal_gates.all()), document["temporal_gates"],
            TemporalGate,
            lambda i: TemporalGate(
                event=event, name=i["name"],
                opens_at=_parse_dt(i.get("opens_at")), closes_at=_parse_dt(i.get("closes_at")),
            ),
            ("opens_at", "closes_at"), prune,
        )  # fmt: skip

    if managed("policy_bindings"):
        _upsert(
            result, "policy_bindings", by(event.policy_bindings.select_related("policy"), "action"),
            document["policy_bindings"], PolicyBinding,
            lambda i: PolicyBinding(
                event=event, action=i["action"],
                policy=_lookup(policies, i["policy"], "policy_bindings", i["action"]),
            ),
            (), prune,
            references=_fk_reference(
                "policy_bindings", "policy", lambda p: p.name, policies, "policy"
            ),
        )  # fmt: skip

    if managed("evaluation_plans"):
        _sync_plans(result, event, document["evaluation_plans"], stages, prune)
    plans = {
        f"{p.stage.name}/{p.name}": p
        for p in EvaluationPlan.objects.filter(stage__event=event).select_related("stage")
    }

    if managed("awards"):
        _sync_awards(result, event, document["awards"], tracks, plans, prune)

    if "page" in document:
        _sync_page(result, event, document["page"], prune)
    return result


def _refuse_if(condition, section, key, message):
    if condition:
        raise ConfigError(section, key, message)


def _sync_transitions(result, event, items, stages, prune):
    existing = {
        f"{t.from_stage.name} -> {t.to_stage.name}": t
        for t in StageTransition.objects.filter(from_stage__event=event).select_related(
            "from_stage", "to_stage"
        )
    }
    desired = {_KEY_OF["stage_transitions"](i): i for i in items}
    for key, item in desired.items():
        if key in existing:
            continue

        def create(key=key, item=item):
            transition = StageTransition(
                from_stage=_lookup(stages, item["from"], "stage_transitions", key),
                to_stage=_lookup(stages, item["to"], "stage_transitions", key),
            )
            transition.full_clean()
            transition.save()
            result.change("stage_transitions", key, "create")

        _step(result, "stage_transitions", key, create)
    extras = sorted(set(existing) - set(desired))
    if extras and not prune:
        result.unmanaged["stage_transitions"] = extras
    if prune:
        for key in extras:

            def remove(key=key):
                existing[key].delete()
                result.change("stage_transitions", key, "delete")

            _step(result, "stage_transitions", key, remove)


def _sync_plans(result, event, items, stages, prune):
    existing = {
        f"{p.stage.name}/{p.name}": p
        for p in EvaluationPlan.objects.filter(stage__event=event).select_related("stage")
    }

    def rubrics(plan, item):
        have = {v.number: v for v in plan.rubric_versions.all()}
        latest = max(have, default=0)
        for version in sorted(item.get("rubric_versions", []), key=lambda v: v["number"]):
            number = version["number"]
            key = f"{plan.stage.name}/{plan.name}#{number}"
            if number in have:
                if have[number].criteria != version["criteria"]:
                    raise ConfigError(
                        "evaluation_plans", key,
                        "Published rubric versions are immutable; add a new version number.",
                    )  # fmt: skip
                continue
            if number <= latest:
                raise ConfigError(
                    "evaluation_plans", key,
                    "New rubric versions must be numbered above existing ones.",
                )  # fmt: skip
            row = RubricVersion(plan=plan, number=number, criteria=version["criteria"])
            row.full_clean()
            row.save()
            latest = number
            result.change("evaluation_plans", key, "create")

    _upsert(
        result, "evaluation_plans", existing, items, EvaluationPlan,
        lambda i: EvaluationPlan(
            stage=_lookup(stages, i["stage"], "evaluation_plans", i["name"]),
            name=i["name"], candidate_type=i["candidate_type"], pool_strategy=i["pool_strategy"],
            results_visible_to_participants=i.get("results_visible_to_participants", False),
        ),
        ("candidate_type", "pool_strategy", "results_visible_to_participants"), False,
        after=rubrics,
    )  # fmt: skip
    if prune:
        for key in result.unmanaged.pop("evaluation_plans", []):
            result.error(
                "evaluation_plans", key,
                "Evaluation plans hold judging evidence; remove them by hand.",
            )  # fmt: skip


def _sync_awards(result, event, items, tracks, plans, prune):
    existing = {
        a.name: a for a in event.awards.select_related("eligibility_track", "evaluation_plan")
    }

    def frozen(award):
        if award.published_at:
            raise ConfigError("awards", award.name, "A published award cannot be changed.")

    def components(award, item):
        if "components" not in item:
            return
        package = PrizePackage.objects.filter(award=award).first()
        have = {c.name: c for c in package.components.all()} if package else {}
        wanted = {c["name"]: c for c in item["components"]}
        if len(wanted) != len(item["components"]):
            raise ConfigError("awards", award.name, "Prize component names must be unique.")
        for name, spec in wanted.items():
            values = {
                n: spec[n]
                for n in ("kind", "description", "quantity", "amount", "currency", "position")
                if n in spec
            }
            key = f"{award.name}/{name}"
            if name not in have:
                frozen(award)
                if package is None:
                    package = PrizePackage(award=award, name=award.name)
                    package.full_clean()
                    package.save()
                component = PrizeComponent(
                    package=package,
                    name=name,
                    **{n: _model_value(PrizeComponent, n, v) for n, v in values.items()},
                )
                component.full_clean()
                component.save()
                result.change("awards", key, "create")
                continue
            changed = _set_scalars(have[name], PrizeComponent, values)
            if changed:
                frozen(award)
                have[name].full_clean()
                have[name].save()
                result.change("awards", key, "update", changed)
        for name in sorted(set(have) - set(wanted)):
            if prune:
                frozen(award)
                have[name].delete()
                result.change("awards", f"{award.name}/{name}", "delete")
            else:
                result.unmanaged.setdefault("award_components", []).append(f"{award.name}/{name}")

    def plan_name(p):
        return f"{p.stage.name}/{p.name}"

    track_ref = _fk_reference(
        "awards", "eligibility_track", lambda t: t.name, tracks, "eligibility_track"
    )
    plan_ref = _fk_reference("awards", "evaluation_plan", plan_name, plans, "evaluation_plan")

    def references(obj, item):
        return {**track_ref(obj, item), **plan_ref(obj, item)}

    _upsert(
        result, "awards", existing, items, Award,
        lambda i: Award(
            event=event, name=i["name"], selection_source=i["selection_source"],
            eligibility_track=_lookup(tracks, i.get("eligibility_track"), "awards", i["name"]),
            evaluation_plan=_lookup(plans, i.get("evaluation_plan"), "awards", i["name"]),
            **_defaults(
                Award, i,
                ("description", "require_finalized_submission", "winner_count",
                 "allow_stacking", "conflict_group"),
            ),
        ),
        ("selection_source", "description", "require_finalized_submission", "winner_count",
         "allow_stacking", "conflict_group"),
        prune, references=references, guard=frozen, after=components,
        protect_delete=lambda a: _refuse_if(
            bool(a.published_at) or a.winners.exists(), "awards", a.name,
            "A published or decided award cannot be removed.",
        ),
    )  # fmt: skip


def _sync_page(result, event, desired, prune):
    page = Page.objects.filter(event=event).first()
    if desired is None:
        if page is not None and prune:
            page.delete()
            result.change("page", "page", "delete")
        elif page is not None:
            result.unmanaged["page"] = ["page"]
        return

    target = {
        "theme": desired.get("theme", "default"),
        "theme_config": desired.get("theme_config", {}),
        "blocks": [
            {"kind": b["kind"], "position": b.get("position", i), "config": b.get("config", {})}
            for i, b in enumerate(desired.get("blocks", []))
        ],
    }

    def work():
        current = _page_doc(event)
        if current == target:
            return
        row = page or Page(event=event)
        row.theme = target["theme"]
        row.theme_config = target["theme_config"]
        row.full_clean()
        row.save()
        row.blocks.all().delete()
        for block in target["blocks"]:
            block_row = PageBlock(page=row, **block)
            block_row.full_clean()
            block_row.save()
        result.change(
            "page", "page", "update" if current else "create",
            {"blocks": {"before": len(current["blocks"]) if current else 0,
                        "after": len(target["blocks"])}},
        )  # fmt: skip

    _step(result, "page", "page", work)


# ---- public operations --------------------------------------------------


def _preflight(event, document):
    errors = schema_errors(document)
    if event.status == EventStatus.ARCHIVED:
        errors.append(
            {"section": "event", "key": "", "message": "Archived events cannot be changed."}
        )
    return errors


def validate(event, document):
    """Structural validation plus a full trial apply (rolled back)."""
    return plan(event, document)["errors"]


def plan(event, document, *, prune=False):
    errors = _preflight(event, document)
    before = digest(event)
    if errors:
        return {"digest": before, "changes": [], "errors": errors, "unmanaged": {}, "summary": {}}
    with transaction.atomic():
        locked = Event.objects.select_for_update().get(pk=event.pk)
        result = apply_document(locked, document, prune=prune)
        transaction.set_rollback(True)
    return _report(before, result)


def apply(event, document, *, expected_digest, actor, prune=False):
    from audit.services import record_mutation

    errors = _preflight(event, document)
    with transaction.atomic():
        locked = Event.objects.select_for_update().get(pk=event.pk)
        before = digest(locked)
        if expected_digest != before:
            raise StaleDigest(before)
        if errors:
            return {
                "digest": before,
                "changes": [],
                "errors": errors,
                "unmanaged": {},
                "summary": {},
            }
        result = apply_document(locked, document, prune=prune)
        if result.errors:
            transaction.set_rollback(True)
            return _report(before, result)
        if result.changes:
            record_mutation(
                actor=actor,
                workspace=locked.workspace,
                action="event.config_applied",
                target=locked,
                metadata={
                    "event_id": str(locked.public_id),
                    "before_digest": before,
                    "summary": _summary(result),
                    "prune": prune,
                },
            )
    report = _report(before, result)
    report["digest"] = digest(locked)
    return report


class StaleDigest(Exception):
    def __init__(self, current):
        super().__init__("The event changed since this plan was made.")
        self.current = current


def _summary(result):
    summary = {}
    for change in result.changes:
        summary[change["action"]] = summary.get(change["action"], 0) + 1
    return summary


def _report(before, result):
    return {
        "digest": before,
        "changes": result.changes,
        "errors": result.errors,
        "unmanaged": result.unmanaged,
        "summary": _summary(result),
    }
